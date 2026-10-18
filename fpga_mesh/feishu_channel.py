"""Real Feishu group ingress for one Astra role.

Only the local Astra app opens a long connection. DeepSeek identities are
outbound-only and are never subscribed to group events by this module.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from .protocol import Envelope, MessageKind, SourceKind, task_id_from_message


def _message_uuid(app_id: str, operation_id: str) -> str:
    """A stable, bounded idempotency key accepted by Feishu send APIs."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{app_id}:{operation_id}"))


class FeishuSendError(RuntimeError):
    """Only a fixed error category and numeric API code cross the SDK boundary."""

    def __init__(
        self, category: str, code: int | None = None, *, definitely_rejected: bool = False,
    ):
        self.code = code if type(code) is int else None
        self.definitely_rejected = definitely_rejected
        super().__init__(category + (f":{self.code}" if self.code is not None else ""))


def _send_error(error: Any) -> FeishuSendError:
    if isinstance(error, FeishuSendError):
        return error
    # SDK SendError.raw_code is structured, but token acquisition exceptions
    # are flattened by SDK 1.4 into UNKNOWN + hint. Parse only its fixed prefix;
    # never persist hint, msg, raw response, exception args or message content.
    category = getattr(getattr(error, "code", None), "value", None)
    allowed = {"format_error", "target_revoked", "rate_limited", "permission_denied",
               "upload_failed", "download_failed", "ssrf_blocked", "send_timeout",
               "not_connected", "unknown", "not_supported", "meeting_not_found",
               "too_many_sessions"}
    if isinstance(category, str) and category in allowed:
        code = getattr(error, "raw_code", None)
        hint = getattr(error, "hint", None)
        if type(code) is int and code == 21001:
            return FeishuSendError("access_policy", code, definitely_rejected=True)
        if category == "unknown" and code is None and isinstance(hint, str):
            match = re.match(
                r"\Aobtain (?:self|isv) (?:app|tenant) access token failed, "
                r"code: ([0-9]{1,10}), msg: ", hint,
            )
            if match:
                return FeishuSendError("access_token_error", int(match[1]),
                                       definitely_rejected=int(match[1]) > 0)
        # An internal server error may occur after message creation. Only
        # classified precondition/auth/rate rejections establish non-delivery.
        rejected = category in {"format_error", "target_revoked", "rate_limited", "permission_denied"}
        return FeishuSendError(category, code,
                               definitely_rejected=rejected and type(code) is int and code > 0)
    if (type(error).__module__ == "lark_channel.core.exception"
            and type(error).__name__ == "ObtainAccessTokenException"):
        code = getattr(error, "code", None)
        return FeishuSendError("access_token_error", code,
                               definitely_rejected=type(code) is int and code > 0)
    for kind in (TimeoutError, ConnectionError, ValueError, RuntimeError):
        if isinstance(error, kind):
            return FeishuSendError(kind.__name__)
    return FeishuSendError("send_error")


def _require_message_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeishuSendError("missing_message_id")
    return value


def _message_metadata(msg, raw):
    def fields(obj, names):
        return {name: getattr(obj, name, None) for name in names}
    return {
        'body_text': str(getattr(msg, 'body_text', '') or ''),
        'content_text': str(getattr(msg, 'content_text', '') or ''),
        'message_type': getattr(msg, 'raw_content_type', None),
        'thread_id': getattr(getattr(msg, 'conversation', None), 'thread_id', None),
        'mentions': [fields(item, ('key','open_id','user_id','union_id','name','is_bot'))
                     for item in getattr(msg, 'mentions', ())],
        'resources': [fields(item, ('type','file_key','file_name','duration_ms','cover_image_key'))
                      for item in getattr(msg, 'resources', ())],
        'reply': fields(getattr(msg, 'reply', None), ('message_id','text','sender_id')),
        'raw_message': {key: raw[key] for key in ('message_id','root_id','parent_id','thread_id',
            'create_time','update_time','message_type','content','mentions') if key in raw},
        'attachments_downloaded': False,
    }


class FeishuIngress:
    def __init__(
        self, *, node_id: str, project_id: str, group_id: str,
        app_id: str, controller: Any,
        local_bot_open_ids: set[str] | None = None,
        allowed_sender_ids: set[str] | None = None,
        trusted_receiver: Callable[[Envelope], Awaitable[bool]] | None = None,
    ) -> None:
        if node_id not in {"A", "B", "C"}:
            raise ValueError("node_id must be A, B, or C")
        if not group_id.startswith("oc_"):
            raise ValueError("Feishu group_id must begin with oc_")
        self.node_id = node_id
        self.project_id = project_id
        self.group_id = group_id
        self.app_id = app_id
        self.controller = controller
        self.trusted_receiver = trusted_receiver
        self.local_bot_open_ids = set(local_bot_open_ids or ())
        self.allowed_sender_ids = (
            set(allowed_sender_ids) if allowed_sender_ids is not None else None
        )
        self._highest_revision: dict[str, int] = {}

    async def ingest(self, msg: Any) -> bool:
        sources = getattr(msg, 'batched_sources', None)
        if sources:
            accepted = False
            for source in sources:
                if source is msg:
                    raise ValueError('recursive normalized message batch')
                accepted = await self.ingest(source) or accepted
            return accepted
        if getattr(msg, "chat_id", None) != self.group_id:
            return False
        if getattr(msg, "chat_type", None) not in {"group", "topic"}:
            return False
        if getattr(msg, "sender_type", None) != "user":
            return False
        sender_id = getattr(msg, "sender_id", "")
        if not sender_id or (
            self.allowed_sender_ids is not None
            and sender_id not in self.allowed_sender_ids
        ):
            return False
        # Every human instruction in the designated group reaches Astra.  A
        # mention of another bot does not lower its priority or wake a child.
        text = str(getattr(msg, "body_text", "") or "").strip()
        if not text:
            text = (str(getattr(msg, 'content_text', '') or '').strip()
                    or '[收到无正文的人类群消息；请查看原消息信息。]')
        platform_message_id = str(getattr(msg, "message_id", "") or "")
        if not platform_message_id:
            return False
        raw = getattr(msg, "raw", None)
        raw = raw if isinstance(raw, dict) else {}
        created_ms = int(getattr(msg, "create_time", 0) or 0)
        revision = max(1, int(raw.get("update_time") or created_ms or 1))
        if revision <= self._highest_revision.get(platform_message_id, 0):
            return False
        command = text.casefold()
        kind = {
            "/fpga pause": MessageKind.STOP_REQUEST,
            "/fpga resume": MessageKind.RESUME_REQUEST,
        }.get(command, MessageKind.HUMAN_INSTRUCTION)
        target_node: str | None = None
        if kind == MessageKind.HUMAN_INSTRUCTION:
            addressed = re.match(
                r"^(?:/fpga\s+([abc])\b|astra-([abc])\s*[:：])",
                text, re.IGNORECASE,
            )
            if addressed:
                target_node = (addressed.group(1) or addressed.group(2)).upper()
            else:
                named = {
                    match.group(1).upper()
                    for mention in getattr(msg, "mentions", ())
                    if getattr(mention, "is_bot", False)
                    for match in [re.fullmatch(
                        r"FPGA\s+(?:Astra|DeepSeek)\s+([ABC])",
                        str(getattr(mention, "name", "") or ""), re.IGNORECASE,
                    )]
                    if match is not None
                }
                if len(named) == 1:
                    target_node = next(iter(named))
                elif getattr(msg, "mentioned_bot", False) or any(
                    getattr(mention, "open_id", None) in self.local_bot_open_ids
                    for mention in getattr(msg, "mentions", ())
                ):
                    target_node = self.node_id
            if target_node is not None and target_node != self.node_id:
                return False
        envelope = Envelope(
            message_id=f"feishu:{self.group_id}:{platform_message_id}:{revision}",
            project_id=self.project_id,
            sender=sender_id,
            recipient=f"{self.node_id}/Astra-{self.node_id}",
            task_id=task_id_from_message(self.group_id, platform_message_id),
            task_version=revision,
            sent_at=datetime.fromtimestamp(
                created_ms / 1000, timezone.utc,
            ) if created_ms else datetime.now(timezone.utc),
            kind=kind,
            source=SourceKind.HUMAN,
            payload={
                "text": text, "scope": "all",
                "feishu": _message_metadata(msg, raw),
                "ownership_required": (
                    kind == MessageKind.HUMAN_INSTRUCTION
                    and target_node is None
                ),
            },
            revision=revision,
            platform_group_id=self.group_id,
            platform_message_id=platform_message_id,
            platform_event_id=str(raw.get("event_id") or "") or None,
        )
        accepted = False
        if self.trusted_receiver is not None:
            accepted = await self.trusted_receiver(envelope) is True
        if not accepted:
            accepted = await self.controller.offer(envelope)
        if accepted:
            self._highest_revision[platform_message_id] = revision
        return accepted


class FeishuAppSender:
    """Send with the DeepSeek app's identity without opening an event stream."""

    def __init__(
        self, *, app_id: str, secret_file: Path,
        client_factory: Callable[[str, str], Any] | None = None,
    ) -> None:
        self.app_id = app_id
        self.secret_file = Path(secret_file)
        self.client_factory = client_factory
        self._client: Any | None = None

    async def send(self, group_id: str, text: str, operation_id: str) -> str:
        return await asyncio.to_thread(
            self._send_sync, group_id, text, operation_id,
        )

    def _send_sync(self, group_id: str, text: str, operation_id: str) -> str:
        if not group_id.startswith("oc_") or not text.strip() or not operation_id:
            raise ValueError("invalid Feishu group send request")
        try:
            from lark_channel import Client
            from lark_channel.api.im.v1.model.create_message_request import (
                CreateMessageRequest,
            )
            from lark_channel.api.im.v1.model.create_message_request_body import (
                CreateMessageRequestBody,
            )
        except ImportError as exc:
            raise RuntimeError("DeepSeek Feishu sender requires lark-channel-sdk") from exc
        if self._client is None:
            secret = self.secret_file.read_text(encoding="utf-8-sig").strip()
            if not secret:
                raise ValueError("DeepSeek Feishu app secret file is empty")
            self._client = (
                self.client_factory(self.app_id, secret)
                if self.client_factory is not None else
                Client.builder().app_id(self.app_id).app_secret(secret).build()
            )
        request = CreateMessageRequest.builder().receive_id_type("chat_id").request_body(
            CreateMessageRequestBody.builder()
            .receive_id(group_id)
            .msg_type("text")
            .content(json.dumps({"text": text}, ensure_ascii=False))
            .uuid(_message_uuid(self.app_id, operation_id))
            .build()
        ).build()
        try:
            response = self._client.im.v1.message.create(request)
        except Exception as exc:
            raise _send_error(exc) from None
        if not response.success():
            code = getattr(response, "code", None)
            if type(code) is int:
                from lark_channel.channel.errors import classify_error
                raise _send_error(classify_error(code))
            raise FeishuSendError("api_error")
        return _require_message_id(getattr(getattr(response, "data", None), "message_id", None))


class FeishuNodeService:
    """Connect the node's Astra app and send group reports as that app."""

    def __init__(
        self, *, node_id: str, project_id: str, group_id: str,
        astra_app_id: str, astra_secret_file: Path, controller: Any,
        local_bot_open_ids: set[str] | None = None,
        allowed_sender_ids: set[str] | None = None,
        channel_factory: Callable[..., Any] | None = None,
        store: Any | None = None,
        retry_seconds: float = 30.0,
        deepseek_app_id: str = "",
        deepseek_secret_file: Path | None = None,
        deepseek_sender: Any | None = None,
        job_lookup: Callable[[str], dict] | None = None,
        trusted_receiver: Callable[[Envelope], Awaitable[bool]] | None = None,
        history_state_dir: Path | None = None,
        history_receiver: Callable[[dict], Awaitable[bool]] | None = None,
        history_pending: Callable[[], list[dict]] | None = None,
        history_scan_begin: Callable[[dict], Awaitable[bool]] | None = None,
        history_scan_end: Callable[[dict], Awaitable[bool]] | None = None,
        history_recheck: Callable[[], bool] | None = None,
        history_api: Any | None = None,
    ) -> None:
        self.group_id = group_id
        self.astra_app_id = astra_app_id
        self.astra_secret_file = Path(astra_secret_file)
        self.ingress = FeishuIngress(
            node_id=node_id, project_id=project_id, group_id=group_id,
            app_id=astra_app_id, controller=controller,
            local_bot_open_ids=local_bot_open_ids,
            allowed_sender_ids=allowed_sender_ids,
            trusted_receiver=trusted_receiver,
        )
        self.channel_factory = channel_factory
        self.store = store
        self.job_lookup = job_lookup
        self.deepseek_sender = deepseek_sender or (
            FeishuAppSender(
                app_id=deepseek_app_id, secret_file=deepseek_secret_file,
            ) if deepseek_app_id and deepseek_secret_file else None
        )
        if retry_seconds <= 0:
            raise ValueError("retry_seconds must be positive")
        self.retry_seconds = retry_seconds
        self.channel: Any | None = None
        self.connected = False
        self._outbox_errors: dict[str, str | None] = {"astra": None, "deepseek": None}
        self._role_locks = {role: asyncio.Lock() for role in self._outbox_errors}
        self._role_events = {role: asyncio.Event() for role in self._outbox_errors}
        self._outbox_task: asyncio.Task | None = None
        if history_state_dir is not None and history_receiver is None:
            raise ValueError('history recovery requires a durable hold receiver')
        if history_receiver is not None and history_state_dir is None:
            raise ValueError('history recovery requires its durable state directory')
        self.history_state_dir = Path(history_state_dir) if history_state_dir is not None else None
        self.history_receiver, self.history_pending = history_receiver, history_pending
        self.history_scan_begin, self.history_api = history_scan_begin, history_api
        self.history_scan_end = history_scan_end
        self.history_recheck = history_recheck
        self.history: Any | None = None
        self._history_task: asyncio.Task | None = None
        self._history_event = asyncio.Event()
        self._history_triggers: set[str] = set()
        self._history_error: str | None = None

    @property
    def last_error(self) -> str | None:
        pending_error = self.store.group_outbox_health()["last_error"] if self.store else None
        return (pending_error or self._history_error
                or next((error for error in self._outbox_errors.values() if error), None))

    def history_health(self):
        latest = self.history.last_result if self.history is not None else None
        return {'enabled': self.history_state_dir is not None,
                'running': self._history_task is not None and not self._history_task.done(),
                'error': self._history_error,
                'checkpoint_ms': self.history.checkpoint_ms if self.history is not None else None,
                'last_scan': {key: latest.get(key) for key in
                    ('scan_id','status','lower_ms','upper_ms','gap','notification_gap')}
                    if latest else None}

    async def start(self) -> None:
        if self.connected:
            return
        secret = self.astra_secret_file.read_text(encoding="utf-8-sig").strip()
        if not secret:
            raise ValueError("Astra Feishu app secret file is empty")
        if self.channel_factory is None:
            try:
                from lark_channel import (
                    FeishuChannel, OutboundConfig, PolicyConfig, RetryConfig, SecurityConfig,
                )
            except ImportError as exc:
                raise RuntimeError(
                    "Feishu requires lark-channel-sdk; install the feishu extra"
                ) from exc
            self.channel_factory = lambda **kwargs: FeishuChannel(
                **kwargs,
                policy=PolicyConfig(
                    dm_policy="disabled", group_policy="allowlist",
                    group_allowlist=[self.group_id], require_mention=False,
                ),
                security=SecurityConfig(mode="strict"),
                outbound=OutboundConfig(retry=RetryConfig(max_attempts=1)),
            )
        channel = self.channel_factory(app_id=self.astra_app_id, app_secret=secret)
        controller_loop = asyncio.get_running_loop()
        if self.history_state_dir is not None:
            from .feishu_history import FeishuHistoryAPI, FeishuHistoryRecovery
            self.history = FeishuHistoryRecovery(self.history_state_dir / 'history.sqlite',
                group_id=self.group_id, app_id=self.astra_app_id,
                api=self.history_api or FeishuHistoryAPI(channel.client, expected_app_id=self.astra_app_id),
                sink=self.history_receiver, pending_messages=self.history_pending or (lambda: []),
                on_scan_begin=self.history_scan_begin,
                on_scan_end=self.history_scan_end,
                allowed_sender_ids=self.ingress.allowed_sender_ids)

        def request_history(trigger: str, message_id: str | None = None) -> None:
            def enqueue():
                if self.history is None:
                    return
                try:
                    if trigger == 'reconnected' and self.history_recheck is not None:
                        if self.history_recheck() is not True:
                            raise ValueError('history source gate was not persisted')
                    if message_id:
                        self.history.watch(message_id)
                except Exception:
                    self._history_error = 'Feishu history source gate/watch persistence failed'
                self._history_triggers.add(trigger)
                self._history_event.set()
            if not controller_loop.is_closed():
                controller_loop.call_soon_threadsafe(enqueue)

        async def ingest_with_recovery(msg: Any) -> bool:
            try:
                return await self.ingress.ingest(msg)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Persist the failed source reference before returning to the
                # SDK, whose handler wrapper may swallow this exception and
                # whose dedup may already have consumed the message ID.
                if self.history is not None:
                    for source in (getattr(msg, 'batched_sources', None) or (msg,)):
                        if getattr(source, 'chat_id', None) == self.group_id:
                            self.history.watch(getattr(source, 'message_id', None))
                self._history_error = 'Feishu live durable sink failed; history recovery required'
                request_history('sink_failure')
                raise

        async def deliver_message(msg: Any) -> bool:
            # The SDK dispatches WS events from its own event-loop thread.
            # Controller, child coordinator and SQLite state belong to the
            # runtime loop and must never be called on that SDK thread.
            if asyncio.get_running_loop() is controller_loop:
                return await ingest_with_recovery(msg)
            if not controller_loop.is_running():
                return False
            delivery = asyncio.run_coroutine_threadsafe(
                ingest_with_recovery(msg), controller_loop,
            )
            return await asyncio.wrap_future(delivery)

        channel.on("message", deliver_message)
        if self.history is not None:
            channel.on('reconnected', lambda: request_history('reconnected'))
            def rejected(event):
                if (getattr(event, 'chat_id', None) == self.group_id
                        and getattr(event, 'reason', None) in {'stale', 'duplicate', 'lock_contention'}):
                    request_history('reject', getattr(event, 'message_id', None))
            channel.on('reject', rejected)
        try:
            if self.history is not None and self.history_recheck is not None:
                if self.history_recheck() is not True:
                    raise ValueError('history source gate was not persisted')
            await channel.connect_until_ready(timeout=30)
        except BaseException:
            if self.history is not None:
                self.history.close()
                self.history = None
            raise
        self.channel = channel
        self.connected = True
        if self.history is not None:
            self._history_task = asyncio.create_task(self._run_history())
            request_history('start')
        if self.store is not None:
            self._outbox_task = asyncio.create_task(self._run_outbox())
            self.notify_report()

    async def stop(self) -> None:
        if self._history_task is not None:
            self._history_task.cancel()
            try:
                await self._history_task
            except asyncio.CancelledError:
                pass
            self._history_task = None
        if self.history is not None:
            self.history.close()
            self.history = None
        if self._outbox_task is not None:
            self._outbox_task.cancel()
            try:
                await self._outbox_task
            except asyncio.CancelledError:
                pass
            self._outbox_task = None
        channel = self.channel
        self.channel = None
        self.connected = False
        if channel is not None:
            await channel.disconnect()

    async def _run_history(self) -> None:
        """Ordinary resident-program retries; never dispatch a model turn."""
        while self.connected:
            try:
                await asyncio.wait_for(self._history_event.wait(), timeout=self.retry_seconds)
            except asyncio.TimeoutError:
                pass
            self._history_event.clear()
            triggers = sorted(self._history_triggers)
            self._history_triggers.clear()
            try:
                result = await self.history.scan(','.join(triggers) or 'retry')
                gap = result.get('gap')
                self._history_error = ('Feishu history gap: ' + gap['category']
                    + (':' + str(gap['code']) if gap.get('code') is not None else '')) if gap else None
            except asyncio.CancelledError:
                raise
            except Exception:
                self._history_error = 'Feishu history persistence/recovery failed'
            if self._history_error:
                # Reconnect/reject bursts coalesce during a failed scan's
                # cooldown instead of hammering a denied API such as 21001.
                await asyncio.sleep(self.retry_seconds)

    async def send_as_astra(self, text: str, *, operation_id: str) -> str:
        if not self.connected or self.channel is None:
            raise RuntimeError("Feishu Astra channel is not connected")
        if not text.strip():
            raise ValueError("group message must not be empty")
        expected_chunks = self._expected_astra_chunks(text)
        try:
            result = await self.channel.send(
                self.group_id, {"text": text},
                {"uuid": _message_uuid(self.astra_app_id, operation_id)},
            )
        except Exception as exc:
            raise _send_error(exc) from None
        if not result.success:
            error = _send_error(getattr(result, "error", None))
            # SDK 1.4 loses successful prior chunk IDs on a later chunk failure,
            # and later chunks use random UUIDs. An API rejection then proves
            # only that chunk failed, not that the logical report was unsent.
            if expected_chunks is None or expected_chunks != 1:
                error.definitely_rejected = False
            raise error
        return self._acknowledged_astra_result(operation_id, result, expected_chunks)

    def _expected_astra_chunks(self, text: str) -> int | None:
        outbound = getattr(getattr(self.channel, "config", None), "outbound", None)
        limit = getattr(outbound, "text_chunk_limit", 3500)
        mode = getattr(outbound, "chunk_mode", "newline")
        if type(limit) is int and limit > 0 and mode in {"newline", "paragraph", "none"}:
            if len(text) <= limit:
                return 1
            elif getattr(outbound, "on_oversize", None) is None:
                # Use the installed SDK's real boundary algorithm, including
                # newline cuts and atomic mentions, not ceil(length / limit).
                from lark_channel.channel.outbound.sender import chunk_text
                return len(chunk_text(text, limit=limit, mode=mode))
        return None

    def _acknowledged_astra_result(
        self, operation_id: str, result: Any, expected: int | None,
    ) -> str:
        message_id = getattr(result, "message_id", None)
        chunk_ids = getattr(result, "chunk_ids", None)
        ids = [message_id] if chunk_ids is None else chunk_ids
        valid_ids = isinstance(ids, list) and all(
            isinstance(value, str) and value.strip() for value in ids
        )
        complete = bool(
            isinstance(message_id, str) and message_id.strip() and valid_ids
            and len(ids) == expected and len(set(ids)) == len(ids)
            and ids[0] == message_id
        )
        if self.store is not None:
            state = self.store.group_report_delivery(operation_id)
            if state is not None:
                known_ids = [value for value in ids if isinstance(value, str) and value.strip()] \
                    if isinstance(ids, list) else []
                if not self.store.append_event(
                    f"feishu-ack:{_message_uuid(self.astra_app_id, operation_id)}:{state['attempts']}",
                    "feishu_report_acknowledgements",
                    {"operation_id": operation_id, "role": "astra",
                     "expected_chunks": expected, "message_ids": known_ids, "complete": complete},
                ):
                    raise FeishuSendError("acknowledgement_evidence_conflict")
        if not complete:
            _require_message_id(message_id)
            raise FeishuSendError("incomplete_chunk_acknowledgements")
        return message_id

    async def flush_reports(self) -> None:
        if self.store is None or not self.connected:
            return
        # Two lanes inside the original sender, with a single lock per app.
        # One unresolved app call must not own the other app's delivery lock.
        results = await asyncio.gather(
            *(self._flush_role_reports(role) for role in self._role_locks),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, BaseException):
                raise result

    async def _flush_role_reports(self, role: str) -> None:
        async with self._role_locks[role]:
            first_error: Exception | None = None
            blocked = False
            for operation_id, text, report_role in self.store.pending_group_messages():
                if report_role != role:
                    continue
                attempted = False
                try:
                    job_id = self.store.group_report_job(operation_id)
                    if job_id:
                        if self.job_lookup is None:
                            raise RuntimeError("child job lookup is not configured")
                        job = self.job_lookup(job_id)
                        if job["stale"] or job["status"] != "completed":
                            self.store.cancel_group_report(operation_id)
                            continue
                    if blocked or not self.store.group_role_ready(role):
                        continue
                    if role == "deepseek":
                        if self.deepseek_sender is None:
                            raise FeishuSendError("DeepSeek Feishu sender is not configured")
                        self.store.attempt_group_report(operation_id)
                        attempted = True
                        sent_id = await self.deepseek_sender.send(
                            self.group_id, text, operation_id,
                        )
                    else:
                        self.store.attempt_group_report(operation_id)
                        attempted = True
                        sent_id = await self.send_as_astra(
                            text, operation_id=operation_id,
                        )
                    self.store.ack_group_report(operation_id, _require_message_id(sent_id))
                except asyncio.CancelledError:
                    if attempted:
                        self.store.fail_group_report(
                            operation_id, "cancelled_attempt", self.retry_seconds,
                            delivery_unknown=True,
                        )
                    raise
                except Exception as exc:  # noqa: BLE001 - retain failed item
                    error = _send_error(exc)
                    self.store.fail_group_report(
                        operation_id, str(error), self.retry_seconds,
                        delivery_unknown=attempted and not error.definitely_rejected,
                    )
                    # Preserve order within this app. A denial (notably 21001)
                    # must not fan out across its queue, while the other app runs.
                    blocked = True
                    if first_error is None:
                        first_error = error
            if first_error is not None:
                raise first_error
            self._outbox_errors[role] = None

    async def reconcile_report(
        self, operation_id: str, *, evidence_sha256: str,
        platform_message_id: str | None = None, confirmed_not_sent: bool = False,
    ) -> None:
        """Owner-only local reconciliation after separately reviewing platform evidence."""
        if self.store is None:
            raise ValueError("reconciliation requires the original outbox store")
        role = next((role for operation, _, role in self.store.pending_group_messages()
                     if operation == operation_id), None)
        if role not in self._role_locks:
            raise ValueError("reconciliation requires a pending original report")
        async with self._role_locks[role]:
            self.store.reconcile_group_report(
                operation_id, evidence_sha256=evidence_sha256,
                platform_message_id=platform_message_id, confirmed_not_sent=confirmed_not_sent,
            )
            self._outbox_errors[role] = None
            self.notify_report()

    def notify_report(self) -> None:
        for event in self._role_events.values():
            event.set()

    async def _run_outbox(self) -> None:
        workers = [asyncio.create_task(self._run_role_outbox(role)) for role in self._role_locks]
        try:
            await asyncio.gather(*workers)
        finally:
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    async def _run_role_outbox(self, role: str) -> None:
        event = self._role_events[role]
        while self.connected:
            event.clear()
            try:
                await self._flush_role_reports(role)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - retain pending reports
                self._outbox_errors[role] = str(_send_error(exc))
            try:
                await asyncio.wait_for(
                    event.wait(), timeout=self.retry_seconds,
                )
            except asyncio.TimeoutError:
                pass

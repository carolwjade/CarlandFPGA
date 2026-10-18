"""The original resident controller's authenticated routes to its Desktop owner."""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .desktop_inbox import DesktopBinding, DesktopInbox, CodexQueueClient, dispatch_one
from .desktop_history import DesktopHistory
from .protocol import Envelope, MessageKind, SourceKind


class DesktopRoute:
    def __init__(self, *, state_dir, node_id, project_id, group_id, controller,
                 store, client_factory=CodexQueueClient, on_report=None,
                 history_app_id=None, history_allowed_user_ids=None):
        self.state_dir = Path(state_dir)
        self.binding_path = self.state_dir / 'desktop-group-owner.json'
        # Once configured, a missing/broken binding must never restore the old
        # per-message background writer as an implicit fallback.
        self.enabled = (self.binding_path.exists()
            or (self.state_dir / 'desktop-inbox.sqlite').exists()
            or (self.state_dir / 'desktop-feishu-spool').exists()
            or (self.state_dir / 'desktop-peer-spool').exists())
        self.node_id, self.project_id, self.group_id = node_id, project_id, group_id
        self.controller, self.store = controller, store
        self.client_factory, self.on_report = client_factory, on_report
        self.spool = self.state_dir / 'desktop-feishu-spool'
        self.peer_spool = self.state_dir / 'desktop-peer-spool'
        self.inbox = (DesktopInbox(self.state_dir / 'desktop-inbox.sqlite', recover_inflight=True)
                      if self.enabled else None)
        self.history_app_id = history_app_id
        self.history_allowed_user_ids = history_allowed_user_ids
        self.history = (DesktopHistory(self.state_dir / 'desktop-history.sqlite')
                        if self.enabled and history_app_id else None)
        self.error = None
        self.spool_errors = {}
        self._event, self._lock = asyncio.Event(), asyncio.Lock()
        self._task = None
        self._closed = False
        self._history_startup_required = self.history is not None
        if self.history is not None:
            try:
                self.history_recheck()
            except Exception as exc:
                # A broken binding or disk must not expose an authorization
                # window while remote connection/recovery is still pending.
                self.error = 'Desktop startup verification blocked: ' + type(exc).__name__

    def binding(self):
        doc = json.loads(self.binding_path.read_text(encoding='utf-8'))
        binding = DesktopBinding(project_id=doc['project_id'], node_id=doc['node_id'],
            group_id=doc['group_id'], thread_id=doc['thread_id'], generation=doc['generation'],
            task_id=doc['task_id'], active=doc.get('status') == 'active')
        if (binding.project_id, binding.node_id, binding.group_id) != (self.project_id, self.node_id, self.group_id):
            raise ValueError('Desktop binding does not match this original node and group')
        owner = json.loads((self.state_dir / 'external-task-owners.json').read_text(encoding='utf-8')).get(binding.task_id, {})
        if (owner.get('owner_kind'), owner.get('thread_id'), owner.get('director_generation')) != (
                'desktop', binding.thread_id, binding.generation):
            raise ValueError('Desktop binding conflicts with the existing authoritative owner')
        return binding, doc

    def _history_receipts(self, binding):
        records, cursor = [], None
        while True:
            page = self.inbox.list_receipts(binding, include_completed=True,
                                            after_receipt_id=cursor, limit=1000)
            records.extend(row for row in page['rows']
                           if row['source_channel'] == 'feishu' and not row['superseded_by'])
            cursor = page['next_cursor']
            if cursor is None:
                return records

    def history_pending(self):
        binding, _ = self.binding()
        if self._history_startup_required:
            self._refresh_before_claim(binding)
        # Completed acknowledgements can still concern ongoing work. Keep their
        # source IDs watched too; an edit is new evidence, not permission replay.
        return [{'message_id': row['platform_message_id'], 'revision': row['revision'],
                 'sender_id': row['envelope']['sender']}
                for row in self._history_receipts(binding)]

    def history_recheck(self):
        """Synchronously gate existing sources before startup/reconnect awaits."""
        if self.history is None or self._closed:
            return False
        self._history_startup_required = True
        binding, _ = self.binding()
        self._refresh_before_claim(binding)
        return True

    async def history_scan_begin(self, document):
        if self.history is None or self._closed:
            return False
        binding, _ = self.binding()
        return self.history.begin(document, binding, self._history_receipts(binding))

    async def receive_history(self, observation):
        if self.history is None or self._closed:
            return False
        binding, _ = self.binding()
        accepted = self.history.observe(observation, binding, self._history_receipts(binding),
            app_id=self.history_app_id, allowed_sender_ids=self.history_allowed_user_ids)
        self._event.set()
        return accepted

    async def history_scan_end(self, result):
        if self.history is None or self._closed:
            return False
        binding, _ = self.binding()
        accepted = self.history.finish(result, binding)
        self._event.set()
        return accepted

    def _recover_history_notifications(self, binding):
        if self.history is None:
            return
        for batch in self.history.pending_batches(binding):
            message = Envelope(message_id='history-review:' + batch['batch_id'],
                project_id=binding.project_id, sender=f'{binding.node_id}/FeishuRecovery',
                recipient=f'{binding.node_id}/Astra-{binding.node_id}', task_id=binding.task_id,
                task_version=1, sent_at=datetime.fromisoformat(batch['created_at']),
                kind=MessageKind.STATUS, source=SourceKind.SYSTEM,
                payload={'text': f"Review {len(batch['observation_ids'])} saved Feishu history observations.",
                         'history_batch_id': batch['batch_id'], 'disposition': 'review_only'})
            row = self.inbox.accept_history_review(message, binding)
            self.history.mark_notified(batch['batch_id'], binding, row['receipt_id'])

    def _peer_binding(self, message):
        """Only explicitly registered tasks can deliver peer data to this owner."""
        owners = json.loads((self.state_dir / 'external-task-owners.json').read_text(encoding='utf-8'))
        if not isinstance(owners, dict):
            raise ValueError('external task owners must be an object')
        owner = owners.get(message.task_id)
        try:
            doc = json.loads(self.binding_path.read_text(encoding='utf-8'))
            tasks = doc.get('peer_tasks', {})
        except (OSError, ValueError, AttributeError):
            if owner is None:
                return self._independent_peer_task(message)
            raise
        if not isinstance(tasks, dict):
            if owner is None:
                return self._independent_peer_task(message)
            raise ValueError('Desktop peer_tasks must be an object')
        if message.task_id not in tasks:
            if owner is not None:
                raise ValueError('Desktop-owned peer task has no explicit receipt registration')
            return self._independent_peer_task(message)
        if type(tasks[message.task_id]) is not int or tasks[message.task_id] < 1:
            raise ValueError('peer task version must be a positive integer')
        binding, _ = self.binding()
        if (not isinstance(owner, dict)
                or (owner.get('owner_kind'), owner.get('thread_id'), owner.get('director_generation'),
                    owner.get('task_version')) != ('desktop', binding.thread_id, binding.generation,
                                                   tasks[message.task_id])
                or message.task_version != tasks[message.task_id]):
            raise ValueError('peer task version or authoritative Desktop owner mismatch')
        binding.require_active()
        return binding

    def _independent_peer_task(self, message):
        # Missing current declarations are not an authorized ownership transfer.
        known = self.inbox.has_peer_task(self.project_id, self.node_id, message.task_id)
        if not known:
            for path in self.peer_spool.glob('*.json'):
                saved = json.loads(path.read_text(encoding='utf-8'))
                prior = Envelope.from_json(saved['envelope_json'])
                if (prior.project_id == self.project_id
                        and prior.recipient == f'{self.node_id}/Astra-{self.node_id}'
                        and prior.task_id == message.task_id):
                    known = True
                    break
        if known:
            raise ValueError('previously Desktop-owned peer task requires explicit current ownership')
        return None

    @staticmethod
    def _save_spool(message, directory, *, channel):
        raw = message.to_json()
        name = hashlib.sha256(message.dedupe_key.encode('utf-8')).hexdigest()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (name + '.json')
        if path.exists():
            prior = json.loads(path.read_text(encoding='utf-8'))
            if prior['envelope_json'] != raw:
                raise ValueError('immutable ' + channel + ' spool conflict')
        else:
            record = json.dumps({'envelope_json': raw,
                'received_at': datetime.now(timezone.utc).isoformat()}, ensure_ascii=False)
            temporary = directory / (name + '.tmp')
            if temporary.exists():
                temporary = directory / (name + '.' + os.urandom(8).hex() + '.tmp')
            with temporary.open('x', encoding='utf-8') as stream:
                stream.write(record); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, path)

    async def receive_peer(self, message):
        """Only called after the original peer HTTP HMAC and source checks."""
        if not self.enabled:
            return False
        if (self._closed or message.source != SourceKind.ASTRA
                or message.kind != MessageKind.AGENT_REPORT
                or message.project_id != self.project_id
                or message.recipient != f'{self.node_id}/Astra-{self.node_id}'
                or message.sender not in {f'{n}/Astra-{n}' for n in {'A','B','C'} - {self.node_id}}
                or any(value is not None for value in (message.platform_group_id,
                        message.platform_message_id, message.platform_event_id))):
            raise ValueError('not a trusted peer report for this route')
        binding = self._peer_binding(message)
        if binding is None:
            return False
        self._save_spool(message, self.peer_spool, channel='peer')
        self.inbox.accept_trusted_peer(message, binding)
        self._event.set()
        return True

    async def receive(self, message):
        """Only called after the Feishu SDK ingress authenticated and filtered it."""
        if not self.enabled:
            return False
        if (message.source != SourceKind.HUMAN or message.project_id != self.project_id
                or message.recipient != f'{self.node_id}/Astra-{self.node_id}'
                or message.platform_group_id != self.group_id or not message.platform_message_id):
            raise ValueError('not a trusted Feishu envelope for this route')
        self._save_spool(message, self.spool, channel='Feishu')
        try:
            binding, _ = self.binding()
            # Supersession must be visible before acknowledging a new revision,
            # even while the asynchronous queue dispatcher is busy.
            self.inbox.accept_trusted_feishu(message, binding)
        except Exception as exc:
            self.error = 'Desktop routing blocked: ' + type(exc).__name__
        self._event.set()
        if message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}:
            # Apply control to the original controller immediately, independently
            # of when Desktop can consume its copy. Normal instructions never go
            # through that controller's background-model dispatcher.
            await self.controller.offer(message)
        return True

    async def flush(self):
        if not self.enabled or self._closed:
            return
        async with self._lock:
            try:
                binding, doc = self.binding()
                binding.require_active()
                if self._history_startup_required:
                    self._refresh_before_claim(binding)
                records = []
                self.spool_errors = {}
                for path in self.spool.glob('*.json'):
                    try:
                        saved = json.loads(path.read_text(encoding='utf-8'))
                        records.append((saved['received_at'], path,
                                        Envelope.from_json(saved['envelope_json'])))
                    except Exception as exc:
                        self.spool_errors[path.name] = type(exc).__name__
                for _, path, message in sorted(records, key=lambda pair: pair[0]):
                    try:
                        self.inbox.accept_trusted_feishu(message, binding)
                        if message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}:
                            await self.controller.offer(message)
                    except Exception as exc:
                        self.spool_errors[path.name] = type(exc).__name__
                for path in sorted(self.peer_spool.glob('*.json')):
                    try:
                        saved = json.loads(path.read_text(encoding='utf-8'))
                        message = Envelope.from_json(saved['envelope_json'])
                        peer_binding = self._peer_binding(message)
                        if peer_binding is None:
                            raise ValueError('previously routed peer task is no longer registered')
                        self.inbox.accept_trusted_peer(message, peer_binding)
                    except Exception as exc:
                        self.spool_errors['peer/' + path.name] = type(exc).__name__
                client = self.client_factory(executable=doc['codex_executable'],
                    expected_sha256=doc['codex_sha256'], cwd=doc['cwd'], codex_home=doc['codex_home'],
                    requests_dir=self.state_dir / 'desktop-inbox-claims')
                self._recover_history_notifications(binding)
                while self.inbox.pending(binding):
                    pending = self.inbox.pending(binding)[0]
                    if pending.get('source_channel') == 'peer':
                        try:
                            message = Envelope.from_json(json.dumps(pending['envelope']))
                            if self._peer_binding(message) is None:
                                raise ValueError('peer task registration was removed')
                        except Exception:
                            self.inbox.hold_pending(pending['receipt_id'], binding,
                                                    reason='peer task owner or version changed')
                            continue
                    if await dispatch_one(self.inbox, binding, client) is None:
                        break
                self._recover_replies(binding)
                self.error = ('Desktop spool records need review' if self.spool_errors else None)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # Original authenticated envelopes stay in the durable spool.
                # Exception text may contain source data; expose only its type.
                self.error = 'Desktop routing blocked: ' + type(exc).__name__

    def _reply(self, row):
        if row.get('source_channel') != 'feishu':
            return None
        result = row.get('result')
        if row['processing_state'] != 'completed' or not isinstance(result, dict):
            return None
        text = result.get('reply_text')
        if not isinstance(text, str) or not text.strip() or len(text) > 2800:
            raise ValueError('completed Desktop receipt requires a bounded reply_text')
        operation = 'desktop-result:' + row['receipt_id']
        added = self.store.enqueue_group_report(operation,
            f'Astra-{self.node_id} · 回复 {row["platform_message_id"]}\n{text}')
        if added and self.on_report:
            self.on_report()
        return {'operation_id': operation, 'status': self.store.group_report_status(operation)}

    def _recover_replies(self, binding):
        cursor = None
        while True:
            page = self.inbox.list_receipts(binding, include_completed=True, after_receipt_id=cursor)
            for row in page['rows']:
                self._reply(row)
            cursor = page['next_cursor']
            if cursor is None:
                break

    def _target(self, args):
        if not self.enabled or self._closed:
            raise ValueError('Desktop route is not enabled')
        binding, _ = self.binding()
        if (args.get('thread_id'), args.get('generation')) != (binding.thread_id, binding.generation):
            raise ValueError('caller must name the current Desktop owner generation')
        return binding

    def _claim_block(self, row, *, ownership_verified=False):
        message = row['envelope']
        if (getattr(self.controller, 'dispatch_blocked', False)
                and message['kind'] not in {'stop_request', 'resume_request'}):
            return 'human_pause'
        if row.get('source_channel') == 'peer':
            if self._peer_binding(Envelope.from_json(json.dumps(message))) is None:
                raise ValueError('peer task is no longer registered to this Desktop')
            return None
        if row.get('source_channel') == 'feishu_history':
            if self.history is None:
                raise ValueError('history review source is not configured')
            return None
        if self.history is not None:
            binding, _ = self.binding()
            blocked = self.history.block_reason(binding, row['platform_message_id'], row['revision'])
            if blocked:
                return blocked
        if message['payload'].get('ownership_required') and not ownership_verified:
            return 'shared_task_ownership_unverified'
        return None

    def _refresh_before_claim(self, binding):
        # Acknowledged spool writes can precede an inbox write (disk/DB error,
        # paused owner, crash). Reapply them synchronously before any claim,
        # including after restart and after an ownership-network await.
        try:
            records = []
            for path in self.spool.glob('*.json'):
                saved = json.loads(path.read_text(encoding='utf-8'))
                records.append((saved['received_at'], Envelope.from_json(saved['envelope_json'])))
            for _, message in sorted(records, key=lambda item:item[0]):
                self.inbox.accept_trusted_feishu(message, binding)
                if message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}:
                    self.controller.recover_control(message)
            if self._history_startup_required:
                self.history.require_recheck(binding, self._history_receipts(binding))
                self._history_startup_required = False
        except Exception as exc:
            self.error = 'Desktop claim blocked by unapplied spool: ' + type(exc).__name__
            raise ValueError('unapplied Desktop spool requires recovery before execution') from None

    async def claim(self, args):
        binding = self._target(args)
        self._refresh_before_claim(binding)
        row = self.inbox.inspect_receipt(args['receipt_id'], binding, args['envelope_sha256'])
        block = self._claim_block(row, ownership_verified=True)
        if block:
            return {**row, 'effects_allowed':False, 'blocked_reason':block}
        verified = False
        if (row['processing_state'] == 'pending' and not row['superseded_by']
                and row.get('source_channel') == 'feishu'
                and row['envelope']['payload'].get('ownership_required')):
            owner = getattr(self.controller, 'claim_ownership', None)
            result = owner(Envelope.from_json(json.dumps(row['envelope']))) if owner else None
            result = await result if inspect.isawaitable(result) else result
            verified = result is True
        # Recheck binding, pause and revision after the ownership await.
        return self.call('desktop_inbox_claim', args, ownership_verified=verified)

    def call(self, action, args, *, ownership_verified=False):
        binding = self._target(args)
        if action == 'desktop_inbox_list':
            return self.inbox.list_receipts(binding, include_completed=args.get('include_completed', False),
                limit=args.get('limit', 100), after_receipt_id=args.get('after_receipt_id'))
        receipt = args['receipt_id']
        if action == 'desktop_history_read':
            row = self.inbox.inspect_receipt(receipt, binding, args['envelope_sha256'])
            if row['source_channel'] != 'feishu_history' or self.history is None:
                raise ValueError('not a configured history review receipt')
            return self.history.inspect_batch(row['envelope']['payload']['history_batch_id'], binding,
                                              offset=args.get('offset', 0), limit=args.get('limit', 20))
        if action == 'desktop_inbox_claim':
            self._refresh_before_claim(binding)
            row = self.inbox.inspect_receipt(receipt, binding, args['envelope_sha256'])
            block = self._claim_block(row, ownership_verified=ownership_verified)
            if block:
                return {**row, 'effects_allowed':False, 'blocked_reason':block}
            return self.inbox.claim(receipt, binding, claim_id=args['claim_id'],
                expected_envelope_sha256=args['envelope_sha256'])
        if action == 'desktop_inbox_complete':
            result = args['result']
            original = self.inbox.get(receipt)
            field = 'summary' if original and original.get('source_channel') != 'feishu' else 'reply_text'
            if (not isinstance(result, dict) or not isinstance(result.get(field), str)
                    or not result[field].strip() or len(result[field]) > 2800):
                raise ValueError('completion needs ' + field + ' of 1 to 2800 characters')
            row = self.inbox.complete(receipt, binding, claim_id=args['claim_id'], result=result)
            return {**row, 'reply': self._reply(row)}
        if action == 'desktop_inbox_reconcile':
            row = self.inbox.reconcile(receipt, binding,
                expected_envelope_sha256=args['envelope_sha256'], evidence=args['evidence'])
            self._event.set()
            return row
        raise ValueError('unknown Desktop inbox action')

    def health(self):
        result = {'enabled': self.enabled, 'error': self.error,
                  'spool_errors': dict(self.spool_errors)}
        if self.enabled and not self._closed:
            try:
                binding, _ = self.binding()
                result.update(self.inbox.health(binding))
                if self.history is not None:
                    result['history'] = self.history.health(binding)
            except Exception as exc:
                result['error'] = 'Desktop binding blocked: ' + type(exc).__name__
        return result

    async def start(self):
        if self.enabled and self._task is None and not self._closed:
            self._task = asyncio.create_task(self._run(), name='fpga-desktop-inbox')
            self._event.set()

    async def _run(self):
        while True:
            self._event.clear()
            await self.flush()
            try:
                await asyncio.wait_for(self._event.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass

    async def stop(self):
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if not self._closed and self.inbox is not None:
            self.inbox.close()
        if not self._closed and self.history is not None:
            self.history.close()
        self._closed = True

"""Event-driven controller with no idle model polling."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from .protocol import Envelope, MessageKind, SourceKind
from .store import SQLiteStore


@dataclass(slots=True)
class ActionResult:
    accepted: bool
    output: dict[str, Any] = field(default_factory=dict)


class ModelGateway(Protocol):
    async def handle(self, message: Envelope) -> ActionResult:
        ...


class Controller:
    """Dispatches only pending messages that require model reasoning."""

    def __init__(self, store: SQLiteStore, gateway: ModelGateway):
        self.store = store
        self.gateway = gateway
        self.dispatch_blocked = False
        self._paused_at: datetime | None = None
        self._pause_scope: str | None = None
        self._wakeup = asyncio.Event()
        self._stop = asyncio.Event()
        self._serve_task: asyncio.Task[None] | None = None

    async def offer(self, message: Envelope) -> bool:
        accepted = self.store.accept_inbound(message)
        if not accepted:
            return False
        self._apply_control(message)
        self._wakeup.set()
        return True

    async def run_until_idle(self) -> None:
        observed: set[str] = set()
        while True:
            pending = [
                stored
                for stored in self.store.pending_inbound()
                if stored.message.message_id not in observed
            ]
            if not pending:
                return
            for stored in pending:
                message = stored.message
                observed.add(message.message_id)
                if self._is_expired(message):
                    self.store.mark_inbound_processed(message.message_id)
                    continue
                if self._is_control_message(message):
                    self.store.mark_inbound_processed(message.message_id)
                    continue
                if self.dispatch_blocked:
                    continue
                try:
                    await self.gateway.handle(message)
                except Exception as exc:  # noqa: BLE001 - persisted as recovery state
                    self.store.mark_inbound_failed(
                        message.message_id,
                        f"{type(exc).__name__}: {exc}",
                        retry_at=None,
                    )
                    continue
                self.store.mark_inbound_processed(message.message_id)

    async def wait_for_work(self, timeout: float | None = None) -> bool:
        if self.store.pending_inbound():
            return True
        self._wakeup.clear()
        try:
            await asyncio.wait_for(self._wakeup.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return False
        return True

    async def serve(self) -> None:
        self._stop.clear()
        while not self._stop.is_set():
            await self.run_until_idle()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

    async def start(self) -> None:
        if self._serve_task is not None and not self._serve_task.done():
            return
        self._serve_task = asyncio.create_task(self.serve(), name="fpga-mesh-controller")

    async def stop(self) -> None:
        self._stop.set()
        self._wakeup.set()
        if self._serve_task is not None:
            self._serve_task.cancel()
            try:
                await self._serve_task
            except asyncio.CancelledError:
                pass
            self._serve_task = None

    def _is_expired(self, message: Envelope) -> bool:
        return message.expires_at is not None and message.expires_at <= datetime.now(
            timezone.utc
        )

    def _is_control_message(self, message: Envelope) -> bool:
        return (
            message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}
            and message.source == SourceKind.HUMAN
        )

    def _apply_control(self, message: Envelope) -> None:
        if message.source != SourceKind.HUMAN:
            return
        if message.kind == MessageKind.STOP_REQUEST:
            self.dispatch_blocked = True
            self._paused_at = message.sent_at
            self._pause_scope = str(message.payload.get("scope", "all"))
        elif message.kind == MessageKind.RESUME_REQUEST:
            resume_scope = str(message.payload.get("scope", "all"))
            time_is_later = (
                self._paused_at is not None
                and message.sent_at > self._paused_at
            )
            scope_matches = (
                self._pause_scope in {None, "all", resume_scope}
                or resume_scope == "all"
            )
            if time_is_later and scope_matches:
                self.dispatch_blocked = False
                self._paused_at = None
                self._pause_scope = None

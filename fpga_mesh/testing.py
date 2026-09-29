"""Explicit test doubles; callers must label their output as simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

from .controller import ActionResult
from .protocol import Envelope


@dataclass
class RecordingGateway:
    calls: list[str] = field(default_factory=list)

    async def handle(self, message: Envelope) -> ActionResult:
        self.calls.append(message.message_id)
        return ActionResult(accepted=True, output={"message_id": message.message_id})

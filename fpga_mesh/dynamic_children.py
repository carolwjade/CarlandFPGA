"""Native Codex dynamic tools for one Astra's local DeepSeek pool."""

from __future__ import annotations

from copy import deepcopy
from typing import Protocol

from .mcp_children import TOOLS


class ControlClient(Protocol):
    async def call(self, action: str, arguments: dict) -> object: ...


class ChildDynamicTools:
    ACTIONS = {
        "fpga_child_status": "status",
        "fpga_child_scale": "scale",
        "fpga_child_delegate": "delegate",
        "fpga_child_wait": "wait",
        "fpga_child_cancel": "cancel",
    }

    def __init__(self, client: ControlClient):
        self.client = client

    @classmethod
    def specs(cls) -> list[dict]:
        result = []
        for tool in TOOLS:
            copy = deepcopy(tool)
            copy["type"] = "function"
            copy["name"] = f"fpga_{tool['name']}"
            result.append(copy)
        return result

    async def call(self, name: str, arguments: dict) -> object:
        try:
            action = self.ACTIONS[name]
        except KeyError as exc:
            raise ValueError(f"unknown child tool: {name}") from exc
        return await self.client.call(action, arguments)

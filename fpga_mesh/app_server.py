"""Thin Codex app-server adapter pinned to the local protocol contract."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Protocol

from .rpc import JsonRpcSession, StdioTransport


class RpcSession(Protocol):
    async def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        ...

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        ...

    async def close(self) -> None:
        ...


class AppServerClient:
    def __init__(self, session: RpcSession, *, client_version: str):
        self.session = session
        self.client_version = client_version

    async def initialize(self) -> Any:
        return await self.session.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "fpga-mesh",
                    "title": "FPGA multi-agent controller",
                    "version": self.client_version,
                },
                "capabilities": {"experimentalApi": True},
            },
        )

    async def thread_start(
        self,
        *,
        cwd: str,
        model: str,
        model_provider: str,
    ) -> Any:
        return await self.session.request(
            "thread/start",
            {
                "cwd": cwd,
                "model": model,
                "modelProvider": model_provider,
            },
        )

    async def turn_start(
        self,
        *,
        thread_id: str,
        text: str,
        model: str,
        effort: str,
    ) -> Any:
        return await self.session.request(
            "turn/start",
            {
                "threadId": thread_id,
                "model": model,
                "effort": effort,
                "input": [{"type": "text", "text": text}],
            },
        )

    async def account_rate_limits(self) -> Any:
        return await self.session.request("account/rateLimits/read", {})

    async def close(self) -> None:
        await self.session.close()

    @classmethod
    async def start_stdio(
        cls,
        *,
        codex_home: str | Path,
        codex_command: list[str] | None = None,
        client_version: str,
    ) -> "AppServerClient":
        command = codex_command or ["codex", "app-server", "--stdio"]
        if sys.platform == "win32" and command[0].lower() == "codex":
            command = ["cmd.exe", "/d", "/c", *command]
        env = dict(**__import__("os").environ)
        env["CODEX_HOME"] = str(codex_home)
        transport = StdioTransport(command, env=env)
        await transport.start()
        session = JsonRpcSession(transport)
        return cls(session, client_version=client_version)

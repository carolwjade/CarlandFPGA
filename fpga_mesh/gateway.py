"""Codex app-server gateways used only after an actionable event arrives."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Awaitable, Callable, Literal

from .app_server import AppServerClient
from .codex import RouteGuard
from .controller import ActionResult
from .protocol import Envelope


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    node_id: str
    role: Literal["astra", "deepseek_child"]
    model: str
    provider: str
    reasoning_effort: str
    cwd: str
    codex_home: str
    client_version: str = "0.159.0"


class AppServerGateway:
    def __init__(
        self,
        config: GatewayConfig,
        *,
        client_factory: Callable[[], AppServerClient | Awaitable[AppServerClient]]
        | None = None,
        timeout_seconds: float = 300.0,
    ):
        self.config = config
        self.client_factory = client_factory
        self.timeout_seconds = timeout_seconds
        self._client: AppServerClient | None = None
        self._thread_id: str | None = None
        self._lock = asyncio.Lock()
        self._guard = RouteGuard()
        if config.role == "deepseek_child":
            self._guard.assert_child_request(
                model=config.model,
                provider=config.provider,
                effort=config.reasoning_effort,
            )

    async def handle(self, message: Envelope) -> ActionResult:
        async with self._lock:
            client = await self._ensure_client()
            if self._thread_id is None:
                response = await client.thread_start(
                    cwd=self.config.cwd,
                    model=self.config.model,
                    model_provider=self.config.provider,
                )
                self._thread_id = response["thread"]["id"]
            await client.turn_start(
                thread_id=self._thread_id,
                text=str(message.payload.get("text", message.message_id)),
                model=self.config.model,
                effort=self.config.reasoning_effort,
            )
            completed = await asyncio.wait_for(
                self._wait_for_completion(),
                timeout=self.timeout_seconds,
            )
            return ActionResult(
                accepted=True,
                output={
                    "thread_id": self._thread_id,
                    "turn": completed.params.get("turn", {}),
                    "text": self._extract_text(completed.params),
                },
            )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._thread_id = None

    async def _ensure_client(self) -> AppServerClient:
        if self._client is not None:
            return self._client
        if self.client_factory is not None:
            candidate = self.client_factory()
            client = await candidate if inspect.isawaitable(candidate) else candidate
            await client.initialize()
            self._client = client
            return client
        client = await AppServerClient.start_stdio(
            codex_home=self.config.codex_home,
            client_version=self.config.client_version,
        )
        await client.initialize()
        self._client = client
        return client

    async def _wait_for_completion(self):
        while True:
            notification = await self._client.session.next_notification()
            if notification.method in {"turn/completed", "error"}:
                return notification

    @staticmethod
    def _extract_text(params: dict) -> str:
        items = params.get("turn", {}).get("items", [])
        for item in items:
            if item.get("type") == "agentMessage":
                return str(item.get("text", ""))
        return ""

"""Codex app-server gateways used only after an actionable event arrives."""

from __future__ import annotations

import asyncio
import inspect
import json
from dataclasses import dataclass
from typing import Awaitable, Callable, Literal

from .app_server import AppServerClient
from .codex import RouteGuard
from .controller import ActionResult
from .effort import EFFORTS, AstraEffortSelector
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
        thread_config_factory: Callable[[], dict] | None = None,
        dynamic_tools: list[dict] | None = None,
        dynamic_tool_handler: Callable[
            [str, dict], dict | Awaitable[dict]
        ] | None = None,
        effort_selector: AstraEffortSelector | None = None,
        timeout_seconds: float | None = 300.0,
    ):
        self.config = config
        self.client_factory = client_factory
        self.thread_config_factory = thread_config_factory
        self.dynamic_tools = dynamic_tools
        self.dynamic_tool_handler = dynamic_tool_handler
        self.effort_selector = effort_selector
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
            prompt = str(message.payload.get("text", message.message_id))
            effort = self.config.reasoning_effort
            if self.config.role == "astra" and self.effort_selector is not None:
                try:
                    chosen = await self.effort_selector.choose(
                        client, cwd=self.config.cwd, model=self.config.model,
                        text=prompt,
                    )
                except (Exception, asyncio.CancelledError):
                    try:
                        await asyncio.shield(self.close())
                    except Exception:  # noqa: BLE001 - retain selector failure
                        pass
                    raise
                effort = chosen if chosen in EFFORTS else "max"
            if self._thread_id is None:
                response = await self._start_request(client.thread_start(
                    cwd=self.config.cwd,
                    model=self.config.model,
                    model_provider=self.config.provider,
                    config=(self.thread_config_factory()
                            if self.thread_config_factory is not None else None),
                    dynamic_tools=self.dynamic_tools,
                ))
                self._thread_id = response["thread"]["id"]
            started = await self._start_request(client.turn_start(
                thread_id=self._thread_id,
                text=prompt,
                model=self.config.model,
                effort=effort,
            ))
            turn_id = started["turn"]["id"]
            try:
                completed = await asyncio.wait_for(
                    self._wait_for_completion(turn_id),
                    timeout=self.timeout_seconds,
                )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                try:
                    await asyncio.wait_for(client.turn_interrupt(
                        thread_id=self._thread_id, turn_id=turn_id,
                    ), timeout=min(5.0, self.timeout_seconds or 5.0))
                except (Exception, asyncio.CancelledError):
                    pass
                try:
                    await self.close()
                except Exception:  # noqa: BLE001 - keep the original failure
                    pass
                raise
            turn = completed.params.get("turn", {})
            if turn.get("status") != "completed":
                error = turn.get("error") or {}
                detail = (error.get("message") if isinstance(error, dict)
                          else str(error)) or turn.get("status", "unknown")
                raise RuntimeError(f"Codex turn did not complete: {detail}")
            return ActionResult(
                accepted=True,
                output={
                    "thread_id": self._thread_id,
                    "turn": completed.params.get("turn", {}),
                    "text": self._extract_text(completed.params),
                    "reasoning_effort": effort,
                },
            )

    async def close(self) -> None:
        client = self._client
        self._client = None
        self._thread_id = None
        if client is not None:
            await client.close()

    async def _start_request(self, request: Awaitable[dict]) -> dict:
        try:
            return await asyncio.wait_for(request, timeout=self.timeout_seconds)
        except (Exception, asyncio.CancelledError):
            try:
                await asyncio.shield(self.close())
            except Exception:  # noqa: BLE001 - preserve the startup failure
                pass
            raise

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

    async def _wait_for_completion(self, turn_id: str):
        while True:
            notification = await self._client.session.next_notification()
            if notification.method == "item/tool/call":
                await self._handle_dynamic_tool(notification, turn_id)
                continue
            if notification.method == "error":
                raise RuntimeError(str(notification.params.get("message", "Codex error")))
            if notification.method == "turn/completed" and notification.params.get(
                "turn", {},
            ).get("id", turn_id) == turn_id:
                return notification

    async def _handle_dynamic_tool(self, request, turn_id: str) -> None:
        if request.request_id is None:
            raise RuntimeError("dynamic tool request omitted its id")
        try:
            if self.dynamic_tool_handler is None:
                raise RuntimeError("dynamic tools are not enabled")
            if (request.params.get("threadId") != self._thread_id or
                    request.params.get("turnId") != turn_id):
                raise RuntimeError("dynamic tool request targeted another turn")
            name = request.params.get("tool")
            arguments = request.params.get("arguments") or {}
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise ValueError("invalid dynamic tool name or arguments")
            candidate = self.dynamic_tool_handler(name, arguments)
            result = (await candidate if inspect.isawaitable(candidate)
                      else candidate)
            result_text = json.dumps(result, ensure_ascii=True)
            success = True
        except Exception as exc:  # noqa: BLE001 - tool errors return to Astra
            result_text = json.dumps({
                "error": f"{type(exc).__name__}: {exc}",
            }, ensure_ascii=True)
            success = False
        await self._client.session.respond(request.request_id, {
            "contentItems": [{"type": "inputText", "text": result_text}],
            "success": success,
        })

    @staticmethod
    def _extract_text(params: dict) -> str:
        items = params.get("turn", {}).get("items", [])
        messages = [item for item in items if item.get("type") == "agentMessage"]
        for item in reversed(messages):
            if item.get("phase") == "final_answer":
                return str(item.get("text", ""))
        if messages:
            return str(messages[-1].get("text", ""))
        return ""

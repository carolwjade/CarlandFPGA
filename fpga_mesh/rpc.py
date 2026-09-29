"""Minimal asynchronous JSON-RPC 2.0 transport used by Codex app-server."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol


class JsonRpcError(RuntimeError):
    def __init__(self, method: str, error: dict[str, Any]):
        self.method = method
        self.code = error.get("code")
        self.message = error.get("message", "JSON-RPC error")
        super().__init__(f"{method}: [{self.code}] {self.message}")


@dataclass(frozen=True, slots=True)
class JsonRpcNotification:
    method: str
    params: dict[str, Any]


class Transport(Protocol):
    async def send(self, payload: str) -> None:
        ...

    async def recv(self) -> str:
        ...

    async def close(self) -> None:
        ...


class InMemoryTransport:
    """Test transport with explicit client/server queue helpers."""

    def __init__(self) -> None:
        self._client_writes: asyncio.Queue[str] = asyncio.Queue()
        self._server_writes: asyncio.Queue[str] = asyncio.Queue()
        self.closed = False

    async def send(self, payload: str) -> None:
        await self._client_writes.put(payload)

    async def recv(self) -> str:
        return await self._server_writes.get()

    async def close(self) -> None:
        self.closed = True

    async def next_client_message(self) -> str:
        return await self._client_writes.get()

    async def inject_server_message(self, payload: str) -> None:
        await self._server_writes.put(payload)


class JsonRpcSession:
    """Route responses and notifications without coupling to Codex methods."""

    def __init__(self, transport: Transport):
        self.transport = transport
        self._next_id = 1
        self._pending: dict[int, tuple[str, asyncio.Future[Any]]] = {}
        self._notifications: asyncio.Queue[JsonRpcNotification] = asyncio.Queue()
        self._reader = asyncio.create_task(self._read_loop())

    async def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self._next_id
        self._next_id += 1
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = (method, future)
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        await self.transport.send(json.dumps(payload, ensure_ascii=False))
        return await future

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        await self.transport.send(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params or {},
                },
                ensure_ascii=False,
            )
        )

    async def next_notification(self) -> JsonRpcNotification:
        return await self._notifications.get()

    async def close(self) -> None:
        if self._reader is not None:
            self._reader.cancel()
            try:
                await self._reader
            except asyncio.CancelledError:
                pass
            self._reader = None
        await self.transport.close()

    async def _read_loop(self) -> None:
        while True:
            payload = await self.transport.recv()
            if not payload:
                return
            data = json.loads(payload)
            if "id" in data and "method" not in data:
                request_id = int(data["id"])
                entry = self._pending.pop(request_id, None)
                if entry is None:
                    continue
                method, future = entry
                if "error" in data:
                    future.set_exception(JsonRpcError(method, data["error"]))
                else:
                    future.set_result(data.get("result"))
            elif "method" in data:
                await self._notifications.put(
                    JsonRpcNotification(
                        method=data["method"],
                        params=data.get("params") or {},
                    )
                )


class StdioTransport:
    """Async subprocess transport for `codex app-server --stdio`."""

    def __init__(self, command: list[str], *, env: dict[str, str] | None = None):
        self.command = command
        self.env = env
        self.process: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )

    async def send(self, payload: str) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("transport is not started")
        async with self._lock:
            self.process.stdin.write((payload + "\n").encode("utf-8"))
            await self.process.stdin.drain()

    async def recv(self) -> str:
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("transport is not started")
        data = await self.process.stdout.readline()
        return data.decode("utf-8").rstrip("\r\n")

    async def close(self) -> None:
        if self.process is None:
            return
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
        self.process = None

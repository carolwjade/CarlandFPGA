"""HMAC-authenticated HTTP peer transport for Tailscale/local tests."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib import error, request

from .controller import Controller
from .protocol import Envelope
from .store import SQLiteStore


class HttpPeer:
    def __init__(
        self,
        *,
        node_id: str,
        store: SQLiteStore,
        controller: Controller,
        peer_urls: dict[str, str],
        shared_secret: str,
    ):
        self.node_id = node_id
        self.store = store
        self.controller = controller
        self.peer_urls = peer_urls
        self.shared_secret = shared_secret.encode("utf-8")

    async def send(self, peer_id: str, message: Envelope) -> bool:
        self.store.enqueue_outbound(message, peer_id=peer_id)
        return await self.flush()

    async def flush(self) -> bool:
        while True:
            item = self.store.next_outbound()
            if item is None:
                return True
            url = self.peer_urls.get(item.peer_id)
            if not url:
                self.store.mark_outbound_failed(
                    item.message.message_id,
                    f"no URL for peer {item.peer_id}",
                    retry_at=None,
                )
                return False
            delivered = await asyncio.to_thread(
                self._post,
                url,
                item.message.to_json().encode("utf-8"),
            )
            if not delivered:
                self.store.mark_outbound_failed(
                    item.message.message_id,
                    f"peer {item.peer_id} unavailable",
                    retry_at=None,
                )
                return False
            self.store.ack_outbound(item.message.message_id)

    async def receive(self, message: Envelope) -> bool:
        return await self.controller.offer(message)

    def _post(self, url: str, body: bytes) -> bool:
        signature = hmac.new(self.shared_secret, body, hashlib.sha256).hexdigest()
        req = request.Request(
            url.rstrip("/") + "/v1/messages",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-FPGA-Signature": signature,
            },
        )
        try:
            with request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except (error.URLError, TimeoutError, OSError):
            return False


class HttpPeerServer:
    def __init__(
        self,
        peer: HttpPeer,
        *,
        shared_secret: str,
        host: str = "127.0.0.1",
        port: int = 8787,
    ):
        self.peer = peer
        self.shared_secret = shared_secret.encode("utf-8")
        self.host = host
        self.requested_port = port
        self._server: asyncio.AbstractServer | None = None

    @property
    def port(self) -> int:
        if self._server is None or not self._server.sockets:
            raise RuntimeError("server is not started")
        return int(self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle,
            self.host,
            self.requested_port,
        )

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=5)
            if not request_line:
                return
            parts = request_line.decode("latin1").strip().split()
            if len(parts) != 3 or parts[0] != "POST" or parts[1] != "/v1/messages":
                await self._respond(writer, 404, {"error": "not found"})
                return
            headers: dict[str, str] = {}
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=5)
                if line in (b"\r\n", b"\n", b""):
                    break
                name, _, value = line.decode("latin1").partition(":")
                headers[name.strip().lower()] = value.strip()
            length = int(headers.get("content-length", "0"))
            body = await asyncio.wait_for(reader.readexactly(length), timeout=5)
            expected = hmac.new(
                self.shared_secret,
                body,
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(headers.get("x-fpga-signature", ""), expected):
                await self._respond(writer, 401, {"error": "signature"})
                return
            message = Envelope.from_json(body.decode("utf-8"))
            accepted = await self.peer.receive(message)
            await self._respond(writer, 200, {"accepted": accepted})
        except Exception as exc:  # noqa: BLE001 - network boundary
            await self._respond(writer, 400, {"error": type(exc).__name__})
        finally:
            writer.close()
            await writer.wait_closed()

    async def _respond(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        payload: dict,
    ) -> None:
        reason = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 404: "Not Found"}[status]
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = (
            f"HTTP/1.1 {status} {reason}\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode("latin1")
        writer.write(headers + body)
        await writer.drain()

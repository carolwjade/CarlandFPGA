"""Persistent peer delivery transports.

The local bus is the deterministic test double. The same peer interface can be
backed by Tailscale HTTP or an SSH tunnel without changing controller logic.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from .controller import Controller
from .protocol import Envelope
from .store import SQLiteStore


class LocalBus:
    def __init__(self) -> None:
        self._peers: dict[str, "LocalPeer"] = {}

    def register(self, peer: "LocalPeer") -> None:
        self._peers[peer.node_id] = peer

    def unregister(self, node_id: str) -> None:
        self._peers.pop(node_id, None)

    async def deliver(self, node_id: str, message: Envelope) -> bool:
        peer = self._peers.get(node_id)
        if peer is None:
            return False
        return await peer.receive(message)


class LocalPeer:
    def __init__(
        self,
        node_id: str,
        store: SQLiteStore,
        controller: Controller,
        bus: LocalBus,
    ):
        self.node_id = node_id
        self.store = store
        self.controller = controller
        self.bus = bus

    async def send(self, peer_id: str, message: Envelope) -> bool:
        self.store.enqueue_outbound(message, peer_id=peer_id)
        return await self.flush()

    async def flush(self) -> bool:
        while True:
            item = self.store.next_outbound()
            if item is None:
                return True
            delivered = await self.bus.deliver(item.peer_id, item.message)
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

    @property
    def routing_id(self) -> str:
        return f"{self.node_id}/Astra-{self.node_id}"

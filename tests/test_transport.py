import asyncio
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fpga_mesh.controller import ActionResult, Controller
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.store import SQLiteStore
from fpga_mesh.transport import LocalBus, LocalPeer


class CountingGateway:
    def __init__(self):
        self.calls = []

    async def handle(self, message: Envelope) -> ActionResult:
        self.calls.append(message.message_id)
        return ActionResult(accepted=True)


def envelope(message_id: str, recipient: str = "B/Astra-B") -> Envelope:
    return Envelope(
        message_id=message_id,
        project_id="fpga-main",
        sender="A/Astra-A",
        recipient=recipient,
        task_id="task-1",
        task_version=1,
        sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        kind=MessageKind.AGENT_REPORT,
        source=SourceKind.ASTRA,
        payload={"text": "peer update"},
    )


class LocalTransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stores = []

    async def asyncTearDown(self):
        for store in self.stores:
            store.close()
        self.tmp.cleanup()

    def make_peer(self, node_id: str, bus: LocalBus):
        store = SQLiteStore(self.root / f"{node_id}.sqlite")
        self.stores.append(store)
        gateway = CountingGateway()
        controller = Controller(store, gateway)
        peer = LocalPeer(node_id, store, controller, bus)
        bus.register(peer)
        return peer, gateway

    async def test_a_to_b_delivery_acks_sender_and_processes_receiver(self):
        bus = LocalBus()
        a, _ = self.make_peer("A", bus)
        b, b_gateway = self.make_peer("B", bus)

        accepted = await a.send("B", envelope("msg-1"))
        self.assertTrue(accepted)
        await b.controller.run_until_idle()

        self.assertEqual(b_gateway.calls, ["msg-1"])
        self.assertEqual(a.store.pending_outbound(), [])

    async def test_offline_peer_keeps_message_pending_until_reconnect(self):
        bus = LocalBus()
        a, _ = self.make_peer("A", bus)

        self.assertFalse(await a.send("B", envelope("msg-1")))
        self.assertEqual(len(a.store.pending_outbound()), 1)

        b, b_gateway = self.make_peer("B", bus)
        self.assertTrue(await a.flush())
        await b.controller.run_until_idle()
        self.assertEqual(b_gateway.calls, ["msg-1"])
        self.assertEqual(a.store.pending_outbound(), [])

    async def test_duplicate_delivery_is_ignored_by_receiver(self):
        bus = LocalBus()
        _, _ = self.make_peer("A", bus)
        b, b_gateway = self.make_peer("B", bus)

        await bus.deliver("B", envelope("msg-1"))
        await bus.deliver("B", envelope("msg-1"))
        await b.controller.run_until_idle()

        self.assertEqual(b_gateway.calls, ["msg-1"])


if __name__ == "__main__":
    unittest.main()

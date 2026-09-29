import asyncio
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fpga_mesh.controller import ActionResult, Controller
from fpga_mesh.http_transport import HttpPeer, HttpPeerServer
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.store import SQLiteStore


class Gateway:
    def __init__(self):
        self.calls = []

    async def handle(self, message: Envelope) -> ActionResult:
        self.calls.append(message.message_id)
        return ActionResult(accepted=True)


def envelope(message_id: str) -> Envelope:
    return Envelope(
        message_id=message_id,
        project_id="fpga-main",
        sender="A/Astra-A",
        recipient="B/Astra-B",
        task_id="task-1",
        task_version=1,
        sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        kind=MessageKind.AGENT_REPORT,
        source=SourceKind.ASTRA,
        payload={"text": "peer update"},
    )


class HttpPeerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stores = []

    async def asyncTearDown(self):
        for store in self.stores:
            store.close()
        self.tmp.cleanup()

    def make_peer(self, node, urls=None, secret="shared-secret"):
        store = SQLiteStore(self.root / f"{node}.sqlite")
        self.stores.append(store)
        gateway = Gateway()
        controller = Controller(store, gateway)
        peer = HttpPeer(
            node_id=node,
            store=store,
            controller=controller,
            peer_urls=urls or {},
            shared_secret=secret,
        )
        return peer, gateway

    async def test_http_delivery_is_authenticated_and_acked(self):
        b, b_gateway = self.make_peer("B")
        server = HttpPeerServer(b, shared_secret="shared-secret", port=0)
        await server.start()
        try:
            a, _ = self.make_peer(
                "A",
                urls={"B": f"http://127.0.0.1:{server.port}"},
            )
            self.assertTrue(await a.send("B", envelope("msg-1")))
            await b.controller.run_until_idle()
            self.assertEqual(b_gateway.calls, ["msg-1"])
            self.assertEqual(a.store.pending_outbound(), [])
        finally:
            await server.close()

    async def test_bad_hmac_is_rejected_without_processing(self):
        b, b_gateway = self.make_peer("B")
        server = HttpPeerServer(b, shared_secret="right-secret", port=0)
        await server.start()
        try:
            a, _ = self.make_peer(
                "A",
                urls={"B": f"http://127.0.0.1:{server.port}"},
                secret="wrong-secret",
            )
            self.assertFalse(await a.send("B", envelope("msg-1")))
            await b.controller.run_until_idle()
            self.assertEqual(b_gateway.calls, [])
        finally:
            await server.close()


if __name__ == "__main__":
    unittest.main()

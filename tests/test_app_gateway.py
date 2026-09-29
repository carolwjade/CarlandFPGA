import tempfile
import unittest
from pathlib import Path

from fpga_mesh.app_server import AppServerClient
from fpga_mesh.gateway import AppServerGateway, GatewayConfig
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.rpc import JsonRpcNotification
from datetime import datetime, timezone


class FakeSession:
    def __init__(self):
        self.requests = []
        self.notifications = []

    async def request(self, method, params=None):
        self.requests.append((method, params or {}))
        if method == "thread/start":
            return {"thread": {"id": "thread-1"}}
        if method == "turn/start":
            return {"turn": {"id": "turn-1"}}
        return {}

    async def notify(self, method, params=None):
        self.requests.append((method, params or {}))

    async def next_notification(self):
        return self.notifications.pop(0)

    async def close(self):
        self.requests.append(("close", {}))


def message() -> Envelope:
    return Envelope(
        message_id="msg-1",
        project_id="fpga-main",
        sender="human-1",
        recipient="A/Astra-A",
        task_id="task-1",
        task_version=1,
        sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        kind=MessageKind.HUMAN_INSTRUCTION,
        source=SourceKind.HUMAN,
        payload={"text": "inspect"},
    )


class AppServerGatewayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = FakeSession()
        self.client = AppServerClient(self.session, client_version="0.159.0")
        self.config = GatewayConfig(
            node_id="A",
            role="astra",
            model="gpt-6-astra",
            provider="openai",
            reasoning_effort="max",
            cwd=str(Path.cwd()),
            codex_home=str(Path(self.tmp.name)),
        )
        self.gateway = AppServerGateway(
            self.config,
            client_factory=lambda: self.client,
        )

    async def asyncTearDown(self):
        await self.gateway.close()
        self.tmp.cleanup()

    async def test_no_model_call_until_a_message_is_handled(self):
        self.assertEqual(self.session.requests, [])
        self.session.notifications.append(
            JsonRpcNotification(
                method="turn/completed",
                params={
                    "turn": {
                        "status": "completed",
                        "items": [{"type": "agentMessage", "text": "done"}],
                    }
                },
            )
        )
        result = await self.gateway.handle(message())
        self.assertTrue(result.accepted)
        self.assertEqual(result.output["text"], "done")

    async def test_second_message_reuses_the_same_thread(self):
        self.session.notifications.extend(
            [
                JsonRpcNotification(
                    method="turn/completed",
                    params={"turn": {"status": "completed", "items": []}},
                ),
                JsonRpcNotification(
                    method="turn/completed",
                    params={"turn": {"status": "completed", "items": []}},
                ),
            ]
        )
        await self.gateway.handle(message())
        await self.gateway.handle(message())
        methods = [method for method, _ in self.session.requests]
        self.assertEqual(methods.count("initialize"), 1)
        self.assertEqual(methods.count("thread/start"), 1)
        self.assertEqual(methods.count("turn/start"), 2)

    async def test_child_gateway_uses_provider_and_max_from_config(self):
        config = GatewayConfig(
            node_id="A",
            role="deepseek_child",
            model="deepseek-flash",
            provider="deepseek",
            reasoning_effort="max",
            cwd=str(Path.cwd()),
            codex_home=str(Path(self.tmp.name)),
        )
        gateway = AppServerGateway(config, client_factory=lambda: self.client)
        self.session.notifications.append(
            JsonRpcNotification(
                method="turn/completed",
                params={"turn": {"status": "completed", "items": []}},
            )
        )
        await gateway.handle(message())
        turn = [
            params
            for method, params in self.session.requests
            if method == "turn/start"
        ][0]
        self.assertEqual(turn["model"], "deepseek-flash")
        self.assertEqual(turn["effort"], "max")
        await gateway.close()


if __name__ == "__main__":
    unittest.main()

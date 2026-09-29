import tempfile
import unittest
from pathlib import Path

from fpga_mesh.codex import CodexHomeFactory
from fpga_mesh.controller import ActionResult
from fpga_mesh.pool import InstancePool
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from datetime import datetime, timezone


class CountingGateway:
    def __init__(self):
        self.calls = []

    async def handle(self, message: Envelope) -> ActionResult:
        self.calls.append(message.message_id)
        return ActionResult(accepted=True)


def message(message_id: str) -> Envelope:
    return Envelope(
        message_id=message_id,
        project_id="fpga-main",
        sender="A/Astra-A",
        recipient="A/DeepSeek-A",
        task_id="task-1",
        task_version=1,
        sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        kind=MessageKind.DELEGATION,
        source=SourceKind.ASTRA,
        payload={"work": "inspect"},
    )


class InstancePoolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.gateway = CountingGateway()
        self.pool = InstancePool(
            node_id="A",
            gateway=self.gateway,
            home_factory=CodexHomeFactory(self.root / "homes"),
            state_path=self.root / "pool.json",
        )

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_standby_instances_are_config_ready_without_model_calls(self):
        await self.pool.ensure_standby(2)
        snapshot = self.pool.snapshot()
        self.assertEqual(snapshot["standby"], 2)
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(
            {item["model"] for item in snapshot["instances"]},
            {"deepseek-flash"},
        )

    async def test_scale_up_uses_new_ids_and_reap_does_not_reuse_them(self):
        await self.pool.ensure_standby(1)
        await self.pool.scale_to(3)
        ids = [item["instance_id"] for item in self.pool.snapshot()["instances"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 3)

        await self.pool.reap(ids[0])
        await self.pool.scale_to(3)
        after = [item["instance_id"] for item in self.pool.snapshot()["instances"]]
        self.assertNotIn(ids[0], after)
        self.assertEqual(len(after), 3)
        self.assertEqual(self.gateway.calls, [])

    async def test_wake_runs_exactly_one_delegated_child(self):
        await self.pool.ensure_standby(2)
        instance_id = self.pool.snapshot()["instances"][0]["instance_id"]

        result = await self.pool.wake(instance_id, message("delegate-1"))

        self.assertTrue(result.accepted)
        self.assertEqual(self.gateway.calls, ["delegate-1"])
        self.assertEqual(self.pool.snapshot()["working"], 1)

    async def test_pool_state_survives_restart(self):
        await self.pool.ensure_standby(2)
        before = self.pool.snapshot()

        restarted = InstancePool(
            node_id="A",
            gateway=self.gateway,
            home_factory=CodexHomeFactory(self.root / "homes"),
            state_path=self.root / "pool.json",
        )
        after = restarted.snapshot()

        self.assertEqual(
            [item["instance_id"] for item in before["instances"]],
            [item["instance_id"] for item in after["instances"]],
        )
        self.assertEqual(after["standby"], 2)

    async def test_each_child_gets_an_independent_gateway_kept_across_wakes(self):
        gateways = []

        def factory(instance):
            gateway = CountingGateway()
            gateways.append(gateway)
            return gateway

        pool = InstancePool(
            node_id="B",
            gateway=None,
            gateway_factory=factory,
            home_factory=CodexHomeFactory(self.root / "homes-b"),
            state_path=self.root / "pool-b.json",
        )
        await pool.ensure_standby(2)
        ids = [item["instance_id"] for item in pool.snapshot()["instances"]]
        await pool.wake(ids[0], message("first"))
        await pool.wake(ids[0], message("second"))
        await pool.wake(ids[1], message("third"))
        self.assertEqual(len(gateways), 2)
        self.assertEqual(gateways[0].calls, ["first", "second"])
        self.assertEqual(gateways[1].calls, ["third"])


if __name__ == "__main__":
    unittest.main()

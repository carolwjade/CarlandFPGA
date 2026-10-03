import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.child_control import ChildCoordinator, LocalControlServer, LocalControlClient
from fpga_mesh.codex import CodexHomeFactory
from fpga_mesh.controller import ActionResult
from fpga_mesh.pool import InstancePool


class DelayedGateway:
    def __init__(self):
        self.started = asyncio.Queue()
        self.release = asyncio.Event()
        self.calls = []

    async def handle(self, message):
        self.calls.append(message)
        await self.started.put(message.message_id)
        await self.release.wait()
        return ActionResult(accepted=True, output={"text": message.payload["text"]})


class ChildCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.gateway = DelayedGateway()
        self.pool = InstancePool(
            node_id="A",
            gateway=self.gateway,
            home_factory=CodexHomeFactory(root / "homes"),
            state_path=root / "pool.json",
        )
        await self.pool.ensure_standby(2)
        self.coordinator = ChildCoordinator(
            node_id="A", project_id="fpga-main", pool=self.pool,
            state_path=root / "jobs.sqlite",
        )

    async def asyncTearDown(self):
        await self.coordinator.close()
        self.temp.cleanup()

    async def test_two_jobs_run_in_parallel_and_wait_returns_distinct_results(self):
        first = await self.coordinator.delegate(
            task_id="fpga-1", task_version=1, text="timing report",
        )
        second = await self.coordinator.delegate(
            task_id="fpga-1", task_version=1, text="constraint review",
        )
        await asyncio.wait_for(self.gateway.started.get(), 1)
        await asyncio.wait_for(self.gateway.started.get(), 1)
        self.assertNotEqual(first["instance_id"], second["instance_id"])
        self.assertEqual(len(self.gateway.calls), 2)
        self.assertFalse(self.coordinator.job(first["job_id"])["terminal"])
        self.gateway.release.set()
        results = await asyncio.wait_for(
            self.coordinator.wait([first["job_id"], second["job_id"]]), 1,
        )
        self.assertEqual([r["result"]["text"] for r in results],
                         ["timing report", "constraint review"])
        self.assertEqual(self.pool.snapshot()["standby"], 2)

    async def test_dynamic_growth_keeps_max_and_rejects_busy_reap(self):
        jobs = []
        for index in range(3):
            jobs.append(await self.coordinator.delegate(
                task_id="fpga-2", task_version=1, text=f"job {index}",
                auto_expand=True,
            ))
        for _ in range(3):
            await asyncio.wait_for(self.gateway.started.get(), 1)
        self.assertEqual(len(self.pool.snapshot()["instances"]), 3)
        with self.assertRaises(RuntimeError):
            await self.pool.reap(jobs[0]["instance_id"])
        self.assertEqual({item["reasoning_effort"] for item in self.pool.snapshot()["instances"]}, {"max"})
        self.gateway.release.set()
        await self.coordinator.wait([job["job_id"] for job in jobs])

    async def test_newer_human_version_marks_old_result_stale(self):
        job = await self.coordinator.delegate(
            task_id="fpga-3", task_version=1, text="old plan",
        )
        await asyncio.wait_for(self.gateway.started.get(), 1)
        self.coordinator.update_task_version("fpga-3", 2)
        self.gateway.release.set()
        result = (await self.coordinator.wait([job["job_id"]]))[0]
        self.assertTrue(result["stale"])
        self.assertEqual(result["task_version"], 1)

    async def test_newer_version_rejects_an_old_assignment(self):
        self.coordinator.update_task_version("fpga-3-new", 2)
        with self.assertRaisesRegex(ValueError, "stale"):
            await self.coordinator.delegate(
                task_id="fpga-3-new", task_version=1, text="obsolete work",
            )
        self.assertEqual(len(self.coordinator.status()["jobs"]), 0)
        self.assertEqual(self.pool.snapshot()["standby"], 2)

    async def test_completed_result_survives_coordinator_restart(self):
        job = await self.coordinator.delegate(
            task_id="fpga-4", task_version=1, text="saved result",
        )
        await asyncio.wait_for(self.gateway.started.get(), 1)
        self.gateway.release.set()
        await self.coordinator.wait([job["job_id"]])
        restarted = ChildCoordinator(
            node_id="A", project_id="fpga-main", pool=self.pool,
            state_path=Path(self.temp.name) / "jobs.sqlite",
        )
        try:
            self.assertEqual(restarted.job(job["job_id"])["result"]["text"], "saved result")
        finally:
            await restarted.close()

    async def test_cancel_stops_job_and_does_not_reassign_other_child(self):
        job = await self.coordinator.delegate(
            task_id="fpga-5", task_version=1, text="cancel me",
        )
        await asyncio.wait_for(self.gateway.started.get(), 1)
        await self.coordinator.cancel(job["job_id"])
        result = (await self.coordinator.wait([job["job_id"]]))[0]
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(self.pool.snapshot()["standby"], 2)

    async def test_concurrent_assignments_claim_different_children(self):
        jobs = await asyncio.gather(*(
            self.coordinator.delegate(task_id="fpga-6", task_version=1,
                                      text=f"part {index}")
            for index in range(2)
        ))
        self.assertNotEqual(jobs[0]["instance_id"], jobs[1]["instance_id"])
        self.gateway.release.set()
        await self.coordinator.wait([job["job_id"] for job in jobs])

    async def test_scale_waits_for_in_progress_child_claim(self):
        original_reserve = self.pool.reserve
        entered = asyncio.Event()
        release_claim = asyncio.Event()

        async def paused_reserve(instance_id):
            entered.set()
            await release_claim.wait()
            await original_reserve(instance_id)

        self.pool.reserve = paused_reserve
        claim = asyncio.create_task(self.coordinator.delegate(
            task_id="race", task_version=1, text="claim first",
        ))
        await asyncio.wait_for(entered.wait(), 1)
        scale = asyncio.create_task(self.coordinator.scale(1))
        await asyncio.sleep(0)
        self.assertFalse(scale.done())
        release_claim.set()
        job = await asyncio.wait_for(claim, 1)
        await asyncio.wait_for(scale, 1)
        self.assertIn(job["instance_id"], [
            item["instance_id"] for item in self.pool.snapshot()["instances"]
        ])
        self.gateway.release.set()
        await self.coordinator.wait([job["job_id"]])

    async def test_human_version_change_during_claim_blocks_stale_dispatch(self):
        original_reserve = self.pool.reserve
        entered = asyncio.Event()
        release_claim = asyncio.Event()

        async def paused_reserve(instance_id):
            entered.set()
            await release_claim.wait()
            await original_reserve(instance_id)

        self.pool.reserve = paused_reserve
        claim = asyncio.create_task(self.coordinator.delegate(
            task_id="human-update", task_version=1, text="old task",
        ))
        await asyncio.wait_for(entered.wait(), 1)
        self.coordinator.update_task_version("human-update", 2)
        release_claim.set()
        with self.assertRaisesRegex(ValueError, "stale"):
            await claim
        self.assertEqual(self.pool.snapshot()["standby"], 2)
        self.assertEqual(self.coordinator.status()["jobs"], [])

    async def test_loopback_tool_bridge_authenticates_and_waits_for_result(self):
        server = LocalControlServer(self.coordinator, token="a-private-token")
        await server.start()
        try:
            client = LocalControlClient(host="127.0.0.1", port=server.port,
                                        token="a-private-token")
            initial = await client.call("status", {})
            self.assertEqual(initial["pool"]["standby"], 2)
            delegated = await client.call("delegate", {
                "task_id": "fpga-7", "task_version": 1, "text": "analyze timing",
            })
            await asyncio.wait_for(self.gateway.started.get(), 1)
            waiting = asyncio.create_task(client.call("wait", {
                "job_ids": [delegated["job_id"]],
            }))
            await asyncio.sleep(0)
            self.assertFalse(waiting.done())
            self.gateway.release.set()
            result = await asyncio.wait_for(waiting, 1)
            self.assertEqual(result[0]["result"]["text"], "analyze timing")
            bad_client = LocalControlClient(host="127.0.0.1", port=server.port,
                                            token="wrong")
            with self.assertRaises(PermissionError):
                await bad_client.call("status", {})
        finally:
            await server.close()

    async def test_discovery_file_follows_server_lifecycle_and_supports_client(self):
        path = Path(self.temp.name) / "control.json"
        server = LocalControlServer(
            self.coordinator, token="fresh-token", discovery_path=path,
        )
        await server.start()
        try:
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["port"],
                             server.port)
            result = await LocalControlClient.from_discovery_file(path).call(
                "status", {},
            )
            self.assertEqual(result["pool"]["standby"], 2)
        finally:
            await server.close()
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()

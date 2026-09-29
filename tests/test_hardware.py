import asyncio
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.hardware import (
    FakeHardwareAdapter,
    HardwareConflict,
    HardwareRequest,
    HardwareService,
)


class HardwareServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "hardware.sqlite"
        self.service = HardwareService(self.path)

    async def asyncTearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def request(self, operation_id="op-1", commit="abc123") -> HardwareRequest:
        return HardwareRequest(
            operation_id=operation_id,
            task_id="task-1",
            task_version=1,
            requester="A/Astra-A",
            code_commit=commit,
            test_steps=["run smoke"],
            expected_result="pass",
        )

    async def test_submit_is_idempotent_by_operation_id_and_request_hash(self):
        first = self.service.submit(self.request())
        second = self.service.submit(self.request())
        self.assertEqual(first.operation_id, second.operation_id)
        self.assertEqual(len(self.service.queue()), 1)

        with self.assertRaises(HardwareConflict):
            self.service.submit(self.request(commit="different"))

    async def test_experiments_are_serialized_even_when_requested_concurrently(self):
        self.service.submit(self.request("op-1"))
        self.service.submit(self.request("op-2"))
        adapter = FakeHardwareAdapter(delay=0.02)

        results = await asyncio.gather(
            self.service.run_next(adapter),
            self.service.run_next(adapter),
        )
        self.assertEqual(adapter.max_active, 1)
        self.assertEqual({result.operation_id for result in results}, {"op-1", "op-2"})

    async def test_stop_request_reaches_safe_point_and_cancels_execution(self):
        self.service.submit(self.request("op-1"))
        adapter = FakeHardwareAdapter(delay=0.3)
        running = asyncio.create_task(self.service.run_next(adapter))
        await asyncio.sleep(0.03)
        requested = self.service.request_stop("op-1")
        self.assertTrue(requested)
        result = await running
        self.assertEqual(result.state, "cancelled")
        self.assertTrue(adapter.stop_seen)

    async def test_restart_marks_an_interrupted_running_operation_unknown(self):
        self.service.submit(self.request("op-1"))
        self.service._mark_running_for_test("op-1")
        self.service.close()

        reopened = HardwareService(self.path)
        self.service = reopened
        self.assertEqual(reopened.recover_unknown(), ["op-1"])
        with self.assertRaises(HardwareConflict):
            await reopened.run_next(FakeHardwareAdapter())


if __name__ == "__main__":
    unittest.main()

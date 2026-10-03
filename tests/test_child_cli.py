import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.child_control import ChildCoordinator, LocalControlServer
from fpga_mesh.codex import CodexHomeFactory
from fpga_mesh.controller import ActionResult
from fpga_mesh.pool import InstancePool


class Gateway:
    async def handle(self, message):
        return ActionResult(accepted=True, output={"text": message.payload["text"]})


class ChildCliTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        pool = InstancePool(
            node_id="A", gateway=Gateway(),
            home_factory=CodexHomeFactory(root / "homes"),
            state_path=root / "pool.json",
        )
        await pool.ensure_standby(1)
        self.coordinator = ChildCoordinator(
            node_id="A", project_id="fpga-main", pool=pool,
            state_path=root / "jobs.sqlite",
        )
        self.control_file = root / "control.json"
        self.server = LocalControlServer(
            self.coordinator, token="private", discovery_path=self.control_file,
        )
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.close()
        await self.coordinator.close()
        self.temp.cleanup()

    async def _call(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "fpga_mesh.child_cli",
            "--control-file", str(self.control_file), *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, env=env,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), 3)
        self.assertEqual(process.returncode, 0, stderr.decode(errors="replace"))
        return json.loads(stdout.decode("utf-8"))

    async def test_cli_delegates_and_waits_for_a_chinese_result(self):
        initial = await self._call("status")
        self.assertEqual(initial["pool"]["standby"], 1)
        job = await self._call("delegate", "--task-id", "t-1",
                               "--task-version", "1", "--text", "检查时序")
        result = await self._call("wait", "--job-id", job["job_id"])
        self.assertEqual(result[0]["result"]["text"], "检查时序")
        self.assertEqual((await self._call("status"))["pool"]["standby"], 1)


if __name__ == "__main__":
    unittest.main()

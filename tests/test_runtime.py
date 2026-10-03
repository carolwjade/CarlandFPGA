import tempfile
import unittest
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from fpga_mesh.runtime import NodeConfig, NodeRuntime
from fpga_mesh.child_control import LocalControlClient
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind


class NodeRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "node-a.toml"
        self.config_path.write_text(
            "\n".join(
                [
                    'node_id = "A"',
                    'project_id = "fpga-main"',
                    'state_dir = "state"',
                    "default_children = 2",
                    'mode = "test_double"',
                    "hardware_enabled = false",
                    "[peers]",
                    'B = ""',
                    'C = ""',
                    "[security]",
                    'secret_env = "FPGA_MESH_SHARED_SECRET"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_runtime_starts_idle_with_two_standby_children(self):
        config = NodeConfig.load(self.config_path)
        runtime = NodeRuntime(config)
        await runtime.start()
        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["node_id"], "A")
        self.assertEqual(snapshot["pool"]["standby"], 2)
        self.assertEqual(snapshot["pending_inbound"], 0)
        self.assertEqual(snapshot["idle_model_calls"], 0)
        await runtime.stop()

    async def test_parent_tool_bridge_reaches_runtime_child_pool(self):
        runtime = NodeRuntime(NodeConfig.load(self.config_path))
        await runtime.start()
        try:
            client = LocalControlClient(
                host="127.0.0.1", port=runtime.child_control.port,
                token=runtime.child_control.token,
            )
            assigned = await client.call("delegate", {
                "task_id": "fpga-test", "task_version": 1,
                "text": "inspect constraints",
            })
            results = await client.call("wait", {"job_ids": [assigned["job_id"]]})
            self.assertEqual(results[0]["status"], "completed")
            self.assertEqual(results[0]["instance_id"], assigned["instance_id"])
            self.assertEqual(runtime.snapshot()["pool"]["standby"], 2)
        finally:
            await runtime.stop()

    async def test_live_parent_config_advertises_local_mcp_and_uses_chatgpt_home(self):
        config = NodeConfig.load(self.config_path)
        runtime = NodeRuntime(config)
        await runtime.start()
        try:
            mcp = runtime.astra_tool_config()["mcp_servers"]["fpga_children"]
            self.assertEqual(mcp["command"], sys.executable)
            self.assertEqual(mcp["args"], ["-m", "fpga_mesh.mcp_children"])
            self.assertEqual(mcp["env"]["FPGA_CHILD_CONTROL_FILE"],
                             str(config.state_dir / "child-control.json"))
            self.assertNotIn("DEEPSEEK_API_KEY", mcp["env"])
            self.assertEqual(
                {tool["name"] for tool in runtime.dynamic_children.specs()},
                {"fpga_child_status", "fpga_child_scale", "fpga_child_delegate",
                 "fpga_child_wait", "fpga_child_cancel"},
            )
        finally:
            await runtime.stop()

    async def test_new_human_task_version_invalidates_old_child_assignment(self):
        runtime = NodeRuntime(NodeConfig.load(self.config_path))
        await runtime.start()
        try:
            first = await runtime.children.delegate(
                task_id="new-plan", task_version=1, text="old work",
            )
            await runtime.children.wait([first["job_id"]])
            await runtime.controller.offer(Envelope(
                message_id="human-new-plan", project_id="fpga-main",
                sender="human", recipient="A/Astra-A",
                task_id="new-plan", task_version=2,
                sent_at=datetime.now(timezone.utc),
                kind=MessageKind.HUMAN_INSTRUCTION,
                source=SourceKind.HUMAN, payload={"text": "new plan"},
            ))
            self.assertTrue(runtime.children.job(first["job_id"])["stale"])
            with self.assertRaisesRegex(ValueError, "stale"):
                await runtime.children.delegate(
                    task_id="new-plan", task_version=1, text="obsolete",
                )
        finally:
            await runtime.stop()

    async def test_real_parent_and_child_have_finite_turn_watchdogs(self):
        config = replace(NodeConfig.load(self.config_path), mode="app_server",
                         turn_timeout_seconds=1800)
        runtime = NodeRuntime(config)
        try:
            self.assertEqual(runtime.astra_gateway.timeout_seconds, 1800)
            await runtime.pool.ensure_standby(1)
            child = runtime.pool.snapshot()["instances"][0]
            gateway = runtime._make_child_gateway(
                runtime.pool._active[child["instance_id"]]
            )
            self.assertEqual(gateway.timeout_seconds, 1800)
        finally:
            await runtime.stop()


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from fpga_mesh.runtime import NodeConfig, NodeRuntime


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


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_simulate_runs_three_local_nodes_without_real_model_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "simulation.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "fpga_mesh.cli",
                    "simulate",
                    "--root",
                    str(root / "state"),
                    "--output",
                    str(output),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["mode"], "local_test_double")
            self.assertEqual(data["nodes"], ["A", "B", "C"])
            self.assertEqual(data["pending_outbox_total"], 0)
            self.assertEqual(data["idle_model_calls"], 0)
            self.assertEqual(
                set(data["model_calls_by_node"]),
                {"A", "B", "C"},
            )

    def test_init_configs_creates_three_non_secret_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "fpga_mesh.cli",
                    "init-configs",
                    "--output",
                    str(root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            files = sorted(path.name for path in root.glob("node-*.toml"))
            self.assertEqual(files, ["node-a.toml", "node-b.toml", "node-c.toml"])
            combined = "\n".join(
                (root / name).read_text(encoding="utf-8")
                for name in files
            )
            self.assertNotIn("sk-", combined)
            self.assertIn('secret_env = "FPGA_MESH_SHARED_SECRET"', combined)


if __name__ == "__main__":
    unittest.main()

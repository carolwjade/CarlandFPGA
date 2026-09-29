import subprocess
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.git_manager import GitRepositoryManager


class GitRepositoryManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote = self.root / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(self.remote)],
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_checkpoint_pushes_and_retry_preserves_local_commit(self):
        repo = self.root / "repo"
        manager = GitRepositoryManager(
            repo,
            remote_url=str(self.remote),
            node_id="A",
            author_name="Node A",
            author_email="a@example.invalid",
        )
        manager.initialize()
        manager.ensure_task_branch("task-1")
        (repo / "result.txt").write_text("first\n", encoding="utf-8")
        first = manager.checkpoint(["result.txt"], "task checkpoint", state="working")
        pushed = manager.push()
        self.assertTrue(pushed.ok)
        self.assertIsNotNone(first)

        (repo / "result.txt").write_text("second\n", encoding="utf-8")
        second = manager.checkpoint(["result.txt"], "second checkpoint", state="working")
        manager.remote_url = str(self.root / "missing-remote.git")
        failed = manager.push()
        self.assertFalse(failed.ok)
        self.assertIsNotNone(second)
        self.assertTrue((repo / ".git").exists())

        manager.remote_url = str(self.remote)
        retried = manager.push()
        self.assertTrue(retried.ok)
        remote_refs = subprocess.run(
            ["git", "--git-dir", str(self.remote), "show-ref"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("codex/a/task-1", remote_refs)

    def test_large_artifact_manifest_records_size_and_sha256(self):
        repo = self.root / "manifest-repo"
        manager = GitRepositoryManager(
            repo,
            remote_url=str(self.remote),
            node_id="A",
            author_name="Node A",
            author_email="a@example.invalid",
        )
        manager.initialize()
        artifact = repo / "wave.vcd"
        artifact.write_bytes(b"abc")

        manifest = manager.artifact_manifest([artifact])

        self.assertEqual(
            manifest["wave.vcd"]["sha256"],
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        self.assertEqual(manifest["wave.vcd"]["size"], 3)


if __name__ == "__main__":
    unittest.main()

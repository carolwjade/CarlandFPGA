import asyncio
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.ownership import GitOwnershipLedger


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True, text=True)


class GitOwnershipLedgerTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_fast_forward_claim_wins_and_other_node_observes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            work = root / "seed"
            work.mkdir()
            git(root, "init", "--bare", str(remote))
            git(work, "init")
            (work / "README.md").write_text("seed\n", encoding="utf-8")
            git(work, "add", "README.md")
            git(work, "-c", "user.name=Test", "-c", "user.email=test@local",
                "commit", "-m", "seed")
            git(work, "branch", "-M", "main")
            git(work, "remote", "add", "origin", str(remote))
            git(work, "push", "origin", "main")
            a = GitOwnershipLedger(remote_url=str(remote),
                                   scratch_root=root / "a-scratch")
            b = GitOwnershipLedger(remote_url=str(remote),
                                   scratch_root=root / "b-scratch")
            self.assertEqual(await a.claim(task_id="task-1",
                                           source_message_id="om_1", node_id="A"), "A")
            self.assertEqual(await b.claim(task_id="task-1",
                                           source_message_id="om_1", node_id="B"), "A")
            records = subprocess.run(
                ["git", "--git-dir", str(remote), "show",
                 "refs/heads/codex/coordination:claims.jsonl"],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines()
            self.assertEqual(len(records), 1)
            self.assertEqual(json.loads(records[0])["owner"], "A")

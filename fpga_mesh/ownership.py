"""Append-only Git ownership claims for unaddressed Feishu tasks.

Only a confirmed fast-forward push grants execution rights. A node without
write access keeps the instruction queued instead of guessing ownership.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


class GitOwnershipLedger:
    def __init__(
        self, *, remote_url: str, scratch_root: Path,
        branch: str = "codex/coordination", timeout_seconds: float = 20,
    ) -> None:
        if not remote_url or not branch.startswith("codex/"):
            raise ValueError("a remote and coordination branch are required")
        self.remote_url = remote_url
        self.scratch_root = Path(scratch_root)
        self.branch = branch
        self.timeout_seconds = timeout_seconds

    async def claim(
        self, *, task_id: str, source_message_id: str, node_id: str,
    ) -> str | None:
        if node_id not in {"A", "B", "C"} or not task_id or not source_message_id:
            raise ValueError("valid task, source message and node are required")
        return await asyncio.to_thread(
            self._claim_sync, task_id, source_message_id, node_id,
        )

    def _claim_sync(self, task_id: str, source_message_id: str, node_id: str) -> str | None:
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        root = self.scratch_root.resolve()
        for _ in range(3):
            with tempfile.TemporaryDirectory(prefix="claim-", dir=root) as tmp:
                checkout = Path(tmp).resolve()
                if not checkout.is_relative_to(root):
                    raise RuntimeError("coordination scratch escaped its root")
                if not self._git(checkout, "init", "-q"):
                    return None
                if not self._git(checkout, "remote", "add", "origin", self.remote_url):
                    return None
                branch_ref = f"refs/heads/{self.branch}"
                if not self._git(checkout, "fetch", "-q", "origin", branch_ref):
                    if not self._git(checkout, "fetch", "-q", "origin", "refs/heads/main"):
                        return None
                if not self._git(checkout, "checkout", "--detach", "-q", "FETCH_HEAD"):
                    return None
                ledger_path = checkout / "claims.jsonl"
                if ledger_path.exists():
                    for line in ledger_path.read_text(encoding="utf-8").splitlines():
                        claim = json.loads(line)
                        if claim.get("task_id") == task_id:
                            return str(claim["owner"])
                record = {
                    "task_id": task_id,
                    "source_sha256": hashlib.sha256(
                        source_message_id.encode("utf-8")
                    ).hexdigest(),
                    "owner": node_id,
                    "version": 1,
                }
                with ledger_path.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(record, sort_keys=True) + "\n")
                if not self._git(checkout, "add", "claims.jsonl"):
                    return None
                if not self._git(
                    checkout, "-c", "user.name=FPGA Mesh",
                    "-c", "user.email=fpga-mesh@local",
                    "commit", "-qm", f"Claim task {task_id[:12]} for {node_id}",
                ):
                    return None
                if self._git(checkout, "push", "origin", f"HEAD:{branch_ref}"):
                    return node_id
                # A competing writer may have won; the next fresh fetch reads
                # its record. A permission or network failure leaves no claim.
        return None

    def _git(self, cwd: Path, *args: str) -> bool:
        environment = dict(os.environ)
        environment["GIT_TERMINAL_PROMPT"] = "0"
        environment["GCM_INTERACTIVE"] = "Never"
        try:
            result = subprocess.run(
                ["git", *args], cwd=cwd, env=environment,
                capture_output=True, text=True, timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

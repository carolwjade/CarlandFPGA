"""Git checkpoint, branch and push helpers for per-node task work."""

from __future__ import annotations

import os
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitCommandError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PushResult:
    ok: bool
    error: str = ""
    output: str = ""


class GitRepositoryManager:
    def __init__(
        self,
        root: str | Path,
        *,
        remote_url: str,
        node_id: str,
        author_name: str,
        author_email: str,
    ):
        if node_id not in {"A", "B", "C"}:
            raise ValueError("node_id must be A, B, or C")
        self.root = Path(root)
        self.remote_url = remote_url
        self.node_id = node_id
        self.author_name = author_name
        self.author_email = author_email

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not (self.root / ".git").exists():
            self._run(["git", "init"], check=True)
        self._run(["git", "config", "user.name", self.author_name], check=True)
        self._run(["git", "config", "user.email", self.author_email], check=True)
        if (
            self._run(
                ["git", "rev-parse", "--verify", "HEAD"],
                check=False,
            ).returncode
            != 0
        ):
            (self.root / ".gitkeep").write_text("", encoding="utf-8")
            self._run(["git", "add", ".gitkeep"], check=True)
            self._run(["git", "commit", "-m", "initial checkpoint"], check=True)
        remotes = self._run(["git", "remote"], check=True).stdout.split()
        if "origin" not in remotes:
            self._run(["git", "remote", "add", "origin", self.remote_url], check=True)
        else:
            self._run(["git", "remote", "set-url", "origin", self.remote_url], check=True)

    def ensure_task_branch(self, task_id: str) -> str:
        branch = f"codex/{self.node_id.lower()}/{task_id}"
        exists = (
            self._run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
                check=False,
            ).returncode
            == 0
        )
        if exists:
            self._run(["git", "checkout", branch], check=True)
        else:
            self._run(["git", "checkout", "-b", branch], check=True)
        return branch

    def checkpoint(
        self,
        paths: list[str],
        message: str,
        *,
        state: str,
    ) -> str | None:
        if not paths:
            return None
        self._run(["git", "add", "--", *paths], check=True)
        diff = self._run(["git", "diff", "--cached", "--quiet"], check=False)
        if diff.returncode == 0:
            return None
        self._run(
            ["git", "commit", "-m", f"{state}: {message}"],
            check=True,
        )
        return self._run(["git", "rev-parse", "HEAD"], check=True).stdout.strip()

    def push(self) -> PushResult:
        self._run(
            ["git", "remote", "set-url", "origin", self.remote_url],
            check=True,
        )
        result = self._run(
            ["git", "push", "-u", "origin", "HEAD"],
            check=False,
        )
        return PushResult(
            ok=result.returncode == 0,
            error=result.stderr.strip() if result.returncode else "",
            output=result.stdout.strip(),
        )

    def current_branch(self) -> str:
        return self._run(["git", "branch", "--show-current"], check=True).stdout.strip()

    def artifact_manifest(self, paths: list[str | Path]) -> dict[str, dict]:
        manifest: dict[str, dict] = {}
        for raw_path in paths:
            path = Path(raw_path)
            if not path.is_absolute():
                path = self.root / path
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
            try:
                key = path.resolve().relative_to(self.root.resolve()).as_posix()
            except ValueError:
                key = path.name
            manifest[key] = {
                "sha256": digest.hexdigest(),
                "size": size,
                "lfs": path.suffix.lower()
                in {".bit", ".bin", ".vcd", ".fsdb", ".wlf", ".gtkw"},
            }
        return manifest

    def _run(self, args: list[str], *, check: bool) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["GIT_TERMINAL_PROMPT"] = "0"
        result = subprocess.run(
            args,
            cwd=self.root,
            capture_output=True,
            text=True,
            env=env,
        )
        if check and result.returncode != 0:
            raise GitCommandError(
                f"{' '.join(args)} failed: {result.stderr.strip()}"
            )
        return result

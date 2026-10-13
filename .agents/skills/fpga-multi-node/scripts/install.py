"""Install only this project skill; never configure or restart the mesh."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import shutil
import tempfile
import tomllib
import uuid
from pathlib import Path

PREFIX = ".agents/skills/fpga-multi-node"
BEGIN = "<!-- fpga-multi-node:begin -->"
END = "<!-- fpga-multi-node:end -->"
ENTRY = f"""{BEGIN}
## Mandatory project collaboration skill

Every conversation in this project must read `.agents/skills/fpga-multi-node/SKILL.md`
and follow its node-matched role, task ownership, delegation and evidence rules.
Apply the existing human > main > child priority; this skill grants no new role,
credentials, cloud permissions, board access or service-change authorization.
Keep presence silent unless the human asks; report actual task blockers concisely.
Waiting is handled by the resident program, with no model polling.
{END}
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payloads(source: Path) -> dict[str, bytes]:
    result = {}
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError("skill source must not contain symlinks")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(source).as_posix()] = path.read_bytes()
    return result


def verify_package(source: Path) -> None:
    package = source.parents[2]
    manifest_path = package / "MANIFEST.json"
    if not manifest_path.is_file():
        raise ValueError("package MANIFEST.json is required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("revision") or not manifest.get("files"):
        raise ValueError("package revision or file list is missing")
    expected = set()
    for entry in manifest["files"]:
        relative = Path(entry["path"])
        candidate = (package / relative).resolve()
        if relative.is_absolute() or not candidate.is_relative_to(source):
            raise ValueError("package path outside skill")
        if (not candidate.is_file() or candidate.stat().st_size != entry["size"]
                or digest(candidate) != entry["sha256"]):
            raise ValueError(f"package hash mismatch: {entry['path']}")
        expected.add(candidate.relative_to(source).as_posix())
    if expected != set(payloads(source)):
        raise ValueError("package hash file set mismatch")


@contextmanager
def installation_lock(project: Path):
    """Non-blocking OS lock, automatically released if the installer exits."""
    path = project / ".local/skill-install.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.seek(0, 2) == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            acquire = lambda: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            release = lambda: msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            acquire = lambda: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            release = lambda: fcntl.flock(stream, fcntl.LOCK_UN)
        try:
            acquire()
        except OSError as exc:
            raise RuntimeError("skill install already running") from exc
        try:
            yield
        finally:
            stream.seek(0)
            release()


def install(source: Path, project: Path, node: str) -> dict:
    source, project = Path(source).resolve(), Path(project).resolve()
    role = json.loads((source / "skill-role.json").read_text(encoding="utf-8"))
    if node not in role["allowed_nodes"]:
        raise ValueError("package role does not allow this node")
    verify_package(source)
    if not (project / ".git").exists():
        raise ValueError("project must be an existing Git checkout")
    configs = list((project / ".local/deployment").glob("node-*/node-*.toml"))
    if len(configs) != 1 or tomllib.loads(configs[0].read_text(encoding="utf-8-sig")).get("node_id") != node:
        raise ValueError("existing node identity does not match installation role")
    with installation_lock(project):
        return _install_locked(source, project, node)


def _install_locked(source: Path, project: Path, node: str) -> dict:
    target = (project / PREFIX).resolve()
    if (project / PREFIX).is_symlink() or not target.is_relative_to(project) or target == project:
        raise ValueError("skill target is outside project")
    agent_path = project / "AGENTS.md"
    if agent_path.is_symlink() or not agent_path.resolve().is_relative_to(project):
        raise ValueError("project AGENTS path is unsafe")
    old_agents = agent_path.read_bytes() if agent_path.exists() else b""
    text = old_agents.decode("utf-8-sig")
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(END) < text.index(BEGIN):
            raise ValueError("project skill entry markers are invalid")
        start, end = text.index(BEGIN), text.index(END) + len(END)
        updated = (text[:start] + ENTRY.rstrip("\n") + text[end:]).encode("utf-8")
        if updated.decode("utf-8") == text:
            updated = old_agents
    else:
        updated = old_agents + (b"\n" if old_agents and not old_agents.endswith(b"\n") else b"") + b"\n" + ENTRY.encode("utf-8")
    source_files = payloads(source)
    original_target = payloads(target) if target.exists() else None
    same = original_target == source_files
    if same and updated == old_agents:
        return {"status": "unchanged", "node": node, "skill": str(target)}
    backup = project / ".local/skill-backups" / uuid.uuid4().hex
    # Finish all validation before writing. The backup lives outside skill discovery.
    backup.mkdir(parents=True)
    if old_agents:
        (backup / "AGENTS.md").write_bytes(old_agents)
    target.parent.mkdir(parents=True, exist_ok=True)
    moved = False
    published = False
    try:
        if not same:
            with tempfile.TemporaryDirectory(prefix=".mesh-skill-", dir=target.parent) as temporary:
                staged = Path(temporary) / "skill"
                for relative, content in source_files.items():
                    destination = staged / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(content)
                if target.exists():
                    if payloads(target) != original_target:
                        raise RuntimeError("skill changed during install; refusing overwrite")
                    target.rename(backup / "skill")
                    moved = True
                staged.rename(target)
                published = True
        if agent_path.exists() and agent_path.read_bytes() != old_agents:
            raise RuntimeError("AGENTS changed during install; refusing overwrite")
        if updated != old_agents:
            with tempfile.NamedTemporaryFile(dir=project, delete=False) as pending:
                pending.write(updated)
                pending_path = Path(pending.name)
            try:
                pending_path.replace(agent_path)
            finally:
                pending_path.unlink(missing_ok=True)
    except Exception:
        # Roll back only our own verified staged bytes; preserve concurrent changes.
        if published and target.exists() and payloads(target) == source_files:
            shutil.rmtree(target)
        if moved and not target.exists():
            (backup / "skill").rename(target)
        raise
    return {"status": "installed", "node": node, "skill": str(target), "backup": str(backup)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--node", choices=("A", "B", "C"), required=True)
    args = parser.parse_args()
    print(json.dumps(install(Path(__file__).resolve().parents[1], args.project_root, args.node), ensure_ascii=True))


if __name__ == "__main__":
    main()

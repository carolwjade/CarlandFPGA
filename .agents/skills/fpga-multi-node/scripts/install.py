"""Install two project skills atomically without changing runtime services or identity."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import re
import shutil
import tempfile
import tomllib
import uuid
import zipfile
from pathlib import Path

VERSION = "2026.10.13.3"
SKILLS = ("fpga-multi-node", "pynq-z2-single-node")
PREFIX = ".agents/skills/"
BEGIN, END = "<!-- fpga-project-skills:begin -->", "<!-- fpga-project-skills:end -->"
OLD_BEGIN, OLD_END = "<!-- fpga-multi-node:begin -->", "<!-- fpga-multi-node:end -->"
ENTRY = f"""{BEGIN}
## Mandatory project skills

Every new conversation must read `.agents/skills/fpga-multi-node/SKILL.md` and its
node-matched role; use `.agents/skills/pynq-z2-single-node/SKILL.md` for local FPGA
design and verification. A alone operates the physical board. Both skills are
project-local; a new conversation loads the installed version.
Apply the existing human > main > child priority, task ownership and evidence
rules. Skills grant no new role, credentials, cloud scope or service authority.
Keep presence silent unless the human asks; report actual task blockers concisely.
The resident program handles waiting, without model polling.
{END}
"""
LEGACY_NAMES = frozenset({
    "pynq-z2-single-node", "fpga-multi-node", "fpga-mesh-coordination",
    "pynq-z2-client-b", "pynq-z2-client-c", "pynq-z2-single-node-b",
    "pynq-z2-single-node-c", "pynq-z2-single-node-client-b", "pynq-z2-single-node-client-c",
})
LEGACY_BACKUP = re.compile(
    r"(?:pynq-z2-single-node|fpga-multi-node|fpga-mesh-coordination)\.backup-[A-Za-z0-9_-]+\Z")


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def plain_path(path: Path) -> None:
    """Reject symlinks and Windows junctions, including ancestor redirects."""
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError(f"symlink or reparse path is not allowed: {part}")


def payloads(source: Path) -> dict[str, bytes]:
    plain_path(source)
    if not source.exists():
        return {}
    if not source.is_dir():
        raise ValueError("skill path must be a directory")
    result = {}
    for path in sorted(source.rglob("*")):
        plain_path(path)
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(source).as_posix()] = path.read_bytes()
    return result


def package_root(source: Path) -> Path:
    source = Path(source).absolute()
    plain_path(source)
    if (source / "MANIFEST.json").is_file():
        return source.resolve()
    if source.name in SKILLS and source.parent.name == "skills" and source.parent.parent.name == ".agents":
        return source.parents[2].resolve()
    raise ValueError("source must be the extracted combined package or one of its two skills")


def verify_package(source: Path) -> tuple[dict, dict[str, dict[str, bytes]]]:
    package = package_root(source)
    manifest_path = package / "MANIFEST.json"
    plain_path(manifest_path)
    if not manifest_path.is_file():
        raise ValueError("package MANIFEST.json is required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("project") != "CarlandFPGA" or manifest.get("version") != VERSION
            or manifest.get("profile") not in {"project-skills-a", "project-skills-bc"}
            or not isinstance(manifest.get("revision"), str)
            or not manifest["revision"].strip() or manifest["revision"] == "uncommitted"
            or not isinstance(manifest.get("files"), list) or not manifest["files"]):
        raise ValueError("package profile, version, revision or file list is invalid")
    expected, folded = set(), set()
    for entry in manifest["files"]:
        name = entry.get("path", "")
        if not isinstance(name, str):
            raise ValueError("invalid package path")
        relative = Path(name)
        if (relative.is_absolute() or "\\" in name or ":" in name or ".." in relative.parts
                or any(part.endswith((" ", ".")) for part in relative.parts)
                or relative.as_posix() != name
                or not any(name.startswith(PREFIX + skill + "/") for skill in SKILLS)
                or name.casefold() in folded):
            raise ValueError("package path outside the two skills or duplicate path")
        candidate = package / relative
        plain_path(candidate)
        if (not candidate.resolve().is_relative_to(package) or not candidate.is_file()
                or not isinstance(entry.get("size"), int) or candidate.stat().st_size != entry["size"]
                or sha(candidate.read_bytes()) != entry.get("sha256")):
            raise ValueError(f"package hash mismatch: {name}")
        expected.add(name)
        folded.add(name.casefold())
    sources = {skill: payloads(package / PREFIX / skill) for skill in SKILLS}
    actual = {PREFIX + skill + "/" + name for skill, files in sources.items() for name in files}
    if expected != actual or set(payloads(package)) != expected | {"MANIFEST.json"}:
        raise ValueError("package hash file set mismatch")
    allowed = ["A"] if manifest["profile"] == "project-skills-a" else ["B", "C"]
    for skill, files in sources.items():
        if not {"SKILL.md", "skill-role.json", "agents/openai.yaml"}.issubset(files):
            raise ValueError("package skill or role is incomplete")
        role = json.loads(files["skill-role.json"])
        expected_role = "host" if allowed == ["A"] else "client"
        if (role.get("allowed_nodes") != allowed or role.get("scope") != "project"
                or role.get("version") != VERSION or role.get("schema") != 1
                or role.get("role") != expected_role or role.get("board_operator") != "A"):
            raise ValueError("the two package roles must match profile and version")
        if skill == "pynq-z2-single-node":
            if role.get("board_access") is not (allowed == ["A"]):
                raise ValueError("single-node board role is invalid")
            if allowed != ["A"] and {"scripts/board_run.py", "scripts/board_probe.py", "requirements-board.txt"} & set(files):
                raise ValueError("client package contains physical board entrypoints")
    return manifest, sources


def agent_rules(old: bytes) -> bytes:
    """Replace only managed blocks; preserve all unrelated rule bytes."""
    old.decode("utf-8-sig")
    # Migrate exactly the obsolete project-relative pointer, without changing
    # already-canonical paths or arbitrary external/unrelated paths.
    old = re.sub(rb"(?<![A-Za-z0-9_./\\-])skills/pynq-z2-single-node(?=/|[\s`'\"]|$)",
                 b".agents/skills/pynq-z2-single-node", old)
    regions = []
    for begin, end in ((BEGIN, END), (OLD_BEGIN, OLD_END)):
        left, right = begin.encode(), end.encode()
        if left in old or right in old:
            if old.count(left) != 1 or old.count(right) != 1 or old.index(right) < old.index(left):
                raise ValueError("project skill entry markers are invalid")
            regions.append((old.index(left), old.index(right) + len(right)))
    if not regions:
        return old + (b"\n" if old and not old.endswith(b"\n") else b"") + b"\n" + ENTRY.encode()
    regions.sort()
    if any(regions[i][1] > regions[i + 1][0] for i in range(len(regions) - 1)):
        raise ValueError("project skill entry markers overlap")
    updated = old
    for index, (start, end) in reversed(list(enumerate(regions))):
        updated = updated[:start] + (ENTRY.rstrip("\n").encode() if index == 0 else b"") + updated[end:]
    return updated


@contextmanager
def installation_lock(project: Path):
    """Nonblocking OS lock automatically released on process exit."""
    path = project / ".local/skill-install.lock"
    plain_path(path)
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


def legacy_candidates(roots: list[Path] | None = None, *, project: Path | None = None) -> list[tuple[Path, dict[str, bytes]]]:
    if roots is None:
        home = Path.home()
        roots = [home / ".codex/skills", home / ".agents/skills"]
        if os.environ.get("CODEX_HOME"):
            roots.append(Path(os.environ["CODEX_HOME"]) / "skills")
    else:
        roots = list(roots)
    protected = set()
    if project is not None:
        roots.extend([project / "skills", project / PREFIX])
        protected = {(project / PREFIX / skill).resolve() for skill in SKILLS}
    result, seen = [], set()
    for supplied in roots:
        root = Path(supplied).absolute()
        plain_path(root)
        root = root.resolve()
        if root in seen or not root.exists():
            continue
        seen.add(root)
        if not root.is_dir():
            raise ValueError("legacy skill root must be a directory")
        for candidate in sorted(root.iterdir()):
            if candidate.name not in LEGACY_NAMES and not LEGACY_BACKUP.fullmatch(candidate.name):
                continue
            plain_path(candidate)
            if candidate.resolve() in protected:
                continue
            if candidate.resolve().parent != root or not candidate.is_dir():
                raise ValueError("legacy target is outside its exact permitted parent")
            files = payloads(candidate)
            declared = re.search(rb"\A---\r?\n(?:[^\n]*\n)*?name:\s*([^\r\n]+)", files.get("SKILL.md", b""))
            expected = "pynq-z2-single-node" if candidate.name.startswith("pynq-z2-") else candidate.name.split(".backup-")[0]
            if not declared or declared.group(1).decode("utf-8").strip(" \"'") != expected:
                raise ValueError(f"legacy skill identity is not confirmed: {candidate}")
            if any(".local" in Path(name).parts or Path(name).name in {"auth.json", "credentials.json", "state.sqlite"}
                   or re.fullmatch(r"node-[abc]\.toml", Path(name).name) for name in files):
                raise ValueError("legacy directory contains runtime identity or state; refusing cleanup")
            result.append((candidate, files))
    return result


def _write_files(directory: Path, files: dict[str, bytes]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for relative, content in files.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _replace_agents(path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as pending:
        pending.write(content)
        temporary = Path(pending.name)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_backup(path: Path, old: dict, agents: bytes, agents_existed: bool,
                  legacy: list[tuple[Path, dict]], manifest: dict) -> str:
    entries = {"project/AGENTS.md": agents} if agents_existed else {}
    for skill, files in old.items():
        if files is not None:
            entries.update({"project/" + PREFIX + skill + "/" + name: data for name, data in files.items()})
    targets = []
    for index, (target, files) in enumerate(legacy):
        prefix = f"legacy/{index}/{target.name}/"
        entries.update({prefix + name: data for name, data in files.items()})
        targets.append({"path": str(target), "archive_prefix": prefix})
    recovery = {"project": "CarlandFPGA", "version": VERSION, "revision": manifest["revision"],
                "legacy_targets": targets, "files": [
                    {"path": name, "size": len(data), "sha256": sha(data)} for name, data in sorted(entries.items())]}
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
        archive.writestr("BACKUP.json", json.dumps(recovery, ensure_ascii=False, indent=2) + "\n")
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None or any(sha(archive.read(name)) != sha(data) for name, data in entries.items()):
            raise RuntimeError("backup verification failed")
    return sha(path.read_bytes())


def install(source: Path, project: Path, node: str, *, cleanup_legacy: bool = False,
            legacy_roots: list[Path] | None = None) -> dict:
    """Validate first, then install the pair with recoverable rollback."""
    manifest, sources = verify_package(source)
    if node not in json.loads(sources[SKILLS[0]]["skill-role.json"])["allowed_nodes"]:
        raise ValueError("package role does not allow this node")
    project = Path(project).absolute()
    plain_path(project)
    project = project.resolve()
    if not (project / ".git").exists():
        raise ValueError("project must be an existing Git checkout")
    configs = [p for p in (project / ".local/deployment").glob("node-*/node-*.toml")
               if p.name == p.parent.name + ".toml"]
    if len(configs) != 1:
        raise ValueError("exactly one existing formal node configuration is required")
    plain_path(configs[0])
    config_bytes = configs[0].read_bytes()
    # Match the controller's universal-newline text reading, but retain raw bytes
    # for race detection and exact configuration preservation.
    if tomllib.loads(config_bytes.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")).get("node_id") != node:
        raise ValueError("existing node identity does not match installation role")
    with installation_lock(project):
        if verify_package(source) != (manifest, sources) or configs[0].read_bytes() != config_bytes:
            raise RuntimeError("package or node configuration changed during install")
        return _install_locked(package_root(source), project, node, manifest, sources,
                               configs[0], config_bytes, cleanup_legacy, legacy_roots)


def _install_locked(package: Path, project: Path, node: str, manifest: dict, sources: dict,
                    config: Path, config_bytes: bytes, cleanup: bool, roots: list[Path] | None) -> dict:
    target_root = project / PREFIX
    plain_path(target_root)
    targets = {skill: target_root / skill for skill in SKILLS}
    for target in targets.values():
        plain_path(target)
        if target.resolve().parent != target_root.resolve() or not target.resolve().is_relative_to(project):
            raise ValueError("skill target is outside project")
    if target_root.exists():
        for candidate in target_root.iterdir():
            if candidate.name not in SKILLS and (candidate / "SKILL.md").exists():
                if not cleanup or (candidate.name not in LEGACY_NAMES and not LEGACY_BACKUP.fullmatch(candidate.name)):
                    raise ValueError("unrelated project skill requires review; installer will not delete it")
    agent_path = project / "AGENTS.md"
    plain_path(agent_path)
    agents_existed = agent_path.exists()
    old_agents = agent_path.read_bytes() if agents_existed else b""
    updated_agents = agent_rules(old_agents)
    old = {skill: payloads(target) if target.exists() else None for skill, target in targets.items()}
    legacy = legacy_candidates(roots, project=project) if cleanup else []
    if all(old[skill] == sources[skill] for skill in SKILLS) and updated_agents == old_agents and not legacy:
        return {"status": "unchanged", "node": node, "version": VERSION,
                "revision": manifest["revision"], "skills": [str(path) for path in targets.values()]}
    backup = project / ".local/skill-backups" / (uuid.uuid4().hex + ".zip")
    receipt_path = backup.with_suffix(".json")
    plain_path(backup)
    moved, published, removed = [], [], []
    agents_published = False
    with tempfile.TemporaryDirectory(prefix="skill-install-", dir=project / ".local") as temporary:
        stage = Path(temporary)
        for skill in SKILLS:
            _write_files(stage / "new" / skill, sources[skill])
        if verify_package(package) != (manifest, sources) or config.read_bytes() != config_bytes:
            raise RuntimeError("package or node configuration changed during install")
        for skill, target in targets.items():
            if (payloads(target) if target.exists() else None) != old[skill]:
                raise RuntimeError("skill changed during install; refusing overwrite")
        if agent_path.exists() != agents_existed or (agent_path.read_bytes() if agent_path.exists() else b"") != old_agents:
            raise RuntimeError("AGENTS changed during install; refusing overwrite")
        for target, files in legacy:
            if payloads(target) != files:
                raise RuntimeError("legacy skill changed during install; refusing cleanup")
        backup_hash = _write_backup(backup, old, old_agents, agents_existed, legacy, manifest)
        try:
            target_root.mkdir(parents=True, exist_ok=True)
            for skill, target in targets.items():
                if old[skill] == sources[skill]:
                    continue
                if (payloads(target) if target.exists() else None) != old[skill]:
                    raise RuntimeError("skill changed during install; refusing overwrite")
                if target.exists():
                    original = stage / "original" / skill
                    original.parent.mkdir(parents=True, exist_ok=True)
                    target.rename(original)
                    moved.append(skill)
                (stage / "new" / skill).rename(target)
                published.append(skill)
            if agent_path.exists() != agents_existed or (agent_path.read_bytes() if agent_path.exists() else b"") != old_agents:
                raise RuntimeError("AGENTS changed during install; refusing overwrite")
            if updated_agents != old_agents:
                _replace_agents(agent_path, updated_agents)
                agents_published = True
            for target, files in legacy:
                if payloads(target) != files:
                    raise RuntimeError("legacy skill changed during install; refusing cleanup")
                removed.append((target, files))
                shutil.rmtree(target)
            if (config.read_bytes() != config_bytes or agent_path.read_bytes() != updated_agents
                    or any(payloads(target) != sources[skill] for skill, target in targets.items())):
                raise RuntimeError("project changed during install; refusing completion")
            receipt = {"status": "installed", "node": node, "version": VERSION,
                       "revision": manifest["revision"], "profile": manifest["profile"],
                       "skills": [str(path) for path in targets.values()], "backup": str(backup),
                       "backup_sha256": backup_hash, "cleaned_legacy": [str(path) for path, _ in legacy],
                       "new_conversation_required": True}
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception:
            for target, files in reversed(removed):
                present = payloads(target) if target.exists() else {}
                if all(name in files and files[name] == data for name, data in present.items()):
                    _write_files(target, files)
            if agents_published and agent_path.exists() and agent_path.read_bytes() == updated_agents:
                if agents_existed:
                    _replace_agents(agent_path, old_agents)
                else:
                    agent_path.unlink()
            for skill in reversed(published):
                target = targets[skill]
                if target.exists() and payloads(target) == sources[skill]:
                    shutil.rmtree(target)
            for skill in reversed(moved):
                if not targets[skill].exists():
                    (stage / "original" / skill).rename(targets[skill])
            raise
    return {**receipt, "receipt": str(receipt_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--node", choices=("A", "B", "C"), required=True)
    parser.add_argument("--cleanup-legacy", action="store_true",
                        help="Remove only confirmed obsolete FPGA skills after saving a verified ZIP")
    args = parser.parse_args()
    print(json.dumps(install(Path(__file__).resolve().parents[1], args.project_root, args.node,
                             cleanup_legacy=args.cleanup_legacy), ensure_ascii=True))


if __name__ == "__main__":
    main()

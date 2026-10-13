"""Build a credential-free teammate ZIP from the committed Git file list."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


_KEY_PATTERN = re.compile(
    rb"sk-[A-Za-z0-9_-]{24,}|-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE "
    rb"KEY-----|-----BEGIN PGP PRIVATE " rb"KEY BLOCK-----"
)
_PRIVATE_FILENAMES = {"auth.json", "deepcodex.txt", "id_ed25519", "id_rsa", "id_ecdsa", "id_dsa"}
_PRIVATE_SUFFIXES = ("-secret.txt", ".p12", ".pfx", ".pem", ".key", ".lic")
SKILL_VERSION = "2026.10.13.2"
SKILL_NAMES = ("fpga-multi-node", "pynq-z2-single-node")
_SKILL_PREFIX = ".agents/skills/"
_PROFILE_ALIASES = {
    "mesh-skill-a": "project-skills-a", "pynq-skill": "project-skills-a",
    "mesh-skill-bc": "project-skills-bc", "pynq-client-b": "project-skills-bc",
    "pynq-client-c": "project-skills-bc",
}
_CLIENT_TEMPLATES = {"fpga-multi-node": "packaging/multi-node-client",
                     "pynq-z2-single-node": "packaging/pynq-client"}
_ROLE_FILES = {"SKILL.md": "SKILL.md", "skill-role.json": "skill-role.json",
               "agents/openai.yaml": "openai.yaml"}
_BOARD_ONLY = {"scripts/board_run.py", "scripts/board_probe.py", "requirements-board.txt"}


def _verified_source_path(root: Path, path: Path) -> Path:
    """Check original paths before reading bytes, including role replacements."""
    if not path.is_absolute():
        path = root / path
    if not path.absolute().is_relative_to(root) or not path.resolve().is_relative_to(root):
        raise ValueError("skill source is outside package root")
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("symlink or reparse path cannot enter skill package")
    return path


def select_package_paths(paths: list[str], profile: str) -> list[str]:
    """The controller never installs skills; each role bundle contains both skills."""
    profile = _PROFILE_ALIASES.get(profile, profile)
    if profile in {"project-skills-a", "project-skills-bc"}:
        return [path for path in paths
                if any(path.startswith(_SKILL_PREFIX + name + "/") for name in SKILL_NAMES)]
    if profile == "mesh":
        return [path for path in paths if not (
            path.startswith("skills/")
            or path.startswith(_SKILL_PREFIX)
            or path.startswith("packaging/")
            or path == "tests/test_mesh_skill_distribution.py"
            or path.startswith("docs/deployment/SINGLE_NODE_")
            or path.startswith("docs/deployment/HOST_TOOLCHAIN_")
            or path.startswith("docs/deployment/evidence/pynq-z2-")
            or path.startswith("packaging/pynq-client/")
            or path == "tests/test_pynq_client_distribution.py"
            or path.startswith("tests/test_pynq_z2_")
        )]
    raise ValueError(f"unknown package profile: {profile}")


def build_project_skills_archive(
    root: Path, role: str, output: Path, *, revision: str, paths: list[str] | None = None,
) -> Path:
    """Package two project-local skills from one shared source and role templates."""
    if role not in {"a", "bc"}:
        raise ValueError("project skills role must be a or bc")
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix="project-skills-") as temporary:
        staging = Path(temporary)
        files = []
        for name in SKILL_NAMES:
            prefix = _SKILL_PREFIX + name + "/"
            source = root / prefix
            selected = ([root / entry for entry in paths if entry.startswith(prefix)]
                        if paths is not None else list(source.rglob("*")))
            for item in sorted(selected):
                _verified_source_path(root, item)
                if not item.is_file() or "__pycache__" in item.parts or item.suffix == ".pyc":
                    continue
                relative = item.relative_to(source).as_posix()
                if role == "bc" and name == "pynq-z2-single-node" and relative in _BOARD_ONLY:
                    continue
                replacement = _ROLE_FILES.get(relative)
                original = (root / _CLIENT_TEMPLATES[name] / replacement
                            if role == "bc" and replacement else item)
                _verified_source_path(root, original)
                if paths is not None and original.relative_to(root).as_posix() not in paths:
                    raise ValueError(f"skill source is not tracked: {original.name}")
                target = staging / prefix / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(original.read_bytes())
                files.append(prefix + relative)
            required = {prefix + entry for entry in ("SKILL.md", "skill-role.json", "agents/openai.yaml")}
            if not required.issubset(files):
                raise ValueError(f"incomplete project skill: {name}")
        return build_archive(staging, files, output, revision=revision,
                             profile=f"project-skills-{role}")


def build_mesh_skill_archive(root: Path, role: str, output: Path, *, revision: str,
                             paths: list[str] | None = None) -> Path:
    """Compatibility API: the old mesh-skill profile now supplies the complete pair."""
    return build_project_skills_archive(root, role, output, revision=revision, paths=paths)


def build_archive(
    root: Path, paths: list[str], output: Path, *, revision: str = "uncommitted",
    profile: str = "mesh", previous_archives: list[Path] | None = None,
) -> Path:
    root = Path(root).resolve()
    output = Path(output).resolve()
    files = []
    payloads: dict[str, bytes] = {}
    for raw in sorted(set(paths)):
        relative = Path(raw)
        resolved = (root / relative).resolve()
        if (relative.is_absolute() or ".." in relative.parts or "\\" in raw or ":" in raw
                or not resolved.is_relative_to(root)):
            raise ValueError(f"unsafe package path: {raw}")
        _verified_source_path(root, root / relative)
        normalized = relative.as_posix()
        lowered = [part.casefold() for part in relative.parts]
        if ({".git", ".local", "__pycache__"} & set(lowered)
                or relative.name.casefold() in _PRIVATE_FILENAMES
                or relative.name.casefold().endswith(_PRIVATE_SUFFIXES)):
            raise ValueError(f"private path cannot enter package: {raw}")
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        content = resolved.read_bytes()
        if _KEY_PATTERN.search(content):
            raise ValueError(f"key-like material found in: {raw}")
        payloads[normalized] = content
        files.append({
            "path": normalized, "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    manifest = {
        "project": "CarlandFPGA",
        "profile": profile,
        "revision": revision,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    if profile.startswith("project-skills-"):
        manifest["version"] = SKILL_VERSION
    if previous_archives:
        if profile != "mesh":
            raise ValueError("in-place updates are only supported for mesh packages")
        # Read actual distributed bytes, including their checkout line endings.
        # No old source or credential is copied into the new ZIP.
        from .update import canonical_hash, read_package
        previous = []
        bases = []
        for path in previous_archives:
            old_manifest, old_payloads = read_package(path, require_update=False)
            selected = select_package_paths(list(old_payloads), "mesh")
            previous.append({name: canonical_hash(old_payloads[name]) for name in selected})
            bases.append({"revision": old_manifest["revision"],
                          "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()})
        before = {
            name: sorted({base[name] for base in previous if name in base})
                  + ([None] if any(name not in base for base in previous) else [])
            for name in payloads
        }
        removed = {}
        for base in previous:
            for name, digest in base.items():
                if name not in payloads:
                    removed.setdefault(name, set()).add(digest)
        manifest["update"] = {
            "schema": 1, "bases": bases, "before": before,
            "removed": {name: sorted(values) for name, values in removed.items()},
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in payloads.items():
            archive.writestr(name, content)
        archive.writestr(
            "MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC verification failed")
        for entry in files:
            if hashlib.sha256(archive.read(entry["path"])).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"ZIP hash verification failed: {entry['path']}")
    return output


def build_client_archive(
    root: Path, node: str, output: Path, *, revision: str = "uncommitted",
) -> Path:
    """Compatibility API: B and C share the same board-free two-skill bundle."""
    if node not in {"B", "C"}:
        raise ValueError("client node must be B or C")
    return build_project_skills_archive(root, "bc", output, revision=revision)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", choices=("mesh", "project-skills-a", "project-skills-bc",
                                             *_PROFILE_ALIASES), default="mesh")
    parser.add_argument("--previous-archive", type=Path, action="append", default=[],
                        help="Known previously distributed ZIP; repeat for compatibility")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root,
        capture_output=True, text=True, check=True,
    ).stdout
    if dirty.strip():
        raise SystemExit("Commit all source changes before building the package")
    listed = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root,
        capture_output=True, check=True,
    ).stdout.decode("utf-8", errors="strict")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    profile = _PROFILE_ALIASES.get(args.profile, args.profile)
    if args.previous_archive and profile != "mesh":
        raise SystemExit("--previous-archive is only supported for controller packages")
    if profile.startswith("project-skills-"):
        path = build_project_skills_archive(root, profile.removeprefix("project-skills-"),
                                           args.output, revision=revision,
                                           paths=[name for name in listed.split("\0") if name])
        with zipfile.ZipFile(path) as archive:
            file_count = len(archive.namelist()) - 1
    else:
        paths = select_package_paths(
            [name for name in listed.split("\0") if name], profile,
        )
        path = build_archive(root, paths, args.output, revision=revision,
                             profile=profile, previous_archives=args.previous_archive)
        file_count = len(paths)
    print(json.dumps({
        "archive": str(path), "profile": profile,
        "revision": revision, "files": file_count,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

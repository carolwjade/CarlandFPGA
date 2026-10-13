"""Create and verify a single-machine FPGA evidence handoff manifest.

Only root-relative files are packaged. SHA-256 checks integrity, not authorship.
No board execution or vendor tool invocation is performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
REQUEST_FIELDS = {
    "operation_id", "task_id", "task_version", "requester", "code_commit",
    "test_steps", "expected_result",
}
STAGE_STATUSES = {"passed", "failed", "blocked", "not_run"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _read_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def _root_path(root: str | Path) -> Path:
    path = Path(root).resolve()
    if not path.is_dir():
        raise ValueError(f"root is not an existing directory: {path}")
    return path


def _contained_absolute(root: Path, path: str | Path, *, must_exist: bool) -> Path:
    given = Path(path)
    if given.drive and not given.is_absolute():
        raise ValueError(f"path escapes root: {path}")
    candidate = (given if given.is_absolute() else root / given).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise ValueError(f"path escapes root: {path}")
    if must_exist and not candidate.is_file():
        raise ValueError(f"missing file: {path}")
    return candidate


def _evidence_path(root: Path, name: Any) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError(f"invalid evidence path: {name!r}")
    posix = PurePosixPath(name)
    if (
        posix.is_absolute()
        or str(posix) != name
        or any(part in ("", ".", "..") for part in name.split("/"))
    ):
        raise ValueError(f"invalid evidence path: {name!r}")
    candidate = (root / Path(*posix.parts)).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise ValueError(f"evidence path escapes root: {name}")
    if not candidate.is_file():
        raise ValueError(f"missing evidence file: {name}")
    return candidate


def _validate_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
        raise ValueError(f"request must contain exactly: {', '.join(sorted(REQUEST_FIELDS))}")
    for field in REQUEST_FIELDS - {"task_version", "test_steps"}:
        if not isinstance(request[field], str) or not request[field].strip():
            raise ValueError(f"request.{field} must be a nonempty string")
    version = request["task_version"]
    if type(version) is not int or version <= 0:
        raise ValueError("request.task_version must be a positive integer")
    steps = request["test_steps"]
    if not isinstance(steps, list) or not steps or any(
        not isinstance(step, str) or not step.strip() for step in steps
    ):
        raise ValueError("request.test_steps must be a nonempty list of nonempty strings")
    return request


def _request_hash(request: dict[str, Any]) -> str:
    # Matches fpga_mesh.hardware.HardwareRequest.request_hash exactly.
    raw = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_artifacts(artifacts: Any, root: Path) -> list[str]:
    if not isinstance(artifacts, list) or any(not isinstance(item, str) for item in artifacts):
        raise ValueError("artifacts must be a list of root-relative file paths")
    if len(set(artifacts)) != len(artifacts):
        raise ValueError("artifacts contains duplicate paths")
    for item in artifacts:
        _evidence_path(root, item)
    return artifacts


def _validate_stages(stages: Any, root: Path) -> dict[str, dict[str, str]]:
    if not isinstance(stages, dict) or not stages:
        raise ValueError("stages must be a nonempty object")
    for name, stage in stages.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("stage names must be nonempty strings")
        if not isinstance(stage, dict) or set(stage) not in ({"status"}, {"status", "log"}):
            raise ValueError(f"stage {name!r} needs status and optional log")
        status = stage["status"]
        if not isinstance(status, str) or status not in STAGE_STATUSES:
            raise ValueError(f"unsupported stage status for {name!r}: {status!r}")
        if status == "passed" and "log" not in stage:
            raise ValueError(f"passed stage {name!r} requires an existing log")
        if "log" in stage:
            log_path = _evidence_path(root, stage["log"])
            if status == "passed" and log_path.stat().st_size == 0:
                raise ValueError(f"passed stage {name!r} has an empty log")
    return stages


def _digest(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"sha256": digest.hexdigest(), "size": size}


def _file_names(artifacts: list[str], stages: dict[str, dict[str, str]]) -> set[str]:
    return set(artifacts) | {stage["log"] for stage in stages.values() if "log" in stage}


def create_manifest(
    root: str | Path, input_path: str | Path, output_path: str | Path
) -> dict[str, Any]:
    """Validate the handoff input, hash its evidence, and write a JSON manifest."""
    base = _root_path(root)
    output = _contained_absolute(base, output_path, must_exist=False)
    payload = _read_object(Path(input_path))
    if set(payload) != {"request", "artifacts", "stages"}:
        raise ValueError("input needs exactly request, artifacts, and stages")
    request = _validate_request(payload["request"])
    artifacts = _validate_artifacts(payload["artifacts"], base)
    stages = _validate_stages(payload["stages"], base)
    names = _file_names(artifacts, stages)
    if output in {_evidence_path(base, name) for name in names}:
        raise ValueError("manifest output cannot be listed as evidence")
    files = {name: _digest(_evidence_path(base, name)) for name in sorted(names)}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "request": request,
        "request_hash": _request_hash(request),
        "artifacts": artifacts,
        "stages": stages,
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output = _contained_absolute(base, output, must_exist=False)
    content = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with output.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        try:
            previous = output.read_bytes()
        except OSError as exc:
            raise ValueError(f"cannot read existing manifest: {exc}") from exc
        if previous != content:
            raise ValueError(f"manifest already exists with different contents: {output}")
    except OSError as exc:
        raise ValueError(f"cannot write manifest: {exc}") from exc
    return manifest


def verify_manifest(root: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    """Recheck schema, request identity, root confinement, and all file hashes."""
    base = _root_path(root)
    path = _contained_absolute(base, manifest_path, must_exist=True)
    manifest = _read_object(path)
    if (
        set(manifest) != {
            "schema_version", "request", "request_hash", "artifacts", "stages", "files"
        }
        or type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != SCHEMA_VERSION
    ):
        raise ValueError("unsupported manifest schema")
    request = _validate_request(manifest["request"])
    if manifest["request_hash"] != _request_hash(request):
        raise ValueError("request_hash mismatch")
    artifacts = _validate_artifacts(manifest["artifacts"], base)
    stages = _validate_stages(manifest["stages"], base)
    names = _file_names(artifacts, stages)
    if path in {_evidence_path(base, name) for name in names}:
        raise ValueError("manifest cannot be listed as evidence")
    files = manifest["files"]
    if not isinstance(files, dict) or set(files) != names:
        raise ValueError("manifest file inventory does not match artifacts and logs")
    for name, expected in files.items():
        if (
            not isinstance(expected, dict)
            or set(expected) != {"sha256", "size"}
            or not isinstance(expected["sha256"], str)
            or not SHA256_RE.fullmatch(expected["sha256"])
            or type(expected["size"]) is not int
            or expected["size"] < 0
        ):
            raise ValueError(f"invalid file digest record: {name}")
        observed = _digest(_evidence_path(base, name))
        if observed != expected:
            raise ValueError(f"hash or size mismatch for {name}")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or verify a root-contained FPGA single-machine evidence manifest."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Hash listed artifacts and stage logs")
    create.add_argument("--root", required=True, help="Directory containing all evidence")
    create.add_argument("--input", required=True, help="Handoff input JSON path")
    create.add_argument("--output", required=True, help="Manifest JSON path inside root")
    verify = commands.add_parser("verify", help="Recheck manifest and file digests")
    verify.add_argument("--root", required=True, help="Directory containing all evidence")
    verify.add_argument("--manifest", required=True, help="Manifest JSON path inside root")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            manifest = create_manifest(args.root, args.input, args.output)
            result = {
                "manifest": str(_contained_absolute(_root_path(args.root), args.output, must_exist=True)),
                "request_hash": manifest["request_hash"],
                "files": len(manifest["files"]),
            }
        else:
            manifest = verify_manifest(args.root, args.manifest)
            result = {
                "valid": True,
                "manifest": str(_contained_absolute(_root_path(args.root), args.manifest, must_exist=True)),
                "files_checked": len(manifest["files"]),
            }
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

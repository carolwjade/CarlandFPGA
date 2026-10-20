"""Read-only integrity audit for the pinned operation-12 source snapshot."""
import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_HEAD = "f7e95af8f8abae6d4a5312c08d99e095a7e5dec1"
EXPECTED_PARENT = "61141302a68c3085951721074abbfeec31bfcb3a"
EXPECTED_REQUEST = "9951beb894c52fa1e9ec6ae6f487856125a9a91e7e91b8aae75c297b04420e56"
EXPECTED_MANIFEST = "6d6de98ec58741efdd20110dba91ea3cff644ae59901413910fc654376b7cd04"
EXPECTED_REQUIREMENTS = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
EXPECTED_RTL = "9dc8ecf96e59a2ae8467bda64572f62eb602d52db535733f236f64ff97c43428"
EXPECTED_MAIN_TB = "7bff8dbcdb4325910de35e498aea3ebe770db0b6b8ab1280009363f02d9cd228"
EXPECTED_HISTORICAL_VERIFIER = "ba2491beffd479c2f1e28ab63dd7eefa4df82d29bf8e0bc2cb80856665cb6839"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def blob_id(data):
    prefix = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(prefix + data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    snapshot = repo / ".planning/deepeye-resume-20261018/b-pr30-followup-20261020/source"
    artifact_path = snapshot.parent / "artifact-integrity.json"
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite {args.output}")

    integrity_bytes = artifact_path.read_bytes()
    integrity = json.loads(integrity_bytes)
    manifest_path = snapshot / "handoffs/b/B-DEEPEYE-PWM-ATOMIC-20261020-12/manifest.json"
    input_path = snapshot / "handoffs/b/B-DEEPEYE-PWM-ATOMIC-20261020-12/input.json"
    manifest_bytes = manifest_path.read_bytes()
    input_bytes = input_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    request_file = json.loads(input_bytes)

    actual_files = sorted(
        path.relative_to(snapshot).as_posix()
        for path in snapshot.rglob("*") if path.is_file()
    )
    expected_files = sorted(integrity["files"])
    missing = sorted(set(expected_files) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected_files))
    if missing or extra:
        raise SystemExit(f"file-set mismatch missing={missing} extra={extra}")
    if len(actual_files) != 357 or integrity["selected_files"] != 357:
        raise SystemExit("selected-file count mismatch")
    if len(integrity["files"]) != 357:
        raise SystemExit("integrity entry count mismatch")

    entries = {}
    blob_mismatches = []
    digest = hashlib.sha256()
    for relative in actual_files:
        data = (snapshot / relative).read_bytes()
        actual = {"bytes": len(data), "sha256": sha256(data), "git_blob": blob_id(data)}
        expected = integrity["files"][relative]
        if actual != expected:
            blob_mismatches.append({"path": relative, "expected": expected, "actual": actual})
        entries[relative] = actual
        digest.update(f"{relative}\t{actual['bytes']}\t{actual['sha256']}\n".encode("utf-8"))
    if blob_mismatches:
        raise SystemExit("selected-file identity mismatch: " + json.dumps(blob_mismatches[:3]))

    manifest_files = manifest["files"]
    if len(manifest_files) != 353 or integrity["manifest_entries"] != 353:
        raise SystemExit("manifest entry count mismatch")
    expected_artifacts = set(request_file["artifacts"])
    if set(manifest_files) != expected_artifacts:
        raise SystemExit("manifest and request artifact set differ")
    manifest_mismatches = []
    for relative, expected in manifest_files.items():
        actual = entries.get(relative)
        pinned = {"sha256": actual["sha256"], "size": actual["bytes"]} if actual else None
        if actual is None or pinned != expected:
            manifest_mismatches.append({"path": relative, "expected": expected, "actual": pinned})
    if manifest_mismatches:
        raise SystemExit("manifest identity mismatch: " + json.dumps(manifest_mismatches[:3]))

    canonical_request = json.dumps(
        request_file["request"], sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    request_hash = sha256(canonical_request)
    if request_hash != EXPECTED_REQUEST:
        raise SystemExit(f"request hash mismatch: {request_hash}")
    if integrity["request_hash"] != EXPECTED_REQUEST or manifest["request_hash"] != EXPECTED_REQUEST:
        raise SystemExit("request hash does not match pinned metadata")
    if integrity["tested_head"] != EXPECTED_HEAD or integrity["code_commit"] != EXPECTED_PARENT:
        raise SystemExit("head/parent pin mismatch")

    scope_path = repo / "docs/competition/deepeye-2026/immutable_scope.json"
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    canonical_scope = json.dumps(
        scope["requirements"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    scope_hash = sha256(canonical_scope)
    if scope_hash != EXPECTED_REQUIREMENTS:
        raise SystemExit(f"requirements hash mismatch: {scope_hash}")
    requirement_ids = [item["id"] for item in scope["requirements"]]
    if requirement_ids != [f"H{number:02d}" for number in range(1, 16)]:
        raise SystemExit("H01-H15 ids mismatch")

    relevant = {
        "rtl": "competition/deepeye/fpga/control3d/deepeye_atomic_pwm.sv",
        "main_tb": "competition/deepeye/tests/rtl/control3d/main_tb_atomic_pwm.sv",
        "verifier": "competition/deepeye/tools/control3d/main_verify_atomic_pwm.py",
        "author_tb": "competition/deepeye/tests/rtl/control3d/tb_atomic_pwm.sv",
        "author_runner": "competition/deepeye/tools/control3d/run_atomic_pwm.py",
        "oracle": "competition/deepeye/evidence/control3d/pwm-atomic-20261020-12/main/oracle_frozen.json",
        "candidate_note": "competition/deepeye/fpga/control3d/atomic_pwm_candidate.md",
    }
    relevant_hashes = {name: entries[path]["sha256"] for name, path in relevant.items()}
    if relevant_hashes["rtl"] != EXPECTED_RTL:
        raise SystemExit("RTL pin mismatch")
    if relevant_hashes["main_tb"] != EXPECTED_MAIN_TB:
        raise SystemExit("main TB pin mismatch")

    cache_dirs = sorted(str(path.relative_to(snapshot)) for path in snapshot.rglob("__pycache__"))
    if cache_dirs:
        raise SystemExit("unexpected source pycache: " + json.dumps(cache_dirs))

    output = {
        "schema": 1,
        "status": "passed",
        "snapshot_root": str(snapshot),
        "snapshot_aggregate_sha256": digest.hexdigest(),
        "selected_files": len(actual_files),
        "manifest_entries": len(manifest_files),
        "selected_not_in_manifest": sorted(set(actual_files) - set(manifest_files)),
        "all_selected_size_sha256_git_blob_match": True,
        "all_manifest_size_sha256_match": True,
        "all_tar_members_safe": integrity["all_tar_members_safe"],
        "archive": {"bytes": integrity["tar_bytes"], "sha256": integrity["tar_sha256"]},
        "artifact_integrity": {
            "bytes": len(integrity_bytes), "sha256": sha256(integrity_bytes)
        },
        "manifest_file": {"bytes": len(manifest_bytes), "sha256": sha256(manifest_bytes)},
        "input_file": {"bytes": len(input_bytes), "sha256": sha256(input_bytes)},
        "request": {
            "canonical_bytes": len(canonical_request), "sha256": request_hash
        },
        "pins": {
            "tested_head": EXPECTED_HEAD,
            "code_parent": EXPECTED_PARENT,
            "manifest_sha256": EXPECTED_MANIFEST,
            "requirements_sha256": scope_hash,
            "requirement_ids": requirement_ids,
            "historical_verifier_in_run03": EXPECTED_HISTORICAL_VERIFIER,
        },
        "relevant_hashes": relevant_hashes,
        "source_pycache_dirs": cache_dirs,
        "files": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in output if key != "files"}, indent=2))


if __name__ == "__main__":
    main()

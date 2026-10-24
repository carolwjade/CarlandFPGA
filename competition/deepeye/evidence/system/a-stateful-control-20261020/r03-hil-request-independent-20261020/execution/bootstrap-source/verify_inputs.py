"""Read-only input verification; writes evidence only in this assignment."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
AUTHOR = D.parent / "r03-hil-request-implementation-20261020"
WORKTREE = ROOT / ".local/deepeye-implementation-a"
PRODUCT = WORKTREE / "competition/deepeye"
LOCK = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
MANIFEST = "b1e2fe9cd8be1991cefd3b74dcc083d89e1965621fa92132dd178d122bdcced2"


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def save(name, value):
    with (D / name).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


def verify():
    manifest_path = AUTHOR / "artifact-manifest.json"
    assert pin(manifest_path)["sha256"] == MANIFEST
    manifest = json.loads(manifest_path.read_bytes())
    actual = {}
    for relative, expected in manifest["files"].items():
        assert relative not in ("lease.private.json", "reserve-request.json")
        path = (AUTHOR / relative).resolve()
        assert path.is_relative_to(AUTHOR.resolve())
        actual[relative] = pin(path)
        assert actual[relative] == expected, (relative, actual[relative], expected)
    assert len(actual) == 43
    pairs = {
        "integration/hil_request_tracker.py": "hil_request_tracker.py",
        "integration/test_hil_request_tracker.py": "test_hil_request_tracker.py",
        "tests/vectors/r03_hil_request_lifecycle.json": "r03_hil_request_lifecycle.json",
    }
    product = {}
    for relative, snapshot in pairs.items():
        path = PRODUCT / relative
        product[relative] = pin(path)
        assert path.read_bytes() == (AUTHOR / "final-source" / snapshot).read_bytes()
        assert path.read_bytes() == (AUTHOR / "final-green" / snapshot).read_bytes()
    baseline = json.loads((AUTHOR / "baseline.json").read_bytes())
    baseline_current = {}
    for relative, expected in baseline["input_pins"].items():
        baseline_current[relative] = pin(WORKTREE / relative)
        assert baseline_current[relative] == expected, relative
    dirty = {}
    for relative, expected in baseline["C_dirty_files"].items():
        dirty[relative] = pin(WORKTREE / relative)
        assert dirty[relative]["sha256"] == expected, relative
    contract = json.loads((ROOT / "docs/competition/deepeye-2026/immutable_scope.json").read_bytes())
    canonical = hashlib.sha256(json.dumps(contract["requirements"], sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    assert canonical == contract["requirements_sha256"] == LOCK
    assert [r["id"] for r in contract["requirements"]] == [f"H{i:02}" for i in range(1, 16)]
    transfer_path = ROOT / ".planning/deepeye-desktop-handoff-20261015/transfer.json"
    transfer = json.loads(transfer_path.read_bytes())
    assert transfer["status"] == "active" and transfer["director_generation"] == 2
    assert transfer["new_director_thread_id"] == "01a13d7e-dcf1-7272-a738-a637dd62ff9d"
    completed = json.loads((AUTHOR / "native-complete-response.json").read_bytes())
    assert completed["status"] == "completed" and completed["terminal"] is True
    assert completed["result"]["text"] == (AUTHOR / "final-result.txt").read_text(encoding="utf-8")
    return {
        "author_manifest": pin(manifest_path), "author_files": actual,
        "author_original_completed_terminal_exact": True,
        "author_completion": pin(AUTHOR / "native-complete-response.json"),
        "product_equals_final_source_and_tested_snapshot": product,
        "baseline_inputs_unchanged": baseline_current, "C_dirty_unchanged": dirty,
        "requirements_sha256": canonical, "transfer": pin(transfer_path),
        "director_active_generation": 2,
        "independent_tests": "not_run_by_this_static_verifier",
    }


if __name__ == "__main__":
    result = verify()
    save("input-verification.json", result)
    print(json.dumps({"author_files": len(result["author_files"]),
        "product_snapshot_pairs": len(result["product_equals_final_source_and_tested_snapshot"]),
        "baseline_input_pins": len(result["baseline_inputs_unchanged"]),
        "dirty_pins": len(result["C_dirty_unchanged"]), "verified": True}))

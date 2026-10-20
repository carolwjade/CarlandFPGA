"""Read-only identity audit; outputs restricted to this assignment directory."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / ".local/deepeye-implementation-a"
AUTHOR = D.parent / "r03-mailbox-implementation-20261020"
EXPECTED_MANIFEST = "b2ff0aa626b0a391594f169ad7bb9d54c2dfd199fa13c76d745d5e56b4ff539b"
REQUIREMENTS = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"

def identify(path):
    assert not path.is_symlink() and not (path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def run(label):
    assert label in ("initial", "final")
    manifest_path = AUTHOR / "artifact-manifest.json"
    assert identify(manifest_path)["sha256"] == EXPECTED_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest["files"]
    assert len(files) == 46
    actual = {}
    for relative, expected in files.items():
        parts = Path(relative).parts
        assert ".." not in parts and not Path(relative).is_absolute()
        assert not any("private" in p.lower() or "lease" in p.lower() for p in parts)
        actual[relative] = identify(AUTHOR / relative)
        assert actual[relative] == expected, relative
    baseline = json.loads((AUTHOR / "baseline.json").read_text(encoding="utf-8"))
    inputs = {}
    for relative, expected in baseline["input_pins"].items():
        inputs[relative] = identify(PRODUCT / relative)
        assert inputs[relative] == expected, relative
    dirty = {}
    for relative, digest in baseline["C_dirty_files"].items():
        dirty[relative] = identify(PRODUCT / relative)
        assert dirty[relative]["sha256"] == digest, relative
    new = {}
    for relative in baseline["new_owned_files_absent"]:
        current = identify(PRODUCT / relative)
        snapshot = AUTHOR / "final-source" / Path(relative).name
        assert identify(snapshot) == current, relative
        assert files["final-source/" + Path(relative).name] == current
        new[relative] = current
    scope_path = ROOT / "docs/competition/deepeye-2026/immutable_scope.json"
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    canonical = json.dumps(scope["requirements"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == scope["requirements_sha256"] == REQUIREMENTS
    assert [r["id"] for r in scope["requirements"]] == [f"H{i:02}" for i in range(1, 16)]
    transfer_path = ROOT / ".planning/deepeye-desktop-handoff-20261015/transfer.json"
    transfer = json.loads(transfer_path.read_text(encoding="utf-8"))
    assert transfer["status"] == "active" and transfer["director_generation"] == 2
    assert transfer["new_director_thread_id"] == "01a13d7e-dcf1-7272-a738-a637dd62ff9d"
    assert transfer["requirements_sha256"] == REQUIREMENTS
    validation = json.loads((D / "native-validate-response.json").read_text(encoding="utf-8"))
    # Validation shape is persisted by the safe helper; its contents are public.
    result = {
        "label": label, "author_manifest": identify(manifest_path), "author_files": actual,
        "input_pins": inputs, "C_dirty_pins": dirty, "product_final_source_identity": new,
        "scope_file": identify(scope_path), "requirements_sha256": REQUIREMENTS,
        "transfer_file": identify(transfer_path), "active_director_generation": 2,
        "product_acceptance": "all29/R03 not_run",
        "baseline_head_record_only": baseline["head"],
        "no_current_head_execution_claim": True,
    }
    if label == "final":
        before = json.loads((D / "initial-audit.json").read_text(encoding="utf-8"))
        for key in ("author_manifest", "author_files", "input_pins", "C_dirty_pins", "product_final_source_identity", "scope_file", "transfer_file"):
            assert result[key] == before[key], key
        result["all_initial_identities_unchanged"] = True
    with (D / f"{label}-audit.json").open("x", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"label": label, "author_files": len(actual), "product_files": len(new), "inputs": len(inputs), "C_dirty": len(dirty), "requirements_sha256": REQUIREMENTS, "verified": True}))

if __name__ == "__main__":
    run(sys.argv[1])

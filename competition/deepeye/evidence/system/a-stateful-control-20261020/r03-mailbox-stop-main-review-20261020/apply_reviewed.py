import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
OUT = D.parent
ROOT = OUT.parents[1]
PRODUCT = ROOT / ".local/deepeye-implementation-a"
AUTHOR = OUT / "r03-mailbox-stop-fix-20261020"
INTEGRATION = PRODUCT / "competition/deepeye/integration"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


audit = json.loads((D / "initial-audit.json").read_bytes())
assert audit["exact_result"] and audit["implementation_exact_single_decorator"]
for path, row in audit["original_inputs"].items():
    assert sha(Path(path)) == row["sha256"]
checks = json.loads((D / "stop-callshape-01/checks.json").read_bytes())
terminal = json.loads((D / "stop-callshape-01/terminal.json").read_bytes())
assert checks["tests_run"] == 3
assert not any(checks[key] for key in ("failures", "errors", "skipped", "prohibited_attempts"))
assert terminal["status"] == "success" and terminal["exit_code"] == 0
assert terminal["all_processes_terminated"] and terminal["active_processes_final"] == 0
assert all(p["signaled"] and p["wait_result"] == 0 for p in terminal["held_members"])
assert checks["module_file_hashes"][str(D / "candidate_mailbox.py")] == audit["proposed_module_sha256"]
assert len(checks["traces"]) == 2
for trace in checks["traces"]:
    assert trace["after_invalid_call"]["stopped"]
    assert trace["after_invalid_call"]["pending_candidate_id"] is None
    assert trace["subsequent_consume_candidate_id"] is None
protected = {
    "docs/competition/deepeye-2026/.gitattributes": "bd36dbd14f9885f0a63e1fab18064bbd0bbe44f200fe97c95129e867b2972e44",
    "competition/deepeye/ai_pc/host_timing/reference.py": "22885eb958a1839f628a2f82e3f9d7b1bd2022b40ed8b47df05f22343ac372f0",
    "competition/deepeye/evidence/ai/host_timing/reference_evidence.txt": "b4fc17dd93cbad0e9449e9b1c3c8571451d4a065393267360eba1544b96f3713",
    "competition/deepeye/tests/ai/host_timing/test_reference.py": "bbc1fdcdc2d71327ce4907493e35ed60fc3b65523a05cc52855f1d46b4efa013",
}
for rel, digest in protected.items():
    assert sha(PRODUCT / rel) == digest
files = {}
for name, expected in [
    ("candidate_mailbox.py", audit["proposed_module_sha256"]),
    ("test_candidate_mailbox.py", audit["proposed_test_sha256"]),
]:
    source = AUTHOR / "proposed" / name
    assert sha(source) == expected
    destination = INTEGRATION / name
    with (D / ("pre-application-" + name)).open("xb") as f:
        f.write(destination.read_bytes())
    destination.write_bytes(source.read_bytes())
    assert sha(destination) == expected
    files[destination.relative_to(PRODUCT).as_posix()] = expected
for path, row in audit["original_inputs"].items():
    if Path(path).name not in ("candidate_mailbox.py", "test_candidate_mailbox.py"):
        assert sha(Path(path)) == row["sha256"]
for rel, digest in protected.items():
    assert sha(PRODUCT / rel) == digest
save(D / "application.json", {
    "utc": datetime.now(timezone.utc).isoformat(),
    "files": files, "independent_focused_tests": 3,
    "author_final_tests": 30, "distinct_suites": True,
    "original_failures_preserved": True, "protected_files": protected,
    "R03": "not_run", "full_H12": "not_run", "all29": "not_run",
})
print(json.dumps({"applied": files, "independent_tests": 3,
                  "source_identity_verified": True, "all29": "not_run"}))

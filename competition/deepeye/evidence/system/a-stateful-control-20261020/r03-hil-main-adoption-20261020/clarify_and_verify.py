import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
OUT = D.parent
ROOT = OUT.parents[1]
PRODUCT = ROOT / ".local/deepeye-implementation-a"
SOURCE = PRODUCT / "competition/deepeye/integration/hil_request_tracker.py"
GUIDE = PRODUCT / "competition/deepeye/docs/hil_request_tracker.md"
LOCK = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def executable(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


scope = json.loads((ROOT / "docs/competition/deepeye-2026/immutable_scope.json").read_bytes())
assert sha(json.dumps(scope["requirements"], ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode()) == LOCK
transfer = json.loads((ROOT / ".planning/deepeye-desktop-handoff-20261015/transfer.json").read_bytes())
assert transfer["status"] == "active" and transfer["director_generation"] == 2
assert transfer["new_director_thread_id"] == "01a13d7e-dcf1-7272-a738-a637dd62ff9d"
assert json.loads((OUT / "next-software-main-20261020/hil-independent-verified.json").read_bytes())["exact_result"]

protected = {
    "docs/competition/deepeye-2026/.gitattributes": "bd36dbd14f9885f0a63e1fab18064bbd0bbe44f200fe97c95129e867b2972e44",
    "competition/deepeye/ai_pc/host_timing/reference.py": "22885eb958a1839f628a2f82e3f9d7b1bd2022b40ed8b47df05f22343ac372f0",
    "competition/deepeye/evidence/ai/host_timing/reference_evidence.txt": "b4fc17dd93cbad0e9449e9b1c3c8571451d4a065393267360eba1544b96f3713",
    "competition/deepeye/tests/ai/host_timing/test_reference.py": "bbc1fdcdc2d71327ce4907493e35ed60fc3b65523a05cc52855f1d46b4efa013",
}
for rel in ("competition/deepeye/integration/test_hil_request_tracker.py",
            "competition/deepeye/tests/vectors/r03_hil_request_lifecycle.json"):
    protected[rel] = sha((PRODUCT / rel).read_bytes())
for rel, digest in protected.items():
    assert sha((PRODUCT / rel).read_bytes()) == digest

before = SOURCE.read_bytes()
assert sha(before) == "7e3b9f8661eb54b51c504ec1d32adef2c39d7168ae53987a91b65ce4ccd9c77f"
assert not GUIDE.exists()
old = b"    Foreign-thread input requests a pending STOP; owner drains before publishing."
new = (
    b"    Foreign-thread input queues STOP for the next owner entry/fence.\r\n"
    b"    A successful response diagnostic linearizes at the final fence's last\r\n"
    b"    pending-STOP observation. Later overlapping STOP is drained on the next\r\n"
    b"    owner entry; an immutable diagnostic is never a continuing authorization."
)
assert before.count(old) == 1
after = before.replace(old, new)
assert executable(before) == executable(after)
with (D / "before.py").open("xb") as f:
    f.write(before)
with (D / "after.py").open("xb") as f:
    f.write(after)
with (D / "documentation.diff").open("x", encoding="utf-8") as f:
    f.writelines(difflib.unified_diff(before.decode().splitlines(keepends=True),
                                     after.decode().splitlines(keepends=True),
                                     fromfile="reviewed/hil_request_tracker.py",
                                     tofile="clarified/hil_request_tracker.py"))
guide = """# HIL request tracker caller contract

`HilRequestTracker` is a bounded, serialized software diagnostic. It binds
retries and responses to the original request and never grants permission
to send a command or move the simulator or board.

The constructing thread owns every API call. A call from another thread is
rejected and queues STOP. The owner drains queued STOP on entry and at
verification fences. For a successful `response`, its last pending-STOP
observation inside the final fence is the diagnostic's linearization point.
A foreign STOP overlapping after that observation may be ordered after the
diagnostic and is drained on the next owner entry. A returned immutable
`Association` can immediately become stale.

STOP queued before an owner call is drained before that call can qualify a
response. STOP queued during a synchronous verifier is drained by its return
fence and vetoes the transition. A STOP after the final fence is handled on
the next owner entry. The independent review retained 25 of 26 passing tests,
one failure asserting a stronger before-return promise, and a separate
passing pre-entry control. That failure remains evidence of the former
overbroad documentation; no executable behavior was changed to relabel it.

`now_ns` is the explicitly supplied instant at which the diagnostic is
evaluated. It is not a trusted clock source. Real authority must obtain
current trusted time after verifier work and at each physics/send action,
serialize STOP with those actions, and check its own authoritative gate.
It must not treat a previously returned `qualified=True` as an active lease.

BOOT, sensor source, timing bounds and independent capture require actual
upstream verifiers. The provided record types, hashes and opaque objects
are containers, not credentials. Missing evidence remains unknown. The
helper does not provide a board watchdog, transport, AI, runtime activation,
or PC_DIRECT-to-board-capture substitution.

Histories are capped at 16 requests, four observations and 64 sessions.
The original first-send TTL and original observation-age cap never renew
on retries or responses. Real restart uniqueness, measured timing, both
complete H12 control chains and the remaining R03 gates require integration.

This adoption is bounded software evidence. R03, G05, full H12 and all 29
formal taskbook cards remain `not_run`. H01-H15 are unchanged under
`DEEPEYE-HUMAN-LOCK-20261014/revision1`.
"""
with GUIDE.open("x", encoding="utf-8", newline="\n") as f:
    f.write(guide)
SOURCE.write_bytes(after)
assert SOURCE.read_bytes() == after
for rel, digest in protected.items():
    assert sha((PRODUCT / rel).read_bytes()) == digest
save(D / "verification.json", {
    "utc": datetime.now(timezone.utc).isoformat(),
    "work_id": "A-R03-HIL-DIAGNOSTIC-DOCUMENTATION-20261020-v1",
    "before_sha256": sha(before), "after_sha256": sha(after),
    "executable_ast_equal_excluding_docstrings": True,
    "guide_sha256": sha(GUIDE.read_bytes()),
    "unchanged_files": protected, "requirements_sha256": LOCK,
    "independent_original_tests": {"passed": 25, "total": 26, "failure_retained": True},
    "separate_pre_entry_control_exit": 0, "runtime_rerun": False,
    "all29": "not_run", "R03": "not_run", "full_H12": "not_run",
})
print(json.dumps({"documentation_updated": True, "executable_ast_equal": True,
                  "after_sha256": sha(after), "protected_files_unchanged": len(protected)}))

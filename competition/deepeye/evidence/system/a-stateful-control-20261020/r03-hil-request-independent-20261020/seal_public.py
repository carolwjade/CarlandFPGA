"""Freeze the read-only review: no tracker/test imports or execution."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
P = ROOT / ".local/deepeye-implementation-a"
A = D.parent / "r03-hil-request-implementation-20261020"
sys.path.insert(0, str(D))
from verify_inputs import verify, save, pin

started = time.monotonic()
before = json.loads((D / "input-verification.json").read_bytes())
assert verify() == before
controls = json.loads((D / "controls-results.json").read_bytes())
assert (controls["tests_run"], controls["failures"], controls["errors"], controls["skipped"]) == (26, 1, 0, 0)
assert sum(r["status"] == "passed" for r in controls["rows"]) == 25
assert len(controls["rows"]) == 26 and controls["all_inputs_unchanged"]
assert controls["prohibited_attempts"] == []
failed = [r for r in controls["rows"] if r["status"] == "failed"]
assert len(failed) == 1 and failed[0]["test"].endswith("test_foreign_thread_after_final_fence_cannot_publish_qualified")
assert "True is not false" in failed[0]["traceback"]
traces = json.loads((D / "literal-traces.json").read_bytes())
race = next(r for r in traces["test_foreign_thread_after_final_fence_cannot_publish_qualified"] if r["event"] == "publication_race")
assert race["injection_line"] == [463] and race["returned_qualified"] is True
assert race["next_owner_snapshot_stopped"] is True and race["returned_deadline_ns"] == 1258*10**6
assert race["errors"] == ["constructing serialized owner required"]

run_summaries = {}
for label in ("execution", "execution-controls", "execution-prequeued"):
    execution = D / label
    ended = json.loads((execution / "terminal.json").read_bytes())
    began = json.loads((execution / "started.json").read_bytes())
    assert ended["exit_code"] == (0 if label == "execution-prequeued" else 1) and ended["all_processes_terminated"] is True
    assert ended["active_processes_final"] == 0 and not ended["faults"]
    assert all(r["wait_result"] == 0 and r["signaled"] for r in ended["held_members"])
    assert ended == json.loads((execution / "process/terminal.json").read_bytes())
    for stream, expected in ended["logs"].items():
        assert pin(execution / "process" / f"{stream}.txt") == expected
    source = execution / "bootstrap-source" if label == "execution" else D
    for name, sha in began["source_pins"].items():
        assert pin(source / name)["sha256"] == sha
    run_summaries[label] = {"exit":ended["exit_code"], "seconds":ended["seconds"],
        "launcher_pid":ended["launcher_pid"], "held_members":ended["held_members"],
        "terminal_pin":pin(execution / "terminal.json"), "started_pin":pin(execution / "started.json")}
assert controls["worker_pid"] in [r["pid"] for r in run_summaries["execution-controls"]["held_members"]]
assert controls["worker_parent_pid"] == run_summaries["execution-controls"]["launcher_pid"]
pending = json.loads((D / "pending-before-entry-result.json").read_bytes())
assert pending["status"] == "passed" and pending["all_input_pins_unchanged"]
assert not pending["blocked_attempts"] and pending["snapshot_stopped"]
assert pending["worker_pid"] in [r["pid"] for r in run_summaries["execution-prequeued"]["held_members"]]
assert pending["worker_parent_pid"] == run_summaries["execution-prequeued"]["launcher_pid"]
assert pending["literal_source"] == pin(D / "literal-traces.json")
assert [e["event"] for e in pending["events"]] == ["baseline_response",
    "foreign_stop_called", "foreign_stop_rejected", "foreign_thread_joined_before_owner_call",
    "owner_response_after_prequeued_stop"]
assert pending["events"][0]["qualified"] is True
assert pending["events"][-1]["qualified"] is False and pending["events"][-1]["status"] == "stopped"
for name, expected in pending["module_file_pins"].items():
    assert pin(Path(name)) == expected, name
save("three-stop-orderings.json", {
    "before_owner_entry":{"evidence":"pending-before-entry-result.json",
        "result":"pending STOP drained; response stopped/unqualified", "exit":0,
        "same_saved_packet_bytes":True},
    "during_verifier":{"evidence":"controls-results.json",
        "test":"test_foreign_thread_inside_verifier_is_fenced",
        "result":"callback fence raises ValueError; owner stopped", "test_status":"passed",
        "rerun":False},
    "after_final_fence":{"evidence":"literal-traces.json",
        "test":"test_foreign_thread_after_final_fence_cannot_publish_qualified",
        "injected_line":463, "result":"qualified diagnostic returned; next owner drains STOP",
        "strong_before_publication_assertion":"retained failure", "rerun":False},
    "interpretation":"post-fence overlap may linearize after diagnostic; before-publishing wording is broader; main decides code/documentation contract",
    "motion_authority_or_TTL_violation_proven":False,
})

imports = json.loads((D / "imports-and-reads.json").read_bytes())
assert imports["no_private_lease_read"] and imports["prohibited_attempts"] == []
assert imports["no_production_encoder_or_author_tests_used"] and imports["product_writes"] == 0
for name, expected in imports["module_file_pins"].items():
    assert pin(Path(name)) == expected, name
    assert "candidate_mailbox" not in name and "test_hil_request_tracker" not in name
assert not any("lease.private.json" in p for p in imports["read_paths"])
controls_ast = ast.parse((D / "review_controls.py").read_text(encoding="utf-8"))
assert not any(isinstance(n, ast.Attribute) and n.attr == "encode" and
    isinstance(n.value, ast.Name) and n.value.id in ("wire", "hil") for n in ast.walk(controls_ast))

spec = [
    (P / "competition/deepeye/integration/hil_request_tracker.py", [(37,65),(159,221),(236,284),(324,384),(399,491)]),
    (P / "competition/deepeye/integration/host_envelope.py", [(1,24),(484,574)]),
    (P / "competition/deepeye/docs/host_timing_contract.md", [(49,83)]),
    (P / "docs/competition/deepeye-2026/taskbook_final.md", [(126,142),(264,274),(340,348)]),
    (A / "api-resolution.md", [(1,99)]),
]
evidence = []
for path, ranges in spec:
    lines = path.read_text(encoding="utf-8").splitlines()
    evidence.append({"path":str(path), **pin(path), "extracts":[
        {"start":lo, "end":min(hi,len(lines)), "lines":[{"line":i+1,"text":lines[i]}
            for i in range(lo-1,min(hi,len(lines)))]} for lo,hi in ranges]})
save("source-evidence.json", evidence)
save("recorded-evidence-verification.json", {"author_and_product_pins_unchanged":True,
    "imports_rehashed":len(imports["module_file_pins"]), "prequeued_imports_rehashed":len(pending["module_file_pins"]),
    "runs":run_summaries,
    "tests_rerun_during_seal":0, "failure_count_preserved":1,
    "scope":"static read/hash/AST only", "requirements_sha256":before["requirements_sha256"]})

exclude = {"lease.private.json", "reserve-request.json", "nonsecret-artifact-manifest.json",
    "seal-result.json", "native-complete-response.json"}
files, directories = {}, []
for root, dirs, names in os.walk(D, followlinks=False):
    base = Path(root)
    for name in dirs:
        path = base / name
        assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        directories.append(path.relative_to(D).as_posix())
    for name in names:
        relative = (base / name).relative_to(D).as_posix()
        if relative in exclude:
            continue
        path = base / name
        assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        files[relative] = pin(path)
manifest = {"schema":1, "work_id":"A-R03-HIL-REQUEST-INDEPENDENT-20261020-v1",
    "files":dict(sorted(files.items())), "directories":sorted(directories),
    "exclusions":sorted(exclude), "requirements_sha256":before["requirements_sha256"],
    "formal_all29_R03_G05_full_H12":"not_run"}
save("nonsecret-artifact-manifest.json", manifest)
for relative, expected in manifest["files"].items():
    assert pin(D / relative) == expected
result = {"verified":True, "files":len(files), "directories":len(directories),
    "manifest":pin(D / "nonsecret-artifact-manifest.json"), "seconds":time.monotonic()-started,
    "review_outcome":"26 tests:25 pass / 1 retained strong-publication assertion failure; additional prequeued control passed; main linearization/code/docs disposition pending",
    "test_replays":0, "all_owned_test_processes_terminated":True}
save("seal-result.json", result)
print(json.dumps(result, ensure_ascii=False))

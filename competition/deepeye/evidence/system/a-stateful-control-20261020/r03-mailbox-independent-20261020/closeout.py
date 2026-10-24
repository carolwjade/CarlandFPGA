"""Freeze this review after evidence verification; no execution or source fix."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from audit_inputs import run, identify, PRODUCT, AUTHOR, REQUIREMENTS

def save(name, value):
    with (D / name).open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2, ensure_ascii=False)
        out.write("\n")

def main():
    runs = {}
    imports = {}
    held = []
    for label, count in (("suite-01", 16), ("stop-callshape-01", 3)):
        terminal = json.loads((D / label / "terminal.json").read_text(encoding="utf-8"))
        start = json.loads((D / label / "started.json").read_text(encoding="utf-8"))
        checks = json.loads((D / label / "checks.json").read_text(encoding="utf-8"))
        assert terminal["exit_code"] == 1 and terminal["stop_reason"] is None
        assert terminal["status"] == "failed"
        assert terminal["all_processes_terminated"] and terminal["active_processes_final"] == 0
        assert terminal["total_job_processes"] == 3 and len(terminal["held_members"]) == 3
        assert not terminal["faults"] and not terminal["absent_before_handle_open"]
        assert all(m["signaled"] and m["wait_result"] == 0 for m in terminal["held_members"])
        assert start["hidden"] and start["private_job"] and start["assigned_before_resume"]
        assert start["priority"] == "below_normal"
        assert checks["tests_run"] == count and not checks["errors"] and not checks["skipped"]
        assert not checks["prohibited_attempts"] and len(checks["failures"]) == 2
        assert all("test_malformed_stop_call_must_latch_stop" in f["test"] for f in checks["failures"])
        traces = [r for r in checks["traces"] if r.get("case") == "malformed_stop"]
        assert {t["mode"] for t in traces} == {1, 2}
        assert all(t["exception"] == "TypeError" and not t["after_invalid_call"]["stopped"]
                   and t["subsequent_consume_candidate_id"] == 1 for t in traces)
        for name in ("stdout", "stderr"):
            assert identify(D / label / (name + ".txt")) == terminal["logs"][name]
        for filename, expected in checks["module_file_hashes"].items():
            actual = identify(Path(filename))
            assert actual["sha256"] == expected, filename
            if filename in imports:
                assert imports[filename] == actual
            imports[filename] = actual
        held.extend(terminal["held_members"])
        runs[label] = {
            "test_methods": count, "failing_subcases": 2, "errors": 0, "skips": 0,
            "exit_code": 1, "failure": "R03-MBIR-01", "seconds": terminal["seconds"],
            "module_file_count": len(checks["module_file_hashes"]),
            "all_processes_terminated": True, "held_process_objects": len(terminal["held_members"]),
            "prohibited_attempts": [],
        }
    assert len({(m["pid"], m["creation_filetime"]) for m in held}) == 6
    save("import-pin-readback.json", {
        "unique_files": len(imports), "all_recorded_imports_currently_identical": True, "files": imports,
        "note": "Exact bytes for imports used in bounded tests; no provider authentication claim.",
    })
    run("final")
    result = {
        "work_id": "A-R03-MAILBOX-INDEPENDENT-20261020-v1",
        "job_id": "child-2658fcebb6e94501aefddf919647e34e",
        "agent_id": "/root/g03_controls_reference_review_20261020",
        "review_outcome": "one reproducible defect submitted to main; main decides acceptance",
        "findings": [{"id": "R03-MBIR-01", "proposed_priority": "P2",
                      "path": "competition/deepeye/integration/candidate_mailbox.py",
                      "lines": [315, 316], "sha256": identify(PRODUCT / "competition/deepeye/integration/candidate_mailbox.py")["sha256"],
                      "trigger": "stop(reason='emergency', unexpected=True)",
                      "actual": "TypeError; pending remains; subsequent exact-slot consume returns candidate1 in both modes",
                      "expected": "invalid public input latches STOP, no subsequent selection"}],
        "runs": runs, "distinct_held_process_objects_signaled": 6,
        "independent_saved_vector_calculations": 12, "new_nanosecond_boundary_mode_cases": 24,
        "all29": "not_run", "R03": "not_run", "requirements_sha256": REQUIREMENTS,
        "product_modified": False, "author_modified": False, "C_dirty_modified": False,
        "full_suite_replayed": False, "runtime_activated": False, "physical_execution": False,
        "credential_scan": "No private lease read; public serialization checked for token assignments.",
    }
    save("result.json", result)
    final_text = (
        "R03 independent mailbox review complete; one finding R03-MBIR-01 (proposed P2) submitted to main.\n"
        "candidate_mailbox.py:315-316 malformed stop(reason='emergency', unexpected=True) raises TypeError before STOP; "
        "pending candidate1 remains consumable at210ms in both H12 modes. Selection is non-authorizing; no real send/motion occurred.\n"
        "16-method independent suite:15 methods passed; two failed mode subcases of this one defect. "
        "Focused three-method reproduction retained the same two failures, with valid STOP and other invalid-call controls passing. "
        "Both executions exited1, zero errors/skips/prohibited effects; all six held process objects signaled and both jobs empty.\n"
        "All46 author artifact hashes, three product/final-source identities, nine inputs and four C dirty pins verified unchanged. "
        "Twelve saved timeline calculations and24 new nanosecond mode cases checked; original strict-deadline negative control preserved.\n"
        "Product/author files unedited; no Git, services, board, install, network, UI or full-suite replay. "
        "H01-H15 SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 preserved; all29/R03 not_run. "
        "Main decides adoption, repair and acceptance. Evidence: findings.md, result.json, artifact-manifest.json in this assignment folder.\n"
    )
    with (D / "final-result.txt").open("x", encoding="utf-8") as out:
        out.write(final_text)
    excluded = {"lease.private.json", "reserve-request.json", "native-complete-response.json", "artifact-manifest.json"}
    files, dirs = {}, []
    for directory, directory_names, names in os.walk(D, followlinks=False):
        parent = Path(directory)
        for name in directory_names:
            child = parent / name
            info = child.lstat()
            assert not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            dirs.append(child.relative_to(D).as_posix())
        for name in names:
            relative = (parent / name).relative_to(D).as_posix()
            if relative in excluded:
                continue
            assert "private" not in name.lower()
            info = (parent / name).lstat()
            assert info.st_nlink == 1 and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            content = (parent / name).read_bytes()
            assert not re.search(rb'"(?:lease_token|access_token|refresh_token)"\s*:\s*"[A-Za-z0-9_.-]{12,}"', content)
            files[relative] = identify(parent / name)
    save("artifact-manifest.json", {
        "work_id": result["work_id"], "files": dict(sorted(files.items())), "directories": sorted(dirs),
        "excluded": sorted(excluded), "completion_rule": "final-result is exact native result; terminal receipt follows manifest and is excluded",
        "requirements_sha256": REQUIREMENTS, "all29": "not_run", "R03": "not_run",
    })
    manifest = json.loads((D / "artifact-manifest.json").read_text(encoding="utf-8"))
    assert all(identify(D / rel) == pin for rel, pin in manifest["files"].items())
    print(json.dumps({"files": len(files), "directories": len(dirs),
                      "manifest_sha256": identify(D / "artifact-manifest.json")["sha256"],
                      "finding": "R03-MBIR-01", "review_complete": True, "native_complete_pending": True}))

if __name__ == "__main__":
    main()

"""Independent audit of fresh ModelSim results and author evidence bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re


EXPECTED_VECTORS = {
    "w2_t1": (7041, 309809, "792c44276245cdfb192ed3e7e9cc8f0dbed7e091fa6db59b7eb3d043511926d7"),
    "w3_t64": (26603, 1486417, "1ffad1a5a2d8c65016c6a2aa05d915255d130112a90b9d0fcc6cd5c5445d7201"),
    "w32_t32": (12546, 791834, "a399c4d33ec1dd4cd3c1301d55d456ff3c9539dd3063606c792c7db48edceee7"),
}
EXPECTED_POSITIVE = {
    "w2_t1": "MAIN_PWM_PASS rows=7041 COUNT_W=2 TAG_W=1",
    "w3_t64": "MAIN_PWM_PASS rows=26603 COUNT_W=3 TAG_W=64",
    "w32_t32": "MAIN_PWM_PASS rows=12546 COUNT_W=32 TAG_W=32",
}
EXPECTED_LONG = (
    "MAIN_PWM_LONG_PASS full_period=2000000 "
    "high_counts=10000,490000,70000 new_period=37 new_frames=2"
)
EXPECTED_MUTATION = {
    "stop_ignored": (815, 13, "got=0000000000000001 expected=0000000000000000"),
    "pitch_from_yaw": (12, 19, "got=0000000000000000 expected=0000000000000001"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def parse_vectors(path):
    lines = path.read_text(encoding="ascii").splitlines()
    require(lines and int(lines[0]) == len(lines) - 1, f"bad vector count in {path}")
    rows = []
    for line in lines[1:]:
        fields = line.split()
        require(len(fields) == 22, f"bad vector field count in {path}")
        rows.append([int(value, 16) for value in fields])
    return rows


def check_trace(path, vectors):
    lines = path.read_text(encoding="ascii").splitlines()
    require(len(lines) == len(vectors), f"trace row mismatch in {path}")
    for index, (line, expected) in enumerate(zip(lines, vectors)):
        parts = line.split()
        fields = [int(parts[0], 10), *[int(value, 16) for value in parts[1:]]]
        require(fields == [index, *expected[8:]], f"trace mismatch {path} row={index}")
    return len(lines)


def check_clean_positive(path, marker):
    raw = path.read_bytes()
    text = raw.decode("utf-8", "strict")
    require(marker in text, f"missing marker {marker}")
    require("** Error" not in text and "** Fatal" not in text, f"error/fatal in {path}")
    require("Errors: 0, Warnings: 0" in text, f"nonzero diagnostics in {path}")
    return {"bytes": len(raw), "sha256": sha(raw), "marker": marker}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--source-before", type=Path, required=True)
    parser.add_argument("--source-after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = args.review.resolve()
    before = json.loads(args.source_before.read_text(encoding="utf-8"))
    after = json.loads(args.source_after.read_text(encoding="utf-8"))
    require(before["snapshot_aggregate_sha256"] == after["snapshot_aggregate_sha256"],
            "source snapshot changed during review")
    source = Path(before["snapshot_root"])
    main_run = review / "work/main-run-04"
    result_bytes = (main_run / "result.json").read_bytes()
    result = json.loads(result_bytes)
    require(result["status"] == "passed", "main result status")
    require(result["rtl_sha256"] == "9dc8ecf96e59a2ae8467bda64572f62eb602d52db535733f236f64ff97c43428",
            "RTL pin")
    require(result["tb_sha256"] == "7bff8dbcdb4325910de35e498aea3ebe770db0b6b8ab1280009363f02d9cd228",
            "main TB pin")
    require(result["runner_sha256"] == "ba2491beffd479c2f1e28ab63dd7eefa4df82d29bf8e0bc2cb80856665cb6839",
            "runner pin")
    require(all(command["exit_code"] == 0 for command in result["commands"]), "tool exit nonzero")

    cases = {}
    total_rows = 0
    for label, (rows, size, vector_hash) in EXPECTED_VECTORS.items():
        vector_path = main_run / f"{label}.vectors.txt"
        vector_bytes = vector_path.read_bytes()
        require(len(vector_bytes) == size and sha(vector_bytes) == vector_hash, f"vector pin {label}")
        vectors = parse_vectors(vector_path)
        require(len(vectors) == rows, f"row count {label}")
        trace_rows = check_trace(main_run / f"{label}.ports.txt", vectors)
        total_rows += trace_rows
        cases[label] = check_clean_positive(main_run / f"{label}.stdout.txt", EXPECTED_POSITIVE[label])
        cases[label].update({"rows": rows, "vector_bytes": size, "vector_sha256": vector_hash})
    require(total_rows == 46190, f"edge total {total_rows}")

    long_result = check_clean_positive(main_run / "long.stdout.txt", EXPECTED_LONG)
    long_result.update({"full_frame_intervals": 2000000, "new_complete_frames": 2})

    invalid = []
    for count_w, tag_w in ((1, 32), (33, 32), (3, 0), (3, 65)):
        label = f"invalid_w{count_w}_t{tag_w}"
        stdout_path = main_run / f"{label}.stdout.txt"
        raw = stdout_path.read_bytes()
        text = raw.decode("utf-8", "strict")
        marker = f"** Fatal: ATOMIC_PWM_UNSUPPORTED_PARAMETERS COUNT_W={count_w} TAG_W={tag_w}"
        require(marker in text, f"guard marker {label}")
        require("Time: 0 ps" in text, f"guard time {label}")
        require("Errors: 1, Warnings: 0" in text, f"guard diagnostics {label}")
        require("MAIN_PWM_PASS" not in text, f"false positive marker {label}")
        command = next(item for item in result["commands"] if item["name"] == label)
        require(command["exit_code"] == 0, f"recorded guard exit {label}")
        invalid.append({"count_w": count_w, "tag_w": tag_w, "exit_code": command["exit_code"],
                        "bytes": len(raw), "sha256": sha(raw), "marker": marker,
                        "time_zero": True, "errors": 1, "warnings": 0})

    mutations = {}
    for name, (row, field, mismatch) in EXPECTED_MUTATION.items():
        run = review / f"work/mutation-{name}-01"
        data = json.loads((run / "result.json").read_text(encoding="utf-8"))
        require(data["status"] == "expected_public_port_rejection", f"mutation status {name}")
        require(data["runs"][0]["passed"] is False, f"mutation unexpectedly passed {name}")
        raw = (run / "w2_t1.stdout.txt").read_bytes()
        text = raw.decode("utf-8", "strict")
        exact = f"** Fatal: row={row} field={field} {mismatch}"
        require(exact in text, f"mutation mismatch {name}")
        require("Errors: 1, Warnings: 0" in text, f"mutation diagnostics {name}")
        mutations[name] = {"result_rtl_sha256": data["rtl_sha256"], "row": row, "field": field,
                           "bytes": len(raw), "sha256": sha(raw), "exact_fatal": exact}

    author = source / "competition/deepeye/evidence/control3d/pwm-atomic-20261020-12/main/author-rerun-01"
    manifest_bytes = (author / "AUTHOR_EVIDENCE_MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    require(manifest["status"] == "pass" and manifest["author_verification_only"] is True,
            "author evidence status")
    require(manifest["not_independent_acceptance"] is True, "author acceptance boundary")
    require(len(manifest["files"]) == 85, "author manifest count")
    manifest_path_aliases = []
    uncommitted_work_entries = []
    committed_manifest_entries = 0
    for entry in manifest["files"]:
        relative = entry["path"]
        require(".." not in Path(relative).parts and not Path(relative).is_absolute(),
                f"unsafe author path {relative}")
        if relative.startswith("work/"):
            uncommitted_work_entries.append(relative)
            continue
        payload_path = author / relative
        aliases = {"replay_events.log": "replay_events.log.txt", "transcript": "transcript.txt"}
        if not payload_path.exists() and relative in aliases:
            payload_path = author / aliases[relative]
            manifest_path_aliases.append({
                "declared_path": relative,
                "committed_path": aliases[relative],
                "reason": ".gitignore excludes **/*.log and **/transcript; committed names add .txt",
            })
        payload = payload_path.read_bytes()
        require(len(payload) == entry["size_bytes"] and sha(payload) == entry["sha256"],
                f"author byte mismatch {relative}")
        committed_manifest_entries += 1
    require(len(uncommitted_work_entries) == 45, "author work-entry count")
    require(committed_manifest_entries == 40, "author committed manifest count")
    actual_author_files = [path for path in author.rglob("*") if path.is_file()]
    require(len(actual_author_files) == 42, "author committed file count")
    summary_bytes = (author / "run_summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    require(summary["main_simulation"]["summary"]["cases"] == 9, "author case count")
    require(summary["main_simulation"]["summary"]["pass"] == 9, "author pass count")
    require(summary["main_simulation"]["summary"]["fail"] == 0, "author fail count")
    require(summary["main_simulation"]["summary"]["checks"] == 90644277, "author checks")
    require(summary["independent_acceptance"] is False, "author independence")
    require(len(summary["parameter_guards"]) == 4, "author guard count")
    for guard in summary["parameter_guards"]:
        raw = (author / guard["stdout"].replace("\\", "/")).read_bytes().decode("utf-8", "strict")
        require(guard["marker"] in raw and re.search(r"Time: 0 (?:ps|ns)", raw)
                and "Errors: 1, Warnings: 0" in raw,
                f"author guard {guard['marker']}")
        require("MAIN_PWM_PASS" not in raw, f"author guard false pass {guard['marker']}")
    replay = author / summary["replay_vectors"]["path"]
    if not replay.exists():
        replay = replay.with_name(replay.name + ".txt")
    replay_bytes = replay.read_bytes()
    require(len(replay_bytes) == summary["replay_vectors"]["size_bytes"], "author replay size")
    require(sha(replay_bytes) == summary["replay_vectors"]["sha256"], "author replay hash")
    require(len(replay_bytes.splitlines()) == 12009, "author replay lines")

    tool_paths = [
        Path(r"C:\modeltech64_2020.4\win64\vlib.exe"),
        Path(r"C:\modeltech64_2020.4\win64\vlog.exe"),
        Path(r"C:\modeltech64_2020.4\win64\vsim.exe"),
    ]
    tools = {path.name: {"bytes": path.stat().st_size, "sha256": sha(path.read_bytes())} for path in tool_paths}
    require(tools["vlib.exe"]["sha256"] == "12fa9f43fac4af70f9694e6055f376dcc419c39518a0e30d7aa047c37aaca576", "vlib hash")
    require(tools["vlog.exe"]["sha256"] == "39e7f5cbae66a5aa65a179f5ab8faee01a0c53dc838e5e2b76510ac6c77e80a6", "vlog hash")
    require(tools["vsim.exe"]["sha256"] == "011f110291dc69707d7118e8f8d712b91438e0c837f9bc10ce6bf53c1d048cfd", "vsim hash")

    output = {
        "schema": 1,
        "status": "passed",
        "scope": "installed-ModelSim digital public-port simulation only",
        "source_snapshot_unchanged": True,
        "source_aggregate_sha256": before["snapshot_aggregate_sha256"],
        "main_result": {
            "bytes": len(result_bytes), "sha256": sha(result_bytes), "status": result["status"],
            "runner_sha256": result["runner_sha256"], "rtl_sha256": result["rtl_sha256"],
            "tb_sha256": result["tb_sha256"], "commands": len(result["commands"]),
        },
        "positive_cases": cases,
        "public_port_edge_rows": total_rows,
        "long_case": long_result,
        "invalid_parameters": invalid,
        "mutations": mutations,
        "author_evidence": {
            "manifest_bytes": len(manifest_bytes), "manifest_sha256": sha(manifest_bytes),
            "files_verified": len(manifest["files"]), "cases": 9, "pass": 9, "fail": 0,
            "checks": 90644277, "replay_bytes": len(replay_bytes), "replay_sha256": sha(replay_bytes),
            "manifest_path_aliases": manifest_path_aliases,
            "committed_manifest_entries_verified": committed_manifest_entries,
            "uncommitted_work_entries": len(uncommitted_work_entries),
            "committed_files_on_disk": len(actual_author_files),
            "rerun_by_reviewer": False, "reason_not_rerun": "No distinct unresolved issue; author suite is not independent evidence.",
        },
        "tool_binaries": tools,
        "not_run": {
            "synthesis_implementation_timing": True,
            "cdc_rdc": True,
            "board_or_physical": True,
            "formal_29_cards": True,
            "g05_b06_r03_system": True,
        },
    }
    require(not args.output.exists(), "refusing to overwrite result audit")
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

"""Execute reviewed portable checks on new copies; preserve the Git export."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = HERE / "candidate"
EXEC = HERE / "execution"
PYTHON = ROOT / ".local/venv/Scripts/python.exe"


def load(p):
    return json.loads(p.read_bytes())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, obj):
    with p.open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def copy_exact(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("xb") as f:
        f.write(source.read_bytes())
    assert sha(source) == sha(dest)


export = load(HERE / "exported-inputs.json")
for row in export["files"]:
    assert sha(HERE / row["export"]) == row["sha256"], row["export"]
checks = []
for base, manifest in ((SRC, "artifact_manifest.json"),
                       (SRC / "independent_review", "manifest.json")):
    doc = load(base / manifest)
    for row in doc["files"]:
        path = (base / row["path"]).resolve()
        assert path.is_relative_to(base.resolve())
        assert sha(path) == row["sha256"], str(path)
        assert path.stat().st_size == row["bytes"]
    checks.append(dict(manifest=str((base / manifest).relative_to(HERE)),
                       files=len(doc["files"]), exact=True))
EXEC.mkdir(exist_ok=False)
for name in ("candidate_decode.py", "replay.py", "provenance.py"):
    copy_exact(SRC / name, EXEC / name)
for p in sorted((SRC / "inputs").iterdir()):
    assert p.is_file()
    copy_exact(p, EXEC / "inputs" / p.name)
for name in ("probe.py", "candidate_snapshot.py"):
    copy_exact(SRC / "independent_review" / name, EXEC / "independent_review" / name)
assert sha(EXEC / "independent_review/candidate_snapshot.py") == sha(EXEC / "candidate_decode.py")
copy_exact(SRC / "main_review/main_probe.py", EXEC / "main_review/main_probe.py")
env = {k: v for k, v in os.environ.items() if k.upper() in
       ("SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "TEMP", "TMP")}
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
commands = [
    ("provenance", [str(EXEC / "provenance.py"), "--check-only"]),
    ("replay", [str(EXEC / "replay.py")]),
    ("independent-qa", [str(EXEC / "independent_review/probe.py")]),
    ("c-main-controls", [str(EXEC / "main_review/main_probe.py"),
                         "--candidate", str(EXEC / "candidate_decode.py")]),
]
runs = []
for name, args in commands:
    cmd = [str(PYTHON), "-B", "-X", "utf8", *args]
    start = time.monotonic()
    record = dict(command=cmd, cwd=str(HERE), environment=env,
                  script_sha256=sha(Path(args[0])), start_utc=datetime.now(timezone.utc).isoformat(),
                  hidden=True, below_normal=True, timeout_seconds=45)
    save(HERE / (name + "-command.json"), record)
    with (HERE / (name + "-stdout.txt")).open("xb") as out, \
         (HERE / (name + "-stderr.txt")).open("xb") as err:
        completed = subprocess.run(cmd, cwd=HERE, env=env, stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=err, timeout=45,
                                   creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    record.update(exit_code=completed.returncode, elapsed_seconds=time.monotonic() - start,
                  stdout_sha256=sha(HERE / (name + "-stdout.txt")),
                  stderr_sha256=sha(HERE / (name + "-stderr.txt")))
    save(HERE / (name + "-result.json"), record)
    runs.append({k: record[k] for k in ("command", "exit_code", "elapsed_seconds")})
    assert completed.returncode == 0, name

# Independent A boundary check: valid offline bytes must remain inadmissible to
# the existing production ABI whitelist. This loads only its pure framing code.
production = ROOT / ".local/deepeye-implementation-a/competition/deepeye/integration/wire.py"
prod_sha = sha(production)
spec = importlib.util.spec_from_file_location("a_current_trace_boundary", production)
wire = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wire
spec.loader.exec_module(wire)
vectors = load(SRC / "inputs/trace_candidate_vectors.json")
packets = [bytes.fromhex(r["frame_hex"]) for r in vectors["manual_vectors"]["vectors"]]
packets += [bytes.fromhex(f) for row in vectors["synthetic_vectors"] for f in row["frames_hex"]]
for packet in packets:
    try:
        wire.decode(packet)
    except ValueError as exc:
        assert "unfrozen frame type" in str(exc)
    else:
        raise AssertionError("production TRACE admission unexpectedly open")
assert sha(production) == prod_sha
for row in export["files"]:
    assert sha(HERE / row["export"]) == row["sha256"], row["export"]
replay = load(EXEC / "replay_results.json")
assert replay["status"] == "passed" and replay["total_checks"] == 81
cost = {k: sum(r.get("ledger", {}).get(k, 0) for r in replay["results"])
        for k in ("selected_raw_bytes_total", "frame_bytes_total", "line_bits_8n1_total")}
result = dict(work_id="A-C-TRACE-EXACT-CANDIDATE-REVIEW-20261020-v1",
              utc=datetime.now(timezone.utc).isoformat(), manifests=checks, executions=runs,
              replay_groups=replay["total_checks"], costs=cost,
              qa_metrics=load(EXEC / "independent_review/metrics.json"),
              production_rejected_offline_packets=len(packets), production_wire_sha256=prod_sha,
              all70_exported_bytes_unchanged=True, all29="not_run", R03="not_run",
              runtime_or_hardware_adoption=False)
save(HERE / "check-results.json", result)
print(json.dumps(result, ensure_ascii=False))

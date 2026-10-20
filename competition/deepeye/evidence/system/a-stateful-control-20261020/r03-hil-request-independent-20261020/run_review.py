"""Hidden private-job envelope for the independent synthetic HIL controls."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRIOR = D.parent / "r02-install-recipe-fix-20261020"
PINS = {
    "win_job.py": "127daf70b2aa6cf3e7a299978596766fc310d191d13f6a2165626f719889052d",
    "boundary.py": "dc27aea6104424fbb2ee9109bb5e2adaf90684161e9d43bd2636b5ea4d6f2908",
}
for name, sha in PINS.items():
    assert hashlib.sha256((PRIOR / name).read_bytes()).hexdigest() == sha
sys.path.insert(0, str(PRIOR))
from win_job import run_bounded
from boundary import save_new

previous = json.loads((D / "execution/terminal.json").read_bytes())
assert previous["all_processes_terminated"] is True
assert previous["active_processes_final"] == 0
assert all(row["signaled"] and row["wait_result"] == 0 for row in previous["held_members"])
execution = D / "execution-controls"
execution.mkdir()
argv = [str(ROOT / ".local/venv/Scripts/python.exe"),
    "-I", "-S", "-B", "-X", "utf8", str(D / "review_controls.py")]
env = {k: v for k, v in os.environ.items() if k.upper() in ("SYSTEMROOT", "WINDIR")}
env.update(PATH="", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
    TEMP=str(execution), TMP=str(execution))
budget = {"seconds": 40, "job_memory_bytes": 512 * 1024**2,
    "process_memory_bytes": 256 * 1024**2, "active_processes": 4,
    "stdout_bytes": 2 * 1024**2, "stderr_bytes": 2 * 1024**2,
    "tree_bytes": 16 * 1024**2, "tree_entries": 500,
    "free_reserve_bytes": 10 * 1024**3}
save_new(execution / "started.json", {"argv": argv, "cwd": str(D),
    "environment": env, "budget": budget, "runner_pins": PINS,
    "source_pins": {name: hashlib.sha256((D / name).read_bytes()).hexdigest()
        for name in ("run_review.py", "review_controls.py", "verify_inputs.py")},
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "independent synthetic HIL association controls; no authority/capture authentication"})
result = run_bounded(argv, env, D, execution / "process", budget, [D])
save_new(execution / "terminal.json", result)
print(json.dumps({"exit_code": result["exit_code"], "termination": result.get("termination"),
    "receipt": str(execution / "terminal.json")}, ensure_ascii=False))
raise SystemExit(0 if result["exit_code"] == 0 else 1)

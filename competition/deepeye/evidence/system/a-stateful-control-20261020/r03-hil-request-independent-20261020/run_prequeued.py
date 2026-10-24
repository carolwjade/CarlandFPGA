"""Bounded hidden run of only the newly requested pre-entry control."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
OLD = D.parent / "r02-install-recipe-fix-20261020"
for label in ("execution", "execution-controls"):
    receipt = json.loads((D / label / "terminal.json").read_bytes())
    assert receipt["all_processes_terminated"] is True and receipt["active_processes_final"] == 0
    assert all(row["signaled"] and row["wait_result"] == 0 for row in receipt["held_members"])
pins = {"win_job.py":"127daf70b2aa6cf3e7a299978596766fc310d191d13f6a2165626f719889052d",
    "boundary.py":"dc27aea6104424fbb2ee9109bb5e2adaf90684161e9d43bd2636b5ea4d6f2908"}
for name, sha in pins.items():
    assert hashlib.sha256((OLD / name).read_bytes()).hexdigest() == sha
sys.path.insert(0, str(OLD))
from win_job import run_bounded
from boundary import save_new
execution = D / "execution-prequeued"
execution.mkdir()
argv = [str(ROOT / ".local/venv/Scripts/python.exe"), "-I", "-S", "-B", "-X", "utf8",
    str(D / "pending_before_entry.py")]
env = {k:v for k,v in os.environ.items() if k.upper() in ("SYSTEMROOT","WINDIR")}
env.update(PATH="", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", TEMP=str(execution), TMP=str(execution))
budget = {"seconds":20, "job_memory_bytes":512*1024**2, "process_memory_bytes":256*1024**2,
    "active_processes":4, "stdout_bytes":1024**2, "stderr_bytes":1024**2,
    "tree_bytes":16*1024**2, "tree_entries":500, "free_reserve_bytes":10*1024**3}
save_new(execution / "started.json", {"argv":argv, "cwd":str(D), "environment":env,
    "budget":budget, "runner_pins":pins, "started_utc":datetime.now(timezone.utc).isoformat(),
    "source_pins":{name:hashlib.sha256((D / name).read_bytes()).hexdigest()
        for name in ("pending_before_entry.py","run_prequeued.py","verify_inputs.py")},
    "scope":"one main-requested prequeued foreign STOP ordering control; no prior suite replay"})
result = run_bounded(argv, env, D, execution / "process", budget, [D])
save_new(execution / "terminal.json", result)
print(json.dumps({"exit_code":result["exit_code"], "seconds":result["seconds"],
    "all_processes_terminated":result["all_processes_terminated"]}))
raise SystemExit(0 if result["exit_code"] == 0 else 1)

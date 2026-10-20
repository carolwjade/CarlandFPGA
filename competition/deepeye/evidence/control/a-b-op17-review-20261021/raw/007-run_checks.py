import hashlib
import json
import os
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
LIB = D.parent / "r02-local-hostname-independent-20261020"
assert hashlib.sha256((LIB / "win_job.py").read_bytes()).hexdigest() == "127daf70b2aa6cf3e7a299978596766fc310d191d13f6a2165626f719889052d"
assert hashlib.sha256((LIB / "boundary.py").read_bytes()).hexdigest() == "dc27aea6104424fbb2ee9109bb5e2adaf90684161e9d43bd2636b5ea4d6f2908"
sys.path.insert(0, str(LIB))
from win_job import run_bounded

temp = D / "tmp"
temp.mkdir()
env = {"SYSTEMROOT": os.environ["SYSTEMROOT"], "WINDIR": os.environ["SYSTEMROOT"],
       "PATH": "", "TEMP": str(temp), "TMP": str(temp),
       "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
budget = {"seconds": 30, "active_processes": 4, "process_memory_bytes": 384 * 1024**2,
          "job_memory_bytes": 512 * 1024**2, "stdout_bytes": 128 * 1024,
          "stderr_bytes": 256 * 1024, "tree_bytes": 128 * 1024**2,
          "tree_entries": 2000, "free_reserve_bytes": 512 * 1024**2}
sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
           for p in [D / "independent_checks.py", D / "run_checks.py", LIB / "win_job.py", LIB / "boundary.py"]}
with (D / "worker-input-pins.json").open("x", encoding="utf-8") as f:
    json.dump(sources, f, indent=2)
argv = [str(ROOT / ".local/venv/Scripts/python.exe"), "-I", "-S", "-B", "-X",
        "utf8", str(D / "independent_checks.py")]
result = run_bounded(argv, env, D, D / "run-01", budget, [D])
assert result["all_processes_terminated"], "Unresolved owned tree; no replay"
print(json.dumps({k: result[k] for k in ("status", "exit_code", "all_processes_terminated",
                                        "held_members", "seconds", "stop_reason")}))
raise SystemExit(result["exit_code"] if result["exit_code"] is not None else 125)

"""One hidden, quota-bounded review worker. No unknown tree is replayed."""
import hashlib
import json
import os
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
SOURCE = D.parent / "r02-install-recipe-fix-20261020"
COPIES = {
    "win_job.py": "127daf70b2aa6cf3e7a299978596766fc310d191d13f6a2165626f719889052d",
    "boundary.py": "dc27aea6104424fbb2ee9109bb5e2adaf90684161e9d43bd2636b5ea4d6f2908",
}
for name, expected in COPIES.items():
    content = (SOURCE / name).read_bytes()
    assert hashlib.sha256(content).hexdigest() == expected
    target = D / name
    if target.exists():
        assert target.read_bytes() == content
    else:
        with target.open("xb") as stream:
            stream.write(content)

sys.path.insert(0, str(D))
from win_job import run_bounded

label, case = sys.argv[1:]
assert (label, case) in {("suite-01", "all"), ("stop-callshape-01", "stop")}
assert (D / "initial-audit.json").is_file()
env = {
    "SYSTEMROOT": os.environ["SYSTEMROOT"],
    "WINDIR": os.environ.get("WINDIR", os.environ["SYSTEMROOT"]),
    "PATH": "",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONIOENCODING": "utf-8",
    "TEMP": str(D),
    "TMP": str(D),
}
budget = {
    "seconds": 30, "active_processes": 4,
    "process_memory_bytes": 384 * 1024**2, "job_memory_bytes": 512 * 1024**2,
    "stdout_bytes": 128 * 1024, "stderr_bytes": 256 * 1024,
    "tree_bytes": 32 * 1024**2, "tree_entries": 512,
    "free_reserve_bytes": 512 * 1024**2,
}
argv = [str(ROOT / ".local/venv/Scripts/python.exe"), "-I", "-S", "-B", "-X", "utf8",
        str(D / "independent_controls.py"), case, label]
result = run_bounded(argv, env, D, D / label, budget, [D])
print(json.dumps({
    "label": label, "status": result["status"], "exit_code": result["exit_code"],
    "stop_reason": result["stop_reason"], "all_processes_terminated": result["all_processes_terminated"],
    "held_members": result.get("held_members"), "seconds": result["seconds"],
}, ensure_ascii=False))
assert result["all_processes_terminated"], "Never retry an unresolved process tree"
raise SystemExit(result["exit_code"] if result["exit_code"] is not None else 125)

"""Fix1-only hidden/bounded receipts; never imports target packages."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / ".local/deepeye-implementation-a"
PYTHON = ROOT / ".local/venv/Scripts/python.exe"
ORIGINAL = HERE.parent / "r02-preflight-implementation-20261020"
OWNERSHIP = json.loads((ORIGINAL / "ownership.json").read_text(encoding="utf-8"))

def hashes():
    paths = OWNERSHIP["product_files"] + list(OWNERSHIP["preserved_dirty_sha256"])
    paths += ["docs/competition/deepeye-2026/immutable_scope.json"]
    return {p: hashlib.sha256((PRODUCT / p).read_bytes()).hexdigest() for p in paths}

def frozen_hashes():
    files = sorted(p for p in ORIGINAL.rglob("*") if p.is_file())
    files += [PRODUCT / ".superpowers/sdd/2026-10-20-r02-readonly-preflight/task-1-brief.md",
              PRODUCT / ".superpowers/sdd/2026-10-20-r02-readonly-preflight/task-1-report.md",
              PRODUCT / "competition/deepeye/hardware/environment.json"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def main():
    name = sys.argv[1]
    if name in ("red", "green"):
        args = [str(PYTHON), "-B", "-X", "utf8", "-m", "unittest", "discover",
                "-s", "competition/deepeye/tests", "-p", "test_preflight.py", "-v"]
    elif name == "live":
        args = [str(PYTHON), "-B", "-X", "utf8", "competition/deepeye/tools/preflight.py",
                "--inventory-only", "--output", str(HERE / "host-inventory.json")]
    else:
        raise ValueError(name)
    receipt = {"command": args, "cwd": str(PRODUCT), "source_hashes_before": hashes(),
               "frozen_hashes_before": frozen_hashes(),
               "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "creationflags": 0x08004000, "timeout_seconds": 55}
    proc = subprocess.Popen(args, cwd=PRODUCT, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=0x08004000)
    try:
        stdout, stderr = proc.communicate(timeout=55)
        receipt["timed_out"] = False
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)
        receipt["timed_out"] = True
    receipt.update(exit_code=proc.returncode, ended_at_utc=datetime.now(timezone.utc).isoformat(),
                   source_hashes_after=hashes(), frozen_hashes_after=frozen_hashes())
    for suffix, content in [("stdout.txt", stdout), ("stderr.txt", stderr)]:
        with (HERE / f"{name}.{suffix}").open("xb") as stream:
            stream.write(content)
        receipt[suffix + "_sha256"] = hashlib.sha256(content).hexdigest()
    with (HERE / f"{name}.receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False)
    print(json.dumps({"run": name, "exit_code": proc.returncode,
                      "timed_out": receipt["timed_out"], "receipt": str(HERE / f"{name}.receipt.json")}))

if __name__ == "__main__":
    main()

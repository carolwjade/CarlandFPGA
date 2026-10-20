"""Task-scoped hidden, bounded command receipt writer (no target imports)."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / ".local/deepeye-implementation-a"
PYTHON = ROOT / ".local/venv/Scripts/python.exe"

def hashes():
    ownership = json.loads((HERE / "ownership.json").read_text(encoding="utf-8"))
    paths = ownership["product_files"] + list(ownership["preserved_dirty_sha256"])
    paths += ["docs/competition/deepeye-2026/immutable_scope.json"]
    return {p: hashlib.sha256((PRODUCT / p).read_bytes()).hexdigest()
            if (PRODUCT / p).is_file() else None for p in paths}

def main():
    name = sys.argv[1]
    if name == "red" or name.startswith("green"):
        args = [str(PYTHON), "-B", "-X", "utf8", "-m", "unittest", "discover",
                "-s", "competition/deepeye/tests", "-p", "test_preflight.py", "-v"]
        timeout = 40
    elif name == "live":
        args = [str(PYTHON), "-B", "-X", "utf8", "competition/deepeye/tools/preflight.py",
                "--inventory-only", "--output", str(HERE / "host-inventory.json")]
        timeout = 35
    else:
        raise ValueError(name)
    receipt = {"command": args, "cwd": str(PRODUCT), "source_hashes_before": hashes(),
               "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "creationflags": 0x08004000, "timeout_seconds": timeout}
    proc = subprocess.Popen(args, cwd=PRODUCT, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=0x08004000)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        receipt["timed_out"] = False
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)
        receipt["timed_out"] = True
    receipt.update(exit_code=proc.returncode, ended_at_utc=datetime.now(timezone.utc).isoformat(),
                   source_hashes_after=hashes())
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

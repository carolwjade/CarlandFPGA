from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from run_evidence import HERE, ROOT, PRODUCT, hashes

ownership = json.loads((HERE / "ownership.json").read_text(encoding="utf-8"))
current = hashes()
assert all(current[p] == digest for p, digest in ownership["preserved_dirty_sha256"].items())
final_tests = json.loads((HERE / "green-final.receipt.json").read_text(encoding="utf-8"))
live_receipt = json.loads((HERE / "live.receipt.json").read_text(encoding="utf-8"))
assert current == final_tests["source_hashes_after"] == live_receipt["source_hashes_after"]
live = json.loads((HERE / "host-inventory.json").read_text(encoding="utf-8"))
raw_equal = (HERE / "host-inventory.json").read_bytes() == (HERE / "live.stdout.txt").read_bytes()
assert live == json.loads((HERE / "live.stdout.txt").read_text(encoding="utf-8"))
git = r"C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
git_results = {}
for name, args in [("head", ["rev-parse", "HEAD"]), ("status", ["status", "--porcelain=v1", "--untracked-files=all"])]:
    command = [git, "-C", str(PRODUCT), *args]
    done = subprocess.run(command, capture_output=True, timeout=15, stdin=subprocess.DEVNULL,
                          creationflags=0x08004000, env={**__import__('os').environ, "GIT_OPTIONAL_LOCKS": "0"})
    assert done.returncode == 0
    git_results[name] = {"command": command, "exit_code": done.returncode,
                         "stdout": done.stdout.decode("utf-8"), "stderr": done.stderr.decode("utf-8")}
assert git_results["head"]["stdout"].strip() == ownership["base"]
for line in git_results["status"]["stdout"].splitlines():
    if line[3:] in ownership["preserved_dirty_sha256"]:
        assert line[:2] in (" M", "??"), line
audit = {"at_utc": datetime.now(timezone.utc).isoformat(), "source_hashes": current,
         "protected_dirty_bytes_preserved": True, "protected_files_unstaged": True,
         "test_and_live_sources_identical": True, "stdout_output_bytes_identical": raw_equal,
         "stdout_output_json_identical": True,
         "git": git_results, "live_exit_code": live_receipt["exit_code"],
         "live_inventory_complete": live["inventory_complete"],
         "live_error": live["errors"][0]["code"]}
with (HERE / "final-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in audit.items() if k not in ("git", "source_hashes")}))

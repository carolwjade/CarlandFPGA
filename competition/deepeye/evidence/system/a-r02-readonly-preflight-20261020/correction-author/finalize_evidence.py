from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
from run_evidence import HERE, ROOT, PRODUCT, OWNERSHIP, hashes, frozen_hashes

def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))

current = hashes()
red, green, live = [read(name + ".receipt.json") for name in ("red", "green", "live")]
assert green["exit_code"] == live["exit_code"] == 0
assert not green["timed_out"] and not live["timed_out"]
assert current == green["source_hashes_before"] == green["source_hashes_after"]
assert current == live["source_hashes_before"] == live["source_hashes_after"]
assert all(current[p] == expected for p, expected in OWNERSHIP["preserved_dirty_sha256"].items())
frozen = frozen_hashes()
assert all(receipt["frozen_hashes_before"] == receipt["frozen_hashes_after"] == frozen
           for receipt in (red, green, live))
host = read("host-inventory.json")
stdout = read("live.stdout.txt")
assert host == stdout and host["inventory_complete"] and not host["errors"]
assert host["R02"] == "not_run" and host["formal_acceptance"] is False
assert all(group["status"] == "ok" for group in host["observations"]["groups"].values())
assert host["collector_source_sha256"] == current["competition/deepeye/tools/preflight_windows.ps1"]
assert host["contract"]["actual_requirements_sha256"] == OWNERSHIP["requirements_sha256"]
contracts = {}
for label, folder in (("root", ROOT), ("product", PRODUCT)):
    scope = json.loads((folder / "docs/competition/deepeye-2026/immutable_scope.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(scope["requirements"], ensure_ascii=False, sort_keys=True,
                                      separators=(",", ":")).encode("utf-8")).hexdigest()
    assert digest == OWNERSHIP["requirements_sha256"]
    assert scope["contract_id"] == "DEEPEYE-HUMAN-LOCK-20261014" and scope["revision"] == 1
    assert {entry["id"] for entry in scope["requirements"]} == {f"H{i:02}" for i in range(1, 16)}
    contracts[label] = digest
git = r"C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
git_results = {}
for name, args in [("head", ["rev-parse", "HEAD"]), ("status", ["status", "--porcelain=v1", "--untracked-files=all"])]:
    command = [git, "-C", str(PRODUCT), *args]
    completed = subprocess.run(command, capture_output=True, timeout=15, stdin=subprocess.DEVNULL,
                               creationflags=0x08004000, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    assert completed.returncode == 0
    git_results[name] = {"command": command, "exit_code": completed.returncode,
                         "stdout": completed.stdout.decode("utf-8"), "stderr": completed.stderr.decode("utf-8")}
assert git_results["head"]["stdout"].strip() == OWNERSHIP["base"]
for line in git_results["status"]["stdout"].splitlines():
    if line[3:] in OWNERSHIP["preserved_dirty_sha256"]:
        assert line[:2] in (" M", "??"), line
raw_hashes = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
              for name in ("live.stdout.txt", "live.stderr.txt", "host-inventory.json")}
audit = {"at_utc": datetime.now(timezone.utc).isoformat(), "source_hashes": current,
         "protected_dirty_bytes_preserved": True, "protected_files_unstaged": True,
         "historical_evidence_brief_report_environment_preserved": True,
         "test_and_live_sources_identical": True, "stdout_output_json_identical": True,
         "stdout_output_bytes_identical": (HERE / "host-inventory.json").read_bytes() == (HERE / "live.stdout.txt").read_bytes(),
         "raw_file_hashes": raw_hashes, "contracts": contracts, "git": git_results,
         "live_exit_code": live["exit_code"], "inventory_complete": host["inventory_complete"],
         "group_counts": {key: len(group["rows"]) for key, group in host["observations"]["groups"].items()}}
with (HERE / "final-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
print(json.dumps({key: value for key, value in audit.items() if key != "git"}))

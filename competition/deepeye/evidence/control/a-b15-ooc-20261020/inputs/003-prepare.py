"""Freeze the selected B blobs and one background-only synthesis invocation."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMIT = "df82af1bc91d01aeb9adee19f48c0890dfc1ac5b"
CONTRACT = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
NAMES = (
    "deepeye_atomic_pwm.sv",
    "deepeye_pwm_coherent_capture.sv",
    "deepeye_pwm_applied_capture.sv",
)


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def git(*args):
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def sha(data):
    return hashlib.sha256(data).hexdigest()


scope = json.loads((ROOT / "docs/competition/deepeye-2026/immutable_scope.json").read_bytes())
assert sha(json.dumps(scope["requirements"], ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")) == CONTRACT
transfer = json.loads((ROOT / ".planning/deepeye-desktop-handoff-20261015/transfer.json").read_bytes())
assert transfer["status"] == "active" and transfer["director_generation"] == 2
assert transfer["new_director_thread_id"] == "01a13d7e-dcf1-7272-a738-a637dd62ff9d"
b_scope = json.loads(git("show", COMMIT + ":docs/competition/deepeye-2026/immutable_scope.json"))
assert sha(json.dumps(b_scope["requirements"], ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")) == CONTRACT
assert git("rev-parse", COMMIT).decode().strip() == COMMIT
sources = HERE / "sources"
sources.mkdir()
rows = []
for name in NAMES:
    relative = "competition/deepeye/fpga/control3d/" + name
    blob = git("rev-parse", COMMIT + ":" + relative).decode().strip()
    raw = git("cat-file", "blob", blob)
    with (sources / name).open("xb") as stream:
        stream.write(raw)
    rows.append({"path": relative, "snapshot": "sources/" + name,
                 "blob": blob, "size": len(raw), "sha256": sha(raw)})
assert rows[0]["sha256"] == "9dc8ecf96e59a2ae8467bda64572f62eb602d52db535733f236f64ff97c43428"
assert rows[1]["sha256"] == "4baddfc31248c49000c00ac74bc2319cef6c9016c7df3f1822030c69cd82f456"
launcher = (ROOT / ".local/toolchain/LaunchVivadoLicensed.vbs").read_text(encoding="utf-8-sig")
batch = Path(re.search(r'^vivadoBatch = "([^"]+)"', launcher, re.M)[1])
fallback_license = Path(re.search(r'^\s*licenseFile = "([^"]+)"', launcher, re.M)[1])
assert batch == Path("D:/AMDFPGA/2026.1/Vivado/bin/vivado.bat") and batch.is_file()
assert fallback_license.is_file()
alias = Path(os.environ["LOCALAPPDATA"]) / "Temp/deepeye-a-b15-ooc-20261020-v1"
assert str(alias).isascii() and not os.path.lexists(alias)
save(HERE / "inputs.json", {
    "utc": datetime.now(timezone.utc).isoformat(), "source_commit": COMMIT,
    "requirements_sha256": CONTRACT, "sources": rows, "batch": str(batch),
    "launcher_sha256": sha(launcher.encode("utf-8")), "license_file_exists": True,
    "alias": str(alias), "alias_target": str(HERE),
    "top": "deepeye_pwm_applied_capture", "part": "xc7z020clg400-1",
    "parameters": {"COUNT_W": 32, "WITNESS_W": 64, "TAG_W": 32},
    "clock_constraint": None, "implementation": "not_run", "board": "not_run",
    "formal_cards": "all29 not_run"})
print(json.dumps({"source_files": len(rows), "source_commit": COMMIT,
                  "alias": str(alias), "outputs": str(HERE), "prepared": True}))

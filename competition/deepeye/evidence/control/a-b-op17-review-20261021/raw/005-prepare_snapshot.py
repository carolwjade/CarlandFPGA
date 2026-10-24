import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
HEAD = "ccf3698cce065e20dbfa24bb6d07a97be7e38de6"
SOURCE = "32b64d907375d3fff42db457de29d3f820450e8d"
BASE = "f7736ac737d1c7b256974beb1574b94096819270"
PREFIX = "competition/deepeye/"
RUNNER = PREFIX + "tools/control3d/run_pwm_applied_capture.py"
TEST = PREFIX + "tests/control/test_pwm_applied_capture_runner.py"
commands = []


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*args, data=None):
    argv = ["git", "-c", "core.longpaths=true", "-C", str(ROOT), *args]
    p = subprocess.run(argv, input=data, capture_output=True, timeout=20,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    commands.append({"argv": argv, "exit": p.returncode,
                     "stdout_bytes": len(p.stdout), "stdout_sha256": sha(p.stdout)})
    assert p.returncode == 0
    return p.stdout


def tree(ref):
    rows = {}
    for line in git("ls-tree", "-r", "-z", "--full-tree", ref).split(b"\0"):
        if not line:
            continue
        meta, name = line.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split()
        rows[name.decode("utf-8")] = {"mode": mode, "kind": kind, "oid": oid}
    return rows


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(raw)


old, new = tree(BASE), tree(HEAD)
assert ("parent " + SOURCE + "\n") in git("cat-file", "-p", HEAD).decode()
assert git("merge-base", BASE, HEAD).decode().strip() == BASE
changed = [p for p in old if p in new and old[p] != new[p]]
removed = [p for p in old if p not in new]
added = [p for p in new if p not in old]
assert set(changed) == {RUNNER, TEST} and not removed
assert all(p.startswith(PREFIX + "evidence/control3d/pwm-runner-qualification-20261020-17/")
           or p.startswith("handoffs/b/B-DEEPEYE-PWM-RUNNER-QUALIFICATION-20261020-17/")
           for p in added)
m = json.loads((D / "original-manifest.json").read_bytes())
request_raw = json.dumps(m["request"], ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
assert sha(request_raw) == m["request_hash"] == "cd8362506041657d4295bc4a47511d87e0ed561f87907e8bec1ee579b36e9ddd"
assert m["request"]["code_commit"] == SOURCE and set(m["artifacts"]) == set(m["files"])
requests = list(m["files"])
for path in requests:
    pp = PurePosixPath(path)
    assert not pp.is_absolute() and ".." not in pp.parts and "\\" not in path
    assert new[path]["kind"] == "blob" and new[path]["mode"] == "100644"
raw = git("cat-file", "--batch", data=("\n".join(new[p]["oid"] for p in requests) + "\n").encode())
offset = 0
for path in requests:
    end = raw.index(b"\n", offset)
    oid, kind, size = raw[offset:end].split()
    assert oid.decode() == new[path]["oid"] and kind == b"blob"
    start = end + 1
    blob = raw[start:start + int(size)]
    offset = start + int(size) + 1
    assert raw[offset - 1:offset] == b"\n"
    row = m["files"][path]
    assert len(blob) == row["size"] and sha(blob) == row["sha256"], path
    write(D / "snapshot" / path, blob)
assert offset == len(raw)
assert sha((D / "snapshot" / RUNNER).read_bytes()) == "b6735257dbfc107a14791ec69cb7386f306d0408173acf9466a0f69c93c30b94"
assert sha((D / "snapshot" / TEST).read_bytes()) == "f8d4d5633949f8583e2d25b2622b3a67b30a05880bd84c2788e327c440516a34"
for name in (RUNNER, TEST):
    baseline = git("cat-file", "blob", old[name]["oid"])
    write(D / "baseline" / name, baseline)
    current = (D / "snapshot" / name).read_bytes()
    diff = "".join(difflib.unified_diff(baseline.decode().splitlines(True),
                   current.decode().splitlines(True), fromfile=BASE + "/" + name,
                   tofile=HEAD + "/" + name))
    write(D / (Path(name).name + ".diff.txt"), diff.encode())
for path in added:
    if path in m["files"]:
        continue
    write(D / "snapshot" / path, git("cat-file", "blob", new[path]["oid"]))
result = {
    "head": HEAD, "source": SOURCE, "base": BASE,
    "manifest_files_verified": len(requests), "request_hash": m["request_hash"],
    "changed_existing": changed, "added_files": len(added), "removed_files": removed,
    "old_tree_count": len(old), "unchanged_old_files": len(old) - len(changed),
    "snapshot": str(D / "snapshot"), "commands": commands,
}
write(D / "source-verification.json", json.dumps(result, indent=2).encode())
print(json.dumps({k: v for k, v in result.items() if k != "commands"}))

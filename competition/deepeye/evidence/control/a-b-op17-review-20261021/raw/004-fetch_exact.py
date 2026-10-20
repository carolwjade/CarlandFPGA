"""Read an exact peer handoff without checking it out over an active writer."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
HEAD = "ccf3698cce065e20dbfa24bb6d07a97be7e38de6"
REL = "handoffs/b/B-DEEPEYE-PWM-RUNNER-QUALIFICATION-20261020-17/manifest.json"
SHA = "8f0dd8188e640f3abbbc118cbf40bf6f559a8a2f06d950560924dec49b151a8d"


def save(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def call(label, argv, timeout=50):
    save(D / (label + ".started.json"), {
        "argv": argv, "started_utc": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": timeout, "hidden": True,
    })
    with (D / (label + ".stdout.bin")).open("xb") as out, \
            (D / (label + ".stderr.bin")).open("xb") as err:
        p = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err, timeout=timeout,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    save(D / (label + ".result.json"), {"exit_code": p.returncode})
    assert p.returncode == 0, (label, p.returncode)
    return (D / (label + ".stdout.bin")).read_bytes()


if sys.argv[1:] == ["api"]:
    pr = json.loads(call("pr-before", ["gh", "api",
        "repos/carolwjade/CarlandFPGA/pulls/30"]))
    save(D / "pr-summary.json", {k: pr[k] for k in ("number", "state", "html_url", "head", "base")})
    assert pr["head"]["sha"] == HEAD and pr["state"] == "open"
    obj = json.loads(call("manifest-api", ["gh", "api",
        "repos/carolwjade/CarlandFPGA/contents/" + REL + "?ref=" + HEAD]))
    assert obj["type"] == "file" and obj["path"] == REL and obj["encoding"] == "base64"
    raw = base64.b64decode(obj["content"], validate=False)
    assert len(raw) == obj["size"] and hashlib.sha256(raw).hexdigest() == SHA
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == obj["sha"]
    with (D / "original-manifest.json").open("xb") as f:
        f.write(raw)
    m = json.loads(raw)
    print(json.dumps({"head": HEAD, "manifest_sha256": SHA,
                      "metadata": {k: v for k, v in m.items() if k not in ("files", "artifacts")},
                      "files_count": len(m.get("files", {})), "artifacts_count": len(m.get("artifacts", []))}))
elif sys.argv[1:] == ["git"]:
    # Only fetch immutable objects: no checkout, branch/index or FETCH_HEAD change.
    call("git-fetch", ["git", "-c", "http.version=HTTP/1.1",
        "-c", "http.lowSpeedLimit=1024", "-c", "http.lowSpeedTime=30",
        "-C", str(ROOT), "fetch", "--no-tags", "--no-write-fetch-head",
        "--negotiation-tip=f7736ac737d1c7b256974beb1574b94096819270",
        "origin", HEAD], timeout=55)
    raw = call("git-manifest", ["git", "-c", "core.longpaths=true", "-C", str(ROOT),
        "cat-file", "blob", HEAD + ":" + REL], timeout=10)
    assert raw == (D / "original-manifest.json").read_bytes()
    print(json.dumps({"head": HEAD, "git_api_exact": True}))
else:
    raise SystemExit("select one fresh phase: api or git")

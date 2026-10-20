import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / ".local/deepeye-implementation-a"
C_HEAD = "942fa309ffc8f1d32c816cfa643b009b031d7d0a"
B_HEAD = "f7736ac737d1c7b256974beb1574b94096819270"
PREFIX = "competition/deepeye/evidence/ai/trace_candidate_decode/"


def git(*args):
    return subprocess.run(["git", "-C", str(PRODUCT), *args], check=True,
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=15,
                          creationflags=subprocess.CREATE_NO_WINDOW).stdout


def put(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        f.write(data)


records = []
tree = git("ls-tree", "-r", "-z", C_HEAD, "--", PREFIX)
for entry in tree.split(b"\0"):
    if not entry:
        continue
    meta, raw_path = entry.split(b"\t", 1)
    mode, kind, oid = meta.decode("ascii").split()
    path = raw_path.decode("utf-8")
    assert mode == "100644" and kind == "blob" and path.startswith(PREFIX)
    relative = path[len(PREFIX):]
    dest = HERE / "candidate" / relative
    assert dest.resolve().is_relative_to((HERE / "candidate").resolve())
    blob = git("cat-file", "blob", oid)
    assert hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest() == oid
    put(dest, blob)
    records.append(dict(path=path, export="candidate/" + relative, blob=oid,
                        bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest()))
source = HERE / "candidate/candidate_decode.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == \
    "b02010280b72d3a94842db627f733df9c1fa6ecfe54f572509d57869d2d3d72c"
normative = {}
for name in ("trace_candidate_layout.json", "trace_candidate_vectors.json"):
    path = "competition/deepeye/golden/codec/" + name
    blob = git("show", B_HEAD + ":" + path)
    put(HERE / "b-normative" / name, blob)
    candidate = (HERE / "candidate/inputs" / name).read_bytes()
    normative[name] = dict(b_commit=B_HEAD, b_sha256=hashlib.sha256(blob).hexdigest(),
                          c_input_sha256=hashlib.sha256(candidate).hexdigest(),
                          exact_bytes_equal=blob == candidate)
    assert blob == candidate, name
result = dict(utc=datetime.now(timezone.utc).isoformat(), c_exact_commit=C_HEAD,
              b_exact_commit=B_HEAD, files=records, normative=normative,
              current_remote_head_claim=False, product_writes=False)
put(HERE / "exported-inputs.json",
    (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"exported": len(records), "source_pin_verified": True,
                  "B_C_normative_byte_matches": len(normative)}))

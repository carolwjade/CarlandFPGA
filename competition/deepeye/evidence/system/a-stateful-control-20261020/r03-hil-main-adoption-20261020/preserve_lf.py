import ast
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
P = ROOT / ".local/deepeye-implementation-a/competition/deepeye/integration/hil_request_tracker.py"
raw = P.read_bytes()
assert hashlib.sha256(raw).hexdigest() == "6cc8264741e59657c744b21212795cbefb84d126b92911875876af3c4dd48d05"
assert raw.count(b"\r\n") == 3
original = (D / "before.py").read_bytes()
assert original.count(b"\r\n") == 0
final = raw.replace(b"\r\n", b"\n")
assert ast.dump(ast.parse(raw), include_attributes=False) == ast.dump(ast.parse(final), include_attributes=False)
with (D / "after-lf.py").open("xb") as f:
    f.write(final)
P.write_bytes(final)
assert P.read_bytes() == final
with (D / "line-ending-readback.json").open("x", encoding="utf-8") as f:
    json.dump({
        "reason": "Match original source LF; only the three inserted docstring line separators had CRLF.",
        "intermediate_sha256": hashlib.sha256(raw).hexdigest(),
        "final_sha256": hashlib.sha256(final).hexdigest(),
        "all_ast_including_docstring_values_equal": True,
        "original_before_and_intermediate_after_snapshots_preserved": True,
    }, f, indent=2)
print(json.dumps({"final_hil_source_sha256": hashlib.sha256(final).hexdigest(),
                  "original_line_ending_preserved": True}))

import ast
import asyncio
import hashlib
import json
from pathlib import Path
import stat
import sys

D = Path(__file__).resolve().parent
OUT = D.parent
ROOT = OUT.parents[1]
PRODUCT = ROOT / ".local/deepeye-implementation-a/competition/deepeye"
AUTHOR = OUT / "r03-mailbox-stop-fix-20261020"
REVIEW = OUT / "r03-mailbox-independent-20261020"
sys.path.insert(0, str(ROOT))
from fpga_mesh.child_control import LocalControlFileClient


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def copy(path, raw):
    with path.open("xb") as f:
        f.write(raw)


async def main():
    manifest = (AUTHOR / "artifact-manifest.json").read_bytes()
    assert sha(manifest) == "b8d3ed1a2903be504d83509bc9db5e99a705a4225287eed919f7079addc2de60"
    rows = json.loads(manifest)["files"]
    for rel, row in rows.items():
        path = AUTHOR / rel
        assert path.resolve().is_relative_to(AUTHOR.resolve())
        st = path.lstat()
        assert stat.S_ISREG(st.st_mode)
        assert not getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
        assert st.st_size == row["bytes"] and sha(path.read_bytes()) == row["sha256"]
    c = LocalControlFileClient(ROOT / ".local/deployment/node-a/.local/node-a/main-control.json")
    result = await c.call("job", {"job_id": "child-4126792ead044c7da100414b353266f8"})
    assert result["status"] == "completed" and result["terminal"]
    assert result["result"]["text"] == (AUTHOR / "final-result.txt").read_text(encoding="utf-8")
    pins = json.loads((AUTHOR / "input-pins.json").read_bytes())["files"]
    for path, row in pins.items():
        raw = Path(path).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    before = (PRODUCT / "integration/candidate_mailbox.py").read_bytes()
    after = (AUTHOR / "proposed/candidate_mailbox.py").read_bytes()
    token = b"    def stop(self, reason='stop'):"
    assert before.count(token) == 1
    assert after == before.replace(token, b"    @_entry\n" + token)
    assert sha(after) == "5ca4aafb97f88b3080cc918e38f6c27a462f4caa7af5fa436eeb663f91d3f1d5"
    old_test = ast.parse((PRODUCT / "integration/test_candidate_mailbox.py").read_bytes())
    new_test_raw = (AUTHOR / "proposed/test_candidate_mailbox.py").read_bytes()
    assert sha(new_test_raw) == "7ff79841abbd6aac12b017a486d296ce58335424471379cfb8af2b020aec9f82"
    new_test = ast.parse(new_test_raw)
    new_classes = {c.name: c for c in new_test.body if isinstance(c, ast.ClassDef)}
    original_methods = 0
    for cls in (c for c in old_test.body if isinstance(c, ast.ClassDef)):
        after_methods = {m.name: m for m in new_classes[cls.name].body if isinstance(m, ast.FunctionDef)}
        for method in (m for m in cls.body if isinstance(m, ast.FunctionDef)):
            assert ast.dump(method, include_attributes=False) == ast.dump(after_methods[method.name], include_attributes=False)
            original_methods += 1
    original_controls = (REVIEW / "independent_controls.py").read_bytes()
    old_path = b'sys.path[:0] = [str(PRODUCT / "integration"), str(ROOT / ".local/deepeye-host-deps")]'
    new_path = b'sys.path[:0] = [str(D), str(PRODUCT / "integration"), str(ROOT / ".local/deepeye-host-deps")]'
    assert original_controls.count(old_path) == 1
    controls = original_controls.replace(old_path, new_path)
    copy(D / "independent_controls.py", controls)
    copy(D / "original-independent-controls.py.reference", original_controls)
    copy(D / "candidate_mailbox.py", after)
    copy(D / "run_review.py", (REVIEW / "run_review.py").read_bytes())
    save(D / "initial-audit.json", {
        "author_manifest_sha256": sha(manifest), "author_files_verified": len(rows),
        "original_job": "child-4126792ead044c7da100414b353266f8",
        "completed": True, "terminal": True, "exact_result": True,
        "implementation_exact_single_decorator": True,
        "original_test_methods_ast_unchanged": original_methods,
        "original_inputs": pins, "proposed_module_sha256": sha(after),
        "proposed_test_sha256": sha(new_test_raw),
        "controls_old_sha256": sha(original_controls), "controls_new_sha256": sha(controls),
        "controls_delta": "Only prepend owned proposed module import path; existing independent STOP assertions unchanged.",
        "new_run": "stop-callshape-01 in this new directory only",
        "product_application": "pending independent focused result", "R03": "not_run",
    })
    print(json.dumps({"verified_author_files": len(rows), "exact_terminal": True,
                      "original_test_methods_unchanged": original_methods, "prepared": True}))


asyncio.run(main())

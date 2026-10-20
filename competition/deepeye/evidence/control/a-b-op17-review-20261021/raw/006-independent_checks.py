"""Pure Python qualification; no simulator entrypoint is executed."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

D = Path(__file__).resolve().parent
OUT = D.parent
P = "competition/deepeye/"
RP = P + "tools/control3d/run_pwm_applied_capture.py"
TP = P + "tests/control/test_pwm_applied_capture_runner.py"
events = []
checks = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(event, args):
    if event.startswith("socket.") or event in {
            "subprocess.Popen", "os.system", "os.startfile", "os.posix_spawn"}:
        events.append(event)
        raise AssertionError("External effect forbidden: " + event)


sys.addaudithook(audit)


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(sp)
    sys.modules[name] = mod
    sp.loader.exec_module(mod)
    return mod


def save(name, value):
    with (D / name).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


oldraw = (D / "baseline" / TP).read_bytes()
newraw = (D / "snapshot" / TP).read_bytes()


def methods(raw):
    tree = ast.parse(raw)
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}


old_methods, new_methods = methods(oldraw), methods(newraw)
assert len(old_methods) == 23 and len(new_methods) == 31
assert all(new_methods[k] == v for k, v in old_methods.items())
unit = load("b17_current_tests", D / "snapshot" / TP)
runner = unit.runner
suite = unittest.defaultTestLoader.loadTestsFromModule(unit)
current_result = unittest.TextTestRunner(verbosity=2).run(suite)
assert current_result.wasSuccessful() and current_result.testsRun == 31

# Preserve the original 23 method bodies and exact old module bytes. Its
# imported runner is replaced only with the exact final module under review.
previous_tests = load("b16_original_tests", D / "baseline" / TP)
previous_tests.runner = runner
suite2 = unittest.defaultTestLoader.loadTestsFromModule(previous_tests)
original_result = unittest.TextTestRunner(verbosity=2).run(suite2)
assert original_result.wasSuccessful() and original_result.testsRun == 23
baseline = load("b16_original_runner", D / "baseline" / RP)

old_cases = json.loads((OUT / "b-op16-independent-20261020/counterexamples.json").read_bytes())
normal = {"group": 0, "loopback": 0, "count_w": 4, "witness_w": 8, "tag_w": 8}
guard = {"id": "guard", "count_w": 0, "witness_w": 64, "tag_w": 32}
fixtures = D / "fresh-fixtures"
fixtures.mkdir()


def guard_call(module, text, err=b"", spec=None, exit_code=1):
    if spec is None:
        spec = guard
    (fixtures / (spec["id"] + ".stdout.txt")).write_bytes(text)
    (fixtures / (spec["id"] + ".stderr.txt")).write_bytes(err)
    with patch.object(module, "run_command", return_value={"exit": exit_code}):
        return module.run_invalid(fixtures, fixtures, [], {"vsim": "NEVER_EXECUTE"}, spec, 1)


def tb_call(module, text, spec=None):
    (fixtures / "tb.stdout.txt").write_bytes(text)
    (fixtures / "tb.stderr.txt").write_bytes(b"")
    parsed = module.parse_tb_output(fixtures / "tb.stdout.txt", fixtures / "tb.stderr.txt")
    return module.positive_result(spec or normal, {"record": {"exit": 0}, "parsed": parsed})


for row in old_cases["cases"]:
    src = OUT / "b-op16-independent-20261020" / row["stdout_path"]
    raw = src.read_bytes()
    assert sha(raw) == row["stdout_sha256"]
    if row["kind"] == "guard":
        observed = [guard_call(m, raw)["passed"] for m in (baseline, runner)]
    else:
        observed = [tb_call(m, raw) for m in (baseline, runner)]
    assert observed == [True, row["expected_accepted"]]
    checks.append({"name": row["name"], "stdout_sha256": sha(raw),
                   "baseline_accepted": observed[0], "final_accepted": observed[1]})

diag = (b"DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM COUNT_W=0 WITNESS_W=64 TAG_W=32 "
        b"SAFE_COUNT_W=2 SAFE_WITNESS_W=64 SAFE_TAG_W=32")
fatal = b"** Fatal: DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM unsupported widths"
legal = diag + b"\n" + fatal + b"\n"
# Independent asymmetric framing and post-terminal failure probes.
probes = [
    ("mixed-known-prefix-crlf", b"# " + diag + b"\r\n" + fatal + b"\n", b"", True),
    ("unterminated-final-fatal", diag + b"\n" + fatal, b"", True),
    ("embedded-NUL-diagnostic", diag[:30] + b"\x00" + diag[30:] + b"\n" + fatal, b"", False),
    ("double-CR", diag + b"\r\r\n" + fatal, b"", False),
    ("terminal-UTF8-refusal", legal + b"\xff", b"", False),
    ("stderr-late-own-fatal", legal, fatal, False),
    ("unknown-fatal-prefix", diag + b"\nNOTE " + fatal, b"", False),
    ("leading-zero-safe", legal.replace(b"SAFE_TAG_W=32", b"SAFE_TAG_W=032"), b"", False),
    ("negative-zero-input", legal.replace(b"COUNT_W=0", b"COUNT_W=-0"), b"", False),
    ("extra-fatal-between", diag + b"\n** Fatal: unrelated\n" + fatal, b"", False),
]
for name, text, err, expected in probes:
    actual = guard_call(runner, text, err)["passed"]
    assert actual is expected, name
    checks.append({"name": name, "expected": expected, "observed": actual,
                   "stdout_sha256": sha(text), "stderr_sha256": sha(err)})
supported = legal.replace(b"COUNT_W=0", b"COUNT_W=2")
assert guard_call(runner, supported, spec={**guard, "count_w": 2})["passed"] is False
checks.append({"name": "fully-supported-request-refuses-guard", "observed": False})

stats = b"TB_STATS groups=1 cases=1 samples=29 assertions=206 records=2 raw_faults=0 failure_events=0 window_starts=1 handshakes=1 mismatches=0\n"
code7 = b"CODE7_OBSERVED code=7 window_active=0 out_valid=0\n"
for label, text, requested, expected in [
    ("dedicated-code7-control", code7 + stats + b"TB_PASS group=30 loopback=0\n",
     {**normal, "group": 30}, True),
    ("dedicated-missing-code7", stats + b"TB_PASS group=30 loopback=0\n",
     {**normal, "group": 30}, False),
    ("loopback-code7-refused", code7 + stats + b"TB_PASS group=30 loopback=1\n",
     {**normal, "group": 30, "loopback": 1}, False),
]:
    actual = tb_call(runner, text, requested)
    assert actual is expected, label
    checks.append({"name": label, "expected": expected, "observed": actual})

# Old saved streams are independently rehashed here. Their Git blobs are
# unchanged between B16 and B17, as checked in source-verification.json.
saved = OUT / "b-op16-independent-20261020/snapshot/saved"
summary_raw = (saved / "RUN_SUMMARY.json").read_bytes()
assert sha(summary_raw) == "1bc4a0db74686b8c6d5033052f4a626f9ba9d59cd5f954d43965a99754f4bf31"
summary = json.loads(summary_raw)
records = {x["name"]: x for x in summary["commands"]}
assert len(records) == 47
for record in records.values():
    for channel in ("stdout", "stderr"):
        path = saved / Path(record[channel]).name
        assert sha(path.read_bytes()) == record[channel + "_sha256"]


def saved_result(name):
    record = records[name]
    parsed = runner.parse_tb_output(*(saved / Path(record[k]).name for k in ("stdout", "stderr")))
    parsed.update(transcript=None, transcript_sha256=None, wlf=None, wlf_sha256=None)
    return {"record": record, "parsed": parsed}


scenarios = []
for spec in runner.POSITIVE_RUNS:
    result = saved_result(spec["id"])
    scenarios.append({"name": spec["id"], "kind": "positive",
                      "accepted": runner.positive_entry(spec, result)["passed"],
                      "samples": result["parsed"]["stats"]["samples"]})
for mutant in runner.MUTANT_SPECS:
    for spec in mutant["runs"]:
        name = mutant["id"] + "-g" + str(spec["group"])
        scenarios.append({"name": name, "kind": spec["expect"],
                          "accepted": runner.mutant_result(spec, saved_result(name))})
for spec in runner.INVALID_RUNS:
    record = records[spec["id"]]
    stdout, stderr = [(saved / Path(record[k]).name).read_bytes() for k in ("stdout", "stderr")]
    actual = guard_call(runner, stdout, stderr, spec, record["exit"])["passed"]
    scenarios.append({"name": spec["id"], "kind": "guard", "accepted": actual})
assert len(scenarios) == 33 and all(x["accepted"] for x in scenarios)
assert sum(x.get("samples", 0) for x in scenarios) == 208667
assert not events
save("checks-result.json", {
    "current_methods": 31, "original_methods": 23, "original_method_ASTs_unchanged": True,
    "checks": checks, "saved_streams_rehashed": 94, "saved_scenarios": scenarios,
    "saved_positive_samples": 208667, "new_simulator_commands": 0,
    "prohibited_effect_attempts": events,
    "runner_sha256": sha((D / "snapshot" / RP).read_bytes()),
    "test_sha256": sha(newraw),
})
print(json.dumps({"current_methods": 31, "original_methods": 23,
                  "independent_checks": len(checks), "saved_scenarios": 33,
                  "saved_streams": 94, "prohibited_attempts": events}))

"""Build the post-run inspection manifest for the bounded R01 rereview."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PRODUCT = REPO / ".local" / "deepeye-implementation-a"
STAGE = ROOT / "stage-01" / "product"
REVIEW = REPO / ".planning" / "deepeye-resume-20261018" / "r01-checker-review"
REPAIR = REPO / ".planning" / "deepeye-resume-20261018" / "r01-checker-repair"
PRE = REPAIR / "pre-repair"
GIT = Path(r"C:\Users\CarlJade\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe")
REQUESTED_CANDIDATE = "9582bde875bf1aa2daef6c8f1b3d4925ed67cba0a22cb11f9d7ac0d773291f90"
REQUIREMENTS_SHA256 = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
EXPECTED_WEIGHTS = {
    "system_completeness": 20,
    "pc_ai": 20,
    "fpga_quality": 25,
    "cooperation": 20,
    "engineering_innovation": 15,
}
SOURCES = [
    "competition/deepeye/tools/check_rules.py",
    "competition/deepeye/tests/test_check_rules.py",
    "competition/deepeye/docs/rules_verification.md",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rec(path):
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False}
    data = path.read_bytes()
    return {"path": str(path), "exists": True, "bytes": len(data), "sha256": sha(data)}


def js(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def tree(root):
    outer = hashlib.sha256()
    files = sorted(p for p in Path(root).rglob("*") if p.is_file())
    for path in files:
        data = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        outer.update(rel.encode() + b"\0" + str(len(data)).encode() + b"\0" + sha(data).encode() + b"\n")
    return {"count": len(files), "tree_sha256": outer.hexdigest()}


def method_bodies(path):
    parsed = ast.parse(Path(path).read_text(encoding="utf-8"))
    return {
        n.name: ast.dump(n, include_attributes=False)
        for n in ast.walk(parsed)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
    }


def weights(path):
    for node in ast.parse(Path(path).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "ASSESSMENT_WEIGHTS":
            return ast.literal_eval(node.value)
    return None


def run_record(run_dir):
    command_path = run_dir / "command.json"
    command = js(command_path)
    stdout_path, stderr_path = run_dir / "stdout.log", run_dir / "stderr.log"
    stdout, stderr = rec(stdout_path), rec(stderr_path)
    exit_code = int((run_dir / "exit_code.txt").read_text(encoding="ascii").strip())
    report = None
    if stdout_path.stat().st_size:
        try:
            report = js(stdout_path)
        except json.JSONDecodeError:
            pass
    item = {
        "label": run_dir.name,
        "command": command,
        "command_file": rec(command_path),
        "exit_code_file": rec(run_dir / "exit_code.txt"),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "report": report,
        "capture_integrity": stdout.get("sha256") == command.get("stdout", {}).get("sha256")
        and stderr.get("sha256") == command.get("stderr", {}).get("sha256")
        and exit_code == command.get("exit_code")
        and command.get("environment", {}).get("PYTHONDONTWRITEBYTECODE") == "1"
        and command.get("environment", {}).get("PYTHONNOUSERSITE") == "1"
        and command.get("environment", {}).get("PYTHONIOENCODING") == "utf-8"
        and command.get("removed_pythonpath") is None,
    }
    if run_dir.name == "unittest20":
        text = stderr_path.read_text(encoding="utf-8")
        item["summary"] = {
            "ran_20_tests": "Ran 20 tests" in text,
            "ok": text.rstrip().endswith("OK"),
            "method_ok_lines": sum(line.startswith("test_") and " ... ok" in line for line in text.splitlines()),
        }
    return item


def main():
    static, provenance = js(ROOT / "review-static.json"), js(ROOT / "provenance.json")
    repair_manifest = js(REPAIR / "candidate-manifest.json")
    original_manifest = js(REPO / ".planning" / "deepeye-resume-20261018" / "r01-checker-main" / "candidate-manifest.json")
    candidate = rec(REPAIR / "candidate-manifest.json")
    patch = rec(REPAIR / "repair.patch")
    original_candidate = rec(REPO / ".planning" / "deepeye-resume-20261018" / "r01-checker-main" / "candidate-manifest.json")

    source_rehash = []
    for rel in SOURCES:
        source_rehash.append({
            "path": rel,
            "manifest": repair_manifest["source_files"][rel],
            "pre_repair": rec(PRE / rel),
            "product": rec(PRODUCT / rel),
            "staged": rec(STAGE / rel),
        })
    input_rehash = [{"expected": x["expected"], "current": rec(x["current"]["path"])} for x in static["inputs"]]
    evidence_rehash = [{"path": x["path"], "expected": x["expected"], "current": rec(REPAIR / x["path"])} for x in static["repair_evidence"]]

    before_methods = method_bodies(PRE / SOURCES[1])
    after_methods = method_bodies(PRODUCT / SOURCES[1])
    unchanged = sorted(k for k in before_methods if k in after_methods and before_methods[k] == after_methods[k])
    changed = sorted(k for k in before_methods if k in after_methods and before_methods[k] != after_methods[k])
    removed = sorted(k for k in before_methods if k not in after_methods)
    added = sorted(k for k in after_methods if k not in before_methods)

    checker_value = weights(PRODUCT / SOURCES[0])
    frozen_value = js(PRODUCT / "competition/deepeye/docs/rules.json").get("assessment_weights")
    weights_check = {
        "expected": EXPECTED_WEIGHTS,
        "checker": checker_value,
        "frozen_rules": frozen_value,
        "exact_key_set": isinstance(checker_value, dict) and set(checker_value) == set(EXPECTED_WEIGHTS),
        "all_values_exact_int": isinstance(checker_value, dict) and all(type(v) is int for v in checker_value.values()),
        "sum": sum(checker_value.values()) if isinstance(checker_value, dict) else None,
        "checker_equals_expected": checker_value == EXPECTED_WEIGHTS,
        "frozen_rules_equal_expected": frozen_value == EXPECTED_WEIGHTS,
        "checker_equals_frozen_rules": checker_value == frozen_value,
    }

    root_scope_path = REPO / "docs" / "competition" / "deepeye-2026" / "immutable_scope.json"
    product_scope_path = PRODUCT / "docs" / "competition" / "deepeye-2026" / "immutable_scope.json"
    root_scope, product_scope = js(root_scope_path), js(product_scope_path)
    canonical = json.dumps(root_scope["requirements"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ids = [row["id"] for row in root_scope["requirements"]]
    requirements_check = {
        "contract_id": root_scope.get("contract_id"),
        "revision": root_scope.get("revision"),
        "count": len(ids),
        "ids": ids,
        "expected_ids": [f"H{i:02d}" for i in range(1, 16)],
        "ids_match": ids == [f"H{i:02d}" for i in range(1, 16)],
        "declared_sha256": root_scope.get("requirements_sha256"),
        "canonical_sha256": sha(canonical),
        "expected_sha256": REQUIREMENTS_SHA256,
        "sha256_matches": sha(canonical) == REQUIREMENTS_SHA256,
        "root_scope": rec(root_scope_path),
        "product_scope": rec(product_scope_path),
        "scope_copies_identical": root_scope_path.read_bytes() == product_scope_path.read_bytes(),
    }

    original_tree = tree(REVIEW)
    historical = {}
    for label in ("case-weights-tamper", "case-weights-missing"):
        data = js(REVIEW / "runs" / f"{label}.json")
        historical[label] = {
            "metadata": rec(REVIEW / "runs" / f"{label}.json"),
            "returncode": data.get("returncode"),
            "stdout": data.get("stdout"),
            "stderr": data.get("stderr"),
            "preserved_false_pass": data.get("returncode") == 0,
        }

    fixtures = {}
    for label in ("weights-tamper", "weights-missing"):
        original, staged = REVIEW / "work" / "counterexamples" / label, ROOT / "stage-01" / "cases" / label
        staged_rules = js(staged / "competition/deepeye/docs/rules.json")
        fixtures[label] = {
            "original_rules": rec(original / "competition/deepeye/docs/rules.json"),
            "staged_rules": rec(staged / "competition/deepeye/docs/rules.json"),
            "rules_unchanged": (original / "competition/deepeye/docs/rules.json").read_bytes() == (staged / "competition/deepeye/docs/rules.json").read_bytes(),
            "assessment_weights": staged_rules.get("assessment_weights"),
            "assessment_weights_sum": sum(staged_rules["assessment_weights"].values()) if "assessment_weights" in staged_rules else None,
            "trace_unchanged": (original / "competition/deepeye/docs/requirements_trace.csv").read_bytes() == (staged / "competition/deepeye/docs/requirements_trace.csv").read_bytes(),
            "scope_unchanged": (original / "docs/competition/deepeye-2026/immutable_scope.json").read_bytes() == (staged / "docs/competition/deepeye-2026/immutable_scope.json").read_bytes(),
            "original_checker": rec(original / SOURCES[0]),
            "staged_checker_is_repaired": (staged / SOURCES[0]).read_bytes() == (PRODUCT / SOURCES[0]).read_bytes(),
            "original_checker_is_pre_repair": (original / SOURCES[0]).read_bytes() == (PRE / SOURCES[0]).read_bytes(),
        }

    runs = [run_record(path) for path in sorted(p for p in (ROOT / "runs").iterdir() if p.is_dir())]
    by_label = {item["label"]: item for item in runs}
    test = by_label["unittest20"]
    reference, default, full = by_label["cli-reference"], by_label["cli-default"], by_label["cli-full"]
    tamper, missing = by_label["case-weights-tamper"], by_label["case-weights-missing"]
    cli_reports = [reference["report"], default["report"], full["report"], tamper["report"], missing["report"]]
    checks = {
        "candidate_pin": candidate["sha256"] == REQUESTED_CANDIDATE,
        "repair_patch_pin": patch["sha256"] == repair_manifest["repair_evidence"]["repair.patch"],
        "original_candidate_pin": original_candidate["sha256"] == repair_manifest["original_candidate_sha256"] == static["original_candidate_manifest"]["sha256"],
        "sources_match_manifest_and_stage": all(x["product"]["sha256"] == x["manifest"] and x["staged"]["sha256"] == x["manifest"] for x in source_rehash),
        "sources_match_pre_repair_original": all(x["pre_repair"]["sha256"] == original_manifest["source_files"][x["path"]] for x in source_rehash),
        "all_6_inputs_stable": len(input_rehash) == 6 and all(x["current"]["sha256"] == x["expected"] for x in input_rehash),
        "all_24_repair_evidence_stable": len(evidence_rehash) == 24 and all(x["current"]["sha256"] == x["expected"] for x in evidence_rehash),
        "original_17_test_bodies_unchanged": len(unchanged) == 17 and not changed and not removed,
        "exactly_3_tests_added": len(added) == 3 and len(after_methods) == 20,
        "weights_exact_and_sum_100": all([weights_check["exact_key_set"], weights_check["all_values_exact_int"], weights_check["sum"] == 100, weights_check["checker_equals_expected"], weights_check["frozen_rules_equal_expected"], weights_check["checker_equals_frozen_rules"]]),
        "requirements_h01_h15": requirements_check["sha256_matches"] and requirements_check["ids_match"] and requirements_check["scope_copies_identical"],
        "original_review_95_files_stable": original_tree == {"count": 95, "tree_sha256": static["original_review_tree"]["tree_sha256"]},
        "imports_from_fresh_stage": provenance.get("import_origins_match_stage") is True and provenance.get("test_method_count") == 20,
        "suite_20_once_ok": test["exit_code"] == 0 and test["summary"] == {"ran_20_tests": True, "ok": True, "method_ok_lines": 20},
        "reference_0": reference["exit_code"] == 0 and reference["report"]["status"] == "reference_checks_passed",
        "default_2": default["exit_code"] == 2 and default["report"]["status"] == "blocked" and default["report"]["scope"] == "full_R01",
        "full_2": full["exit_code"] == 2 and full["report"]["status"] == "blocked" and full["report"]["scope"] == "full_R01",
        "tamper_1": tamper["exit_code"] == 1 and tamper["report"]["status"] == "failed" and tamper["report"].get("error") == "assessment weights differ from the reviewed section 3.2 distribution",
        "missing_1": missing["exit_code"] == 1 and missing["report"]["status"] == "failed" and missing["report"].get("error") == "assessment weights must contain exactly the reviewed section 3.2 categories",
        "formal_hardware_false": all(x.get("R01") == "not_run" and x.get("formal_acceptance") is False and x.get("hardware_enable_eligible") is False for x in cli_reports),
        "capture_integrity": all(x["capture_integrity"] for x in runs),
        "no_r01_scope_pycache": not any(any((base / "competition/deepeye" / part).rglob("__pycache__")) for base in (PRODUCT, STAGE) for part in ("tools", "tests", "docs")),
    }

    def git(*args):
        proc = subprocess.run([str(GIT), "-C", str(PRODUCT), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
        return {"argv": [str(GIT), "-C", str(PRODUCT), *args], "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}

    manifest = {
        "schema": 1,
        "task_id": "DEEPEYE-IMPLEMENTATION-20261014",
        "task_version": 1,
        "work_id": "A-R01-CHECKER-REREVIEW-20261020-v1",
        "main": "Desktop01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2",
        "candidate_sha256": REQUESTED_CANDIDATE,
        "candidate_manifest": candidate,
        "repair_patch": patch,
        "original_candidate_manifest": original_candidate,
        "static_review_artifact": rec(ROOT / "review-static.json"),
        "provenance_artifact": rec(ROOT / "provenance.json"),
        "provenance": provenance,
        "sources_before_after": source_rehash,
        "inputs": input_rehash,
        "repair_evidence": evidence_rehash,
        "test_methods": {"before_count": len(before_methods), "after_count": len(after_methods), "unchanged_count": len(unchanged), "changed": changed, "removed": removed, "added": added},
        "assessment_weights": weights_check,
        "source_association": static["source_association"],
        "requirements": requirements_check,
        "original_review": {"tree": original_tree, "key_files": static["original_review_key_files"], "historical_false_passes": historical},
        "counterexample_fixture_derivation": fixtures,
        "runs": runs,
        "run_count": len(runs),
        "run_exit_map": {x["label"]: x["exit_code"] for x in runs},
        "normal_default_full_exit_map": {"reference_only": reference["exit_code"], "default": default["exit_code"], "full_explicit_source": full["exit_code"]},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "finding_R01_CHK_01_closed_in_bounded_scope": all(checks.values()),
        "new_regression_observed": not all(checks.values()),
        "historical_policy": "The original findings.md and its two exit-0 reference-only false passes remain preserved as historical evidence and are not rewritten as PASS.",
        "git": {
            "initial_head_observed_by_static": static["git"]["head"],
            "final_head": git("rev-parse", "HEAD"),
            "final_branch": git("branch", "--show-current"),
            "final_subject": git("log", "-1", "--format=%H%n%ci%n%s"),
            "scoped_status": git("status", "--porcelain=v1", "--untracked-files=all", "--", *SOURCES, "competition/deepeye/docs/rules.json", "competition/deepeye/docs/requirements_trace.csv"),
            "note": "HEAD advanced through concurrent main work; the scoped source hashes and all pinned inputs stayed stable.",
        },
        "pycache_scope": {
            "r01_scope_clean": checks["no_r01_scope_pycache"],
            "unrelated_preexisting_product_paths": static["pycache_paths"],
        },
        "formal29": "not_run",
        "formal29_count": 29,
        "R01": "not_run",
        "formal_acceptance": False,
        "hardware_enable_eligible": False,
        "live_organizer_qualification": "not_run",
        "registration_qualification": "not_run",
        "rocm_project_C03": "not_run",
        "physical_gain_rules_recognition": "not_run",
        "physical_gain_engineering_A05": "not_run",
        "physical_task_qualification": "not_run",
    }
    manifest["checks"]["normal_default_full_0_2_2"] = manifest["normal_default_full_exit_map"] == {"reference_only": 0, "default": 2, "full_explicit_source": 2}
    manifest["all_checks_pass"] = all(manifest["checks"].values())
    manifest["finding_R01_CHK_01_closed_in_bounded_scope"] = manifest["all_checks_pass"]
    manifest["new_regression_observed"] = not manifest["all_checks_pass"]
    (ROOT / "inspection_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(ROOT / "inspection_manifest.json"), "sha256": rec(ROOT / "inspection_manifest.json")["sha256"], "all_checks_pass": manifest["all_checks_pass"], "exit_map": manifest["run_exit_map"], "requirements_sha256": requirements_check["canonical_sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

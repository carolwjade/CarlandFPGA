"""Bounded local evidence review; writes only beside this script, never retrieves."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qs
import ast
import csv
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import sys

OWN = Path(__file__).resolve().parent
ROOT = OWN.parents[2]
ORIGINAL = OWN.parent / "r01-official-source-refresh-20261020"
CANDIDATE = ORIGINAL / "candidate"
PRODUCT = ROOT / ".local/deepeye-implementation-a"
EVIDENCE_REL = Path("competition/deepeye/evidence/system/a-r01-official-source-refresh-20261020")
E = CANDIDATE / EVIDENCE_REL
PIN = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
PDF_PIN = "c6ad82acd4f7bdcd13bd412e232ed85d05f2a87dd5e2cdd04f9d219f88b569fc"
HEAD = "c0745419d7a317011d747f124544c98a900b1863"
CHECKS = []
READS = {}


def read(path):
    raw = path.read_bytes()
    READS[path.relative_to(ROOT).as_posix()] = {
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()
    }
    return raw


def load(path):
    return json.loads(read(path))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def check(name, condition, detail=None):
    entry = {"check": name, "passed": bool(condition)}
    if detail is not None:
        entry["detail"] = detail
    CHECKS.append(entry)


def save(name, value):
    path = (OWN / name).resolve()
    assert path.parent == OWN
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def without_query(value):
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def differences(a, b, parts=()):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                result.append(".".join(parts + (key,)))
            else:
                result += differences(a[key], b[key], parts + (key,))
        return result
    return [] if a == b else [".".join(parts)]


def url_query_fields(obj, parts=()):
    result = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            result += url_query_fields(value, parts + (key,))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            result += url_query_fields(value, parts + (str(index),))
    elif isinstance(obj, str) and obj.startswith(("http://", "https://")):
        parsed = urlsplit(obj)
        if parsed.query:
            result.append({"field": ".".join(parts), "query_keys": sorted(parse_qs(parsed.query))})
    return result


def main():
    source_snapshot = {
        p.relative_to(ORIGINAL).as_posix(): digest(p.read_bytes())
        for p in sorted(ORIGINAL.rglob("*")) if p.is_file()
    }
    root_scope = load(ROOT / "docs/competition/deepeye-2026/immutable_scope.json")
    product_scope_path = PRODUCT / "docs/competition/deepeye-2026/immutable_scope.json"
    product_scope = load(product_scope_path)
    for label, scope in (("root", root_scope), ("product", product_scope)):
        actual = digest(json.dumps(scope["requirements"], ensure_ascii=False,
                                   sort_keys=True, separators=(",", ":")).encode("utf-8"))
        check(label + "_immutable_hash", actual == PIN == scope["requirements_sha256"])
        check(label + "_H01_H15", [r["id"] for r in scope["requirements"]] ==
              ["H%02d" % i for i in range(1, 16)])
    transfer = load(ROOT / ".planning/deepeye-desktop-handoff-20261015/transfer.json")
    check("active_director", transfer["status"] == "active" and
          transfer["director_generation"] == 2 and
          transfer["new_director_thread_id"] == "01a13d7e-dcf1-7272-a738-a637dd62ff9d" and
          transfer["requirements_sha256"] == PIN)

    git = shutil.which("git")
    if git is None:
        installed = Path("C:/Program Files/Git/cmd/git.exe")
        git = str(installed) if installed.exists() else None
    git_result = {"available": git is not None}
    if git:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
        def git_read(*args):
            p = subprocess.run([git, "--no-optional-locks", "-C", str(PRODUCT), *args],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=20, creationflags=flags)
            if p.returncode:
                raise RuntimeError("read-only Git command failed with code " + str(p.returncode))
            return p.stdout
        actual_head = git_read("rev-parse", "HEAD").decode("ascii").strip()
        git_result.update(head=actual_head, head_matches=actual_head == HEAD)
        check("product_head", actual_head == HEAD, actual_head)
        committed_rules = git_read("show", HEAD + ":competition/deepeye/docs/rules.json")
    else:
        committed_rules = None
        check("product_head", False, "Git unavailable; no fallback authority assumed")

    manifest_path = ORIGINAL / "candidate-manifest.json"
    manifest = load(manifest_path)
    listed = {r["path"]: r for r in manifest["files"]}
    actual_paths = {p.relative_to(CANDIDATE).as_posix() for p in CANDIDATE.rglob("*") if p.is_file()}
    check("exact_ten_file_set", len(listed) == len(manifest["files"]) == 10 and actual_paths == set(listed))
    candidate_hashes = []
    for name in sorted(actual_paths):
        raw = read(CANDIDATE / name)
        actual = {"path": name, "bytes": len(raw), "sha256": digest(raw)}
        candidate_hashes.append(actual)
        check("manifest:" + name, actual == listed.get(name))

    original_rules_path = PRODUCT / "competition/deepeye/docs/rules.json"
    original_bytes = read(original_rules_path)
    original_rules = json.loads(original_bytes)
    candidate_rules_path = CANDIDATE / "competition/deepeye/docs/rules.json"
    candidate_bytes = read(candidate_rules_path)
    candidate_rules = json.loads(candidate_bytes)
    check("original_rules_pin", digest(original_bytes) == manifest["original_rules_sha256"])
    check("original_rules_equal_commit", committed_rules == original_bytes)
    changed = differences(original_rules, candidate_rules)
    allowed = ["source.latest_online_refresh", "source.online_refresh_evidence", "source.online_refresh_scope"]
    check("exact_allowed_json_changes", changed == allowed, changed)
    expected_bytes = original_bytes.replace(
        b'"latest_online_refresh": "blocked_web_tool_unavailable_for_official_site"',
        b'"latest_online_refresh": "official_catalogue_object_bytes_match_frozen_source_20261020",\n'
        b'    "online_refresh_evidence": "competition/deepeye/evidence/system/a-r01-official-source-refresh-20261020/result.json",\n'
        b'    "online_refresh_scope": "point-in-time download-catalogue object identity; not full R01 acceptance or proof of no later/other update"')
    check("minimal_rules_text_change", candidate_bytes == expected_bytes)

    pdf = read(E / "current-amd-guide.pdf")
    frozen_pdf = read(ROOT / "docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf")
    check("exact_frozen_pdf", pdf == frozen_pdf and len(pdf) == 950952 and
          digest(pdf) == PDF_PIN and pdf.startswith(b"%PDF-"))
    source_pdf = read(ORIGINAL / "current-amd-guide.pdf")
    check("candidate_pdf_equal_original_retrieval", source_pdf == pdf)

    raw_early_path = ORIGINAL / "fpga-public-signed-list.body"
    raw_zh_path = ORIGINAL / "fpga-public-signed-list-zh.body"
    raw_early_bytes, raw_zh_bytes = read(raw_early_path), read(raw_zh_path)
    raw_early, raw_zh = json.loads(raw_early_bytes), json.loads(raw_zh_bytes)
    sanitized = load(E / "catalogue-zh-sanitized.json")
    keys = ["id", "title", "createTime", "updateTime", "isEmphasis", "isTop"]
    expected = {
        "code": raw_zh["code"], "total": raw_zh["total"],
        "rows": [{**{k: row.get(k) for k in keys}, "object_url": without_query(row["file"])}
                 for row in raw_zh["rows"]]
    }
    check("exact_sanitized_projection", sanitized == expected)
    check("all_23_records", raw_early["code"] == raw_zh["code"] == sanitized["code"] == 200 and
          raw_early["total"] == raw_zh["total"] == sanitized["total"] ==
          len(raw_early["rows"]) == len(raw_zh["rows"]) == len(sanitized["rows"]) == 23 and
          len({r["id"] for r in sanitized["rows"]}) == 23)
    early_paths = {r["id"]: without_query(r["file"]) for r in raw_early["rows"]}
    zh_paths = {r["id"]: without_query(r["file"]) for r in raw_zh["rows"]}
    check("earlier_and_zh_object_paths_equal", early_paths == zh_paths)
    amd = next(r for r in sanitized["rows"] if r["id"] == 25)
    matches = [r["id"] for r in sanitized["rows"] if "2026" in (r["title"] or "") and "AMD" in (r["title"] or "")]
    check("unique_2026_AMD_id25", matches == [25] and amd["object_url"] == original_rules["source"]["official_url"])

    receipts = {}
    receipt_bindings = [
        ("current-amd-guide.retrieval.json", "current-amd-guide.pdf", "fetch-current-amd-guide.py", "script_sha256"),
        ("fpga-public-list.retrieval.json", "fpga-public-list.body", "fetch-index.py", "fetch_script_sha256"),
        ("fpga-public-signed-list-zh.retrieval.json", "fpga-public-signed-list-zh.body", "fetch-public-signed-list-zh.py", "fetch_script_sha256"),
        ("pinned-pdf.retrieval.json", "pinned-pdf.body", "fetch.py", "fetch_script_sha256"),
        ("official-download.retrieval.json", None, "fetch.py", "fetch_script_sha256"),
    ]
    for receipt_name, body_name, script_name, hash_field in receipt_bindings:
        receipt_bytes = read(E / receipt_name)
        receipt = json.loads(receipt_bytes)
        receipts[receipt_name] = receipt
        check("unchanged_receipt:" + receipt_name, receipt_bytes == read(ORIGINAL / receipt_name))
        check("receipt_script:" + receipt_name, digest(read(ORIGINAL / script_name)) == receipt[hash_field])
        if body_name:
            body = read(ORIGINAL / body_name)
            check("receipt_body:" + receipt_name, digest(body) == receipt["body_sha256"] and
                  len(body) == receipt["body_bytes"])
    retrieval = receipts["current-amd-guide.retrieval.json"]
    check("https_pdf_receipt", retrieval["status"] == 200 and
          retrieval["headers"]["Content-Type"] == "application/pdf" and
          int(retrieval["headers"]["Content-Length"]) == retrieval["body_bytes"] == 950952 and
          retrieval["body_sha256"] == retrieval["frozen_sha256"] == PDF_PIN and
          retrieval["public_object_url_without_query"] == amd["object_url"] and
          urlsplit(amd["object_url"]).scheme == "https" and retrieval["tls_verification"] == "default" and
          retrieval["account_credentials"] == "none" and retrieval["frozen_match"] is True and
          retrieval["pdf_signature"] is True)
    check("pdf_links_earlier_catalogue", retrieval["catalogue_body_sha256"] == digest(raw_early_bytes) and
          retrieval["catalogue_id"] == 25 and early_paths[25] == amd["object_url"])
    early_receipt = load(ORIGINAL / "fpga-public-signed-list.retrieval.json")
    check("earlier_catalogue_receipt", early_receipt["body_sha256"] == digest(raw_early_bytes) and
          early_receipt["body_bytes"] == len(raw_early_bytes) and early_receipt["status"] == 200 and
          early_receipt["fetch_script_sha256"] == digest(read(ORIGINAL / "fetch-public-signed-list.py")))
    api_error = load(ORIGINAL / "fpga-public-list.body")
    check("api401_invalid_timestamp", receipts["fpga-public-list.retrieval.json"]["status"] == 401 and
          api_error["code"] == 1001 and api_error["message"] == "时间戳无效")
    check("unsigned_object403_preserved", receipts["pinned-pdf.retrieval.json"]["status"] == 403 and
          receipts["pinned-pdf.retrieval.json"]["matches_frozen_pdf"] is False)
    check("original_https_catalogue_failure_preserved",
          receipts["official-download.retrieval.json"]["error_type"] == "URLError" and
          "CERTIFICATE_VERIFY_FAILED" in receipts["official-download.retrieval.json"]["error"])

    frontend = read(ORIGINAL / "fpga-http-utils.body")
    frontend_text = frontend.decode("utf-8-sig")
    zh_receipt = receipts["fpga-public-signed-list-zh.retrieval.json"]
    check("frontend_hash_bound", digest(frontend) == zh_receipt["public_frontend_sha256"])
    check("anonymous_schema_static_correspondence",
          all(marker in frontend_text for marker in [
              "Date.now().toString()", "i < 16", "Object.keys(signParams).sort()",
              "md5(stringToSign).toUpperCase()", "delete signParams.sign"]))
    check("http_transport_qualified", zh_receipt["endpoint"].startswith("http://") and
          "no transport authenticity claim" in zh_receipt["transport"] and
          zh_receipt["account_credentials"] == zh_receipt["cookies"] == "none")

    # Values below stay in memory. Outputs contain only names/counts, never values.
    private_strings = []
    for raw in [raw_early, raw_zh]:
        for row in raw["rows"]:
            parsed = urlsplit(row["file"])
            if parsed.query:
                private_strings += [row["file"], parsed.query]
                for key, values in parse_qs(parsed.query).items():
                    if key.lower() in {"signature", "ossaccesskeyid"}:
                        private_strings += values
    constant = re.search(r"""const\s+defaultKey\s*=\s*(['"])(.*?)\1\s*;""", frontend_text)
    if constant:
        private_strings.append(constant.group(2))
    leaks = []
    public_queries = []
    for row in candidate_hashes:
        path = CANDIDATE / row["path"]
        raw = read(path)
        if any(value and value.encode("utf-8") in raw for value in private_strings):
            leaks.append(row["path"])
        if path.suffix == ".json":
            for field in url_query_fields(json.loads(raw)):
                public_queries.append({"path": row["path"], **field})
    allowed_query_path = (EVIDENCE_REL / "fpga-public-list.retrieval.json").as_posix()
    check("no_temporary_authorization_or_client_signing_values", not leaks, {"matching_files": leaks})
    check("only_allowed_fixed_pagination_queries", len(public_queries) == 2 and all(
          f["path"] == allowed_query_path and f["field"] in {"requested_url", "final_url"} and
          f["query_keys"] == ["pageNum", "pageSize"] for f in public_queries), public_queries)
    check("raw_catalogues_not_packaged", not any(name.endswith(".body") for name in actual_paths))
    result = load(E / "result.json")
    readme = read(E / "README.md").decode("utf-8")
    check("result_matches_evidence", result["catalogue_item"] == amd and
          result["catalogue_titles_with_2026_and_AMD"] == matches and
          result["source_sha256"] == PDF_PIN and result["source_bytes"] == len(pdf) and
          result["catalogue_reported_total"] == result["catalogue_returned_count"] == 23)
    limits = "\n".join(result["limits"])
    check("limits_and_prior_diagnostic_disclosed", all(word in limits for word in [
          "point-in-time", "HTTP", "transport authenticity is not claimed", "elsewhere or later",
          "invalid timestamp", "no account credentials", "unsigned PDF URL returned403",
          "preliminary diagnostic accidentally printed raw file fields"]) and
          "Temporary URL queries" in readme)
    check("no_acceptance_promotion", result["R01"] == "not_run" and
          result["formal_cards"] == "all29 not_run" and
          result["formal_acceptance"] is result["hardware_enable_eligible"] is False and
          all(r["product_status"] == "not_run" for r in candidate_rules["requirements"]) and
          all(candidate_rules["gates"][k] == "not_run" for k in
              ["rocm_project_C03", "physical_gain_rules_recognition", "physical_gain_engineering_A05", "R01"]) and
          candidate_rules["registration"] == original_rules["registration"] and
          candidate_rules["registration"]["independent_receipt_verified"] is False)
    plan = load(PRODUCT / "docs/competition/deepeye-2026/execution_plan_final.json")
    tasks = plan["tasks"]
    check("all29_actual_formal_cards_not_run", isinstance(tasks, dict) and len(tasks) == 29 and
          all(t["status"] == "not_run" for t in tasks.values()))

    # Extract unchanged pure definitions only. The module's main, file helpers,
    # path globals and imports are not executed.
    checker_path = PRODUCT / "competition/deepeye/tools/check_rules.py"
    checker = read(checker_path).decode("utf-8")
    tree = ast.parse(checker, filename=str(checker_path))
    constant_names = {"PIN", "CONTRACT", "SOURCE", "SOURCE_SHA", "LIMIT", "STATES",
                      "COLUMNS", "POLICY", "SPECIALS", "ASSESSMENT_WEIGHTS"}
    function_names = {"require", "_pairs", "_constant", "_finite_float", "parse_json",
                      "parse_trace", "_same_members", "_state", "validate_metadata"}
    nodes = [n for n in tree.body if
             (isinstance(n, ast.Assign) and len(n.targets) == 1 and
              isinstance(n.targets[0], ast.Name) and n.targets[0].id in constant_names) or
             (isinstance(n, ast.FunctionDef) and n.name in function_names)]
    selected_functions = {n.name for n in nodes if isinstance(n, ast.FunctionDef)}
    assert selected_functions == function_names
    module = ast.Module(body=nodes, type_ignores=[])
    namespace = {"csv": csv, "hashlib": hashlib, "io": io, "json": json, "math": math}
    exec(compile(module, str(checker_path), "exec"), namespace)
    trace_path = PRODUCT / "competition/deepeye/docs/requirements_trace.csv"
    trace_bytes = read(trace_path)
    scope_bytes = read(product_scope_path)
    validation = namespace["validate_metadata"](
        namespace["parse_json"](candidate_bytes),
        namespace["parse_trace"](trace_bytes),
        namespace["parse_json"](scope_bytes))
    check("pure_validate_metadata", validation["human_requirements"] == 15 and
          validation["official_requirements"] == 15 and validation["core_metrics"] == 5 and
          validation["special_metrics"] == 2 and validation["requirements_sha256"] == PIN, validation)
    check("trace_all30_not_run", all(r["status"] == "not_run" for r in namespace["parse_trace"](trace_bytes)))
    metadata = {
        "status": "passed", "mode": "unchanged AST-selected pure functions; no module import/main/file helpers",
        "input_sha256": {
            "candidate_rules": digest(candidate_bytes), "current_trace": digest(trace_bytes),
            "current_scope": digest(scope_bytes), "checker_source": digest(checker.encode("utf-8"))
        },
        "extracted_functions": sorted(function_names),
        "selected_ast_sha256": digest(ast.dump(module, include_attributes=False).encode("utf-8")),
        "validate_metadata_output": validation, "formal_acceptance": False,
        "R01": "not_run", "full_reference_cli": "not_run; main will run after adoption",
    }
    save("metadata-validation.json", metadata)
    source_after = {
        p.relative_to(ORIGINAL).as_posix(): digest(p.read_bytes())
        for p in sorted(ORIGINAL.rglob("*")) if p.is_file()
    }
    check("original_evidence_and_candidate_unchanged_during_review", source_snapshot == source_after)
    check("all_read_inputs_unchanged_during_review", all(
        digest((ROOT / name).read_bytes()) == entry["sha256"] for name, entry in READS.items()))
    report = {
        "schema": 1, "checked_utc": datetime.now(timezone.utc).isoformat(),
        "work_id": "A-R01-SOURCE-REFRESH-INDEPENDENT-20261020-v1",
        "agent_id": "/root/r01_source_refresh_independent_20261020",
        "job_id": "child-6ff6b0ece2704e3e9726e816b0c07d9d",
        "scope": "bounded independent artifact/metadata/source-receipt review; no new retrieval or formal acceptance",
        "all_checks_passed": all(c["passed"] for c in CHECKS),
        "checks": CHECKS, "product_git": git_result,
        "candidate_manifest_sha256": digest(read(manifest_path)),
        "candidate_files": candidate_hashes, "changed_json_paths": changed,
        "source_sha256": digest(pdf), "source_bytes": len(pdf),
        "raw_catalogue_hashes": {"earlier": digest(raw_early_bytes), "zh": digest(raw_zh_bytes)},
        "formal_cards": {key: value["status"] for key, value in tasks.items()},
        "formal_acceptance": False, "hardware_enable_eligible": False,
        "remaining_gates": [
            "independent registration/qualification evidence",
            "organizer recognition of the proposed physical task",
            "actual ROCm project and physical engineering evidence",
            "separately reviewed formal acceptance integration"
        ],
        "clarification": "Main allows fixed pageNum/pageSize in original safe receipts; all temporary object authorization queries and client signing values are excluded.",
        "evidence_limitations": [
            "HTTP catalogue transport authenticity is not established.",
            "Earlier and zh catalogue responses are distinct; PDF receipt binds the earlier response and their full object-path maps agree.",
            "Local receipt/script/byte correspondence does not constitute a new network observation.",
            "The prior diagnostic disclosure is acknowledged by assignment and candidate; original conversation output was not replayed.",
            "No source semantics changed and no runtime, board, registration or product acceptance follows."
        ],
        "input_hashes": READS,
    }
    save("review-evidence.json", report)
    save("source-snapshot-before-after.json", {
        "original_directory": ORIGINAL.relative_to(ROOT).as_posix(),
        "unchanged": source_snapshot == source_after,
        "file_count": len(source_snapshot), "sha256_by_relative_path": source_snapshot
    })
    print(json.dumps({"checks": len(CHECKS), "passed": sum(c["passed"] for c in CHECKS),
                      "failed_checks": [c["check"] for c in CHECKS if not c["passed"]],
                      "candidate_files": len(candidate_hashes), "metadata": validation,
                      "formal_cards": "all29 not_run"}, ensure_ascii=False))
    return 0 if all(c["passed"] for c in CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

"""DeepEye R03 pipeline selftest suite (software only, Python stdlib only).

Run from the isolated worktree:
    <venv-python> -X utf8 tests/test_pipeline.py -v
with cwd = competition/deepeye.

The suite loads tools/pipeline.py from THIS worktree only and keeps every
ledger in a temporary directory; the default repository ledger is never
created here. No board, model, network or service calls are made.
"""
from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve()
DEEPEYE = HERE.parents[1]
PIPELINE = DEEPEYE / "tools" / "pipeline.py"
PYTHON = sys.executable
SELFTEST_DEPTH = int(os.environ.get("DEEPEYE_SELFTEST_DEPTH", "0") or "0")


def load_pipeline():
    if not PIPELINE.is_file():
        raise AssertionError("RED: tools/pipeline.py is not implemented yet (%s)" % PIPELINE)
    spec = importlib.util.spec_from_file_location("deepeye_pipeline_under_test", PIPELINE)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load %s" % PIPELINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(args, timeout=180):
    return subprocess.run(
        [PYTHON, "-X", "utf8", "-B", str(PIPELINE)] + [str(a) for a in args],
        cwd=str(DEEPEYE),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def stdout_json(proc):
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "stdout is not JSON (exit=%s): %r; stderr=%r"
            % (proc.returncode, proc.stdout[:400], proc.stderr[:400])
        ) from exc


def stderr_json(proc):
    for chunk in (proc.stderr, proc.stdout):
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            continue
    raise AssertionError("no JSON error document (exit=%s): %r" % (proc.returncode, proc.stderr[:400]))


def tree_listing(root):
    root = Path(root)
    return sorted(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*"))




WORKTREE = DEEPEYE.parents[1]

TRACKED_FIXTURE_CANDIDATES = (
    "competition/deepeye/hardware/environment.json",
    "competition/deepeye/README.md",
    "competition/deepeye/integration/wire.py",
    "competition/deepeye/integration/motion.py",
    "competition/deepeye/docs/rules.json",
    "competition/deepeye/docs/registers.csv",
)

def git(args, timeout=60):
    return subprocess.run(
        ["git", "-C", str(WORKTREE)] + [str(a) for a in args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def head_commit():
    proc = git(["rev-parse", "HEAD"])
    if proc.returncode != 0:
        raise AssertionError("git rev-parse HEAD failed: %r" % proc.stderr)
    return proc.stdout.strip()


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_clean_tracked_fixture():
    """Fixture only: existing tracked file whose worktree bytes equal the HEAD blob."""
    for rel in TRACKED_FIXTURE_CANDIDATES:
        path = WORKTREE / rel
        if not path.is_file():
            continue
        blob = git(["rev-parse", "HEAD:%s" % rel])
        if blob.returncode != 0:
            continue
        obj = git(["hash-object", "--", rel])
        if obj.returncode == 0 and obj.stdout.strip() == blob.stdout.strip():
            return rel
    raise AssertionError("selftest fixture error: no clean tracked file for provenance fixtures")


def make_clone_fixture(holder):
    """Fixture only: disposable local clone of the tested commit.

    Reads the existing object database with --shared (no network, no new
    commits, no change to the product repository); every write stays inside
    the temporary directory. The untracked-evidence regression uses this
    instead of depending on product files staying untracked forever.
    """
    clone = Path(holder) / "clone"
    proc = subprocess.run(
        ["git", "clone", "--quiet", "--shared", "--no-checkout", str(WORKTREE), str(clone)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    if proc.returncode != 0:
        raise AssertionError("fixture clone failed: %r" % proc.stderr)
    proc = subprocess.run(
        ["git", "-C", str(clone), "checkout", "--quiet", "--detach", head_commit()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    if proc.returncode != 0:
        raise AssertionError("fixture checkout failed: %r" % proc.stderr)
    return clone


class PipelineTestCase(unittest.TestCase):
    def setUp(self):
        self.mod = load_pipeline()
        holder = tempfile.TemporaryDirectory(prefix="deepeye-pipeline-")
        self.addCleanup(holder.cleanup)
        self.tmp = Path(holder.name)
        self.ledger_path = self.tmp / "state" / "pipeline_ledger.json"

    def ledger(self):
        return self.mod.Ledger(self.ledger_path)

    def test_plan_status_resume_are_strictly_read_only(self):
        before = tree_listing(self.tmp)
        proc = cli(["plan"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        plan = stdout_json(proc)
        self.assertEqual(plan["route_task_id"], self.mod.ROUTE_TASK_ID)
        self.assertEqual(plan["route_task_version"], self.mod.ROUTE_TASK_VERSION)
        self.assertEqual(plan["design_task_version"], self.mod.DESIGN_TASK_VERSION)
        self.assertEqual(plan["task_version"], self.mod.DESIGN_TASK_VERSION)
        self.assertIn("R03", plan["stages"]["s0"]["cards"])
        self.assertEqual(plan["stages"]["s7"]["cards"], [])
        proc = cli(["status", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        status = stdout_json(proc)
        self.assertFalse(status["ledger_exists"])
        self.assertEqual(status["records"], {})
        self.assertEqual(status["counts"]["running"], 0)
        proc = cli(["resume", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        audit = stdout_json(proc)
        self.assertFalse(audit["action_required"])
        self.assertEqual(audit["items"], [])
        self.assertFalse(self.ledger_path.exists())
        self.assertFalse(self.ledger_path.parent.exists())
        self.assertEqual(tree_listing(self.tmp), before)

    def test_scope_contract_hash_verified_on_every_run_and_verify(self):
        info = self.mod.verify_scope_contract()
        self.assertEqual(
            info["requirements_sha256"],
            "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804",
        )
        self.assertEqual(info["contract_id"], "DEEPEYE-HUMAN-LOCK-20261014")
        self.assertEqual(info["revision"], 1)
        self.assertEqual(info["requirement_ids"], ["H%02d" % n for n in range(1, 16)])
        real = json.loads(Path(self.mod.SCOPE_JSON).read_text(encoding="utf-8"))
        tampered = json.loads(json.dumps(real))
        tampered["requirements"][0]["must"] = str(tampered["requirements"][0]["must"]) + " TAMPERED"
        fake = self.tmp / "fake_scope.json"
        fake.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(self.mod.ContractError) as ctx:
            self.mod.verify_scope_contract(fake)
        self.assertEqual(ctx.exception.code, "contract_mismatch")
        proc = cli(["run", "--stage", "s0", "--card", "R03", "--task-version", "5",
                    "--work-id", "wrk-scope", "--ledger", self.ledger_path, "--scope", fake])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(stderr_json(proc)["code"], "contract_mismatch")
        proc = cli(["verify", "--scope", fake])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(stderr_json(proc)["code"], "contract_mismatch")
        self.assertFalse(self.ledger_path.exists())
        self.assertFalse(self.ledger_path.parent.exists())
        revision_fake = self.tmp / "fake_revision.json"
        revision_doc = json.loads(json.dumps(real))
        revision_doc["revision"] = 2
        revision_fake.write_text(json.dumps(revision_doc, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(self.mod.ContractError):
            self.mod.verify_scope_contract(revision_fake)
        contract_fake = self.tmp / "fake_contract.json"
        contract_doc = json.loads(json.dumps(real))
        contract_doc["contract_id"] = "OTHER-CONTRACT"
        contract_fake.write_text(json.dumps(contract_doc, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(self.mod.ContractError):
            self.mod.verify_scope_contract(contract_fake)
        proc = cli(["verify"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(stdout_json(proc)["contract"]["requirements_sha256"], self.mod.REQUIREMENTS_SHA256)

    def test_ownership_path_normalization_denies_escapes_and_aliases(self):
        good = {
            "competition/deepeye/tools/pipeline.py": "competition/deepeye/tools/pipeline.py",
            "Competition/Deepeye/Tools/Pipeline.py": "competition/deepeye/tools/pipeline.py",
            "a//b/./c/": "a/b/c",
        }
        for raw, want in good.items():
            self.assertEqual(self.mod.normalize_owned_path(raw), want, raw)
        denied = [
            "/etc/passwd",
            "//server/share",
            "C:/repo/x",
            "C:\\repo\\x",
            "\\\\server\\share\\x",
            "a\\b",
            "..",
            "a/../b",
            "a/../../x",
            "",
            "   ",
            "con/x",
            "aux",
            "nul.txt",
            "com1",
            "LPT9",
            "a:b",
            "a*b",
            "a?b",
            'a"b',
            "a<b",
            "a>b",
            "a|b",
            "a\x01b",
            "a /b",
            "a./b",
        ]
        for raw in denied:
            with self.assertRaises(self.mod.NormalizationError):
                self.mod.normalize_owned_path(raw)
        self.assertTrue(self.mod.paths_overlap("a/b", "a/b"))
        self.assertTrue(self.mod.paths_overlap("a/b", "a/b/c"))
        self.assertTrue(self.mod.paths_overlap("A/B", "a/b/c"))
        self.assertFalse(self.mod.paths_overlap("a/b", "a/bc"))
    def test_reservation_duplicate_reuse_and_conflicts(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = ["competition/deepeye/work/s0/reserve-fixture"]
        hash_a = "0" * 64
        rec1, created1 = ledger.reserve("wrk-dup", task, hash_a, ownership)
        self.assertTrue(created1)
        self.assertEqual(rec1["status"], "running")
        self.assertEqual(rec1["ownership"], ["competition/deepeye/work/s0/reserve-fixture"])
        bytes1 = self.ledger_path.read_bytes()
        rec2, created2 = ledger.reserve("wrk-dup", task, hash_a, list(reversed(ownership)))
        self.assertFalse(created2)
        self.assertEqual(rec2, rec1)
        self.assertEqual(self.ledger_path.read_bytes(), bytes1)
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.reserve("wrk-dup", task, "f" * 64, ownership)
        self.assertEqual(ctx.exception.code, "input_hash_conflict")
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.reserve("wrk-dup", self.mod.make_task("s1", ["B01"]), hash_a, ownership)
        self.assertEqual(ctx.exception.code, "task_conflict")
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.reserve("wrk-dup", task, hash_a, ["competition/deepeye/work/s0/other-fixture"])
        self.assertEqual(ctx.exception.code, "ownership_conflict")
        overlapping = [
            "competition/deepeye/work/s0/reserve-fixture",
            "competition/deepeye/work/s0",
            "competition/deepeye/work/s0/reserve-fixture/sub",
            "Competition/Deepeye/Work/S0/Reserve-Fixture",
        ]
        for index, held in enumerate(overlapping):
            with self.assertRaises(self.mod.ConflictError) as ctx:
                ledger.reserve("wrk-overlap-%d" % index, task, hash_a, [held])
            self.assertEqual(ctx.exception.code, "ownership_overlap")
        rec3, created3 = ledger.reserve("wrk-fresh", task, "b" * 64, ["competition/deepeye/work/s0/reserve-fixture2"])
        self.assertTrue(created3)
        self.assertEqual(rec3["status"], "running")
        with self.assertRaises(self.mod.NormalizationError):
            ledger.reserve("wrk-bad", task, "c" * 64, ["../escape"])

    def test_run_records_blocked_when_implementation_missing(self):
        args = ["run", "--stage", "s0", "--card", "R03", "--task-version", "5",
                "--work-id", "wrk-blocked", "--ledger", self.ledger_path]
        proc = cli(args)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertTrue(out["created"])
        self.assertFalse(out["reused"])
        record = out["record"]
        self.assertEqual(record["status"], "blocked")
        self.assertTrue(str(record["detail"]).startswith("implementation_missing"))
        self.assertEqual(record["task"]["cards"], ["R03"])
        self.assertEqual(record["task"]["owner"], "A")
        self.assertIsNone(record["acceptance"])
        self.assertEqual(record["execution"]["verdict"], "blocked")
        self.assertEqual(record["attempts"], 1)
        self.assertEqual(out["status"], "blocked")
        doc = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(doc["contract"]["requirements_sha256"], self.mod.REQUIREMENTS_SHA256)
        self.assertEqual(doc["records"]["wrk-blocked"]["status"], "blocked")
        before = self.ledger_path.read_bytes()
        proc = cli(args)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertTrue(out["reused"])
        self.assertEqual(out["record"]["attempts"], 1)
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_parallel_overlapping_reservations_exactly_one_wins(self):
        base = [str(PIPELINE), "run", "--stage", "s0", "--card", "R03", "--task-version", "5",
                "--ownership", "competition/deepeye/work/s0/parallel-fixture",
                "--ledger", str(self.ledger_path)]
        procs = []
        for work_id in ("wrk-par-1", "wrk-par-2"):
            procs.append(subprocess.Popen(
                [PYTHON, "-X", "utf8", "-B"] + base + ["--work-id", work_id],
                cwd=str(DEEPEYE), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace"))
        streams = [proc.communicate(timeout=180) for proc in procs]
        codes = sorted(proc.returncode for proc in procs)
        self.assertEqual(codes, [0, 2], streams)
        doc = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        records = doc["records"]
        winners = [work_id for work_id in ("wrk-par-1", "wrk-par-2") if work_id in records]
        self.assertEqual(len(records), 1)
        self.assertEqual(len(winners), 1)
        self.assertEqual(records[winners[0]]["status"], "blocked")
        loser_text = "".join(stream[1] for stream in streams)
        self.assertIn("ownership_overlap", loser_text)
    def test_failed_result_retained_and_never_replayed(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/failure-fixture"
        input_hash = self.mod.default_input_hash("s0", ["R03"])
        _, created = ledger.reserve("wrk-fail", task, input_hash, [ownership])
        self.assertTrue(created)
        record = ledger.complete("wrk-fail", "failed", "simulated_runner_failure")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["execution"]["verdict"], "failed")
        self.assertEqual(record["attempts"], 1)
        before = self.ledger_path.read_bytes()
        proc = cli(["run", "--stage", "s0", "--card", "R03", "--task-version", "5",
                    "--work-id", "wrk-fail", "--ownership", ownership,
                    "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertTrue(out["reused"])
        self.assertEqual(out["record"]["status"], "failed")
        self.assertEqual(out["record"]["attempts"], 1)
        self.assertEqual(self.ledger_path.read_bytes(), before)
        proc = cli(["resume", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 3, proc.stderr)
        audit = stdout_json(proc)
        self.assertTrue(audit["action_required"])
        items = {item["work_id"]: item for item in audit["items"]}
        self.assertEqual(items["wrk-fail"]["kind"], "failed_no_replay")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        proc = cli(["status", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        status = stdout_json(proc)
        self.assertEqual(status["records"]["wrk-fail"]["status"], "failed")
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_unknown_status_resume_is_read_only_without_side_effects(self):
        doc = {
            "schema": "deepeye.pipeline.ledger.v1",
            "records": {
                "wrk-unknown": {
                    "work_id": "wrk-unknown",
                    "status": "mystery_future_status",
                    "detail": "injected-by-selftest",
                    "task": {"stage": "s0", "cards": ["R03"], "owner": "A", "design_task_version": 5},
                    "ownership": ["competition/deepeye/work/s0/unknown-fixture"],
                    "input_hash": "c" * 64,
                    "attempts": 1,
                }
            },
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = self.ledger_path.read_bytes()
        listing_before = tree_listing(self.tmp)
        proc = cli(["resume", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 3, proc.stderr)
        audit = stdout_json(proc)
        self.assertTrue(audit["action_required"])
        items = {item["work_id"]: item for item in audit["items"]}
        self.assertEqual(items["wrk-unknown"]["kind"], "unknown_status")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        self.assertEqual(tree_listing(self.tmp), listing_before)
        self.assertFalse(Path(str(self.ledger_path) + ".lock").exists())

    def test_passed_requires_explicit_main_acceptance(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/accept-fixture"
        ledger.reserve("wrk-ok", task, "d" * 64, [ownership])
        record = ledger.complete("wrk-ok", "ok", "software_result_recorded")
        self.assertNotEqual(record["status"], "passed")
        self.assertEqual(record["status"], "running")
        self.assertEqual(record["execution"]["verdict"], "ok")
        self.assertIsNone(record["acceptance"])
        before = self.ledger_path.read_bytes()
        proc = cli(["run", "--stage", "s0", "--card", "R03", "--task-version", "5",
                    "--work-id", "wrk-ok", "--ownership", ownership, "--input-hash", "d" * 64,
                    "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertTrue(out["reused"])
        self.assertEqual(out["record"]["status"], "running")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        ledger.reserve("wrk-inflight", task, "e" * 64, ["competition/deepeye/work/s0/inflight-fixture"])
        proc = cli(["accept", "--work-id", "wrk-inflight", "--decision", "accepted",
                    "--by", "A-quality-main", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertEqual(stderr_json(proc)["code"], "invalid_transition")
        proc = cli(["accept", "--work-id", "wrk-nope", "--decision", "accepted",
                    "--by", "A-quality-main", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertEqual(stderr_json(proc)["code"], "unknown_work_id")
        fixture = find_clean_tracked_fixture()
        fixture_sha = sha256_of(WORKTREE / fixture)
        commit = head_commit()
        proc = cli(["accept", "--work-id", "wrk-ok", "--decision", "accepted",
                    "--by", "A-quality-main", "--artifact", "%s=%s" % (fixture, fixture_sha),
                    "--source", "%s=%s" % (fixture, fixture_sha),
                    "--commit", commit, "--command", "python tests/test_pipeline.py -v",
                    "--exit-code", "0", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertEqual(out["record"]["status"], "passed")
        self.assertEqual(out["record"]["acceptance"]["decision"], "accepted")
        self.assertEqual(out["record"]["acceptance"]["by"], "A-quality-main")
        provenance = out["record"]["acceptance"]["provenance"]
        self.assertEqual(provenance["commit"], commit)
        self.assertEqual(provenance["artifacts"], [{"path": fixture, "sha256": fixture_sha}])
        self.assertEqual(provenance["exit_code"], 0)
        ledger.reserve("wrk-rej", task, "a" * 64, ["competition/deepeye/work/s0/reject-fixture"])
        ledger.complete("wrk-rej", "ok", "")
        proc = cli(["accept", "--work-id", "wrk-rej", "--decision", "rejected",
                    "--by", "A-quality-main", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(stdout_json(proc)["record"]["status"], "failed")

    def test_run_rejects_unknown_cards_and_bad_versions_without_side_effects(self):
        cases = [
            (["run", "--stage", "s0", "--card", "NOPE", "--task-version", "5", "--work-id", "wrk-v1"], "unknown_card"),
            (["run", "--stage", "s7", "--card", "R03", "--task-version", "5", "--work-id", "wrk-v2"], "card_not_in_stage"),
            (["run", "--stage", "s7", "--task-version", "5", "--work-id", "wrk-v3"], "stage_has_no_cards"),
            (["run", "--stage", "s9", "--card", "R03", "--task-version", "5", "--work-id", "wrk-v4"], "unknown_stage"),
            (["run", "--stage", "s0", "--card", "R03", "--task-version", "4", "--work-id", "wrk-v5"], "design_task_version_mismatch"),
            (["run", "--stage", "s0", "--card", "R03", "--task-version", "5", "--work-id", "bad id!"], "invalid_work_id"),
        ]
        for args, code in cases:
            proc = cli(args + ["--ledger", self.ledger_path])
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertEqual(stderr_json(proc)["code"], code)
        self.assertFalse(self.ledger_path.exists())
        self.assertFalse(self.ledger_path.parent.exists())

    def _accepted_record(self, work_id, ownership):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ledger.reserve(work_id, task, self.mod.default_input_hash("s0", ["R03"]), [ownership])
        ledger.complete(work_id, "ok", "software_result_recorded")
        return ledger

    def test_accept_requires_artifact_and_commit_provenance(self):
        ownership = "competition/deepeye/work/s0/provenance-fixture"
        ledger = self._accepted_record("wrk-prov", ownership)
        commit = head_commit()
        fixture = find_clean_tracked_fixture()
        fixture_sha = sha256_of(WORKTREE / fixture)
        before = self.ledger_path.read_bytes()
        rejected = [
            (dict(), "provenance_missing"),
            (dict(artifacts=[("competition/deepeye/work/s0/absent.bin", "0" * 64)], commit=commit),
             "provenance_artifact_nonexistent"),
            (dict(artifacts=[(fixture, "0" * 64)], commit=commit), "provenance_artifact_changed"),
            (dict(artifacts=[(fixture, "zz" * 32)], commit=commit), "provenance_hash_invalid"),
            (dict(artifacts=[("../escape.bin", "0" * 64)], commit=commit), "provenance_path_unsafe"),
            (dict(artifacts=[(fixture, fixture_sha)], commit="0" * 40), "provenance_commit_invalid"),
            (dict(artifacts=[(fixture, fixture_sha)], commit=None), "provenance_commit_invalid"),
            (dict(artifacts=[(fixture, fixture_sha)], sources=[("/abs/source.py", "0" * 64)],
                  commit=commit), "provenance_path_unsafe"),
        ]
        parent = git(["rev-parse", "HEAD~1"])
        if parent.returncode == 0 and parent.stdout.strip() != commit:
            rejected.append((dict(artifacts=[(fixture, fixture_sha)], commit=parent.stdout.strip()),
                             "provenance_commit_mismatch"))
        clone = make_clone_fixture(self.tmp)
        untracked_rel = "competition/deepeye/work/s0/untracked-fixture.bin"
        untracked_path = clone / untracked_rel
        untracked_path.parent.mkdir(parents=True, exist_ok=True)
        untracked_path.write_bytes(b"untracked fixture bytes, never committed\n")
        rejected.append(
            (dict(artifacts=[(untracked_rel, sha256_of(untracked_path))], sources=[(fixture, fixture_sha)],
                  commit=commit, command="fixture command", exit_code=0, worktree_root=clone),
             "provenance_artifact_untracked")
        )
        for kwargs, code in rejected:
            with self.assertRaises(self.mod.ConflictError) as ctx:
                ledger.accept("wrk-prov", "accepted", "A-quality-main", **kwargs)
            self.assertEqual(ctx.exception.code, code, kwargs)
            self.assertEqual(self.ledger_path.read_bytes(), before)
        record = ledger.accept(
            "wrk-prov", "accepted", "A-quality-main",
            artifacts=[(fixture, fixture_sha)],
            sources=[(fixture, fixture_sha)],
            commit=commit,
            command="python tests/test_pipeline.py -v",
            exit_code=0,
        )
        self.assertEqual(record["status"], "passed")
        provenance = record["acceptance"]["provenance"]
        self.assertEqual(provenance["commit"], commit)
        self.assertEqual(provenance["artifacts"], [{"path": fixture, "sha256": fixture_sha}])
        self.assertEqual(provenance["sources"], [{"path": fixture, "sha256": fixture_sha}])
        self.assertEqual(provenance["exit_code"], 0)
        self.assertTrue(provenance["command"])

    def test_accept_cli_requires_pair_flags_and_rejects_bad_commit(self):
        ownership = "competition/deepeye/work/s0/provenance-cli-fixture"
        self._accepted_record("wrk-prov-cli", ownership)
        commit = head_commit()
        fixture = find_clean_tracked_fixture()
        before = self.ledger_path.read_bytes()
        proc = cli(["accept", "--work-id", "wrk-prov-cli", "--decision", "accepted",
                    "--by", "A-quality-main", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(stderr_json(proc)["code"], "provenance_missing")
        proc = cli(["accept", "--work-id", "wrk-prov-cli", "--decision", "accepted",
                    "--by", "A-quality-main", "--artifact", "no-separator",
                    "--commit", commit, "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(stderr_json(proc)["code"], "provenance_pair_invalid")
        proc = cli(["accept", "--work-id", "wrk-prov-cli", "--decision", "accepted",
                    "--by", "A-quality-main", "--artifact", "%s=%s" % (fixture, "0" * 64),
                    "--commit", commit, "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(stderr_json(proc)["code"], "provenance_artifact_changed")
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_verify_rejects_stale_or_missing_accepted_provenance(self):
        commit = head_commit()
        fixture = find_clean_tracked_fixture()
        fixture_sha = sha256_of(WORKTREE / fixture)
        ledger = self._accepted_record("wrk-stale", "competition/deepeye/work/s0/stale-fixture")
        record = ledger.accept("wrk-stale", "accepted", "A-quality-main",
                               artifacts=[(fixture, fixture_sha)], sources=[(fixture, fixture_sha)],
                               commit=commit, command="python tests/test_pipeline.py -v", exit_code=0)
        self.assertEqual(record["status"], "passed")
        proc = cli(["verify", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        doc = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        doc["records"]["wrk-stale"]["acceptance"]["provenance"]["artifacts"][0]["sha256"] = "0" * 64
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = self.ledger_path.read_bytes()
        proc = cli(["verify", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 1, proc.stdout)
        error = stderr_json(proc)
        self.assertEqual(error["code"], "ledger_invariant_failed")
        self.assertIn("provenance", error["error"])
        self.assertEqual(self.ledger_path.read_bytes(), before)
        doc["records"]["wrk-stale"]["acceptance"].pop("provenance")
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        proc = cli(["verify", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("provenance", stderr_json(proc)["error"])

    def test_release_requires_explicit_stop_confirmation_and_evidence(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/release-fixture"
        ledger.reserve("wrk-rel", task, self.mod.default_input_hash("s0", ["R03"]), [ownership])
        record = ledger.complete("wrk-rel", "failed", "simulated_runner_failure")
        execution_before = dict(record["execution"])
        history_before = len(record.get("history") or [])
        before = self.ledger_path.read_bytes()
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-rel", "A-quality-main", False, "verified stop: main confirmed")
        self.assertEqual(ctx.exception.code, "release_not_confirmed")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-rel", "A-quality-main", True, "   ")
        self.assertEqual(ctx.exception.code, "release_evidence_required")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-rel", "A-quality-main", True, "")
        self.assertEqual(ctx.exception.code, "release_evidence_required")
        ledger.reserve("wrk-live", task, "5" * 64, ["competition/deepeye/work/s0/live-fixture"])
        live_bytes = self.ledger_path.read_bytes()
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-live", "A-quality-main", True, "stop requested but unverified")
        self.assertEqual(ctx.exception.code, "active_operation_no_release")
        self.assertEqual(self.ledger_path.read_bytes(), live_bytes)
        released = ledger.release(
            "wrk-rel", "A-quality-main", True,
            "main stop confirmation: operation stopped, no pending side effects",
        )
        self.assertEqual(released["status"], "failed")
        self.assertEqual(released["detail"], "simulated_runner_failure")
        self.assertEqual(released["execution"], execution_before)
        self.assertEqual(len(released["history"]), history_before + 1)
        self.assertTrue(released["release"]["stop_confirmed"])
        self.assertEqual(released["release"]["by"], "A-quality-main")
        self.assertTrue(released["release"]["evidence"].strip())
        released_bytes = self.ledger_path.read_bytes()
        again = ledger.release(
            "wrk-rel", "A-quality-main", True,
            "main stop confirmation: operation stopped, no pending side effects",
        )
        self.assertEqual(again["release"], released["release"])
        self.assertEqual(self.ledger_path.read_bytes(), released_bytes)
        rec2, created2 = ledger.reserve("wrk-rel-next", task, "6" * 64, [ownership])
        self.assertTrue(created2)
        self.assertEqual(rec2["status"], "running")

    def test_release_rejects_unknown_status_and_unverified_terminal(self):
        doc = {
            "schema": "deepeye.pipeline.ledger.v1",
            "records": {
                "wrk-unknown-rel": {
                    "work_id": "wrk-unknown-rel",
                    "status": "mystery_future_status",
                    "detail": "injected-by-selftest",
                    "task": {"stage": "s0", "cards": ["R03"], "owner": "A", "design_task_version": 5},
                    "ownership": ["competition/deepeye/work/s0/unknown-release-fixture"],
                    "input_hash": "8" * 64,
                    "attempts": 1,
                    "acceptance": None,
                    "execution": {"verdict": None, "detail": "", "started_at": None, "finished_at": None},
                    "history": [],
                }
            },
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = self.ledger_path.read_bytes()
        ledger = self.ledger()
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-unknown-rel", "A-quality-main", True, "stop confirmed")
        self.assertEqual(ctx.exception.code, "unknown_status_no_release")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        doc["records"]["wrk-unknown-rel"]["status"] = "failed"
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = self.ledger_path.read_bytes()
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-unknown-rel", "A-quality-main", True, "stop confirmed")
        self.assertEqual(ctx.exception.code, "unverified_terminal_no_release")
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_released_duplicate_reserve_reuses_identity_and_never_reexecutes(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/dup-release-fixture"
        input_hash = self.mod.default_input_hash("s0", ["R03"])
        _, created = ledger.reserve("wrk-dup-rel", task, input_hash, [ownership])
        self.assertTrue(created)
        ledger.complete("wrk-dup-rel", "failed", "simulated_failure")
        ledger.release("wrk-dup-rel", "A-quality-main", True, "verified stop: failure contained")
        before = self.ledger_path.read_bytes()
        record, created2 = ledger.reserve("wrk-dup-rel", task, input_hash, list(reversed([ownership])))
        self.assertFalse(created2)
        self.assertEqual(record["attempts"], 1)
        self.assertEqual(record["execution"]["verdict"], "failed")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.complete("wrk-dup-rel", "ok", "replay attempt")
        self.assertEqual(ctx.exception.code, "invalid_transition")
        proc = cli(["run", "--stage", "s0", "--card", "R03", "--task-version", "5",
                    "--work-id", "wrk-dup-rel", "--ownership", ownership,
                    "--input-hash", input_hash, "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertTrue(out["reused"])
        self.assertEqual(out["record"]["attempts"], 1)
        self.assertEqual(out["record"]["execution"]["verdict"], "failed")
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_verify_ignores_released_claims_and_rejects_invalid_release(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/released-overlap-fixture"
        ledger.reserve("wrk-v1", task, "a1" * 32, [ownership])
        ledger.complete("wrk-v1", "failed", "simulated_failure")
        ledger.release("wrk-v1", "A-quality-main", True, "verified stop")
        rec2, created2 = ledger.reserve("wrk-v2", task, "b2" * 32, [ownership])
        self.assertTrue(created2)
        proc = cli(["verify", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        out = stdout_json(proc)
        self.assertTrue(out["checks"][-1]["ok"])
        self.assertEqual(out["checks"][-1]["problems"], [])
        doc = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        doc["records"]["wrk-v1"]["release"]["evidence"] = "   "
        doc["records"]["wrk-v3"] = {
            "work_id": "wrk-v3",
            "status": "running",
            "detail": "injected-active-overlap",
            "task": {"stage": "s0", "cards": ["R03"], "owner": "A", "design_task_version": 5},
            "ownership": [ownership],
            "input_hash": "c3" * 32,
            "attempts": 1,
            "acceptance": None,
            "execution": {"verdict": None, "detail": "", "started_at": None, "finished_at": None},
            "history": [],
        }
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = self.ledger_path.read_bytes()
        proc = cli(["verify", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 1, proc.stdout)
        error = stderr_json(proc)
        self.assertEqual(error["code"], "ledger_invariant_failed")
        self.assertIn("release", error["error"])
        self.assertIn("overlapping ownership", error["error"])
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_release_cli_and_inert_runners(self):
        self.assertEqual(self.mod.RUNNERS, {})
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/release-cli-fixture"
        ledger.reserve("wrk-cli-rel", task, "d4" * 32, [ownership])
        ledger.complete("wrk-cli-rel", "failed", "simulated_failure")
        proc = cli(["release", "--work-id", "wrk-cli-rel", "--by", "A-quality-main",
                    "--stop-confirmed", "--evidence", "main verified stop",
                    "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = stdout_json(proc)
        self.assertEqual(out["command"], "release")
        self.assertTrue(out["record"]["release"]["stop_confirmed"])
        self.assertEqual(out["record"]["status"], "failed")
        before = self.ledger_path.read_bytes()
        proc = cli(["release", "--work-id", "wrk-cli-rel", "--by", "A-quality-main",
                    "--evidence", "no confirmation", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(stderr_json(proc)["code"], "release_not_confirmed")
        proc = cli(["release", "--work-id", "wrk-cli-rel", "--by", "A-quality-main",
                    "--stop-confirmed", "--evidence", "   ", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(stderr_json(proc)["code"], "release_evidence_required")
        self.assertEqual(self.ledger_path.read_bytes(), before)

    @unittest.skipIf(SELFTEST_DEPTH > 0, "nested verify --selftest run")
    def test_verify_selftest_runs_real_tests(self):
        proc = cli(["verify", "--selftest"])
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        out = stdout_json(proc)
        selftest = out["selftest"]
        self.assertTrue(selftest["ok"])
        self.assertGreaterEqual(selftest["tests_ran"], 8)
        self.assertEqual(selftest["returncode"], 0)
        self.assertIn("OK", selftest["stdout_tail"])


    def test_accept_requires_source_command_and_successful_exit_provenance(self):
        ownership = "competition/deepeye/work/s0/strict-provenance-fixture"
        ledger = self._accepted_record("wrk-strict", ownership)
        commit = head_commit()
        fixture = find_clean_tracked_fixture()
        fixture_sha = sha256_of(WORKTREE / fixture)
        before = self.ledger_path.read_bytes()
        base = dict(artifacts=[(fixture, fixture_sha)], commit=commit)
        sources = [(fixture, fixture_sha)]
        rejected = [
            (dict(base, command="python tests/test_pipeline.py -v", exit_code=0),
             "provenance_sources_missing"),
            (dict(base, sources=[], command="python tests/test_pipeline.py -v", exit_code=0),
             "provenance_sources_missing"),
            (dict(base, sources=sources, exit_code=0), "provenance_command_invalid"),
            (dict(base, sources=sources, command="   ", exit_code=0), "provenance_command_invalid"),
            (dict(base, sources=sources, command="fixture command"),
             "provenance_exit_code_invalid"),
            (dict(base, sources=sources, command="fixture command", exit_code=None),
             "provenance_exit_code_invalid"),
            (dict(base, sources=sources, command="fixture command", exit_code=True),
             "provenance_exit_code_invalid"),
            (dict(base, sources=sources, command="fixture command", exit_code=23),
             "provenance_exit_code_nonzero"),
        ]
        for kwargs, code in rejected:
            with self.assertRaises(self.mod.ConflictError) as ctx:
                ledger.accept("wrk-strict", "accepted", "A-quality-main", **kwargs)
            self.assertEqual(ctx.exception.code, code, kwargs)
            self.assertEqual(self.ledger_path.read_bytes(), before)
        record = ledger.accept(
            "wrk-strict", "accepted", "A-quality-main",
            artifacts=[(fixture, fixture_sha)], sources=sources, commit=commit,
            command="python tests/test_pipeline.py -v", exit_code=0,
        )
        self.assertEqual(record["status"], "passed")
        provenance = record["acceptance"]["provenance"]
        self.assertEqual(provenance["sources"], [{"path": fixture, "sha256": fixture_sha}])
        self.assertEqual(provenance["command"], "python tests/test_pipeline.py -v")
        self.assertEqual(provenance["exit_code"], 0)

    def test_verify_rejects_accepted_records_without_source_command_exit(self):
        commit = head_commit()
        fixture = find_clean_tracked_fixture()
        fixture_sha = sha256_of(WORKTREE / fixture)
        ledger = self._accepted_record(
            "wrk-legacy-strict", "competition/deepeye/work/s0/legacy-strict-fixture"
        )
        record = ledger.accept(
            "wrk-legacy-strict", "accepted", "A-quality-main",
            artifacts=[(fixture, fixture_sha)], sources=[(fixture, fixture_sha)], commit=commit,
            command="python tests/test_pipeline.py -v", exit_code=0,
        )
        self.assertEqual(record["status"], "passed")
        doc = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        mutations = (("sources", []), ("command", None), ("command", "   "),
                     ("exit_code", None), ("exit_code", True), ("exit_code", 23))
        for field, value in mutations:
            doc["records"]["wrk-legacy-strict"]["acceptance"]["provenance"][field] = value
            self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
            before = self.ledger_path.read_bytes()
            proc = cli(["verify", "--ledger", self.ledger_path])
            self.assertEqual(proc.returncode, 1, proc.stdout)
            error = stderr_json(proc)
            self.assertEqual(error["code"], "ledger_invariant_failed")
            self.assertIn("provenance", error["error"])
            self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_malformed_release_cannot_free_ownership(self):
        ownership = "competition/deepeye/work/s0/malformed-release-fixture"
        doc = {
            "schema": "deepeye.pipeline.ledger.v1",
            "records": {
                "wrk-mal-rel": {
                    "work_id": "wrk-mal-rel",
                    "status": "running",
                    "detail": "injected-active-record-with-incomplete-release",
                    "task": {"stage": "s0", "cards": ["R03"], "owner": "A", "design_task_version": 5},
                    "ownership": [ownership],
                    "input_hash": "7" * 64,
                    "attempts": 1,
                    "acceptance": None,
                    "execution": {"verdict": None, "detail": "", "started_at": None, "finished_at": None},
                    "release": {"stop_confirmed": True,
                                "evidence": "fixture injected incomplete release metadata"},
                    "history": [],
                }
            },
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")
        before = self.ledger_path.read_bytes()
        self.assertFalse(self.mod.is_released_record(doc["records"]["wrk-mal-rel"]))
        ledger = self.ledger()
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.release("wrk-mal-rel", "A-quality-main", True, "stop claim without terminal proof")
        self.assertEqual(ctx.exception.code, "active_operation_no_release")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        with self.assertRaises(self.mod.ConflictError) as ctx:
            ledger.reserve("wrk-mal-next", self.mod.make_task("s0", ["R03"]), "8" * 64, [ownership])
        self.assertEqual(ctx.exception.code, "ownership_overlap")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        proc = cli(["verify", "--ledger", self.ledger_path])
        self.assertEqual(proc.returncode, 1, proc.stdout)
        error = stderr_json(proc)
        self.assertEqual(error["code"], "ledger_invariant_failed")
        self.assertIn("release", error["error"])
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_valid_terminal_releases_still_free_ownership(self):
        ledger = self.ledger()
        task = self.mod.make_task("s0", ["R03"])
        ownership = "competition/deepeye/work/s0/valid-terminal-release-fixture"
        ledger.reserve("wrk-ok-pending", task, "9" * 64, [ownership])
        ledger.complete("wrk-ok-pending", "ok", "software_result_recorded")
        released = ledger.release("wrk-ok-pending", "A-quality-main", True,
                                  "verified stop: ok pending main, no pending side effects")
        self.assertTrue(released["release"]["stop_confirmed"])
        self.assertEqual(released["status"], "running")
        self.assertEqual(released["execution"]["verdict"], "ok")
        _, created = ledger.reserve("wrk-ok-next", task, "a9" * 32, [ownership])
        self.assertTrue(created)
        for status, verdict in (("passed", "ok"), ("blocked", "blocked")):
            fixture_record = {
                "work_id": "wrk-pred-fixture",
                "status": status,
                "execution": {"verdict": verdict, "finished_at": "2026-10-15T00:00:00+00:00"},
                "release": {"stop_confirmed": True, "by": "A-quality-main",
                            "at": "2026-10-15T00:00:01+00:00", "evidence": "verified stop"},
            }
            self.assertTrue(self.mod.is_released_record(fixture_record), status)

    def test_evidence_paths_must_stay_inside_the_worktree_root(self):
        clone = make_clone_fixture(self.tmp)
        commit = head_commit()
        fixture = find_clean_tracked_fixture()
        fixture_sha = sha256_of(clone / fixture)
        outside = self.tmp / "outside"
        outside.mkdir()
        (outside / "provenance.bin").write_bytes(b"outside-the-root bytes\n")
        escape = clone / "aliasdir"
        created = True
        try:
            escape.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            created = False
            proc = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(escape), str(outside)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            created = proc.returncode == 0 and escape.exists()
        if not created:
            self.skipTest("native symlink/junction privilege unavailable on this platform")
        escape_sha = sha256_of(outside / "provenance.bin")
        with self.assertRaises(self.mod.ConflictError) as ctx:
            self.mod._validate_evidence_file(
                "artifact", "aliasdir/provenance.bin", escape_sha, commit, clone
            )
        self.assertEqual(ctx.exception.code, "provenance_path_unsafe")
        record = {
            "work_id": "wrk-alias",
            "status": "passed",
            "acceptance": {
                "decision": "accepted",
                "provenance": {
                    "commit": commit,
                    "artifacts": [{"path": "aliasdir/provenance.bin", "sha256": escape_sha}],
                    "sources": [{"path": fixture, "sha256": fixture_sha}],
                    "command": "python tests/test_pipeline.py -v",
                    "exit_code": 0,
                },
            },
            "execution": {"verdict": "ok", "finished_at": "2026-10-15T00:00:00+00:00"},
        }
        problems = self.mod.check_record_provenance(record, worktree_root=clone)
        self.assertTrue(
            any("uses a link or reparse point" in item for item in problems), problems
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

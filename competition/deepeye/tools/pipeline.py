#!/usr/bin/env python3
"""DeepEye bounded software pipeline foundation (competition card R03).

Entry point: python tools/pipeline.py

Design task version: 5 (frozen design
1011259415a0916054eb580687612580bc1e5f09). Execution route fields are
separate: route task DEEPEYE-IMPLEMENTATION-20261014 version 1.

Human contract: DEEPEYE-HUMAN-LOCK-20261014/revision 1, requirements H01-H15
mandatory and immutable; the canonical requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 is verified
on every run/verify/accept invocation and the command aborts on mismatch.

Bounded semantics (Python standard library only; no board, model, network or
service calls, no hidden side effects):
  plan    read-only stage/card view; never writes and never creates directories
  status  read-only ledger view; never writes and never creates directories
  run     bounded reservation for explicitly chosen known cards only; the
          reservation claims normalized ownership paths; a card without a
          registered implementation is recorded blocked (implementation_missing)
  verify  recomputes the contract hash and ledger invariants; --selftest runs
          the real unit suite tests/test_pipeline.py (no fabricated counters)
  resume  read-only audit of running/failed/blocked/unknown records; returns
          the main decision required and never re-executes anything
  accept  records the explicit quality-main acceptance; only this decision
          flips a completed execution to passed, and acceptance requires
          existing safe artifact bytes matching their recorded SHA256 plus a
          non-empty tested source manifest, the exact tested command, a
          successful integer exit code 0 and a tested full Git commit whose
          blobs match the worktree bytes (no metadata-only acceptance, no
          dirty-worktree acceptance)
  release records an explicit operator-confirmed stop and frees the recorded
          ownership for later distinct work only for a record that still
          shows a verified terminal execution (valid verdict, finish time and
          compatible status); the original status, detail, execution result,
          acceptance and history are preserved unchanged

Ledger statuses: not_run / running / passed / failed / blocked. Failures,
unknown states and in-flight reservations are retained and are never replayed
automatically; resume only reports the required main decision.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

DESIGN_TASK_VERSION = 5
ROUTE_TASK_ID = "DEEPEYE-IMPLEMENTATION-20261014"
ROUTE_TASK_VERSION = 1
CONTRACT_ID = "DEEPEYE-HUMAN-LOCK-20261014"
CONTRACT_REVISION = 1
REQUIREMENTS_SHA256 = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"

PIPELINE_FILE = Path(__file__).resolve()
DEEPEYE_DIR = PIPELINE_FILE.parents[1]
WORKTREE_ROOT = DEEPEYE_DIR.parents[1]
SCOPE_JSON = WORKTREE_ROOT / "docs" / "competition" / "deepeye-2026" / "immutable_scope.json"
PLAN_JSON = WORKTREE_ROOT / "docs" / "competition" / "deepeye-2026" / "execution_plan_final.json"
TASKBOOK_MD = WORKTREE_ROOT / "docs" / "competition" / "deepeye-2026" / "taskbook_final.md"
DEFAULT_LEDGER = DEEPEYE_DIR / "evidence" / "system" / "pipeline_ledger.json"

VALID_STAGES = ("s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7")
VALID_STATUSES = ("not_run", "running", "passed", "failed", "blocked")
# A released record must still show a verified terminal execution: valid
# verdict, recorded finish time, and a status compatible with that verdict.
RELEASE_TERMINAL_STATUSES = {
    "ok": ("running", "passed"),
    "failed": ("failed",),
    "blocked": ("blocked",),
}
WORK_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ROUTE_FIELDS = {"route_task_id": ROUTE_TASK_ID, "route_task_version": ROUTE_TASK_VERSION}

# Card implementations register bounded runners here in later tasks. The R03
# foundation intentionally ships no registered runner, so `run` records
# blocked (implementation_missing) instead of guessing or shelling out.
RUNNERS = {}

# Declared card outputs used as default bounded ownership claims (taskbook R03
# card: docs/interface.json, docs/registers.csv, tests/vectors, tools/pipeline.py).
# Cards without a declared mapping fall back to a bounded claim namespace.
DEFAULT_CLAIMS = {
    "R03": (
        "competition/deepeye/docs/interface.json",
        "competition/deepeye/docs/registers.csv",
        "competition/deepeye/tests/vectors",
        "competition/deepeye/tools/pipeline.py",
    ),
}


class PipelineError(Exception):
    code = "pipeline_error"
    exit_code = 1

    def __init__(self, message, code=None):
        super().__init__(message)
        if code:
            self.code = code


class ContractError(PipelineError):
    code = "contract_mismatch"
    exit_code = 1


class PlanError(PipelineError):
    code = "plan_error"
    exit_code = 2


class NormalizationError(PipelineError):
    code = "invalid_ownership_path"
    exit_code = 2


class ConflictError(PipelineError):
    code = "conflict"
    exit_code = 2


class LedgerError(PipelineError):
    code = "ledger_error"
    exit_code = 1


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def git_command(args, worktree_root=None, timeout=60):
    root = Path(worktree_root) if worktree_root else WORKTREE_ROOT
    try:
        return subprocess.run(
            ["git", "-C", str(root)] + [str(item) for item in args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ConflictError(
            "git is required for provenance checks: %s" % (exc,), code="provenance_git_unavailable"
        )


def parse_evidence_pair(raw, flag):
    text = str(raw)
    if "=" not in text:
        raise ConflictError(
            "--%s evidence must be given as PATH=SHA256: %r" % (flag, raw), code="provenance_pair_invalid"
        )
    path_text, sha_text = text.rsplit("=", 1)
    return path_text, sha_text


def normalize_evidence_pairs(entries, flag):
    normalized = []
    for item in entries or []:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            path_text, sha_text = str(item[0]), str(item[1])
        elif isinstance(item, str):
            path_text, sha_text = parse_evidence_pair(item, flag)
        else:
            raise ConflictError(
                "malformed --%s evidence entry: %r" % (flag, item), code="provenance_pair_invalid"
            )
        normalized.append((path_text, sha_text))
    return normalized


def _evidence_target_within_root(root, relative):
    """Resolve an evidence path under root; reject links, reparse points and escapes."""
    base = Path(root).resolve()
    current = base
    for part in Path(relative).parts:
        current = current / part
        try:
            info = os.lstat(current)
        except OSError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            return None, "uses a link or reparse point"
    target = (base / relative).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None, "escapes the worktree root"
    return target, None


def _validate_evidence_file(kind, path_text, sha_text, commit, root):
    try:
        relative = normalize_owned_path(path_text)
    except (NormalizationError, TypeError) as exc:
        raise ConflictError("unsafe %s path: %s" % (kind, exc), code="provenance_path_unsafe")
    if not isinstance(sha_text, str) or not SHA256_RE.match(sha_text):
        raise ConflictError(
            "%s %r has an invalid recorded SHA256 (need 64 lowercase hex)" % (kind, relative),
            code="provenance_hash_invalid",
        )
    target, unsafe = _evidence_target_within_root(root, relative)
    if unsafe is not None:
        raise ConflictError(
            "unsafe %s path %s: %s" % (kind, relative, unsafe), code="provenance_path_unsafe"
        )
    if not target.is_file():
        raise ConflictError("%s does not exist: %s" % (kind, relative), code="provenance_%s_nonexistent" % kind)
    if sha256_file(target) != sha_text:
        raise ConflictError(
            "%s bytes changed vs recorded SHA256: %s" % (kind, relative), code="provenance_%s_changed" % kind
        )
    tracked = git_command(["cat-file", "-e", "%s:%s" % (commit, relative)], worktree_root=root)
    if tracked.returncode != 0:
        raise ConflictError(
            "%s is not tracked at tested commit %s: %s" % (kind, commit, relative),
            code="provenance_%s_untracked" % kind,
        )
    blob = git_command(["rev-parse", "%s:%s" % (commit, relative)], worktree_root=root).stdout.strip()
    worktree_blob = git_command(["hash-object", "--", relative], worktree_root=root).stdout.strip()
    if not blob or not worktree_blob or worktree_blob != blob:
        raise ConflictError(
            "%s worktree bytes differ from the tested commit blob: %s" % (kind, relative),
            code="provenance_%s_changed" % kind,
        )
    return {"path": relative, "sha256": sha_text}


def validate_acceptance_provenance(artifacts=None, sources=None, commit=None, command=None, exit_code=None,
                                   worktree_root=None):
    """Acceptance needs real bytes plus a tested full Git commit; nothing here is assumed."""
    root = Path(worktree_root) if worktree_root else WORKTREE_ROOT
    artifact_entries = normalize_evidence_pairs(artifacts, "artifact")
    if not artifact_entries:
        raise ConflictError(
            "acceptance requires at least one --artifact PATH=SHA256; metadata-only acceptance is denied",
            code="provenance_missing",
        )
    if not isinstance(commit, str) or not COMMIT_RE.match(commit):
        raise ConflictError(
            "tested source commit must be a full 40-hex git commit: %r" % (commit,),
            code="provenance_commit_invalid",
        )
    resolved = git_command(["rev-parse", "--verify", "%s^{commit}" % commit], worktree_root=root)
    if resolved.returncode != 0:
        raise ConflictError("tested source commit does not exist: %s" % commit, code="provenance_commit_invalid")
    head = git_command(["rev-parse", "HEAD"], worktree_root=root).stdout.strip()
    if head != commit:
        raise ConflictError(
            "tested source commit %s is not the current HEAD %s; commit the tested source before acceptance"
            % (commit, head),
            code="provenance_commit_mismatch",
        )
    validated_artifacts = [
        _validate_evidence_file("artifact", path_text, sha_text, commit, root)
        for path_text, sha_text in artifact_entries
    ]
    source_entries = normalize_evidence_pairs(sources, "source")
    if not source_entries:
        raise ConflictError(
            "acceptance requires at least one --source PATH=SHA256 binding the tested input/source; "
            "an artifact alone is not input/source provenance",
            code="provenance_sources_missing",
        )
    validated_sources = [
        _validate_evidence_file("source", path_text, sha_text, commit, root)
        for path_text, sha_text in source_entries
    ]
    if not isinstance(command, str) or not command.strip():
        raise ConflictError(
            "acceptance requires the explicit exact tested command string", code="provenance_command_invalid"
        )
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise ConflictError(
            "acceptance requires an integer tested command exit code", code="provenance_exit_code_invalid"
        )
    if exit_code != 0:
        raise ConflictError(
            "tested command exit code must be 0 for acceptance, got %r" % (exit_code,),
            code="provenance_exit_code_nonzero",
        )
    return {
        "artifacts": validated_artifacts,
        "sources": validated_sources,
        "commit": commit,
        "command": command,
        "exit_code": exit_code,
        "validated_at": utc_now(),
    }


def check_record_provenance(record, worktree_root=None):
    """Read-only re-validation of an accepted record; returns problem strings, never mutates."""
    root = Path(worktree_root) if worktree_root else WORKTREE_ROOT
    problems = []
    acceptance = record.get("acceptance") or {}
    if acceptance.get("decision") != "accepted":
        return problems
    provenance = acceptance.get("provenance")
    work_id = record.get("work_id")
    if not isinstance(provenance, dict):
        return ["record %r was accepted without provenance" % work_id]
    commit = provenance.get("commit")
    artifacts = provenance.get("artifacts")
    if not isinstance(commit, str) or not COMMIT_RE.match(commit):
        return ["record %r acceptance provenance has no valid tested commit" % work_id]
    if not isinstance(artifacts, list) or not artifacts:
        return ["record %r acceptance provenance has no artifacts" % work_id]
    sources = provenance.get("sources")
    if not isinstance(sources, list) or not sources:
        problems.append("record %r acceptance provenance has no tested source manifest" % work_id)
    command = provenance.get("command")
    if not isinstance(command, str) or not command.strip():
        problems.append("record %r acceptance provenance has no tested command" % work_id)
    exit_code = provenance.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int) or exit_code != 0:
        problems.append("record %r acceptance provenance has no successful tested exit code" % work_id)
    resolved = git_command(["rev-parse", "--verify", "%s^{commit}" % commit], worktree_root=root)
    if resolved.returncode != 0:
        problems.append("record %r accepted commit %s no longer resolves" % (work_id, commit))
        return problems
    for entry in list(artifacts) + list(provenance.get("sources") or []):
        if not isinstance(entry, dict):
            problems.append("record %r has a malformed provenance entry" % work_id)
            continue
        try:
            relative = normalize_owned_path(entry.get("path"))
        except (NormalizationError, TypeError):
            problems.append("record %r provenance path is not safe: %r" % (work_id, entry.get("path")))
            continue
        sha_text = entry.get("sha256")
        if not isinstance(sha_text, str) or not SHA256_RE.match(sha_text):
            problems.append("record %r provenance hash is invalid for %s" % (work_id, relative))
            continue
        target, unsafe = _evidence_target_within_root(root, relative)
        if unsafe is not None:
            problems.append(
                "record %r acceptance provenance path %s: %s" % (work_id, unsafe, relative)
            )
            continue
        if not target.is_file():
            problems.append("record %r acceptance provenance artifact is missing: %s" % (work_id, relative))
            continue
        if sha256_file(target) != sha_text:
            problems.append(
                "record %r acceptance provenance artifact bytes changed: %s" % (work_id, relative)
            )
            continue
        tracked = git_command(["cat-file", "-e", "%s:%s" % (commit, relative)], worktree_root=root)
        if tracked.returncode != 0:
            problems.append(
                "record %r acceptance provenance artifact is not tracked at %s: %s" % (work_id, commit, relative)
            )
            continue
        blob = git_command(["rev-parse", "%s:%s" % (commit, relative)], worktree_root=root).stdout.strip()
        worktree_blob = git_command(["hash-object", "--", relative], worktree_root=root).stdout.strip()
        if not blob or not worktree_blob or worktree_blob != blob:
            problems.append(
                "record %r acceptance provenance artifact differs from the tested commit blob: %s"
                % (work_id, relative)
            )
    return problems


def is_released_record(record):
    """Strict release validity: operator stop plus verified terminal execution.

    A release frees ownership only for a record that still shows a known
    terminal execution (valid verdict and recorded finish time) with a
    compatible status and explicit operator identity/time/evidence. Malformed,
    unknown or active records are never treated as released.
    """
    if not isinstance(record, dict):
        return False
    work_id = record.get("work_id")
    if not isinstance(work_id, str) or not WORK_ID_RE.match(work_id):
        return False
    release = record.get("release")
    if not isinstance(release, dict) or release.get("stop_confirmed") is not True:
        return False
    for field in ("by", "at", "evidence"):
        value = release.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    execution = record.get("execution")
    if not isinstance(execution, dict):
        return False
    finished_at = execution.get("finished_at")
    if not isinstance(finished_at, str) or not finished_at.strip():
        return False
    return record.get("status") in RELEASE_TERMINAL_STATUSES.get(execution.get("verdict"), ())


def verify_scope_contract(scope_path=None):
    path = Path(scope_path) if scope_path else SCOPE_JSON
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ContractError("scope contract file unreadable: %s (%s)" % (path, exc), code="contract_unreadable")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("scope contract file is not valid JSON: %s (%s)" % (path, exc), code="contract_unreadable")
    if data.get("contract_id") != CONTRACT_ID:
        raise ContractError(
            "contract id mismatch: got %r, frozen %r" % (data.get("contract_id"), CONTRACT_ID),
            code="contract_id_mismatch",
        )
    if data.get("revision") != CONTRACT_REVISION:
        raise ContractError(
            "contract revision mismatch: got %r, frozen %r" % (data.get("revision"), CONTRACT_REVISION),
            code="contract_revision_mismatch",
        )
    requirements = data.get("requirements")
    if not isinstance(requirements, list):
        raise ContractError("scope contract has no requirements array", code="contract_requirements_missing")
    digest = sha256_bytes(canonical_bytes(requirements))
    if digest != REQUIREMENTS_SHA256:
        raise ContractError(
            "requirements canonical SHA256 mismatch: got %s, frozen %s" % (digest, REQUIREMENTS_SHA256),
            code="contract_mismatch",
        )
    declared = data.get("requirements_sha256")
    if declared is not None and declared != REQUIREMENTS_SHA256:
        raise ContractError("declared requirements_sha256 mismatch: %r" % (declared,), code="contract_mismatch")
    ids = [item.get("id") for item in requirements if isinstance(item, dict)]
    expected_ids = ["H%02d" % number for number in range(1, 16)]
    if sorted(identifier for identifier in ids if identifier) != expected_ids:
        raise ContractError("H01-H15 must remain intact; found %r" % (ids,), code="contract_requirements_mismatch")
    return {
        "contract_id": data.get("contract_id"),
        "revision": data.get("revision"),
        "task_id": data.get("task_id"),
        "requirements_sha256": digest,
        "requirement_ids": ids,
        "scope_path": str(path),
    }


_BAD_PATH_CHARS = set('<>:"|?*')
_DEVICE_NAMES = {"con", "prn", "aux", "nul"}
_DEVICE_NAMES.update("com%d" % number for number in range(1, 10))
_DEVICE_NAMES.update("lpt%d" % number for number in range(1, 10))


def normalize_owned_path(raw):
    if not isinstance(raw, str):
        raise NormalizationError("ownership path must be a string: %r" % (raw,))
    text = raw.strip()
    if not text:
        raise NormalizationError("ownership path must not be empty")
    if text.startswith("/") or text.startswith("\\") or re.match(r"^[A-Za-z]:", text):
        raise NormalizationError("absolute, drive or UNC ownership paths are denied: %r" % (raw,))
    if "\\" in text:
        raise NormalizationError("backslash aliases are denied: %r" % (raw,))
    segments = []
    for segment in text.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            raise NormalizationError("parent-directory escapes are denied: %r" % (raw,))
        if any(character in _BAD_PATH_CHARS or ord(character) < 32 for character in segment):
            raise NormalizationError("nonportable character in ownership path segment %r" % (segment,))
        if segment[-1] in (" ", "."):
            raise NormalizationError("segment may not end with space or dot: %r" % (segment,))
        stem = segment.split(".")[0].casefold()
        if stem in _DEVICE_NAMES:
            raise NormalizationError("reserved device-name segment is denied: %r" % (segment,))
        segments.append(segment.casefold())
    if not segments:
        raise NormalizationError("ownership path resolves to nothing: %r" % (raw,))
    return "/".join(segments)


def paths_overlap(left, right):
    left = left.strip("/").casefold()
    right = right.strip("/").casefold()
    if not left or not right:
        return False
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")
def load_plan(plan_path=None):
    path = Path(plan_path) if plan_path else PLAN_JSON
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PlanError("plan file unreadable: %s (%s)" % (path, exc), code="plan_unreadable")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanError("plan file is not valid JSON: %s" % (exc,), code="plan_unreadable")
    tasks = data.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise PlanError("plan has no tasks mapping", code="plan_invalid")
    if data.get("task_version") != DESIGN_TASK_VERSION:
        raise PlanError(
            "plan design task_version is %r, frozen %d" % (data.get("task_version"), DESIGN_TASK_VERSION),
            code="design_task_version_mismatch",
        )
    stages = {stage: [] for stage in VALID_STAGES}
    for task_id in sorted(tasks):
        stages.setdefault(tasks[task_id].get("stage"), []).append(task_id)
    return data, tasks, stages


def make_task(stage, cards):
    selected = sorted({str(card) for card in cards})
    if not selected:
        raise PlanError("no cards selected", code="no_cards_selected")
    _, tasks, _ = load_plan()
    for card in selected:
        if card not in tasks:
            raise PlanError("unknown card %r" % card, code="unknown_card")
        if tasks[card].get("stage") != stage:
            raise PlanError(
                "card %r belongs to stage %r, not %r" % (card, tasks[card].get("stage"), stage),
                code="card_not_in_stage",
            )
    owners = sorted({tasks[card].get("owner") for card in selected})
    if len(owners) != 1:
        raise PlanError("mixed-owner card selection is not a bounded reservation", code="mixed_owner_cards")
    return {"stage": stage, "cards": selected, "owner": owners[0], "design_task_version": DESIGN_TASK_VERSION}


def build_inputs(stage, cards):
    scope = verify_scope_contract()
    return {
        "design_task_version": DESIGN_TASK_VERSION,
        "route_task_id": ROUTE_TASK_ID,
        "route_task_version": ROUTE_TASK_VERSION,
        "stage": stage,
        "cards": sorted({str(card) for card in cards}),
        "scope_sha256": scope["requirements_sha256"],
        "plan_sha256": sha256_file(PLAN_JSON),
        "taskbook_sha256": sha256_file(TASKBOOK_MD),
    }


def default_input_hash(stage, cards):
    return sha256_bytes(canonical_bytes(build_inputs(stage, cards)))


def default_claims(stage, cards):
    claims = []
    for card in sorted({str(card) for card in cards}):
        declared = DEFAULT_CLAIMS.get(card)
        if declared:
            claims.extend(declared)
        else:
            claims.append("competition/deepeye/work/%s/%s" % (stage, card.casefold()))
    return claims


@contextlib.contextmanager
def file_lock(lock_path, timeout=60.0):
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+b")
    try:
        if os.name == "nt":
            import msvcrt

            if lock_path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            deadline = time.monotonic() + timeout
            while True:
                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise PipelineError("timed out waiting for ledger lock: %s" % lock_path, code="lock_timeout")
                    time.sleep(0.05)
            try:
                yield
            finally:
                handle.seek(0)
                with contextlib.suppress(OSError):
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise PipelineError("timed out waiting for ledger lock: %s" % lock_path, code="lock_timeout")
                    time.sleep(0.05)
            try:
                yield
            finally:
                with contextlib.suppress(OSError):
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


class Ledger:
    """Durable, process-safe execution ledger for the DeepEye pipeline."""

    SCHEMA = "deepeye.pipeline.ledger.v1"

    def __init__(self, path=DEFAULT_LEDGER):
        self.path = Path(path)

    @property
    def lock_path(self):
        return self.path.with_name(self.path.name + ".lock")

    def empty_document(self):
        return {
            "schema": self.SCHEMA,
            "contract": {
                "id": CONTRACT_ID,
                "revision": CONTRACT_REVISION,
                "requirements_sha256": REQUIREMENTS_SHA256,
            },
            "design_task_version": DESIGN_TASK_VERSION,
            "route_task_id": ROUTE_TASK_ID,
            "route_task_version": ROUTE_TASK_VERSION,
            "records": {},
        }

    def read(self):
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            return self.empty_document()
        except OSError as exc:
            raise LedgerError("ledger unreadable: %s (%s)" % (self.path, exc), code="ledger_unreadable")
        last_error = None
        for _ in range(5):
            try:
                document = json.loads(raw.decode("utf-8"))
                if not isinstance(document, dict) or not isinstance(document.get("records"), dict):
                    raise LedgerError("ledger schema is invalid: %s" % self.path, code="ledger_invalid")
                return document
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(0.05)
                try:
                    raw = self.path.read_bytes()
                except OSError:
                    break
        raise LedgerError("ledger is not valid JSON: %s (%s)" % (self.path, last_error), code="ledger_invalid")

    def write_atomic(self, document):
        parent = self.path.parent
        parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        temporary = self.path.with_name(self.path.name + ".tmp.%d" % os.getpid())
        try:
            with open(temporary, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            with contextlib.suppress(OSError):
                if temporary.exists():
                    temporary.unlink()
        if os.name != "nt":
            try:
                directory_fd = os.open(str(parent), os.O_RDONLY)
            except OSError:
                return
            try:
                os.fsync(directory_fd)
            except OSError:
                pass
            finally:
                os.close(directory_fd)

    def reserve(self, work_id, task, input_hash, ownership):
        if not isinstance(work_id, str) or not WORK_ID_RE.match(work_id):
            raise PlanError("work_id must be a stable id matching %s" % WORK_ID_RE.pattern, code="invalid_work_id")
        if not isinstance(input_hash, str) or not input_hash:
            raise PlanError("input_hash must be a non-empty string", code="invalid_input_hash")
        if not isinstance(task, dict):
            raise PlanError("task must be a mapping", code="invalid_task")
        normalized_ownership = sorted({normalize_owned_path(item) for item in ownership})
        if not normalized_ownership:
            raise NormalizationError("a bounded reservation requires at least one ownership path", code="empty_ownership")
        with file_lock(self.lock_path):
            document = self.read()
            records = document.setdefault("records", {})
            existing = records.get(work_id)
            if existing is not None:
                if existing.get("input_hash") != input_hash:
                    raise ConflictError(
                        "work_id %r is already reserved with a different input hash" % work_id,
                        code="input_hash_conflict",
                    )
                if existing.get("task") != task:
                    raise ConflictError(
                        "work_id %r is already reserved with a different task" % work_id,
                        code="task_conflict",
                    )
                if sorted(existing.get("ownership") or []) != normalized_ownership:
                    raise ConflictError(
                        "work_id %r is already reserved with different ownership" % work_id,
                        code="ownership_conflict",
                    )
                return existing, False
            for other_id, other in records.items():
                if is_released_record(other):
                    continue
                for claimed in normalized_ownership:
                    for held in other.get("ownership") or []:
                        if paths_overlap(claimed, held):
                            raise ConflictError(
                                "ownership overlap: %s claims %s which %s holds" % (work_id, claimed, other_id),
                                code="ownership_overlap",
                            )
            now = utc_now()
            record = {
                "work_id": work_id,
                "task": task,
                "input_hash": input_hash,
                "ownership": normalized_ownership,
                "status": "running",
                "detail": "reserved",
                "attempts": 1,
                "created_at": now,
                "updated_at": now,
                "execution": {"verdict": None, "detail": "", "started_at": now, "finished_at": None},
                "acceptance": None,
                "history": [{"at": now, "event": "reserved"}],
            }
            records[work_id] = record
            self.write_atomic(document)
            return record, True
    def complete(self, work_id, verdict, detail=""):
        if verdict not in ("ok", "failed", "blocked"):
            raise PlanError("verdict must be one of ok/failed/blocked", code="invalid_verdict")
        with file_lock(self.lock_path):
            document = self.read()
            record = (document.get("records") or {}).get(work_id)
            if record is None:
                raise ConflictError("unknown work_id %r" % work_id, code="unknown_work_id")
            if record.get("status") != "running":
                raise ConflictError(
                    "record %r is %r; completion is not allowed" % (work_id, record.get("status")),
                    code="invalid_transition",
                )
            if (record.get("execution") or {}).get("verdict") is not None:
                raise ConflictError(
                    "record %r already has an execution result; it is never replayed" % work_id,
                    code="invalid_transition",
                )
            now = utc_now()
            execution = record.get("execution") or {}
            record["execution"] = {
                "verdict": verdict,
                "detail": detail,
                "started_at": execution.get("started_at", now),
                "finished_at": now,
            }
            if verdict == "ok":
                record["status"] = "running"
                record["detail"] = "execution_ok_pending_main_acceptance"
            else:
                record["status"] = verdict
                record["detail"] = detail or verdict
            record["updated_at"] = now
            record.setdefault("history", []).append(
                {"at": now, "event": "completed", "verdict": verdict, "detail": detail}
            )
            self.write_atomic(document)
            return record

    def accept(self, work_id, decision, by, artifacts=None, sources=None, commit=None,
               command=None, exit_code=None, worktree_root=None):
        if decision not in ("accepted", "rejected"):
            raise PlanError("decision must be accepted or rejected", code="invalid_decision")
        operator = (by or "").strip()
        if not operator or len(operator) > 128:
            raise PlanError("acceptance requires an explicit operator name", code="invalid_operator")
        with file_lock(self.lock_path):
            document = self.read()
            record = (document.get("records") or {}).get(work_id)
            if record is None:
                raise ConflictError("unknown work_id %r" % work_id, code="unknown_work_id")
            execution_verdict = (record.get("execution") or {}).get("verdict")
            now = utc_now()
            provenance = None
            if decision == "accepted":
                if record.get("status") != "running" or execution_verdict != "ok":
                    raise ConflictError(
                        "cannot accept %r: status=%r execution=%r"
                        % (work_id, record.get("status"), execution_verdict),
                        code="invalid_transition",
                    )
                provenance = validate_acceptance_provenance(
                    artifacts=artifacts,
                    sources=sources,
                    commit=commit,
                    command=command,
                    exit_code=exit_code,
                    worktree_root=worktree_root,
                )
                record["status"] = "passed"
                record["detail"] = "accepted_by_" + operator
            else:
                if record.get("status") not in ("running", "blocked"):
                    raise ConflictError(
                        "cannot reject %r from status %r" % (work_id, record.get("status")),
                        code="invalid_transition",
                    )
                record["status"] = "failed"
                record["detail"] = "rejected_by_" + operator
            record["acceptance"] = {"decision": decision, "by": operator, "at": now}
            if provenance is not None:
                record["acceptance"]["provenance"] = provenance
            record["updated_at"] = now
            record.setdefault("history", []).append(
                {"at": now, "event": "acceptance", "decision": decision, "by": operator}
            )
            self.write_atomic(document)
            return record

    def release(self, work_id, by, stop_confirmed, evidence):
        """Explicit operator-confirmed ownership release; never touches the original result."""
        operator = (by or "").strip()
        if not operator or len(operator) > 128:
            raise PlanError("release requires an explicit operator name", code="invalid_operator")
        if stop_confirmed is not True:
            raise ConflictError(
                "release requires an explicit operator stop confirmation", code="release_not_confirmed"
            )
        text = evidence if isinstance(evidence, str) else ""
        if not text.strip():
            raise ConflictError(
                "release requires non-empty evidence binding the verified stop", code="release_evidence_required"
            )
        with file_lock(self.lock_path):
            document = self.read()
            record = (document.get("records") or {}).get(work_id)
            if record is None:
                raise ConflictError("unknown work_id %r" % work_id, code="unknown_work_id")
            status = record.get("status")
            if status not in VALID_STATUSES:
                raise ConflictError(
                    "record %r has unknown status %r; release is refused without mutation" % (work_id, status),
                    code="unknown_status_no_release",
                )
            execution = record.get("execution") or {}
            verdict = execution.get("verdict")
            if verdict not in ("ok", "failed", "blocked"):
                if status == "running" and verdict is None:
                    raise ConflictError(
                        "record %r is active with no terminal execution result; it is never released" % (work_id,),
                        code="active_operation_no_release",
                    )
                raise ConflictError(
                    "record %r has status %r without a verified terminal execution result" % (work_id, status),
                    code="unverified_terminal_no_release",
                )
            finished_at = execution.get("finished_at")
            if not isinstance(finished_at, str) or not finished_at.strip():
                raise ConflictError(
                    "record %r has no recorded terminal execution finish time; release needs a confirmed stop"
                    % (work_id,),
                    code="unverified_terminal_no_release",
                )
            if status not in RELEASE_TERMINAL_STATUSES[verdict]:
                raise ConflictError(
                    "record %r status %r is not compatible with terminal execution %r; release is refused"
                    % (work_id, status, verdict),
                    code="unverified_terminal_no_release",
                )
            existing = record.get("release")
            if existing is not None:
                if (
                    existing.get("stop_confirmed") is True
                    and existing.get("by") == operator
                    and existing.get("evidence") == text
                ):
                    return record
                raise ConflictError("record %r already has a different release" % work_id, code="already_released")
            now = utc_now()
            record["release"] = {
                "by": operator,
                "at": now,
                "stop_confirmed": True,
                "evidence": text,
            }
            record.setdefault("history", []).append(
                {"at": now, "event": "released", "by": operator, "evidence": text}
            )
            record["updated_at"] = now
            self.write_atomic(document)
            return record

    def audit(self):
        document = self.read()
        items = []
        for work_id in sorted(document.get("records") or {}):
            record = document["records"][work_id]
            status = record.get("status")
            execution_verdict = (record.get("execution") or {}).get("verdict")
            if status in ("passed", "not_run"):
                continue
            if status == "running" and execution_verdict == "ok":
                kind = "awaiting_main_acceptance"
                decision = "quality main must accept or reject the recorded execution result"
            elif status == "running":
                kind = "in_flight_never_replayed"
                decision = "reconcile with the original operation receipt; never auto re-execute"
            elif status == "failed":
                kind = "failed_no_replay"
                decision = "failure retained; main decision required before any new task version"
            elif status == "blocked":
                kind = "blocked_no_replay"
                decision = "implementation missing or main override required; never auto re-execute"
            else:
                kind = "unknown_status"
                decision = "main decision required; ledger is left untouched"
            items.append(
                {
                    "work_id": work_id,
                    "status": status,
                    "released": is_released_record(record),
                    "kind": kind,
                    "required_decision": decision,
                    "task": record.get("task"),
                    "ownership": record.get("ownership"),
                }
            )
        return {
            "ledger": str(self.path),
            "ledger_exists": self.path.exists(),
            "action_required": bool(items),
            "items": items,
        }

    def status_view(self):
        document = self.read()
        counts = {status: 0 for status in VALID_STATUSES}
        counts["unknown"] = 0
        summaries = {}
        for work_id, record in sorted((document.get("records") or {}).items()):
            status = record.get("status")
            counts[status if status in counts else "unknown"] += 1
            summaries[work_id] = {
                "status": status,
                "released": is_released_record(record),
                "detail": record.get("detail"),
                "task": record.get("task"),
                "input_hash": record.get("input_hash"),
                "ownership": record.get("ownership"),
                "attempts": record.get("attempts"),
                "updated_at": record.get("updated_at"),
            }
        return {
            "ledger": str(self.path),
            "ledger_exists": self.path.exists(),
            "counts": counts,
            "records": summaries,
        }


def emit(document):
    print(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True))


def emit_error(exc):
    print(
        json.dumps(
            {
                "error": str(exc),
                "code": getattr(exc, "code", "pipeline_error"),
                **ROUTE_FIELDS,
                "design_task_version": DESIGN_TASK_VERSION,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        file=sys.stderr,
    )


def cmd_plan(args):
    data, tasks, stages = load_plan()
    view = {}
    for stage in sorted(stages):
        card_ids = stages[stage]
        view[stage] = {
            "cards": card_ids,
            "owners": sorted({tasks[card].get("owner") for card in card_ids}) if card_ids else [],
            "details": {
                card: {
                    "owner": tasks[card].get("owner"),
                    "dependencies": tasks[card].get("dependencies"),
                    "status_plan": tasks[card].get("status"),
                }
                for card in card_ids
            },
            "note": "no_cards_in_plan" if not card_ids else "",
        }
    emit(
        {
            "command": "plan",
            **ROUTE_FIELDS,
            "design_task_version": DESIGN_TASK_VERSION,
            "task_version": data.get("task_version"),
            "entrypoint": data.get("entrypoint"),
            "cards_total": len(tasks),
            "stages": view,
            "implemented_cards": sorted(RUNNERS),
            "read_only": True,
        }
    )
    return 0


def cmd_status(args):
    ledger = Ledger(args.ledger)
    view = ledger.status_view()
    emit({"command": "status", **ROUTE_FIELDS, "design_task_version": DESIGN_TASK_VERSION, "read_only": True, **view})
    return 0


def cmd_resume(args):
    ledger = Ledger(args.ledger)
    audit = ledger.audit()
    emit({"command": "resume", **ROUTE_FIELDS, "design_task_version": DESIGN_TASK_VERSION, "read_only": True, **audit})
    return 3 if audit["action_required"] else 0


def cmd_accept(args):
    verify_scope_contract(args.scope)
    ledger = Ledger(args.ledger)
    record = ledger.accept(
        args.work_id,
        args.decision,
        args.by,
        artifacts=args.artifact,
        sources=args.source,
        commit=args.commit,
        command=args.tested_command,
        exit_code=args.exit_code,
    )
    emit(
        {
            "command": "accept",
            **ROUTE_FIELDS,
            "design_task_version": DESIGN_TASK_VERSION,
            "record": record,
        }
    )
    return 0


def cmd_release(args):
    ledger = Ledger(args.ledger)
    record = ledger.release(args.work_id, args.by, args.stop_confirmed, args.evidence)
    emit(
        {
            "command": "release",
            **ROUTE_FIELDS,
            "design_task_version": DESIGN_TASK_VERSION,
            "release_is_separate_from_execution_and_acceptance": True,
            "record": record,
        }
    )
    return 0


def cmd_run(args):
    verify_scope_contract(args.scope)
    if args.task_version != DESIGN_TASK_VERSION:
        raise PlanError(
            "design task version must be %d, got %r (execution route fields are separate)"
            % (DESIGN_TASK_VERSION, args.task_version),
            code="design_task_version_mismatch",
        )
    stage = args.stage
    if stage not in VALID_STAGES:
        raise PlanError("unknown stage %r (expected %s)" % (stage, ", ".join(VALID_STAGES)), code="unknown_stage")
    _, tasks, stages = load_plan()
    selected = [card.strip() for card in (args.card or []) if card.strip()]
    if selected:
        for card in selected:
            if card not in tasks:
                raise PlanError("unknown card %r" % card, code="unknown_card")
            if tasks[card].get("stage") != stage:
                raise PlanError(
                    "card %r belongs to stage %r, not %r" % (card, tasks[card].get("stage"), stage),
                    code="card_not_in_stage",
                )
    else:
        selected = list(stages.get(stage, []))
        if not selected:
            raise PlanError(
                "stage %r has no cards in the plan; choose a bounded card explicitly" % stage,
                code="stage_has_no_cards",
            )
    work_id = (args.work_id or "").strip()
    if not WORK_ID_RE.match(work_id):
        raise PlanError("work_id must match %s" % WORK_ID_RE.pattern, code="invalid_work_id")
    task = make_task(stage, selected)
    claims = list(args.ownership) if args.ownership else default_claims(stage, selected)
    input_hash = args.input_hash or default_input_hash(stage, selected)
    ledger = Ledger(args.ledger)
    record, created = ledger.reserve(work_id, task, input_hash, claims)
    result = {"created": created, "reused": not created}
    if created:
        missing = [card for card in task["cards"] if card not in RUNNERS]
        if missing:
            record = ledger.complete(work_id, "blocked", "implementation_missing:" + ",".join(sorted(missing)))
        else:
            try:
                notes = [str(RUNNERS[card](task=task, work_id=work_id, ledger=ledger)) for card in task["cards"]]
                record = ledger.complete(work_id, "ok", "; ".join(note for note in notes if note) or "executed")
            except Exception as exc:  # runner failures are retained, never replayed
                record = ledger.complete(work_id, "failed", "runner_error:%s:%s" % (type(exc).__name__, exc))
    emit(
        {
            "command": "run",
            **ROUTE_FIELDS,
            "design_task_version": DESIGN_TASK_VERSION,
            "stage": stage,
            "cards": task["cards"],
            "work_id": work_id,
            "status": record.get("status"),
            "detail": record.get("detail"),
            "record": record,
            **result,
        }
    )
    return 0


def run_selftest():
    test_file = DEEPEYE_DIR / "tests" / "test_pipeline.py"
    if not test_file.is_file():
        raise PipelineError("selftest file missing: %s" % test_file, code="selftest_missing")
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["DEEPEYE_SELFTEST_DEPTH"] = str(int(environment.get("DEEPEYE_SELFTEST_DEPTH", "0") or "0") + 1)
    command = [sys.executable, "-X", "utf8", "-B", str(test_file), "-v"]
    completed = subprocess.run(
        command,
        cwd=str(DEEPEYE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=environment,
        timeout=1800,
    )
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace") if completed.stderr else ""
    match = re.search(r"Ran (\d+) tests?", stdout + "\n" + stderr)
    tests_ran = int(match.group(1)) if match else 0
    ok = completed.returncode == 0 and tests_ran > 0 and re.search(r"^OK\b", stdout, re.MULTILINE) is not None
    return {
        "command": command,
        "returncode": completed.returncode,
        "tests_ran": tests_ran,
        "ok": bool(ok),
        "stdout_tail": "\n".join(stdout.splitlines()[-30:]),
        "stderr_tail": "\n".join(stderr.splitlines()[-10:]),
    }


def cmd_verify(args):
    scope = verify_scope_contract(args.scope)
    result = {
        "command": "verify",
        **ROUTE_FIELDS,
        "design_task_version": DESIGN_TASK_VERSION,
        "contract": scope,
        "checks": [],
    }
    _, tasks, _ = load_plan()
    result["checks"].append({"check": "plan_loaded", "ok": True, "cards_total": len(tasks)})
    ledger = Ledger(args.ledger)
    exit_code = 0
    if ledger.path.exists():
        document = ledger.read()
        records = document.get("records") or {}
        problems = []
        unknown_statuses = []
        entries = sorted(records.items())
        for work_id, record in entries:
            status = record.get("status")
            if status not in VALID_STATUSES:
                unknown_statuses.append(work_id)
            if not WORK_ID_RE.match(str(work_id)):
                problems.append("record %r has an unstable work id" % work_id)
            try:
                normalized = [normalize_owned_path(item) for item in record.get("ownership") or []]
            except NormalizationError:
                problems.append("record %r has non-normalizable ownership" % work_id)
                normalized = []
            if normalized != sorted(record.get("ownership") or []):
                problems.append("record %r ownership is not canonical" % work_id)
            if record.get("release") is not None and not is_released_record(record):
                problems.append("record %r has an invalid release record" % work_id)
            problems.extend(check_record_provenance(record))
        for index, (work_id, record) in enumerate(entries):
            if is_released_record(record):
                continue
            for other_id, other in entries[index + 1:]:
                if is_released_record(other):
                    continue
                for claimed in record.get("ownership") or []:
                    for held in other.get("ownership") or []:
                        if paths_overlap(claimed, held):
                            problems.append("records %r and %r have overlapping ownership" % (work_id, other_id))
        result["checks"].append(
            {
                "check": "ledger",
                "ok": not problems,
                "exists": True,
                "records": len(records),
                "problems": problems,
                "unknown_statuses": unknown_statuses,
            }
        )
        if problems:
            raise LedgerError("ledger invariant problems: %s" % "; ".join(problems), code="ledger_invariant_failed")
        if unknown_statuses:
            exit_code = 3
    else:
        result["checks"].append({"check": "ledger", "ok": True, "exists": False})
    if args.selftest:
        result["selftest"] = run_selftest()
        emit(result)
        return 0 if result["selftest"]["ok"] else 1
    result["action_required"] = bool(exit_code)
    emit(result)
    return exit_code


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python tools/pipeline.py",
        description="DeepEye bounded software pipeline (R03 foundation). Statuses: %s." % ", ".join(VALID_STATUSES),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plan", help="read-only stage/card view; never writes or creates directories")
    status = subparsers.add_parser("status", help="read-only ledger view; never writes or creates directories")
    status.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    run = subparsers.add_parser("run", help="bounded reservation for explicitly chosen known cards")
    run.add_argument("--stage", required=True)
    run.add_argument("--task-version", required=True, type=int, dest="task_version")
    run.add_argument("--work-id", required=True, dest="work_id")
    run.add_argument("--card", action="append", default=[], help="repeatable; known plan cards only")
    run.add_argument("--ownership", action="append", default=[], help="repeatable normalized claim path")
    run.add_argument("--input-hash", default=None, dest="input_hash")
    run.add_argument("--scope", default=None, help="contract file override (must still hash to the frozen value)")
    run.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    verify = subparsers.add_parser("verify", help="recompute contract hash and ledger invariants")
    verify.add_argument("--selftest", action="store_true", help="run the real unit suite tests/test_pipeline.py")
    verify.add_argument("--scope", default=None)
    verify.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    resume = subparsers.add_parser("resume", help="read-only audit returning the required main decision")
    resume.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    accept = subparsers.add_parser("accept", help="record the explicit quality-main decision")
    accept.add_argument("--work-id", required=True, dest="work_id")
    accept.add_argument("--decision", required=True, choices=["accepted", "rejected"])
    accept.add_argument("--by", required=True)
    accept.add_argument("--artifact", action="append", default=[],
                        help="repeatable PATH=SHA256 of an existing artifact; bytes must match and be tracked at the tested commit")
    accept.add_argument("--source", action="append", default=[], dest="source",
                        help="repeatable PATH=SHA256 of tested source files bound to the tested commit")
    accept.add_argument("--commit", default=None,
                        help="tested full 40-hex git source commit; must be the current HEAD")
    accept.add_argument("--command", default=None, dest="tested_command",
                        help="optional tested command string")
    accept.add_argument("--exit-code", default=None, type=int, dest="exit_code",
                        help="optional tested command exit code")
    accept.add_argument("--scope", default=None)
    accept.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    release = subparsers.add_parser(
        "release",
        help="explicit operator-confirmed stop releasing ownership of a known-stopped operation",
    )
    release.add_argument("--work-id", required=True, dest="work_id")
    release.add_argument("--by", required=True, help="explicit operator/main identity")
    release.add_argument("--stop-confirmed", action="store_true", dest="stop_confirmed",
                         help="required: explicit confirmation that the operation is actually stopped")
    release.add_argument("--evidence", required=True, help="required non-empty evidence binding the verified stop")
    release.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            return cmd_plan(args)
        if args.command == "status":
            return cmd_status(args)
        if args.command == "run":
            return cmd_run(args)
        if args.command == "verify":
            return cmd_verify(args)
        if args.command == "resume":
            return cmd_resume(args)
        if args.command == "accept":
            return cmd_accept(args)
        if args.command == "release":
            return cmd_release(args)
    except PipelineError as exc:
        emit_error(exc)
        return exc.exit_code
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except Exception as exc:  # defensive: no silent traceback, no partial state claim
        print(
            json.dumps(
                {"error": "%s: %s" % (type(exc).__name__, exc), "code": "internal_error", **ROUTE_FIELDS},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    raise PlanError("unknown command %r" % (args.command,), code="unknown_command")


if __name__ == "__main__":
    sys.exit(main())

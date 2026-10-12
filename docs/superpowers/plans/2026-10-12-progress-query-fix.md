# Progress query implementation plan

**Goal:** Pure progress queries leave execution and priority intact and report evidence.
**Architecture:** Dedicated status_query ingress; immediate Controller callback;
read-only ledger snapshot with persistent report dedupe and a CLI status action.
**Tech stack:** Python asyncio, sqlite3, unittest; existing dependencies only.

## Constraints and ownership

Follow ../specs/2026-10-12-progress-query-design.md. Quality main owns design and
acceptance; Flash only supplies factual read-only inventory. All writes are in
.local/progress-query-fix-20261012, on codex/a/progress-query-fix-20261012.
Additional minimal control-plane paths store.py, sessions.py, progress.py and
evidence/progress-query-fix-20261012 are explicitly included in this plan.

## Tasks

- [x] Trace ingress -> accept/version callback -> cancel -> gateway ledger -> report.
- [x] Check child ownership, create ignored isolated worktree, review written spec.
- [ ] Baseline: `python -m unittest discover -s tests -q`; preserve output.
- [ ] RED: tests/test_progress_query.py constructs blocked gateway, offers the
  original query, asserts `active.cancelling() == 0` and unchanged version callback.
  Run `python -m unittest discover -s tests -p test_progress_query.py -v`.
- [ ] GREEN: protocol full-match helper and dedicated kind; normalize before
  accept_inbound, handle status immediately and before pause in run_until_idle.
  Track active message until finally; preserve all existing cancellation rules.
- [ ] Snapshot: add store.inbound_progress() including delayed rows and
  sessions.run_summaries(); progress module reconciles them with active dispatch.
  Runtime.progress_snapshot()/status callback and ProjectActions `status` expose it.
- [ ] Expand tests: full/routed/mention/compound grammar, duplicate and pause,
  no claims/versions/inference, actual AppServerGateway with blocked provider,
  failed/interrupted/stale running/unknown/queued and original no-replay behavior.
- [ ] Run relevant regression modules, then full unittest discovery and diff check.
- [ ] Main code/requirements review, evidence commands and hashes, commit/push/PR.
- [ ] Verify remote SHA; one feedback session_open to B-git-handoff v1 with exact
  paths, tests, commit and undeployed state; one final group report if useful.

## Next step

Capture baseline and failing behavioral reproduction before production edits.

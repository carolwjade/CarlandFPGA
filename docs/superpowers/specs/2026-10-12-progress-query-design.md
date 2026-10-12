# Read-only progress queries

Task: MESH-20261011-132845-c94f2686-A-progress-query-fix v1
Owner: Astra-A; work_id: A-progress-query-fix-20261012-v1.
Base: 920ab35. Branch: codex/a/progress-query-fix-20261012.

## Evidence and root cause

FeishuIngress.ingest and HumanMessageRouter.ingest classify human text as an
instruction. SQLiteStore.accept_inbound advances human_task_versions for that
kind; Controller.offer invokes the child-version callback and cancels an active
gateway task for every human message. Runtime._on_result reports model text.
AppServerGateway persists cancellation as interrupted and refuses to replay the
same failed/interrupted message. Thus a question can destroy useful work and a
subsequent model response can misstate progress. pending_inbound excludes retry
backoff rows, so its length alone is not a queue count.

## Options and main decision

1. Selected: strict query classification before persistence, immediate local
   snapshot callback, plus authenticated CLI status. Covers the original phrase
   and bypasses version updates, claims, cancellation and model inference.
2. Cancel-condition-only change: rejected because queries would still mutate
   versions, acquire ownership and wait for/start inference.
3. CLI-only status: useful supplementary entry, insufficient for the original
   group query. No LLM classification or model polling is permitted.

## Contract

Accept only the full trimmed text `/fpga status` or `当前工作进度`, optionally
preceded by existing `/fpga A|B|C`, `Astra-A|B|C:` routing or recognized Feishu bot
mentions. Use known mention metadata to remove platform placeholder prefixes.
Extra words, punctuation, attachments or compound stop/change requests remain
instructions. Normal target routing remains in force; unaddressed queries report
each receiving node's local status and require no shared ownership claim.

Normalize direct Controller.offer human instructions too, before accept_inbound.
Persist the query as status_query for dedupe and crash recovery, without changing
task versions. Only query inbox/reply delivery bookkeeping may be written.
Handle accepted queries immediately even while busy or paused; process persisted
status_query entries before pause/claim/model dispatch on recovery. Existing old
instruction rows and failed/interrupted work are never reclassified or replayed.
Keep callback failure in the inbox with bounded existing backoff.

The snapshot reads live controller active identity/cancellation flag, all pending
inbox rows including backoff, main run ledger summaries, and child ledger status.
Include UTC snapshot time and node, pause state, controller dispatch state,
cumulative main counts and recent rows with running/queued/failed/interrupted/
completed/unknown separated. A ledger running row without matching live dispatch
is unknown. A queued ledger row without a pending inbox entry is unknown. Terminal
records are preserved. Child counts are explicitly ledger observations, not live
process proof. Completion percentage and remote/board progress are unknown.
No result text, prompts, credentials or arbitrary errors enter the public report.

Use one durable report operation per query dedupe identity; delivery retries use
the existing sender. CLI `status` returns the same snapshot without a group post,
model catalog lookup, thread creation or any task write.

## Ownership and scope

At start: child ledger had no nonterminal assignment; base checkout had only
unrelated ab-outage-test-temp. This owner writes only in its isolated worktree.
Production paths: controller.py, protocol.py, feishu.py, feishu_channel.py,
runtime.py, project_control.py, plus store.py and sessions.py for small read-only
summary methods. New fpga_mesh/progress.py holds snapshot/report logic. Tests:
tests/test_progress_query.py; existing relevant tests only if needed. Documents:
this spec, task plan, OPERATIONS.md, evidence/progress-query-fix-20261012/.
Flash assignment is read-only test/API inventory, with no file ownership.
No B handoffs, outage directory, configuration, resident services or board writes.

## Verification and delivery

Use real Controller, FeishuIngress, SQLiteStore, NodeRuntime and AppServerGateway
with a deterministically blocked local fake provider. Observe baseline RED, then
GREEN: query does not cancel, original completes, only one model turn starts;
new instructions/pause still interrupt; compounds stay instructions; duplicates
are idempotent; pause survives status and restart; failed/interrupted/unknown and
backoff queues report truthfully. Keep regression/full-suite commands and hashes.
These are local integration facts, not deployed or three-machine acceptance.
Publish reviewed branch/PR and exact remote SHA. Deployment is deferred to round
owner using existing idle fence after outage work; never stop/restart services here.

## Main self-review

Approved by quality main under the explicit autonomous repair instruction.
Checked: anchored grammar, no substring bypass, no task-version/claim/model query
path, persistent dedupe, conservative unknowns, no automatic replay, isolated
ownership, and deployment separation. Human reconfirmation is not needed for
the authorized reversible repair. No unresolved design placeholders.

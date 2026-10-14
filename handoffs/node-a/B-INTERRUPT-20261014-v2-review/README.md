# A review of B-INTERRUPT-20261014 v2

The scoped software review passes at PR #18 head `8afeaed96c28730466bb353317bdc9a479c3b50c`. **A deployment is NOT_RUN: the existing idle preflight refuses because active/pending work remains.** No Stop/restart, live source replacement, historical replay, merge or hardware operation was attempted.

- Original operation: `B-INTERRUPT-20261014:group-continuity-v2`
- Request hash: `d855848bdaafc76fb4d3bc0f0662ed5dc2672120d089ea7621f8f986ab40abb0`
- Actual tested commit: `8afeaed96c28730466bb353317bdc9a479c3b50c`
- Source commit: `fea98eefed3a1c6d085d492f6dd6ba155d95e3de`, confirmed ancestor of the tested head
- Original manifest: `handoffs/node-b/B-INTERRUPT-20261014-v2/manifest.json`
- A feedback operation: `B-INTERRUPT-20261014:A:review-v2`

## Measured evidence

The project handoff verifier passed all 16 manifest entries. A separately recomputed canonical request hash, file lengths/SHA-256, and exact equality with Git blobs; all matched. See `readiness.json`.

The manifest's seven-module unittest command ran in the isolated PR worktree with Python 3.12.14 and exited 0: **96 tests passed in 7.798 seconds**. DeepSeek performed the bounded execution; A main independently checked module location, report/head, raw log hashes, count, request hashes and repository changes. See `software-regression.json` and the original stdout/stderr bytes.

B's saved runtime-copy log reports 98 tests. Its two additional tests are `test_default_sdk_import_owns_loop_separate_from_controller` and `test_injected_factory_does_not_load_optional_sdk`; they are absent from this PR head's `tests/test_feishu_channel.py`. There is also a runtime test-name difference: B has `test_peer_presence_changes_stay_internal_without_model_turn`, while the PR has `test_peer_presence_changes_queue_human_status_without_model_turn`. This is a scope difference, not a claim that A reproduced B's entire runtime or 98 tests. Any later adoption must preserve A's existing quiet-presence policy and other local patches by reviewing only the intended controller change. The original unclosed-event-loop ResourceWarning remains visible in both logs; no live Feishu SDK acceptance is claimed.

## Main review

Reviewed the controller diff together with store admission, runtime child-version callback, session recovery and gateway cancellation behavior. No blocking defect was found within the stated continuity scope:

- Ordinary human instructions and revisions remain durable while the active gateway runs; version updates are deferred while `_active_message` is set, including result delivery.
- At the next turn boundary, the controller rereads the queue so pending human work precedes peer work; unstarted superseded human revisions retain the existing skip rule.
- Effective explicit STOP still records cancellation provenance. Expired/stale STOP and RESUME do not cancel ordinary active work.
- The gateway's durable failed/interrupted guard is unchanged; queuing does not authorize replay or bypass ownership.

The documented limit remains: desktop-only children without an active resident main turn are outside `_active_message` protection. Unit tests do not prove live ingress, real model behavior, or A service adoption.

## Deployment boundary

The A read-only `assert_idle` check raised `node has active or pending work; finish or explicitly resolve it before updating`. Snapshot counts and the unchanged active controller hash are in `readiness.json`; these are observations at its recorded time, not a permanent status.

Leave the original controller, task definition, credentials, configuration, ledgers, hardware setting and planning gates in place. A later authorized idle maintenance window must revalidate the PR head and existing local bytes, use the existing `stop_idle_node` writer fence through confirmed shutdown, preserve all local state, and record actual installed bytes/runtime evidence separately. This review neither schedules a restart nor grants merge approval. C deployment is not evaluated. Synthesis, implementation, RTL simulation and board stages are NOT_RUN.

Formal sender readback of the matching PR feedback is a separate handoff step; peer transport ACK alone is not that readback.

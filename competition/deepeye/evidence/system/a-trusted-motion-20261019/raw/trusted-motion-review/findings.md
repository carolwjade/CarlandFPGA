# Trusted owned motion executor: independent review

**Repair request TM-R1: a later authority passage materialization exception does not stop the executor or retire further movement.** The exact candidate passes the author's 135-test baseline and seven of eight new independent methods. The remaining method fails on this missing failure latch; a separate continuation witness demonstrates another commit with the same BOOT and command after the fault. Main retains classification, repair and acceptance decisions. This is not candidate approval.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-trusted-motion-review-20261019-v1`; native job `child-34daa654230745abb8816e0b9baad365`; reviewer `/root/pc_direct_review_20261018`. Original A Desktop generation 2 remains sole director. The new job was authenticated with execution_allowed=true before project work. Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15, canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` independently recomputed unchanged in ROOT and PRODUCT.

## Exact byte binding

Author report SHA256 `a8e18ad0fb4c880b1c659c8731734378e1feb4c97965b367d9e0cab7b0e7b6db` and receipt SHA256 `1deafc745e2041f811bb7c962395358e90b8972fb11d057ffb39407f4fc6a92b` matched the assignment. Every entry in author's final manifest matched current bytes and was snapshotted into this review's `frozen/`: **35 total relevant files, comprising four owned candidate files and 31 other inputs/dependencies**. No whole-checkout clean claim is made; unrelated isolation repair is disjoint.

| Candidate path, relative to competition/deepeye | SHA256 |
| --- | --- |
| simulation/authority/motion_executor.py | f38b28ead8b5f2564301b007bcd6b57df08bdd9d99a9859390669a41b065dabc |
| simulation/authority/motion/passage_phase.py | 19ba2644db3b9bf3e78af7dddc896ee2e5ebea1cc6363b936aea5110928df6fe |
| tests/simulation/test_motion_executor.py | 05f527da19263330e0f5855f94fdc584898d8021813966eb7ef992c5b6f070aa |
| docs/motion_executor.md | 6a75bd53e7059a18a2d3fe0760b4833891094d2f402f07c2693c6ec49007beb3 |

The pre-author passage snapshot matched SHA256 `28c948f63ba9010bc48a89f5472faa70a18887733284b1f5b0fcb03c65bc07cc`. Independently comparing AST nodes established that the entire pre-existing module prefix, including preview, remains unchanged; relative records/helpers are appended. No prior geometry or runtime acceptance was promoted to acceptance of this executor.

## TM-R1: audit-time materialization can fail while movement remains active

Location: `simulation/authority/motion_executor.py:188–194`, `OwnedMotionExecutor.passage_state`. It calls `materialize_committed_transition` directly and propagates failures. Unlike mutation transactions protected by `_entry` at lines 109–121, this later authority materialization path does not call `_revoke` (line 201), set stopped or retire pending state.

Minimal test uses the real executor and geometry with the author's explicitly numerical fixtures:

1. Activate the fixture BOOT, admit its original command, prepare and successfully commit one complete 10 ms step.
2. On a later authority `passage_state()` access, inject `MemoryError` only at `materialize_committed_transition` to represent failed allocation/materialization. Observe the exception; do not alter the store, prepared objects or any private field.
3. Pose revision remains 1, as required for already committed motion, but `controller_view()` still reports `stopped=False`, `trial_failed=False`.
4. Remove the temporary fault. Without new BOOT or command admission, another normal prepare/commit succeeds: pose revision 2, interval [1,020,000,000, 1,030,000,000], same BOOT identity and command sequence.

`test_later_materialization_failure_latches_stop_without_new_motion` fails the explicit stopped assertion. `materialization_continuation.py` separately records the actual second commit in `continuation.stdout.log`; that script exits 0 because observation succeeded, **not because safety passed**. No source/BOOT authentication is forged, no frozen object is forcibly mutated, and no production provider is required for this local failure boundary.

This contradicts the assigned later-materialization fail-latch requirement and the chosen conservative stop-on-rejection policy. It does **not** establish a collision, false arrival or movement during the failed access; those were not observed. The problem is implicit recovery of movement after an authority materialization failure without retirement/reauthorization. A failure while preparing a later step does stop via `_entry`, but the same failure during standalone authority access currently does not.

Proposed repair for the author/main: catch materialization/validation/allocation errors at the authority access boundary, preserve the already published pose/frame and prior proof/history, revoke pending/future motion before propagating, and apply the selected fresh-BOOT recovery policy. An unknown computational failure should not automatically become a proved geometric violation or permanent collision trial latch. Add regressions for both authority access and later prepare, with a retained pending handle, and require no subsequent commit under the old admission. Do not roll back or replay the already committed step. Exact recovery/latch policy is main's decision.

## Fresh tests and finite positive observations

Interpreter for every subprocess: ROOT `.local/venv/Scripts/python.exe -B -X utf8`, cwd PRODUCT. PYTHONPATH was product plus process-local `.local/deepeye-host-deps`; TEMP/TMP under this evidence directory. Exact commands/environment/exits are in `author-command.json`, `independent-command.json`, `continuation-command.json`; raw stdout/stderr are preserved.

| Run | Actual result |
| --- | --- |
| Author selected suite, once | 135 passed, exit 0; 22 executor + 113 prior tests |
| Fresh independent suite | 8 methods: 7 passed / 1 failed, exit 1 |
| Fault continuation observer | exit 0, records active state and subsequent same-admission commit |

The seven passing independent methods establish these specific boundaries at tested fixture bytes:

- Successful post-fence suffix calls no CanonicalPath, materialization, digest, scene certification, SHA256 or dataclass replace. Guards were installed on those actual dependencies; publication succeeds and the final callback count is exactly one. This verifies call placement, not wall-clock execution cost or a 10 ms guarantee.
- Delayed second interval preserves all prior event values and the untouched original anchor proof, while publishing actual end time 1,310,000,000. Waiting does not cause additional integration.
- A superseded pending handle cannot reach the fence; rejection also prevents its newer sibling from subsequently publishing under the stopped root.
- Equal-but-distinct BOOT, bool identities/timestamps, wrong duration, original-deadline extension, deadline equality and pre-issue interval are rejected, with one callback at most and no pose publication/repeat effect.
- World invalidation inside the callback prevents movement, preserves pose and cannot restart by a new BOOT on the retired world.
- Existing committed history and trial-failure latch survive STOP and a new BOOT. Overlapping actual intervals cannot publish a second pose.

Source inspection confirms one identity-consumed prepared handle, root identity comparison, original raw-command binding, full canonical duration, all workspace slices and every solid-scene slice before publication, and error/capsule margin forwarding. The author baseline exercises thin later-slice obstruction/no safe prefix, scene completeness/forbidden union, full-body blue-entry/red-exit role, inherited speed/uncertainty carry, strict original deadlines and real-runtime fixture integration. These are bounded software/numerical observations; this review does not claim a new exhaustive geometric theorem or new provider authentication.

No new contradiction was found in the successful final-fence suffix or relative mapping on valid histories. Exact private authority records/scene assertions, frozen dataclasses and hashes remain non-authenticating. Malicious authority reflection, genuine source/clock/AI provider implementation, live renderer/material behavior and measured asset containment are separate boundaries; none was invented as a blocker for this increment.

## Scope and next action

Main was promptly given the failure location, raw test and continuation outcome. Reviewer made no source repair. Resolve TM-R1 under new author ownership and re-review the repaired exact bytes before promoting this executor. Preserve this RED result and the existing author failures/history.

All reviewer writes are under `.planning/deepeye-resume-20261018/trusted-motion-review/`; original evidence and all product/dependency bytes are read-only. No Run activation, live OS process/fixture, service, isolation profile, hardware/board, credentials, external feedback, Git mutation or additional agent occurred. All 29 formal cards, actual AI/clock/source authentication, both live control chains, renderer visibility and full game/runtime/board acceptance remain **not_run**.

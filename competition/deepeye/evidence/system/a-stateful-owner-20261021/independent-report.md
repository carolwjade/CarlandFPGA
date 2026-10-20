# PC_DIRECT stateful owner independent review

Work `A-R03-STATEFUL-OWNER-INDEPENDENT-20261021-v1`; original job
`child-2c35d0e9ff2342cf9ec2be5f3732c179`; reviewer
`/root/r02_static_dependency_review_20261020`.

The bounded source review and eight new adversarial controls found no functional
counterexample at the five assigned product hashes. One low severity evidence
wording issue is recorded below. This is independent software review evidence
for main's acceptance decision; production activation, R03, full H12 and all29
remain `not_run`.

H01–H15 canonical requirements SHA256 remains
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
The active transfer remains generation 2. No product file was changed; no real
AI actor, production provider, GUI/input, network, vendor/model/driver, service,
board, Git or additional agent operation was performed. The test subprocesses
were hidden, below normal priority and confined to the owned JobObject.

## Finding R03-SOI-01 — original RED does not separately record a numeric commit

Severity: P3, evidence precision; no new product malfunction reproduced.

Location: original author's
`executions/red-original-v3/source-snapshots/red_controls.py:15`, corresponding
`test-result.json` failure trace, and author `report.md` RED description.
The old control computes `committed = False if refused else self.step().committed`
but only asserts `refused and not committed`. Its failed assertion proves that
the required combined refusal/no-commit condition was not satisfied. That false
condition permits both an unrefused command with a failed step and an unrefused
command with a successful step. The saved failure receipt does not separately
serialize those two local values or the pose revision. Its assertion message
therefore cannot by itself establish the author's stronger statement that this
particular old run numerically committed motion.

This limitation is reproducible by inspecting that immutable assertion and its
saved trace; no original run was replayed. Keep both genuine RED failures and
the stronger numeric-commit wording qualified unless another original saved
observation establishes it. The missing original completion entry is separately
directly asserted. Final successful tests and the new positive real-CAS control
are independent of that historical wording. No product fix is proposed here.

## Original identity and evidence verification

`audit_inputs.py` recomputed all 1,184 public author file hashes and lengths
against manifest SHA256
`9547bd821046dd4a349b75df099009022f2b77bbf86b7b335b2a937baa0bae0f`.
It independently read the original author native completion as
`completed / terminal=true / exact_result=true`.
All five current product files match the pinned assignment and frozen author
copies. `source-pins.json` records this review's exact bounded source inputs.
Seventeen unowned selected-design source inputs retain their original hashes,
including runtime, numerical executor, mailbox, HIL, actor/native sources and
schema/profile inputs. This review did not repeat a repository-wide ownership
audit or attribute other workers' files.

The original ten created process runs have ten actual terminal receipts and
30 original held-handle records, all `wait_result=0 / signaled=true`.
Eight receipts give final active process count zero. Two exit125 quota races
omit that numeric field: their original assigned-process exception path sets
`all_processes_terminated` only after empty-job plus held-handle termination.
The omitted count remains absent. The 55-second prelaunch refusal created no
process; it is outside these ten runs.

Original result distinctions verified from each run's own receipt/results:

| Attempt | Result retained |
|---|---|
| red-original-v2, composition-integration-v1 | exit125, incomplete executions; no test pass/product failure inferred |
| red-original-v3 | two assertion failures, no errors; evidence limit above |
| red-stateful-v1 | 22 fixture setup errors; not product RED |
| red-stateful-v2 | 22 tests: one failure, 20 errors, one pass |
| green-stateful-v1 | 22 tests: 20 activation errors, two passes; placeholder BOOT fixture corrected |
| green-stateful-v2 | 22/22, exit0 |
| composition-integration-v2 | 74/74, exit0 |
| final-focused-v1 | 31/31, exit0 |
| runtime-executor-v1 | 91/91, exit0 |

These runs overlap and are not summed. The current production files and old
composition test file match the 74-test snapshot. Its 22-test candidate suite
differs from final 25 by exactly three added provider tests; removing only those
methods gives identical full AST. All final five files match focused/runtime
snapshots, and their recorded product imports match current bytes. The earlier
failures, wrapper KeyError and static-audit version mismatch remain intact.

The local author runner callback catches only `FileNotFoundError` with a fresh
absence check, conservatively counts disappeared entries and preserves link,
reparse, nonregular and hardlink refusal. Permission/recreation failures
propagate. Its native runner and boundary bytes remain pinned. Only current-run
quota scope and owned write scope were used; retained temporary fixture files
remain quota-bounded. This is sampled filesystem accounting, not an atomic
snapshot or an OS isolation proof. The two interrupted original scans are not
retroactively repaired or recounted as success.

## Forty-five old test methods and ten migrations

Independent AST comparison retained every one of the 45 original method names;
35 method ASTs are identical. Shared fixture changes are explicit: canonical
frozen BOOT digest, established synthetic origin 0, legal initial time 210ms,
synthetic zero transfer bounds, original completion event before broker command,
and removal of the legacy command lookup.

| Changed method suffix | Reviewed change and retained boundary |
|---|---|
| changed_duplicate_invocation_is_rejected_without_new_freshness | Conflicting original completion is now submitted as its own event; refusal/no pose retained |
| unrelated_new_completion_does_not_extend_old_command | A legitimate new pending result is allowed; old duplicate keeps original bound and expires at original deadline |
| missing_original_completion_rejects_alive_actor | Missing mandatory completion callback output still rejects a live actor |
| broker_stop_needs_no_inference_completion | Completion sentinel must not be called for STOP |
| original_completion_lookup_time_cannot_refresh_initial_deadline | Delay original event verifier across fixed initial deadline; require no bound/no pose |
| revoke_during_original_wait_cannot_restore_progress | Proof retrieval moved to bounded last_completion fixture; original Wait/revocation checks unchanged |
| private_proof_identity_bounds_and_model_are_not_caller_claims | Same retrieval migration; identity/bounds/model checks retained |
| time_addition_overflow_never_produces_progress | Same retrieval migration; checked-addition assertions retained |
| new_completed_candidate_advances_bound_and_commits | Explicit 750ms fixture policy and two intermediate heartbeats cross a real 500ms slot; original progression/commit assertions retained |
| old_command_replay_cannot_replace_new_completion | Same explicit next-window fixture; old replay still refuses without replacing bound |

The two next-window fixture ages do not change product defaults. The default
100ms and existing 5ms deadline controls remain, including an explicit 5ms
policy rejection when waiting for the next 500ms slot. New independent controls
below cover both changed duplicate bytes and unchanged duplicate expiry with a
separately pending newer result.

## Source-supported authority and state boundaries

Paths below are relative to product `competition/deepeye/`.

| Boundary | Source and independent conclusion |
|---|---|
| Original proof | `candidate_owner.py:102` checks exact proof/BOOT/source/clock/model, strict integers and original ordered completion interval; checked original lower+age. Moved proof fields/decorator match old definition. Objects are correlation, never authentication. |
| Pending/current state | `candidate_owner.py:127–162`: one pending proof and one committed association. Mailbox retains its own one completed high-water and four observations. No unbounded completion dictionary; transient owner transaction clears in entry finally and retirement. |
| Observation tap | `actor_composition.py:247,476`: same verified record after runtime succeeds; no second verifier or tap after partial runtime failure. |
| Slot/time/veto | `actor_composition.py:254–278,488`: refresh owner time after verifiers, preserve callback veto epoch, pass that actual time to exact-current-slot consumption. No nominal-slot substitution. |
| Irreversible consume | `candidate_owner.py:133–151` and mailbox consume: consume original selected bytes/invocation; `_ProgressGate` further verifies complete command/candidate association. Failed downstream admission retires without reinsertion. |
| Duplicate | `candidate_owner.py:127,153` reuses only exact committed request bytes and original proof object; unchanged ProgressGate checks fixed original metadata/deadline. A newer pending completion cannot refresh current authority. |
| Association commit | `actor_composition.py:498–516`: both real runtime and real executor admission precede current association commit; exceptions/veto clear tentative and retained proof state. |
| STOP ordering | `actor_composition.py:373–384`: owner veto, transaction/proof clearing and mailbox stop precede runtime/executor cleanup callbacks. Nonmotion STOP never asks completion/slot providers. Foreign thread only signals veto; owner performs authority/native cleanup. |
| Original lifetime | `actor_composition.py:280–302`: original actor is the sole lease target; minimum with original progress deadline. No source lease/boolean fallback. |
| Final deadline/CAS | Unchanged runtime step and executor `motion_executor.py:325–359`: real final callback, exact command/root identities, strict full-step end<deadline, one root publication, no new work between callback and CAS. |
| Production gate | `actor_composition.py:162,548`: raises before registry construction/acquisition. No new public provider/actor injection or factory activation. |

Six important authority ASTs independently match the baseline: `_ProgressGate`,
`_Dependencies.ai_lease`, `prepare_step`, `commit_step`, `_production_channels`
and `create_authority`. Real authentication, original actor invocation ledger,
conservative source-clock mapping, BOOT slot origin/transfer measurements and
current-window scheduler verification remain missing production dependencies.
The strict point-time rule has no demonstrated real scheduling guarantee.
Topology1 refuses this PC_DIRECT adapter; HIL original request/capture authority
remains a separate mandatory path.

## Eight new independent controls

`independent_controls.py` imports the existing fixture setup only. The explicit
eight method names in `control-01/started.json` prevent inherited suites from
being rerun. Real mailbox, ProgressGate, runtime, actor lifetime/cleanup and
numerical executor/CAS execute. Synthetic seams are upstream opaque records,
owner time and the fake native API. No mock grants final motion authority.

| Control | Observed result |
|---|---|
| Exact old duplicate with newer pending, then stale receipt | No consume; pending/current original identities retained; old fixed deadline retires and clears both |
| Changed same command sequence with newer pending | Cannot adopt new proof or commit; permanently retires |
| Caught malformed reentry during slot verifier | Proof/transaction cleared and mailbox stopped before runtime-stop callback observes state |
| Foreign STOP during completion verifier | No foreign native effects; owner veto clears pending/current and prevents motion |
| Real runtime admission then injected refusal | Slot consumed but no association committed/reinserted; runtime/executor stopped |
| Real executor admission then caught STOP | No association installed despite provider swallowing reentry exception |
| One-ns native probe cost inside final callback, full-step equality | Actual time refreshed; no CAS at end==original progress deadline |
| Same final native probe, end one ns inside | Real numeric CAS succeeds, pose revision1 |

Actual result: 8/8, no failures/errors/skips/prohibited attempts, exit0;
test body0.854s, owned tree1.625s, active process count0, all three held process
objects signaled. No test was repeated after success. The reviewed v6 scanner
runner was copied byte-identical (`80cc41fd…77d`) with original native/termination
mechanics; boundary `04cf7d53…040fe`. Limits stayed 50s, 512MiB job, 256MiB
process, four processes, 2MiB per output, 64MiB/3000-entry tree, 10GiB reserve.
The worker audit adds the second `os.startfile/2` refusal; no startfile call ran.

All recorded import/read hashes were checked again after termination, and
source pins remain unchanged. Five loaded cached code objects were additionally
compared with compilation of their exact source; `-B` alone was not treated as
proof of cache bypass. Full receipts, imports and code/source checks are in
`final-verification.json`. Review and final authority checks establish bounded
software evidence only. Main owns acceptance/publication; no production gate or
formal task status is advanced by this report.

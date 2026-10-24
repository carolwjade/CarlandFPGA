# R03 stateful original-completion owner — implementation evidence

Work `A-R03-STATEFUL-OWNER-IMPLEMENTATION-20261020-v1`; original job
`child-b4ad57212b1943f09f34fab01700abde`; agent `/root/r02_recipe_fix_20261020`.
The main-selected private PC_DIRECT connection is implemented in exactly the
five assigned product paths. This is software implementation evidence awaiting
main's independent review. The production factory remains closed; original
completion, BOOT schedule/transfer and slot providers remain absent.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 canonical requirements
SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
and active director generation 2 are preserved. R03/full H12/all29 remain
`not_run`. No Git, UI, board, service, vendor/model execution, production actor
acquisition, provider installation, network/peer operation or additional agent
was used.

## Scope and immutable inputs

The main supplied source baseline commit
`26aa83e68d89c41da456459df852406b8957e1a6`; Git was not invoked to establish
or alter it. Before implementation, `baseline.json` pinned 7,325 product files,
the three existing owned files, all 20 selected-design source inputs, the
10 design artifacts and the active contract/transfer. The design manifest is
`422732203312366c206e54d3496ebfbe864b5cc3122a69bdcbd29e8e147ca92d`.

The final ownership audit found exactly three changed existing files and two
new files. All 7,322 existing unowned product files are byte-identical, including
the four C dirty files, runtime, executor, mailbox/HIL sources and vectors,
actor native boundary, BOOT/schema/ABI and frozen profile. There are 29
additional files in main's explicitly authorized
`evidence/control/a-b-op17-review-20261021/` directory. Their hashes are recorded
as main-owned additions, not this worker's changes. `__pycache__` is excluded
consistently with the original baseline; tests ran with `-B`.

Full before/after bytes and unified diffs are under `baseline/`,
`product-after/` and `diffs/`. Product paths below are relative to
`.local/deepeye-implementation-a/competition/deepeye/`.

| Product path | Final SHA256 |
|---|---|
| `simulation/authority/candidate_owner.py` | `07f68aacc3a4fd5738cd557402cb6990771b483183889c7da7470125d3fea59d` |
| `simulation/authority/actor_composition.py` | `06ad811d1395b5a24c3b5886e17e35e74ec57397278e60edc70d3d36278381ec` |
| `tests/simulation/test_candidate_owner.py` | `a5b093b924450e1915f468bd930ec7df8fd6b524c9972242490b7bef8489f391` |
| `tests/simulation/test_actor_composition.py` | `cc113aa09ecff3909b0379e66748fdd7f40f2dcce314ff5479e5a482c4b622ce` |
| `docs/actor_composition.md` | `4b10270fcbfd48607094742ed09d1c404283fd82dcfd796d00f85848aa1d0ede` |

## Concrete behavior and unchanged authority

`_CandidateOwner` retains one pending original `_CompletedInference`, one
committed command/proof association and no completion dictionary. Its transient
observation/command transaction is cleared on owner exit and retirement.
The proof's fields and frozen decorator are identical to the old definition;
only its module moved, with the private composition import alias retained.
These records remain correlation containers, not credentials.

Activation requires exact original BOOT/source/clock identities, established
slot origin and explicit conservative transfer bounds. The adapter uses the
existing mailbox and frozen profile digest. It refuses topology 1; it does not
create HIL actuation/capture evidence or replace that separately required path.

After the original runtime admits an observation, its same single verified
record is offered to the mailbox. No second observation verifier runs. A partial
runtime admission failure prevents that tap and retires the composition.
`accept_completion` invokes the original event verifier before command
selection. Source/clock/BOOT/model, strict bounded integers, original causal
ordering and checked `completion_lower + progress_max_age` are required.
An ignored old/duplicate completion cannot replace pending state or requeue a
consumed result. Arrival never renews the initial/current progress deadline.

For new motion, original broker verification precedes original slot verification.
The owner refreshes actual time after each verifier and checks the same veto
epoch. Mailbox consumption uses the exact current legal slot; returning one
nanosecond late refuses. No nominal timestamp, equality change or synthetic
jitter tolerance is used. The retained original proof passes to the existing
progress gate. Selection is irreversible, while the committed association is
installed only after both runtime and executor admission succeed.

An exact current command duplicate uses its original committed association,
without another consume, completion callback, slot or renewal. Changed bytes
or a newly numbered command using an already consumed proposal refuse.
STOP bypasses completion/slot prerequisites. Retirement clears pending/current
proof before authority/cleanup callbacks; caught reentry or foreign STOP
cannot restore admission. There is no reset/reactivation path for the old owner.
A later veto still preserves an already observed positive CAS outcome.

`semantic-guards.json` proves AST equality of `_ProgressGate`,
`_Dependencies.ai_lease`, `prepare_step`, `commit_step`,
`_production_channels` and `create_authority`. The original actor remains the
only lifetime target. Runtime/executor files are byte-identical: original
freshness, geometry, strict full-step deadline and final callback/root CAS are
unchanged. No operation was inserted between that final callback and CAS.
Neither production module contains `completion_for_command`.

## RED, GREEN and exact test versions

The original broker-only counterexample actually admitted and numerically
committed a command with no preceding original completion event. Its separate
missing-entry control also failed. These are the two genuine
`red-original-v3` failures. The subsequent new-suite RED had 1 failure and
20 errors caused by absent required activation/entry/state; topology refusal
already passed. Fixture/harness errors below are kept distinct from this RED.

Final successful runs use the real mailbox, runtime, numerical executor and
actor ownership/cleanup code with explicitly synthetic upstream events, native
API and monotonic time. No permissive mock supplies final motion authority.

| Run | Actual result | Exact composition |
|---|---|---|
| `green-stateful-v2` | 22/22, exit 0 | Initial focused owner tests |
| `composition-integration-v2` | 74/74, exit 0 | 45 existing composition + 22 owner + 5 initial quota controls + 2 original RED controls |
| `final-focused-v1` | 31/31, exit 0 | All 25 final owner + all 6 final quota controls |
| `runtime-executor-v1` | 91/91, exit 0 | 64 existing runtime + 27 existing executor |

These are overlapping runs and are not summed as a unique test count.
All complete test results report no skipped tests and no intercepted prohibited
attempts. Exact argument arrays, budgets, stdout/stderr, test outcomes,
import/read hashes and source snapshots are retained per run.

Commands used the common executable/prefix:

```text
.local/venv/Scripts/python.exe -I -S -B -X utf8
.planning/deepeye-resume-20261018/r03-stateful-owner-implementation-20261020/run_tests.py
```

The final group arguments were:

```text
composition-integration-v2
  test_tree_observer.TreeObserverTests
  competition.deepeye.tests.simulation.test_actor_composition.ActorCompositionTests
  competition.deepeye.tests.simulation.test_candidate_owner.CandidateOwnerTests
  red_controls.RedTests.test_command_must_not_invent_completion_after_command
  red_controls.RedTests.test_original_completion_owner_entry_required

final-focused-v1
  test_tree_observer.TreeObserverTests
  competition.deepeye.tests.simulation.test_candidate_owner.CandidateOwnerTests

runtime-executor-v1
  competition.deepeye.tests.simulation.test_pc_direct_runtime.PcDirectRuntimeTests
  competition.deepeye.tests.simulation.test_motion_executor.MotionExecutorTests
```

`tested-version-map.json` proves current production sources and the existing
composition test file exactly match the 74-test run, and all five current files
and current harness match the final focused/runtime snapshots. The earlier
22-test owner file differs only by three added provider test methods; removing
those exact methods makes the entire AST identical. They are retained in
`diffs/owner-tests-22-to-25.diff` and all 25 passed in the later focused run.
No successful test was repeated during sealing.

The 25 owner tests cover the six selected scenario groups: opposite completion
order and exact original proof; late completion/broker/slot verifiers; caught
reentry, foreign STOP and fresh BOOT; duplicate identity and bounded history;
strict selection/full-dt equality versus one nanosecond inside; absent/wrong
providers, records, identities, model, mode and overflow. They also exercise
partial runtime/executor admission, single observation verification and the
closed production factory before acquisition.

## Explicit existing-test migrations

All 45 original test method names remain. Thirty-five methods have identical
ASTs. The shared fixture now verifies the real frozen profile digest and begins
at a deterministic legal 210 ms slot with established origin 0 and synthetic
zero transfer cost. Its completion event is emitted before broker command
creation; the old dictionary/command-to-completion lookup is removed.
This fixture supplies no real timing, transport, scheduler or authentication
evidence.

The ten changed methods are explicitly accounted for below; full source diff
contains every assertion.

| Existing method suffix | Migration and preserved obligation |
|---|---|
| `changed_duplicate_invocation_is_rejected_without_new_freshness` | Alter the original completion verifier result and offer that event; changed invocation still revokes with no pose |
| `unrelated_new_completion_does_not_extend_old_command` | A legitimate unrelated completion may be pending; exact current duplicate reuses old proof; old bound is identical and its original deadline still refuses motion |
| `missing_original_completion_rejects_alive_actor` | Missing result now comes from `verify_completion`; alive actor cannot bypass it |
| `broker_stop_needs_no_inference_completion` | Completion verifier is an assertion-raising sentinel; STOP never calls it |
| `original_completion_lookup_time_cannot_refresh_initial_deadline` | Historical name retained; delay the completion verifier across the fixed initial deadline and require no admitted bound or pose |
| `revoke_during_original_wait_cannot_restore_progress` | Retrieve the same synthetic proof from bounded `last_completion`; original Wait/revoke assertions unchanged |
| `private_proof_identity_bounds_and_model_are_not_caller_claims` | Same proof retrieval migration; original adversarial assertions unchanged |
| `time_addition_overflow_never_produces_progress` | Same proof retrieval migration; overflow assertions unchanged |
| `new_completed_candidate_advances_bound_and_commits` | Actually reach next 500 ms window using explicit 750 ms age and two intermediate 250 ms STATE8 heartbeats; original monotonic bound/commit assertions remain |
| `old_command_replay_cannot_replace_new_completion` | Same next-window timing fixture; old command still refuses and cannot replace current bound |

The default age remains 100 ms, and original 5 ms boundary tests retain that
policy. A separate new control rejects waiting 500 ms under a 5 ms policy.
The broker-only RED control explicitly bypasses the new convenience fixture
which would otherwise emit a completion; its no-original-event scenario is
unchanged. No production budget or deadline was tuned.

## Retained failures and bounded runner correction

| Attempt | Preserved result and handling |
|---|---|
| `red-original-v1` | Requested 55 s exceeded the reviewed maximum; no process created. Changed to the original 50 s limit |
| `red-original-v2` | Directory deletion raced original quota enumeration; exit 125, incomplete test. All three held handles signaled |
| First dispatch of `red-original-v3` | Wrapper expected absent numeric `active_processes_final` in the prior exception receipt; KeyError before a new tree. Wrapper now checks the pinned exception termination path without fabricating a numeric field |
| `red-original-v3` | Two genuine preimplementation failures, preserved |
| `red-stateful-v1` | 22 setup errors from unbound `setUp`/`super` misuse; explicit fixture setup corrected. Not counted as product RED |
| `red-stateful-v2` | 1 failure, 20 errors, 1 pass against old composition; preserved |
| `green-stateful-v1` | 20 activation errors, 2 negative controls passed; synthetic placeholder BOOT digest corrected to the real frozen profile digest |
| `composition-integration-v1` | Second transient path deletion race, exit 125, incomplete tests; three held handles signaled. Partial stderr also identified the next-window heartbeat fixture error, corrected with intermediate heartbeats |
| Initial static seal audit | Overly broad version-equality assertion compared earlier 22 tests with final 25. Failure and successful exact three-method continuation are both saved; no product change or rerun |

Only this task's local `tree_observer.py` replaces the quota measure callback.
The reviewed immutable `win_job.py`
(`127daf70b2aa6cf3e7a299978596766fc310d191d13f6a2165626f719889052d`)
and `boundary.py`
(`dc27aea6104424fbb2ee9109bb5e2adaf90684161e9d43bd2636b5ea4d6f2908`)
are unchanged. Process creation, suspended assignment, owned JobObject,
termination and held-handle checks are the original implementation.

The local observer catches only `FileNotFoundError` and continues only if the
enumerated/queued path is still absent. Recreated paths and permission errors
propagate. Link/reparse, nonregular and hardlink checks remain. Vanished
enumerated entries still count against the scan cap. The six independent stdlib
controls use real temporary file/directory deletions, an actual recreated path,
permission denial and synthetic hardlink/reparse metadata; all six passed.
`diffs/measure_tree.diff` gives the exact callback change.

The limits remain 50 s, 512 MiB job/256 MiB process, 4 processes, 2 MiB each
output stream, 64 MiB tree, 3,000 entries and 10 GiB free reserve. The worker
open-write audit and watched quota root are both the current run directory.
Fixture TemporaryDirectory files are retained as bounded evidence; native actor
cleanup is unchanged. Earlier runs and failure traces are not deleted.
No code or result was inherited from the separately assigned R02 quota repair.

Ten actual process runs have terminal receipts; each retains all three original
held-process observations with `wait_result=0` and `signaled=true`. Successful
and test-failure receipts also give final active count 0. The two exception
receipts omit that numeric field; their pinned assigned-process path returns
`all_processes_terminated` only after `HeldMembers.wait_terminated` observes
an empty job and all held handles signaled. Both even retain an intermediate
empty-job/pending-handle observation. They are not treated as terminated merely
from process-list emptiness or an exit code. Prior closure was checked before
every fresh run ID.

## Handoff artifacts and limits

`ownership-audit.json`, `source-pins.json`, `semantic-guards.json`,
`execution-audit.json`, `tested-version-map.json`, `harness-corrections.json`,
`static-audit-initial-result.json` and `static-audit-completion.json` bind the
claims above to exact bytes and outcomes. `artifact-manifest.json` indexes all
public task artifacts; `seal-result.json` binds that manifest, final result and
five product hashes. Private lease/reservation files and the later native
completion receipt are explicitly outside the precompletion public manifest.

The library is ready for independent software review. Real authenticated event,
source-clock, BOOT/transfer and slot providers are still missing; the strict
point-time mailbox rule remains an unproven real scheduling obligation. No
provider fallback, actual product activation, H11 usefulness, complete H12 path
or all29 acceptance is claimed. Main owns publication and acceptance. After the
original native job is completed once and its persisted exact result is read
back, this worker stops all writes.

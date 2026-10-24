# Independent PC_DIRECT authority-adapter review

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-PC-DIRECT-RUNTIME-INDEPENDENT-20261018-v1`; job `child-708a40fa80674499a5a65ef2b582a804`; agent `/root/r03_review_20261018`. Sole director `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. H01-H15 canonical requirements SHA256 verified as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. All product files and prior evidence remained read-only; only this report directory was written.

**Conclusion: one actionable BOOT-transaction veto-loss defect is reproduced by two independent cases. Do not treat the adapter as ready for activation until this is repaired and independently checked.** The source delivery otherwise has useful bounded evidence, with explicit trusted-provider/executor obligations. This review is not full PC_DIRECT, C05/G06/H12, physical motion, authentication, AI-process or board acceptance.

## PCR-R1: in-flight BOOT erases a newly raised STOP/reentrant-event latch

Location: `simulation/authority/pc_direct_runtime.py`, `boot()` activation, especially lines 231-257; interaction with `_event` at 203 and `_trip` at 178.

`boot(event)` enters an event transaction, calls the trusted `verify_boot`, then constructs its new watchdog and unconditionally assigns `_latched=False`. It does not check whether a STOP or validation error was raised during that same verification. Because the runtime begins latched already, a check of the boolean alone would also be insufficient to distinguish an old recovery condition from a new STOP.

Two deterministic repros are in `adversarial_runtime.py`:

1. A normal fixture BOOT verifier returns the same valid immutable binding but first calls the public `owner.stop('operator STOP during BOOT verification')`. The subsequent outer BOOT clears that STOP. Normal valid STATE8, observation and broker command then lead to `step(...).committed=True` and one fixture pose-update count.
2. While verifying that BOOT, a nested `owner.board(None)` call is correctly rejected by `_event`'s reentrancy guard and latches STOP. The verifier catches the nested ValueError and returns the valid BOOT binding. The outer BOOT again clears the new latch, and normal subsequent inputs produce a successful fixture commit.

Both assertions expecting no commit fail. `independent_results.json` records `committed:true`, `reason:trusted_executor_receipt`, `fixture_commits:1` for each. This is one root cause with two triggering events, not two unrelated defects.

The fixture still performs the actual schema/CRC/watchdog validation and a normal single-use final fence. It does not forge a commit receipt, omit the fence, fabricate a new liveness mechanism, mutate runtime private fields or require a malicious executor. The concrete boundary is the public STOP/invalid-event semantics during a synchronous dependency verifier. The code/documentation promise that validation errors latch and explicit STOP cannot restore motion without a new verified BOOT. The same in-progress BOOT must not absorb a STOP/error raised inside itself as though it occurred before that handshake.

Suggested repair boundary for the main: distinguish the recovery latch that existed before BOOT from new veto events during the BOOT transaction (for example, a monotonically changing STOP/error generation checked before activation). A fresh, separate verified handshake may recover; the in-flight activation that observed the veto must remain stopped. Preserve these two RED cases and add behavioral regressions. Final implementation/acceptance belongs to the main.

This is an adapter-level unsafe acceptance/fixture receipt, **not measured physical movement**. The production executor and actual verifier are still missing, and this review does not claim the current viewer moved.

## Fresh test evidence

| Suite | Actual child result |
|---|---|
| Current author runtime suite | 44 tests passed, exit 0 |
| Independent counterexamples | 8 tests: 6 passed, 2 failed, 0 errors, exit 1 |

Passing independent cases add coverage for:

* Explicit STOP delivered during AI verification in command admission remains latched.
* Replaying an **exact** observation envelope does not renew its original native sample age. With a later fresh heartbeat and command, the final nanosecond ending at the original FAST age cap can commit, while starting at the cap cannot.
* A saved successful final-fence closure cannot be reused after the synchronous executor returns; the reuse latches and subsequent execution stops.
* Suppressing a failed final-fence exception and returning a receipt without a successful fence cannot be accepted.
* Evicted last-four observation identities cannot be restored by replay.
* Catching a rejected reentrant event during geometry preparation cannot bypass the final veto.

Exact argv/cwd/environment/child exit codes are in `commands.json`; complete stdout/stderr are separate raw logs. The driver exits 0 after recording results; that is not the independent suite's exit code. No failed assertion was weakened or hidden.

The previously passed watchdog40/STATE8-heartbeat5/host-envelope34 dependency evidence is reused as authorized, not rerun. Author receipt and every owned/direct-dependency hash match actual bytes (`author_delivery_match.json`); final source snapshots establish this review's scoped stability. No old test count is relabeled a newly executed suite.

## Other reviewed boundaries and their limits

* **Trust boundary:** `AuthorityDependencies` has no permissive provider. BOOT/channel/observation/command records are explicitly verifier results, not credentials. Real channel authentication, original FPGA quality/time/source provenance, C candidate correlation, actual AI process identity/lifetime and geometry/executor correctness are appropriately declared future trusted implementations. Their absence alone is not reported as a defect in a bounded adapter.
* **Original lifetime/replay:** current code caps command lifetime by original issue+duration and original conservative sample+FAST1500ms/STRESS12000ms; identical active command retries retain the earlier deadline. Changed, expired, superseded or wrapped identities reject. The observation ledger keeps four originals and a nonwrapping high-water sequence; eviction and age are checked again before execution.
* **BOOT/context:** run/generation/session/context/AI-instance checks, unused-session requirement and ordinary BOOT invalidation are covered by the author tests. The new defect is specifically veto changes *during* BOOT activation; it does not negate those existing checks.
* **STATE8 dispatch:** only STATE8 refreshes watchdog health. Other structurally valid responses do not create observations/capture or renew heartbeat, and declared fault/rejected fields stop. A healthy heartbeat alone cannot invoke the executor.
* **AI/final fence:** current identity-bound AI leases are rechecked before preparation, after preparation and inside the final fence. Expiry, death, identity change and caught reentrant errors outside the BOOT exception above stop. A production provider must independently measure actual process state rather than returning the fixture's deterministic records.
* **Single CAS:** single-use callback, failed-attempt consumption, synchronous callback closure, exact receipt/revision checks and committed-interval high-water behavior have actual fixture evidence. The executor contract must still bind prepared geometry and perform one atomic pose CAS immediately after the fence; this adapter cannot undo or independently authenticate a malicious trusted executor's unreported side effects.

`docs/pc_direct_runtime.md` generally states the preview/fixture/provider/activation boundaries accurately. Its broad STOP/reentrant-error claim is currently contradicted by PCR-R1 and should only be treated as the intended invariant until fixed. The adapter is not linked to an active viewer, actual board receiver or real AI supervisor by this delivery. H01-H15, both H12 topologies and all 29 formal cards remain unchanged/not_run; no default ledger or acceptance status was written.

## Release

Scope source/test/doc and direct-dependency hashes matched author delivery and remained unchanged. Review commands finished, no subprocess or product write is pending. This new independent review job is completed with the truthful reproduced finding; repair ownership and final acceptance return to the main.

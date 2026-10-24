# Independent PCR-R1 generation-fence post-fix review

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-PC-RUNTIME-BOOT-VETO-REVIEW-20261018-v1`; job `child-93e51e026ac1430cacc0ebaa5dbea6ac`; agent `/root/r03_review_20261018`. Sole director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. H01-H15 pinned canonical SHA256 verified as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Sources and index remained read-only.

**Original PCR-R1 counterexamples now pass, but two additional BOOT transaction gaps remain. This candidate is not yet clear for adapter activation.** Neither finding depends on forged receipts or an executor bypassing its final fence. All commits below are deterministic fixture counter increments, not measured physical motion.

## What the repair fixes

The exact original independent eight-case probe was imported without executing its `__main__`; all eight methods passed freshly under this reviewer. Original source/evidence files were not overwritten. The public BOOT-entry veto generation, pre-activation comparison, repeated-STOP counting and first-observed-watchdog-latch tracking fix the original operator-STOP and caught board-reentry cases. The author adds nine tests to its original44; its recorded final53 pass against exactly the current frozen source/test hashes. Those53 were not unnecessarily rerun here. Unchanged79 dependency checks remain reused evidence.

## PCR-R2: malformed step reentry escapes the generation fence while idle

`step()` validates `expected_pose_revision` and `dt_ns` before checking `_busy/_stepping`. When an already booted healthy runtime is idle with no command, a verifier's nested `step(dt_ns=0)` or `step(expected_pose_revision=False,dt_ns=1)` fails at `_integer` before reaching the explicit reentrancy veto. Its exception path trips only if a command exists or the runtime was already latched. Neither condition holds in this state, so the nested call returns a stopped result **without changing veto generation**.

The outer higher-generation/new-session BOOT then activates. With ordinary valid STATE8, observation and broker command, the subsequent step returns `committed=True` and the fixture count is1. Both independent cases reproduce this. The original exact valid-argument recursive-step regression does not cover validation failure before the busy check.

This contradicts the transaction's documented recursive-step/rejected-input veto invariant. A bounded fix should make the reentrant-call veto unconditional with respect to malformed arguments and prior command/latch state. The main chooses the implementation. Preserve both RED cases rather than exempting malformed reentrant calls.

## PCR-R3: activation exception leaves an independently verified proposal replayable

The BOOT verifier returns a structurally valid binding, but the subsequent activation `_advance()` calls a clock hook that raises ValueError. This throws before the proposed session/generation is retired. `_event` correctly trips STOP, yet the same BOOT binding can be replayed on the next call after removing that one failing clock hook; it activates and ordinary valid inputs yield a committed fixture count of1.

The new documentation says a verified proposal invalidated during the transaction is retired and cannot itself clear STOP; recovery requires a different unused session and higher generation. A clock-callback failure is a new invalid-event veto after verification, but the current retirement point does not cover it. The fix must retain the distinction between a never-verified proposal and a valid verified proposal whose later activation fails. Avoid replaying the latter as fresh recovery. Final repair/acceptance remains main-owned.

## New evidence and successful recovery

Fresh commands:

| Probe group | Actual child result |
|---|---|
| Exact original independent8 | 8 passed, exit0 |
| Four new BOOT boundary cases | 1 passed, 3 failed, 0 errors, exit1 |

The passing new case exercises a **newly discovered** old watchdog timeout at BOOT entry: the first proposal aborts, replay remains rejected, and a separate higher-generation/different-session BOOT recovers and commits once. Thus the report distinguishes false revival from legitimate fresh recovery; it does not demand permanent STOP after any prior fault.

`new_probe_results.json` records two malformed-reentry cases and one post-verification activation-error replay, each with `committed:true`/fixture count1. `probes.py` contains exact standalone counterexamples; raw stderr preserves the three failed assertions. `commands.json` records exact argv, cwd, environment and actual child exits. The recording driver exits0 after collecting both results; that is not the failing child suite's exit.

## Exact bytes and prospective Git blob equivalence

The three current source/test/doc SHA256 values match `pc-runtime-boot-fix/receipt.json` and its frozen author delivery. All direct dependencies match the same frozen record and remain unchanged around this review. `source_before.json`, `source_after.json` and `source_final.json` bind those bytes.

`git_blob_byte_equivalence.json` records effective text/eol/filter/encoding attributes and read-only Git hash-object checks. All three files already contain LF only. Their raw blob OIDs equal `git hash-object --path=... --stdin` clean-filter OIDs, so repository normalization would not change these reviewed bytes. The command used no `-w`; no Git object/index write occurred. All three index entries are currently absent/untracked, so this is **prospective clean-blob equivalence**, not a claim that these files are already staged or committed.

## Scope and release

No product/index edits, default ledger, services, board, native actor/ACL operations, credentials, external sends, Git writes or new agents were used. Original failed reviews and the author's RED/GREEN logs remain unchanged. Actual providers, AI supervision, geometry/executor, viewer activation, full PC_DIRECT/HIL/C05/G06/H12, all29 formal cards and board/game/timing acceptance remain not_run.

All commands finished, no subprocess or product write is pending. This independent job reports the remaining defects truthfully and releases review execution for the main's repair assignment.

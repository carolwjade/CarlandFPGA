# Independent R03 mailbox review

One reproducible call-shape defect is submitted to main as R03-MBIR-01, proposed P2. This is an independent software review, not acceptance. H01-H15 remain pinned to `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`; all29/R03 remain not_run.

## R03-MBIR-01: malformed STOP leaves the candidate consumable

Reviewed source: `.local/deepeye-implementation-a/competition/deepeye/integration/candidate_mailbox.py`, SHA256 `c30a52d58a6dde7569ea7f55e751ba766d6887e5858e6b84a1229d8de5cbfca0`, lines315-316.

The public `stop(self, reason='stop')` method lacks the `_entry` wrapper. That wrapper, at lines33-41, catches argument-binding `TypeError` inside its variadic call and invokes `_halt`. It is present on activate/observe/complete/plan/consume but absent from stop. The author's `design-api.md:17` explicitly says “Invalid public input latches STOP and raises ValueError.”

The focused self-authored reproduction constructs a real schema-valid TELEM observation and model_candidate, bound to the actual full BOOT digest. At150ms, candidate1 is pending for the210ms FAST epoch. Calling:

```python
owner.stop(reason="emergency", unexpected=True)
```

raises `TypeError` before `_halt` runs. `snapshot()` still reports `stopped=false`, `pending_candidate_id=1`, one retained observation and the150ms time high-water. A subsequent `consume(210_000_000, grant=SlotGrant(1,0))` returns candidate1. This happens in both HIL_PC_FPGA and PC_DIRECT.

The defect concerns fail-closed handling of an invalid STOP API invocation. Correctly shaped `stop("...")` clears pending state and prevents consumption; fresh-session activation and rejection of the old completion also pass. All five other time-taking public methods reject tested malformed call shapes and latch STOP. The evidence does not show real motion or sending: Selection remains non-authorizing. An upstream caller would have to catch the TypeError and continue for the stale pending state to be consumed.

Main should consider giving STOP argument binding the same fail-closed entry boundary and retaining a regression that consumes after a malformed STOP attempt. No repair, mutant or alternative product implementation was written in this review.

Evidence:

- `independent_controls.py:338` defines the failing control using independently constructed wire/schema inputs; no author test helper or mocked validator is imported.
- `suite-01/checks.json` and stderr:16 test methods,15 passing methods, two failed subcases of this one method, zero errors/skips, exit1.
- `stop-callshape-01/checks.json` and stderr: focused three-method reproduction, two failing mode subcases of the same defect; valid STOP/fresh-identity and the five other malformed entrypoint controls pass, exit1.
- Both `terminal.json` receipts confirm private hidden jobs, no unresolved tree, and all six distinct held process objects signaled across the two runs. The test failure is retained; exit1 is not relabeled as a passing suite.

## Other independently checked behavior

All12 saved literal timelines agree with an independent integer ceiling calculation using fixed taskbook epochs FAST210+500k ms and STRESS2050+8000k ms, age caps1500/12000ms, original completion+15ms transfer bound and strict selected-slot<deadline. Actual BOOT fields confirm those constants; mailbox output was not the expected-value oracle.

New nanosecond-edge controls cover deadline-before/equal/one-nanosecond-after-slot; completion+packing exactly at/one nanosecond after a slot; missed slots; age-excluded next slots; and a nonzero fixed origin37,000,011ns. Those12 cases run in both H12 modes. Actual schema, CRC codec and BOOT helper were used throughout.

Targeted lifecycle controls passed for:

- Diagnostic plan not consuming; exact-time consume only; wrong grant/window refusal; consumed-slot replay; identical completion after consume not rearming; a new candidate not consuming twice in the same slot.
- Later arrival of an older observation completion cannot displace a newer observation candidate, including after consume.
- Conflicting completion deadline extension latches STOP; original sample age and duplicate observation/completion do not renew freshness.
- A retained old observation is usable within the four-entry window; an evicted reference cannot be consumed or newly admitted.
- Missing source/domain/transfer bound/sample mapping, missing or wrong-generation grant produce no selection.
- Both TELEM and EVENT schema paths; CRC/context/mapping rejection; causal original receipt/dispatch/completion ordering; strict integer, generation, source/domain and deadline rejection.
- Four retained observation entries, half-range/backward/wrap rejection, nonregressing clock,64-session capacity and refusal of the65th activation.

The author's original strict-deadline negative control remains unchanged and failed as recorded. The actual BOOT helper still returns its early `send` branch for ready35ms/deadline100ms. The mailbox's extra lines286-288 correctly refuse the210ms slot. This historical failed control was read and checked, not rerun or replaced.

## Identity, scope and limits

`initial-audit.json` verifies all46 author artifact hashes under the pinned manifest `b2ff0aa626b0a391594f169ad7bb9d54c2dfd199fa13c76d745d5e56b4ff539b`, exact identity of all three current product files with author final-source snapshots, nine task inputs and four C dirty-file pins. Final audit repeats these identities after the review.

The new tests bind exact file bytes and recorded import hashes. The author's baseline HEAD is `c77ee6460cc8dad527c4a7c5dad050c62a9be990`; this review makes no claim that the retained tests executed at the author's later closeout HEAD or the current repository HEAD. No Git operation was performed.

The documentation accurately states that identity objects and record construction do not authenticate a producer, prove measured bounds or authorize motion. `plan()` is diagnostic; `consume()` only retires the selected mailbox result at a software epoch. PC_DIRECT's control-primary epoch does not imply a wire downlink or HIL capture. The owner must serialize calls; actual verified producer/IPC, source clocks, global session freshness, transport/world authority, B PL history and full two-mode runtime remain external.

History cardinality is bounded; this is not a whole-process memory proof. Opaque caller objects and the free-form STOP diagnostic string are outside a fixed byte-size bound. The tests establish bounded software behavior, not measured latency, runtime deployment, physical board behavior or full R03 acceptance.

Two worker runs were hidden and below-normal priority. The harness creates suspended processes, assigns a private Windows job before resume, imposes time/process/memory/output limits and verifies held handles on termination. Tree/free-space quotas are sampled and can overshoot; the Python audit is a cooperative effect guard, not an OS security sandbox. No denied effect was attempted. No author output, product file, C dirty byte, service, board, installation, communication or UI was changed.

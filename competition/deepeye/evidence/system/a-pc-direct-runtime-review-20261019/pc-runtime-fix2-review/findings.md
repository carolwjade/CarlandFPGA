# FIX2 independent BOOT/public-entry review

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-PC-RUNTIME-BOOT-VETO-FIX2-REVIEW-20261018-v1`; job `child-066d9470a72f477b9b9b27fa4c6095d3`; agent `/root/r03_review_20261018`. Sole director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation2. H01-H15 canonical SHA256 verified unchanged: `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Product source/index and prior evidence are read-only.

**PCR-R2/R3 original counterexamples are independently verified fixed. One narrow public-wrapper argument-binding defect remains (PCR-R4), reproduced across six entry points with the same root cause.** This is not a new reflection/`__wrapped__`/malicious-trusted-code threat model. No such bypasses were probed.

## Original repairs verified

The exact original eight-case probe and exact supplemental four-case probe were imported without executing their output-writing main blocks; all12 tests passed freshly. No test methods or previous files were altered. Busy/reentry now precedes step argument validation. Only the explicit private ordinary no-command outcome avoids latching; malformed actual calls/errors veto. Valid BOOT identity retirement now precedes activation clock and guard construction. Original malformed-step and activation-clock-error replay cases no longer activate.

The author63 and unchanged dependency79 test results are reused against matching frozen hashes rather than rerun. The exact author diff and source show the intended changes; neither real providers nor actual executor/AI supervision are supplied by this patch.

## PCR-R4: wrapper receiver keyword raises before its own guard

`_runtime_entry` wraps each method using `def call(self, *args, **kwargs)`. The explicit call below is rejected by Python while binding **the wrapper's** named `self` parameter, before its `try/except TypeError` begins:

```
owner.step(self=None, expected_pose_revision=0, dt_ns=1)
```

Analogous keyword calls affect `boot`, `board`, `observe`, `command`, and `stop`. In a healthy-idle runtime, a BOOT verifier catches this TypeError and returns the valid proposal. No `_trip` or veto-generation change occurred, so that outer BOOT activates. Subsequent ordinary valid heartbeat/observation/command invokes the standard fixture fence and produces `committed=True`, fixture commit count1.

`new_probes.py:test_reserved_self_keyword_cannot_bypass_public_guard` records six subcases: every method catches TypeError, `boot_rejected:false`, `committed:true`. These six RED assertions are **one root defect**, not six independent findings. They use ordinary public argument binding; they do not mutate private runtime state, forge executor receipts or omit the final fence. No actual movement was measured. This is a trusted-callback malformed-call handling gap; it is not a claim of arbitrary external-controller access.

A positional-only wrapper receiver, or equivalent forwarding arrangement that allows `self=` to reach the protected method call, can close this gap. The main has retained the frozen source while this review closes and owns that subsequent repair. No source fix was made here.

## Adjacent checks and test results

| Command group | Fresh result |
|---|---|
| Exact original independent8 | 8 passed, exit0 |
| Exact supplemental4 | 4 passed, exit0 |
| New entry-edge suite | 3 test methods: 2 passed, one method has6 failing subcases; zero errors, exit1 |

The passing new checks show ordinary duplicate arguments are converted to ValueError and veto correctly across all six methods. A guard-construction exception after valid verification retires the old identity; replay is rejected and a separate higher-generation/new-session handshake recovers. Thus the new finding is specifically wrapper-level receiver binding, not a failure of the repaired retirement order or legitimate recovery.

Exact new probe file: `.planning/deepeye-resume-20261018/pc-runtime-fix2-review/new_probes.py`.

Reproduction command from the root, using existing dependency environment as recorded in `commands.json`:

```
.local/venv/Scripts/python.exe -B -X utf8 .planning/deepeye-resume-20261018/pc-runtime-fix2-review/new_probes.py
```

The failing child exit is1; the recording driver exits0 only after preserving all outcomes. Full stderr and `new_probe_results.json` retain the six failures. A future repair rerun must preserve this RED evidence and write new output under its new ownership.

## Source and Git byte gate

All three source/test/doc hashes match the author's FIX2 receipt and remain unchanged around testing. All12 direct dependency bytes also match. Before/after/final source manifests record exact SHA256 values.

The three raw streams are LF-only and their raw Git blob OIDs equal Git clean-filter OIDs under current text=set/eol=lf attributes. The hash-object commands did not use `-w`. All three index entries remain absent, so this is prospective clean-blob equivalence rather than an already-staged/committed claim. No normalization or index change was made.

## Release and acceptance limits

Review commands are finished; no subprocess or product write is pending. The new job is completed with its one remaining finding and exact RED evidence. The main owns the next repair and acceptance decision. The offline adapter is not actual trusted-source/AI/physics integration; full PC_DIRECT/HIL/C05/G06/H12, all29 formal cards, board/game/timing acceptance remain not_run. No services, hardware, OS/ACL actors, credentials, external sends, new agents, Git writes or default ledger changes occurred.

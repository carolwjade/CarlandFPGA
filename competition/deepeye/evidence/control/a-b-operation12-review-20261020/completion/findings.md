# Independent A evidence reconciliation of B operation 12

Work `A-B-OP12-REVIEW-COMPLETION-20261020-v1`, native job
`child-dee2ddf706be42e4abe16057fcf794f5`, agent
`/root/b_op12_review_complete_20261020`. This is a new bounded evidence review.
The original job `child-5345bee33b45490bbc0c070bd3473a41` remains terminal
**failed**, `TimeoutError:`, observed at `2026-10-20T00:06:00.422936+00:00`.
Its completed simulation files do not turn its failed model job into a completed
review. Final adoption and acceptance belong to the quality main.

Exact tested B head: `f7e95af8f8abae6d4a5312c08d99e095a7e5dec1`.
Source commit: `61141302a68c3085951721074abbfeec31bfcb3a`.
Operation: `B-DEEPEYE-PWM-ATOMIC-20261020-12`.
Request SHA256: `9951beb894c52fa1e9ec6ae6f487856125a9a91e7e91b8aae75c297b04420e56`.
Handoff manifest SHA256: `6d6de98ec58741efdd20110dba91ea3cff644ae59901413910fc654376b7cd04`.
Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01-H15 recomputed as
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
The active generation-2 Desktop director and A node identity were checked.

## Reconciled evidence

The new `reconcile.py` finished with exit 0; raw stdout/stderr and command are
in `audit-attempt-02/`. It launches no simulator. It rehashes preserved files,
regenerates deterministic oracle vectors in memory, and parses raw traces.
The 357 selected source files match size, SHA256 and Git blob identity; all
353 handoff entries match. The archived bytes also match and its 2,549 members
were checked without extraction. Source aggregate SHA256 is
`63bc299b223c2bab97eaa063f98bb9b7dec86ea951ef94bc25557d02d3995c5f`.
Original source and review bytes remained unchanged during reconciliation.

| Preserved simulation | Freshly reconciled result |
|---|---|
| COUNT_W=2, TAG_W=1 | 7,041 edge samples; all 99 legal small tuples |
| COUNT_W=3, TAG_W=64 | 26,603 edge samples; all 1,295 legal small tuples |
| COUNT_W=32, TAG_W=32 | 12,546 edge samples; bounded unsigned/high-bit cases |
| Long fixture | Complete 2,000,000-interval frame; high totals 10,000/490,000/70,000; atomic change followed by two complete period-37 frames |
| Parameter guards | (1,32), (33,32), (3,0), (3,65): exact DUT `g_param_guard` fatal at time 0, one error and zero warnings |
| STOP-ignored mutant | Actual one-line RTL mutant; row 815, field 13 (`frame_start`), got 1, expected 0 |
| Pitch-from-yaw mutant | Actual one-line RTL mutant; row 12, field 19 (`active_high_pitch`), got 0, expected 1 |

All 46,190 samples match all recorded public output fields, including pre/post
ready, event pulses, running/pending, PWM levels, active tuple and tag. Each
canonical LF vector file matches its frozen hash; regenerating it from the
inspected absolute-edge deadline oracle reproduces the same bytes. Every
positive log has its exact completion marker, no fatal/error, zero diagnostic
errors/warnings and empty stderr. Four guard processes returned 0 after `$fatal`;
their exact DUT diagnostic, scope, time and absence of a success marker establish
the intended negative result. Both mutants have matching compiled copies,
partial failing traces and explicit oracle counterexamples. No new simulation
was necessary to fill a missing or falsifying check.

The inspected RTL/oracle/testbench cover the internal atomic tuple queue,
old-boundary application, one-edge backpressure bubble, reset/STOP flushing,
restart only after a fresh request, zero/full duty, period 1, small maximum
periods, and opaque tags. The 32-bit cases include unsigned bit31-set values
and invalid widths; large maximum periods receive bounded observations only.
Static counter arithmetic inspection is distinct from a complete max32-wrap
simulation or a formal proof. The testbench observes public ports without
hierarchical force/seeding. The independent oracle uses absolute origins and
deadlines rather than copying the RTL phase counter.

## Harness and metadata findings

The installed tool evidence is ModelSim SE-64 2020.4 (Oct 13 2020). Binary hashes
match the preserved audit. Initial launcher/path failures and two SQLite
non-ASCII work-path compile failures remain intact. The subsequent interactive
launch reached `$finish` but lacked the positive marker and reported
`FileWatch(fileName)` in stderr. The passing run used the disclosed ASCII R:
mapping and wrapper: `Path.resolve` became `Path.absolute`, and vsim
`-c -onfinish stop` became `-batch -syncio`. RTL, TB, vectors and verifier bytes
were not edited by that wrapper. The compiled copies match the pinned source.

The runner's `result.json` records pre-wrapper argv. The actual translated argv
was independently recovered from `COMPAT_VSIM` stderr and matched for all
positive/guard/mutant launches. `simulator-command-reconciliation.json` records
both forms for 22 version/compile/simulation commands; the outer process exits
and all 26 captured command raw-stream hashes were also checked.

The frozen metadata's runner hash `e34e0bf9...` differs from the executed
`ba2491be...` runner. This review claims byte identity for the frozen vectors,
not for those different runner versions. The preserved later runner change
from `run-02` to `run-03` changes vector writing from Windows text to canonical
LF bytes; the inspected oracle schedule regenerates the frozen bytes exactly.

The original `result-audit.json` says author `files_verified=85`. That is too
broad for the published snapshot: **40 entries have verifiable committed bytes;
45 are unavailable `work/` compiler entries**. Two original names are published
as byte-identical `.txt` aliases. The new receipt records those counts exactly.
The author summary reports 9 groups and 90,644,277 assertion invocations; it is
author evidence and was not rerun or counted as independent cases.

All original failed source/result-audit attempts remain unchanged. Their
recorded failures concern canonical Unicode serialization, decimal versus hex
trace index parsing, published filename aliases, 0 ns versus 0 ps time display,
and a mistyped expected tool hash. The new audit also preserved its own first
attempt: an overly narrow four-key author-summary comparison failed, then was
corrected to check the intended keys in the richer dictionary. That was an
audit-script schema error, not a simulation failure. See `audit-attempt-01.json`.

## Cleanup and limits

Historical R: creation/removal commands both returned 0. `cleanup-current.json`
records a fresh read-only process and SUBST snapshot: no ModelSim process,
no original-review Python process, and no R: mapping. This does not invent a
historical process stop time. No process or mapping was changed by this review.

Only this new review directory was written. No product/source changes, Git
operations, messages, child work, installations, services, credentials, board
access or synthesis occurred. Later operation 13/14/15 heads are outside scope.
All 29 formal cards and G05/B06/R03 system acceptance remain **not_run**.
Synthesis, implementation, timing, CDC/RDC, stopped-clock/asynchronous STOP,
pins/capture/HWH, clock rate, TTL/BOOT/motion/ABI authority, both complete
control chains, and physical measurements have no new result here. H01-H15
remain mandatory. The evidence supports only the bounded synchronous digital
simulation of these exact operation-12 bytes.

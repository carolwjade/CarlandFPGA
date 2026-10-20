# A independent evidence review of B operation 14

Work `A-B-OP14-INDEPENDENT-20261020-v1`, job
`child-9f94617fff6047d9b56574520f9b431c`, agent
`/root/b_op14_review_20261020`. The parent-supplied guard returned
`execution_allowed=true` before project work. No private lease content was
displayed or copied into this review. Active generation-2 Desktop director,
node A identity, project role declarations, both skills and both immutable
scope files were read. The requirements canonical SHA256 was recomputed as
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
This report supplies evidence to the quality main and makes no final acceptance
decision. Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01-H15 unchanged.

Exact B head: `7dd2c4108ee49cc6e0feb7c715d786f8b11a99c2`.
Source commit: `21ae4c6bc9d03aea8a79bf784d9873ebdaf1c903`.
Operation: `B-DEEPEYE-PWM-COHERENT-CAPTURE-20261020-14`.
Request SHA256: `1d23fc80980b0269bece376230d3722892355b725e217f7644e5b519b8230970`.
Handoff manifest SHA256: `f93e490bb0da5fb7e676538ec29e73aa56aacd388b574351de008b1d61ea8602`.
DUT SHA256: `4baddfc31248c49000c00ac74bc2319cef6c9016c7df3f1822030c69cd82f456`.
All 293 manifest entries match size/SHA256. All 309 selected files match their
size/SHA256/Git-blob records and the untruncated exact-head Git tree. The raw
commit identifies this head. Canonical request hashing also matches. Before
and after inventories are identical and the post-run audit rechecked current
source bytes. Original B failures and all other evidence remain read-only.

## Fresh bounded ModelSim evidence

ModelSim SE-64 2020.4 actually compiled the exact DUT and reused public replay
testbench. `review.py` imports or executes no B Python model or runner. Its
`EventLedger` records observed transition timestamps, chooses a shared R0,
and at shared R1 searches each lane's recorded falls strictly inside R0/R1.
High times come from timestamp subtraction rather than DUT-style per-lane
capture counters. Absolute deadlines determine period and witness exhaustion;
a separate transport mailbox models retirement, backpressure and drops.

The exact handoff stimulus schedule and public replay TB were reused. All
19 expected pre/post port fields were independently recomputed at every
expanded sample, compared with the frozen vectors, and reconstructed into
identical vector bytes before A compilation. All repeated RLE edges are
checked by the TB. Its saved trace contains each row's ending outputs and
cumulative sample count. All six actual traces equal B's committed traces.

This A oracle was written after reading RTL, B reference and scope. The saved
oracle freeze precedes this A simulation; it is not a claim that the oracle
was frozen before source inspection. Command-recording and ASCII-path lessons
from the prior op13 harness were reused; the op13 oracle was not imported.

| COUNT / WITNESS / TAG widths | Sampled edges | RLE rows |
|---|---:|---:|
| 2 / 6 / 1 | 9,921 | 9,474 |
| 3 / 6 / 64 | 18,129 | 15,703 |
| 2 / 2 / 64 | 9,556 | 9,539 |
| 2 / 3 / 32 | 9,682 | 9,637 |
| 16 / 17 / 64 | 731,517 | 10,420 |
| 32 / 64 / 64 | 22,065 | 10,383 |

Total **800,870 sampled edges / 65,156 RLE rows**. Every positive run has
its exact completion marker, empty stderr, `Errors: 0, Warnings: 0`, actual
exit 0 and verified trace. These are sampled-edge counts, not independent
test cases or physical measurements. All 450 small-width legal period/high
triples were observed independently (9 at COUNT_W2, 441 at COUNT_W3), with
the nine triples repeated at WITNESS_W3. The reused schedules include the
author's 48,000 deterministic-random samples; all were checked as inputs,
without claiming independently generated randomness.

The per-sample oracle checks common R0/R1, unequal/extra rising edges, mixed
rise/fall samples, missing falls and constant lanes, exact first-fall widths,
reset/STOP/rearm priority and held controls, high rearm baselines, latched
opaque zero/full-width tags while input tags change, queued payload preservation,
overrun drops, saturating loss diagnostics, old-slot retirement with same-edge
refill, and retirement after witness disarm. For example, COUNT_W3/WITNESS_W6
observes 12 same-edge refills and 1,297 fault pulses after count saturation;
COUNT_W2/WITNESS_W3 observes 14 edges where witness exhaustion outranks an
otherwise overflowing period. Those are coverage observations, not additional
test cases.

COUNT_W16 directly observes periods 32,768, 32,769 and 65,535 with their stated
high triples. Four period-overflow witnesses occur at elapsed 65,536, including
a genuine common rise at zero-based sample 524,559 that starts a fresh partial.
The small witness widths exhaust without wrapping and retain/retire old queued
transport as required. No complete maximum 32-bit period, 32-bit overflow or
maximum 64-bit witness traversal was executed.

## Actual negative diagnostics and preserved failures

All 11 invalid triples reach the exact original DUT's own time-zero guard:
COUNT_W 1/33/0/-1; WITNESS_W 1/65/0/-1; TAG_W 0/-1/65, with other parameters
held at their listed valid values in `receipt.json`. An independently authored
guard-only top clamps its signal widths just as the DUT does, so invalid
parameters cause no unrelated connection-width warnings. Each run has exact
parameter display before `DEEPEYE_COHERENT_INVALID_PARAM unsupported widths`,
one DUT fatal at **0 ps**, scope `guard_tb.dut`, `dut.sv:136`, no guard-missing
or PASS marker, and `Errors: 1, Warnings: 0`. Each actual outer exit is **0**.
The explicit diagnostic, scope, time and error count establish guard rejection;
exit 0 alone does not.

The original B run-01 diagnostic-parser failure remains preserved and was
verified from raw bytes. B run-02 reaches all 11 named DUT guards, but its
unclamped replay top produces connection-width warnings in nine guard cases:
5 warnings for COUNT_W -1/1/33; 2 for WITNESS_W -1/1/65 and TAG_W -1/0/65.
COUNT_W0 and WITNESS_W0 have zero warnings. All still contain the exact DUT
time-zero diagnostic. These warnings are retained in `audit-result.json`;
they are not silently promoted to clean elaboration. B's harness-correction
record discloses that the corrected freeze followed RTL inspection, with the
reference/stimulus/vector/TB bytes unchanged. This review makes no revised
historical provenance claim.

Both exact private faulty copies compile with `Errors: 0, Warnings: 0` and
are rejected on public ports:

- `relaxed_common_R1`, SHA256
  `616b8f92e326578d8243faa791aa65d014be55eca185af7d3ebe80149624e922`:
  row 5363, one-based sample 7362, field 2 (`out_valid`), actual 1 versus
  expected 0, at 36,809 ns. Common start and falls are followed by levels
  `000 -> 001`; accepting that subset as a common closing edge is exposed.
- `stale_rearm_slot`, SHA256
  `466c3a8664fdebcec8a08fb3ef0f912fed3b5452666865cc3767c3ac36dfad82`:
  row 6876, one-based sample 9242, field 3 (`out_period`), actual 5 versus
  expected 0, at 46,209 ns. A queued period-5 record remains in the faulty
  copy after explicit rearm; combinational valid masking does not conceal
  the stale public payload.

Both runs show a named `PUBLIC_PORT_MISMATCH` fatal and `Errors: 1, Warnings: 0`,
with actual process exit 0 and no positive completion marker. Their diffs,
hashes, nearby input/expected rows, partial traces and raw logs are preserved.
No functional discrepancy was found in the original DUT within this bounded
review scope. Adoption and acceptance remain the quality main's decisions.

## Execution integrity and limits

`receipt.json` and `commands/` retain all 30 actual simulator/tool/mapping
commands, argv/cwd, timestamps, PIDs, actual exits, stdout/stderr hashes and
termination flags. Every direct process exited with no timeout; the outer
Python launcher also returned 0. Both compilation and simulation versions are
actual 2020.4 results. Tool binary hashes, oracle freeze, exact RTL/TB snapshots,
vectors and public traces are recorded. The launcher used `-batch -syncio` to
retain stopped-fatal diagnostics. The helper never changed source resolution,
argv interpretation or credentials.

A verified-unused Q: mapping targeted this owned directory only. Creation and
removal each exited 0. The fresh cleanup snapshot shows no recorded direct
process, no owned review Python process, no Q: mapping and no timeout. All
private libraries and scratch remain under this evidence directory. The
post-run `audit.py` independently verifies source-tree/blob identity, manifest
entries, command-log hashes, diagnostics, positive traces, exits and cleanup.

Only `.planning/deepeye-resume-20261018/b-op14-independent-20261020` was written.
No product edit, physical board, native GUI, product Run, services, drivers,
configuration, install, Git mutation, external message or child delegation
occurred. No later op15 result is included. All 29 formal cards and G05/B06/R03
remain **not_run**. No new synthesis, implementation, physical timing,
CDC/RDC, asynchronous capture, applied-command proof, source liveness,
freshness/TTL/profile, pins/HWH/BOOT/TRACE ABI, stopped-clock safety, motion
authority, or complete product control-chain result is established.
`out_valid` means queued transport only. H01-H15 remain mandatory.

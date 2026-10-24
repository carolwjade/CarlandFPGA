# Independent A evidence review of B operation 13

Work `A-B-OP13-INDEPENDENT-20261020-v1`, job
`child-353d776cb7564092a0960bce35b6c14f`, agent
`/root/b_op13_review_20261020`. The assigned lease returned
`execution_allowed=true` before project work. The active generation-2 Desktop
director, A node configuration, both project role declarations and H01-H15 were
read. The requirements canonical SHA256 was recomputed as
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
This is evidence for the quality main; it makes no final acceptance decision.

Exact B head: `732a58ba60c7cce0027d683e912d986453755843`.
Code commit: `923e19dedf53b0b38134e4a7da3cc121d8c0e505`.
Operation: `B-DEEPEYE-PWM-EDGE-MEASURE-20261020-13`.
Request SHA256: `1a3bf5940f10ae3d0076ecb192490dfcd8e672efc9ab507194e8031b3ae5fd33`.
Handoff manifest SHA256: `47382b6eeb6a9fd24b60f6c0d209328c141a4e3f513a55c472e7313b50121230`.
All 373 selected files match their size/SHA256/Git-blob records, including the
363 manifest entries. The request canonical hash also matches. The source
inventories are identical before and after execution; preserved B failures and
all prior op12 evidence remain read-only.

## Fresh bounded simulation evidence

ModelSim SE-64 2020.4 actually compiled the exact DUT and public replay TB. The
review's `TimeOracle` imports no B model or runner. It recomputes every expected
port from input samples, absolute rising/falling timestamps, an absolute expiry
deadline, a latched epoch tag and a separate transport mailbox. It checks every
expanded edge of the frozen stimulus before compilation. It uses no internal
DUT signals, counters, hierarchical force, seeded state or generator round trip.

The stimulus schedule and public replay testbench are reused from the exact B
handoff; the expected values were independently recomputed in `review.py`.
This A oracle was written after source/B-oracle inspection. Its persisted freeze
is before this A simulation, not evidence of a freeze before reading B source.
The testbench checks all repeated RLE edges, while the public trace records each
RLE row's ending outputs and cumulative checked-edge count. All five new traces
and vector files equal B's committed bytes.

| COUNT_W / TAG_W | Checked edges | RLE rows | Result |
|---|---:|---:|---|
| 2 / 1 | 14,372 | 11,680 | all 3 legal period/high pairs |
| 3 / 64 | 18,760 | 16,802 | all 21 legal pairs |
| 4 / 32 | 21,432 | 17,674 | all 105 legal pairs |
| 16 / 64 | 1,132,372 | 16,585 | selected periods through 65,535; overflow at 65,536 |
| 32 / 64 | 66,670 | 16,506 | bounded functional observations |

Total: **1,253,606 sampled edges / 79,247 RLE rows / 129 exhaustive small-width
pairs**. These are sample counts, not independent test cases or physical
measurements. Positive runs have their exact edge/row completion marker,
`Errors: 0, Warnings: 0`, empty stderr and actual exit 0.

The oracle observes exact R0/fall/R1 subtraction, high=1 and high=MAX-1,
MAX-valid and MAX+1 rejection, a fresh rising at overflow becoming the new R0,
constant levels without a starting edge, held rearm and control priorities,
latched opaque zero/full64 tags, queued-record preservation while a later
partial overflows, same-edge retirement/refill, output backpressure and loss
saturation. Per-edge expected pulses, sticky flags, loss and queue payloads are
compared, including after saturation. The 16-bit witness records explicitly bind
overflow elapsed=65,536 and fresh-overflow-rise recovery to sample indices.
No complete maximum 32-bit period or 32-bit overflow was executed.

All seven invalid configurations `(1,32), (33,32), (3,0), (3,65), (0,32),
(-1,32), (3,-1)` produce exactly one named
`PWM_EDGE_UNSUPPORTED_PARAMETERS COUNT_W=... TAG_W=...` DUT fatal at
**0 ps**, scope `main_tb_pwm_edge_measure.dut.g_param_guard`, `dut.sv:202`,
and `Errors: 1, Warnings: 0`. Their outer process exit is 0. The exact fatal,
scope, time and absence of PASS establish the intended negative result;
exit 0 alone would not establish it.

Two actual private faulty RTL copies compile cleanly and fail on public ports:

- `high-plus-one`: DUT line 176 adds one to the high payload. The first
  counterexample is post row 4, edge 5, time 24 ns: high=2, expected high=1.
- `rearm-stale-slot`: DUT lines 106-109 retain the old slot on rearm. The first
  counterexample is post row 84, edge 119, time 594 ns: payload 2/1/tag1,
  expected cleared payload 0/0/tag0. Valid is masked but payload still exposes
  the omitted reset, so this is a public-port rejection.

Both faulty-copy exits are also 0; the named `PUBLIC_PORT_MISMATCH` fatal,
trace/counterexample and `Errors: 1, Warnings: 0` prove rejection. Source diffs,
mutant hashes, raw commands/streams and partial traces are retained. No new
functional discrepancy was found in the reviewed DUT within this bounded scope.

## Execution integrity and limitations

The 25 actual commands, argv/cwd, timestamps, process IDs, actual exits,
termination flags, stdout/stderr and binary hashes are in `commands/` and
`receipt.json`. The outer Python launcher returned 0. The simulator launches
use the disclosed `-batch -syncio` mode, avoiding the prior op12 interactive
`$finish` flushing problem. A verified-unused Q: mapping targeted this owned
directory only. There is no `Path.resolve` monkey patch or hidden argv wrapper.
Q: creation/removal each exited 0. Every direct command process exited; a fresh
process/SUBST snapshot shows no ModelSim/review Python process or Q: mapping.
Private compiler libraries and scratch files are retained under `run/`.

The initial lease read mistakenly emitted the private lease record into tool
output, contrary to the assignment. It is not copied into any authored review
artifact, findings result, native-completion text or final report. The private
input remains at its original path. No credential/provider changes or replay
were attempted. The follow-up token read and validation were handled without
printing the value. This confidentiality exception must not be omitted from
the execution audit.

Only this evidence directory was written. No board, native GUI, product Run,
service/config/driver/install operation, Git mutation, external message, child
delegation or product edit occurred. All 29 formal cards and G05/B06/R03 remain
**not_run**. Synthesis, implementation, timing, CDC/RDC, asynchronous/physical
capture, stopped-clock STOP, pins/HWH/BOOT/clock, waveform freshness/liveness,
motion authority, three-channel applied-command capture, and both complete
product control chains have no new result here. `out_valid` remains queued
transport only. H01-H15 and the fixed contract are unchanged; final adoption and
acceptance belong to the quality main.

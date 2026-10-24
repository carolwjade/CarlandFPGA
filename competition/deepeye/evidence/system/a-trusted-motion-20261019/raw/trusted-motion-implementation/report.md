# Frozen owned motion executor implementation

Task DEEPEYE-IMPLEMENTATION-20261014/v1; work A-trusted-motion-executor-20261019-v1.
Owner `/root/r03_review_20261018`; original job
`child-026f779d3a764a98aa2cf629e454d164`. Main retains acceptance.
H01–H15 canonical requirements hash was recomputed and remains
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

Implemented and frozen for independent review: real local numerical
prepare/commit executor, relative passage preparation/materialization helpers,
22 regression methods and integration documentation. Final combined run:
**135 tests passed, exit 0** (22 new executor methods, 113 existing
passage/workspace/solid/runtime methods; runtime has 64 methods).
This is bounded local software evidence. All 29 formal taskbook cards remain
`not_run`; no actual source/BOOT authentication, live AI, renderer, physical
runtime, board, OS isolation or full R03 acceptance is claimed.

## Final mechanism

Only the four assigned product files changed. `OwnedMotionExecutor` requires an
explicit valid owned phase, full independently enumerated solid scene,
matching capsule model and explicit conservative margins. It implements only
motion prepare/commit, with separately bound trusted admission; it provides no
default `verify_*`, AI provider or production activation.

Preparation derives the canonical path from the owned pose and original command
bytes; all six workspace faces and each complete solid-scene slice must pass.
The CP chord-covering length, curvature/rotation floor, numerical/speed carry,
asset/engine/obstacle margins remain included. UNKNOWN/DRILLING_REQUIRED and
unresolved arrival fail the entire step. Proved workspace violation latches
trial failure. A relative proof anchor never supplies freshness or extends TTL.

Commit consumes its private handle before any callback. It preallocates its
publication objects, invokes the actual runtime final fence once inside the
serialized owner transaction, checks exact BOOT object/command/unchanged root,
actual nonoverlapping interval and strict end < original deadline, then makes
one root publication. There are no geometry/hash/clock/I/O/external calls in
the successful post-fence suffix. Pose, phase proof and actual interval publish
together. Events are materialized on later authority access, preserving older
events and the untouched anchor proof. Lost receipts reconcile through the
owned committed frame; handles cannot repeat effects.

STOP/revoke, BOOT or admitted-command changes retire pending handles. Scene,
asset, epoch or layout changes use explicit `invalidate_world` and require a
new run/store/history; BOOT cannot resume the retired world. The integration
must deliver these registry changes and STOP to the executor and runtime on
their owner thread. This object does not watch files or authenticate a world
registry. One pending preparation is retained. Recovery is deliberately
conservative: rejected transactions stop the store, fresh BOOT cannot clear a
trial failure, and the final BOOT record must be the same immutable object.

## Concrete coverage

| ID | Implemented regression evidence |
|---|---|
| T01 | Successful prepare preserves the exact visible root/pose/revision. |
| T02 | Real geometric partial entry; actual delayed fence maps only new events; one callback/publication. |
| T03 | STOP inside callback followed by a valid fence still prevents movement; handle consumed. |
| T04 | Owner world invalidation for scene/asset/epoch, new BOOT, new command and revoke reject old handles before callback. World event delivery itself remains an integration dependency. |
| T05 | Repeated/foreign/reentrant handles reject; caught recursion cannot revive outer commit. Additional tests use the real runtime double-fence guard and missing callback. |
| T06 | Actual accepted runtime with actual executor; separate original TTL, sample-age, STATE8 and AI-liveness expiration. TTL/sample fixtures keep heartbeat fresh before entering the serial step; no reentrant channel delivery is used as a substitute. |
| T07 | Exact deadline equality and overlap with last actual committed interval reject. |
| T08 | Thin forbidden water layer: first solid slice clears, second does not, whole pose remains unchanged. Slice/solid work budgets fail without a prefix. |
| T09 | Missing compound piece rejects, overlapping ordinary rock cannot hide forbidden water. |
| T10 | Speed rounding carries into next inherited error; sweep arc covers encoded endpoint chord; rotation floor survives; missing explicit margin rejects. Positive margin partition also exercised. |
| T11 | Tip-first partial blue entry is not entered; complete tail enters. Red centre-only exit is not arrived; complete tail arrives. Same-face red aperture cannot serve blue role. Intermediate phase seeds are explicit numerical fixtures, not executed history. |
| T12 | Multi-slice unresolved arrival stays UNKNOWN; ordinary rock requiring drilling stays DRILLING_REQUIRED; no CAS. |
| T13 | New BOOT preserves trial failure/history; invalidated world cannot restart by BOOT. |
| T14 | Long real-time wait changes fence interval while pose integrates only the requested 10ms; initial event time remains unchanged. |
| T15 | Fence exception consumes handle; invalid fence validation has no movement; injected pre-fence allocation failure has no callback/pose effect; post-CAS lost result reconciles from root with no replay. |
| T16 | Frozen renderer pose/revision view; controller view only stopped/trial-failed; no authenticators/provider exposure. This is an API surface claim, not a process sandbox. |

Additional runtime integration completes two consecutive owned geometric
commits with advancing real fixture clock and correct pose revisions. Malformed
mutation calls and BOOT aliases received independent adversarial regressions.

## RED/GREEN and diagnostics

All test subprocess commands, cwd/environment, exits and raw stdout/stderr are
in `<label>.command.json`, `<label>.stdout.log`, `<label>.stderr.log`.

- `red-missing-executor`: exit 1, 16 assertion failures for absent implementation.
- `green-attempt-1`: exit 1. Two hand-computed test positions omitted braking
  acceleration; two fixtures changed same command sequence and correctly hit
  replay rejection. Corrected fixture values/sequence, no weakened product gate.
- `green-attempt-2`: exit 0, original 16 methods passed.
- `red-adversarial-entry`: exit 1, three real failures: malformed revoke/world
  call shapes caught by callback did not veto; structurally aliased BOOT could
  pass equality after the root check. Added protected revocation wrappers and
  exact active BOOT identity; `green-adversarial-entry` exit 0, 20 passed.
- `green-focused-refined`: exit 1, attempted fixture heartbeat delivery during
  the serial runtime step correctly hit reentry STOP. Moved fresh heartbeats
  before the step; `green-focused-final` exit 0. This preserves runtime's
  existing reentrancy gate.
- `final-suite`: exit 0, 133 passed. Then added allocation-fault and actual
  double-fence/missing-callback cases; `final-suite-frozen`: exit 0, **135 passed**.
  No source changed after that final run.

The finalizer initially stopped on inherited dirty `.gitattributes` versus the
older base, then on the approved design being absent from that older commit.
Those checks were corrected explicitly: attributes are recorded as observed
(no before-snapshot stability claim), and the newly selected design is checked
against its exact pre-implementation input hash. No product bytes or test gate
were changed by those evidence-script corrections. Finalizer subsequently
passed. Its successful Git commands/exits are `git_commands.json`.

## Byte binding and limitations

`source_before.json`/metadata bind the initial snapshot at
`9d29d4c87b964de98479fe62067aeb0da91ace63`. Main's authorized disjoint commit
moved HEAD to `addb2c944ea8f659c48a783c5af1853be8d24d65`; exact non-owned
dependencies from the input manifest stayed unchanged. The final manifest
records 35 relevant files. Added fixture/schema dependencies match the original
base, except the already inherited dirty attributes (recorded explicitly).
All four owned raw byte streams equal their Git clean-filter blobs and use LF.
No source/index/config/commit was modified by the blob comparison.

`passage_phase.before.py` was retrieved from the base after work and verified
against the actual pre-write manifest hash. AST comparison proves the entire
old module prefix (including preview) is unchanged; only the new relative
record and two helpers were appended. `dependency_manifest.json` and
`source_final.json` bind exact final bytes; `receipt.json` names frozen files.

Remaining production dependencies: real trusted admission/clock/AI lifetime,
source provenance, STOP/world event wiring, mesh/engine asset containment and
transform fidelity, material state law, visible renderer publication, genuine
PC_DIRECT and FPGA-chain integration. No service, board, isolation probe,
external message, Run activation, product commit or source outside ownership
was performed. Main and independent review decide subsequent integration.

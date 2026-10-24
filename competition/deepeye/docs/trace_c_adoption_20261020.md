# A independent acceptance of C's offline TRACE candidate

Main review A-C-TRACE-EXACT-CANDIDATE-REVIEW-20261020-v1 under
DEEPEYE-IMPLEMENTATION-20261014/v1, sole A Desktop generation2.
H01-H15 / DEEPEYE-HUMAN-LOCK-20261014/revision1 unchanged, canonical SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.

**Accept the pinned C decoder as independently implemented offline format and
receiver-lifecycle reference evidence.** No actionable blocking defect was
found in this reviewed scope. This decision does not admit production type7,
grant motion, validate a live source, or close R03.

## Exact inputs and actual executions

C PR25 head was read on GitHub as OPEN/DRAFT
942fa309ffc8f1d32c816cfa643b009b031d7d0a during this review. All70 tracked files
in its trace_candidate_decode folder were exported from exact Git objects;
all Git object IDs and SHA256 values were verified. Decoder SHA256 is
b02010280b72d3a94842db627f733df9c1fa6ecfe54f572509d57869d2d3d72c.
C's43 author artifacts and15 independent-review artifacts match their manifests.
The two copied normative layout/vector files are byte-identical to B's locally
pinned f7736ac737d1c7b256974beb1574b94096819270 objects.

A reviewed the decoder, replay, provenance and QA sources before executing
exact copies in a new isolated directory. No C product or original archive
bytes changed. The first A harness stopped before any test because the two
manifests use different list/map keys; its failed source and cause are retained.
The corrected harness handles both observed shapes without relaxing hashes.

Four new hidden software commands completed with actual exit0:

- Portable provenance:7 inputs,4 documented pins and H01-H15 checked.
- Replay:81 groups, including8 manual vectors,32 synthetic streams,
  23 malformed payloads,11 malformed frames and receiver/strictness controls.
- C independent QA:5 methods;300 valid grid cases,154 noncanonical RAW and
  254 nonoptimal Rice-k rejections, plus held/progression/atomic-state cases.
- C main controls:4 methods, including296 individual bit corruptions,
  cache eviction, no sequence wrap, defensive snapshots and terminal close.

These are new executions on A of C's exact saved checks, not new B encoder
experiments and not an A-authored independent encoder. A additionally exercised
all126 accepted manual/synthetic fixture packets against its current production
wire decoder; every packet was rejected as an unknown/unfrozen type. Production
wire SHA25631533439f1bab32ca71fae138bb988f51ce1d043b4e364a6c33a09eab1d5f5ec
remained unchanged.

The exact fixture totals are1816 selected original valid RAW bytes,
5346 complete frame bytes and53460 8N1 line bits. This is traffic expansion,
not proof of compression benefit or live scheduling capacity.

## Interpretation and dependencies

The implementation independently reads the frozen byte fields and bitstream,
checks local canonicality, preserves acquisition and held-source timestamps,
rejects malformed input before state commit, retains at most16 packet entries
plus four channel high-water pairs, emits no points for duplicates, and never
wraps/rebinds its receiver instance. Source/API assertions are offline structural
checks, not source authentication or measured timing.

This satisfies the previously outstanding A adoption of C's bounded offline
decoder evidence. Full B/C/A runtime interoperability still needs full BOOT,
source/profile/unit/calibration and clock-origin binding, C's live input/grouping
adapter, actual measured spare-slot budget and the original runtime gates.
Production type7 remains rejected. No ADC/EM acquisition eligibility is expanded.
The existing project-model/weights dependency is unchanged.

No board, service, driver, OS, GUI, focus, input or installed-dependency change.
All29/R03 and full two-mode runtime/board/system acceptance remain not_run.
Original peer delivery unknowns and four protected C dirty files are preserved.

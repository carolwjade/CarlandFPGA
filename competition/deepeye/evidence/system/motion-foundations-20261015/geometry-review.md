# Independent gate primitive review

Work `A-g06-gate-independent-review-20261015-v1`; Desktop worker
`01a14019-b2e3-7dc2-9029-2430683b0ba9`, director generation2
`01a13d7e-dcf1-7272-a738-a637dd62ff9d`.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` recomputed.
Reviewed source `gate_geometry.py` SHA256
`5e33a60927334cee4473d5f78afc248f04d3a5ef00db465b2bcdf14c1adc3839`.
All six source/evidence inputs in `source_before.json` remained unchanged.

No correctness defect was found within the declared instantaneous capsule/plane
primitive scope. This is not a proof of arbitrary inputs or formal G06 acceptance.
The implementation cannot establish sweep freedom, entry/arrival, routing,
asset containment, process isolation, motion authority or board performance.

## Independent evidence

- **363 capsule section cases:** 343 deterministic cases with precision160
  Decimal stationary-polynomial maximization, plus20 tiny-angle/end-cap cases
  at precision240. All returned finite lower/upper bounds contained the
  independently calculated maximum within numerical comparison tolerance1e-90m.
  No false EMPTY, false certified nonempty, wrong CLEAR/contact, excessive
  exported bounded width or UNKNOWN-to-clear transition was found.
- **128 arbitrary plane support cases:** independently normalized arbitrary
  normals/axes, coordinates up to the admitted bound, variable dimensions.
  All exact-form support estimates were enclosed by exported float intervals.
- **12 precision cross-checks:** independent maxima at160 and240 digits agreed
  to better than1e-120m, including oblique/end-cap and degenerate cases.
- **6 actual SceneDocument face mappings:** existing hash-verified real Godot
  4.7.2 executed a private copy of the actual document script. Centres and
  normals at(u=1.25,v=-2.5) matched the Python API on every face. Original product
  inputs were not executed in a writable engine project.
- Existing author's suite rerun separately: **24/24**, exit0. This supplements
  the independent oracle; it is not the independent geometric argument itself.

`independent_oracle.py` contains the full deterministic generator and oracle.
For tangent-plane coordinates, q(t)=||c+t b||²=A t²+2B t+C and
w(t)=r²-(s0+s t)². All differentiable stationary points of
sqrt(q)+sqrt(w) satisfy

    (A t+B)² w - s²(s0+s t)² q = 0.

The independent solver isolates all degree≤4 real roots by recursively finding
derivative roots and bisecting the resulting monotone intervals. It also
evaluates feasible endpoints, norm-zero and disk maximum candidates. Squaring
may add candidates, but these are feasible points and cannot exceed the true
global maximum. A separate regular grid checks enumeration against additional
lower witnesses. This differs from the production interval branch bound.
The oracle uses high precision numerical roots, not outward interval proof;
its small endpoint-roundoff allowance and comparison tolerance are explicit.

The code/proof review independently confirmed:

1. A capsule is the union of balls on the finite segment. Its plane section is
   the union of feasible disks, whose farthest radius is the stated norm-plus-
   disk expression. Convexity of the projected-centre norm bounds it by endpoint
   maxima on each retained interval; minimum possible plane distance bounds
   disk radius above. Only certified feasible points supply lower witnesses.
2. Feasible t division keeps an outer interval and excludes a zero denominator.
   Retaining the full segment when uncertain is conservative. Decimal floor/
   ceiling operations, context-independent sign changes and adjacent values
   around nearest-rounded square roots preserve enclosures. Export padding and
   outward nextafter preserve the final interval direction.
3. Tangency cannot become CLEAR. The1pm guard tightens separation. Budget or
   existence uncertainty remains UNKNOWN; EMPTY is not a passage claim.
4. h=.4/r=.12 means total length1.04m, and pivot radius≥.52m. It encloses a
   flat-ended length.8/radius.12 cylinder. That geometric fact is distinct from
   verifying the complete visual asset.

## Integration blockers and severity

**P1 integration blocker: current greybox is not contained by the default
candidate capsule.** `simulator/viewer/main.gd` constructs a.8m cylinder at the
pivot and a.22m cone centred at local Z=.51m. The cone reaches Z=.62m, while the
candidate capsule ends at.52m. The exact reproduction is to compare
`cone.height`, `tip.position` and the capsule's h+r; `supplement.json` records
the source hash and values. The source/document explicitly says the envelope
requires asset measurement, so this does not contradict the primitive's stated
guarantee. It blocks treating the candidate as the current full drill envelope.
The responsible main must reconcile actual mesh/pivot/collision containment
before using it to grant motion.

**P2 integration blocker: a synchronous call has no100Hz deadline guarantee.**
Observed solver-only times on this run:

|Workload|Count|Median ms|P95 ms|Max ms|Calls over10ms|
|---|---:|---:|---:|---:|---:|
|0–5 degrees, eccentric|64|5.87765|18.328|21.0428|19|
|0–60 degrees, eccentric|64|114.40175|167.7656|176.8571|53|
|Oblique end caps|64|.2994|157.4581|178.0446|20|

All accepted API dimensions were also tested; h=r=10m took741.169ms at3807
interval evaluations. That is not the normal drill size. Exact inputs and
per-call timings are in `oracle_results.json`. These are one observed workload
on this host, without a real-time scheduling or integrated-frame guarantee.
No deadline target is relaxed. Integration must stop on unresolved/deadline
uncertainty and cannot call these measurements100Hz acceptance.

## Artifacts and execution

`receipt.json` contains the real worker ID, commands, exit codes and SHA256 of
raw logs/source artifacts. `oracle_results.json` retains all343 original cases;
`supplement.json` retains20 additional cases, precision checks and actual
SceneDocument output. `author-unit.stdout/stderr.log`, `engine-version` and
`face-mapping` logs are captured directly as subprocess bytes.

Reproduce the independent oracle from the original repository root:

    .local/venv/Scripts/python.exe -B .planning/deepeye-implementation-a/g06-gate-independent-review-20261015/independent_oracle.py

It checks the pinned source hashes before and after execution and exits1 on
any geometric discrepancy. `capture_review.py` records the additional checks;
its output filenames use exclusive creation, so preserve the original evidence
instead of rerunning it over those files.

No product file, ACL, service, board state, credential or external conversation
was modified. Product acceptance remains pending the director's independent
decision; this review does not expand the task.

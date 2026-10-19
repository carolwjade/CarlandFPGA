# G06 entry role refinement — bounded design for main review

Work A-G06-entry-role-refinement-design-20261019-v1; original native job
child-cf373a04748847349b2b82930e4ebaa8; owner /root/r03_review_20261018.
Product baseline 3f702903f1e16fa72eae15f03ba431b78de24bd0.
This is a proposed numerical proof composition, not an implemented fix or
main acceptance. Product source/index were read only.

DEEPEYE-HUMAN-LOCK-20261014/revision1, all H01–H15, canonical requirements
SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804
are unchanged and recomputed. Sole A director remains Desktop generation2.

## Diagnosis and actual numerical evidence

The taskbook §8.3 requires complete correctly directed blue entry before
entered, complete red exit before arrived, six-face boundary safety and full
rotating-body sweeps. §G06 includes wrong direction/face, tail, rim, thin layer
and same-face U tasks. It does not require a phase event at the first possible
nanosecond. This proposal nevertheless retains the existing certified ENTERED
window rather than moving it to solve a numerical issue.

`diagnostics-r3.command.json` records exit0: four diagnostic methods, ten
numerical seeds. They call the actual CanonicalPath, six-face checker and
passage reducer. They do not implement the proposed reducer. Before/after
manifests match, with exact dependency bytes in `before.json`/`after.json`.
`observations.json` retains every entry-role and exit-role proof and side bound.

Fixture: h=.4m, r=.12m, Rb=.52m outer capsule (1.04m total envelope, not a
claim about actual drill length), identity inward −Z axis quaternion(0,1,0,0),
v0=.25m/s, FAST speed20/yaw7000/pitch0, original dt10,000,000ns. Blue front
z=15, red back z=−15, circles radius.15. All inherited errors initially zero
as explicit exact mathematical fixture assumptions; subsequent numerical
errors are computed and retained. Histories are seeded ENTRY_CROSSING, not
evidence of a preceding route or a real live provider.

| Start z | First end whole-body upper support against blue | Next full cast upper | Current result |
|---|---:|---:|---|
|14.481|−0.0007858663320444m|strictly negative|SAFE/INSIDE|
|14.4815|−0.0002858663320438m|positive, ENVELOPE_NOT_CLEAR|UNKNOWN, original state|

Both plans have original slices [0,7142857] and [7142857,10000000]ns.
Rho is about .000500194791204m then .000500031166598m. At14.4815 the first
slice proves pointwise complete entry at its end and locally creates ENTERED.
The next slice therefore uses exit role: blue becomes a closed nonactive face.
Its ≥.5mm cast inflation exceeds the ≈.285866mm starting clearance, despite
the actual curve continuing inward. That conservative failure rolls back the
entire preview and history, as it should. Both original entry-role checks are
SAFE/APERTURE; their six-face conjunction alone does not prove no blue re-exit.
Final point support is −.001000297903105m, but endpoints alone cannot close
the missing continuous interval.

The exact collision witness (.03,0,15), inward and yaw0, exact_fixture=True,
returns VIOLATION_PROVED/EXACT_FIXTURE_RIM_WITNESS. Rotating near-rim,
outward-facing blue, wrong-right-face and corner seeds remain UNKNOWN.
The corner has first entry proof SAFE and second entry proof UNKNOWN: a good
blue proof cannot erase the other face. These are genuine geometric negative
results, not injected statuses. UNKNOWN is not a proved actual asset collision.

## Recommended narrow composition

Keep the current ENTERED event and normal exit-role path. Add one explicit,
private **entry-handoff bridge certificate**, only for an INSIDE slice after
ENTERED was proved earlier in this same original plan that began in an entry
phase. It is not a second aperture authorization after entry. Its three
conjuncts are:

1. The unchanged original entry-role full slice certificate is SAFE, has exactly
   six unique valid faces, blue APERTURE, and the other five STRICT_INSIDE.
   Retain it unmodified with all rho, angle, curve, source/numeric/model bounds.
2. A new directed-interval analytic certificate proves the *entire uncertain
   body* stays strictly inside the blue plane throughout this same slice.
   Conditions and missing lemma are below. In particular its starting bound
   uses the uniform whole-slice errors, not the earlier point-time witness.
3. Original plan/context/body/gates/index/time/error provenance and the earlier
   ENTERED proof are bound together. There is no imported arbitrary phase,
   altered path, fresh speed law, new timestamp authority or hidden extra step.

The bridge therefore gives all six inside obligations. It grants no crossing
of blue, red or any other face and adds no event. Only a later ordinary exit
certificate may create EXIT_WINDOW/ARRIVED. Normal exit proofs retain priority;
the bridge is a separately typed proof, not `UNKNOWN -> SAFE` or a relabeled
entry SliceProof. Do not merge two aperture disks or discard the failing proof
if normal exit was checked first. Prefer deciding the explicit bridge
preconditions before invoking ordinary reduction, so a genuine violation is
never overridden. If an already-evaluated normal proof is VIOLATION_PROVED,
stop with that verdict; only the narrowly identified conservative blue-face
role mismatch may select an alternative proof obligation.

Narrow first implementation should allow bridge use only in the current plan
after its own ENTERED, with no new persistent phase or cross-command capability.
Every later original slice must independently use normal exit proof or another
bridge satisfying all the same conditions. Future cross-step generalization
requires separately designed provenance and is not part of this increment.

## Missing lemma: uniformly bounded inward support

This lemma does **not** exist as a sufficient certificate in current code.
`monotone_at_gate=True` is merely one nominal derivative inequality. It neither
checks direction by itself nor relates a point-time error to the next slice's
uniform error. It must not be treated as a complete new safety proof.

Let s be the original canonical nondecreasing arclength; a(s)=R(s)e_z and
X_y(s)=p(s)+R(s)y for each fixed body point |y|≤Rb. The accepted canonical
constant-curvature law gives p'(s)=a(s), and |R'(s)y|≤K Rb. A whole-slice inward
angle proof gives n·a(s)≤−c for all s, using c=.99595 < cos(5deg). If

    d = directed_lower(c − Rb*K_upper) > 0,

then n·X_y'(s)≤−d for every y throughout the slice. Hence the nominal maximum
support H(s)=sup_y(n·X_y(s)−15) cannot increase. Zero-speed intervals hold;
no division by speed or assumption of positive v is needed. This proves
rotation as well as translation for the complete pivot-radius covering body.

Use a constant E for the whole slice bounding source position/orientation,
asset/transform/numeric margins and inherited speed carry. With current CP,
`record.errors` uses original-start angle drift through `record.end` distance,
maximum endpoint position export error and start orientation/axis export error.
For this *monotonicity proof*, those exports only enclose the start of the
exact analytic curve; future mathematical support is controlled analytically.
Consequently an outward bound is:

    B = upper(n·encoded_start_p − 15
              + h*abs(n·encoded_start_axis) + r
              + record.errors.position_error_m
              + Rb*record.errors.angle_error_rad
              + record.errors.additional_margin_m).

Require B < −1e−12, with the existing directed guard. An implementation must
document and test that E covers the exact canonical body plus inherited source
perturbations uniformly, not assume a linear interpolation of point errors.
Inherited angle causes displacement ≤s_end*e_angle; speed carry has already
been enlarged for full original dt by required_inherited_errors. Numerical
start pose/axis enclosure is included conservatively. No claim that the
uncertain body's actual perturbation is monotone is required: the *constant*
outer error ball around the monotone mathematical body stays inside.

The angle proof must be recomputed/bound over this exact slice using the
accepted inward direction −1, normalized start axis, whole rotation upper and
full angle error. Do not infer it from a positive d or the presence of an
arbitrary gate certificate. B alone is also insufficient without direction.

For14.4815 second slice, the actual diagnostic B is
−.000285866332043517m and d=.741830060909625602. Thus this proposed analytic
condition has substantial strict margin while its retained full APERTURE cast
still has rho≥.0005m. This is an additional exact-law non-exit proof, not a
reduced rotation inflation: existing casts, gate/rim tests, solids and all
other faces still use their original complete inflated envelopes.

The diagnostic computes B and d but is **not the implemented lemma verifier**.
Its passing arithmetic does not upgrade the current UNKNOWN to SAFE.
If uniform source bounds or exact rotation containment cannot be established
for a caller, reject the bridge as UNKNOWN. No unknown actuator/asset error is
made zero by this derivation.

An additional .001m inherited position bound makes second-slice B positive
(+.000714133667956483m): the bridge is unavailable. In this particular fixture
the middle endpoint also is not entered, so the *existing* entry reducer
legitimately continues and records ENTERED only at the final end. That is not
a bridge success and not an error reset.

## Alternatives and limits

Simply keeping entry role until the final slice or delaying ENTERED is
insufficient: a delayed label must not grant blue re-exit after an earlier
complete entry, nor allow a same-face blue/red union. A stronger handoff to
the ordinary exit checker remains desirable when it already returns SAFE;
requiring it alone preserves today's14.4815 deadlock. Reusing only two endpoint
inside witnesses or only monotone_at_gate is insufficient for whole-body
continuous safety with the complete error budget.

Adaptive subdivision is unnecessary for this seed and cannot itself remove
the ≥.5mm floor at the first post-ENTERED starting point. Repeatedly shrinking
that slice still starts at ≈.286mm clearance. Subdivision would need an
overlapping, independently proved bridge anyway; restarting CP from rounded
samples or omitting the interval before a later deep point is forbidden.
No exact-crossing-time root search is proposed. Events remain certified windows.

Same-face gates are legal when nonoverlapping; §8.3/§G02 require radius.15,
centre at least.15 from edges, no cross-edge/overlap, and valid initial inside
alignment space. Actual gate_geometry permits tangent editor circles by exact
binary64 comparison (centre distance == .30), separately from drill/ring
contact failure. Layout permits the pair at u=±.15 and rejects ±.149. Do not
invent an extra gate-spacing requirement or disable all same-face tasks.
The bridge's strict blue-plane inside result also contains the red plane when
they share a face; it cannot produce EXIT_WINDOW/ARRIVED there. A later real
U-turn must use the existing red-only outward certificate. Outward through
blue at the same-face fixture is UNKNOWN. Adjacent/corner slices still require
all five other faces STRICT_INSIDE and can fail despite blue APERTURE SAFE.

## Bounded implementation proposal and verification plan

Main may assign only these five existing files to one implementation owner:

* motion/workspace_boundaries.py: private typed non-exit/bridge certificate,
  exact interval inequalities, domain/direction/binding checks; no public ABI.
* motion/passage_phase.py: same-plan after-ENTERED bridge composition; preserve
  original certificates, one event history and current strict-red suffix.
* tests/simulation/test_workspace_boundaries.py: analytic certificate bounds
  and meaningful failed-precondition/corruption tests.
* tests/simulation/test_passage_phase.py: reducer/full-step and event tests.
* competition/deepeye/docs/workspace_passage.md: proof, narrow scope and limits.

Source paths above are relative to competition/deepeye/simulation/authority/
for motion modules and competition/deepeye/ for tests. CP, gate_clearance,
solid_clearance, executor/runtime, wire and actor/isolation files need no edits.
If proof work reveals a CP bound deficiency, stop and return that precise
dependency to main instead of expanding ownership or silently fixing it.

Proposed tests (future implementation; not claimed executed):

|Case|Required result|
|---|---|
|14.4815 existing seed|RED current UNKNOWN -> GREEN full10ms SAFE/INSIDE only with new bound; earlier ENTERED binding/window unchanged|
|14.481 neighbor; single-slice entry|existing path and event bytes unaffected unless versioned proof trace changes explicitly|
|larger whole-record error / point error smaller than record error|B fails; bridge unavailable, no point-only substitution|
|inward angle absent, reversed axis, excessive rotation/uncertain angle, d≤0|UNKNOWN; positive B/d alone never authorizes|
|body tail still outside, rim contact/rotation, larger actual Rb|no bridge; retain UNKNOWN vs exact VIOLATION semantics|
|wrong face/corner with blue APERTURE SAFE|other-face failure blocks full original state/history|
|same-face tangent legal pair; overlap invalid; blue outward vs red outward|no union, no invented spacing; only actual red passage can arrive|
|missing/duplicate/wrong-face/foreign-index proof or forged weaker bounds|reject composed proof; retain exact original certificates|
|3+ original slices, speed-ramp mandatory edge, zero-speed interval|shared original law, full coverage; no restart; bounded work checked before advance|
|slice/bridge work budget exhaustion, STOP, one-ns deadline clip, final-slice UNKNOWN/VIOLATION|original state/history; no accepted prefix; exact status distinction|
|old strict-red-outside suffix and APERTURE-only red tail|existing published SAFE vs UNKNOWN results unchanged|
|owned executor obstacle on final original slice + STOP/world/AI expiry at final fence|all solids checked before single original CAS; no geometry after fence; no commit on failure|

Reserve a bounded explicit bridge-proof work budget or charge every attempted
entry/exit/direction check against the current slice budget; no unbounded retry
or adaptive loop. Every successful bridge-containing preview must cover the
complete requested duration. Candidate pose/errors/speed carry use original
plan.end, one revision, and exactly one ENTERED; a bridge appends no event.
Full initial and per-original-slice solids remain in OwnedMotionExecutor,
followed by the unchanged single actual final fence, original TTL/source/AI/
BOOT/STOP/revision identity checks and one owned-root CAS. No re-run/motion
grant or post-fence geometry is added. Preserve raw RED before implementing,
run focused GREEN and existing253 regression dependencies once at exact pins,
then obtain independent review before main publication.

## Evidence limits and handoff

Exact source/doc hashes and sizes are in before.json/after.json. Current
diagnostics ran no model, native OS probe, UI, service, board or control chain;
no1000-case campaign was started. First command failed before tests on an
incorrect dependency doc filename; raw exit1 logs remain. Second diagnostic
run had one mistaken expectation: increasing source error delays the *existing*
pointwise ENTERED until the last edge rather than forcing total rejection.
That original exit1/observations-r2 evidence is retained. The expectation was
corrected to assert bridge B fails while existing entry remains legitimate;
the source checker or any acceptance gate was not changed.

The .5mm floor, ≤.05deg slice rotation, volume/guard/error budgets, ≤10ms original
step and original deadline all remain unchanged. General APERTURE tails,
complete36 face-pair routes including U turns, real containment, causal sources,
both actual H12 chains, G06/G07, hardware and all29 formal cards remain not_run.
This design and diagnostic evidence is for the responsible main's decision.

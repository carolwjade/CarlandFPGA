# Authority gate geometry primitives

Work `A-g06-gate-geometry-20261015-v1`, owner A. Human contract
`DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
Design input: pinned taskbook commit `1011259415a0916054eb580687612580bc1e5f09`,
sections 8.3 and G06. This is an internal A geometry API, not a public ABI
revision or a motion grant. H01–H15 are unchanged.

## Scope and use

`simulation/authority/motion/gate_geometry.py` computes whole-capsule signed
plane support and bounds the farthest radial point of its **instantaneous plane
section**. It validates immutable inputs and the six editor face mappings.
It does not integrate motion, sweep between poses, authorize either topology,
validate the 5 degree passage angle, or implement entered/arrived phases.
An empty section is not proof of passage; a precise section is not proof of
continuous collision freedom. A controller must not receive this truth query.

```python
from competition.deepeye.simulation.authority.motion.gate_geometry import (
    Capsule, Gate, aperture_radius_bounds, plane_support, validate_gate_pair,
)

entry = Gate("front", 0.0, 0.0)
exit = Gate("back", 0.0, 0.0)
validate_gate_pair(entry, exit)  # editor geometry only, no reachability claim
body = Capsule(position_m=(0.0, 0.0, 15.0), axis=(0.0, 0.0, -1.0))
support = plane_support(body, entry.plane)
section = aperture_radius_bounds(body, entry, tolerance_m=1e-5,
                                 max_intervals=4096)
# section.classification == "clear" proves only this one nonempty section fits.
# It must never directly enable motion or set entered/arrived.
```

`Capsule` stores the supplied finite direction vector as an immutable tuple.
Its geometry uses the exact mathematical normalization of that vector, enclosed
by Decimal intervals. Thus multiplying the direction by a nonzero scalar
preserves the solid; its sign cannot affect shape. The caller still owns the
directional meaning of +Z and the signed entry/exit progression.
`Plane(point_m, normal)` follows the same normalization convention.

All scalar inputs are strict built-in int/float (bool rejected), converted to
binary64 once. Coordinates and vector components have absolute bound 1000;
half-segment is in [0,10]m and radius is in (0,10]m. Zero axis/normal, nonfinite
inputs and malformed dimensions are rejected. The gate radius is fixed .15m,
cube faces at ±15m, and |u|/|v|≤14.85m. Input list mutation cannot alter a value.
Numbers mean their exact binary64 values, not a hidden decimal-text rounding
rule. Conversion/asset measurement errors outside this model belong to the
caller’s error budget.

|Editor face|Centre|Outward normal|Existing host face name|
|---|---|---|---|
|top|(u,15,v)|(0,1,0)|+Y|
|bottom|(u,-15,v)|(0,-1,0)|-Y|
|front|(u,v,15)|(0,0,1)|+Z|
|back|(u,v,-15)|(0,0,-1)|-Z|
|right|(15,v,u)|(1,0,0)|+X|
|left|(-15,v,u)|(-1,0,0)|-X|

Same-face entry and exit are legal. `validate_gate_pair` rejects overlapping
same-face circles, using exact rational arithmetic over the encoded inputs.
Touching editor circles at centre distance .30m are permitted, as in
SceneDocument; touching the **drill** to a circle rim never proves passage.
The function does not silently relocate a circle, validate the 1m alignment
volume, or prove a U-turn exists.

## Candidate envelope and whole-body support

The default capsule has segment half-length h=.40m and radius r=.12m:

    K = union of balls Ball(p+t*a, r), for -h <= t <= h.

Its total length is **1.04m**, with pivot bound radius .52m. It contains a
flat-ended cylinder of length .80m and diameter .24m. A capsule whose *total*
length were .80m would miss that cylinder’s flat end edges. The extra .12m at
each end is intentional envelope conservatism; it is not a .1mm approximation
of the rendered model.

`envelope_status` remains `candidate_requires_asset_containment_measurement`.
B must supply and A must independently verify actual visual/collision geometry,
pivot and scaling bounds before this candidate is used as the asset envelope.
The properties here do not constitute that measurement or G01 acceptance.

For outward plane normal n and gate centre g, let s0=n·(p-g). Whole-body signed
support is:

    e = h*abs(n·a)+r
    minimum = s0-e
    maximum = s0+e.

`PlaneSupport` returns outward float bounds for each extremum. Its conservative
`entirely_positive/negative` predicates require strict separation beyond 1pm.
A positive centre or drill tip cannot establish that the tail is outside.
Whether the sign means entry/exit is a separate directional state machine.

## Exact section formula and finite interval bounds

Let P=I-nnᵀ, c=P(p-g), b=P*a, and d(t)=s0+t*(n·a). Feasible ball centres are

    T = [-h,h] intersect {t : |d(t)| <= r}.

For nonempty T the section’s maximum radial distance is exactly

    M = max over t in T of ( |c+t*b| + sqrt(r²-d(t)²) ).

Each sphere contributes a disk in the plane; the farthest point of that disk
is its centre distance plus its radius. Taking the maximum over the finite
segment therefore covers the complete section. For a central 5 degree tilt,
M=.12/cos(5°)≈.12045838m, even though the whole capsule’s projected silhouette
extends to .4*sin(5°)+.12≈.15486230m. The latter would wrongly reject the .15m
hole. Likewise, a finite end-cap section can be smaller than the infinite
cylinder ellipse; omitting caps gives incorrect geometry.

For each closed candidate parameter interval [l,u], convexity bounds the centre
norm by max(|c+l*b|,|c+u*b|). The affine signed-distance interval provides a
lower bound m on |d(t)|, so sqrt(r²-m²) bounds the disk radius above. The sum
of those two independently maximized terms is a valid (possibly loose) upper
bound. Evaluations at parameters proved feasible provide lower witnesses.
The implementation splits the interval with the greatest upper bound first.
It does not assume the objective is unimodal or concave.

## Numerical guarantee for the implemented path

This implementation uses directed interval arithmetic rather than relying on
“60 digits should be enough”:

1. `Decimal.from_float` receives each finite binary64 input exactly. Coordinates
   and axes are copied before computation. Every bound-producing add,
   subtraction, multiplication and division uses explicit precision-60
   ROUND_FLOOR/ROUND_CEILING contexts.
2. Normalization uses interval sums of squares, interval square roots and
   division by a strictly positive length interval. Axial unit vectors are
   handled exactly. No inverse with an interval containing zero is attempted.
3. Decimal square roots round to nearest. `Context.next_minus/next_plus` around
   that result enclose the exact square root. An interval may be intersected
   with nonnegative values only where nonnegativity has already been proved
   (norms, squared distances, or an actually feasible ball-section witness).
4. Feasible parameter clipping uses an outer interval. A near-zero normal
   component keeps the whole segment if division cannot be proved safe.
   Samples outside the proved feasible region never create lower witnesses.
   A negative upper radicand produces UNKNOWN, never a guessed clear result.
5. The global lower bound is a maximum of feasible lower witnesses; the global
   upper bound is a maximum over all surviving candidate intervals. Dependency
   overestimation can slow convergence but cannot turn into false clearance.
6. Sign changes use `copy_negate/copy_abs`, which do not round through the
   ambient Decimal context. A regression test deliberately sets ambient
   precision to six. Python documents these context-independent operations and
   adjacent-number operations in the [Decimal reference](https://docs.python.org/3/library/decimal.html).
7. Export adds outward 1e-20m padding and uses binary64 `nextafter` outward.
   The exported gap, checked with directed Decimal subtraction, must fit the
   requested tolerance. The export padding is extra conservatism, not the
   justification for internal correctness.

These operations give a finite arithmetic-path bound by induction: each
primitive encloses its real inputs’ possible result, and each section bound
encloses all feasible parameter values in its retained interval. Internal
precision therefore affects convergence/width, not a silent unbounded error.
The input bounds, finite binary64 exponent range and finite evaluation budget
stay within the Decimal contexts’ exponent range. Impossible internal interval
states remain exceptions/UNKNOWN and must not be caught by a caller as CLEAR.

Default requested width is 1e-5m; allowed positive widths are at most 1e-4m.
The latter is the taskbook’s overall analytic geometry ceiling, so using all
of it here leaves no allowance for pose conversion or temporal approximation.
Integration must account for those other errors explicitly. Actual asset
uncertainty, Godot numeric tolerance, the mandated .5mm rotational sweep
inflation, and the centre-path chord deviation are **not** proved by this
instantaneous solver. They must not be hidden in this tolerance.

The separate 1e-12m separation guard prevents a coordinate round-off-sized gap
from being used as proof of noncontact; it never expands the hole. Strictly
disjoint support beyond that guard yields EMPTY. A possible tangent section
without a feasible witness stays UNKNOWN. A nonempty section receives CLEAR
only if its upper bound plus the guard is strictly below the gate radius.
Mathematically tangent/ambiguous results cannot pass.

## Result meanings and runtime cost

|status / classification|Meaning|
|---|---|
|empty / empty|Strictly separated from this plane; no section, no passage claim|
|bounded / clear|Proved nonempty instantaneous section strictly inside the hole|
|bounded / contact_or_outside|A feasible radial witness reaches/exceeds the radius|
|bounded / unknown|Precise radius interval still cannot separate contact|
|unknown / unknown|Budget, parameter resolution or section existence unresolved|

For empty/unresolved existence the radii may be null. Otherwise returned
radii are conservative bounds even when computation runs out of budget.
`interval_evaluations` counts interval bounds, not elapsed time. The default
budget is 4096, accepted budgets are integer 1..1,000,000. Exhaustion never
returns clear, even if a partial estimate looks promising.

The solver is synchronous and has no 100Hz deadline guarantee. The authority
should cheaply reject distant planes with support before requesting sections,
cache static data, and measure the actual integrated workload. It must stop on
budget/deadline uncertainty. No performance target is relaxed by this module.

## Verification scope

Run from repository root:

    python -B -m unittest discover -s competition/deepeye/tests/simulation -p test_gate_geometry.py -v

Tests cover finite normal/parallel/tilted/end-cap sections, a sphere, eccentric
contact, all six face mappings and 36 directed pair configurations, complete
signed body support, tangency guards, budget exhaustion, invalid values,
immutability and ambient context isolation. This is not 36 complete routes.
The separate private review compares against independent precision-120 closed
forms and measures elapsed times; raw results retain their scope.

Required next work remains actual B envelope validation, continuous swept-body
tests including tail scrape/thin layers, entry/exit state machine, authenticated
mode grants and expiry, real physics/viewer linkage and process isolation.
Pure primitives do not close G06, R03, 1000 executor cases, game performance,
either complete control chain or any board acceptance.

Independent review of this checkpoint checked 363 sections, 128 arbitrary
plane supports and actual Godot mappings for all six faces without finding a
false conservative bound or false CLEAR. It also identified two integration
blockers that remain open: the current static greybox cone extends to local
Z=0.62m while this candidate ends at Z=0.52m, so the candidate does not contain
that complete visible asset; and the independently measured 0–5 degree
eccentric workload reached 21.04ms, with 19 of 64 calls over 10ms. Do not bind
this candidate to that asset or call the precise solver a verified 100Hz path.
These observations refer to the source checkpoint recorded in the evidence,
not to a later corrected or final B asset.

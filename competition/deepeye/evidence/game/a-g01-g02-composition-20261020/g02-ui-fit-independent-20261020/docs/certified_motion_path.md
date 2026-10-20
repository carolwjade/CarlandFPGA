# Canonical certified motion path — internal numeric contract

`simulation/authority/motion/certified_path.py` derives an entire analytic
centre/orientation path and its gate-clearance slice bounds from one newly
validated raw command. It accepts no caller `MotionStep`, curvature, arc length
or rotation upper bound. It does not apply a transform or issue a motion grant.

H01–H15 remain unchanged under `DEEPEYE-HUMAN-LOCK-20261014/revision1`, pinned
requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
The A Desktop generation-2 director owns integration and acceptance.

## API and authority boundary

```python
path = CanonicalPath(
    start_state, profile, speed_code, yaw_q, pitch_q, dt_ns,
    inherited_errors=ErrorBounds(position_error_m, angle_error_rad, additional_margin_m),
    error_budget_reference="explicit source/version of those asserted bounds",
)
sample = path.sample(integer_elapsed_ns)
plan = path.plan(
    start_monotonic_ns=actual_start,
    deadline_monotonic_ns=actual_deadline,
    hard_stop=observed_stop,
)
```

`dt_ns` is an integer from 1 through 10,000,000; samples include both endpoints.
Position coordinates are finite binary64 values within ±1000 m. A `RigidState`
has already rejected nonfinite positions/quaternions/speeds and bools. This
factory requires that exact immutable type, revalidates integer raw codes and
the selected profile ceiling, and bounds the actual resulting binary64
curvature. Bool is not an integer time/code. Error bounds and their nonempty
reference are required, including explicitly justified zero in mathematical
fixtures. Invalid input or an unexportable bound raises; an exception cannot
authorize motion.

The immutable provenance retains raw codes, newly validated `MotionCommand`,
the original `RigidState`, requested duration, inherited errors, their reference,
derivation version and exact command semantics. It is a numeric record, not an
authenticated registry. Python `frozen`, a string, a version, or a file hash
cannot establish source ownership. The current module does not accept or verify
an authority grant, world revision, scene hash or clock observation.

`CertifiedPlan.motion_grant` and `authority_authenticated` are always false.
It retains timestamp/STOP inputs and the complete provenance. `slices` are an
immutable tuple; consecutive slices share the same endpoint sample object.
There is no `entered`, `arrived` or gate-phase inference, including for an empty
slice set or an empty plane section.

Each `CertifiedSlice` contains start/end samples, exact rational arc length,
the outward path arc bound, derived `gate_clearance.SliceBounds` and combined
`ErrorBounds`. Use `Capsule(slice.start.state.position_m, slice.start.axis, ...)`
with these exact derived gate bounds/errors. Asset dimensions, pivot and the
actual volume proof remain separate required inputs. Do not substitute another
position/axis, collider, state or scene and reuse the certificate.

## Canonical path semantics and exact speed integration

The canonical path means the exact mathematical values of the **newly
validated command's binary64 fields**, the exact initial position/speed and
the **exact mathematical normalization of the stored initial quaternion**.
The earlier `kinematics.MotionStep` libm samples are not this canonical path.
No legacy `_pose`, sample or `advance` is called to create certified endpoints.

For exact rational time `t = elapsed_ns / 10**9`, define

```
v0 = Fraction(start.speed_m_s)
vt = Fraction(validated.target_speed_m_s)
a  = sign(vt - v0) / 4
tr = 4 * abs(vt - v0)
u  = min(t, tr)
S(t) = v0*u + a*u*u/2 + vt*(t-u)
v(t) = v0 + a*u    for t < tr, otherwise vt
```

These calculations are exact `Fraction` arithmetic. Nonnegative speed is
bounded by the selected validated profile. All slices use this same original
function, never a sequence restarted from rounded substep speeds. Code zero
brakes according to this law; explicit hard STOP advances nothing.

`CertifiedSample.exact_distance_m` and `exact_speed_m_s` preserve the rational
values. The binary64 output speed has a separate outward
`speed_export_error_m_s`. The later cross-step authority must choose and record
its velocity-state semantics and propagate any export error; it cannot silently
treat rounded output speed as exact continuation of the previous path. This
module's inherited pose error does not claim to bound an unknown initial speed
or command error. The canonical start speed and command are exact by definition.

An executable consumption rule for the next runtime is:

1. Within one step, consume the same `plan.slices` and original path. Do not
   create a new path per slice.
2. Across committed steps, retain an authority-owned upper bound `epsilon_v`
   on physical/canonical continuous speed versus the next nominal binary64
   speed. It must have an explicit source; zero is not an automatic reset.
3. With `T = Fraction(next_dt_ns, 10**9)`, enlarge the previous end sample's
   propagated position bound by `epsilon_v*T`, and its angle bound by
   `Fraction(1, 2)*epsilon_v*T`, rounding each sum outward. Pass those enlarged
   errors explicitly to the new path, preserving the additional margin and
   a reference to the carry record. Use the previous **committed** end state;
   speculative or rejected plans are not continuation seeds.
4. After committing the next plan, retain its `end.errors` and update
   `epsilon_v_next = epsilon_v + Fraction(end.speed_export_error_m_s)`
   outward (or use a separately proved tighter interval). Never discard this
   carry because a new `CanonicalPath` or `RigidState` was constructed.

The following arithmetic illustrates step 3; it has no authority side effect:

```python
from fractions import Fraction
from math import inf, nextafter

def up(value):
    return 0.0 if value == 0 else nextafter(float(value), inf)

T = Fraction(next_dt_ns, 10**9)
position_carry = up(Fraction(previous_end.errors.position_error_m) + epsilon_v*T)
angle_carry = up(Fraction(previous_end.errors.angle_error_rad) + epsilon_v*T/2)
next_errors = ErrorBounds(position_carry, angle_carry,
                          previous_end.errors.additional_margin_m)
```

Here `epsilon_v` is a nonnegative exact rational from the retained record. This
rule is justified because acceleration toward a fixed target at rate .25 is
1-Lipschitz in initial speed. Consequently the full-step arclength difference
is at most `epsilon_v*T`; the centre-position difference is no larger, and the
pose-angle difference is at most `K*epsilon_v*T≤0.5*epsilon_v*T`. These are
uniform pose perturbations around the new canonical path, so they also cover
its intermediate times. The existing inherited-angle displacement term may
overcount them, conservatively. The runtime must prove both speed trajectories
stay in the selected profile domain, reject an invalid profile transition,
and fail closed if combined errors exceed accepted domains/budgets. This
documented carry algorithm is a required integration rule, not an implemented
authenticated carry registry or a claim about unknown actuator errors.

For command components `ky, kp`, derive `K = sqrt(ky² + kp²)` with outward
arithmetic and reject unless its upper bound is ≤0.5/m. The centre curve is the
constant-curvature rigid exponential with body +Z forward and body rotation
vector `(-kp, ky, 0)` per metre. Its arclength curvature is `K`. A speed ramp
changes time parameterization, not the spatial curve. The curve has a smooth
arclength extension through stopped times.

## Whole-domain pose enclosure

Let `s = S(t)`, `theta = K*s` and `sinc(x) = sin(x)/x`, continuously extended at
zero. The relative quaternion and local translation are

```
dq = (-kp*s/2*sinc(theta/2), ky*s/2*sinc(theta/2), 0, cos(theta/2))
dp = (ky*s²/2*sinc(theta/2)², kp*s²/2*sinc(theta/2)², s*sinc(theta))
q  = normalize_exact(q0) * dq
p  = p0 + rotate(normalize_exact(q0), dp)
```

Every step is at most 10 ms and speed at most 0.25 m/s. Therefore `s≤0.0025 m`
and `|theta|≤0.00125 rad`. This is a bound for every real time in the step,
not an inference from sampled endpoints.

The even polynomials through term `j=4` for sinc and cosine, with their next
alternating term subtracted for the lower bound, enclose the functions on the
entire domain. In detail the sinc remainder is at most `x^10/11!`, and cosine's
is at most `x^10/10!`. Successive positive term magnitudes decrease on this
domain. Square arguments avoid an unnecessary angle square root. Exact zero
uses the removable singularity; subnormal movement/curvature is never dropped
through an epsilon threshold.

All proof arithmetic uses the reviewed internal `gate_geometry._Interval`
helpers and explicit Decimal precision-60 FLOOR/CEILING contexts. Rational
division is enclosed, square-root neighbours enclose correctly rounded roots,
and interval quaternion normalization/multiplication/rotation encloses the
exact expressions. This is an intentional private-module dependency, not a
new public ABI. Calls do not depend on the ambient Decimal precision, rounding,
exponent limits or traps, including cold import. As with the other Python
internal modules, mutating their private global contexts is outside this
contract and is not prevented by an authentication mechanism.

Nominal position/quaternion values come from interval midpoints. `RigidState`
may normalize the emitted quaternion again. The module compares the **final
returned value**, exactly normalized, with the canonical quaternion interval.
It proves the matching quaternion hemisphere, then bounds SO(3) error by
`3*d` where `d≤1` is their unit-quaternion chord (`4 asin(d/2)≤3d`).

The emitted body +Z axis is computed from that returned quaternion, converted
to floats and exactly normalized again using the same semantics as `Capsule`.
Its independent angular bound is `2*d_axis` (`2 asin(d_axis/2)≤2d_axis` for
`d_axis≤1`). Axis export is not assumed free. Position error is the interval
Euclidean bound on the distance to the final returned position.

Every nonnegative bound is exported with a binary64 `nextafter` toward +∞.
An exact zero stays zero; a positive value underflowing on conversion becomes
at least the smallest positive subnormal. There is no fixed rounding pad which
could erase or overwhelm a 1 ns/subnormal exact distance. The per-sample
calculated bounds, rather than the largest observed test error, are the evidence.

## Integer scheduling, deadline and continuous slice geometry

The scheduler includes both floor and ceil integer-nanosecond neighbours of
the exact target-speed time when interior to the plan. The speed law itself
is never rounded to either boundary. It then chooses maximal integer endpoints
whose **exported** whole-slice rotation bound satisfies `Theta≤pi/3600` (0.05°).
The pi bound comes from gate clearance's exact-rational Machin/alternating-series
interval. Testing the exported float prevents a final outward rounding from
silently exceeding the limit.

`Theta = K*(S(t1)-S(t0))` bounds the entire rotation relative to the slice start;
it is not a start/end net-angle measurement. Times are contiguous, strictly
increasing integers with no zero-duration slice. A numerical export correction
is covered by pose uncertainty, not asserted to be a physical angular-velocity
path. The eventual executor must follow this canonical path and must not insert
arbitrary intermediate rotations between certified samples.

The current expiry convention is `now >= deadline`. Numeric planning therefore
covers at most `min(requested_dt, deadline-start-1)` ns, clamped at zero. Hard
STOP yields no slices and preserves the original state. A stationary command
may still cover time with zero arc length. These tests establish input/output
semantics only; they do not verify actual watchdog or clock provenance.
In particular a duration-zero result is `sample(0)` and **retains the input
speed**. It proves no numerical advancement. It does not establish completion
of a real STOP, braking, velocity reset, epoch invalidation or queue flushing.
The authority runtime must separately perform its specified STOP state/epoch
transition before it can permit any subsequent command.

Two lengths are retained:

* `path_arc_upper_m` encloses the exact physical centre arc.
* `gate_bounds.arc_length_upper_m` encloses the larger of that arc and the
  distance between exported nominal endpoints.

For example, at `pz=17`, speed .25 and 1 ns, the true arc is 2.5e−10 m, while
the rounded nominal endpoint chord is about 2.5000090886351245e−10 m. Enlarging
the gate length addresses the chord precondition and remains a valid upper
bound on physical arc. The explicit endpoint error remains required; it is
not replaced by that length enlargement.

For a centre curve with arclength curvature ≤K, its deviation from the endpoint
chord at matching arclength fraction is ≤`K*L_path²/8`. Replacing L_path by the
larger L_gate preserves the bound. Linear interpolation of two endpoint export
errors is bounded by their maximum. Existing gate clearance additionally uses
`max(0.0005, Rb*Theta)` for full-body rotation and its explicit remaining margins.
Thus the adapter supplies complete-path quantities, including tail rotation
and curve sag, without accepting an external caller's invented κ/L/Theta.

## Inherited errors and remaining integration

If the original position error is `ep` and full initial pose angle error `ea`,
the original orientation uncertainty displaces the integrated centre by at most
`2*S*sin(ea/2)≤S*ea`. A slice therefore carries

```
position = ep + S(slice.end)*ea + max(numeric_start_pos, numeric_end_pos)
angle    = ea + max(numeric_start_orientation, numeric_start_axis)
additional_margin = explicit inherited additional_margin
```

All sums/products are outward. The full original distance, not just the current
slice's length, propagates initial orientation error. The slice angle concerns
its fixed start frame; the complete canonical rotation is already in Theta.
The returned end sample separately carries its own full position/orientation/
axis error. Unknown source/engine/asset margins cannot be silently set to zero.
Combined errors outside `ErrorBounds`' finite domains raise conservatively.

The next authority factory must bind the records to actual command/session/
control epochs, observation/capture/grant validity, source monotonic deadline,
state and scene revisions, complete asset/pivot/scale/axis proof and policy
versions. It must verify all initial overlaps and actual whole-volume engine
queries, then recheck fresh STOP/deadline and state/scene CAS before applying a
transform. On a failed query, stale state, expiry or STOP it must not advance.
These requirements are not implemented by this numeric module.

The previous capsule candidate `h=.4, r=.12` is 1.04 m end to end and requires
the corresponding tested asset containment. This work does not certify final
B assets or engine error, nor claim the full 0.1 mm asset/engine error budget.
Initial overlap, thin layers, rotation tail contact and contact equality still
need actual Godot validation. No 3D/UI or dual-control requirement is removed.

## Verification evidence

Public tests cover exact speed ramps, fractional target cuts, 1 ns acceleration,
subnormal braking, still versus hard STOP, deadline equality, all 1–10 ms steps
and profiles, complete rotation, signed/rotated circle paths, quaternion signs,
separate export errors, nominal-chord excess, inherited drift, immutable
provenance, illegal inputs and hostile Decimal contexts. An independent
closed-form circle test avoids using the interval implementation as its oracle.

Author-private evidence is under the root workspace
`.planning/deepeye-implementation-a/certified-path-20261016/`. It includes the
original missing-module RED, failed invocation/fixture logs, corrected GREEN,
an independent Decimal160 direct sin/cos plus rotation-matrix oracle, mutation
logs, source hashes and raw timing distributions. The finite-precision oracle
allows 1e−140 comparison tolerance, which is not a product error budget.

The initial independent run checked 330 models, 434 slices, 3298 distinct path
samples and 3906 intermediate chord-envelope cases, including 142 nominal
chords larger than the physical arc. Eleven mutations of acceleration,
deadline/STOP, tiny motion, curve/rotation bounds, chord representation,
inherited error and target cuts were rejected after a passing baseline.
The corrected public regression ran 112 tests successfully. Serial numeric
factory/plan timing is recorded separately; it excludes Godot, world/grant CAS,
other gate/obstacle queries and concurrent load, and is not a 10 ms deadline
guarantee. Independent review and full G06 runtime acceptance remain separate.

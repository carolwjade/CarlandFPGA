# Exact solid clearance kernel

`simulation/authority/motion/solid_clearance.py` is an authority-internal
**sufficient geometric certificate**, not a movement grant. It is not connected
to Run, the game process, a real command/path factory, B's mesh importer or a
scene registry. H01–H15 remain unchanged under
`DEEPEYE-HUMAN-LOCK-20261014/revision1`; pinned requirements SHA256 is
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## Corrected rotation policy

The earlier private `conservative-collision-design-20261016/prototype.py` used
only `Rb*Theta`. Its curved example total `.0004640724287400073m` is below the
taskbook section8.3 required rotation allowance even before adding other errors.
That directory, receipt and logs are preserved unchanged as historical evidence.
The new work `A-G06-solid-clearance-20261016-v1` records an actual failing
regression against those original bytes, and a passing product regression.

For a whole interval the new budget, in metres, is exactly

```
rotation = max(1/2000, Rb*Theta)
arc      = kappa*L*L/8
pose     = Rb*pose_angle
total    = rotation + arc + position + pose + numeric + asset + obstacle
```

`Theta` and `pose_angle` are radians. `Theta` must bound the entire orientation
path relative to its start (total angular variation suffices), not the net
endpoint quaternion difference. `L` is a verified upper bound on centre-curve
**arc length**, not chord length. The constructor checks `L >= chord`; that
necessary check does not verify the actual path. Curvature bounds require a
continuous arclength tangent with `|dT/ds| <= kappa`. The path factory must enforce
the taskbook substep angle <=0.05 degrees; this mathematical module also encloses
larger supplied bounds but cannot authorize such a product step.

`ErrorBounds(position, pose_angle, numeric, asset, obstacle, source)` requires
every value and a nonempty provenance label. Zero has no implicit default.
Explicit zero in tests means an exact fixture assumption; no numeric margin is
claimed measured. Runtime error calibration and evidence are still required.
Shape kind, material policy and evaluation stage require exact built-in strings.
String subclasses are rejected before sealing or dispatch, so custom equality
cannot change geometry or forbidden-material policy while retaining the same
serialized digest, or make a full-interval request select the initial stage.
`obstacle` is a uniform upper bound on static obstacle transform/model error;
using a per-scene worst-case bound is conservative. It is added as a ball margin,
not by enlarging ellipsoid semiaxes (which is not a general ball offset).

`Rb` is explicitly supplied with the immutable capsule model. The constructor
checks `Rb >= half_segment + radius` for the declared central-pivot capsule.
This does not measure the actual B asset, verify its pivot, or prove its
containment. Actual complete visual/collision model and pivot evidence remain
G01 dependencies. Asset/pose/error assumptions must cover the entire interval.

## Complete body and interval proof

Let the nominal capsule have axis endpoints `p ± h*u` and ball radius `r`.
Translating its fixed starting axis along the full endpoint chord yields exactly

```
conv(p0-h*u, p0+h*u, p1-h*u, p1+h*u) + ball(r).
```

No endpoint-only contact test is substituted for that convex sweep. Rotation
displacement of a point within `Rb` is at most
`2Rb*sin(theta/2) <= Rb*theta`. The error between a curve and its endpoint
linear interpolant is at most `kappa*s*(L-s)/2 <= kappa*L²/8`: the interpolation
Green kernel is nonnegative and the arclength second derivative has norm <=kappa.
These are 3D norm bounds. Minkowski addition and the triangle inequality let the
independent margins add. Under the caller's stated assumptions, the resulting
inflated sweep covers every intermediate body point.

The **initial** stage separately uses the complete starting capsule, inflated by
position, pose, numeric, asset and obstacle uncertainties. It excludes the future
rotation and arc terms. Every scene piece needs initial and full certificates.
No strict certificate means UNKNOWN, not proof that the actual body overlaps.
A certified exact common point could support a future contact classification;
that feature is not implemented here.

## Encoded solids and support proof

All inputs are copied into frozen dataclasses with nested tuples. Finite floats
are treated as their exact encoded binary rationals; they are not rounded to
their displayed decimals. Decimal strings and Fractions encode exact rationals.
The quaternion `xyzw` is normalized algebraically by its exact squared norm,
without an approximate square root. The resulting rational matrix is exactly
orthogonal for the encoded nonzero quaternion. All support queries use `R^T*n`.

`Solid(model_id, version, kind, centre, dimensions, quaternion, vertices=())`
describes one **closed filled** convex solid. Dimensions mean:

| kind | dimensions | support extent in local direction m |
|---|---|---|
| box | three half sizes | `sum(abs(d_i*m_i))` |
| ellipsoid | three semiaxes | `sqrt(sum((d_i*m_i)^2))` |
| cylinder | two elliptical radii and half length on local Z | `sqrt((a*m_x)^2+(b*m_y)^2)+c*abs(m_z)` |
| polytope | positive per-axis scales of supplied local vertices | `max(dot(vertex, d*m))` |

Polytopes are the full-dimensional convex hull of their vertices. Zero volume,
unknown kinds, extra vertices on non-polytopes and zero quaternions reject input.
A cylinder is the entire filled outer cylinder, including caps; it is not a
hollow visual ring. A cavity ellipsoid is its entire prohibited volume. A
nonconvex asset is a union of declared convex pieces, with every piece separately
checked; taking one large convex hull would incorrectly close free channels.
Irregular B shapes still need validated decomposition and containment/error
proofs. Merely calling a fixture `water` or `casing` does not establish that map.

For any nonzero encoded normal n, the sole certificate issuer computes

```
US = max(dot(endpoint_i,n)) + inflated_radius*sqrt_upper(dot(n,n))
LO = -support_upper(obstacle,-n)
gap_lower = LO-US
```

All additions/products/comparisons are exact Fraction arithmetic. Square roots
are enclosed upward using integer `isqrt` on a `2^-96` rational grid. If
`k=floor(sqrt(q)*2^96)`, return `k/2^96` only when its square equals q exactly,
otherwise `(k+1)/2^96`. Thus `US` is an upper support bound and `LO` a lower
bound. **Only `gap_lower > 0` issues a certificate**. For all sweep points a and
obstacle points b, `dot(n,b-a) >= gap_lower > 0`, proving disjointness.
Tangency, invalid normals, wrong directions, exhausted budgets or numerical
proposal failures cannot pass this test.

The kernel's trusted core is input normalization, exact rigid transforms,
complete sweep construction, outward support bounds, strict gap comparison and
scene completeness/policy composition. Floating support/GJK/simplex arithmetic
is only a direction proposer; it has no authority to return CLEAR. Coordinate
axes form a cheap certified broadphase because their gap is rechecked exactly.
A cached normal is likewise rechecked against all current inputs each step.
There is no cached CLEAR result and no cache populated by this module.

## Binding, completeness and material policy

Canonical SHA256 includes `KERNEL_VERSION='solid-clearance-v1'`. Model and shape
IDs/versions, every encoded geometry/path/error field, error-source label and
the independent full scene manifest are hashed. A plane certificate binds the
sweep digest, solid digest, initial/full stage, proposed normal and context.
`certify_scene` supplies the full scene digest as context, including material,
superhard policy, every declared piece and its full model/version/geometry.
Its result binds sweep plus complete scene. A standalone `check_plane` with
empty context proves only that encoded geometry pair, not a scene policy.
Certificate values can be rechecked by `recheck_certificate`; changing even a
normal, gap, version, error, shape or scene context invalidates that record.
Hashes bind encoded inputs, not truth, authorship, asset correctness or calibration.

`Scene(scene_id, version, manifest, objects)` must receive an **independent**
frozen manifest of `(object_id, (piece_id,...))` from the future trusted registry.
Its full validation precedes every query: object IDs and per-object piece IDs
must be unique, expected/actual sets must match exactly, every piece must be a
supported immutable Solid, and every material must be known. Missing objects,
missing pieces, duplicate IDs and unsupported shapes reject the whole scene.
An empty scene is valid only with an independently empty manifest. Deriving the
expected set from the supplied actual objects would defeat completeness; this
module cannot prove how its caller obtained the manifest.

Forbidden bodies (`casing`, `fault`, `void`, `water`, superhard rock) are checked
before ordinary rock, preserving material ordering within the forbidden set.
Their union cannot be erased by overlapping higher-priority drillable rock.
Every convex piece needs strict initial and full separation. Any missing
certificate gives UNKNOWN. Ordinary rock lacking separation instead gives
DRILLING_REQUIRED after forbidden checks; it is neither a permanent prohibited
product zone nor permission to traverse. The independent load/consumption/speed
drilling state machine remains required. All result types have
`motion_grant=False`.

## Work limits and caller contract

`separate(sweep, solid, stage='full', context='', limits=Limits(), cached_normals=())`
and `certify_scene(sweep, scene, limits=Limits())` operate on exact immutable
types. Invalid inputs raise; the caller must stop/reject the complete scene or
command, never omit the invalid piece or reinterpret exceptions as clearance.

Default limits are64 verified normals per pair,24 float support-proposal
iterations,2048 initial/full pairs and200000 support-term work units per scene.
Scene preflight uses both phases for every declared piece, including rock, and
rejects an over-budget scene as UNKNOWN before checking any subset. A pair cost
is estimated as `4 + vertex_count` for polytopes or `4+3` for primitives, times
`max_normals+proposal_iterations`. These are structural accounting units, not
CPU instructions or a time bound. GJK retains at most4 simplex points plus one
new point, examines at most30 nonempty faces and solves systems at most5x5.
Constructors/hash/full-rank checks are linear in supplied geometry size.

No64-vertex/16-piece cap or shape/rotation/size reduction is imposed. Finite
encoded scalars have a4096-bit arithmetic resource limit. Geometry outside the
configured work/encoding budget stays unaccepted as a whole; the importer must
extend the bounded implementation or provide a proved representation covering
the released domain, never silently simplify, truncate or omit a B asset.
Exact input caps and configured work limits are not formal100Hz acceptance.

## Current evidence and remaining dependencies

Private evidence is in the owning checkout's
`.planning/deepeye-implementation-a/solid-clearance-20261016/`. Historical RED,
source snapshots, per-stage source hashes, commands, exit codes, raw stdout/stderr
and the final receipt are preserved there. The suite covers the mandatory floor
and separate margins, initial/full interval, strict tangency, thin layers, tail,
caps, filled volumes, arbitrary quaternion/nonuniform support, polytope scales,
compound channels, manifest failures, stale direction/cache records and rock
versus forbidden policy. Independent rational/precision160 expectations do not
use the tested support implementation as their oracle.

The final764 analytic fixtures observed zero false CLEAR results:45 contacts
were never clear, and709/719 known-clear cases were automatically certified.
Ten tiny positive-gap cases remained UNKNOWN; direct independently derived
exact feature directions certified all ten. They are diagnostic certificates,
not automatic proposer completions. The corrected continuous-circle fixture has
rotation exactly0.5mm plus separate nonzero arc/pose/position/numeric terms: the
old near-X=.1205 fixture is now UNKNOWN, near-X=.1206 still obtains a strict
certificate, and the exact actual-contact fixture is never clear. These are
mathematical capsule paths, not product execution evidence.

Sixteen final30-object clear queries (60 initial/full pairs each) took
6.8386–8.5617ms; sweep construction/hash took additional measured time. The first
proposer revision's full timing is retained, including an18.7538ms scene outlier.
The final hard pair fixtures reached15.2192ms. These observations do not prove
WCET or100Hz with sensing/rendering/AI; no deadline or Run grant is claimed.

Remaining dependencies: formal B mesh/model importer and full-domain containment,
Hausdorff excess and pivot evidence; frozen registry and approved revision/source
binding; real-command whole-interval path and calibrated error factories;
independent drilling semantics; all-six-face workspace and entry/exit gates;
atomic state/lease/revision movement commit; truth isolation/process boundary
and causal sensor-only AI feedback; actual game traces and both control chains;
full G06 acceptance and100Hz under simultaneous workload. This module exports
no AI-facing collision query endpoint and creates no hypothetical-path oracle.

# Fixed-orientation Godot collision query probe

Work `A-G06-Godot-cast-probe-20261015-v1`, A-owned. Contract
`DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements canonical SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
H01–H15 and taskbook8.3/G06 remain unchanged.

`simulator/physics/motion_cast.gd` provides an authority-internal **query
foundation**, not a motion executor or permission. The real target binary
demonstrably misses some swept contacts. Therefore there is deliberately no
CLEAR result: an observed hit returns `collision_attempt`, and no hit returns
`unknown`. Every result has `motion_authorized: false`. Contact attempts reject
the entire requested step; the reported safe fraction is diagnostic and must
never be applied as allowed progress.

This is a fixed-orientation expanded translation cast. It supplies neither
rotating CCD, full entry/exit phases, gate openings, observation/mode grants nor
complete G06 acceptance. The existing viewer/editor/Run bridge is not connected.
Collision truth/results must stay in the A authority process, away from AI inputs.

## API and explicit shape expansion

```text
expanded_capsule(rho=.0005, numeric_guard=0) -> Dictionary
query(space, body_pose, motion, rho=.0005, numeric_guard=0,
      collision_mask=1, exclude=[], max_results=32) -> Dictionary
```

The base capsule has segment half-length h=.4m, radius r=.12m, total height1.04m.
For requested spherical expansion e=rho+numeric_guard:

    radius' = r + e
    height' = 2h + 2(radius') = 1.04 + 2e

Both dimensions change; merely changing `query.margin` would not implement this
construction. Shape margin and query margin are explicitly0. Radius is rounded
outward to binary32, then height is rounded outward using the actual stored
radius so the stored half-segment never shrinks. The tiny extra half-length from
height quantization is reported; it is not hidden in the nominal h.

|rho, guard0|Actual radius m|Actual height m|Actual half-segment m|
|---|---:|---:|---:|
|0|.120000004768371582|1.040000081062316895|.400000035762786865|
|.0005|.120500005781650543|1.041000127792358398|.400000058114528656|

The mathematical body forward is +Z, while Godot's capsule axis is +Y. The exact
integer basis columns `(RIGHT, BACK, DOWN)` map +Y to +Z with determinant+1;
the query transform is `body_pose * shape_to_body`. It avoids a trigonometric
90-degree rounding residue. All tested identity/oblique mappings reported zero
native axis mapping residue; that is an observed sample result, not a general
pose conversion certificate.

Accepted origins have components≤32m in magnitude, finite motion length≤64m,
rho and numeric_guard each in[0,.01]m, nonzero32-bit collision mask, at most256
exclusion RIDs and result cap1..256. Basis lengths/dots must lie within the
explicit2e-6 orthonormality residue thresholds, determinant within4e-6 of+1.
Those checks do not certify a pose error budget. Invalid/null space, nonfinite
values, scale/shear outside that range or invalid exclusion types return unknown
before querying. The caller owns actual space synchronization and valid RID
lifetime. Areas are excluded; only the requested body mask/filter set is tested.

## Query ordering and result meanings

1. Query initial overlap independently with zero motion.
2. Call `cast_motion` with the full requested translation and fixed orientation.
3. Query endpoint overlap separately for diagnostics. Endpoints never replace
   the cast; the tests include a thin slab crossed between disjoint endpoints.

The interface saves counts, collider IDs/shape indices, fractions, dimension
readbacks, filter/exclusion metadata and result-cap flags. If either overlap
count reaches the cap, enumeration may be truncated and `query_complete=false`.
Any known hit still rejects the entire step. A list below its cap plus valid
fractions only means the three API queries returned usable structures;
`query_complete=true` does **not** certify world clearance or contact precision.
Filter/exclusion results never describe objects outside that filter.

Fractions must be finite, length2 and ordered within[0,1]. Malformed/empty casts
cannot produce clearance. Known overlap/hit evidence is never overwritten by a
later empty query. Engine-side script/API errors require inspecting stderr;
GDScript does not provide a general exception catcher for native physics errors.
No branch can turn an unreported native error into permission.

There are at most three synchronous space queries per valid request. Result
lists and inputs are capped. This is not a wall-clock or100Hz deadline guarantee:
the engine's broadphase work also depends on the world. Test subprocesses are
bounded independently; the production primitive does not claim to interrupt a
stalled native call.

## Target binary and offline official API reference

The existing official engine reports `4.7.2.stable.official.ed1daf0bf`, executable
SHA256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`.
No network, downloads or installation were used. The official binary's
`--doctool` output supplies the signatures/defaults for `PhysicsDirectSpaceState3D`,
`PhysicsShapeQueryParameters3D`, `CapsuleShape3D` and `Shape3D`; generated XML is
retained under the assigned private evidence `official-docs` directory.
This stripped runtime emits blank prose descriptions. Detailed behavioral claims
below consequently come from actual target-binary measurements, rather than
invented text from those empty descriptions.

The product setting reads `physics/3d/physics_engine = DEFAULT`; the runtime
server class reports `PhysicsServer3D`. The initial probe left the native
implementation unresolved. A subsequent independent review mapped the exact
official binary commit's registration and selection code and compared explicit
backends: DEFAULT and GodotPhysics3D produced identical results for all45 rows.
This identifies Godot Physics for this pinned project/binary, rather than a
general statement about new projects. No global collision tolerance is certified.

## Actual tests and independent oracles

`simulator/tests/test_motion_cast.gd` creates real `StaticBody3D` fixtures with
Box, Cylinder and Capsule shapes. Two physics frames and one process frame
synchronize each fixture before querying. Tests cover:

- Initial surrounding/contained overlap; zero movement with and without overlap.
- Head, side, tail and oblique capsules; translated diagonal movement; full
  passage through a thin slab with clear start/end poses.
- Parallel cylinder/capsule obstacles, eccentric end-cap/edge contact, exact and
  ±1/2/10/100/1000µm perturbations, plus endpoint/initial contact perturbations.
- Explicit masks and RID exclusions. Nine real overlapping bodies produce4
  results with cap4 and9 results with cap16; the capped query marks incompleteness.
- Outward dimension storage, explicit guard expansion, invalid transform/mask/
  expansion/cap/exclusion inputs and preservation of the adapter's own hit evidence.

Expected contacts are derived independently. For a broad plane at normal
coordinate a, capsule centre c, axis u and translation v:

    t_contact = (a - n·c - h|n·u| - R) / (n·v).

With h=.4,R=.1205,2m movement and a=1: head/tail fractions.23975,
side.43975, axis(.6,0,.8) against+Z plane.27975. Parallel cylinder radius.1
gives.38975 and parallel capsule radius.08 gives.39975 for the chosen fixtures.
These predictions are not obtained from production query results.

For fixed+Z motion against an eccentric axis-aligned box whose nearest X is a,
the first end-cap contact is

    t_contact = (z_near - h - sqrt(R²-a²)) / 2,

when a≤R and the returned fraction is in[0,1]. A private precision100 Decimal
analysis separately reconstructs the **actual binary32** box position/size and
the raw/adapter capsule radius/height, rather than treating nominal decimals as
the same geometry. Raw and adapter shapes differ and are measured separately.

## Measured blockers: no safe-fraction clearance certificate

The final run completed45 fixture rows and178 behavior checks with0 failures.
The existing editor suite separately remains696/696. PASS means the probe
preserves its fail-closed contract and records the engine behavior; it does not
mean every engine collision query was geometrically correct.

For the23 fixed-axis grazing/end-cap cases independently classified from actual
encoded geometry:

|Query shape|Analytic contacts|Unreported contacts|False-positive hits|
|---|---:|---:|---:|
|Raw nearest-stored capsule|12|6|5|
|Outward-stored adapter capsule|13|7|2|

All7 adapter unreported contacts returned unknown and never authorized movement.
Detected hits are also not permission for fractional advance. In the
`grazing_rho_0.0005_um_-2.0` counterexample, the actual adapter first-contact
fraction is approximately.299653120616146747, but the API returned
`[.4453125,.44921875]`. Applying its reported safe fraction would advance about
.2913187588m past first contact. The maximum observed early stopping distance
for the same23-case subset was about.00641532m for the adapter. Misses are counted
separately from fraction errors; no-hit `[1,1]` is not a valid safety bound.

A separate direct-space probe reproduces three counterexamples without calling
the adapter. At the -100µm,rho=.0005 fixture, cast returns`[1,1]`, yet independent
`intersect_shape` calls at path fractions.299,.3,.31,.4 and later return overlap.
The -10µm,rho0 case similarly has clear endpoints and overlaps at.3 onward while
cast returns`[1,1]`. The -2µm case has an overlap at.3 despite the reported safe
fraction.4453125. Exact fixture inputs, readbacks, calls and raw logs are retained.

These are specific reproducible observations, not a global engine error bound.
They block using this backend/profile's no-hit or safe fraction as a G06 sweep
certificate. There is no frozen positive engine clearance margin. The.0005m
candidate addresses only the rotation-envelope term; it must not absorb unknown
engine precision, asset/pivot, pose or centre-arc errors. This work does not
change taskbook tolerance or hide misses by enlarging an acceptance threshold.

An independent exact-rational segment-to-AABB distance oracle reproduced the
contact counts and late fraction. Its138 direct-space query rows across three
backend selections and an additional10 physics frames excluded adapter/filter/
synchronization mistakes for these fixtures. Jolt detected all12 raw contacts
but missed1 of13 adapter contacts: the actual binary32 lateral gap equals the
radius exactly, so this is strict tangency, not penetration. Switching to Jolt
alone therefore does not satisfy the required closed-set contact rule.
The independent receipt SHA256 is
`ff3d9032a212487e3e41a4ee41a641d8cd232a8367ca1777101b80ffc8b46b57`,
retained in A's private `godot-collision-independent-review-20261016/` directory.
The precise backend mapping uses the official
[registration source](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/modules/godot_physics_3d/register_types.cpp)
and runtime differential evidence. It does not identify one unique internal
GJK early-exit branch or prove any universal numeric error bound.

## Reproduction and remaining work

Copy the simulator sources, excluding `.godot`, into a caller-owned private
directory; never import the product input tree during evidence collection:

```text
GODOT_EXE --headless --path PRIVATE_SIMULATOR --editor --import --log-file IMPORT_LOG
GODOT_EXE --headless --path PRIVATE_SIMULATOR --script res://tests/test_motion_cast.gd --log-file CAST_LOG
GODOT_EXE --headless --path PRIVATE_SIMULATOR --script res://tests/test_editor_document.gd --log-file EDITOR_LOG
```

The assigned private `godot-collision-probe-20261015` directory contains
source/staged manifests, original RED, failed typed-array/40s-timeout evidence,
final GREEN, full fixture JSON lines, encoded geometry analysis, direct-space
samples, official API XML and receipt with actual thread/commands/exits/hashes.
Generated `.gd.uid` files stay in private execution copies; they are recorded
separately from immutable product input files.

Remaining work includes a validated collision backend or independent conservative
sweep certificate, rotation substeps, arc deviation, measured asset/pose/error
budgets, gate state machine, actual motion authority/process isolation and complete
G06/1000-case/game/board acceptance. This primitive does not start any of those
paths or connect to Run. Source files are released to the responsible main after
the bounded delivery.

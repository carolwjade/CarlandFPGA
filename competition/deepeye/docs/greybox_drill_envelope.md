# Development greybox drill dimensions and envelope

Work `A-greybox-drill-envelope-20261015-v1`, owner A. Contract
`DEEPEYE-HUMAN-LOCK-20261014/revision1`, canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
H01–H15 and taskbook rigid-tool dimensions are unchanged: total visible length
0.80m, maximum diameter0.24m, local +Z forward and pivot at the length centre.

The viewer retains a cylinder plus a closed solid cone, explicitly labelled
`开发灰盒·钻头（静态；无运动）`. Its geometry is:

|Component|Length|Centre Z|Rear/front Z|Maximum radius|
|---|---:|---:|---|---:|
|Cylinder|.58m|−.11m|[−.40,.18]m|.12m|
|Cone, tip forward|.22m|.29m|[.18,.40]m|.12m|
|Complete greybox|.80m|AABB midpoint0|[−.40,.40]m|.12m|

The pieces share the radius.12m seam at Z=.18m. Both end caps remain present,
so each mesh is independently closed; their touching seam caps are internal
surfaces of the union. The pivot is the full-length/AABB centre, not the volume
centroid of this asymmetric pair. No gate, diameter, authority or motion policy
changes accompany this correction.

The previous body was.80m centred at0 with a further.22m head centred at.51m:
the actual greybox extended from−.4 to+.62m and was1.02m long. It exceeded the
candidate capsule end at+.52m. The repair corrects the visible geometry instead
of weakening its dimensions or the collision requirements.

## Actual mesh regression

`simulator/tests/test_editor_document.gd` instantiates the actual viewer scene.
It recursively finds `MeshInstance3D` children of `DrillGreybox`, reads each
surface's real vertex/index arrays, and applies the instance transform relative
to the drill pivot. `Label3D` annotations are excluded. It checks:

- Whole-mesh dimensions, extrema and centre; unit world basis prevents an
  ancestor scale/shear/reflection from being hidden by relative measurements.
- Every transformed vertex's distance to the axis segment Z∈[−.4,.4] and its
  distance to the pivot. The former must fit capsule h=.4/r=.12 and the latter
  the conservative R_body=.52m bound. The capsule's total length is1.04m;
  that is separate from the visible greybox's required.80m length.
- Each component's closed mesh topology, paired opposite edge orientations and
  nonzero signed tetrahedral volume. Coincident cap/seam vertices are welded at
  1µm coordinate resolution; repeated-vertex cone-apex triangles are discarded.
  Components are tested separately so internal coincident seam caps are valid.
- Geometry-derived cylinder/head ordering, .18m seam, unchanged radius,
  narrowing toward the positive-Z tip, full cylinder end caps and consistent
  component winding. Volumes agree with circular cylinder/cone formulas within
  0.5%, allowing the existing64-sided polygon discretization (about0.16%).
- Authority bridge remains disconnected and motion inactive.

The added regression contributes24 checks: the inherited672 checks become696.
The actual pre-fix mesh fails8 of these checks, including length, pivot,
capsule containment and seam; corrected geometry passes696/696.

## Numerical tolerance and independent vertex audit

The regression allows2µm (2×10⁻⁶m) absolute dimension/containment measurement
tolerance for the existing single-precision mesh and Vector3 transform path.
The1µm welding grid merges coincident seams; it does not move measured vertices
or enlarge the capsule. The2µm tolerance is a test comparison budget, not a
runtime gate-clearance expansion, collision penetration allowance or sweep
error budget. It must not be used to authorize contact.

For this concrete frozen geometry, a separate real-engine export records all978
actual vertex coordinates and both instance transforms. Independent Python
Decimal precision100 remeasurement recovers each original binary32 component
from its JSON representation and performs the transform arithmetic outside
Godot. It avoids treating rounded Vector3 measurements as exact proof:

|Measurement|Exact encoded components, high precision arithmetic|
|---|---:|
|Total length|.7999999821186065673828125m|
|Maximum diameter|.2399999990076228362m|
|Maximum distance to capsule axis segment|.1199999995038114181m|
|Maximum pivot distance|.4176122516502089495m|
|Positive excess beyond default encoded radius.12|0m|

The largest dimension deviation from the specified decimals is1.79×10⁻⁸m,
well below2µm. All independently transformed vertices are strictly within the
default encoded capsule without using the comparison allowance. Convexity of
the capsule then contains every triangle and the enclosed convex components.
The audit's Decimal rounding error at precision100 is immaterial to the
approximately4.9×10⁻¹⁰m positive radial separation in these actual encoded
inputs. This is evidence for the current greybox/source/engine combination;
a changed mesh, pivot, scaling or engine must be remeasured. The2µm test budget
does not generalize into permission for another asset's positive excess.

## Reproduction and remaining gates

Copy `simulator` into a caller-owned evidence directory, excluding `.godot`,
then use the existing verified Godot4.7.2 engine there:

```text
GODOT_EXE --version
GODOT_EXE --headless --path PRIVATE_SIMULATOR --editor --import --log-file PRIVATE_IMPORT_LOG
GODOT_EXE --headless --path PRIVATE_SIMULATOR --script res://tests/test_editor_document.gd --log-file PRIVATE_TEST_LOG
GODOT_EXE --headless --path PRIVATE_SIMULATOR --quit-after 4 --log-file PRIVATE_STARTUP_LOG
```

The real version must be `4.7.2.stable.official.ed1daf0bf`; the engine executable
SHA256 used for the evidence is
`ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`.
Raw commands, exits, measurements and source/log hashes are in the assigned
private `greybox-drill-envelope-20261015` receipt directory. Source and private
execution copies remain byte-identical throughout each phase.

This repair resolves the current development greybox's size/envelope mismatch.
B's final PDC geometry/materials/asset delivery, G01 visual acceptance, G06
continuous collision/sweep and authority integration remain separate work.
There is no new collision shape, motion grant, running bridge, full passage,
100Hz performance or physical-board acceptance claim.

# Exact-owner candidate conductivity field

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
All H01-H15 remain mandatory. This module connects the original motion owner's
numerical scene and current committed pose to private Root sensor callbacks.
It establishes neither frozen/native geometry provenance nor physical material
conductivity, sensor accuracy, a 1% bound, Run/CPU/board or complete H12 evidence.
G03/R03/all29 remain not_run without their separate named evidence.

`OwnedWorldField` takes the exact existing `OwnedMotionExecutor`. It has no
alternative scene argument. It captures that executor's original `_scene`
object, scene ID and digest, `_world_binding`, run ID and world epoch
(`root.phase.context.epoch`). Construction recomputes the numerical scene
digest and rejects an inconsistent scene. Exact classes, a digest and frozen
dataclasses are numerical identity checks, not source authentication or proof
that the original native world was frozen and fully measured. The responsible
Root factory must establish that prerequisite separately.

The complete scene contains at most 30 objects. Root must explicitly supply
`max_pieces`, a positive integer no larger than 256. Every original object and
piece is compiled; exceeding the chosen cap or encountering any unsupported
piece refuses the entire field. It never skips a difficult object or selects
a simpler scene. The current full `WorldValues` source constructor represents
water, hard rock, fault and void as nominal box envelopes, casing as a nominal
cylinder, with separately derived mesh-deviation budgets. This field uses
those actual Solid values; it does not silently replace them with visual mesh
surfaces or claim the envelopes are exact material volumes.

Root must explicitly provide a dictionary with exactly the five keys
`water`, `hard_rock`, `fault`, `void`, `casing`. Every value is a finite scalar
within the existing forward-profile conductivity range `[0.0005, 5]` S/m, or
explicit `None` for unsupported material conductivity. Background formation
conductivity is also mandatory and must be a valid scalar in that range;
background cannot be `None`. There are no vendor/material defaults. Policy
values are copied to scalar tuples, so later dictionary edits cannot rebind
the field. `None` for casing/void means unknown EM response when that material
wins the overlap, not zero conductivity, through-shield sensing or an invented
air/void detector. The existing forward kernel invalidates EM when a queried
conductivity is None; this field does not change kernel quality policy.

Both supported shapes use the original `Solid.centre`, `dimensions` and
rotation `matrix`. Dimensions are half sizes. The world point is mapped to
local coordinates by the transpose of that actual rotation matrix. A box
tests all three local face gaps. A cylinder's axis is local Z, its local
cross-section is the ellipse with radii `dimensions[0:2]`, and its local
half-height is `dimensions[2]`. Cylindrical sampling uses
`hypot(local_x/radius_x, local_y/radius_y)` and the axial face gap. Ellipsoids
and polytopes are deliberately unsupported and refuse the whole field.

Optional `sample_epsilon_m` must be explicitly positive and finite if supplied.
It creates a candidate ambiguity band around box faces and cylinder caps;
the cylinder radial normalized band is `epsilon/min(radius_x, radius_y)`.
This scaling conservatively includes the corresponding Euclidean epsilon
neighborhood for the nominal ellipse, but it does not certify conversion,
matrix, mesh, material or physical modeling error. Omission uses zero for
the comparison band and still returns None at exact nominal boundaries; it
does not assert zero numerical/geometry error. Root must choose and justify
any practical uncertainty allowance using its original world/policy evidence.

Any ambiguous queried boundary or nonfinite/unrepresentable sampling arithmetic
returns None rather than quietly substituting background. This conservative
policy also returns None for an ambiguous lower-priority piece beneath a
higher-priority object, or for an ambiguous seam between pieces of the same
material. Otherwise overlaps use the existing LayoutCodec order: casing 5,
fault 4, void 3, water 2, hard_rock 1. This differs from collision-risk ranking.
A point outside every piece returns only the explicit background policy,
including outside the nominal workspace; no implicit material wall is added.

Every callback first calls the original `authority_snapshot()` owner-thread
guard. Changed scene identity/ID/digest, world binding, run, epoch or a true
`world_invalid` flag permanently retires the field. Restoring old attributes
does not revive it, and repeated `__init__` is refused. Foreign-thread calls
fail before reading world data and do not transfer source ownership. The
field has no rebind/restart/adoption API. Normal committed motion and a STOP
revoke do not change the world binding: `pose_reader()` obtains a fresh
`renderer_view()` pose/revision, verifies they match the same current owner
snapshot and returns a new `forward_profile.Pose`. It never caches the initial
pose or feeds a sampled/readback pose into the executor.

`sample_sigma(x,y,z)` returns a float in S/m or None. Lifecycle/ownership
violations raise ValueError, allowing the existing source pump to fail its
consumed slot. It returns no material label, distance, layout/seed, scene
descriptor or exact collision certificate. Both callbacks and the field
object stay inside trusted Root; they must never be supplied to the mapper,
AI planner, controller or a remote message. Use the existing source pump
internally, without changing the actor/host factory:

```python
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.tools.diagnostic.causal_pl_exchange import CausalSourcePump

# All arguments below are original Root-owned objects/policy, not DTOs from AI.
field = OwnedWorldField(
    original_executor,
    material_sigma=root_policy.material_sigma_s_per_m,
    background_sigma=root_policy.background_sigma_s_per_m,
    max_pieces=root_policy.max_sensor_pieces,
    sample_epsilon_m=root_policy.sample_epsilon_m,
)
source = CausalSourcePump(field.pose_reader, field.sample_sigma)
# Root still owns prepare/start, the original clock/schedule, expiry and stop.
# No new BOOT, action, CPU, movement or physical-source authority is created.
```

Focused source-only tests cover rotated/translated boxes and elliptic
cylinders, literal overlap policies including None, all 60 pieces of a
30-object scene, whole-scene refusal and invalid configuration, fresh actual
numerical-owner commit/STOP pose reads, and retirement/thread guards. They
import an existing MotionExecutor fixture module only to construct synthetic
admissions and perform new numerical steps; no old test class/suite executes.
No Godot/native freeze, PDE/kernel qualification, model, board or physical
sensor operation is part of these controls. Root review and integration remain
separate from this module's source/test completion.

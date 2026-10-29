# Authority pose presentation bridge

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
All H01-H15 remain mandatory. This adapter supplies presentation state only;
full Run integration, either complete H12 mode, game-quality 3D/UI, physical
board results, G03/R03 and all29 acceptance are not established by these tests.

The trusted serialized owner calls
`competition.deepeye.simulation.authority.renderer_frame.frame_from_executor(executor)`
after its existing motion publication or revoke. The function requires the
actual `OwnedMotionExecutor` class. Its existing methods enforce the owner
thread. It selects the run identity and real `_Root.revision`, the committed
`renderer_view()` pose/revision, and the `controller_view()` stopped flag.
There is no recursive root serialization and no callback, geometry query,
provider lookup, mutation, or movement authorization in this read.

The JSON object has exactly these six keys:

```json
{"run_id":"run-1","authority_revision":4,"pose_revision":2,"position_m":[0,0,15.59505],"orientation_xyzw":[0,1,0,0],"stopped":false}
```

`authority_revision` is the real owner state revision, including BOOT,
admission, commit and revoke changes. It is not a renderer counter.
`pose_revision` identifies the published geometry. Both are strict nonnegative
integers at the Python boundary, bounded by `2^53-1`. Godot's JSON parser
represents numeric tokens as doubles, so the native boundary requires a finite,
exact integer value in this same range; fractional values and booleans fail.
Run identifiers contain 1-128 characters without C0/DEL control characters.
Positions must be finite and representable as native float32 components;
quaternion xyzw norm must be within `1e-6` of one. Zero/nonunit/nonfinite
quaternions fail; accepted native quaternions are normalized for rendering.
Numeric arrays are copied. Extra or missing keys fail. No action or command
source is fabricated: the existing renderer view does not supply one.

The frame is private renderer data. Never send it to an AI/controller as a
sensor observation or add scene, obstacle, seed, editor history or collision
oracle fields. Validation is structural, not source authentication. The
trusted host integration must supply frames on its own renderer-only channel;
there is no network listener, controller endpoint or source credential here.

Load `res://viewer/authority_pose_bridge.gd`, instantiate it, and call
`bind_target(existing_body_pose_node, run_id)` once. The target must be the
original in-tree `Node3D` body pose anchor, in world metres with body +Z
forward and +Y up. It must have unit visual scale; put asset-specific scale
on children. Binding creates no duplicate drill or new motion store and
does not modify the target. A new run uses a new bridge. The viewer attachment
below does not enable Run or alter the actor composition gate.

`apply_frame(frame)` validates the complete whitelist, bound run, numeric
representation, native transform and parent inverse before modifying the
target. The authority revision must strictly increase (first frame may be
zero). Pose revision cannot decrease. At an unchanged pose revision, the
original frame position and quaternion arrays must match exactly; comparison
uses the saved original double values, not rounded native float32 readback.
This permits a real revoke/STOP snapshot with higher authority revision and
unchanged geometry. Replayed/stale frames and geometry changes under the
same pose revision fail without changing pose or metadata.

On acceptance the adapter updates the target's `global_transform` and its
`deepeye_authority_*` native metadata, preserving the actual authority/pose
revisions, run and stopped flag. `readback()` reads the target's current
global transform and native metadata, rather than echoing cached input.
Native float32/parent-transform roundoff is visible in that result. External
native changes are consequently visible too; the readback is presentation
evidence, not a collision certificate or authority/STOP ACK. No result
flows back into the Python pose store. The Python full-volume motion owner
and its final fence remain the only movement authority. This one-way update
is not an atomic cross-process transaction or proof of full chain liveness.

The new Python tests use the existing synthetic admitted-source fixture to
execute two actual owner prepare/commit operations, then a real owner revoke.
Only the new `RendererFrameTests` class is selected; no old suite runs.
The headless Godot test consumes those JSON frames on an original native
Node3D under a rotated/translated parent. It checks two different committed
native poses, the higher-state/same-pose STOP snapshot, malformed/stale/truth
field rejection without native mutation, same-pose geometry refusal, and
readback of an independently changed native transform. Fixture admission
does not authenticate a board, model, source observation or live action.

The actual `viewer/main.tscn` now exposes three renderer-only methods through
its existing `main.gd` script:

- `bind_authority_renderer(run_id)` lets the trusted Root explicitly bind the
  viewer's current original `_drill_root` once. A failed bind does not occupy
  the target. It creates only a bridge reference, not another drill node.
- `present_authority_frame(frame)` rejects unbound calls, including a first
  valid frame. After binding it delegates all validation and native updates
  to the same bridge; a frame cannot choose its own run or target.
- `read_authority_presentation()` returns the bridge's actual native
  transform/metadata readback, or an empty dictionary while unbound.

The attachment never changes the document's control connection or motion
state, enables Run/pause/continue, creates an action, or updates Python
authority. The original body asset, disabled presentation collisions, gates,
editing and camera paths are retained. Asset failure still produces the
existing explicitly named greybox; presentation API availability alone does
not prove the body asset loaded or establish complete modeling acceptance.

`tests/test_live_authority_presentation.gd` loads the real `main.tscn` in a
private complete simulator stage, rather than substituting an empty target.
It checks unbound rejection, explicit binding, two actual numerical-owner
commit snapshots and a subsequent owner-revoke STOP snapshot, refused bad
run/stale/truth-bearing frames, the unchanged target/body/camera/gate nodes,
and the closed Run/control gates. Its asset report records the actual target,
asset identifier, mesh count and diagnostics. Its JSON fixture is copied from
the earlier synthetic-source owner test output with original path and hash;
that does not represent a new board/source authentication or rerun that suite.

This is the application-side renderer attachment. A trusted Root cross-process
channel still must initialize and deliver the renderer frames. Run orchestration,
CPU/AI processing and both complete H12 chains remain separate pending work.

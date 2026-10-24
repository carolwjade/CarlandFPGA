# Owned numerical motion transaction

`simulation/authority/motion_executor.py` implements the selected local
prepare/commit dependency. It does not register a runtime provider, activate
Run, authenticate sources, monitor a real AI process, drive Godot or operate a
board. All 29 taskbook cards remain `not_run`. Contract
DEEPEYE-HUMAN-LOCK-20261014/revision1 and H01–H15 remain mandatory; requirements
SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## Trusted integration boundary

One authority thread owns the runtime, executor, immutable scene/asset epoch and
all mutation methods. The integration supplies an internally owned valid
`PassageState`, a separately enumerated complete `solid_clearance.Scene`, the
same capsule dimensions used by workspace proofs and explicit `GeometryBudget`
upper bounds. Frozen objects and their hashes are provenance, not credentials.
Only that authority may call `activate_boot` or `admit_command`; these functions
check structure and identities, and do not verify physical board capture,
source authentication, observation quality or live AI participation.

The existing `AuthorityDependencies.prepare_step` and `commit_step` signatures
can delegate to this object. The surrounding integration must first finish
actual `PcDirectRuntime.boot`/`command` admission, then bind the **same immutable
BOOT object** and original admitted command bytes here. Errors in either half
stop both objects. Any operator STOP, broker STOP, source/AI loss, mode/config
change or lifecycle failure invokes both `runtime.stop` and `executor.revoke`
on the owning serial thread. A runtime rejection by itself is not an executor
BOOT handshake. A new verified BOOT uses an increasing generation and unused
session; it retires old handles but cannot clear the trial failure latch.

No implementation of `verify_*` or `ai_lease` is provided. Do not substitute an
always-true provider or explicit fixture records for genuine provenance.
`before_commit` must be the current runtime step's single-use synchronous
callback. It rechecks original command TTL, original native observation age,
STATE8, current BOOT, STOP generation and bounded actual AI liveness. A forged
`StepFence` is not safe to accept from a controller. The executor also bounds
its end by the command's original issue+duration; it cannot independently
establish observation/heartbeat/AI deadlines from command JSON.

## Preparation and full-volume geometry

`prepare_step` derives a single `CanonicalPath` from the owned current pose,
admitted raw codes, 1–10ms duration and `required_inherited_errors`. No route,
caller pose, externally supplied slice or collision witness is accepted.
The complete workspace passage reducer checks all six faces for every slice
with the active blue-entry/red-exit role. Every contiguous slice also receives
initial and full solid-scene separation checks over every declared convex
piece. An incomplete scene is rejected by the existing scene constructor.

CP's endpoint-chord-covering `gate_bounds.arc_length_upper_m` is used for the
solid sweep, together with its full curvature and rotation bounds. The
existing 0.5mm rotation floor, accumulated positional/orientation uncertainty,
speed rounding carry and all explicit extra margins survive. Workspace and
solid capsule dimensions must agree exactly. Initialization's
`additional_margin_m` must cover `numeric + asset + obstacle` exactly as encoded;
use an outward upper float for non-exact sums. For solids, the same total is
partitioned using rational arithmetic: asset and obstacle retain their explicit
terms, and numeric receives the remaining margin (including engine and any
other conservative remainder). There is no float subtraction or reset of
inherited errors. Zero budgets mean an explicitly asserted exact mathematical
fixture or justified contained model, never an inferred production default.

The relative helper uses the old owned phase time as a **numerical anchor** and
anchor+duration+1 solely to request a complete strict D−1ns geometric proof.
It supplies no real freshness or time authority. The full relative proof,
its absolute anchor trace, prior committed history and later actual fence are
retained separately. Waiting never integrates speed or moves the owned body.

UNKNOWN, HELD and unresolved multi-slice arrival reject the whole step, without
a safe prefix. `DRILLING_REQUIRED` rejects movement pending a separate material
law; hard rock cannot hide the forbidden material union. A proved workspace
violation sets the permanent trial latch. UNKNOWN is not labelled collision.
Rejected transactions stop this store conservatively; a fresh BOOT is required
for recovery, and a trial failure still forbids motion.

## Commit and publication

Prepared handles are private identity-registered, owner-specific and single-use
even after a stale-root rejection or callback exception. Only one pending
preparation is retained; the next preparation retires its predecessor.
Every admission/revocation/BOOT/store change changes the root identity. Any
scene, geometry asset, layout, material policy or epoch edit must call
`invalidate_world` **before** changing the registry/rendered world. This retires
the entire static store; initialize a new run/store/history for the new world.
BOOT alone cannot reinterpret its previous history. This increment does not
watch files, authenticate a registry or implement live editing integration.

Commit consumes the handle, checks the exact root, and preallocates the fixed
publication frame/root/receipt. Inside the serial transaction it invokes the
runtime callback exactly once. Then it checks the unchanged root, exact BOOT
object identity, command sequence, integer actual interval, non-overlap and
strict `end < deadline <= original issue+duration`. Equality at the deadline is
conservatively rejected. A caught recursive/malformed mutation or STOP inside
the callback still changes the root and vetoes publication.

After a valid fence there is no geometry, hashing, clock read, I/O, external
callback, asynchronous work or wait. Fixed-size field binding precedes one
`self._root = new_root` publication. The single owner and callback-free suffix
make this an in-process root compare-and-swap transaction; it is not an OS
isolation or cross-thread atomicity claim. Pose, revision, relative phase proof
and actual-time commit frame become visible together. No engine performs
autonomous integration between calls.

`passage_state` materializes appended event times at actual fence+offset before
later preparation or authority audit. Prior events remain unchanged; the new
trace binds the actual interval to the retained relative proof. No absolute
proof is relabelled. Materialization/hashing is outside the final fence.
If a caller loses a receipt after publication, inspect the owned frame/revision
and reconcile; do not replay an unknown step. The consumed handle cannot repeat
the movement.

If later authority materialization fails or is cancelled, the executor retains
the already committed pose, frame and history, retires pending handles and stops
before propagating the original exception. The same BOOT/command cannot continue
movement without recovery admission. A caught failure inside a final callback
still changes the root and vetoes its publication. An unknown history error does
not establish a collision or newly set the permanent trial-failure flag.

## Read surfaces and remaining gates

`renderer_view` is a frozen pose/revision view, not an engine write capability.
`controller_view` contains only coarse stopped/trial-failed state; its stopped
flag is not a motion grant. `authority_snapshot`, `prepared_audit`,
`passage_state`, original bytes, proofs and detailed exceptions are private
authority tooling. Never expose those methods or the executor object to PC AI,
FPGA/controller processes or an unrestricted plugin. Python naming/frozen
dataclasses do not establish a process boundary or capability sandbox.

Tests use explicit numerical scenes and synthetic authenticated-record fixtures.
Intermediate entry/exit phase seeds are marked numerical fixtures, not actual
executed history. The continuous end-to-end runtime test uses the real geometry
and two owned commits, but its channels and clock are fixtures. T01–T16 and
additional malformed-entry/alias regressions establish bounded local software
behavior only. Real channel/BOOT/source authentication, AI lifetime/benefit,
trusted clock, B asset containment/transform, material-state law, Godot visible
publication, isolation, both live control paths and full game/board acceptance
remain separate integration requirements.

# Owned motion executor: selected implementation design

A Desktop generation 2 selects the relative-proof/final-fence design from
`.planning/deepeye-resume-20261018/trusted-motion-design/design.md` (ROOT;
SHA256 ac742f9728228edd8e20cd320f245b1e72cf7f1c85d121d195e2c4f530fe6967).
Task DEEPEYE-IMPLEMENTATION-20261014/v1, H01-H15 contract
DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 unchanged.
This choice is within the human's existing autonomous implementation authority.

Implement the actual owned simulation-state transaction between the accepted
PC_DIRECT runtime interface and existing canonical motion, workspace passage and
solid-volume checks. Geometry is prepared for a fixed relative duration while
the scene/asset epoch is static. At commit, the one final StepFence supplies the
actual host interval and original earliest deadline. Waiting does not integrate
motion. A single state-root compare-and-swap publishes pose, passage and audit
frame together; STOP/revocation, source/scene/asset/BOOT changes invalidate all
pending steps. A prepared handle is single-use even after failure.

No caller-supplied route, collision witness, pose, safe prefix or refreshed TTL
is accepted. The executor derives one CanonicalPath from the admitted original
command and owned state, then checks every contiguous slice for complete-volume
workspace passage and the entire separately enumerated solid-scene manifest.
UNKNOWN stays unknown; DRILLING_REQUIRED still awaits the material state law.
All certified error/speed carry and asset/engine/obstacle margins are retained.
Successful numeric initialization does not prove source authentication.

Keep prepare_step/commit_step signatures compatible with AuthorityDependencies.
Expose no permissive/default verify_* or AI provider, and do not register or
activate production Run in this increment. Ownership and source records come
from an explicitly supplied trusted authority integration; mathematical tests
are labeled fixtures and cannot supply production authenticity. No hidden-world
proofs or exact rejection geometry are exported to the controller.

The final callback runs once inside the owner's serial transaction. Expensive
geometry/hashing/allocation/audit preparation is before it. Afterward do only
fixed-size validation, final interval binding and one owned-state publication;
no external calls or I/O. Use strict end < original deadline for this first
executor, matching the canonical path D-1ns convention without extending TTL.
Committed relative proof and actual-time mapping are retained independently;
materialization occurs before later preparation/audit, never by relabeling old
absolute proof timestamps. Preserve old passage events and the failure latch.

Implementation scope: new motion_executor.py/test/docs plus the two internal
relative-transition/materialization helpers in passage_phase.py. The existing
preview behavior, runtime/watchdog/wire, C broker and isolation remain unchanged.
Run concrete versions of T01-T16 in the design handoff and obtain an independent
source/behavior review. Real source/BOOT/clock/AI lifetime, asset containment,
material law, rendering visibility, both live control paths and all formal cards
still require their separate integration evidence. This increment is an actual
local software dependency toward those outcomes, not replacement acceptance.

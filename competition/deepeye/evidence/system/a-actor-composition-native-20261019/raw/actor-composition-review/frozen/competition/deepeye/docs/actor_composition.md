# Original-actor composition library: production unavailable

Task DEEPEYE-IMPLEMENTATION-20261014/v1, A-actor-composition-implementation-20261019-v1.
Selected design SHA256 `6ab5929285a4a5ef1fa55ff2f47bd8230c8f318a93a08d31b437903fec3617dd`.
Contract DEEPEYE-HUMAN-LOCK-20261014/revision1, H01-H15 canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` unchanged.

`simulation.authority.actor_composition.create_authority(AuthorityConfig(...))` is a trusted
library composition entry. Its fixed production channel/package gate currently raises
`ActivationUnavailable` **before ActorRegistry construction or launch**. No actual AI entry,
authenticated readiness/BOOT/channel or measured source/clock/capture provider is installed.
The library does not enable viewer Run, register a product provider, stage a model, launch a
process or implement the four product processes. Importing it does not load the native backend.

The explicit config is private trusted-main state: actor policy, initial world state, solid
scene/model/budget, heartbeat timeout and geometry slice bound. It is neither a credential nor
an untrusted controller message. The factory has no public provider, verifier, registry,
executor, actor, PID, HANDLE, alive boolean or AiLease injection argument. The only lifetime
adapter target is this factory's original actor.ai_lease; geometry targets its own executor.
The channel adapter cannot replace either. Python privacy and immutable dataclasses do not
protect against malicious code already inside the trusted authority process.

## Ownership and activation

The factory retains a holder in private `_RETAINED` before registry construction/acquisition.
It constructs the actual registry, owned executor and runtime on one thread. The registry keeps
every original owner, including a process acquired before launch raises. Recovery holders are
never evicted automatically, adopted from disk, reopened by PID or force-discarded. A future
trusted recovery manager must account for this deliberate retention and admission bounds.

After original authenticated readiness/BOOT evidence exists, one closed transaction must:

1. Derive one fresh exact BootBinding from the original owned actor/channel and verifier. No
   plain dataclass, READY text or matching caller string authenticates it.
2. Activate the runtime and executor with that same retained object, then bind the original
   actor to those exact authorities. Recheck transaction veto, verifier health and actor life
   before opening command admission. A failed proposal cannot be retried on this composition.
3. Route runtime command admission first, then admit only its original accepted non-STOP bytes
   to the executor. Broker STOP closes admission and never becomes movement.

The production verifier is deliberately absent. Tests patch a module-private channel factory;
their opaque object identities, synthetic progress status and valid JSON/CRC are **fixtures**,
not real endpoint authentication or inference. They provide no production fallback. A real
implementation needs separately reviewed bounded persistent IPC, original endpoint ownership,
one-use readiness association, approved model/package provenance and actual device/initialization
evidence. Model initialization still does not establish H11 usefulness. Current synchronous
write helpers provide no hard cancellation deadline; this library adds no IPC protocol or wire
fields. Real progress/source/timing deadlines and their final-fence integration remain missing
provider obligations. The fixture health check before events/steps is not their acceptance.

## Revocation and outcomes

Every event/step uses the same owner-thread guard. Malformed shapes and caught reentry veto the
outer operation. A foreign thread only sets a pending Event; the owner drains it before work,
and the fixed actor adapter checks it again after the original HANDLE observation. No foreign
thread closes handles or calls the executor. Polling cadence belongs to the future owner loop;
no watcher/service or guaranteed owner-hang supervision is added.

Failure first closes admission and advances the composition veto. Runtime STOP and executor
revoke independently check the exact original activation at each callback dispatch. The second
check happens after STOP returns, since it may activate an executor successor. R1 actor callback
fences remain in force during cleanup. Even before actor.bind_verified_boot has installed its
own callbacks, the composition can revoke each successfully activated original authority.
Callback exceptions cannot skip the other target or actor cleanup.

Cleanup occurs after the outer owner call has unwound, avoiding reentrant native teardown
during a sample. It visits the registry's retained owners and uses their existing one-attempt
cleanup; repeated close never retries native effects. The primary exception, callback/cleanup
errors and actual last runtime step stay private and strongly retained. Uncertain resources or
incomplete actor evidence remain QUARANTINED. CLOSED describes cleanup, not successful launch
or inference. Public errors are sanitized; status exposes only lifecycle state and step results
only committed/pose_revision. Do not serialize private objects, causes, raw source/geometry
errors or authority exceptions to a controller. Renderer/world transport remains separate work.

All noncommitted steps conservatively retire this composition, including healthy idle/normal
expiry. This deliberate availability cost avoids guessing idle semantics from exception text.
A new composition/actor and independently verified fresh run/session/generation are required
for recovery; no actor replacement occurs inside the old composition. Existing world-edit
invalidations still require a new world/store/history. Late old close/poll/errors cannot revoke
a successor activation.

Geometry preparation, full original dt, original TTL/observation/heartbeat bounds and the
executor's one final callback/strict end<deadline/root CAS remain unchanged. No IPC, log, hash
or added probe is inserted after that final callback. An original-HANDLE sample is a recent
nonsignaled observation, not survival through CAS or responsive/useful inference. A veto after
an observed successful CAS retires future admission while preserving the positive commit fact;
it cannot undo or relabel the numerical side effect. A negative outcome is absence of an
accepted commit receipt, not a universal independent proof against side effects from a broken
trusted executor/provider. Unknown outcomes must never be replayed automatically.

## Verification scope

Offline tests retain the real ActorRegistry/resource cleanup and numerical runtime/executor;
only native acquisition and original channel events are synthetic. They cover zero acquisition
at the absent production gate, detached static channel lease attempts, original death before
and during final checks, real pose publication, partial activation, identity-fenced callbacks,
STOP, malformed/reentrant/foreign calls, strong recovery and post-CAS veto semantics. Existing
actor/runtime/executor regressions use the accepted actor-repair/current-G06 dependency bytes.
The separately owned moving native harness/document are not imported or pinned dependencies.

No native actor, genuine AI/readiness, real source/channel/BOOT/timing authentication, product
Run, both complete H12 chains, game rendering/interaction, hardware/board or all29 formal card
acceptance is established. PC_DIRECT remains a legal independent full path; HIL_PC_FPGA still
requires its own original board actuation/capture evidence. Neither becomes mandatory for the
other. Controller inputs remain causal FPGA observations, legal task geometry and odometry;
world truth, future sensors and collision rejection details never become an AI channel.

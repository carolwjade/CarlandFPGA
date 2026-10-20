# Retained actor owner and original HANDLE observation

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`, delivery `A-actor-owner-implementation-20261019-v1`.
Selected design: owning-root `ai-lifetime-design/design.md`, SHA256
`5eb4fd822d9e30a9ca032de7a9fca969ab24e1751558bb922f654032165cbb4f`.
Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 canonical SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

This component supplies an actual acquisition path and retained ownership for a future
trusted authority composition. It has not launched a native actor in this delivery. It
does not implement AI inference, readiness authentication, channel verifiers, a product Run
entrypoint, an OS supervisor or a default `AuthorityDependencies` provider.

## Trusted construction

`ActorRegistry()` fixes the existing native `win32` backend and host `monotonic_ns` clock.
Create it on the same trusted thread that owns `PcDirectRuntime` and `OwnedMotionExecutor`.
Retain the registry for the complete run and unresolved recovery period. Module-internal
patches are used only in offline tests. Python privacy, subclass checks, immutable policy
and dataclasses are not security boundaries; an untrusted actor must be a separate isolated
process without access to these objects, the authority address space or its filesystem data.

`registry.launch(policy)` accepts exactly one explicit `ActorPolicy`, with no PID, process
handle, previous receipt, external `OwnedReference`, caller-selected alive value or adoption
option. The trusted composition root supplies a fresh run ID, approved immutable file/hash
manifest and source directory, manifested executable, fixed arguments, minimal-environment
roots, stage/output limits and every timing budget. These inputs need prior A review; the
policy dataclass does not attest that review or authenticate a controller request.

All staged files require exact lowercase SHA256, ordinary single-link source files, no
reparse ancestors, canonical safe relative paths and no case-insensitive duplicates. The
factory copies verified bytes into a fresh ACL-contained stage, rather than executing the
source tree. Stage memory is bounded by `max_stage_bytes` (at most 256 MiB). The existing
`available_output` helper hard-caps its native read at 8192 bytes. A smaller `output_limit`
is a post-read acceptance limit: excess returned output is rejected and discarded, not
read with a smaller native count. The existing helper
creates two 16 KiB pipes; only the child input reader/output writer are inherited. Parent
endpoint flags are independently read back as non-inheritable. The final two arguments are
decimal input/output HANDLE numbers, so approved actor code must implement that convention.
There is no controller-selected environment, shell invocation or generic script discovery.

The production factory itself acquires profile/SID, pipes, job and suspended process through
the reviewed helpers. It registers and strongly retains an owner before its first clock,
disk or native action; the helper records both process/thread handles before propagating
post-acquisition failures. It assigns the job and verifies suspended token/capabilities,
mitigations, job limits and creation FILETIME, closes parent copies of child endpoints, then
resumes once. The final current-handle sample occurs after report persistence. A successful
return is `RUNNING_UNBOUND` with the original process HANDLE retained. No one-shot prototype
result or quarantined recovery context can become ACTIVE.

The one-shot `prototype.run` and all existing helpers/runtime/executor remain unchanged.
The retained owner keeps its parent endpoints open; a future bounded persistent causal IPC
protocol is required. No automatic writes, blocking actor-output reads, truth canary or
model/usefulness assertions are added. Cleanup only peeks bounded diagnostic output and
discards it; actor output never becomes trusted liveness/readiness evidence.

## Activation and lifetime

The state sequence is `ALLOCATING → SUSPENDED → RUNNING_UNBOUND → BOUND_ACTIVE`, followed
by irreversible `REVOKED → DRAINING → CLOSED/QUARANTINED`. A launch failure also enters the
same single cleanup path. Registry namespace plus increasing acquisition ordinal mint each
instance label; PID is never queried/reopened to discover life. Creation FILETIME is
corroborating metadata, not a monotonic deadline or independently supplied credential.

Future trusted BOOT composition must authenticate original readiness/channel evidence and
activate the exact runtime/executor BOOT before calling
`owner.bind_verified_boot(boot, runtime=runtime, executor=executor)`. This method does not
verify that evidence. It checks its own factory instance/run and exact activated authority
objects, consumes a strictly increasing generation and unused session within the registry,
then checks current life and the original readiness deadline. Failed proposals remain
retired. Partial activation failure revokes each authority's original captured activation;
it must not affect a successor activated in the meantime. This narrow first
version permits one binding per actor; every recovery/replacement needs a newly acquired
actor, new instance, independently verified fresh session and higher generation.

BOOT freshness across authority restart is a separate trusted verifier obligation: use a
fresh run/session, verify current pose/state, and never reconstruct an old active session
from a receipt. The registry cannot attest cross-process persisted BOOT history. A frozen
dataclass or guessed instance string cannot authenticate a BOOT or acquire an actor.

Only `owner.ai_lease(boot, now_ns)` may return the existing runtime `AiLease`. Each call:

1. Checks same-thread, no reentry, original registry membership, exact retained BOOT and
   original process acquisition reference/native value. Any attempted release, ambiguous
   reuse, terminal flag, sealed cleanup, detach or replacement rejects it.
2. Reads the fixed trusted monotonic clock, rejects regression/malformed values and checks
   the runtime's strict integer `now_ns` is not ahead of that clock. It checks reference
   continuity again after the clock callback before touching the original HANDLE.
3. Calls only `WaitForSingleObject(original_process_handle, 0)`. Literal integer
   `WAIT_TIMEOUT=258` is a nonsignaled sample. `WAIT_OBJECT_0=0` marks terminal. Failure,
   exception, boolean or any other result is unknown and vetoes. Exit code 259 is never
   used to infer life.
4. Rechecks time, lifecycle epoch, reference continuity and fixed deadlines. The result's
   deadline is `min(before_sample + sample_age_cap_ns, fixed_run_deadline_ns)`. A sample
   taking `max_probe_ns` or more is rejected. Completing late never renews the sample.

All four timing inputs are mandatory positive integers. Require
`max_probe_ns < sample_age_cap_ns <= lifetime_timeout_ns` and readiness within lifetime.
They have no permissive defaults and are engineering policy, not measured guarantees.
Readiness and run deadlines start before launch preparation and never move. Unbound `poll`
enforces readiness too; bound `poll` checks the same original life/run limit. The future
owner loop must call it at a reviewed finite cadence even when no command is pending.

The runtime's existing final fence samples again and then rechecks its clock/deadlines.
The executor preserves its stricter `step_end_ns < deadline_ns`, one final callback and
one root CAS. No log, hash, geometry, provider call, I/O or extra clock is added after that
callback. Direct binding uses the pinned runtime's private `_boot` identity and executor's
existing `authority_snapshot`; changing those interfaces requires another exact review.

A sample proves only that this held process object was nonsignaled recently. It cannot
prove responsiveness, meaningful AI or survival through the next interval. Death after the
last successful sample can still precede a valid CAS; an explicit software regression
preserves this observation gap. A guaranteed future-life interpretation is invalid.
Inference progress/IPC deadlines, observation/source health and independent watchdogs remain
separate gates; process existence cannot refresh command TTL, source age or heartbeat.

## Revocation and resource retention

Component failures retire state/epoch before invoking `runtime.stop`; executor `revoke`
is attempted in a `finally` even if STOP throws. Each callback is fenced independently
at its own dispatch boundary by the exact runtime/executor activation captured during
binding. The executor identity is checked after the STOP callback returns, since that
callback may itself advance the other authority. Callback failures remain private evidence
and cannot restore life. Caught callback reentry cannot recursively dispatch endless STOPs.
Malformed API shapes, reentry and exceptions veto outer work. Cross-thread calls set a
thread-safe pending veto and return an error without calling the thread-affine executor or
closing handles; the next authority entry revokes the captured activations still current.
No background watcher mutates it.

Follow-up AOR-R1 repair covers every old-owner entry, including repeated close, poll,
old/malformed ai_lease and errors on CLOSED/QUARANTINED owners. Retained callbacks cannot
stop a newly activated BOOT. A mixed pair is treated independently: the still-original
activation may be stopped while the replacement is untouched. State labels and one native
cleanup attempt are not substitutes for this callback fence. Original partial-activation
failure still stops the two activations captured at that attempted binding. The guard
uses the exact pinned runtime `_boot` and executor `_root.boot` identities; these private
interface dependencies require renewed review if their activation semantics change.

The trusted integration must additionally route every external operator/source/config STOP,
runtime admission/step rejection and composition exception to both motion owners before any
further admission. Calling `owner.close(reason)` conservatively retires the actor and does
that propagation. Runtime latching alone does not revoke an executor's private preparation.
This component does not intercept arbitrary direct calls to existing runtime APIs.

`owner.close` retires admission before diagnostics, termination or waits. Same-thread entry
serialization forbids close during an in-flight probe. Existing cleanup performs its one
attempt on original references, independent terminal readback, terminal-before-process-close,
retention of process/thread/job controls on uncertainty and dependent-profile removal last.
The shared cleanup backend requires exact integer Wait results before classifying either
the initial state or terminal readback. Bool, IntEnum, integer subclasses, float and other
malformed values stay unknown; no equality-to-zero shortcut may release recovery controls.
All four inherited-handle masks are captured first and require exact integers before the
expected `(1, 1, 0, 0)` values can allow resume. AOR-R2/R3 are defensive injected-dependency
shape repairs: the current native DWORD helpers already return plain integers, and these
tests are not evidence that Windows returned malformed values.
Repeated close returns the recorded cleanup result without repeating native effects. An
unknown close is never retried, no actor is automatically restarted, and failure before
factory return still leaves its strongly retained context in `registry._owners` for trusted
inspection. The registry intentionally does not evict recovery contexts.

Primary launch exceptions propagate with their original object/cause despite reporting
failure. Persistence is permitted only after the fresh evidence-root ACL succeeds. Reporting
failure never skips cleanup, but makes evidence incomplete and keeps the owner QUARANTINED.
`CLOSED` describes confirmed resource cleanup, not successful launch/inference/acceptance.
`diagnostics()` exposes only state, opaque instance label and separate evidence/cleanup
completeness flags. Raw handles, paths, context, native/child output and exception text stay
authority-private; do not forward arbitrary authority exceptions to a controller. Python
allocation failure and authority death still limit Python-level acquisition atomicity.

## Remaining supervision and evidence

The owned job has existing kill-on-close/one-process/memory/UI limits. Last-job-handle close
can kill an assigned actor when the authority dies, provided no other holder survives.
There is still a CreateProcess-to-AssignJob owner-death window. This component cannot detect
its own hung owner, guarantee kill latency, send an independent board STOP, close a leaked
job handle elsewhere or stop a separate process's outstanding command. Atomic creation/job
association, independent authority-death/hang supervision and execution-side watchdogs need
separate reviewed ownership and real evidence. No new resident, service or second main is
created here.

Offline tests use a clearly fake native boundary with real Python ownership/cleanup and
real numerical runtime/executor. Synthetic channel fixtures authenticate nothing. They cover
acquisition failures, returned-owner retention, strict samples/clock/TTL, reentry/release,
partial activation, replacement, pending/final-step veto and post-sample death. Native actor
tests are intentionally absent from this assignment. After independent exact-byte review,
A main may authorize bounded real normal, timeout and persistence-failure runs with pinned
stage/runtime/candidate hashes and operation/request records. Those future tests still do
not establish useful AI or product acceptance.

Relevant API facts were checked against Microsoft primary documentation in the selected
design: [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject),
[process handles](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers),
[termination](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process),
[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes),
[GetExitCodeProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess),
[CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle),
[TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
and [job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Actual native launch, real staged AI/causal IPC, authenticated BOOT/channel providers,
independent supervision, live viewer/authority composition, product Run, both H12 chains,
AI usefulness, FPGA/board and all29 formal cards remain **not_run** by this delivery.

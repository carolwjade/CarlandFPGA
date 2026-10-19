# PC_DIRECT authority runtime adapter

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; delivery work
`A-PC-DIRECT-RUNTIME-20261018-v3` (continues preserved v1/v2 work).
Follow-up repair `A-PC-RUNTIME-BOOT-VETO-FIX-20261018-v1` closes independent
finding PCR-R1; its original failing evidence remains preserved.
`A-PC-RUNTIME-BOOT-VETO-FIX2-20261018-v1` addresses follow-up findings PCR-R2/R3
on malformed reentry and activation-error replay, with separate failure evidence.
Human contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`; H01–H15 requirements
SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
Design input `1011259415a0916054eb580687612580bc1e5f09`, taskbook §8.8/C05/G06.

`simulation/authority/pc_direct_runtime.py` composes the existing strict host
envelope validator and PC_DIRECT watchdog in one synchronous authority owner.
It starts stopped, admits separate board/source/broker events, retains original
observation/command lifetimes, and checks again at the physics commit fence.
It supplies neither an authentication provider nor a physics implementation.
There is no default dependency, `authenticated=True`, `healthy=True`, direct
grant setter, synthetic observation generator or automatic topology fallback.
This is a software adapter delivery; actual product activation remains not_run.

## Trusted integration boundary

Construct `PcDirectRuntime(run_id=..., dependencies=..., clock=...,
heartbeat_timeout_ns=...)` only inside world_authority. `dependencies` must
implement `AuthorityDependencies`; `clock` is the authority's monotonic host
nanosecond clock. Timeout is explicit, selected from the independently reviewed
UART/profile/scheduler policy. It is not the source's separate 100ms timeout.

The dependency object is part of the trusted authority code. It must verify
original opaque events from already authenticated channels and its own private
records. The dataclasses below are results of that verification, **not bearer
credentials**. An untrusted controller must never construct the dependency
object, invoke authority methods directly, write BOOT evidence, supply its own
clock, or access the executor/authority address space. Python type checks and
subclassing do not establish an OS or process security boundary.

| Dependency method | Required verified result and obligations |
| --- | --- |
| `verify_boot(event)` | `BootBinding(run_id, generation, context_json, ai_instance)`: complete actual BOOT handshake and active context/hash/profile/session; authority-owned BOOT generation, current run and exact AI process identity. `generation` is a monotonically increasing BOOT generation, not the director thread generation. |
| `verify_board(event, boot)` | `VerifiedEnvelope(boot, raw)`: original received bytes/receipt bounds from authenticated hardware_bridge → world_authority. Bind the current run/generation and original channel provenance; reject replay across process/restart contexts. |
| `verify_observation(event, boot)` | `VerifiedObservation(boot, raw, sample_lower_ns)`: actual FPGA TELEM/EVENT reception, original sequence/quality, measured time mapping and source provenance. `sample_lower_ns` conservatively includes original native/held sensor age; never substitute receipt time or viewer truth. Reject missing measurements, invalid quality/source faults, unknown timing, forged record references and future/precomputed values. |
| `verify_command(event, boot)` | `VerifiedEnvelope(boot, raw)`: original authenticated control_broker motion_request, current AI/candidate association, candidate consumption and full observation provenance. It must not authenticate user-supplied booleans, role strings or dataclasses. |
| `ai_lease(boot, now_ns)` | `AiLease(boot, instance_id, deadline_ns)`: current actual AI process identity/life and a bounded validity interval. Raise on death, unknown state or identity replacement. Cached alive booleans and reused process IDs are insufficient. |
| `prepare_step(boot, command_raw, expected_pose_revision, dt_ns)` | Side-effect-free preparation of the full-volume collision/kinematic/gate/phase step using authority-only state and an exact expected pose revision. No mutation, safe-fraction advance or hidden geometry returned to AI. |
| `commit_step(prepared, before_commit)` | Perform actual atomic pose CAS and return the bound `CommitReceipt`. Execute the final fence as specified below. Any uncertainty/failure raises. |

All providers must fail closed and avoid asynchronous work or reentrant input
admission. Every channel/event/step runs on the constructing owner thread.
External monitors enqueue STOP/source-death/config/mode/restart events into this
same authority serialization domain; the executor's process supervisor must
independently default to stopped if the owner/process disappears. This module
contains no background timer or failure service.

## Events and lifetime

| Runtime call | Effect |
| --- | --- |
| `boot(event)` | Verifies a nonempty matching run, strict immutable context, topology 2, unused session and increasing BOOT generation. Starts with no heartbeat, observation or command. Every input must carry this exact binding, including generation and AI identity. |
| `board(event)` | Validates raw board_response schema, CRC/session/epoch/type, then sends only STATE8 to the existing watchdog. Healthy CONFIG/GAIN/BOOT/ACK3D/STATE3D responses do not refresh or poison heartbeat health. Fault/rejected status in other valid responses also stops, using offsets from frozen interface.json. No response becomes an observation or motion capture. |
| `observe(event)` | Admits verified TELEM/EVENT with known conservative acquisition mapping. Unknown/future/stale mappings reject. Retains at most four records and nonwrapping observed-sequence high-water history. An exact duplicate changes nothing; changed/old/retired identities reject. |
| `command(event)` | Parses control_broker motion_request. SET_TARGET needs a retained actual observation, live bound AI, healthy heartbeat and valid original deadline. Same raw currently active command only retains its earlier deadline. Changed/superseded/expired/wrapped identities cannot return. Broker STOP needs no observation and latches. |
| `stop(reason)` | Latches a conservative stop for operator/source/AI/config/mode/restart changes. Never resets evidence or grants motion. After a latch only a new verified BOOT with a fresh session and generation can recover. |
| `step(expected_pose_revision=..., dt_ns=...)` | Synchronously prepares and conditionally commits one interval. Returns `StepResult`; no reusable motion_grant envelope is issued. |

All timestamps/identities are strict integers; booleans do not alias integer
generation/sequence/revision fields. Envelope contexts preserve their existing
schema. BOOT/reset invalidates heartbeat, observations and commands. Committed
pose revision and executed-time high-water history remain conservative across
a BOOT. A new runtime object must not reconstruct an old active session after
process restart; its trusted provider and executor must establish a fresh BOOT
and independently verify current pose state.

BOOT activation is a veto-generation-fenced transaction. The runtime records
the veto generation at the start of the entire BOOT call, before its entry
clock callback. Any new STOP, rejected/reentrant event, recursive step, newly
observed watchdog latch or activation-clock STOP changes that generation and
prevents the in-flight verifier result from activating. An inherited latch may
be recovered; a new veto during that same call cannot be treated as inherited.
No dependency/clock callback follows the final activation fence.

A structurally valid, independently verified proposal invalidated by such a
veto retires its proposed session and BOOT generation even though it does not
replace the active context. Repeating that proposal cannot clear the STOP;
recovery needs an explicit later verified BOOT with a different unused session
and a higher generation. Retirement occurs as soon as the returned binding,
strict topology-2 context, fresh session and higher generation are validated,
**before any activation clock/guard work**. A clock exception, invalid time or
regression cannot leave that verified handshake reusable. A verifier that never
returned a valid binding, a rejected malformed context, or a failed entry clock
before verification is different: no verified proposal reached activation, so
no unverified identity is retired. A later actual verification may establish it.
Old watchdog latches are counted only when first
observed, so polling an already known old latch does not manufacture endless
new vetoes and block a separate fresh handshake. A previously unobserved old
fault discovered after BOOT call entry conservatively aborts that attempt too.

For each command:

```
deadline = min(original_host_issue + original_duration,
               original_verified_sample_lower + profile_age_cap,
               earlier_deadline_for_same_command)
```

Profile age caps remain FAST 1,500,000,000ns and STRESS 12,000,000,000ns. A source
provider may need an earlier lower bound to account for held native samples.
Duplicate envelopes/STATE/ACK never rejuvenate those bounds or the command TTL.
The retained-observation ledger is bounded; if an active command's observation
is evicted, it cannot pass the next execution check. Newer observation admission
does not silently relabel that command. Sequence wrap requires fresh BOOT.

## Atomic physics fence

`step` checks command, observation, heartbeat, AI identity/liveness and deadlines
before preparation, after preparation and inside `before_commit`. The trusted
executor must call that callback **exactly once inside its pose-CAS critical
section immediately before the only pose update**. The first attempt consumes
the callback even if it fails. Catching a failed fence and retrying cannot
restore execution. Saved callbacks expire synchronously when commit_step ends.

The callback returns a `StepFence` containing exact current boot/command/start,
end and deadline. This local check result is usable only in that synchronous
commit operation. The prepared geometry must apply to that command, pose
revision, duration and interval. No wait, async work, alternate command,
untrusted callback or second pose update may follow the fence. The executor
must stop at the checked end; interval end may equal the deadline, but a new
interval cannot begin there. Actual real-time scheduling, collision safety,
geometry proof and atomicity remain executor obligations.

The adapter rejects repeated pose revisions and overlapping already committed
time intervals. After the first successful commit it requires the exact last
receipt revision. The first revision and actual state still require the
executor's independent CAS verification. `CommitReceipt` binds BOOT, command,
revision and checked start/end. `StepResult.committed=True` reports that trusted
receipt, **not independent physical evidence**. Execution/validation errors return
a stopped result and invalidate execution. Public call shapes rejected by Python
argument binding (missing/unknown arguments) instead raise ValueError and latch
STOP through the public entry guard, including when caught inside a verifier.
The guard's receiver is positional-only so an explicit `self=` keyword also
reaches that guard and cannot fail before the veto is recorded.
If a broken/malicious trusted executor
changes pose without the fence or fabricates receipts, this Python adapter
cannot undo or independently detect all such side effects. Such a provider is
outside the valid integration contract and must never be activated.

Normal command expiry clears the action. A newer independently verified command
may use still-fresh evidence and heartbeat. Faults, malformed inputs, clock
regression, explicit STOP, reentrant events or failed execution checks latch
conservatively. Startup missing-input steps remain stopped without granting
anything or preventing the first BOOT.
The busy/reentrant check precedes step argument validation, so malformed dt or
pose revision cannot avoid a BOOT veto. Only ordinary no-active-command polling
(including normal command expiration) is a non-latching idle result. Malformed
arguments and clock/provider failures latch even in an otherwise healthy idle
runtime; they do not silently become normal no-command polls.

## Verification and activation gaps

The 64 current author tests use deterministic software-only dependency fixtures with
actual schema-checked, CRC-framed JSON through the existing validator/watchdog.
The fixture's counter models a commit side effect; it is not a real simulator,
observation receiver, AI-process probe, authentication implementation or board.
RED and intermediate GREEN evidence is preserved under the owning root's
`.planning/deepeye-resume-20261018/pc-direct-runtime/`.
The original 44 tests are retained. PCR-R1 adds nine regressions covering STOP
and caught reentry during BOOT, both clock-callback boundaries, aborted-proposal
replay, a new STOP during recovery, and successful fresh recovery from a known
watchdog timeout. The unmodified independent eight-case probe also passes;
its earlier two failures and all repair RED/GREEN logs are retained under
`.planning/deepeye-resume-20261018/pc-runtime-boot-fix/`.
PCR-R2/R3 retain those 53 tests and add ten methods, including table-driven
malformed reentry/call-shape and clock-result cases, legitimate unverified
identity handling, healthy idle polling and fresh recovery. The exact original
eight-case probe and follow-up four-case probe pass against the corrected code.
Old failures, three-file before/after bytes and repair logs remain in
`.planning/deepeye-resume-20261018/pc-runtime-boot-fix2/`.
PCR-R4 adds one six-entry regression for the receiver-keyword binding gap.
Its original independent failures and the main's RED/GREEN repair remain under
`pc-runtime-fix2-review/` and `pc-runtime-boot-fix3/` in that same planning parent.

Run from the product checkout, with the existing dependency directory supplied
only in the subprocess environment:

```
python -B -X utf8 -m unittest competition.deepeye.tests.simulation.test_pc_direct_runtime -v
```

Before activation, A main must adopt independently reviewed actual BOOT/channel
verifiers, original board/source timing measurement records, C broker/candidate
correlation, actual AI lifetime supervision, full-volume geometry preparation,
atomic executor and process-death STOP, and the real viewer/render linkage.
Only then can matching operation/request/commit-bound runtime/board traces
establish PC_DIRECT behavior. This file does not connect those providers,
enable Run, touch C broker/UI/geometry files, or replace HIL_PC_FPGA. Actual
FPGA observations, AI usefulness, PC_DIRECT end-to-end, C05/G06/H12 and all
formal timing/game/board acceptance remain **not_run** by this software delivery.

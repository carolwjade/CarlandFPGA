# Trusted actor/runtime composition: bounded next dependency

Recommendation to A quality main, not a selection or activation. Job
`child-37334357eaea4e4a91639bad35a47e67`, canonical owner
`/root/worker_results_review_20261018`. Product observed HEAD
`3f702903f1e16fa72eae15f03ba431b78de24bd0`; checkout includes uncommitted candidates.
`input-manifest.json` pins 47 exact raw inputs independently of HEAD. H01-H15 remain
`DEEPEYE-HUMAN-LOCK-20261014/revision1`, canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`, recomputed here.
Main `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2, owns selection and acceptance.

## Recommendation and alternatives

Implement a single authority-owned composition facade that constructs the actor registry,
actor, executor, runtime and private dependency adapter itself. Its `ai_lease` implementation
always calls the original retained actor's method. It owns every admission, STOP and teardown.
Do not accept a whole `AuthorityDependencies`, an `ai_lease` callable, `AiLease`, actor PID,
external actor or executor as production constructor input. Real producer authentication is
absent in this checkout: the initial production channel implementation must reject activation
before native acquisition. Offline tests may replace private factories explicitly; they cannot
provide production defaults or claim live AI.

| Choice | Benefit and cost | Advice |
| --- | --- | --- |
| Private composition plus unavailable-channel admission gate | Closes accidental lifetime-provider detachment and centralizes failure handling; useful offline integration while actual channels are built | Recommended next bounded slice |
| Pass a caller-built dependency object and document correct wiring | Small change, but repeats the independently demonstrated wrong-provider path; type checking does not bind it to the acquired actor | Reject |
| Build real model packaging, continuous IPC, board authentication and viewer Run together | Would permit genuine live integration once proved, but combines unresolved model/platform, IPC timing and four-process dependencies | Split after the composition slice; no fixture shortcut |

## What actually exists

There is no enabled Python production authority composition in the inspected source directories
`simulation/`, `integration/`, `ai_pc/`, `simulator/`. The visible executable foundation is
Godot `simulator/viewer/main.gd`; its lines 11-12 explicitly leave Run/continue disabled and
send Esc through `SceneDocument.stop_requested`. `tools/pipeline.py` is a development-stage
orchestrator, not the authority's live physics loop. The inspected `ai_pc/` contains only
`host_timing/reference.py`; this says nothing about unpublished or separately owned C work.
Do not graft a model fixture into the viewer or make UI callbacks the authority owner.

The taskbook section at lines 240-248 requires separate world_authority, viewer_editor,
hardware_bridge and ai_controller processes. The new facade belongs inside world_authority,
on its one owner thread. It may hold truth for physics and post-run scoring; it exports neither
truth geometry nor geometry rejection details to AI. Viewer truth/render access stays a
different channel from causal AI observations. The real process entrypoint and render transport
are still missing, and this slice does not enable Run or call itself four-process isolation.

Relevant existing seams (full SHA256 and line anchors are in the manifest):

| Source, relative to competition/deepeye | Current role and limit |
| --- | --- |
| `simulation/isolation/actor_owner.py:167,178,362,393,402` | Factory-owned original process acquisition, one BOOT binding, current HANDLE sample, captured-activation revocation and one cleanup attempt. `bind_verified_boot` assumes prior authentication. |
| `simulation/isolation/actor_lifetime.py:9,23,49` | Original reference continuity; strict integer258 nonsignaled observation and fixed deadlines. Returns a recent observation, not future survival or inference health. |
| `simulation/authority/pc_direct_runtime.py:111,261,363,374,442` | Trusted verifier abstraction, BOOT/session retirement, observation/command/heartbeat/AI gates and final callback. Any valid subclass can currently implement a detached provider. |
| `simulation/authority/motion_executor.py:209,234,251,290,326` | Independent revocation, exact BOOT identity, admitted command, full geometry preparation and one final-fence/root-CAS publication. Runtime STOP alone does not clear its pending preparations. |
| `integration/host_envelope.py` | Schema/CRC/context/cross-field checks; explicitly accepts asserted producer identity and authenticates no endpoint. |
| `integration/boot_profile.py`, `docs/boot_profiles.json` | Full canonical profile identity, SHA128 wire prefix and topology/source/acquisition choices; software reference and null/unmeasured identities cannot authorize ENABLE. |
| `integration/clock_bounds.py`, `ai_pc/host_timing/reference.py` | Integer interval/holdover arithmetic; no actual calibrated clock/USB/capture evidence authentication. |
| `integration/sensor_source.py:156` | SourceLedger preserves original EM time, healthy receive time and separate monotonic high-water state; candidate twin_fixture receiver boundary, not live FPGA provenance. |
| `docs/actor_native_probe.md` | Cooperative CPU fixture preparation. Exact READY is expressly not AI readiness/BOOT proof; synchronous write has no timeout/cancellation and is not used by the harness. |

The original detached-provider witness records `committed=true`, pose_revision1 while the fake
actor process is dead. It deliberately used a wrong trusted provider; it is a composition
counterexample, not evidence that correctly routed actor sampling accepts death. R1-R3 repair
candidate manifest `98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670`
is an input, still subject to main's independent review and joint G06 regression. This design
does not rerun or independently accept its 148-method suite.

## Proposed first implementation ownership

After main selection, allocate only these new product paths, relative to `competition/deepeye/`:

1. `simulation/authority/actor_composition.py` — production facade, private fixed dependency
   adapter, same-thread transaction/veto generation and deliberately unavailable production
   channel adapter. This is a library composition entry, not a product Run switch.
2. `tests/simulation/test_actor_composition.py` — offline focused regressions using fake native
   acquisition and private channel test seams with the real runtime/executor and numerical pose.
3. `docs/actor_composition.md` — provider topology, admission failures, ownership, evidence limits.

Do not edit the six repair paths, actor_lifetime.py, existing runtime/executor, current G06
candidate, viewer, C broker or services in this slice. If integration needs changed APIs,
stop and return that exact dependency for a separate ownership allocation. Main should pin the
independently accepted repair plus its accepted G06 combination before creating the test tree;
do not silently combine the old 3f702903 base with a moving geometry candidate.

Proposed production entry is `create_authority(config) -> composition`, followed by owner-thread
methods `accept_boot(event)`, `accept_board(event)`, `accept_observation(event)`,
`accept_command(event)`, `step(...)`, `poll()`, `stop(reason)` and `close(reason)`.
These names are proposed, not existing APIs. The production factory has fixed module-local
ActorRegistry and monotonic clock factories, a reviewed explicit policy and internally selected
channel implementation. It accepts neither general dependencies nor callable verifier overrides.
Config is trusted-main input bound to a reviewed release, not a controller message or readiness
credential. It fixes model/package hashes and budgets; no shell/discovery or arbitrary path.

Create an inactive authority holder first. Check that the fixed real channel implementation
and reviewed AI package are available before `registry.launch`; initial production code always
raises a sanitized `ActivationUnavailable` here. No native effect is needed to establish that
missing readiness cannot activate. Keep the holder and registry strongly retained when acquisition
begins; factory failures cannot lose quarantined contexts. No context manager/destructor may be
the sole retention. Internal test seams explicitly install fake acquisition and verified-event
objects and label their results software-only.

## Mandatory provider topology

The private adapter implements the existing AuthorityDependencies methods. `ai_lease(boot, now)`
has exactly one target: this composition's original actor.ai_lease. It has no setter, override
argument, fallback/cached lease or replacement path. Geometry methods target this owned executor.
Only a private channel verifier implements verify_*; it cannot supply a lifetime provider or
motion executor. The facade returns coarse status and renderer-safe views, never raw runtime,
dependency adapter, actor, process controls, pending step or callbacks to controller/UI code.

Check retained object identities and composition generation before and after external calls and
before dispatch; a STOP/reentrant/malformed entry sets a veto even if its exception is caught.
Do not inspect only bound-method equality: Python produces fresh bound-method objects. Tests
must observe the actual original native Wait and numerical pose, rather than count forwarding.
No extra work follows the runtime/executor final fence; retain full dt, original TTL/source age,
all full-volume geometry and strict executor step_end < deadline. New IPC is never called by
the final-fence path. Python privacy/slots/type checks do not resist malicious mutation inside
the trusted process; enforce the production API and isolation, not a fictional Python sandbox.

## Admission evidence before actor.bind_verified_boot

Neither READY text, a matching hash string, BootBinding, VerifiedEnvelope, main allow JSON,
isinstance nor a caller's `authenticated=True` proves the following. A trusted verifier must
derive its private one-use admission from original owned endpoints and retained local records.

| Evidence | Required association | Missing dependency |
| --- | --- | --- |
| Original acquired actor/channel | Same registry owner, original input/output acquisition references, unchanged epoch and channel instance, exact staged code/model manifest, policy and run; life samples bracketing readiness acceptance | Real AI stage/entry and reviewed bounded persistent reader/writer API. Current private fixture reader cannot be production authority. |
| Actual model readiness | This approved model successfully initialized and can consume the legal causal input and produce the reviewed bounded output schema, using a fresh authority-issued one-use challenge bound to run/session/channel. Record version/model/device truthfully; initialization alone is not C02/G04 usefulness | Real producer implementation and evidence. No READY fixture or CPU dot-product substitution. |
| Board BOOT completion | Original allowed hardware-bridge event, stopped handshake, fresh session, full locally retained canonical BOOT digest matching wire prefix/profile, all context axes and required reply, active configuration epoch; retain operation/request/commit evidence | Actual channel provenance and BOOT verifier; CRC only proves frame consistency. No invented ABI extension. |
| Source/clock/capture | Same source/topology/acquisition/config/session, original observed seq and native sample interval, actual receipt time, validated measured bounds and required capture records. Reject null/unmeasured identities | Reviewed measurement producer and original records. Arithmetic, schema and candidate SourceLedger do not establish them. |
| Continuing AI progress | Fresh request/response correlation to admitted observations, bounded inference/IPC progress deadline independent of process liveness and command TTL | C's real inference/broker protocol and review; living but hung actor cannot keep renewing readiness. |

The challenge/reply is an ownership/replay association over exclusive endpoints, not a new cloud
credential scheme and not proof of useful inference. Select exact wire bytes only with the real
producer owner; do not add unreviewed fields to host_contract or FPGA frames in this slice.
Private admission tokens must be minted/retained by the original verifier after the exchange,
consumed once, and invalidated by epoch/STOP/deadline changes. A serialized receipt can audit
them but cannot recreate them. A subsequent real bounded IPC slice must solve synchronous
write blocking/cancellation and partial consumption; merely wrapping existing WriteFile in a
Python timeout does not establish a bound. Unknown consumption is preserved and never retried.

Production activation stays unavailable until every applicable evidence item exists. Offline
positive test adapters may supply synthetic verified events only behind private test seams;
their success proves sequencing and provider routing, never actual BOOT or AI authentication.

## Activation, STOP and recovery ordering

Use one same-thread composition transaction with an irreversible local veto generation:

1. Gate external commands and steps. Authenticate original actor readiness and board/context
   evidence with finite deadlines. Reserve/consume the proposed session/generation before
   activation callbacks; failures retire it. Fresh process authority startup uses a fresh run
   and verified state, never reconstructs an active BOOT from a disk receipt.
2. Mint one exact BootBinding with factory instance. Runtime.boot's verifier returns that
   same retained object once; activate the owned executor with that identical object; call
   actor.bind_verified_boot with those exact two objects. Recheck transaction/veto, channel
   epoch, current life and all deadlines. Only then open facade command admission. No runtime
   command/step is exposed during partial activation, even though its BOOT is internally set.
3. On any failure, close the facade gate first. Revoke every successfully activated *captured*
   original runtime/executor activation, including failures before actor binding had captured
   callbacks. Check each identity at its dispatch boundary; one callback may change the other
   target. Use try/finally so a throwing STOP does not skip executor revoke or actor cleanup.
4. actor.close retires its epoch before native diagnostics/cleanup and uses captured-activation
   fences from R1. Preserve the primary error and separate callback/evidence/cleanup errors.
   Unknown terminal or release/persistence outcomes retain the registry/context in quarantine;
   no retry, reopen, forced discard or automatic replacement.

Every command is first admitted by runtime; only the original admitted non-STOP command bytes
are then admitted by executor. Either half failing closes the facade and revokes both. Operator
STOP, source loss, mode/config change, malformed events, clock failure, actor death, readiness
expiry, progress expiry, reentry and composition exceptions all use this common path. A STOP
motion_request must never be forwarded as movement. Ordinary no-command/normal expiry polling
is a distinct stopped result: clear/revoke executor pending work without needlessly destroying
a healthy actor, retain runtime's rule permitting a later independently verified command. Every
other rejection conservatively retires this narrow composition; do not parse exception text to
decide. Until a stable explicit idle distinction is reviewed, conservatively closing on all
noncommitted step results is allowed and documented as availability loss, never success.

Poll original actor and progress/source health at an explicit finite configured cadence even
when idle; sample fresh in each runtime admission/fence as already required. Cadence budgets
need native measurement later. Cross-thread events enqueue a private veto, never mutate the
thread-affine executor or close handles there; owner drains it before admission and steps.
The facade guard must veto malformed/reentrant calls before argument validation can bypass it.

Recovery is a new actor, instance, fresh unused session and higher generation, through a new
closed activation transaction. Prefer retiring a whole facade rather than swapping one actor
inside it. Old close/poll/ai_lease/error callbacks cannot affect a new facade or a mixed successor
pair; preserve existing R1 identity fencing and independently fence any new composition callbacks.
World/asset/layout changes invalidate the executor store and require a new run/store/history,
not a BOOT re-interpretation. Camera changes do not change control inputs.

## Discriminating offline counterexamples

Do TDD against the exact accepted combined source, with no native fixture. These are proposed
test obligations, not results of this design job. Use real runtime/executor pose publication;
keep fakes at acquisition and original-event verification boundaries only.

| Case | Required result and discrimination |
| --- | --- |
| Detached-provider witness through new production API | Cannot pass a static dependency/AiLease/provider or adopted actor. Through internal test activation, kill original fake process after valid command/before step; original Wait must veto and pose revision remains unchanged. Old deliberately unwired witness remains historical. |
| Original-target continuity | Different actor/channel with identical label, reused numeric HANDLE/PID, released/ambiguous reference and late old lease cannot redirect the fixed provider. No cached healthy lease fallback. |
| Death/STOP during preparation and final fence | Actual sampling at existing runtime points; no CAS on detected death or caught veto. Death strictly after last sample remains the documented unavoidable observation gap. |
| Missing or forged readiness | Unconfigured production channel rejects before launch; READY fixture, plain dataclass/dict/bool, wrong model/run/session/channel, consumed/stale token and partial/truncated reply cannot reach BOUND_ACTIVE. Count native acquisitions to prove absence. |
| Partial activation | Fail runtime activation, executor activation, bind sample or post-bind gate check separately. No command admission; original activated targets revoked, cleanup once and original exception preserved even when report/callback fails. |
| Callback recovery/reentry | STOP callback advances other authority; each late dispatch checks captured identity. Old close/poll/malformed calls and mixed pairs cannot revoke successor; caught malformed reentry still vetoes outer work. |
| Boundary/clock/progress | Ready deadline, run deadline, AI progress deadline, source time, heartbeat and command expiry are independent; receiving READY/alive sample/duplicate command cannot refresh other clocks. Strict int/bool/IntEnum/clock-regression cases reject. |
| Dual command admission and opaque views | Runtime accepts then executor rejects, broker STOP, forged observation, bad sequence, geometry UNKNOWN, scene edit: no pose CAS; controller never receives raw truth or exact rejection geometry. Normal healthy idle policy is explicitly asserted. |

Run the targeted new suite plus existing actor/runtime/executor regressions once against the
frozen combined dependency set. No unchanged full R03/geometry/UI campaign just for counts.
Record exact imports, fake/native boundary and RED/GREEN failures. Main then independently
reviews before any subsequent real actor or product authority run.

## Dependency order and acceptance limits

First main independently accepts repair and the combined G06 baseline; then select/implement
the three-file composition slice and its offline counterexamples. Next separately agree the
actual C model/inference entry, approved stage compatible with current AppContainer/job policy,
and bounded persistent IPC. Current actor stage cap256MiB/one-process/zero-capability policy
cannot be presumed compatible with a real model/GPU runtime; preserve protection and report
actual incompatibility for main decision rather than silently relaxing it. Then implement and
review original channel/BOOT/measurement verifiers with B/C, test real staged AI acquisition and
ongoing progress, and only then connect the world-authority process and renderer/UI Run state.
Independent authority-death/hang supervision and board execution-side watchdog remain separate.

H12 remains two full legal paths. This slice composes PC_DIRECT only; it never routes that mode
through mandatory FPGA actuation, and does not reinterpret HIL_PC_FPGA board-capture evidence as
host execution. HIL_PC_FPGA needs its separate accepted executor/provider and original physical
capture chain; FPGA_LOCAL is a protection/control comparison. Mode switch stops and establishes
a fresh verified BOOT. AI input on both paths is actual FPGA observations plus legal public task
geometry/odometry; no truth layout, future sensor values, exact collision oracle or renderer feed.

Execution-plan dependencies remain unchanged: C05 depends R03/B05/C04; G04 depends G03/C01/C02;
G06 depends G02/G04/G05/G09/C05; G07 depends A02/G06/C03. C owns actual model/planner/broker;
A owns authority/secrecy integration and physical board operations. This proposal grants no new
cross-owner writes. Useful AI, both complete H12 chains, real source/capture/timing authentication,
four-process denial tests, live render/Run, game quality, hardware and all29 formal cards remain
not_run. A recent original-HANDLE observation still cannot prove future survival through CAS,
responsive inference or task benefit. No native/product execution occurred in this design job.

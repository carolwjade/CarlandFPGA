# Causal inference progress in the existing final fence

Design recommendation to the sole A main, not implementation or acceptance. Job
child-9b77838d22574ae49550293f0b1d61c3; owner /root/worker_results_review_20261018.
H01-H15 remain DEEPEYE-HUMAN-LOCK-20261014/revision1, canonical requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804, recomputed here.
The active transfer still names Desktop01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2.
Input-manifest.json pins44 raw source/evidence files. Product observed HEAD is
2f5fb02d1679168d71ef9b0a02ceaa540708cc7b; exact source hashes establish identity.

## Recommendation

Extend the accepted actor_composition itself with a private, activation-owned progress gate.
At the existing _Dependencies.ai_lease seam, always sample the original actor, then combine
that lease with the current command's immutable, verified inference-completion deadline:

`combined.deadline_ns = min(original_actor_lease.deadline_ns, bound_progress_deadline_ns)`.

Keep its original boot and instance fields; reject malformed life results before constructing
the combined AiLease. Do not replace actor.ai_lease, use channel.ai_lease, introduce another
facade, or edit the accepted runtime/executor. The runtime already calls this seam at command
admission, before/after preparation and inside its actual before_commit callback. Its post-provider
clock check and the executor's strict whole-step end<deadline check consume the combined minimum.
The final path reads only owner-local gate state and the existing original HANDLE sample;
it invokes no channel verifier, IPC, model, logging or extra external work after the fence.

An authentic bounded progress source cannot yet be implemented from the available model/backend.
The smallest executable next slice is a concrete library gate and actual final-fence wiring,
with synthetic original-completion evidence in private offline tests. Production must continue
raising ActivationUnavailable before registry construction. An accepting readiness verifier alone
must never enable it. Real original completion provenance is a separately owned prerequisite.

| Approach | Consequence | Advice |
| --- | --- | --- |
| Private progress gate and combined existing AiLease | Makes progress constrain the actual runtime final fence without changing ABI, physics or motion interfaces | Select this narrow next slice |
| Call channels.checkpoint again in/after geometry or at commit | A boolean/callback has no stable deadline and can block/reenter; another early call can still become stale | Reject as the solution |
| Add a new runtime progress-provider API or full supervisor | Could express more health dimensions later, but broadens accepted interfaces and ownership unnecessarily | Defer unless the real producer shows this seam is insufficient |

## Exact witnessed gap and current source path

Read the entire independent findings.md, negative JSON and counterexample source. Main selection
actor-composition-main-selection.json SHA256
68d826276c8eb4ebdb8ddcb61f8158619b5aa179c57fe904119807e110ade67f accepts only the deliberately
unavailable-production software scope. The independent negative witness sets FakeChannels.healthy
false after actual executor.prepare_step returns. It observes committed=true/revision1, then
owner poll retires to CLOSED. It is an honest missing-dependency witness, not a production defect
hidden by the acceptance or an AI-safety PASS.

Current _channel_health runs before step; _Dependencies.prepare_step checks only composition
veto after geometry, and _Dependencies.ai_lease returns only original actor life. Runtime._ready
combines command TTL, observation age, STATE8 heartbeat and that life deadline, but has no
inference-progress deadline. Its before_commit repeats _ready immediately before executor CAS.
Executor.commit_step permits no callback/clock/geometry/I/O after before_commit returns. Therefore
the right insertion is inside the existing AiLease dependency, before the final StepFence is
returned, not a pre-step boolean snapshot or a post-CAS stop.

The old synthetic .healthy flag is not a production progress interface. Preserve that original
witness as historical evidence. The discriminating new safety test below replaces the fake boolean
with an explicit original progress deadline that expires during the same geometry hook. Known
channel failure must post the existing owner veto/STOP or invalidate this gate; merely flipping an
unobserved test attribute cannot itself be an authenticated failure notification.

## Producer and schema facts

The inspected PRODUCT ai_pc contains only host_timing/reference.py; it has no real model launch,
backend completion monitor or causal inference-progress producer. The separately managed local C
PR25 reference checkout was read at HEAD942fa309ffc8f1d32c816cfa643b009b031d7d0a. This is a
local exact-source interface reference, not a new remote readback, adoption or review of that head.
Do not reuse the older31267d6 no-current-fix conclusions for its changed bytes.

The existing host_contract model_candidate already carries context, candidate_id, model_sha256,
observation, completed_monotonic_ns and target. Motion_request carries candidate_id, command_seq,
observation, host_issue_monotonic_ns and target; it does not carry model provenance or a progress
lease. C's current MotionRequestAdapter and RuntimeCheck preserve candidate/model/completion and
original timing, require completed<=issue<=now, consume candidate IDs and use a trusted RuntimeVerifier.
Its mailbox retains at most one completed candidate with a high-water key, four sent observations
and original completion time; exact duplicate delivery cannot requeue consumed work. C's causal
input module supplies masked, observation-bound feature windows, not an actual inference backend.

These are useful correlation/arithmetic interfaces. None authenticates completion merely because
bytes parse, a timestamp is <=now or a callback accepts it. A's host_envelope._check_candidate
also only bounds the declared completion against host now and checks target/observation structure.
No new JSON kind, FPGA frame or parallel model schema is needed. Keep original candidate/request
bytes and reuse the same whitelist and causal keys; trusted completion-measurement metadata stays
authority-private until its real producer/IPC contract is reviewed with C.

## Distinguish four evidence layers

| Event/evidence | What may be concluded | Motion progress renewal? |
| --- | --- | --- |
| Pipe received bytes or transport ACK | This endpoint delivered these bytes at a local receipt time | No |
| Request queued, model started, heartbeat or intermediate work | Some bounded protocol/execution activity occurred, if authenticated | No completion lease in this first slice |
| Original trusted backend completion correlated with the actual causal invocation and candidate | This approved model completed this invocation within a verified host-time interval | May establish one bounded progress record, subject to all other gates |
| Independent model/planner trials and useful causal decisions | Evidence toward H11/C02/C03/G04 usefulness | Separate task acceptance; a progress lease does not establish it |

The original actor nonsignaled sample remains necessary in every positive lease. An alive but
stuck model fails progress freshness; a completed result from a dead/replaced actor fails life.
Neither renews source age, command TTL, board heartbeat or the fixed actor/run deadlines.

## Minimal owned implementation slice

After main selects this design, allocate changes to exactly these existing PRODUCT paths,
relative to competition/deepeye:

1. simulation/authority/actor_composition.py — private per-activation gate, required immutable
   progress-age policy, private verified-completion correlation on command admission, and the
   actual combined AiLease path. Production unavailable gate remains unconditional.
2. tests/simulation/test_actor_composition.py — explicit synthetic completion evidence and the
   discriminating final-fence/replay/clock/identity tests. Preserve all current24 assertions.
3. docs/actor_composition.md — progress policy/evidence/API and unimplemented source obligations.

Existing actor_owner/lifetime, runtime, executor, G06, host schemas and C files remain read-only.
No native fixture/harness/source38 snapshot or retained interpreter48521 is a dependency to touch.
No new background process, service, public adopted provider or alternate production construction.

Proposed private interfaces, not currently implemented APIs:

* Add required AuthorityConfig.progress_max_age_ns: strict positive int in the existing bounded
  host-time range, immutable for the composition. No numeric permissive default or per-message
  widening; main selects measured production values separately.
* Private _ProgressGate is created for the exact activated BootBinding/original actor and authority
  monotonic-domain identity. State is EMPTY, BOUND_TO_COMMAND or irreversibly REVOKED. It retains
  one current command record, consumed candidate/invocation high-water identities and a monotonic
  clock high-water value; no unbounded receipt history or reset within activation.
* Extend the private channel verifier obligation with completion_for_command(original_event, boot).
  It must retrieve original model_candidate bytes plus trusted backend completion association for
  this exact accepted motion_request. Missing association raises. It cannot manufacture progress
  from the motion_request alone, take a caller's deadline or return an alive boolean.
* _Dependencies.verify_command uses its already verified original command, existing host-envelope
  validation and the new private correlation obligation before runtime.command reaches _ai.
  STOP bypasses completion prerequisites and keeps its immediate retirement path. Invalid proposals
  remain consumed/retired; a later error closes this composition rather than rolling back freshness.
* _Dependencies.ai_lease samples original actor then reads/checks the local gate's exact binding,
  command and generation. It returns AiLease(life.boot, life.instance_id, min(life.deadline_ns,
  progress.deadline_ns)). It never invokes completion_for_command/checkpoint/other channel code.

Private verified records are verifier results, not credentials. Real production code must mint
and retain their association from original endpoints/backend records; neither class identity nor
a local dataclass proves it. Tests may patch only the private unavailable factory and synthetic
verification boundary. No public record/deadline setter or fake producer is added to the factory.

## Correlation, timing and nonrenewal rules

The original completion association must bind the exact actor acquisition/instance and channel
epoch, exact BOOT/run/session/config/profile/source/topology/acquisition, approved model hash,
causal invocation identity, original admitted observation and candidate bytes. Compare candidate_id,
observation and full target against the original request; bind its command_seq and raw digest.
An unrelated newer inference cannot extend the old command's gate. A new accepted candidate may
establish its own record only while the prior progress state is still healthy; detected expiry
or invalidation retires the activation. Recovery requires new composition/actor/fresh BOOT.

Keep the candidate completion timestamp already in the schema as a claim until the original
trusted producer establishes its domain and content. Remote wall clocks, board ticks and GPU
device event counters cannot be compared directly with authority monotonic_ns. Require reviewed
same-host/same-monotonic-domain binding or a verified conservative conversion interval. Without
that provenance, production stays unavailable. Never solve it by supplying a domain string.

Use a verified completion interval [completion_lower_ns, completion_upper_ns], with an original
causal dispatch lower bound and authority receipt clock. Require strict bounded integers (reject
bool/IntEnum/subclasses), valid ordering, no future completion/receipt, and no observed clock
regression. Clock high-water advances on trusted time observations even when later payload or
duplicate validation fails. The public caller does not provide this trusted now value.

Receipt time is an upper bound on an earlier event, so receipt+age_cap is unsafe freshness.
Compute progress_deadline=completion_lower_ns+fixed_progress_max_age_ns, rejecting overflow.
If no tighter genuine completion lower bound is measured, the original causal dispatch lower
bound is a conservative lower bound on that invocation's completion. It may be used explicitly
and labelled as such, at the cost that inference and delivery consume the same freshness budget.
A timestamp taken just before querying an already-signalled backend fence is not automatically
a lower bound on when it actually completed. No receipt-latency subtraction is valid without a
reviewed bound. If even a trusted dispatch lower bound is absent, admit nothing.

The same candidate/invocation/result/command redelivered retains the original earliest deadline;
new receipt times, later clock samples, model heartbeat and positive life samples cannot extend it.
Same identity with changed payload/model/context/target/completion association fails. Lower consumed
IDs/order and revoked/expired records cannot reappear. If a verifier later tightens an interval,
take min(old_deadline, derived_deadline), never an increased lower bound that renews old work.
Retain these high-water rules after consumption/expiry; a new namespace needs a new activation.

At each combined lease, capture the local gate generation before the original actor sample, then
recheck it, activation identity and veto afterward. Revocation cannot be undone by a caught
callback or fake restoration while Wait is in progress. Gate updates are owner-thread only;
foreign notification sets the existing pending veto, not a foreign lease mutation or executor
call. A positive record is never reset to EMPTY to hide a timeout.

Runtime already samples its fixed clock after the provider and checks the current whole dt
against every minimum. The returned StepFence deadline includes progress as well as life,
command TTL, observation age and heartbeat. Executor additionally requires step_end<deadline;
an end exactly on the progress deadline fails. Do not shorten dt to a safe prefix, renew a
command or perform any extra check/IPC/log after that final callback and before CAS.

## Concrete RED-to-GREEN and other discriminating tests

These are proposed tests, not newly executed results. Existing independent evidence is preserved;
this design does not rerun the172+5 suites or relabel its negative witness.

1. Start with current numerical composition fixture at clock1,000,000,000ns, actual actor alive,
   valid observation/heartbeat/command, and dt1,000,000ns. Give the synthetic original completion
   a fixed deadline1,005,000,000ns. The early whole-step check fits. In the same executor.prepare_step
   hook used by the independent witness, advance clock to1,005,000,000ns after real geometry returns.
   All other current fixture deadlines still permit the step. Existing code ignores progress and
   can commit; the safe assertion is committed=false/revision0, stopped original targets, cleanup
   once. New combined lease must fail at the post-prepare/final checks. Add a second case that
   advances only inside commit_step before before_commit, proving an early/post-prepare snapshot
   is insufficient too.
2. Keep now before expiry but choose dt whose end equals or exceeds that same original progress
   deadline. Require full-dt failure/revision0; dt ending1ns earlier succeeds with exact original
   command and a real numeric pose revision. Verify the actual executor StepFence deadline is
   the min, not only a method-call count.
3. For the same original completion/request, redeliver at a later receipt clock and replay an
   identical candidate after consumption. Deadline never increases. Alter its payload, model,
   target, completion timing or observation under the same identity; reject. A newer completion
   for another command cannot prolong the current command. An expired gate cannot be restored
   by later completion, alive process, higher receipt timestamp or reset.
4. A dead/replaced/released original actor with a very fresh progress record still vetoes. A
   nonsignaled original actor with missing/old progress vetoes. A channel static AiLease cannot
   substitute. Synthetic ACK/queued/start/heartbeat events do not establish completion.
5. Wrong activation/channel/model/invocation/clock domain, malformed integer shapes, reversed
   or future intervals, overflow and clock regression fail closed. An unknown/missing producer
   raises before registry construction in production. Candidate JSON/completed_monotonic_ns
   alone cannot enter a progress gate; retain source-authentication gaps explicitly.
6. During original Wait, invalidate gate or catch malformed/reentrant/foreign input. Generation
   and owner veto checks prevent a lease/CAS even if a fake callback tries to restore data.
   Preserve current partial activation, captured-successor callbacks, strong cleanup and
   post-CAS veto accounting: a veto after an observed commit cannot undo its recorded fact.

Use existing24 tests plus focused additions and the unchanged original actor/runtime/executor
regressions against one frozen accepted dependency set. Main independently reviews exact bytes,
RED/GREEN and imports before acceptance. No broad R03, UI, native or board campaign is needed.

## Next real dependency and acceptance boundary

After this software slice, C/main must deliver the approved real model/backend execution entry
and original completion monitor, correlated original causal input/candidate logs, reviewed host
clock bounds and bounded persistent IPC. A implements/reviews the actual original-channel
verifier and readiness/BOOT/measurement provenance. Only then can the missing production factory
be considered for a separately reviewed activation change. Package/device/isolation compatibility,
current actor budget constraints, progress time budgets, owner-hang/death supervision and physical
execution-side watchdogs require actual evidence. The existing synchronous I/O and post-sample
death race are not solved by a numerical progress deadline.

Keep H12 PC_DIRECT and HIL_PC_FPGA full paths legal and separately evidenced; this slice adds an
authority gate for PC_DIRECT without forcing FPGA actuation. HIL requires its own accepted
board-output/capture path. Neither can borrow the other's causal execution proof. No truth layout,
future sensors, renderer input or precise collision oracle enters the controller. Meaningful AI,
both complete H12 paths, genuine readiness/BOOT/source/time authentication, native product Run,
four-process isolation, game/board and all29 formal cards remain not_run. Original native
interpreter48521/source38 snapshots were neither inspected nor operated by this design job.

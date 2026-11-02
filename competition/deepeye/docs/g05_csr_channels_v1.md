# Explicit G05 CSR demo production route

This new default-off route verifies real Root-owned `OriginalG05OperationBinding`
and `OriginalChainReceiptProducer` events. It preserves the original registered
ActorComposition, owned AI process/invocation, candidate mailbox, command fence,
full-volume collision, pose CAS, world publication and next-source lifecycle.
It neither modifies the four frozen C42 source files nor claims that the old
C36 private-PL schema accepts the new CSR transport.

The selected endpoint94/B131 path is **outer ABI3, kind 0xE4, payload revision2**.
B131 checks CRC and invokes the unchanged TRACE payload revision1 parser after
replacing only the payload revision byte for that parser. Four returned singleton
frames and all four original companion byte strings are retained. Public ABI3
type7/rev1 is another telemetry format and is not substituted into this route.
RAW remains RAW; no compression benefit or physical-sensor origin is claimed.

`G05_CSR_INIT` is a genuine same-load full13-word identity/BEGIN/readback fact.
The resulting local BootBinding binds that verified CSR session to the actual
new AI process instance. It is not a UART BOOT_ACK. Typed CSR status and exact
raw readback receipts provide health; no STATE8 or public board_response frame
is manufactured. Host QPC and board monotonic/cycles stay separate. A host lower
bracket plus the originally selected board duration supplies a conservative
host lifetime cap, without equating clocks or renewing the board deadline.

Original BOOT/COMMAND/STEP transactions exclude source access. The channel's
pending check accepts only that exact retained transition, original busy owner,
configuration/clock/producer/context and original world binding. BOOT/COMMAND and
pre-CAS STEP still require APPLIED publication; post-CAS STEP requires the exact
original committed slot and its original pending-publication gate. It never
enters source acquisition or calls ProjectionSession while source is excluded.

Root selects `G05CsrPolicy` and the frozen new demo AI descriptor explicitly in
AuthorityConfig.g05_csr_v1; the default remains None. Then, after the one actual
pre-source init, `select_original_g05(config, cycle.binding)` registers that
exact binding for the original factory. No JSON, caller callback, verified=True,
foreign session or restored snapshot can activate this factory.

Minimal original-owner call order:

1. Build the real ActorPolicy from the new descriptor's fixed files and runtime.
   Select the same descriptor's model hash, explicit PC_DIRECT consume window,
   source/progress/health bounds <=5s, and original finite bootstrap limits.
   The new `OwnedInvocationPolicy.demo_duration_v1=True` may select prospective
   command validity up to1000ms. The default remains100ms. This validity permits
   a finite command to remain usable while the next actual scan occurs; it is
   neither automatic motion nor a continuous trajectory. Each STEP still has
   an explicitly chosen small dt and all original fences.
2. Validate pre-source plan, acquire the real SSH/ChainSessionV2, run the actual
   init once via `prepare_pre_source_cycle`, and immediately register the binding.
   Init consumes the unchanged <=10s board session. Do not init and wait for code.
3. `FiniteActorBootstrap.start()`, then `.accept_boot(cycle.init_event)` starts
   the source only after the original factory verifies the real CSR init event.
   Obtain `channels_for(config)`, call `.attach_started_source()` and
   `.attach_latest_transition()` after the actual BOOT/source start.
4. Activate the original deferred scanner; enable the original pump. Consume every
   real ordered source_admission event with channels.accept_source_event. Never
   fill missing slots, manufacture C3/EM values or move source origin.
5. For the first demo scan choose an actual native EM sample with
   adc_tick==em_tick and a valid C3 window (at least90ms real source history).
   A native sample can be selected at a real50ms grid point after the source has
   warmed. No pre-board sample is passed to AI as a historical observation.
6. Run producer.scan_actual once. It may issue earlier pumped source events while
   waiting; consume all pending source events before the returned trace event.
   channels.prepare_observation(trace_event) checks the actual E4/companion group,
   retains the actual source token/capture and obtains an original getter/registry
   hold. Actual producer.status events may be admitted with composition.accept_board
   for new CSR health; they do not refresh source or inference deadlines.
7. composition.accept_observation(original_mapped_event) retains the mapping
   inside that exact active observation transaction. Its owned invocation uses
   the selected genuine child package. Pump the original source while polling
   the actual invocation; use the returned original completion event with
   inspect_owned_candidate/accept_completion. Record real quality/age values.
8. channels.broker_next() returns None until an actual configured legal window
   contains a ready original completion. On a returned original broker event,
   composition.accept_command(event,slot_event=event) verifies that same candidate
   and window. After it returns, attach_latest_transition, then STEP through the
   original executor/collision/CAS and attach its actual completed transition.
9. Continue the same source and choose the next actual native EM sample after
   motion. Its second real TRACE scan proves next-source closure. The original
  2TRACE/2command/10s profile may suffice for this bounded demonstration; failure
   to fit remains a failure, with no counter reset or same-operation replay.

Only actual board-returned observations enter public history. Held EM requires
its actual previously captured native origin, so the shortest demo chooses
native EM samples. The new G05 host projection verifies original token/Book,
capture bytes, four frames/companions, actual getter/registry hold, unchanged
current Root and real executed-action receipts before emitting the bounded
public input. It emits no scene truth, geometry queries or hidden object fields.

The new <=5s profile and longer finite command validity are preliminary demo
choices. Actual age and original100ms quality remain visible. Original final
1%/100ms/100MHz, H01-H15, both H12 and original29 acceptance are unchanged.
This source delivery does not itself establish actual native/board/AI/motion
success. The NEW parser controls are explicitly synthetic software examples,
not proof of original production provenance or authority.

The adapter retains separate dispatch, actual RESULT observed-upper and completion
admission quality reports. The broker recomputes quality using its actual issue
QPC as well. `channels.latest_quality()` returns detached diagnostics; no report
changes a sample timestamp, renews a deadline or authorizes an action. A fast
dispatch quality flag is never promoted to a later completion/command quality.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.

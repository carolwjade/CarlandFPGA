# Actual891 — first-send update starvation, not missing AI/E4

One-shot895 ran once, then read-only arithmetic/code diagnosis. Original observer
output/logs preserved. No board/UI/network/model/source/native re-execution, new
tests or source edits. Contract revision2 requirements2afd...; all29 not_run.

Actual: INIT, five returned sense IOs, four E4/source events and four native source
registrations, four ADVISE completions, one positive host command. No board APPLY
or PWM event. Fifth sense was already inflight at failure and completed/settled
in cleanup; it was not admitted/used for another actual AI decision.

Native actual pose12.10000038,10,15.61999989 →12.10000038,10,15.61354351,
6.456mm, max actual speed.025m/s, revision53, history INITIAL_OUTSIDE only.
Primary host-events588: NATIVE_SAFETY_FAULT:pc_direct_observation_or_command_expired,
actual native fault preceding it at587. No collision/other geometry-failure field.

|Actual AI event line|Status/reason|Acq→completion ms|Current pose→completion ms|
|---|---|---:|---:|
|553|ADVISE / continuous_em3_public_exit_search|615.979414|36.792513|
|560|same|643.981014|31.620113|
|567|same|613.923415|37.324314|
|584|same|905.784326|37.488403|

All same A-CONTINUOUS-DIRECT-WORLD-891-R01; speed limits.03159–.03219m/s,
all selected straight FAST code2. Only one operator event, original start seq1.
Numeric generations were not logged. However all four actual-AI-completed rows
are emitted ONLY inside controller889:282 ai_generation==operator_generation;
thus they were not discarded as foreign generations. The real world epoch also
matches. This is not AI STOP, epoch rejection, saturated/faulted E4 or missing data.

Command1(host-events579) references sense3, original acquisition43066494439585,
first_send43067653123700, original host deadline43067994439585. It was already
1158.684115ms old on first send; response carried only315.732ms conservative native
validity (read417495138us, deadline417810870us). It cannot legally be extended by
reusing its original acquisition. Sense4 registered at581; AI4 completed584 with
its genuinely later source43066823249874. A command from that original source
would cap at43068323249874,328.810289ms later than command1, without redating data.

Root cause in actual exact c885 controller:
- Root_live_controller889.py:204 samples now BEFORE native.state().
- It passes that stale earlier value to pc_advice_applicable at294.
- integration/live_pc_direct.py:51 requires AI completed<=now, and53 requires
  0<=now-current_snapshot_lower<=250ms. The current snapshot was acquired by the
  LATER native.state RPC, so the old now can precede the new original acquisition.
- Actual native lower bounds are only4.003–46.045us before RPC send (median16.015us).
  Controller work/serialization before the RPC send can exceed that tiny slack.
  All post-motion observations have only4.003us slack. The one accepted command
  immediately follows the unique largest46.045us slack at event578. It then never
  refreshes despite fresh source4/AI4.

No loop-now scalar was retained, so the exact negative age per rejected iteration
cannot be directly reconstructed. This distinction is explicit. The causal code
ordering is wrong independently; recorded intervals and unique successful slack
strongly identify its practical manifestation. At actual recorded receive times,
23 post-AI/pre-fault samples have fresh source<1500ms and current-read age8.66–93.91ms,
with completed AI already available, while pose change is only6.456mm/no heading
change. These receive-time calculations are diagnostic counterfactuals, not
fabricated dispatch timestamps or new actual executions.

Smallest prospective fix: take a NEW perf_counter_ns() after native.state and
again immediately before expiry/applicability/dispatch checks that follow other
blocking RPC work. Keep original source/current acquisition timestamps unchanged.
Do not remove the negative-age guard, enlarge1500/250ms, renew original command1,
change FAST TTL/mapping or replay891. The command hash/source3 differs from newer
AI4, so chosen_hash comparison at297 would allow a genuinely new command once the
legitimate guard is evaluated in the correct time order. Root owns any new fix.

Cleanup: RESULT.board_stop is null because this failure used original finally
BoardSession.close. Its genuine CLOSED.stop_response is STOP6 COMPLETE/unknownfalse,
status3/fault6/stop_write_returnedtrue; original RESULT.board_close equals CLOSED.
SSH exit0/waittrue/not-killed. This is not a missing stop or physical-zero capture.
No old command or uncertain effect was replayed.

Observer's separate board_ledger_other_event atline1 is normal init-returned,
a classification gap in prepared895, not a runtime error. OBSERVER_ANNOTATION.json
states this without editing/rerunning original observer output. Other observer
errors are the real expiry fault/primary. No E4/host/native correlation discrepancy
was found. CRC was checked once by the observer, not rerun for diagnosis.

884 is a new PC_DIRECT candidate, not actual PC_DIRECT execution evidence.
Revision2 requirements2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d.

Product files:
- integration/continuous_native_client.py is exact822 bytes, unchanged schema.
- integration/live_pc_direct.py explicitly subclasses it for the883 extension.
- controller884.py is a separate Root-run candidate derived from frozen847.
Original847/822/actual835 evidence are untouched. Root owns native, mode selection,
all board/UI/native startup and the final integration/review/publication.

Controller config/frozen.json must agree on admission_mode, BOARD_PWM(default) or
PC_DIRECT. Native must be installed with the same mode/world_epoch before connect.
The original RunControl, publish_display, advice_applicable and stop_native_once
ASTs are identical to847; original board apply branch remains under not direct.

API (actual startup/ports/tokens belong exclusively to Root):

    from competition.deepeye.integration.live_pc_direct import PcDirectClient
    client = PcDirectClient.connect(port, token, world_epoch=epoch)
    client.bind_board({k: actual_init[k] for k in
                       ('boot_id','build_id','request_hash')})
    original_snapshot = client.state()  # preserve EXACT native+Host-QPC wrapper
    # Root passes this actual snapshot to793; keep it with future/pending/sense.
    registered = client.observe_pc(original_snapshot, source_payload,
                                  actual_sense_wrapper, source_seq=source_seq)
    current = client.state()
    accepted = client.apply_advice(actual_completed_advice, current,
                 command_for_advice(actual_completed_advice,current['native'],
                                    control.speed_limit(),control.paused),
                 ttl_ms=3000, paused=control.paused,
                 operator_cap_m_s=control.speed_limit())

source_payload is original793.to_payload(); actual_sense_wrapper is the real822
BoardSession result (response, response_sha256, host_before_ns,host_returned_ns).
No counts/quality/frame digest are invented; verify_e4 independently checks the
original codec, CRC, four lanes/source/tick/quality/continuity and binding. Native
witness MUST be the original source snapshot's witness, not the observe reply's
new witness. Host acquisition is exactly that original read bracket lower bound.
The registered-observation lookup retains older genuinely fresh observations for
1500ms, so a later latest native observation does not relabel an older AI result.
State board_observation_sha256 is the actual sense RESPONSE digest; the separate
board_frame_sha256 hashes original E4 wire and is in observation/command fields.

apply_advice emits EXACT883 command_json canonical ASCII string + SHA256. Integer
codes and decimal-string times avoid float canonicalization across Godot/Python.
first_send is read once from the original Host-QPC clock; deadline=min(first_send
+TTL<=3000ms, ORIGINAL acquisition+1500ms), conservatively translated with822
ClockBracket (including its existing drift assumption/guard). Native independently
uses its own original witness acquisition tick. A duplicate/rejected/unknown write
is never replayed. Actual command+digest/deadline is available as last_pc_command.
The native receipt is checked for exact PC seq/hash/target and a deadline no later
than the submitted conservative one. There is no board capture/PWM/STATE/Book fake.
Current native read must be<=.25s and original source pose<=.25m/15deg. Positive
speed must be within actual AI limit and initial/mode cap. C3 remains genuinely
null. Source fault/saturation/held/foreign epoch/binding/stale samples cannot move.
The source/AI work remains actual793/797, not rerun by these preparation controls.

Controller retains source snapshot/witness with source_future → source_pending →
sense metadata. Genuine E4 is admitted to native before actual AI submission.
PC commands are synchronous localhost calls, independent from the single-inflight
real board sense worker. No normal board.apply exists on the PC branch. Fresh AI
changes target; an unchanged still-valid target keeps advancing in native between
source/AI/RPC boundaries. No healthy mission command/time budget is introduced.
Paused control can consume still-applicable original held ADVISE to issue an exact
zero HOST command; stale observations cannot mint a zero lease. First reservation
consumes initial preference only AFTER genuine native acceptance, including zero.
The unchanged RunControl stores subsequent slider input for a new run only.

Terminal/failure immediately attempts original stop_native_once. If a socket write
became unknown and822 poisoned the client, controller immediately closes that
socket (native disconnect safety), never replays the write, then closes source/AI,
settles original pending board IO and executes unique real board STOP/SSH close.
That terminal native STOP is explicitly not a board acknowledgement or measured
physical zero. Normal ARRIVED remains recorded even though native then stops.

Necessary preparation command (pure local socketpair + public835 fixtures only):

    PYTHON -I -S -B -X utf8 O7/continuous-pc-direct-host-884/controls884.py

Both executed revisions exit0; r1 stdout preserved. New tests cover old822 schema
red/new explicit extension green; unknown/foreign state rejected; actual835 E4 raw
CRC/source integrity and foreign binding; canonical command/real origin FAST bound;
TTL3001/stale/upward cap rejected; latest observation differing from selected older
fresh source; one attempted socket write on EOF then no retry; exact822 hash and
four protected847 ASTs. No old tests/model/PDE/RTL/native/UI/board execution.
Actual835 fixtures are historical public bytes, NOT current hardware authority.

Root remaining: review native883 implementation against these fixed fields; new
exact source publication; new unique mode-labeled operation/world/socket/token;
Root-only actual source→E4→AI→host-command→native continuous crossing and separate
recording/cleanup. Original835 success cannot qualify this missing direct path.
Full29/G03/R03/formal quality/dual-H12 acceptance remain not_run.

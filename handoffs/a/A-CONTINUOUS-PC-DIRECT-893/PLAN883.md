# Continuous PC_DIRECT implementation plan

> For agentic workers: execute the independent host/native tasks with subagent-driven-development. This is the already human-authorized H12 design, not a new scope proposal.

Goal: preserve the completed835 BOARD_PWM demonstration and add a separately evidenced continuous PC_DIRECT path using real board observations and the same native rigid-body motion writer.

Architecture: 793 actual own-pose source → real791 sense/E4 → 797 AI → new explicit PC_DIRECT host command → existing794 Law/Guard/Main writer. PC_DIRECT never calls board APPLY or fabricates PWM/STATE8/Book proofs. Both modes perform real initialization, stop and SSH close. Current immutable revision2/requirements2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d and initial-only human rule apply. Full29 remains active, final quality not_run.

Previous turn: progress (actual835 complete, actual video,866 display correction, byte-exact publicationbd4a1a61...,868 real recovery). Current board SDK idle; native835 stays terminal/open, do not replay it. Three protected ZIP deletions and all other owners remain untouched. Never inspect R/.local/deepeye-implementation-a.

## Design choice

- Chosen: explicit new live admission attached to794, existing source/AI/clock/motion semantics reused. Old original-object broker cannot consume793/797 dictionaries. This directly fills880's evidenced gap.
- Rejected: fabricate original Book/STATE8 or PWM receipts; these would prove another system. Also rejected: a second pose/tween renderer or boardless fallback.
- Use existing fast_9600 motion mapping and FAST safety ceilings (source age1500ms, first-command TTL3000ms). No STRESS speed/age mixing. Late data may not be redated; no mission command/time budget. Formal FAST timing/quality acceptance remains separate.

## Frozen native extension contract

ABI stays DEEPEYE-CONTINUOUS-NATIVE-794-v1. install/Main bind gain optional admission_mode='BOARD_PWM',world_epoch=''; PC_DIRECT requires an explicit nonempty epoch. Mode is immutable per instance. Default BOARD_PWM public state keys and apply/pause behavior remain byte/schema compatible with822.

PC_DIRECT state adds ONLY: admission_mode='PC_DIRECT', action_source='pc_direct_host', world_epoch, source_witness (32 hex), board_observation_seq, board_observation_sha256, source_record_sha256, observation_native_tick_usec (decimal string), pc_command_seq, pc_command_sha256. The existing board_request_seq/board_receipt_sha256 stay0/empty in direct mode; they are not host command fields. Extra fields exist only in direct mode. The direct client explicitly validates this extension and then delegates the stripped base state to822 validation.

Every successful PC_DIRECT RPC response gets a new source_witness tied inside native to the exact returned accepted tick, revision, position and orientation. Native retains witnesses only for the1500ms valid age window; this is resource retention, not a mission operation cap. UI-local state calls do not mint witnesses.

New observe_pc RPC fields:

    world_epoch, source_witness, board_sense_seq,
    board_receipt_sha256, board_frame_sha256, source_record_sha256,
    source_acquisition_qpc_ns (decimal string), source_segment_id,
    source_position_m[3], source_orientation_xyzw[4],
    board_binding{boot_id,build_id,request_hash}

The new host client verifies the original COMPLETE/unknown=false sense response against real init binding, original source digest/counts/quality/E4 frame digest and the actual native snapshot/Host-QPC lower bound before sending. Native consumes only its own unexpired witness matching original pose/revision segment, increasing board sense seq, fixed epoch/binding and hash fields. It stores native acquisition tick from its own witness, never a supplied fresh timestamp. Receipt returns the genuine observed fields; no motion change occurs here.

New apply_pc_direct / pause_pc_direct RPC fields are command_json (canonical ASCII JSON string) and command_sha256. Native hashes the exact string before parsing. Its exact command keys:

    abi='DEEPEYE-LIVE-PC-DIRECT-COMMAND-884-v1', mode='PC_DIRECT',
    world_epoch, profile='fast_9600', command_seq,
    first_send_qpc_ns, source_acquisition_qpc_ns (decimal strings),
    board_sense_seq, board_receipt_sha256, board_frame_sha256,
    source_record_sha256, ai_result_sha256,
    speed_code,yaw_q,pitch_q,ttl_ms,
    native_deadline_usec (decimal string)

All values except identifier/hash/time strings are integers, avoiding cross-language float canonicalization. Host generates first_send from its real clock once, validates original actual ADVISE/STOP/source applicability and mode/quality/liveness; deadline is min(first_send+ttl≤3000ms,source_acquisition_lower+1500ms), conservatively translated by822 ClockBracket. Native requires an already admitted matching fresh observation, strictly increasing command_seq and code bounds; computes speed and curvatures from original FAST integer mapping (κnorm≤.5), and independently caps deadline at its own observation tick+1500ms and now+ttl. A duplicate/changed/expired command cannot extend a grant. Client validates the executable response target/command hash/seq/deadline and never retries an unknown write. Pause requires zero speed/yaw/pitch and remains a real host command.

Native then updates the SAME target/curvature/deadline consumed by _advance. Its accepted receipt identifies PC command; actual speed still ramps by Law and every physical frame is guarded. No motion at observe/hello/state. Final stop remains terminal and is not a board ACK.

## Task1 — Root native/UI (independent of host files)

- [ ] Add meaningful new red/green headless checks for mode exclusion, source-witness age/pose/epoch, command original deadline/seq/target, zero pause and unchanged default state schema.
- [ ] Create simulator/runtime/live_pc_direct_admission.gd; modify continuous_live_runner.gd/Main bind ONLY admission extensions. Keep _advance/Guard/Law/sole pose writer unchanged.
- [ ] Modify Root-owned continuous_demo_bootstrap.gd: pre-start BOARD_PWM/PC_DIRECT selection, frozen mode/epoch; display actual mode/source/PC-command receipt truthfully. Preserve866 terminal display and initial-only/drag/freeze semantics. Do not touch C's shell.gd.
- [ ] Run one new scoped headless control/parser check; preserve meaningful failures, no old suite reruns.

## Task2 — trace_perf_482 host ownership

- [ ] Copy exact822 bytes SHA1ae13d841e7c9ad11dd83d8eb94ec35152fd2e3b516d71fa5ccdc2562b20a0fb into integration/continuous_native_client.py; frozen original822 stays untouched.
- [ ] Create integration/live_pc_direct.py for explicit extension client/broker. No source geometry or new auth token access. Tests use actual835 public source/receipt/snapshot as fixtures only, never current physical facts.
- [ ] Derive O7/continuous-pc-direct-host-884/controller884.py from frozen847 (5886d834...). Original847 never edited. Preserve RunControl initial-only and publish_display functions unchanged. Before first real PC command reserve initial, consume after actual native acceptance including zero. Slider afterward stays next preference only. Current cap/AI advice generation unaffected.
- [ ] PC_DIRECT: single-inflight real board sense continues; no board.apply. Retain original native sample/witness alongside source future → pending source → sense metadata. Register successful actual E4 then submit actual797 AI; fresh AI drives genuine direct commands, renew only actual original advice/source while applicable. Mode-independent terminal immediately stops native, known pending board IO settles, unique real board STOP/close/wait. Keep BOARD_PWM branch as847.
- [ ] Record actual source/E4/AI/host-command/native receipt and origin times separately. Default board log event semantics remain unchanged; new direct events must not be called actual-pwm.
- [ ] New narrow malformed/stale/identity/unknown/initial-only controls only; no old source/model/PDE/RTL/board/UI runs. Deliver exact hashes/API before Root launches anything.

## Task3 — existing B/C ownership

B finishes actual835 sample review/manifest, then independently reviews this direct envelope/admission delta, no duplicate old847 tests, no board/credentials/control listener. C retains existing shell-only read-only display adapter PR25 task; no Root file overlaps. Authenticated envelopes are reference/review only; preserve actual claim/complete and no automatic group reply.

## Task4 — Root integration and one new actual mode case

- [ ] Independently inspect delta/exact files and scoped checks; publish byte-exact handoff and receive B review. No old full-route rerun as a compatibility test.
- [ ] Prepare unique new operation/world/socket/token (never replay834/835/800/808), carry saved next initial.185 unless human changes before first reservation. Root alone initializes the connected board, genuine fresh mouse setup and frozen PC_DIRECT mode.
- [ ] One actual source→real FPGA E4→AI→PC command→native continuous full route; no normal board APPLY. Preserve necessary real fault stops and no unknown replay. Separate real PC_DIRECT recording and terminal evidence; do not reuse835 as direct-mode success.
- [ ] Actual STOP/SSH wait/owned metadata restore, video container + visual review. Full29/G03/R03/formal dual-H12 and numerical metrics remain unaccepted until their own required evidence exists.

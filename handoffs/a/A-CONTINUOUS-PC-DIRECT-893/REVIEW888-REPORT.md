# Native885 ↔ Host884/887 peer review888

Read-only review of current Root-owned five files against fixed883 and delivered
host API. No W/884/887 edits, tests/controls/PDE/RTL/model/source/native/UI/board,
network actions or process inspection. Root's reported40 headless controls are
existing evidence, not rerun/independently promoted to actual-mode evidence here.
Requirements revision2 canonical2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d verified; all29/quality remain not_run.

## One operational finding, already sent to Root

continuous_live_runner.gd:205-220 rejects observe_pc and apply_pc_direct with
reason=not_ready_or_fault whenever _phase==ARRIVED (207,219). Native advances
before polling RPC (109-128). Consequently a valid last read can report a
nonterminal pose, then the next physics frame crosses the complete exit BEFORE
handling its observe/apply RPC. Both real source completion and host-command
submission can hit this race. Host884 NativeRejected then becomes controller887
failure before the next state read; arrival may remain false although the actual
native phase/history already reached ARRIVED. The new40 controls do not cover this
RPC arrival interleaving (test uses helper and an inactive dummy runner).

Smallest aligned fix: retain all no-further-motion/epoch/seq/TTL guards, return an
explicit known terminal reason such as already_arrived with actual _rpc_state,
and let the host consume this ONE known rejection/actual terminal state as
ARRIVED → existing immediate native STOP → settle original board IO → unique
board STOP/close. Or do one new state READ after this exact explicit terminal
rejection and verify actual ARRIVED before recording success. This is not retrying
the rejected command or an unknown write. Unknown/malformed/other failures retain
existing stop/error handling. Do not make not_ready_or_fault generally successful.
Root owns implementation choice;888 changed no files.

## Verified compatible seams

- Helper OBS_FIELDS:7 and COMMAND_FIELDS:8 exactly match host884 observe_pc and
  canonical command fields. Runner211-215 extracts only11 OBS fields from the
  4-field RPC header; apply220 expects exactly header4+command string/digest2.
- Runner171-187 reads actual drill pose/tick, public state then mints a fresh
  32hex witness only in successful PC RPC response. Hello/state/observe/apply/stop
  all use _rpc_state at183-187 and227-250. UI/Main local state has empty witness;
  it never enters the Python client. Host accepts RPC-only witnesses. No board
  target/pose change occurs at hello/state/observe.
- Helper61-93 ties witness to original tick/revision/position/xyzw, source segment
  native-<original revision>, source acquisition string, immutable epoch and fixed
  boot/build/request binding. It consumes the witness only after registration;
  failed pose/identity checks do not manufacture a valid source. Host independently
  validates genuine INIT/sense/E4 CRC/counts/quality/source digest and the exact
  Host-QPC acquisition lower bound; no source QPC number is used as a native tick.
- Helper54-59,88,107-110 retains observations by actual board_sense_seq until their
  ORIGINAL native witness1500ms expiry. It admits strictly increasing new sense
  sequences; an older still-fresh registered observation remains usable. New
  public latest fields130-133 stay distinct from current pc_command_sha/seq. Host
  apply does not compare latest observation against an older command source.
- Helper95-129 hashes exact command string, validates explicit PC_DIRECT/fast_9600,
  original registered source hashes/acquisition, increasing seq, TTL≤3000, original
  witness+1500ms and local now+TTL caps, integer codes and exact FAST combined ROM.
  float(code)/80.0 at123 matches Python Fraction/.0125 target conversion, including
  code3=.0375. Native curvatures match Python motion.validate to the host tolerance.
  Host binds original first_send+TTL and source_acquisition_lower+1500, converts
  via original822 ClockBracket. New heartbeat/observation never renews an old
  command/source. Duplicate command cannot mutate current command seq/hash.
- Runner217-225 changes only SAME _target_speed/_ky/_kp/_deadline/_running used by
  unchanged _advance131-151. PC path never writes _board_seq or _receipt; state
  retains board_request_seq0 and empty board_receipt. Original BOARD apply191-203
  is mode-excluded from PC and defaults to its existing≤12s image behavior.
- BOARD state171-181 contains the exact original822 base keys; direct merges
  exactly the10 host-whitelisted fields. Host subclass strips only those exact
  fields then delegates to unchanged822 base validation; unexpected truth fields
  still fail. No boardPWM/STATE8/Book credential is fabricated.
- Main1472-1490 preserves one explicit owner and defaults BOARD_PWM; it forwards
  frozen mode/epoch to install, labels actual mode, and keeps the sole actual
  writer1500-1504/owner checks1497-1498. No second bridge/tween is enabled.
- Bootstrap348-390 captures actual UI selector once, disables it before freeze,
  writes admission_mode into original frozen record, then installs exactly that
  mode/epoch. This matches new887 adoption of frozen choice rather than config's
  INITIAL preference. Slider407-413 emits initial or next-initial intent using
  actual host initial-consumed flag; Root RunControl still arbitrates reserved
  initial consumption. Pause/resume415-427 do not read/consume next preference.
- Bootstrap622-687 shows actual native phase/speed even readyfalse, distinguishes
  PC command receipt from PWM, retains866 terminal ARRIVED+host complete+real
  board STOP acknowledgement and does not suppress genuine other faults. C3 null
  and source profile/formal not_run remain visible/unchanged. Normal terminal
  operator_stop is not presented as a measured physical-zero capture.

## Minor nonblocking seams (current Root-generated IDs unaffected)

Bootstrap165 accepts epoch length≤160, while runner54 and host884 _label require
≤128 and host requires ASCII identity. Generic PC config validation should reject
unsupported PC epoch earlier (default BOARD compatibility need not narrow).
Current actual generated ASCII short epoch is in all bounds. Bootstrap405 still
says waiting Root board confirmation for a PC intent; later actual status662-663
correctly says Root confirmed request. Prefer generic Root confirmation wording
when convenient; this does not fabricate a board motion acknowledgement or block
admission. No new quality gate is requested.

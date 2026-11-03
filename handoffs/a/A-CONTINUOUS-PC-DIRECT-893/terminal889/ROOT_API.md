889 is a separate terminal-race and partial-observation candidate only.
Parent887 exact1774954908d14494c4db77e468ac6e91da7293e68f70ae7dbf47db069c378312.
Original884/887 and both W clients remain untouched. No deployment or runtime.

Root native must return ok=false,reason=already_arrived,state=actual _rpc_state()
ONLY when original observe_pc/apply_pc_direct encounters actual ARRIVED. Do not
open the motion gate. This candidate catches ONLY the actual packaged class:
competition.deepeye.integration.continuous_native_client.NativeRejected.

pc_rpc_or_arrived(native,result,log,operation,*args,**kwargs) wraps exactly two
calls: native.observe_pc and native.apply_advice. Ordinary success is passed
through. Every other rejection/unknown is re-raised unchanged. A known
already_arrived is accepted only after the PC client's existing strict public
state validator verifies mode/epoch/schema/witness and its actual phaseARRIVED
with faultempty. It immediately invokes original stop_native_once, THEN performs
one genuine native.state() read and validates ARRIVED with operator_stop. Only
then does it set result.arrival/arrival_native, log pc-known-terminal-not-admitted
and returnNone. Both caller sites set want_stop=True and continue the original
loop BEFORE consuming an initial reservation or marking command accepted. The
existing serialized pending boardIO→unique real STOP→CLOSED/wait path remains.
No command is resent, no unknown reply is interpreted as arrival, and no board
ACK/physical-zero fact is manufactured. A failed STOP/confirmation remains failure.

Sense's full observation construction/update now happens only AFTER successful
new direct registration. Expired-before-observe or terminalNone leaves the last
full observation unchanged, so later actual AI never gets the old partial dict.
BOARD sense still constructs exactly the same full record before downstream use.
RunControl/publish_display/advice_applicable/stop_native_once four ASTs unchanged.
Initial-only, frozen-selector887, continuous writer/geometry/source/AI/TTL and
unknown-no-retry semantics otherwise unchanged.

New controls command:
  PYTHON -I -S -B -X utf8 O7/continuous-pc-direct-terminal-889/controls889.py

Final exit0; r1 green stdout preserved. Uses actual835 historical public source
bytes solely as fixture and mocked terminal RPC seams (no native/socket/board/
model/numerical-source execution). Chronology for each wrapped method is exactly
operation once→validate→STOP→one state read→validate→log. Wrongreason, invalidstate,
preexistingfault, unknown write and wrong terminal confirmation all reject.
The exact frozen887 sense body on expired actual835 input reproduces old partial
observation red; exact889 sense body preserves the original full object green.
No broad old controls/suite was rerun. Python3.10 AST checked.

Root adopts this controller as a new unique run only after native reciprocal
reason/state change review. Scope revision2 requirements2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d.
Formal all29/G03/R03/quality/dual-H12 remain not_run, not inferred from pure seams.

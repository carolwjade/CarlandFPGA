847 is a minimal private controller derivative of frozen832/controller833.py
SHA6900970c8e49b5a1691ef8aab466eb6c5a481a3f93c05dec3ca3882a701cf79f.
Root copies controller847.py to O7/Root_live_controller847.py before running;
the child directory is not its runtime location. Root terminates/waits the old
waiting controller before swapping, preserves its evidence, and starts only
the new approved operation/stage. This package started nothing.

Scope revision2:2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d.
Existing generic config, exact board operation check, single board IO pool,
initial-reservation/actual-consumption/next-preference semantics, edge-triggered
pause, fresh-AI resume, raw E4/PWM receipt handling and nonfatal telemetry sharing
error handling remain. No timestamp, source/core/ROM/TTL/geometry rule changes.

F3: every positive real submission, including held renewal, is associated with
the original actual ADVISE in board_meta.actual_advice. A returned real APPLY
retains that object as held_advice. Fresh desired mapping retains control.advice;
renewal uses its own held_advice if still applicable, otherwise a valid latest
actual control.advice, otherwise commands real zero PWM. The final positive
submission guard requires ADVISE status, same epoch, original source acquisition
age0..5s, source-to-current ownpose distance<=.25m and forward angle<=15degrees.
These are the already selected833 checks, now applied to the missing renewal
branch too. No inference/completion time is substituted for acquisition.
Valid held renewal repeats the actual held target; it does not insert a stop
at sample/AI/update boundaries. Invalid renewal produces reason
held_original_advice_inapplicable_at_renewal, classified honestly as host safety
via actual board, and still requires actual zero capture before native pause.

F4: stop_native_once marks its attempt BEFORE the call, preserves the original
response or error, and never retries even an unknown response. Actual board ACK
is not fabricated. First ARRIVED/want_stop, operator stop and native stop request
call it immediately, before waiting for any board Future; explicit operator stop
also precedes host intent logging/display. The exception handler and finally
call it before source/AI close or board waits. Repeated calls are no-ops.

An already in-flight real APPLY still completes under the one original IO order
and is preserved as actual-pwm-terminal-not-admitted. It is NOT submitted to an
already terminal native, acknowledged as native acceptance, or replayed. Its
first actual initial reservation may still be consumed as a physical fact.
The physical board STOP is queued only when the original in-flight request has
returned; unknown effects retain the original transport poison/EOF cleanup
policy. No second executor or side channel is created. Normal ARRIVED keeps the
existing exact planned-operator_stop exemption, allowing original board STOP
and SSH closure to be recorded. Other safety faults still fail.

New result metadata: native_stop_attempted, native_stop_reason and, on failure,
native_stop_error{type,message}. Existing native_stop raw response is retained;
its board_stop_acknowledged=false remains required. Added accepted-PWM log field
advice_source_acquisition_qpc_ns exposes original time only. Existing815 ignores
the additional terminal-not-admitted event and still distinguishes incomplete
route/unknown effects from basic complete evidence. All final gates not_run.

Only two new AST-isolated pure controls ran: original-age/epoch/pose held guards
and actual held branch valid/expired behavior; one-shot successful/unknown native
STOP, late actual APPLY no native readmission, exception/finally ordering, and
normal planned-stop exemption. No controller main, source, AI, native, board,
network or UI executed. The first test harness selected the wrong AST if node;
that selector was corrected, not a product gate. Old suites were not rerun.

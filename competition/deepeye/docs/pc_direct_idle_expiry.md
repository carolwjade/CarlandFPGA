# PC_DIRECT owner-poll expiry observation

`PcDirectRuntime.check_expiry()` is an owner-thread, non-motion diagnostic. Its
frozen `ExpiryStatus(stop_required, reason)` is never a readiness result, source
credential, liveness lease or motion grant. A false stop requirement can include
a newly booted runtime that has not received a heartbeat or command.

The method uses the existing `_advance()` and the actual configured clock. It
does not call input verifiers, `ai_lease`, `prepare_step` or `commit_step`. It
does not create a BOOT, renew a command, reset a session, start a timer or install
a provider. Existing heartbeat expiry latches STOP with its original reason.
An original command is expired at equality with its original deadline. The
retained `_last_command` identifies expiry even if an earlier healthy board
event has already cleared the current command. Runtime command expiry remains
non-latching; a separate fresh verified BOOT retains its existing history reset.

The method rejects event/step/probe reentry and foreign-thread access. Invalid,
regressing or exceptional clocks veto further motion. An exceptional check
latches STOP and re-raises its exception; the existing runtime entry wrapper
retains its argument-TypeError conversion with the original error as its cause.
Catching a nested rejection cannot restore health to the outer check.

`ActorComposition.poll()` first performs its existing channel/progress checks
and polls its original actor. If still `ACTIVE`, it then calls `check_expiry()`
with a fresh clock read. A required stop uses the existing retirement transaction
to revoke runtime, executor, candidate and inference-progress admission and to
clean up the original actor. It returns the existing internal stopped sentinel,
so normal poll retirement does not become a second post-checkpoint rejection.
`RUNNING_UNBOUND` remains able to poll, and a never-commanded active runtime can
wait under the existing progress/lifetime policy. A retired composition cannot
be revived by a late heartbeat, command or completion.

The operation publishes no geometry and performs no motion CAS. A previous
successful numerical CAS remains successful: pose, pose revision and its commit
frame are retained. Stop/revoke bookkeeping legitimately advances general root
revision and revoke generation. Heartbeat, ACK, exact duplicate command and
inference progress cannot extend the original command deadline. The final
commit callback/CAS fence, PC_DIRECT v2 fixed window, production-channel refusal
before actor acquisition and BOOT wire/schema are unchanged.

New focused offline controls are in
`tests/simulation/test_pc_direct_idle_expiry.py`. Its explicit suite includes
only new methods; historical fixtures are setup helpers, not discovered suites.
Synthetic clocks, channel evidence and native API boundaries exercise the real
runtime, candidate/mailbox path and numerical executor. They do not establish
real process ownership, measured wall-clock latency, FPGA observations, useful
CPU-model decisions or a physical command. The production provider remains
unavailable.

A finite owner loop still has to call `poll()` using actual time. This change
does not supply an independent owner-death supervisor or an OS scheduling bound;
a blocked or unscheduled owner cannot promise timely stopping from this method.
Real-board headless integration and both complete H12 paths remain separate
evidence gates. All H01–H15 and G03/R03/all29 `not_run` boundaries are preserved.

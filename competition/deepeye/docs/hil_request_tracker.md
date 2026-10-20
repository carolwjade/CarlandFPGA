# HIL request tracker caller contract

`HilRequestTracker` is a bounded, serialized software diagnostic. It binds
retries and responses to the original request and never grants permission
to send a command or move the simulator or board.

The constructing thread owns every API call. A call from another thread is
rejected and queues STOP. The owner drains queued STOP on entry and at
verification fences. For a successful `response`, its last pending-STOP
observation inside the final fence is the diagnostic's linearization point.
A foreign STOP overlapping after that observation may be ordered after the
diagnostic and is drained on the next owner entry. A returned immutable
`Association` can immediately become stale.

STOP queued before an owner call is drained before that call can qualify a
response. STOP queued during a synchronous verifier is drained by its return
fence and vetoes the transition. A STOP after the final fence is handled on
the next owner entry. The independent review retained 25 of 26 passing tests,
one failure asserting a stronger before-return promise, and a separate
passing pre-entry control. That failure remains evidence of the former
overbroad documentation; no executable behavior was changed to relabel it.

`now_ns` is the explicitly supplied instant at which the diagnostic is
evaluated. It is not a trusted clock source. Real authority must obtain
current trusted time after verifier work and at each physics/send action,
serialize STOP with those actions, and check its own authoritative gate.
It must not treat a previously returned `qualified=True` as an active lease.

BOOT, sensor source, timing bounds and independent capture require actual
upstream verifiers. The provided record types, hashes and opaque objects
are containers, not credentials. Missing evidence remains unknown. The
helper does not provide a board watchdog, transport, AI, runtime activation,
or PC_DIRECT-to-board-capture substitution.

Histories are capped at 16 requests, four observations and 64 sessions.
The original first-send TTL and original observation-age cap never renew
on retries or responses. Real restart uniqueness, measured timing, both
complete H12 control chains and the remaining R03 gates require integration.

This adoption is bounded software evidence. R03, G05, full H12 and all 29
formal taskbook cards remain `not_run`. H01-H15 are unchanged under
`DEEPEYE-HUMAN-LOCK-20261014/revision1`.

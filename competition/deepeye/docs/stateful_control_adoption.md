# Reviewed stateful control helpers

Two bounded host-side helpers now retain the state needed by the R03 lifecycle
requirements. Their outputs remain diagnostics or selections, never authority.
Production BOOT/source/clock/capture providers and final actor integration are
still required; neither helper opens the production gate.

`integration/candidate_mailbox.py` retains the newest completed candidate and
four source observations, rejects old/conflicting completions, preserves the
original completion and observation deadlines, and consumes at most once in a
valid slot. STOP/new activation retires old usable state. Independent review
found that malformed STOP arguments bypassed the stop latch. Adding the same
entry wrapper already used by other mutation methods repairs this boundary.
The author retained original 26 tests and added four; final 30 passed.
The original independent three focused STOP tests then passed at the exact
replacement hash, including both H12 modes. These are separate executions.

`integration/hil_request_tracker.py` retains original request type/sequence,
payload, first-send time, TTL and source observation. Retry, ACK and STATE
cannot extend the original deadline. Qualification requires explicit upstream
BOOT/source/time/capture verification; unknown evidence remains unusable.
Author final37 tests passed. Independent review recorded25 of26 passing and a
separate passing pre-entry STOP control. The retained failure asserted a
stronger before-return promise than the serialized diagnostic implements.
Main clarified the final pending-STOP observation as its linearization point.
Executable AST did not change. See [caller contract](hil_request_tracker.md).

All original RED runs, the author's fixture correction, the independent failures,
process closure receipts and exact-source hashes are retained in
[the evidence archive](../evidence/system/a-stateful-control-20261020/manifest.json).
The mailbox repair author64 artifacts and HIL independent41 artifacts were
rehashed by main, with completed/terminal/exact original job readback.
No full R03 suite was rerun for this publication.

This closes the bounded helper implementation/review work, including mailbox
STOP correction. It does not close R03 or any of the29 formal cards. Real
completion IPC, authority serialization, both H12 runtime chains, B/C full
interoperability, registers/HWH and measured IO/clock evidence remain separate.
No board, service, driver, OS, UI or foreground input was used.
H01-H15 remain fixed under DEEPEYE-HUMAN-LOCK-20261014/revision1,
requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.

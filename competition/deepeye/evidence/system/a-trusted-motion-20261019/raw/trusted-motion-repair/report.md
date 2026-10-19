# TM-R1 main-owned narrow repair

Original A Desktop generation2 selected and implemented this repair after author
and independent review jobs completed. Only motion_executor.py, its existing test
file and documentation changed. Original author/review evidence is preserved.
H01-H15 and requirements c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 unchanged.

passage_state is a legitimate standalone authority read and is also used inside
prepare and final callbacks. Its late materialization exception previously bypassed
the transaction entry guard, allowing the same BOOT/command to move afterward.
It now revokes pending/future motion before rethrowing any materialization failure
or cancellation. The already committed frame, pose and event history remain intact.
The unknown error does not newly set trial_failed; no collision is inferred.
No nested _entry decorator was added, so prepare's normal internal access remains
valid. A caught materialization error in a final callback changes root identity and
vetoes the attempted publication. A later successful history read does not reactivate
the store or restore the retired command.

Two new regression methods cover standalone failure with an existing pending
handle (MemoryError, ValueError, KeyboardInterrupt) and a caught final-callback
failure. Before repair all four subcase/assertion results failed; raw RED is saved.
After repair the full suite passed137 methods (24executor+113existing), exit0.
The original eight independent methods were copied byte-for-byte and rerun once;
all8 pass, exit0. This main rerun does not replace the next independent rereview.
All32 other relevant input files (including the unchanged passage helper) match
the previous35-file manifest. All4 candidate raw streams equal Git clean-filter
blobs. Full source manifest SHA256:
1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533.

Synchronous Python bookkeeping still requires the owner process and enough memory
to record revocation; the injected allocation fault is local to materialization,
not a proof against total process memory exhaustion. No provider, Run path, service,
real OS fixture, board or formal card was activated. All29 cards remain not_run.

# Main-owned three-case native verification

Prepared by original A Desktop generation 2 under DEEPEYE-IMPLEMENTATION-20261014/v1.
H01-H15 and requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 unchanged.

Execution is gated on main review of the repaired exact candidate and independent
evidence. IL-R1 currently blocks execution. No native fixture has been run from
this directory. The gate file will bind the full source manifest after review.

Run the three prepared WindowsLiveTests once in explicit order: normal boundary,
100ms timeout with a staged sleeping fixture, then persistent receipt failure
after successful suspended process creation. Each call creates its own fresh
random run/profile under a fresh attempt folder. Preserve all failed attempts,
pending files, stale receipts, staged runtime manifests and returned-memory data.
No old fixture/profile, service, credential, queue, board or historical output is
selected or cleaned. Existing product sandbox policy remains unchanged.

The wrapper delegates every Windows operation to the real candidate backend.
It returns the same native results and restores GetLastError. At process-handle
close it independently waits on that same still-held process handle and reads
its exit code; it never reopens a PID. After return it independently stats only
the reported fresh profile directory and records absence or the precise error.
These observations are separate from the candidate's verdict. For the injected
save failure, the returned memory snapshot is the final result, not receipt.json.

Keep each RunEvidence object alive. If any ownership remains unresolved, stop
the campaign and hold the runner process with those live references; do not kill
it, retry closes, reopen a PID or silently let process teardown count as cleanup.
The runner's hold accepts only status, which performs no native effects. Main
must record a separate bounded reconciliation decision before any recovery.

The campaign establishes only these three CPU fixture outcomes. G03, four process
isolation, GPU/UI, runtime/game, R03, both control paths and board remain not_run.

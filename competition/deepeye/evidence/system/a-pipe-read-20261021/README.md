# Reviewed native pipe-read diagnostic

Main verified the author's 50 and independent reviewer's 28 manifest entries,
37 current source inputs and both original completed task results. The exact
three new source/test/document files are pinned in main-verification.json.
Every raw archive member was reopened, CRC-checked and compared with its original
bytes. Original failed runs are retained. No tests were repeated for publication.

The leaf distinguishes empty, bounded data and Win32 broken-pipe EOF. It validates
arguments before native initialization and makes one peek and at most one read.
It does not own endpoints, authenticate input, call authority or activate a
consumer. Existing cleanup helpers and the closed production factory are unchanged.

Author final GREEN passed 12 methods. Original RED failed for the absent module;
the first GREEN's assertions passed but evidence serialization failed, so that
run remains failed. Actual final native cases created three pipes and closed six
endpoints once each. Mocked error/race controls remain distinguished from native
observations. Nine held process records across those original runs are signaled.

Independent review found no blocker and added two actual native controls: the
default 8192-byte limit drained 9000 bytes as 8192+808; interleaved original pipes
remained independent after A closed and B accepted further data. Four endpoint
closes and three held process terminations were verified. The worker compiled
the exact source bytes and recorded zero project cache reads. Its 10 polls each
made one peek and at most one read. This is local pipe evidence, not genuine model
completion IPC. The named author ceiling test explicitly passed 8192; the new
independent case additionally checked the omitted default argument.

Sole-reader discipline is a caller obligation. A competing reader can consume
data between peek and read. Native calls retain OS scheduling behavior; no hard
elapsed-time or cancellation guarantee follows from the call/byte bounds.
Freely constructible diagnostics grant no ownership, freshness or motion authority.

Real completion IPC, dispatch/model/BOOT/source/clock/slot providers and complete
PC_DIRECT/FPGA/UI chains remain open. R03, full H12 and all29 formal cards stay
not_run. No physical-board, service, driver, OS or foreground action occurred in
these runs. H01-H15 remain DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.

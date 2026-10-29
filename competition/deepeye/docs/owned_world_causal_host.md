# Already-claimed causal host with the original world

The private `run_private_pl_live._run_claimed(template, out, sources, released,
clock, *, _causal_source=None, _causal_feedback=None, _world_service=None)` runs
the existing claimed diagnostic body and its original SSH/Job/pipe cleanup. It
requires the exact `QpcHostClock` and `_require_binding` check. It never calls a
clock factory, prepares another host, waits for activation or claims again.
`released` is the result of Root's original `_claim`, not a replacement request
or a capability granted by a caller's DTO.

The public CLI still creates one fresh clock, publishes its original prepare,
waits, rechecks all prepared source pins and consumes one activation before
delegating. Preclaim failures retain the original source retirement and
`HOST_TERMINAL.json` without starting SSH. After delegation only the claimed
body writes that terminal and finishes the original transport. The strict SSH
route/provider, exact agent/codec/collector/driver pins, request/activation hashes,
scan limits and original cleanup remain in place.
The claimed body also re-reads the actual driver/codec/clock/agent/collector and
the four causal source files after static source preparation. It compares their
actual bytes/size to the original prepared pins before reading the SSH provider.
Its validated context must match the original clock's domain before SSH starts.

Root's future integrated entry can prepare/wait/claim first, then acquire and
initialize one original native world with that same clock, build its registered
binding/field/source, and call `_run_claimed` with its original values. Root must
retain its preparation/source verification and final source/native cleanup;
this entry does not acquire, adopt or close a world. This avoids spending a
45-second native lifetime in the existing prepare wait of up to 120 seconds.

The optional service is accepted only in causal mode as exact
`RootWorldService`, with `service.clock is clock` and `service.source is source`.
The causal module imports its type lazily because the service imports the
source class. Neither a public flag nor a software service creates an owner.
World polling is explicit before SSH construction, credential send, new source
work, requests, transport sends and the existing single candidate consumer, and
after that bounded consumer. A consumer failure remains primary if the following
world observation also fails; the observation failure is retained as secondary.
The consumer must still return `None`; it creates no CPU completion or action.
Polling precedes the fresh 10-second consumer-dispatch check. After a source
callback, its raw record is retained before the world check and ledger admission.
After the final send-side poll, both the original pending response deadline and
the pending record's original ADC/EM 100ms ages are checked again. The diagnostic
2-second response profile never substitutes for that source-age check.

In world mode, READY and terminal drain use the original transport's
`poll_line()` and the same QPC. Their absolute deadlines are the smaller of the
original 180-second READY or 5-second terminal span and the service's original
native containment deadline. Equality is expired, including a line observed at
the deadline. Terminal drain uses `poll_retired_source()` after the original
source is retired and cannot resume source work. With no service, the original
`line(180)`/`line(5)` branches remain in use.

The source's 10-second session, 100ms SourceLedger admission, callback policy and
finite evidence/scan/request budgets are unchanged. `functional_chain_v1` remains
only its existing exact diagnostic response profile; it does not change source
age, fabricate BOOT/ADC/FORCE8, authenticate a channel or permit movement.

`test_claimed_causal_host_world.py` contains only new software controls. Its
positive wait/core fixtures explicitly identify themselves as software-only and
use the distinct private service type. The public claimed entry rejects that
clock and service. No public production/native-positive run, real QPC factory,
main/SSH/engine/board/PDE/model/network/UI or old suite is executed by these
controls. Full causal chain, Run, both H12 modes, G03/R03/all29 and final 1%/100ms
acceptance remain unproven. H01-H15 and requirements
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
remain mandatory.

# Fresh-run raw QPC clock binding

Work A-HOST-CLOCK-QPC-V1-IMPLEMENT-20261024-v1, task
DEEPEYE-IMPLEMENTATION-20261014/v1. Contract DEEPEYE-HUMAN-LOCK-20261014/revision1,
H01-H15 unchanged; requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

Trusted main may call `qpc_clock_for_new_run()` once for a completely fresh
run/actor/ledger/BOOT/world/history. It returns an exact `QpcHostClock` object.
Pass that same object as `ReceiptLedger(..., host_clock=binding)` and
`create_authority(config, host_clock=binding)`. The BOOT transcript inherits the
original ledger's clock and domain; it accepts no second clock argument. The
composition passes the identical object to ActorRegistry and runtime, and uses
that callable itself as progress/candidate `clock_domain`. Original HANDLE Wait
sampling therefore inherits the same epoch, including both surrounding stamps.

The factory accepts no callable, supplied now, mode or authentication flag. Its
fixed leaf is `time.perf_counter_ns`; it checks this runtime advertises
QueryPerformanceCounter, monotonic and nonadjustable, and refuses unsupported
capability without fallback. A binding rejects foreign threads, bad/bool/
out-of-range integers, clock regression and subsequent calls after failure.
Metadata is read-only; domain_id is a diagnostic correlation label. Exact type
and object identity are trusted-process conventions, not security or provenance.
Private leaf replacement in new tests is a test seam unavailable through the
production constructor.

`binding()` returns raw bounded nanoseconds. `binding.read_sample()` retains the
same raw value and original domain with `interval_ns=None`. Advertised resolution
is metadata only: 100 ns resolution is not timestamp uncertainty, transport cost,
scheduler latency, source bounds or a measured current interval. This increment
does not adapt scalar runtime/lifetime/progress deadlines to physical uncertainty.
Production still unconditionally rejects before registry construction/acquisition.
QPC selection cannot open that gate or create an authenticated timing provider.

Ledger and BOOT snapshot/journal sidecars describe the selected clock. In QPC
mode, raw OS-call brackets are diagnostic fields `raw_read_call_bracket_ns` and
`raw_write_call_bracket_ns`. Measured `read_call_interval_ns` and
`write_call_interval_ns` stay None. Descriptor availability/sample intervals stay
unknown; an empty read does not convert unknown timestamp uncertainty into a
measured availability interval or a claimable board envelope. ACK echo comparison
may compare original same-domain raw call ordering diagnostically; it provides no
arrival, sample, UART completion, build or endpoint authentication.

After an actual read returns, the ledger records its complete original bytes,
stream offset and byte/read budgets before attempting the trailing stamp. If
that stamp fails or regresses, the raw end remains None, availability remains
unknown and capture permanently fails. Bytes are retained; no later read/claim is
allowed. No decoder result or invented end=begin substitutes for the lost stamp.

BOOT reserves its one attempt before the first stamp. A marker or pre-write stamp
failure cannot reenter a new write. The original started_unknown marker is still
flushed and fsynced before the sole actual os.write. After a returned write, a
failed stamp retains the actual count, unknown end and durable started_unknown
record, then permanently closes admission. Short/error/journal failures never
retry. Post-stamp failure does not imply no I/O occurred.

`None` keeps the previous legacy monotonic defaults and diagnostic semantics.
There is no global alias, monkeypatch, runtime switch, epoch offset or adoption of
old records. Equal strings or nearby raw numbers from another binding cannot
replace the original domain. Root must reconstruct a fresh world/history and
verify any future original child-process clock/IPC/compute-time association;
metadata and READY claims do not establish cross-process correspondence.

The published PC_DIRECT v2 width stays 10 ms. Its fixed O/F/P/grant k, ready bound,
half-open consume window and original deadlines are unchanged. ProgressGate,
stateful once-consumption, original runtime/executor/lifetime logic, callback
refresh order and final fence-to-CAS remain unchanged. No clock or diagnostic I/O
is added between the final callback and CAS. Useful AI, actual PL/model timing,
either full H12 chain, G03/R03/all29 and formal acceptance are not established.

New focused controls use actual OS pipes and private fixed-leaf/native/upstream
fixtures, retaining the real mailbox/runtime/geometry/executor. A separate single
actual-QPC pure-policy observation fixes one new operation/run/origin and attempts
one ordinary bounded wait/consume. Success or miss is retained without retries or
policy changes. A successful observation establishes only that local attempt,
never a measured uncertainty or scheduling bound. Old component suites, PDE and
384 board tests are not rerun.

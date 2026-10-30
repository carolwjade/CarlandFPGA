# Original source time book

`RootSourceBook(owner, binding, field, source)` borrows Root's original retained
production world/native/QPC, registered initialized binding and exact field/pump.
Construct it while the source is NEW, after any original EM scope is fully bound.
The original field pose/sampler bound methods and profile remain unmodified.
The read-only `clock`/`source` properties return the original objects without I/O.
No clock, process, handle, BOOT, command, action or provider is created/adopted.

The constructor records a real-QPC-bracketed pose baseline with explicit original
owner polling. This first version requires that same committed Root/pose/revision,
epoch, scene and veto generation throughout. Unrecorded motion fails the book.
Its evidence describes committed-value endpoint observations, not atomic native
getters or a physical pose interval. Multi-action/actual commit-publication
association is unimplemented and marked unavailable; no empty executed-action
history or C30-ready receipt is fabricated.

After the original source starts, call `start()` once. Inside its already consumed
poll slot, `open_sample(tick_ms, observed_qpc_ns)` checks original `_last_tick`,
`_count`, `_polling` and `_high`. Observation must lie in the real10ms bin.
Nominal time remains `origin + tick*1_000_000`; real reads may be much later.
The original origin is never reset, and the full bounded prefix has at most1001
records, without eviction or replay.

For an EM tick call `read_pose(token, 'em')` inside the original EM scope and use
the returned `forward.Pose` for the unchanged producer. After the EM scope closes,
call `read_pose(token, 'adc')`, then `begin_adc(token)`. Root calls the ORIGINAL
retained profile's `sample_adc`, then calls `end_adc(token, handle)`. The opaque
handle brackets that caller operation with actual QPC reads; end also observes
the retained profile's `_last_adc_tick` progression. The book never invokes or
intercepts the producer itself. Both pose reads preserve actual begin/end times
separately from nominal time, with explicit owner polls outside clock/busy entries.

`finish_sample(token, payload)` requires those reads and brackets, validates the
existing nine-field SourceRecord whitelist and tick, and saves detached exact
canonical source bytes/hash, private payload/counts/quality and baseline span.
Late brackets are retained honestly: recording a payload does not admit it through
SourceLedger or establish board provenance. Its source floats stay Root-private;
Root must separately select C30's outward whitelist and real admission/capture.

All operation faults are sticky: book/source FAILED, original exception preserved,
active partial evidence retained, no retry/RNG rollback. `fail(reason)` is pure,
non-throwing and does no clock/native/world I/O. Foreign calls only contaminate;
the next original-thread operation/fail retires the association. `retire(reason)`
only closes book state, preserves history and does not heal failure or call
source/world/resource cleanup. `evidence()` returns detached observations with
no I/O; Root retains its existing cleanup finally.

The private software factory returns a different exact core and refuses real
Root/native owners. New controls simulate profile tick progression explicitly;
they execute no producer/kernel, native engine or board. Exact types/registries
are trusted-process conventions, not an OS security boundary.

H01-H15/c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804
and ForwardProfile6a5 remain unchanged. Original317ms/source100ms failures remain;
this book promises no speedup, source admission, executed action, physical board
result, H12 or complete-chain acceptance. Pump wiring is a separate Root change.
Root's fixed `require_source_pose_current()` gate is mandatory before production
source work. Pending/uncertain numerical effects or an APPLIED publication
without reviewed getter admission cannot produce a next source record. A stopped
initial world with no numerical action remains available for diagnostics.

Retirement while a book operation is busy fails permanently; a later return from
that operation cannot restore RUNNING. Endpoint observations still do not prove
an interval-atomic native getter or an executed action.

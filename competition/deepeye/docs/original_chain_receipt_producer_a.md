# Original chain receipt producer

`OriginalChainReceiptProducer(world, chain, scanner=None)` accepts the exact
fresh prepared `FunctionalWorld`/`FunctionalSource`, `ChainSessionV2`, and
fixed B131 bundle on their one original QPC and owner thread. The session must
have completed the original v2 SSH factory's ready
path. Its factory retains the original immutable spec, process, stream objects,
ready bytes and QPC brackets; no sudo input is retained by this registration.
Construction itself sends nothing and does not acquire a world or board.

Call `init` before source start, then start the actual source and attach the
fresh v2 scanner once with `bind_scanner(scanner)`. Bind the exact original
`OriginalChainSourcePump` once with `bind_pump(pump)`, and explicitly invoke
`enable_pump()`; neither construction nor binding starts the source. `pump_once()`
services the original source on the owner thread when Root is not awaiting a
board reply. During a v2 reply wait the original session uses <=1 ms wait
fragments to invoke that same fixed enabled pump; the I/O worker touches only
the original pipes. This is a scheduling attempt, not a 1 ms or 100 ms timing
guarantee. Unbound or disabled sessions retain their previous wait behavior.
If the pump fails, the session is unknown, the pending I/O thread and process
remain retained, and no retry or automatic STOP occurs.

Call `init`, `apply`, `status`, and `close` only with explicit arguments. Each
calls its fixed original chain client method once. `admit_source(payload)`
calls the original scanner's `admit` with the exact FunctionalSource payload.
`scan_actual(id, payload, facts=..., build_binding=..., max_io=..., timeout_ns=...)`
calls the same scanner's `prepare` and the same chain's `trace_scan`; there is
no caller-provided prepared result. The scanner enforces the complete original
history and latest next source sample. Source data and private world pose are
not sent to an AI by this producer.

Each successful call returns an opaque in-process event. Source admissions made
by the fixed pump while waiting are queued before the board response event;
obtain them in order using `take_pending_events()`. On a pump failure, completed
admissions and an `INCOMPLETE` pending-source reference are retained when
available; they are not represented as completed data. Consume events once,
in original sequence, as `facts, refs = consume_original_receipt(event)`.
`facts` is a detached copy: kind, sequence, operation, original raw response,
parsed response and actual host QPC bounds, or original source admission data.
Trace facts also contain the actual correlation and snapshots of the supplied
Root facts and build binding. `refs` carries exact original world, source,
Book, scanner, bundle, chain, session, factory origin, process, streams, QPC,
and, where applicable, original sample payload/token/draft/ADC and EM handles,
Preparation, source/request bytes, four companion objects and client result.
These references are for trusted Root-side independent validation and may
contain private state. They are not a public serialization or an AI prompt.

The producer checks identity and operation continuity, tracks its original
client request count, retains complete event history, and refuses session,
source, Book, clock, process, bundle, scanner, or sequence replacement. An
unknown result or exception permanently disables further operations; no retry,
automatic init, apply, STOP or replacement occurs. An unknown event that was
returned can still be consumed in sequence. A caller cannot make an event by
passing JSON, a hash, a `verified` flag, a callback, or a lookalike object.
This is an in-process custody convention, not a defense against arbitrary code
execution in the same Python interpreter. Events are observations only: C48/C49
must independently validate sources and enforce authority. No BOOT/STATE8 or
physical board acceptance is inferred.

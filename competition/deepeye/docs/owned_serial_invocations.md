# Explicit owned serial invocation candidate105

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
H01-H15/original29/both H12/final100MHz/timing/1%/100ms remain unchanged.
This adds finite raw transport sequencing. It creates no verified inference,
BOOT, source authentication, action or motion grant. Production channels remain
unavailable. Actual original-process/model/native/board/full-chain runs and
independent exact-source review are pending.

An original `ActorRegistry.launch_overlapped(policy)` owner can explicitly call
`begin_serial_invocations(SerialInvocationLimits(...))` before its first
request. Limits include count2..32, aggregate request bytes<=32*16384,
aggregate output<=16MiB and aggregate reads<=65536. Each invocation reserves
its entire output/read allowance before its request. The same original actor,
owned endpoints, package/operation labels, fixed readiness deadline and overall
lifetime remain in force. Existing `prepare_invocation` stays once-only when
this mode was not selected.

The first request uses `prepare_invocation`, then `dispatch_invocation_once`
and the existing bounded read/poll APIs. For a fully received single framed
response, `seal_serial_invocation_frame()` verifies the retained original OS
operations and raw transcript, samples an actual observation time, appends and
closes that original journal. It returns raw-frame/payload observations with
`authenticated=false` and `completion_verified=false`. The real provider must
still verify the exact package, request/response invocation association,
candidate/model semantics and original host-time bounds before creating any
`_CompletedInference`. A complete raw frame alone is insufficient.

Only a successfully sealed predecessor permits `prepare_next_invocation`.
Each request gets a new retained ticket, exact incrementing invocation label,
new exclusive journal and sole write reservation. Legacy actor/pipe claims
remain permanently true after first use; they are never reset. Pending,
cancelled, failed, EOF, zero-read, unknown, partial, extra or multiple-frame
observations cannot open the next ticket. Errors retire the original owner
through existing cleanup. A caller should continue the same pending read and
its original budget until a complete frame is present, then seal once.

Operations retain the exact original record that owned their IO. Later
settlement/cleanup cannot charge an old read into the current record. All
tickets, original operations and prior records stay strongly retained;
closed journals and cumulative observed stream offsets remain attributable.
Serial metadata is included in the owner's private ACL-contained receipt.
No process/endpoint is adopted, reopened by PID or replaced.

Requests use `DEEPEYE-PRIVATE-FRAMES/1`: a4-byte little-endian length followed
by a nonempty payload. The invocation's16384-byte request limit includes this
prefix, so its payload is at most16380 bytes. The generic output frame codec
allows payload<=16384; output/read allocations must also cover its prefix.
A raw-frame observation does not promise that the child will never emit future
unsolicited bytes. The pinned serial package must emit exactly one response
per input and bind every response to its invocation. The original provider
must reject a wrong/stale/unsolicited response and retire, with no motion grant.

The original launcher appends three inherited handles after policy arguments:
`model_ready_event`, `input_read`, `output_write`. A C37 package signals only
that inherited event after initialization and reserves its output pipe for
framed responses. Source/AI/BOOT startup must use the original event and actual
actor ownership; READY text or child-claimed IDs do not authenticate readiness.
Preparing the actor/source before starting a fresh source origin and accepting
BOOT only when genuine initial causal inputs are available avoids spending
the first inference lease on the source's initial invalid C3 window. Exact
startup and genuine provider integration remain separate pending work.

Validation: a new missing-feature control failed first. Ten NEW focused
software controls then passed under the original60s/512MiB process/1GiBJob
supervisor. One additional NEW coupling control used the actual public owner
API and real exclusive journals under explicit fake native/liveness boundaries
to execute two distinct framed calls, retain both records and keep the original
once claims. It passed once; the earlier ten were not replayed. These tests
prove software sequencing only and establish no original native/model proof.

# Typed anonymous-pipe observation leaf

`simulation.isolation.pipe_read.poll_output(handle, max_bytes=8192)` observes
one caller-owned original anonymous pipe read endpoint. It returns a frozen
`PipeReadResult` with exactly `state` and `data`:

| State | Meaning | Bytes |
|---|---|---|
| data | Successful peek found bytes; one read returned a nonempty bounded piece | Exact bytes, length1..min(available,max_bytes) |
| empty | Successful peek observed zero available bytes | b'' |
| eof | Peek or following read failed with Win32 ERROR_BROKEN_PIPE109 | b'' |

`handle` must be an exact positive int, excluding bool/subclasses, fitting this
process's unsigned pointer width; rejecting larger values prevents ctypes handle
truncation. `max_bytes` must be an exact int1..8192. Invalid arguments raise
ValueError before native module initialization or any native API call.

Each invocation makes one PeekNamedPipe call and at most one ReadFile through
the existing `win32.read` helper. Open-empty never calls ReadFile. Positive
availability requests min(available,max_bytes), without waiting for a larger
message. A short nonempty read is data. Unexpected zero bytes, oversized output
or a non-bytes result raises ValueError; none is silently treated as empty or
healthy. Only OSError.winerror109 maps to eof; invalid handle6, access denied5,
other native errors and a generic errno109 propagate as errors.

The caller must preserve the original endpoint ownership and be its only reader.
No lookup/reopen/adoption by PID or pipe name is offered. A competing reader can
consume data between peek and read; this API supplies no concurrency guarantee
for that case. The native calls still have OS scheduling behavior: one peek and
one bounded read are call/byte bounds, not a hard elapsed-time, cancellation or
owner-hang guarantee. No retry or write operation occurs here.

After the last writer closes, buffered bytes may still be returned as data;
eof follows drainage. Empty means an observed open-empty peek, not responsive
inference, approved initialization or future life. Data is untrusted output,
not an authenticated completion/BOOT/source/clock/slot record. Anyone can
construct a diagnostic result; it grants no ownership or motion authority.

This leaf has no production call site. Existing `win32.available_output`,
ActorOwner, READY/EXIT, authority, host/wire ABI and factories remain unchanged.
No framing protocol, timestamping, authentication, process/pipe acquisition,
teardown, provider activation or lifecycle transition is added. A future EOF
consumer must retire its own provider/owner epoch before accepting more work;
this leaf deliberately cannot perform that retirement or drain a foreign owner.

Focused tests use narrow native-call controls and actual local anonymous pipes
inside a hidden bounded owned test process. Real handle creation, bounded writes,
data/empty/eof ordering, invalid closed read error6 and every handle close are
recorded separately from mocked error cases. No model/actor or existing endpoint
is accessed. These tests establish a native read leaf only. All real completion
IPC/dispatch, original BOOT/source/clock/slot, full PC_DIRECT/HIL/UI integration,
R03/full H12/all29 remain not_run. H01–H15 and director generation2 are unchanged.

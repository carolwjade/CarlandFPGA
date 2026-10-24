# Typed pipe-read implementation evidence

Work `A-R03-PIPE-READ-IMPLEMENTATION-20261021-v1`, original job
`child-d0981a47801240d8b289804acb5209ca`, worker
`/root/r02_static_dependency_review_20261020`.

Implemented exactly the three assigned new product files:
`simulation/isolation/pipe_read.py`, `tests/simulation/test_pipe_read.py`,
`docs/pipe_read_boundary.md`, relative to product `competition/deepeye/`.
The component is inactive and awaits main's independent review.

`poll_output(handle, max_bytes=8192)` returns frozen diagnostic `state/data`:
data for a nonempty bounded read, empty for a successful zero-availability peek,
eof only for Win32 broken-pipe109 at peek/read. It validates strict arguments
before lazy native initialization, makes one peek and at most one read, never
retries/writes/closes/waits for more data and propagates all other native errors.
Unexpected zero/oversized/non-exact-bytes read results fail explicitly.

Positive handles also must fit the native unsigned pointer width, to avoid
ctypes silently truncating an oversized Python int. This is representability
validation, not endpoint ownership verification. No identity or capability is
constructed. The result has only two fields and grants no authority.

The implementation reuses existing Win32 bindings without changing helpers,
ActorOwner, READY/EXIT, ABI, factories or final authority. Thirty-three pinned
existing product source/doc inputs, including adopted owner/factory/runtime/
executor, native/resource helpers, source/clock/mailbox/HIL and UI, rehash
identically. Static scanning of relevant production areas found no pipe_read
consumer. No new production call site or provider activation exists.

## Actual RED/GREEN and preserved evidence failure

| Run | Test result | Process/receipt |
|---|---|---|
| red-01 | 12 assertion failures,0 errors, all specifically missing component; no native pipes created | exit1, active0, all3 held handles signaled |
| green-01 | stdout/stderr shows12/12 OK | Worker failed to serialize ctypes c_void_p handle in evidence JSON; exit1, no structured test-result, active0, all3 held handles signaled |
| green-02 | 12/12, failures/errors/skips/prohibited attempts0 | exit0, full structured evidence, active0, all3 held handles signaled |

The first GREEN's failure is a fixture evidence-serialization failure, retained
in its original logs/snapshots; it is not promoted to a complete successful run.
The exact native handle value is now normalized from the creation callback's
ctypes handle to an int in the test fixture, with an exact-type assertion.
`fixture-correction.diff` preserves the three-line helper change. All12 test
method ASTs are identical between RED and final GREEN; only `open_pipe` changed.
The pipe_read implementation itself is byte-identical across both GREEN runs.
The wrapper was extended to a fresh green-02 ID and verified prior original
held-object termination before creating another process. No unknown effect
was replayed and no failure directory was removed.

Narrow native-call controls cover bool/subclass/type/range refusal before native
access; empty without read; bounded caller/default8192/available-count reads;
one peek/one read; peek109 and read-race109; errors5/6/232 and generic errno109
remaining errors; zero/oversized/type-invalid data; and frozen diagnostic fields.
Mocked109 read race and other mocked errors are separate from actual pipe evidence.

## Actual local anonymous-pipe evidence

Final structured `native_pipe_evidence` has three actual local pipes and six
created endpoints, all closed once successfully on their original handle values.
OS handle values may be reused between completed test cases; each case keeps its
own creation/close sequence, with no PID/name lookup or adoption.

1. Open-empty peek returns empty with read_calls0. A10-byte write, well below
   requested16384-byte pipe capacity, yields exact3/3/3/1 bytes under max_bytes3.
   The next poll is empty. Close the sole writer explicitly; the next poll is
   eof, with no read. Every observed poll has one peek and at most one ReadFile.
2. Write2 bytes and close the last writer before reading: buffered `xy` is data,
   then eof. This establishes drainage ordering rather than labeling writer
   close as immediate data loss.
3. Close original read endpoint then immediately poll that same numeric handle,
   with no intervening kernel-handle creation/reopen: actual Win32 error6.
   It is not mislabeled empty/eof; the still-owned write endpoint is cleaned up.

The final test body took0.037s; owned process tree about0.469s. Each run used the
exact existing interpreter with `-I -S -B -X utf8`, hidden/below-normal original
JobObject assignment. Limits:30s,512MiB job,256MiB process,four processes,
256KiB stdout,512KiB stderr,16MiB/300-entry tree,512MiB free reserve.
Reviewed runner `80cc41fd629bc3618b50c88fbd97332ec14cdd8cbaf8f927f0235390664cb77d`
and boundary `04cf7d53f3dbf1fca66aab05fe497ae193aab94a56ab4e0d36e81d1eb0a040fe`
were copied unchanged. Three process runs retain nine original held-object
records, all wait_result0/signaledtrue. This does not infer image identity from
PID alone. No unrelated process was terminated.

`source-pins.json` binds final three product bytes to final test snapshots and
original33 inputs. `verification.json` and raw receipts retain source/import
hashes, controls, native cleanup and process termination. Recorded cached code
objects were checked against compilation of their exact source when present;
`-B` alone was not assumed to bypass caches. No successful tests were repeated
after final verification.

## Limits and handoff

Single original reader is a caller obligation. Competing readers can consume
data between peek/read, and native operations still have OS scheduling behavior.
Call/byte bounds provide no hard elapsed-time/cancellation or owner-hang bound.
Data/empty are not inference responsiveness, initialization, life, authentication
or meaningful AI evidence. Diagnostic records are freely constructible. Future
EOF integration must retire its own provider/owner epoch before admission; this
leaf cannot do so and makes no authority calls or lifecycle transitions.

H01–H15 canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
and active director generation2 were verified and preserved. No real actor/model,
vendor/driver, board/service/OS change, GUI/input, network/peer send, Git commit
or additional agent occurred. Native operations were only local test-created
pipes and the bounded test process tree. No private endpoint was connected.

Real completion IPC, original dispatch/model/BOOT/source/clock/slot, PC_DIRECT,
HIL/UI integration and formal R03/full H12/all29 remain `not_run`. Main owns
independent review, acceptance and publication. Public manifest is frozen before
the original native completion receipt; safe complete is called once, its exact
persistent terminal read back, then this worker stops all writes.

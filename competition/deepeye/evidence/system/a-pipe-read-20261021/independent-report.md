Independent review of `A-R03-PIPE-READ-INDEPENDENT-20261021-v1`, native job
`child-e84f7e2fa1c74fa2ad45983fa5fc5953`, agent
`/root/pipe_read_review_20261021`.

No blocking defect was found in the assigned inactive pipe-read leaf. The
fixed implementation and its documented caller obligations are supported by
the source review, the retained author evidence, and two new independent local
native controls. This is bounded review evidence for the main's decision;
no integration, provider activation, formal acceptance or publication occurred.

Reviewed product HEAD is `68814fc6963f8ad8e774aa25f598bbd94c34acc1`.
The exact three new product files retain their assigned SHA-256 values:

| Product-relative path under competition/deepeye | SHA-256 |
|---|---|
| simulation/isolation/pipe_read.py | 08186c9c6132a04b33ef90f3d015cfed7a6634f2fc1094241b361d347bca3785 |
| tests/simulation/test_pipe_read.py | daa5cc3c5180ec0a1e7d8a19b361f16d03e6ad2470a24d89c963b56c4dc36eea |
| docs/pipe_read_boundary.md | 2453ee137cb07e39421c4900f76d936ce9f480ab3a9ea815c8dc0a2fe9ff024f |

The review found one informational test-coverage detail, with no required
source correction. At `tests/simulation/test_pipe_read.py:54-59`, the control
whose name mentions the default ceiling explicitly passes `8192`. That control
checks the ceiling calculation; the independent native scenario now also
exercises an actually omitted `max_bytes` argument against 9000 buffered bytes.
The author correctly distinguishes mocked native-call controls from actual
local-pipe cases. No author test class or old broad suite was rerun.

| Review location | Independently checked behavior |
|---|---|
| pipe_read.py:9,33-37 | Exact positive int handle bounded by native pointer width; exact int limit 1..8192; invalid arguments cannot reach `_native()` |
| win32.py:244-249 | PeekNamedPipe/ReadFile use HANDLE and DWORD bindings; accepted handle values cannot exceed the process pointer width |
| pipe_read.py:38-45; win32.py:283-286 | One peek, empty without read, otherwise one existing ReadFile helper with min(available,max_bytes) |
| pipe_read.py:46-51 | Only OSError.winerror 109 maps to EOF; other errors propagate; zero, oversized and non-exact-bytes reads refuse |
| pipe_read.py:12-16,25-31 | Frozen plain diagnostic record; original endpoint ownership and sole-reader usage remain caller obligations |
| pipe_read_boundary.md:25-44 | Competing-reader race, buffered drainage, lack of hard time/cancellation guarantees, no authentication/authority, and future owner-epoch retirement are explicit |

The module contains no retry loop, handle close, write, endpoint lookup,
timestamping, authority call or lifecycle transition. Its native binding import
is lazy and occurs after argument validation. A scan of all product Python
files outside tests found no `pipe_read` consumer. The existing
`available_output` helper and its cleanup use remain byte-identical.

The original author manifest
`a9cf431593a8edfbc4c3d5717f0634244b55535f91a882488074d75e8d48861f`
was rehashed, and all 50 public entries matched exact sizes and hashes.
All 33 existing source/doc inputs, the three new files, mandatory contract
inputs, product HEAD/ref and Git index hash matched before and after this
review. Original completion job
`child-d0981a47801240d8b289804acb5209ca` is recorded as completed/terminal,
not stale, with text exactly matching its retained final-result.txt.

Raw author evidence was checked without rerunning its tests:

| Original run | Verified retained result |
|---|---|
| red-01 | 12 failures specifically for absent component, no errors and no native pipes; process exit 1 |
| green-01 | 12 test assertions passed, then ctypes handle JSON serialization failed; process exit 1 and no structured test-result.json |
| green-02 | 12/12 passed, no errors/skips/prohibited attempts; process exit 0 |

The 12 test-method ASTs are unchanged between RED and final GREEN; only
`open_pipe`'s original-handle normalization helper changed. Production
`pipe_read.py` is identical across both GREEN runs. GREEN01 remains a failed
evidence run. Its exact handle events cannot be reconstructed from a structured
result that was never written, and this review does not invent them.

All nine retained original held-process records have a creation time, signaled
original process object and wait_result 0; all three original jobs ended with
active_processes_final 0. The three final author pipe cases record six original
endpoints, each closed once successfully. Their logs substantiate open-empty,
3/3/3/1 partial drainage, last-writer-close EOF, buffered bytes preceding EOF,
and actual immediately closed read-handle error 6. Error 5/232, generic errno
109, read-race 109 and invalid native-return values remain controlled cases.
Original successful import/read records were rehashed against the applicable
snapshots or unchanged source. No recorded project .pyc file required cached
code equivalence verification; `-B` was not treated as proof of source choice.

One fresh hidden bounded run supplied two independent controls:

1. A single 9000-byte write into a newly created pipe requesting 16384-byte
   capacity was read with the actual default argument as 8192 bytes. After the
   writer closed, the next poll returned the exact remaining 808 bytes, followed
   by EOF. Full payload and each observed piece matched independent expected
   bytes and hashes.
2. Two original anonymous pipes coexisted with four distinct live handles.
   Their payloads stayed separate while reads were interleaved. After both A
   endpoints closed, B retained its remaining 14 bytes, reported empty, accepted
   a fresh 13-byte write and returned that exact data. B reported EOF only after
   its own writer closed.

The run made ten actual `poll_output` calls, each with one native peek and at
most one native read. Empty/EOF calls made no ReadFile call. Native API wrappers
only counted and forwarded calls; they supplied no fake results. The fsynced
29-event journal exactly matches the final JSON, including every create/write/
close attempt and outcome. Four endpoint closes succeeded exactly once.
Requested capacity is recorded as requested, not promoted to an independently
measured kernel capacity.

The copied reviewed runner and boundary retain hashes
`80cc41fd629bc3618b50c88fbd97332ec14cdd8cbaf8f927f0235390664cb77d` and
`04cf7d53f3dbf1fca66aab05fe497ae193aab94a56ab4e0d36e81d1eb0a040fe`.
The run used the pinned existing interpreter with `-I -S -B -X utf8`, hidden
below-normal execution and suspended assignment to its own JobObject before
resume. Limits were 30 seconds, 512 MiB job memory, 256 MiB process memory,
four processes, 256 KiB stdout, 512 KiB stderr, 16 MiB/300 tree entries, and
512 MiB free reserve. The actual run exited 0 in approximately 0.312 seconds,
with no stop reason or failures, active_processes_final 0 and all three held
process objects signaled with wait_result 0. No unrelated process was touched.

The worker compiled the exact pinned source bytes for the isolation package,
`pipe_read.py` and `win32.py` through a source-only loader. It recorded zero
project .pyc reads. The outer verification checked each loaded source hash,
the test/source snapshots, runner hashes, interpreter image hash, journal,
payloads, native closure and process terminal records. Inputs stayed identical.
No native control was repeated after success.

Verification commands, all exit 0, were:

```text
.local/venv/Scripts/python.exe -B -X utf8 <owned-folder>/audit_inputs.py before
.local/venv/Scripts/python.exe -B -X utf8 <owned-folder>/run_independent.py
.local/venv/Scripts/python.exe -B -X utf8 <owned-folder>/audit_inputs.py after
.local/venv/Scripts/python.exe -B -X utf8 <owned-folder>/verify_independent.py
```

The canonical H01-H15 requirements hash remains
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`,
contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`. Active director generation 2
remains `01a13d7e-dcf1-7272-a738-a637dd62ff9d`. Only this review directory was
written. Product/index/branch, previous evidence and other workers were
read-only. No actor/model, external endpoint, network test, GUI/input, board,
service/driver/OS change, peer message, credential/provider change or delegation
was performed.

Remaining limits are substantive: this leaf does not establish genuine
completion IPC, dispatch/model operation, BOOT/source/clock/slot binding,
PC_DIRECT/HIL/UI integration, hard owner-hang cancellation or authenticated
completion. These layers, full H12, R03 and all 29 taskbook cards remain
`not_run`. A future consumer must establish its own ownership, sole-reader
discipline and EOF retirement before admission. Main retains all acceptance
decisions. The public manifest is sealed before this review job is completed;
the separate native completion receipt binds its exact final-result text.

# Original board-reception evidence

`integration/live_board_receipts.py` is the first bounded receiving component
for the authorized real-PL / PC_DIRECT headless diagnostic. It accepts an already
opened OS pipe/socket/device descriptor, duplicates it without inheritance, and
performs its own `os.read`. Regular files and caller-fed bytes are refused.
On Windows its duplicate uses binary mode. Only its constructing owner thread
may read, claim or close; close affects the duplicate and preserves evidence.
Explicit byte/read budgets bound both data and empty-read records.

`CaptureIdentity(operation_id, request_hash, tested_commit,
build_manifest_sha256, connection_generation)` binds correlation labels.
Their valid spelling does not authenticate the declared operation, board,
build or peer. The authority-owned opener must retain the actual authenticated
connection, same-build bit/HWH manifest, request, fresh connection generation
and exclusive reader. A local pipe also satisfies the OS type check; it is
never called FPGA evidence merely because this component accepted it.

`ReceiptLedger(fd, identity, *, max_bytes, max_reads, read_size=4096)` owns a
finite capture. `read_once()` performs exactly one OS call and returns original
frame receipt objects. Actual driver blocking policy remains in force: runtime
adoption needs nonblocking reads or a separately bounded upstream supervisor.
No thread, timer, retry service or board program is launched by this module.

Every read retains its exact bytes and actual host monotonic call interval.
The existing ABI3 decoder locates valid frames; the ledger records the original
packet slice and its read-index/offset/length spans. It never replaces received
bytes with `encode(decoded_frame)`. Corrupt data and noise remain in the read
journal, with decoder rejection/discard counters. Snapshot exports are detached
and can be saved after close; partial packets at EOF remain visible.
An entire OS read counts against its budget immediately, before decoding.
Unexpected parser failure retires further reads and claims. Recovery can emit
an embedded packet later than its actual end; exact original offsets are
matched in retained bytes, independently of the decoder's emission position.

A bracket around a blocking or buffered read is **not** a final-byte arrival
interval: bytes may have been queued earlier. Availability therefore starts
unknown. Only a real nonblocking `BlockingIOError` establishes an empty-queue
observation. Its call-start time is a conservative lower bound for subsequent
complete-frame availability at this descriptor; the retrieving read's return
time is an upper bound. These bounds say nothing about bytes waiting in USB,
UART, an upstream process, a held sensor sample, or FPGA acquisition. EOF is a
terminal condition, never an empty-queue anchor.
Each packet uses the empty observation and return time belonging to its last
original byte's read. Later recovery or a later empty observation cannot give
old bytes a newer timing claim.

`claim_board_response(event, *, context)` requires an original local unconsumed
receipt and known descriptor availability. It consumes before validation, then
uses the existing hardware_bridge-to-world_authority envelope validator. It
returns schema-checked JSON bytes, **not** `VerifiedEnvelope`,
`VerifiedObservation`, authenticated BOOT, or a motion grant. Both timing and
physical-capture record references stay null. Wrong session/epoch/frame kinds
are rejected. TELEM/EVENT cannot be relabeled STATE8; no observation mapper or
sample interval is fabricated. Existing production activation remains closed.

For software_fixture-through-real-PL diagnostics, preserve source_id 4 and
topology_id 2 in independently verified BOOT/context, keep the input-source
sidecar, and leave PC_DIRECT physical-capture references null. This ledger's
own context argument cannot establish that verification. Raw BRAM or host-made
frames do not become original board ABI3 frames. Full BOOT echo verification,
source clocks, causal model/broker association, actual AI-process supervision,
full-volume geometry/CAS, original deadlines and process-death stopping remain
required before a real end-to-end run. No H09/G03/R03/H12 or all29 acceptance
is granted by this software component.

New focused controls use actual local Windows OS pipes and independently built
CRC packets. They validate receiving behavior, not hardware, sensor accuracy,
transport authentication or timing calibration. No old software/board group is
replayed. H01–H15 and the pinned human contract remain unchanged.

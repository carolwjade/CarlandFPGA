# Original BOOT write and ACK echo transcript

`integration/boot_transcript.py` is a narrow diagnostic preparation component
for the real-PL / PC_DIRECT headless path. Main supplies an already-open OS
descriptor and the original `ReceiptLedger` for the same connection. The
component duplicates only the writer descriptor, uses one owner thread and
performs one actual `os.write`. It opens no endpoint, service or board program.
Regular files are refused. A pipe can satisfy these checks without any FPGA.

The explicit constructor is:

```python
BootTranscript(fd, ledger, *, identity, profile, profile_sha256,
               build_manifest, bit_sha256, hwh_sha256, session, mode,
               config_epoch, sequence, tick_ms, max_ack_checks, journal_path)
```

`identity` must be an exact `CaptureIdentity`, equal to the original ledger's
identity at construction, before writing and while checking ACKs. It retains
operation ID, overall request digest, tested commit, complete build-manifest
digest and connection generation. The overall request digest is a main-supplied
operation label; the exact BOOT packet has its own `raw_sha256`. Full lowercase
SHA256 strings and exact bounded integers are required; booleans are refused.

`profile` is a complete profile document, validated and copied before IO.
`profile_sha256` must equal the complete 32-byte digest from the frozen
`boot_profile.canonical_sha256`. This uses UTF-8 canonical JSON, sorted keys,
compact separators and excludes `host_inference`, exactly as that helper
specifies. The complete copied document remains in the transcript. The BOOT
payload carries only the helper's first 16 digest bytes; the journal retains
the full digest. Session/mode/epoch/sequence/tick construct the original request
through `boot_profile.boot_frame`; zero/unknown mode fields and reserved bits
are rejected by the frozen API. The component supports that API's valid modes;
main must explicitly select source 4/topology 2 for the software_fixture
PC_DIRECT diagnostic. It does not infer that choice.

`build_manifest` must be immutable original bytes, 1 byte to 1 MiB; its SHA256
must match `identity.build_manifest_sha256`. The exact bytes are retained as
hex, without rewriting a supplied manifest into a smaller host-made substitute.
`bit_sha256` and `hwh_sha256` retain explicit full digest labels alongside it.
These equalities establish correlation only: they do not authenticate the
actual build, manifest completeness, membership of bit/HWH in the manifest,
actual loaded overlay, connection, peer or tested commit. Main must separately
check the authoritative manifest, original files and actual same-build load.
No caller-provided string, identity, flag or valid digest grants that authority.

`journal_path` must have an existing parent and must not exist. Exclusive
creation and `fsync` persist a prepared header before construction returns.
`send_once()` persists a `write_started` / `started_unknown` record before it
enters the OS call. Its terminal record retains the complete attempted bytes,
SHA256, requested count, returned byte count when known, error type/errno and
actual host monotonic call interval. `written` means only that the OS call
returned the complete count. It does not prove UART transmission completed,
peer reception, FPGA execution, authenticated BOOT or a motion grant.

There is no automatic remainder write, resend, timer, BOOT retry or recovery
send. A short write is `partial_unknown`; any exception, including timeout or
interruption, is `write_error_unknown`, with unknown accepted byte count.
Journal failure before the call is `journal_error_no_write`; failure to persist
the result is `journal_error_after_write`, retaining the in-memory returned
count or original exception fields. Both prevent further operations. A second
send on that object is always refused after an attempt. Reopening any existing
journal, including a partial/crashed started record, is refused. Durability
uses the OS/filesystem `fsync` contract and does not assert power-loss guarantees
beyond it. A persistence failure can leave only a conservative started record.

Main must provide nonblocking IO or a separately bounded transport supervisor;
`os.write` inherits its descriptor's blocking policy. If the process dies or is
killed during a call, the started journal remains unknown. Main must reconcile
the original operation before arranging any new BOOT. Exclusive journal-path
creation is **not global operation/session deduplication**: a different path
can be created, so operation/session/connection uniqueness and crash recovery
remain main-owned prerequisites. Close and ACK checking never send bytes.

`check_ack(event)` requires a complete returned write, the exact original local
receipt object from that same ledger, an unchanged correlation identity and a
nonfailed ledger. It rejects copied, loaded, foreign, repeated and already-read
pre-write receipts. A packet split across pre-write and post-write reads is
also refused. At most `max_ack_checks` (1 to 64) comparisons are journaled;
an exact original mismatching ACK consumes one check. It compares the original
received `event.raw` directly with the original written packet using
`boot_profile.verify_boot_ack`, without re-encoding an ACK. The helper checks
session, mode, profile prefix, guard/slot fields, sequence and epoch. ACK tick
is deliberately not an echo field in that existing contract.

Each comparison retains exact raw bytes, hash, original read spans, read-call
intervals and any original descriptor-availability bound. Read-call intervals
do not prove arrival time. Even matching ACK bytes already buffered before a
write can be read afterward; this API cannot establish freshness. Availability
remains scoped to the descriptor queue and can remain unknown. Source sample
time and physical-capture references stay null. Results always carry
`authenticated=false` and `motion_authorized=false`; they create no
`BootBinding`, `VerifiedEnvelope`, `VerifiedObservation`, context authentication
or production activation. `snapshot()` returns detached diagnostic data, even
after close/failure. `close()` closes only its own duplicate and journal;
the caller descriptor and receive ledger retain their lifetimes.

New focused controls use real local Windows OS pipes for full writes, split
ACK reads and actual broken-pipe failures. Short writes are explicitly injected
by forwarding a prefix through the real pipe; timeout/interrupt uncertainty is
injected after an actual pipe write. Journal `fsync` failures are injected.
Those controls model fault handling and do not claim that a real serial driver
produced these failures. A prequeued unread matching ACK control demonstrates
why diagnostic echo is not freshness/authentication. All original RED/GREEN
logs and the final pipe journals/read ledgers are retained by the assigned
work evidence directory. No old test group or 384-case board baseline is run.

The component remains preparation for main-owned integration and independent
review. Source clocks, authenticated connection/BOOT/context/build, causal
model association, motion/geometry/deadline checks and real end-to-end evidence
remain outside it. H01-H15 and both H12 paths remain unchanged;
G03/R03/all29 remain `not_run`.

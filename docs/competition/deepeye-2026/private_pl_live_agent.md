# Bounded private PL live-session candidate

Source work `A-PRIVATE-PL-LIVE-AGENT-IMPLEMENTATION-20261026-v1`, child job `child-cd9276191988495285f3251356072fd2`. Root design pin: `6c447d414ad42b646f2961d9163a0090fead97ebda923c7c76b9e33f32def7d8`. This delivery contains new local component evidence only. No real prepare, SSH, sudo, ARM FIFO qualification, PYNQ import, image load, MMIO or board operation was run by the author.

## Files to integrate after Root review

Copy only the four mirrored candidate files to Root's owned product branch:

- `competition/deepeye/integration/private_pl_stream.py`
- `competition/deepeye/tools/diagnostic/private_pl_live_agent.py`
- `competition/deepeye/tools/diagnostic/run_private_pl_live.py`
- `competition/deepeye/tests/diagnostic/private_pl_live/test_private_pl_live.py`

The existing collector remains byte-exact 29717 bytes/SHA256 `723435f542b050405d8a6286a806a6561fbb613e6608ebf5f84407c7418407e6`, source commit `8b6e130c9d760ed9b4a935d8d5f6090203fa73b6`. Existing real host_clock remains 3704 bytes/SHA256 `091accae52c376d259d0057f7b93b23dc5f4143508025beec88394c4b657e376`. Neither file is modified/copied over by this candidate. Component fixture directories and owned test logs are evidence, not product integration files.

## One physical session, distinct from old nodes

Root chose one checked load and one START followed by multiple fresh requests/TRIGGERs, one stable actual generation, strictly increasing trigger and lane sequences, and four ACKs per complete scan. The explicit `_LiveSession` FSM reuses pinned helper Bus/session/wait/counter primitives; it does not call repeated collect()/capture(), use a lazy fixture iterator, or install a fake runtime. Every started/unknown request is terminal on failure; no TRIGGER/ACK resend occurs.

The original validator/snapshot uses an explicitly labelled `validation_fixture.json` solely to reuse unchanged package/HWH validation and all24 fresh snapshots. Its run/session/tag/nonce must match the new live session. **Its values and QPC are never staged as live input.** Every actual scan comes from its separate diagnostic request and has its own raw line SHA, sequence and original QPC. Do not relabel the old v4 batch fixture or its preserved success as a new live/fresh observation.

Budgets are checked before any image/MMIO: total_seconds positive<=10, poll_seconds positive<=2, max_scans integer1..16, idle_timeout_ms integer1..100. They are diagnostic bounds, not a physical100ms performance result. Actual active stdin and stdout are nonblocking with explicit session/idle/output deadlines. EOF, bad frame, sequence/session/clock mismatch, signal, timeout or output failure retires the session.

## Host two-phase owner and request hash convention

Run the integrated host script using the existing reviewed Windows interpreter with `-I -B -X utf8`, explicit `--template`, `--template-sha256`, and a new absent `--out`. Fixed `__file__` ancestry bootstraps only that integrated repository before package imports; no cwd/PYTHONPATH/.pth installation is used. `--help` exits before imports. `--import-check-only` verifies actual driver/codec/host_clock resolution and bytes before any QPC factory, directory preparation or SSH. This route was tested in an owned isolated subprocess with real unchanged host_clock plus final actual codec/driver, not only stubs.

The ordinary prepare phase creates exactly one actual QpcHostClock and retains it on its original thread. Template context has operation_id, tested_commit (the future **new live-agent source commit**), build_manifest_sha256, boot_id, session_id and tag; it excludes request_hash, clock_domain_id and现场sampleQPC. Template also supplies agent_source_commit equal to that new commit and original_repository_root for the existing strict SSH/provider evidence.

HOST_PREPARED.json is created exclusively/fsynced with actual clock metadata/domain, original PID/creation FILETIME/native thread, template and driver/agent/codec/collector/host_clock pins. The same original process waits only for a Root activation file, default120s, hard maximum120s (shorter allowed). Prepare expiry has no SSH/hardware effect. This is a bounded ordinary program wait, not model polling.

Root independently reviews and stages the actual request/source bytes, then writes `out/LIVE_REQUEST.json` and exclusive `out/ROOT_ACTIVATION.json`. Live request fields:

```text
schema_version: 1
phase: private_live; execute_a: true; attempts: integer1
requirements_sha256: c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804
context: HOST_PREPARED.context_seed (seven fields, including actual runtime clock_domain_id; no request_hash)
agent_source_commit: actual new live-agent commit == context.tested_commit
collector_source_commit: 8b6e130c9d760ed9b4a935d8d5f6090203fa73b6
agent_sha256: exact final private_pl_live_agent.py
codec_sha256: exact final private_pl_stream.py
session_nonce: fresh Root nonce equal to validation_fixture.a_reference.nonce
relay_owner_uid: actual original unprivileged board owner UID
total_seconds, poll_seconds, max_scans, idle_timeout_ms: selected bounds above
inputs: exact25 {relative_name: {bytes,sha256}} records
request_hash: SHA256(canonical JSON of all other fields)
```

Canonical JSON is UTF-8 with ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False. Both agent and host inject the verified top request_hash into the on-wire context; it is deliberately absent from stored context to avoid a cycle. CLI `--request-sha256` separately pins complete request **file bytes**, including the logical hash. `inputs` is exactly23 unchanged `package/...` files, the pinned collector and validation_fixture.json. Agent and codec are source-bound separately, avoiding self-reference. Remote flat bundle thus has28 files: those25 inputs, agent, codec and LIVE_REQUEST.json. Host source stays in its integrated mirrored repository layout.

Activation requires allowed:true, attempts:integer1, prepared_sha256, request_hash, request_file_sha256, agent_source_commit, remote_directory exactly `/tmp/deepeye-a-private-live-<logicalhash16>`, selected `scans`1..max_scans, four uint16 `values`, four uint8 opaque `qualities`, and optional stricter max_age_ns (integer>0 and<=100000000). Root stages and reads back the remote bytes before activation. `ACTIVATION_CONSUMED.json` is exclusive and durable before the sole SSH start. No duplicate/held activation can replay.

The same clock owner takes four new raw QPC readings immediately while constructing each actual input request, only after original READY/previous capture. It never reloads old QPC from a template, arrival time or board clock. Public HostOwner requires the exact real QpcHostClock/domain. Internal cores/fake clocks in tests are component-only. Source and context pins are rechecked after preparation. Missing/invalid data, stale return or failure retires the owner and preserves raw response **before** rejecting it. No freshness window is renewed by a response, heartbeat or duplicate.

## Credential/FIFO separation and relay-only qualification

One original hidden SSH process and its original Windows Job are retained/waited. Job assignment and nonblocking host stdin happen before sending any credential, so a constructor/Job failure cannot authorize remote physical work. Failures persist original process/handle/pipe cleanup records, including SSH_CONSTRUCTOR_TERMINAL. Existing strict SSH executable/key/knownhost pins and the existing AST provider recipe are reused, never reconfigured. Password bytes go to one original stdin write only and are never logged, hashed or represented in an exception.

The fixed unprivileged `--relay-original` entry reads exactly one bounded credential line (<=128 bytes, no read-ahead, nonblocking/select5s deadline established before reads). It passes only that line to the **original sudo child's private stdin PIPE**, then closes it. Whether sudo consumes zero or one line, the root agent never parses that pipe. Root data is only a new0600 FIFO under the creator's new0700 operation directory. Both ends reject symlinks/type/mode/UID/inode changes. Root opens NONBLOCK, checks its own5s startup deadline and consumes exactly fixed `DEEPEYE_PRIVATE_INPUT_V1\n`, without reading ahead. Relay writes that fixed nonsecret prelude before forwarding data. It is only a private transport handshake, never BOOT/authentication/wire evidence. Root then dup2s the FIFO to raw fd0, before PYNQ/image/MMIO; no old sys.stdin buffer is read.

Relay forward input/output is bounded/nonblocking and only one writer exists; EOF/error closes it so root gets EOF/partial-frame refusal and cleanup. Fixed RELAY_created/sudo_started/unknown/local_cleanup/completed files persist request/source/FIFO identity, original subprocess PID/startticks and actual wait/exit or unknown. No credential bytes/hash/repr appears there. Only the original sudo subprocess is waited/terminated; a local exit does not prove root STOP/exit. FIFO unlink requires this creator's same inode and a normally completed original child exit0; unknown/nonzero keeps it. No old queue, directory, service, permission or sudo-cache change occurs.

**Before any new physical release, Root must perform a separate new ARM relay-only qualification.** It uses the same reviewed source, its own new0700 directory/request/hash, phase `relay_qualification`, execute_a:false, attempts1, requirements hash, agent_sha256, actual relay_owner_uid, actual expected_boot_id and logical request_hash. Root invokes only `--relay-qualification --request ... --request-sha256 ...`; the fixed original sudo child selects only `--fifo-qualification`, never arbitrary command forwarding. It opens/checks the real FIFO/prelude, emits `relay_qualification_ready`, accepts only fixed nonsecret `DEEPEYE_PRIVATE_RELAY_QUALIFICATION_V1\n` followed by EOF, and emits/persists completion. PYNQ membership is observed from sys.modules and preexisting PYNQ rejects; helper/image/MMIO are absent. Qualification input has a5s deadline and output its own nonblocking deadline; failure persists QUALIFICATION_FAILURE with a fixed nonsecret reason. Root must bind actual ARM raw records/original handles and exit, not Windows fake-FIFO tests or elapsed time. **No ARM qualification has run in this delivery.**

## Protocol, cleanup and retained evidence

Strict newline JSON is canonical, <=16384 bytes/line; host request <=2048 bytes per single nonblocking original write, at most one in flight. Scan has schema1, kind diagnostic_scan, source_id4/source software_fixture, exact context, contiguous request_seq, four values, qualities and original_host_qpc_ns. Unknown fields, duplicate JSON keys, nonfinite, bool/float integer fields, reversed clocks, wrong identity/domain/sequence and replay reject. Responses are only diagnostic_ready, diagnostic_capture and diagnostic_stopped; exact raw10-word lanes, counters/generation/trigger/tag/QPC and ACK checks precede acceptance. They cannot construct native wire receipts, SourceLedger records, BOOT ACK/TELEM/STATE8, ActionCandidate or movement authority.

Final/emergency STOP's first hardware write is literal original MMIO0x0C=1, independent of healthy clock, journal or normal Bus. This shared path covers session-constructor failure too. SIGINT/SIGTERM are masked through its critical section. Up to32 raw status/tag read pairs can confirm exact integer0/0; it is explicitly a **read-count bound, not physical-time proof**. No unattempted cleanup result is cached. Clock/journal errors remain secondary, original primary survives terminal stdout failure, and physical confirmation is not erased or invented. Confirmed STOP with secondary errors still makes the overall operation nonzero. Raw unknown/started TRIGGER/ACK never retries; no old overlay restore occurs.

Host and root preserve raw stdout/stderr/journal, per-request original bytes/hash/QPC/domain, raw responses even on stale rejection, and primary/secondary terminal files. Closing/killing/waiting original local SSH/Job never establishes remote STOP/exit. Inspect original markers on uncertainty; never launch a replacement automatically.

New test evidence is under RED/GREEN stage directories. Initial expected RED:17 unavailable-feature failures before production code. Focused later REDs cover actual cleanup/type/output/signal/gate/relay/prelude gaps; all original failures remain. Latest complete new suite:45 tests, actual exit0 under pinned owned-Job supervisor `b1945ae4...`; native command/raw stdout/stderr/source pins are `green-full-03/`. All actual processes there stopped and Job active0 with cleanup checked. The isolated real-source preflight also has its own copied-source/raw-output/PID/exit receipt in `real-source-import-*` fixtures. The sudo zero/one helper control is narrow structural credential separation only, not actual sudo/FIFO/ARM validation.

One R7 test-harness mistake remains explicit: old unified exec session68947 ended outer supervisor exit1 after Popen.wait timeout30s; its original target HANDLE was lost, so target exit is **unavailable**, never waited0/1. Original stdout/stderr show3 tests/121.105s/errors2. Exact prior PID/start labels were subsequently only read for presence; absence is not a wait/exit proof. No PID lookup termination/replay occurred. See `red-relay-stage-gate/original-session-terminal-observation.json` and process-readonly-observation.json. Subsequent tests use Root's pinned owned-Job harness, including bounded mocked-clock R7 RED and full GREEN; none replay the timed-out process.

H01–H15/full H12,100ms, original29 cards, numerical/model/AI quality failures remain unchanged. Production providers, qualified causal model/candidate and headless atomic native bridge are still REQUIRED downstream work. This source4 diagnostic neither relabels sim_em nor manufactures8 features, and grants no motion or final acceptance. Root alone integrates/commits, approves ARM qualification, releases a new physical operation and decides acceptance.

# PC_DIRECT heartbeat executor stop gate

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`, work `A-pc-direct-watchdog-20261015-v1`.
Design input `1011259415a0916054eb580687612580bc1e5f09`, taskbook §8/A02/G06.
Human contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`; H01–H15 requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. No scope change.

`integration/pc_direct_watchdog.py` implements an independent, pure software
executor stop gate. It accepts raw `board_response` JSON bytes, invokes
`host_envelope.validate_message`, decodes the original CRC-protected STATE8
again and keeps health/order/command-deadline history in memory. It neither
accesses a board nor authenticates messages. Its result is a veto check:
`stop_required=False` means only that this guard currently has no stop reason.
It is never an executable motion grant or a proof of real FPGA observations.

## Call interface

| Call | Effect and required caller work |
| --- | --- |
| `PcDirectWatchdog(context=..., heartbeat_timeout_ns=..., now_ns=...)` | Starts stopped with no heartbeat or action. All arguments are required. Context must match the strict host context schema and topology 2. The caller must independently verify the negotiated BOOT/session/profile and current run. |
| `ingest_heartbeat(raw_bytes, producer=..., consumer=..., now_ns=...)` | Only explicit `hardware_bridge` → `world_authority` and `board_response` containing STATE 0x08 can refresh health. Role strings assert a route; they do not authenticate it. Bytes/bytearray go through the strict host validator, including original wire CRC, session/header epoch/payload epoch, reserved fields, context and receipt checks. |
| `track_authority_command(command_seq=..., deadline_ns=..., now_ns=...)` | Stores only the identity and absolute deadline of an action **already independently verified by authority**. It has no command payload, observation, model, credentials or verification-boolean input. Caller must validate the complete command and all remaining motion gates first. |
| `check(now_ns=...)` | Checks heartbeat and command expiration. Call before **every physics step**, including intervals with no incoming messages. An old returned snapshot must never be reused for a later step. |
| `cancel(now_ns=...)` | Clears the action, preserves command high-water history and any safety latch. A cancelled command cannot be installed again; an independently authorized newer command may be tracked if health remains good. |
| `reset(context=..., now_ns=...)` | Caller first stops the executor and independently completes a new BOOT. Requires a session ID never used by this object. Starts stopped again; no heartbeat or action survives. It does not perform or certify that handshake. |
| `context`, `heartbeat_timeout_ns` | Read-only public properties; context is a defensive deep copy. Decisions are frozen dataclasses of immutable scalars. |

All host times are strict nonnegative Python integer monotonic nanoseconds from
one clock domain; booleans, floats and strings are rejected. Timeout is a strict
positive integer, with **no default**. The caller must select and document its
UART/profile/slot/scheduler policy. The sensor source's separately specified
100ms `sensor_valid` timeout is not a UART STATE heartbeat timeout. No measured
UART timeout value is claimed here. This module's lifecycle/ordering policies
are an implementation candidate pending A main's independent review; they do
not amend the frozen ABI, taskbook or H01–H15.

## Heartbeat time and ordering

For receipt interval `[lower_ns, upper_ns]`, expiration is
`lower_ns + heartbeat_timeout_ns`; equality at expiration is already stopped.
This uses the earliest possible receipt, even when the interval is wide. No
upper-bound or current-processing-time substitution is permitted. Receipt must
not predate constructor/reset activation. Against the preceding valid heartbeat,
its lower bound must strictly increase and upper bound may not decrease.

Before processing **any** new heartbeat the guard checks the old deadline. Once
that deadline has passed, even an otherwise valid late frame cannot repair the
gap or restore the previous action. The caller must run the stop check often
enough for its actual physics integration; this module has no background timer
and cannot stop an executor that does not call it.

Both unsigned serial increments must be strictly forward and less than half
their ring: `0 < seq_delta < 2^15`, `0 < tick_delta < 2^31`. Zero, old and exactly
half-range deltas are rejected. Numerical rollover, such as seq 65535 → 0 and
tick 0xffffffff → 0, works within those bounds. A re-serialized envelope carrying
the same old wire frame cannot become new health by changing receipt alone.

Within one activation, cumulative sequence advance must stay below `2^16` and
cumulative tick advance below `2^31` milliseconds. Reaching either horizon stops
and requires a new BOOT/session. These deliberately conservative horizons bound
ambiguity/replay with constant frame-history storage. They support a numerical
rollover without allowing indefinite reuse of the ring. Unknown full-cycle
losses and an unseen old first packet are not distinguishable using unauthenticated
serial values; trusted bridge receive provenance, session uniqueness and correct
BOOT/reset isolation remain external obligations. The object retains used session
IDs only for its lifetime; a process restart requires the external authority to
stop and establish a new session, rather than reconstructing an old active gate.

## Stops, commands and reset

Initial missing heartbeat requires STOP but is not a fault latch. A valid fresh
first heartbeat establishes health only; it creates no action. STATE phase
`stopped=0` is normal for PC_DIRECT, which has no board motion ACK/capture. Phases
1/2/3 are health diagnostics here, never motion proof. Any fault flags or
`rejected=4` latch STOP and clear the active action without refreshing health.

Timeout, monotonic-clock regression, invalid clock type, malformed/unexpected
input, CRC/context/route/order failure and invalid command/reset input also
latch STOP. The first latched reason is preserved. Every runtime validation
exception clears the action before propagating `ValueError`; the executor must
STOP on exceptions and may not use an earlier decision. `check`/`cancel` cannot
clear a latch, nor can a later ordinary heartbeat or command. Recovery is a
stopped-state reset to a new independently verified session, then fresh health,
then an independently verified **new** command. There is no `verified=True`,
credential fallback, auto-BOOT or same-session clear-fault escape hatch.

Command sequence is a strict uint16, increasing within the session; command
sequence rollover requires a new BOOT, as distinct from heartbeat serial
rollover. Duplicate currently active identity retains the earlier deadline;
it may tighten but never extend it. An expired/cancelled/superseded identity
cannot become active again. Command expiry clears the action but does not
invalidate still-timely heartbeat health, so an independently authorized newer
command can be tracked. Rejected command input conservatively latches STOP.

The absolute deadline is supplied by external authority, which must compute
`min(first_issue + bounded_duration, sample_lower + observation_age_cap,
previous_deadline_for_same_command)` and check all provenance. This guard does
not calculate acquisition time or authorize that deadline. Heartbeat payload
`remaining_ttl_ms`, captured-looking fields and sequence never create an
observation, renew its acquisition time/age or change a command deadline.

## Integration and remaining evidence

This is single-owner synchronous state. The caller must serialize ingest,
command registration, reset and physics checks in the world authority loop;
there is no lock, broker, persistent ledger or process/ACL boundary here.
On process failure or restart, the executor must default to stopped. Consumers
must combine this veto with independent broker authorization, run/session/BOOT
verification, source/observation provenance and freshness, AI-process liveness,
geometry/collision/entry-exit legality and all action limits. Passing a sequence
and deadline directly from an untrusted process would bypass those obligations.

Tests use synthetic software fixtures and small hand-checked nanosecond values;
their tick/receipt pairs are not measurements. The module has no wire transport,
physical ADC/capture, FPGA/PC live link, AI liveness watcher, rendering, actuator
or automatic fallback. No test result here grants ENABLE or proves ACL isolation,
real board sensing, PC_DIRECT/HIL end-to-end execution, A02, G06 or other product
acceptance. Those remain dependent on actual integration and independently bound
operation ID/request hash/tested commit/raw hardware and runtime evidence. C's
`ai_pc/control_broker` and the other required topologies remain separate owners
and acceptance paths.

Run from the implementation worktree with the repository's existing Python
runtime and existing `.local/deepeye-host-deps` supplied as the subprocess
`PYTHONPATH`:

```text
python -B -X utf8 -m unittest discover -s competition/deepeye/integration -p test_pc_direct_watchdog.py -v
```

Exact RED/GREEN commands, exit codes, outputs, dependency/file hashes and review
limitations are saved under the owning root's
`.planning/deepeye-implementation-a/app-pc-direct-watchdog-20261015/`.

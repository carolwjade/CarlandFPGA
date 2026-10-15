# Candidate sensor source boundary

This is an independent **pure software** consumer of the existing
`ForwardProfile.to_payload()` record. It does not send hardware data or extend
`host_contract.json`. Task DEEPEYE-IMPLEMENTATION-20261014/v1; work_id
A-app-sensor-boundary-20261015-v1. Current director: Desktop chat
01a13d7e-dcf1-7272-a738-a637dd62ff9d, generation 2.

DEEPEYE-HUMAN-LOCK-20261014/revision1 and every H01-H15 remain mandatory.
The canonical requirements SHA256 is
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`, verified
against fixed design commit `1011259415a0916054eb580687612580bc1e5f09`.
Implementation baseline is `32dff0c4252b1e08dc54beee168fd3959bf822df`.
Taskbook sections 8.5, 8.6 and G03 require causal observations, hidden layout,
separate source/online evidence and a source heartbeat. G03/G09 and physical
product acceptance remain **not_run**.

## Data boundary and exact checks

The intended direction is world_authority -> hardware_bridge. Only the nine
existing fields are accepted: profile_id/status/note, source_mode, adc_tick_ms,
em_tick_ms, channel_values, channel_counts and quality. Exact metadata preserves
the uncalibrated candidate label. Unknown keys, missing keys, nested objects,
booleans posing as numbers, strings posing as numbers, non-finite values,
wrong channel lengths and inconsistent quality/counts fail with ValueError.
The strict JSON entry point also rejects duplicate fields and malformed UTF-8.
No truth, geometry, source callback, action or arbitrary spatial query is an
allowed field. Returned records are detached, frozen dataclasses with tuples;
callers must forward those validated fields, never the original raw object.

`docs/sensor_source_contract.json` is a descriptive candidate contract; executable
enforcement is in `integration/sensor_source.py`. The consumer pins the existing
candidate metadata, limits, 10ms/50ms periods and 100ms deadline independently.
It does not import producer internals or silently follow parameter changes.
Any future profile change needs explicit consumer review and a new contract.
EM saturation requires an endpoint; vibration saturation describes any clipped
sample in the ten-sample RMS window, so its RMS can be below 2g. No quantization
consistency check establishes calibration.

## API and clock assumptions

`validate_record(payload)` validates an already decoded JSON-shaped dict.
`validate_json(raw)` additionally preserves duplicate-key and encoding checks.
`SourceLedger(start_tick_ms=..., start_monotonic_ns=...)` creates an empty,
single-writer ledger for one externally bound run. `accept(payload,
received_monotonic_ns=...)` and `accept_json(raw, received_monotonic_ns=...)`
return Admission(record, new_em_sample, adc_gap_ms). The immutable `snapshot`
contains counts, last record, original EM watermark and receipt diagnostics.
The separate read-only `clock_high_water_ns` property reports the latest observed
trusted receiver clock, initialized to the run origin.
The ledger performs no file, network, serial or device I/O. It is not durable,
thread-safe or integrated into any running process.

The trusted receiver must establish the run's start tick / monotonic-nanosecond
origin independently of the incoming payload. A claimed ADC tick maps to
`start_monotonic_ns + (adc_tick_ms-start_tick_ms)*1000000`. Its mapped time
cannot be in the future or over 100ms old at ingress. Original EM time must
also still be fresh at ingress. Receiver times are strict integers. `healthy`,
`accept` and `accept_json` share one monotonic high-water mark; every clock
argument must be at least that mark. Equality is allowed. Each valid clock is
observed at method entry, before untrusted payload parsing/validation. Even a
malformed JSON record, wrong field or future sample cannot erase that trusted
time observation. Invalid clock types, negative values and backward clocks raise
without moving the mark. Only the clock observation changes on a rejected record;
the sample snapshot, sample/EM counts and heartbeat timestamps remain unchanged.
`healthy(now_monotonic_ns=...)` uses this same guard and does not mutate sample or
heartbeat records; a query may advance the clock high-water mark. Callers use
their actual monotonic clock, supplied independently of the payload.
No adjustable tolerance or drift model is provided here. This exact arithmetic
is a testable candidate assumption, not a measured clock bound. Real distributed
clocking needs a reviewed, measured mapping before adoption.

First ADC tick must equal the declared run origin, and the ledger requires
complete history from the producer's startup. It cannot attach to a warmed-up
model in the middle of a run, nor be recreated to erase faults. Run/session
identity is intentionally not added to the existing nine-field payload; binding
this ledger to one authenticated authority/channel/run remains integration work.

## 10ms ADC, 50ms EM, loss and heartbeat

ADC timestamps strictly increase on the 10ms grid. A new EM timestamp is counted
only when first received at that same ADC tick on the 50ms grid. A delayed first
appearance of EM50 in ADC60 is rejected as unobserved acquisition/backfill.
Regular ADC0..300 therefore gives 31 ADC records and seven EM acquisitions,
including EM0. Held records retain the original EM tick, numeric values, counts
and saturation; they never add independent EM observations. Numerically equal
values from genuinely new acquisitions are allowed: equality cannot identify
whether an acquisition happened.

An ADC gap is recorded rather than filled. It resets the consumer's contiguous
vibration sample count to one. The claimed C3 validity must exactly agree with
ten observed consecutive samples. A real producer ADC gap emits invalid C3 until
its window recovers and is supported. Transport loss may leave the producer
claiming a complete RMS that the receiver cannot audit; this strict candidate
rejects it. Loss of an acquisition's first record also prevents later held data
from introducing it. Such loss requires an explicit stop/new-run decision or a
separately reviewed resynchronization protocol; no resync is implemented here.

Source fault records retain explicit null EM fields and may carry valid vibration.
They are admitted as fault state but do not renew last_healthy_received_ns and
immediately make healthy() false. Old EM cannot revive as held data after a fault;
recovery requires a new, valid EM acquisition in its own ADC slot. Rejected
records change no sample/heartbeat state or deadline; a valid trusted clock
argument still advances the shared clock high-water mark. They do not erase the
last valid record; without valid progression its original deadline expires.

For example, after an origin-zero valid record, a health query at 110ms reports
expired. A subsequent health query or admission with receive time 90ms raises
ValueError even though 90ms is later than the last admitted receipt. The source
cannot revive by rewinding a query clock or retrying a rejected packet with an
earlier clock. A new valid admission at the same or a later observed time can
restore health if its own original EM time is still fresh.

Source health requires latest valid EM, receipt age <=100ms **and original EM
age <=100ms**. At exactly 100ms it is valid; any larger age faults. Late held
delivery cannot renew the original EM deadline. A caller must query health from
its actual runtime clock or schedule an equivalent deadline; this library has
no watchdog thread and cannot stop an actuator. `last_healthy_received_ns` records
healthy ingress including holds; it alone is never a freshness deadline.
This source heartbeat is separate from UART STATE 0x08, TELEM observation age,
PC_DIRECT command TTL and board health. None of those records is accepted here.

## Evidence and practical limits

Tests drive the existing ForwardProfile with explicit software noise and material
inputs, admit actual emitted records, then mutate them for attacks. They cover
unknown/truth keys, finite/type/quality/count constraints, future/off-grid/reverse
times, duplicate/backfill, fake accelerated tick progression, immutable holds,
source-fault persistence/recovery, ADC window loss and exact timeout edges.
They also admit valid startup, saturation, bounded receipt jitter and genuine
model ADC gaps. Test noise choices do not claim physical sensor behavior.

The producer's existing source_mode remains `twin_fixture` because this consumer
does not invent a replacement field or rewrite producer output. That declaration
does not establish that a physical DAC/XADC chain ran. All tests/evidence here
are software-only; no online detection range, ADC calibration or FPGA link pass
is claimed.

This boundary prevents structural field leakage and contradictory/replayed time
claims within its retained run state. It **cannot attest acquisition**: an
untrusted producer can forge plausible values and timestamps, encode information
within allowed scalar values, or supply a false clock origin through a compromised
caller. Authenticated process transport, restricted directories/ACLs, viewer and
AI isolation, trusted scheduler integration, adversarial equal-observation
controller invariance, independent FDEM applicability/convergence and all actual
DAC/XADC/PL/RS485 evidence remain required. Schema tests are not G03 completion.

Reproduce from the implementation worktree with its existing Python environment:

```powershell
& '<repository>/.local/venv/Scripts/python.exe' -B -X utf8 competition/deepeye/integration/test_sensor_source.py -v
& '<repository>/.local/venv/Scripts/python.exe' -B -X utf8 -m unittest discover -s competition/deepeye/tests/simulation -p test_forward_profile.py -v
```

The root planning directory
`.planning/deepeye-implementation-a/app-sensor-boundary-20261015/` retains baseline
hashes, RED/GREEN outputs, command argv/working directory/exit codes and the final
receipt for the director's independent review. No changes were made to the
producer, its existing tests, host contract or interface checker.

# Candidate source4 channel segment

`simulation/authority/live_chain_channels.py` connects the existing candidate
source admission ledger to the private PL request/returned-lane validator. It is
one source segment of the full chain. It is not yet the installed authenticated
ActorComposition channel, an owned CPU provider, a control broker or a Godot bridge.

The Root constructs `LiveFourChannelChannel(context, host_clock,
start_tick_ms=..., start_monotonic_ns=..., max_scans=16,
functional_timing_profile=...)` with the original fixed QPC clock and source run
origin. `accept_ready` consumes the original private diagnostic READY once.
`admit_sample` must receive every actual `ForwardProfile.to_payload()` record in
order from that origin, including records received while a board scan is pending.
It reuses one `SourceLedger`; it never restarts the ledger or backfills a gap.
The bounded history retains at most1001 actual admissions, sufficient for a
100Hz stream over the existing10s private session. A gap remains visible and
resets vibration-window validity according to the existing source contract.

`next_request()` chooses the latest new admitted ADC record, requiring its
original ADC time and any valid held EM time to be at most100ms old before
injection. Explicit source-fault/null EM diagnostics retain their fault state.
It reserves one
scan before the caller writes externally, retains the source admission and exact
request bytes, and refuses replacement, resending or reusing that source tick.
The original private transport performs its one write and returns exact bytes.
`accept_capture(raw)` first calls the original `HostOwner.accept`, retaining the
existing operation/request/build/session/generation/trigger/QPC/counter/lane and
four-ACK checks. Only the returned `raw_words[0]` and `raw_words[1]` supply the
candidate counts and quality. Original floating source values are never used
as a fallback or serialized in the candidate input. Word9 remains an opaque PL
latch-cycle diagnostic, not proof of compression or a decode ratio.

## Explicit quality mapping

The candidate output declares
`quality_encoding: "candidate_four_channel_quality_v1"`. This version describes
an A private diagnostic mapping; it does not change the public wire schema or
claim that B's four arbitrary u8 qualities already had these meanings.

| Per-channel private u8 bit | Original source quality bit |
|---|---|
| 0 valid | channel0..3 |
| 1 saturated | channel4..7 |
| 2 held | channel8..11 |
| 3 source_fault | shared bit12, repeated identically in all four lanes |
| 4..7 | reserved zero |

The mapping preserves all13 source bits. Decode rejects inconsistent fault
copies and reserved bits. A source channel with null count uses transport0
with valid=false; it returns to null after capture. It cannot become a valid
zero observation. Strict `SourceLedger` checks still reject impossible source
validity/held/saturation/time/count relationships before injection.

## Timing and evidence limits

The output identifies source profile
`deepeye_forward_profile_candidate_v1`, source `twin_fixture`, and transport
source4 `software_fixture`. Channels remain log10 apparent resistivity, yaw
difference, pitch difference and vibration RMS. They are not FORCE curves,
eight trained features, calibrated ADC measurements or `sim_em_v2`.

ADC/EM source ages use the pending admission's original ticks and Root-supplied
source schedule origin, evaluated at a conservative QPC upper bound after
capture validation. Host injection QPCs are recorded separately. A newer source
admission cannot refresh an older pending observation. The exact optional
`functional_chain_v1` permits a2s private response wait only; SourceLedger's
100ms source rules remain. A150ms response can be accepted as diagnostic bytes
and still explicitly report `source_fresh_at_capture: false` and
`target100ms_met: false`.

Payload flags always retain `transport_authenticated: false`,
`BOOT_authenticated: false`, `physical_sample_authenticated: false`,
`compression_verified: false`, `CPU_completion_created: false`,
`movement_authorized: false`, and final H12/100ms `not_run`. Hashes/context
matching establish correlation, not authentication. Source freshness is a
necessary data check, not authority to move. The original production gate
continues to reject until actual endpoint/BOOT/sample/completion/broker evidence
is installed and reviewed.

Failures permanently retire the channel and original PL owner, retaining the
pending bytes and bounded admission history. A failed, started-unknown or
consumed operation is never retried. The caller still owns transport/remote
STOP, CPU END/Wait/close and actual simulator-state integration.

NEW component controls are in
`tests/integration/test_live_chain_candidate_channel.py` and the review-derived
`tests/integration/test_live_chain_candidate_preservation.py`. They validate this
source segment using component clocks and synthetic returned lanes only; they
execute no board, real QPC, CPU model/actor or Godot run. No old test group was
rerun. Full sensing/compression/upload/PC-AI/control/simulator/next-observation
cycles, both H12 paths, complete3D/UI and original29 remain the objective.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

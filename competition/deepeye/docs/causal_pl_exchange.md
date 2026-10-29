# Root-owned causal private PL exchange

The original `run_private_pl_live.main` now has an explicit internal Root source
mode. Its default fixed-input mode is preserved. A Root bootstrap passes a fresh
`CausalSourcePump` as `_causal_source`; it is not a controller-supplied provider
or a new writer. The identical exact profile below must occur under
`candidate_source_profile` in the reviewed template, full hash-bound Root request
and one-time activation. Missing/mismatched declarations fail before SSH; the
causal activation must omit `values` and `qualities`. It cannot silently use the
old fixed inputs.

```json
{
  "name": "candidate_causal_source_v1",
  "signal_profile": "deepeye_forward_profile_candidate_v1",
  "quality_encoding": "candidate_four_channel_quality_v1",
  "source_age_cap_ns": 100000000,
  "session_max_ns": 10000000000,
  "max_source_records": 1001
}
```

Root supplies `CausalSourcePump(pose_reader, sampler, contact_reader=...,
medium_context="formation")`. `pose_reader()` reads the current original world
authority pose as `forward_profile.Pose`; `sampler(x, y, z)` is the authority-only
conductivity lookup; optional `contact_reader(tick_ms)` supplies already-occurred
contact acceleration, never a future collision oracle. These callbacks and their
world closure belong in the Root-reviewed source package. This interface does
not authenticate arbitrary callbacks. They never enter a controller payload.

The source warms only the static quadrature table before original SSH acquisition,
so warming cannot consume the board's input-idle window. After the original board
READY arrives, the host prepares and syncs its evidence directory before creating
the source origin. It takes the first actual sample immediately, then constructs
and admits it to one `LiveFourChannelChannel`; it never invents a missed tick0.
The fresh ForwardProfile acquires EM only on actual
50ms slots, and reads ADC at the current actual10ms slot. If the host missed a
slot, it emits the current record and records the gap; it does not backfill,
re-query a missed past pose or redraw noise for held samples. The existing
SourceLedger still validates every actual admission from run origin, including
startup/gapped vibration invalidity and original EM/ADC ages.

`_Transport.poll_line()` observes the same original process and OS pipes without
blocking. `(None, false)` means still pending; `(None, true)` requires original
process termination and a drained pipe. The existing blocking `line` retains its
timeout/error semantics. While one board request is pending, the Root loop
continues pumping source samples. It selects a new actual admitted sample for
each next request, rather than repeating activation constants. It never resends
a pending or consumed request. This is bounded to16 scans,1001 source admissions,
10s source session,10001 loop polls,8MiB new evidence, and the original per-request
response deadline. Root's existing transport still owns SSH/Job cleanup.

New module/source pins are included in HOST_PREPARED and checked again before
original SSH acquisition. Source declarations are part of the Root request hash;
the private per-scan wire shape is unchanged. The board agent still applies its
own current-BOOT/source/build checks; this host option does not waive them.

Evidence is written under `causal-exchange/`: exact source history, request bytes
and hashes before the sole write, raw responses before validation, candidate
returned-count payloads, original raw terminal and confirmed STOP readback. Source
history and request evidence are flushed/synced before an external write.
Failures retain the pending request and original error; teardown/log-close errors
remain secondary. The original host finally closes its own transport once. A
local wait or closed pipe never substitutes for remote raw STOP confirmation.

The fixed optional `functional_chain_v1`2s response profile remains separate from
the100ms source-age policy and final end-to-end100ms requirement. A diagnostic
response can be accepted but explicitly stale at capture. All outputs remain
candidate/twin_fixture via source4/software_fixture, with no manufactured BOOT,
ADC/FORCE qualification, compression proof, CPU completion or movement authority.
`actor_composition._production_channels` remains closed. This code is a callable
source/transport segment; a newly reviewed current-BOOT physical package and the
owned CPU/broker/native Run integration still need actual execution.

NEW `test_causal_pl_exchange.py` covers explicit selection, source pumping during
pending scans, changed observations, no backfill, raw rejection preservation,
EOF/no replay, finite stop, real local process pipe polling, close-error priority,
and an actual candidate-kernel counterfactual with controlled equal source noise.
It runs no SSH, board, trained AI model or old solver/test group. Native renderer
response has its own `authority_pose_bridge.md` evidence boundary. Neither source
component alone proves a complete closed loop or either full H12 mode.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

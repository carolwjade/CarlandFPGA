# Bounded functional diagnostic timing

`functional_chain_v1` is an explicit option for the private source4 / `software_fixture`
PL diagnostic path. It permits functional integration while preserving the default
100ms path and its wire record shapes. It does not grant BOOT, negotiated wire,
sensor observation, AI completion, action or movement authority.

The new Root request must include exactly this profile object, plus the matching
top-level input idle value:

```json
{
  "functional_timing_profile": {
    "name": "functional_chain_v1",
    "max_age_ns": 2000000000,
    "idle_timeout_ms": 2000
  },
  "idle_timeout_ms": 2000
}
```

These are fields within the original full private-live request, not a replacement
request. Its canonical logical `request_hash` includes the profile, and its raw
file SHA256 is independently bound by the original activation and agent entry.
Root activation must contain the identical complete profile and a separate
`max_age_ns: 2000000000`. Missing or conflicting declarations, explicit null,
unknown profile keys, booleans, nonfinite values, floats in integer fields and
larger bounds are rejected. A caller flag cannot select an arbitrary timeout.

`private_pl_stream.request_timing(request, activation)` validates the host pair.
The agent uses the same pinned codec with the original hash-checked request;
`_validated_session_timing` runs before FIFO, runtime imports, image loading or
MMIO. The standalone board codec adds no dependency. The existing limits remain:
total session at most 10s, poll at most 2s, at most 16 scans, and the original
TRIGGER/4-ACK/STOP state machine. Only input idle may become exactly 2000ms;
board output retains its at-most-100ms bound. The host capture wait becomes 2s.

Without the profile, input idle remains 1..100ms, the host's default age remains
100000000ns (and tighter legacy ages remain allowed), and the transport wait
remains 0.1s. A profile in activation without one in the request is rejected.
Functional FIFO-only qualification is rejected. No old operation is replayed.

Age remains measured from the first original host QPC sample to the actual
receiver QPC. As before, `0 <= age <= limit` is inclusive: exactly 2s is accepted
for this diagnostic profile; 2s + 1ns is rejected. Receipt, heartbeat or arrival
never refreshes sample time. Generation, trigger, context/request hashes, sequence,
lane words, original timestamps, counter increments and all four ACK checks are
unchanged. `STARTED_UNKNOWN` still prevents replacement or repeated writes.

Functional runs retain each `response-timing-NN.json`, including stale or invalid
captures which reached the owner. It contains actual `response_latency_ns`, original
first/receiver QPC values, the fixed age limit, `functional_capture_accepted`,
`target100ms_met`, and `formal_100ms_acceptance: "not_run"`. The target flag only
describes this single request-to-receive duration. For example, a valid 150ms
capture is functionally accepted and reports `target100ms_met: false`. A <=100ms
sample still cannot establish final latency or physical acceptance. Functional
`HOST_RESULT.json` adds the profile and timing list; legacy result and wire shapes
remain unchanged. Raw response bytes are retained before validation.

This change does not change downstream strict motion leases or final H01-H15,
1%, 100ms, both H12 paths or the original 29 acceptance items. Contract
`DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` remains fixed.
The NEW tests use component clocks and bounded transport fixtures only; their
success establishes neither real QPC timing nor a board/model/closed-loop result.

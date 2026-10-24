# Explicit PC_DIRECT consumption window v2

Task DEEPEYE-IMPLEMENTATION-20261014/v1; work
A-PC-DIRECT-WINDOW-V2-IMPLEMENT-20261024-v1. Contract
DEEPEYE-HUMAN-LOCK-20261014/revision1, H01-H15 unchanged; requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

The trusted main may explicitly configure
`AuthorityConfig(..., pc_direct_window_v2=PcDirectWindowV2(10_000_000))`.
Ten milliseconds is the root-selected policy, not a measured Windows scheduling
bound. Default `None` preserves legacy exact-slot consumption. HIL_PC_FPGA cannot
opt in. The production factory still unconditionally rejects before registry
acquisition. The policy installs no source, completion, slot, IPC, native actor
or model provider. The policy class is exported by `actor_composition` and defined
in `integration.candidate_mailbox`.

Activation freezes the original BOOT/profile, origin O, first primary-slot offset
F, period P and width W. The original verified grant supplies integer k. Only
`S=O+F+k*P` and `E=S+W` locate the window. Neither now nor ready selects a new k,
moves origin or opens a receipt-relative window. The frozen BOOT document/hash
is unchanged. Values and computed sums/products are strict bounded integers
(0 through 2**63-1), excluding bool and int subclasses; `0<W<P` is required.

`LatestCompletedMailbox.activate(..., pc_direct_window_v2=policy)` enables
`consume_pc_direct_v2(actual_now, grant=original_grant)`. Legacy `plan`/`consume`
and v2 consumption reject mixed policies and latch STOP. A v2 selection extends
the original fields with `consumed_at_ns` and `window_close_ns`; the selection is
policy output, not authentication or motion permission.

Original conservative bounds define `R=completion_upper+usb_upper+packing_upper`;
missing bounds never become zero. Original deadlines define
`D=min(completion_lower+progress_max_age, sample_lower+profile_age_cap)`.
Consumption requires retained original observation/completion and matching
BOOT/generation/source/clock, `R<=S`, `S<=actual_now<min(E,D)` and
`k>last_consumed_window`. E and D equality refuse. A newer late-ready pending
result cannot retrieve a replaced older result. Another original grant may use
a later fixed window only while the original deadlines remain valid.

The stateful owner retains the exact original completion proof. Selection records
k and clears pending before downstream admission. Changed requests, failed
ProgressGate/runtime/executor admission and exceptions never reinsert it. Exact
committed command bytes reuse the original proof without a second consumption,
slot callback or deadline renewal. A newly numbered command cannot reuse a
consumed candidate. STOP, reentry, foreign-thread veto and clock regression retain
the original irreversible retirement.

The composition preserves verifier, checkpoint, actual refreshed
`_progress_time()`, checkpoint, then selection. A verifier returning at E cannot
substitute an older event time. E limits consumption only. Motion may continue
after E while every original TTL, sample age, progress, heartbeat and actor
lifetime deadline remains valid. Geometry, original HANDLE sampling, whole-step
`step_end<deadline`, final callback and root CAS are unchanged. No logging, I/O,
hash, timer or extra callback is inserted between the final fence and CAS. A veto
after an observed positive CAS preserves the committed fact.

Early/late selection creates no movement. The composition's existing selection
failure retires the activation. This increment adds no retry/wait loop,
supervisor, resurrection or owner-hang stop guarantee. A future owner loop must
read actual monotonic time after ordinary bounded waiting; a timer wakeup is no
scheduling guarantee.

Only new focused policy/composition controls are run for this increment. Their
upstream source/completion/BOOT/transfer/native/clock evidence is synthetic;
mailbox, runtime, numerical geometry and executor CAS are real software. The
separate one-shot monotonic observation fixes one origin and performs one consume
attempt with actual time, without parameter changes or retry. Raw evidence is in
the assigned task evidence directory, including a miss if observed. Neither a
software pass nor a successful one-shot establishes scheduler bounds, real
provenance, AI usefulness, board behavior, H09, either full H12 path or formal
G03/R03/all29 acceptance. Production remains unavailable.

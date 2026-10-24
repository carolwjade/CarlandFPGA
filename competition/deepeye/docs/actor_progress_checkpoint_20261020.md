# Original actor inference progress checkpoint

The composed PC-direct numerical path now expires when its bound inference
completion becomes stale even while the original actor is alive. A heartbeat,
queue ACK, duplicate command or unrelated completion cannot renew that deadline.
The source is derived from `889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1`.

The private gate binds the original BOOT, source, monotonic domain, selected model,
candidate, invocation and exact command. It enforces ordered completion bounds,
strict increasing IDs for a new command, a fixed initial budget and irreversible
expiry/revocation. The final AI lease still samples the original actor and uses
the shorter lifetime/progress deadline. The frozen runtime rechecks time after
sampling and the executor requires the whole original dt to end strictly before
that deadline. No extra IPC, parser or clock callback was added at that final seam.

Evidence under `../evidence/system/a-actor-progress-20261020/` preserves the actual
three failing RED tests, author 193 passing regressions, independent 193 passing
regressions and eight independent counterexamples. All 24 original composition
test methods remain unchanged. The independent review found one Low issue in a
new test: its unrelated completion was never consumed. Main corrected that test
to return a mismatched completion through the actual lookup and checked rejection,
revocation and unchanged pose. The subsequent 45 focused tests passed. Only this
new test body changed after independent review; production and documentation bytes
remain the exact reviewed candidate. The new test hash has main follow-up evidence,
not a claimed second independent review.

Main selection SHA-256:
`d11dee5ec911a200d658325b6cafa778855bbbbe921562d82e7392f9aab120a7`.
Reviewed candidate manifest:
`23e07f12b6a22b0c264b2c8ed59312e0546a364423d2008d5f63894a8317b17f`.
The archive manifest identifies final source and original evidence bytes.

This is accepted bounded offline software. Tests use a synthetic verifier and
clock; the gate's object correlation does not authenticate a genuine producer.
Production channels remain unavailable. Genuine inference/BOOT/source/clock
providers, bounded live IPC, game integration, useful PC AI and both complete H12
control paths remain required. No native AI, hardware or game Run was performed
for this change. All 29 formal cards remain `not_run`.

`DEEPEYE-HUMAN-LOCK-20261014/revision1` H01–H15 is unchanged; canonical requirements
SHA-256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

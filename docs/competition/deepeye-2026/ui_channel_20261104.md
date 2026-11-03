# Continuous drilled channel and live dashboard

Human request: green drilled channel at the maximum drill diameter, clear on a
new round, top-centre panel toggle, concise UI, detailed real telemetry, and
model labels 钻头 / 钻入位置 / 钻出位置 with no channel annotation.

`continuous_drilled_channel.gd` receives only successful guarded native pose
writes from Main. It draws a 0.24m tube behind the drill, using the declared
drill-envelope constants, and resets its geometry and measurements per run.
Chunked MultiMeshes retain the passed path while rendering its current end
smoothly. This visual sibling is outside frozen sensor/collision geometry.

`continuous_dashboard_view.gd` formats actual native and host data. The panel
contains motion, channel length, source values/counts/age, E4 frame/payload
bytes, lossless comparison, sample-value compression ratio, AI decisions,
public gate approach, board PWM and host-clock timings. Missing values remain
absent. The final display retains actual complete/STOP data without refreshing
its original timestamp. Old editor captions are shortened only in the explicit
continuous entry; the existing editor and free camera remain available.

The generic public-gate adapter derives approach distance and reference from
current lateral/heading errors, curvature, body volume, pose age and public
workspace planes. It yields to newly observed avoidance; no private obstacle
coordinates are supplied to it.

Validation: new channel path/reset/diameter controls, dashboard value/cache
controls, native parsing, actual mouse fold/unfold, and actual run995 on the
opposite X faces. Run995 completed both causal avoidance episodes, the complete
entry/exit phase history, real STOP743 and clean SSH exit. The full actual raw
recording is retained; its 50s accelerated version is on Desktop.

Run995's recorded caption “采样→运动” measured source acquisition to native
control admission, not first movement. The final display source corrects this
caption to “采样→控制受理”; the original recording and evidence are unchanged.
After the run, resetting the renderer also clears its diagnostic end position;
the added reset check passes. These two small final changes are distinct from
the run995 source pins. This iteration does not claim final original29,
precision, latency, real ADC or formal sensor-model acceptance.

# Actual960 exit diagnosis970 — read only

Scope revision2 SHA2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d. No new numeric/source/physics evaluation, model, board/UI/network execution, product edit or export. Only recorded quaternion/vector arithmetic and original-state extraction.

Confirmed failure: native workspace_or_aperture, complete=false/arrival=false. The same actual run traversed both obstacles according to Root live observation, but this report does not promote it to complete crossing. Authentic STOP724 COMPLETE/unknownfalse, SSHwait=true/exit0/killedfalse. Fault6 is not a physical-zero capture measurement. Failed raw remains failed; export963 correctly refuses it.

The late-return diagnosis is supported. The original policy holds2.5m lateral lane until remaining8m, tapers desired lane offset to0 by3m, then switches to original797 centre/normal guidance. Actual motion has dynamic lag relative to the shrinking lane offset: by remaining3m the capsule centre is still1.454m off-axis and21.54 degrees tilted. Crucially the subsequent guidance itself requests a similarly tilted direction: at2m target24.648/actual24.594 degrees, at1m24.257/24.397, at.5m23.489/23.913. This is not chiefly a late-message or actuator-following failure.

|Requested remaining m|Actual remaining m|Centre lateral m|Actual heading deg|Latest target heading deg|Lane target offset m|Terminal guidance|Recorded JSONL line|
|---|---:|---:|---:|---:|---:|---|---:|
|12|12.0086|2.4662|0.538|0.487|2.5000|False|3088|
|10|10.0022|2.4806|0.309|0.281|2.5000|False|3367|
|8|8.0090|2.4889|0.178|0.160|2.5000|False|3638|
|6|6.0002|2.3995|8.318|10.895|1.6320|False|3921|
|4|4.0031|1.8471|20.783|21.593|0.2727|False|4209|
|3|2.9999|1.4537|21.540|21.680|0.0024|False|4354|
|2|2.0035|1.0147|24.594|24.648|0.0000|True|4507|
|1|0.9930|0.5530|24.397|24.257|0.0000|True|4655|
|0.5|0.4884|0.3263|23.913|23.489|0.0000|True|4733|

Nearest recorded samples were selected for each threshold, not synthesized poses. Latest completed AI/PWM are chronologically preceding each recorded native sample; these are not presumed simultaneous. ACTUAL_SAMPLES.json includes exact positions, original quaternions, forward vectors, desired public targets, yaw/pitch commands, actual curvature, request sequence and original line/time references.

At final accepted pose[-.2302598804,+.2302580476,-14.5130434036], lateral radius is~.32564m and heading~23.91 degrees. Applying the existing guard formula `max(norm(tangent + .4*projected_axis), norm(tangent - .4*projected_axis)) + .12` to THIS RECORDED pose yields.60775833m, already above.25m before inflation. Exit-normal capsule support is.48567216m; remaining centre-to-plane distance.48695660m shows the next tiny step first brings the leading volume to the face. The rejection is consistent with true capsule aperture protection, not an arbitrary angle threshold. Even the centre lateral offset alone exceeds the ring radius.

## Root proposed return12/end7 assessment

Changing return_start8→12 and end3→7 starts return4m earlier and switches to centre guidance4m earlier. The recorded state at12m already has stable lane lateral2.466m/heading.538 degrees and available forward distance, so this is a targeted minimal improvement with a reasonable causal rationale. It does not require source changes, hidden geometry, a new route, speed/TTL relaxation or collision bypass.

It is NOT sufficient to establish success from this trajectory alone. Tapering desired offset tozero does not certify actual position/heading has reached zero; the existing lookahead4m intentionally lags that taper. Original797 guidance points along a centre-seeking vector plus forward clearance. It does not impose a hard pre-face alignment condition. The actual last metre shows its requested heading can remain~24 degrees while closely tracked. Earlier7m adoption gives more opportunity to correct, but no new motion has been simulated or measured and no bound proves final lateral/attitude margins. Root may use12/7 as the next explicitly new case, but should not call it proven sufficient.

A meaningful public-only readiness check for any later refinement is the EXISTING projected-capsule aperture inequality (with actual guard inflation), achieved before leading volume reaches the exit face (centre remaining roughly.52m when aligned). It is stronger than “target offset==0”, “remaining<=7”, or centre-only proximity. If another correction is needed, use public gate centre/normal and own actual pose to settle lateral offset AND normal heading earlier; retain the original real full-volume guard. No suggestion here grants access to obstacles or modifies the current failed operation.

Code references: `competition/deepeye/ai_pc/continuous_observed_avoidance.py` remaining/blend/target/terminal_guidance block; unchanged797 guidance at `ai_pc/continuous_live_advice.py:236-247`; actual mapper `O7/continuous-command-map-810/command_map.py:83-93`; actual capsule/face guard `simulator/runtime/continuous_volume_guard.gd:10-33`. Policy selected by actual960 is099b329eb328bf33e1346af3e8bc90aa4848641b316d68675404d2684c5fdaa5, profile return8/end3. Controller Root_live_controller959.py exception line215. Formal original29 remains not_run.

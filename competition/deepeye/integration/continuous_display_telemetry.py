"""Read-only display derivations from correlated actual returns; no control IO."""
import math


def sense_fields(response, payload, returned_qpc_ns):
    rows = response['decoded']
    ledgers = [row['ledger'] for row in rows]
    counts = [row['points'][0]['value'] for row in rows]
    code_bytes = sum(v['stored_code_bytes'] for v in ledgers)
    raw_bytes = sum(v['selected_raw_bytes'] for v in ledgers)
    lows = (math.log10(.2), -2., -2., 0.)
    spans = (4., 4., 4., 2.)
    return dict(source_counts=counts,
        sensor_values=[None if c is None else low+span*c/4095. for c,low,span in zip(counts,lows,spans)],
        sensor_units=['log10(Ω·m)','Δlog10(Ω·m)','Δlog10(Ω·m)','g RMS'],
        sample_number=response['source_seq'],
        wire_bytes=len(bytes.fromhex(response['wire_hex'])),
        payload_bytes=sum(v['payload_bytes'] for v in ledgers),
        raw_baseline_bytes=raw_bytes,stored_code_bytes=code_bytes,
        compression_ratio=raw_bytes/code_bytes if code_bytes else None,
        codec_modes=[row['mode'].upper() if row['valid'] else '—' for row in rows],
        lossless_match=counts==payload['channel_counts'],
        sample_to_decode_ms=(returned_qpc_ns-int(payload['at_qpc_ns']))/1e6)


def ai_fields(advice):
    gate=advice.get('public_gate_approach',{})
    projection=gate.get('capsule_projection_with_age_m')
    return dict(ai_risk=advice['risk'],ai_uncertainty=advice['uncertainty'],
        ai_direction_world=advice['direction_world'],ai_speed_limit_m_s=advice['speed_limit_m_s'],
        ai_compute_ms=(int(advice['inference_completed_qpc_ns'])-int(advice['evaluated_qpc_ns']))/1e6,
        avoidance_count=advice.get('policy',{}).get('episode_number'),
        gate_control_state=gate.get('status'),gate_required_m=gate.get('required_approach_m'),
        gate_remaining_m=gate.get('remaining_m'),
        gate_projection_margin_m=None if projection is None else .25-projection)


def apply_fields(actual, command, motion_received_ns, advice):
    measured=actual['response']['result']
    return dict(command_speed_code=command['speed_code'],command_yaw_q=command['yaw_q'],
        command_pitch_q=command['pitch_q'],fabric_clock_hz=50_000_000,
        pwm_period_us=[v/50. for v in measured['pwm_period']],
        pwm_high_us=[v/50. for v in measured['pwm_high']],
        board_roundtrip_ms=(actual['host_returned_ns']-actual['host_before_ns'])/1e6,
        sample_to_motion_ms=None if advice is None else (motion_received_ns-int(advice['source_acquisition_qpc_ns']))/1e6)

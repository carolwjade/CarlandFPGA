extends RefCounted
## Pure evaluation of the live span law. This file grants no motion permission.
## The live owner must check the real board grant and whole-body/portal sweep
## before publishing a returned pose as an accepted simulator state.

static func _ns(value) -> int:
	if typeof(value) == TYPE_INT:
		return value if value >= 0 else -1
	if typeof(value) != TYPE_STRING or not value.is_valid_int(): return -1
	var parsed: int = value.to_int()
	return parsed if parsed >= 0 and str(parsed) == value else -1

static func _number(value) -> bool:
	return typeof(value) in [TYPE_FLOAT, TYPE_INT] and is_finite(float(value))

static func _array(value, size: int) -> bool:
	if not value is Array or value.size() != size: return false
	for item in value:
		if not _number(item): return false
	return true

static func _sinc(value: float) -> float:
	if absf(value) < 0.0001:
		var square := value * value
		return 1.0 - square / 6.0 + square * square / 120.0
	return sin(value) / value

static func sample_span(span: Dictionary, elapsed_ns: int) -> Dictionary:
	var required := ["dt_ns", "start_position_m", "start_orientation_xyzw", "start_speed_m_s", "target_speed_m_s", "acceleration_m_s2", "ramp_ns", "yaw_curvature_per_m", "pitch_curvature_per_m"]
	for key in required:
		if not span.has(key): return {"ok": false, "reason": "missing_" + key}
	var duration := _ns(span.dt_ns)
	var ramp := _ns(span.ramp_ns)
	if duration <= 0 or ramp < 0 or ramp > duration or elapsed_ns < 0 or elapsed_ns > duration:
		return {"ok": false, "reason": "span_time"}
	if not _array(span.start_position_m,3) or not _array(span.start_orientation_xyzw,4):
		return {"ok": false, "reason": "span_pose"}
	for key in ["start_speed_m_s","target_speed_m_s","acceleration_m_s2","yaw_curvature_per_m","pitch_curvature_per_m"]:
		if not _number(span[key]): return {"ok": false, "reason": "nonfinite_" + key}
	var v0: float = span.start_speed_m_s
	var vt: float = span.target_speed_m_s
	var acceleration: float = span.acceleration_m_s2
	var ky: float = span.yaw_curvature_per_m
	var kp: float = span.pitch_curvature_per_m
	if minf(v0,vt) < 0.0 or maxf(v0,vt) > 0.25 or absf(acceleration) > 0.25 or ky*ky+kp*kp > 0.250000000001:
		return {"ok": false, "reason": "physical_bounds"}
	var qraw: Array = span.start_orientation_xyzw
	var q0 := Quaternion(qraw[0],qraw[1],qraw[2],qraw[3])
	if absf(q0.length_squared()-1.0) > 0.00001:
		return {"ok": false, "reason": "orientation_norm"}
	q0 = q0.normalized()
	var ramp_seconds := float(ramp) * 0.000000001
	if absf(v0 + acceleration*ramp_seconds-vt) > 0.000001:
		return {"ok": false, "reason": "inconsistent_speed_ramp"}
	var seconds := float(elapsed_ns) * 0.000000001
	var r := minf(seconds,ramp_seconds)
	var distance := v0*r + 0.5*acceleration*r*r + vt*(seconds-r)
	var theta := sqrt(ky*ky+kp*kp)*distance
	var half_sinc := _sinc(theta*0.5)
	var local_delta := Vector3(ky*0.5*distance*distance*half_sinc*half_sinc,kp*0.5*distance*distance*half_sinc*half_sinc,distance*_sinc(theta))
	var delta_q := Quaternion(-kp*distance*half_sinc*0.5,ky*distance*half_sinc*0.5,0.0,cos(theta*0.5))
	var initial: Array = span.start_position_m
	var position := Vector3(initial[0],initial[1],initial[2]) + q0*local_delta
	var orientation := (q0*delta_q).normalized()
	# The completed ramp owns its exact validated endpoint, including pause=0.
	var speed := vt if elapsed_ns>=ramp else v0+acceleration*r
	return {"ok": true,"elapsed_ns":str(elapsed_ns),"position_m":[position.x,position.y,position.z],"orientation_xyzw":[orientation.x,orientation.y,orientation.z,orientation.w],"speed_m_s":speed}

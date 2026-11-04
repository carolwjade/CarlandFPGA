extends SceneTree
## Pure production ramp/kernel regression. No scene, socket, Native or board.
const Runner = preload("res://runtime/continuous_live_runner.gd")
const Law = preload("res://runtime/canonical_live_motion.gd")
var failures: Array[String] = []
var checks := 0

func _init() -> void:
	call_deferred("_run")

func _check(ok: bool, description: String) -> void:
	checks += 1
	if not ok: failures.append(description)

func _span(v0: float, target: float, seconds: float) -> Dictionary:
	var speed: Dictionary = Runner._speed_ramp(v0,target,seconds)
	speed["start_position_m"] = [0.0,0.0,0.0]
	speed["start_orientation_xyzw"] = [0.0,0.0,0.0,1.0]
	speed["yaw_curvature_per_m"] = 0.0
	speed["pitch_curvature_per_m"] = 0.0
	return speed

func _step(v0: float, target: float, seconds: float, want: float, label: String) -> float:
	var span := _span(v0,target,seconds)
	var sample: Dictionary = Law.sample_span(span,int(span.dt_ns))
	_check(sample.get("ok",false),label+": legal target rejected "+str(sample.get("reason"))+"; reached="+str(span.target_speed_m_s))
	if not sample.get("ok",false): return v0
	var speed: float = sample.speed_m_s
	_check(speed>=0.0 and speed<=0.25,label+": returned speed outside physical bounds")
	_check(absf(speed-want)<=0.000000001,label+": wrong independently expected ramp speed")
	if want==target: _check(speed==target,label+": did not reach the exact admitted target")
	return speed

func _run() -> void:
	# Actual last-good1314 speed; its stop ramp rounds to28,859,000ns.
	_step(0.00721474999999997,0.0,0.033333,0.0,"recorded_pause_endpoint")
	# Independently valid span catches Law returning v0+a*r after ramp ends.
	var stop := {"dt_ns":"33333000","ramp_ns":"28859000","start_position_m":[0.0,0.0,0.0],"start_orientation_xyzw":[0.0,0.0,0.0,1.0],"start_speed_m_s":0.00721474999999997,"target_speed_m_s":0.0,"acceleration_m_s2":-0.25,"yaw_curvature_per_m":0.0,"pitch_curvature_per_m":0.0}
	var stopped: Dictionary = Law.sample_span(stop,33333000)
	_check(stopped.get("ok",false) and stopped.get("speed_m_s")==0.0,"kernel_exact_stop_endpoint: residual="+str(stopped.get("speed_m_s")))
	_step(0.24998000000000004,0.25,0.008333,0.25,"upper_speed_endpoint")
	_step(0.000005,0.0,0.01,0.0,"tiny_pause_must_not_be_approximate_cruise")
	var speed := _step(0.0375,0.125,0.2,0.0875,"segmented_acceleration")
	speed = _step(speed,0.125,0.5,0.125,"segmented_target_hold")
	speed = _step(speed,0.025,0.2,0.075,"segmented_deceleration")
	_step(speed,0.0,0.4,0.0,"segmented_pause")
	# Invalid caller inputs must still hit the original strict physical gate.
	for bad in [["start_speed_m_s",-0.000001],["target_speed_m_s",0.250001],["acceleration_m_s2",0.250001],["yaw_curvature_per_m",0.51]]:
		var invalid: Dictionary = stop.duplicate(true)
		invalid[bad[0]] = bad[1]
		var rejected: Dictionary = Law.sample_span(invalid,33333000)
		_check(not rejected.get("ok",false) and rejected.get("reason")=="physical_bounds","invalid "+str(bad[0])+" bypassed strict physical gate")
	print(JSON.stringify({"checks":checks,"failures":failures,"hardware":false,"native":false,"scene":false}))
	quit(0 if failures.is_empty() else 1)

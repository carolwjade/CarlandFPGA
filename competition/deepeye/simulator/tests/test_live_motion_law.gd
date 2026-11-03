extends SceneTree
const Law = preload("res://runtime/canonical_live_motion.gd")
func _initialize() -> void:
	var span := {"dt_ns":"1000000000","start_position_m":[0.0,0.0,0.0],"start_orientation_xyzw":[0.0,0.0,0.0,1.0],"start_speed_m_s":0.025,"target_speed_m_s":0.025,"acceleration_m_s2":0.0,"ramp_ns":"0","yaw_curvature_per_m":0.0,"pitch_curvature_per_m":0.0}
	var middle: Dictionary = Law.sample_span(span,500000000)
	var end: Dictionary = Law.sample_span(span,1000000000)
	var ok: bool = middle.ok and end.ok and absf(middle.position_m[2]-0.0125)<0.000001 and end.speed_m_s==0.025
	span.start_position_m=end.position_m
	var successor: Dictionary = Law.sample_span(span,0)
	ok = ok and successor.ok and successor.position_m==end.position_m and successor.speed_m_s==end.speed_m_s
	span.start_speed_m_s=0.01
	span.acceleration_m_s2=0.25
	span.ramp_ns="60000000"
	span.yaw_curvature_per_m=0.5
	var curved: Dictionary = Law.sample_span(span,500000000)
	ok = ok and curved.ok and curved.position_m[0]>0.0 and curved.speed_m_s==0.025
	print(JSON.stringify({"passed":ok,"scope":"continuous canonical pose law and join only","board":"not_run","live_installer":"not_run","all29":"not_run"}))
	quit(0 if ok else 1)

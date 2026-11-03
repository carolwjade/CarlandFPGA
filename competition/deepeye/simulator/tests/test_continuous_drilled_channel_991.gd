extends SceneTree

var failures: Array[String] = []
func check(ok: bool, detail: String) -> void:
	if not ok: failures.append(detail)
func _initialize() -> void:
	run.call_deferred()
func run() -> void:
	var code = load("res://runtime/continuous_drilled_channel.gd")
	if code == null:
		print(JSON.stringify({"passed":false,"failures":["channel renderer missing"]}))
		quit(1)
		return
	var trail = code.new()
	root.add_child(trail)
	trail.reset_channel("first", 0.12, 0.40)
	trail.record_accepted_center(Vector3.ZERO)
	trail.record_accepted_center(Vector3.ZERO)
	check(is_zero_approx(trail.metrics().travelled_m), "stationary pose must not grow channel")
	trail.record_accepted_center(Vector3(0,0,1))
	trail.render_pending()
	check(is_equal_approx(trail.metrics().channel_diameter_m,0.24),"diameter follows maximum drill envelope")
	check(is_equal_approx(trail.metrics().channel_length_m,0.48),"channel ends behind rigid drill and rounded end cap")
	check(trail.last_rendered_center().is_equal_approx(Vector3(0,0,0.48)),"only passed actual path becomes channel")
	trail.record_accepted_center(Vector3(1,0,1))
	trail.render_pending()
	check(trail.last_rendered_center().is_equal_approx(Vector3(0.48,0,1)),"turn follows accepted polyline, not future direction")
	check(not contains_nonvisual(trail),"channel has no collision object or annotation")
	trail.reset_channel("second",0.12,0.40)
	check(is_zero_approx(trail.metrics().travelled_m) and trail.get_child_count()==0,"new run clears prior geometry and distance")
	check(trail.last_rendered_center()==Vector3.ZERO,"new run clears visual endpoint")
	trail.free()
	print(JSON.stringify({"passed":failures.is_empty(),"failures":failures,"scope":"visual channel only"}))
	quit(0 if failures.is_empty() else 1)
func contains_nonvisual(node: Node) -> bool:
	if node is CollisionObject3D or node is CollisionShape3D or node is Label3D:return true
	for child in node.get_children():
		if contains_nonvisual(child):return true
	return false

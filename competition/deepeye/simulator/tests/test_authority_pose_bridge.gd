extends SceneTree
## New focused native test. Synthetic sources do not authenticate a live chain.
var failures: Array = []
var checks := 0
var rows: Array = []

func _initialize() -> void:
	_run.call_deferred()

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _run() -> void:
	if not ResourceLoader.exists("res://viewer/authority_pose_bridge.gd"):
		check(false, "authority pose bridge is not implemented")
		_finish()
		return
	var script = load("res://viewer/authority_pose_bridge.gd")
	if script == null or not script.can_instantiate():
		check(false, "bridge script must load")
		_finish()
		return
	var bridge = script.new()
	var parent := Node3D.new()
	root.add_child(parent)
	parent.transform = Transform3D(Basis(Vector3.UP, 0.4), Vector3(3, 2, 1))
	var target := Node3D.new()
	parent.add_child(target)
	check(bridge.bind_target(target, "run-1"), "bind original native Node3D")
	check(not bridge.bind_target(target, "other"), "cannot rebind a run")
	var frames = JSON.parse_string(FileAccess.get_file_as_string("res://fixtures/frames.json"))
	for frame in frames:
		var reply: Dictionary = bridge.apply_frame(frame)
		check(reply.get("accepted", false), "accept committed owner revision")
		var readback: Dictionary = bridge.readback()
		check(readback.pose_revision == frame.pose_revision, "revision read from native metadata")
		check(readback.authority_revision == frame.authority_revision, "actual authority revision copied to native metadata")
		check(readback.stopped == frame.stopped, "native STOP snapshot status")
		check(readback.run_id == "run-1", "bound run readback")
		var p = frame.position_m
		check(target.global_position.distance_to(Vector3(p[0], p[1], p[2])) < 0.00001, "actual native world position")
		check(abs(target.global_basis.z.z + 1.0) < 0.00001, "actual native quaternion rotation")
		check(abs(readback.position_m[2] - p[2]) < 0.00001, "readback from actual transform")
		rows.append(readback)
	var before: Transform3D = target.global_transform
	var before_read: Dictionary = bridge.readback()
	var good: Dictionary = frames[1].duplicate(true)
	good.pose_revision = 3
	good.authority_revision = 6
	var mutations: Array = [
		{"run_id": "wrong"}, {"run_id": ""}, {"authority_revision": 5},
		{"authority_revision": 4}, {"authority_revision": -1}, {"authority_revision": true},
		{"authority_revision": 6.5}, {"authority_revision": 9007199254740992.0},
		{"pose_revision": 1}, {"pose_revision": -1}, {"pose_revision": true},
		{"pose_revision": 3.5}, {"pose_revision": 9007199254740992.0},
		{"position_m": [0, NAN, 0]}, {"position_m": [0, INF, 0]},
		{"position_m": [0, 1e100, 0]}, {"position_m": [0, true, 0]},
		{"position_m": [0, 0]}, {"orientation_xyzw": [0, 0, 0, 0]},
		{"orientation_xyzw": [0, 0, 0, 2]}, {"orientation_xyzw": [0, 0, NAN, 1]},
		{"stopped": 0}, {"scene": {}}, {"obstacles": []}, {"seed": 1},
		{"editor_history": []}, {"collision_oracle": "CLEAR"}]
	for mutation in mutations:
		var bad: Dictionary = good.duplicate(true)
		bad.merge(mutation, true)
		check(not bridge.apply_frame(bad).get("accepted", true), "reject invalid frame")
		check(target.global_transform == before, "rejection leaves actual native pose unchanged")
		check(bridge.readback() == before_read, "rejection leaves native revision/status unchanged")
	for geometry in [{"position_m": [0, 0, 1]}, {"orientation_xyzw": [0, 0, 0, 1]}]:
		var changed: Dictionary = frames[2].duplicate(true)
		changed.authority_revision = 6
		changed.merge(geometry, true)
		check(not bridge.apply_frame(changed).get("accepted", true), "same pose revision cannot change geometry")
		check(target.global_transform == before, "same revision geometry refusal has no mutation")
		check(bridge.readback() == before_read, "same revision geometry refusal preserves native metadata")
	for key in good:
		var missing: Dictionary = good.duplicate(true)
		missing.erase(key)
		check(not bridge.apply_frame(missing).get("accepted", true), "reject missing field")
		check(target.global_transform == before, "missing field has no pose side effect")
		check(bridge.readback() == before_read, "missing field has no metadata side effect")
	# A changed actual node must be visible in readback, not a cached input echo.
	target.global_position = Vector3(7, 8, 9)
	var actual: Vector3 = target.global_position
	check(actual.distance_to(Vector3(7, 8, 9)) < 0.00001, "external native pose changed")
	check(bridge.readback().position_m == [actual.x, actual.y, actual.z], "readback observes actual external native transform")
	parent.free()
	check(not bridge.apply_frame(good).get("accepted", true), "freed target rejected")
	_finish()

func _finish() -> void:
	print(JSON.stringify({"checks": checks, "failures": failures, "native_rows": rows}))
	quit(0 if failures.is_empty() else 1)

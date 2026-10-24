extends SceneTree
## Headless SceneTree tests for editor/scene_document.gd (G02 editing foundation, A-only).
## Run from the simulator project root:
##   godot --headless --path . --script res://tests/test_editor_document.gd
## Non-zero exit code means failure. Runtime execution state is recorded in
## competition/deepeye/evidence/game/editor_foundation.txt. These tests cover the
## editor document (undo/redo, gate geometry validity, edit-state gating, random
## layout bounds/reproducibility, disabled run bridge and Esc stop request) plus
## headless runtime regressions of the real viewer scene (initial panel layout
## before any resize, history/overlap refresh, pointer release over panels);
## they are not a G02 product acceptance.

const DocScript = preload("res://editor/scene_document.gd")

var _checks := 0
var _failures: Array = []

func _initialize() -> void:
	print("== test_editor_document (SceneDocument headless) ==")
	_run("initial_state_and_guards", test_initial_state_and_guards)
	_run("undo_redo_depth_ge_50", test_undo_redo_depth_ge_50)
	_run("gate_editing_and_validation", test_gate_editing_and_validation)
	_run("forbidden_edits_running_paused_locked", test_forbidden_edits_running_paused_locked)
	_run("random_layout_bounds_reproducible", test_random_layout_bounds_reproducible)
	_run("run_bridge_disabled_and_esc_stop", test_run_bridge_disabled_and_esc_stop)
	_viewer_runtime_tests.call_deferred()

func _viewer_runtime_tests() -> void:
	var before := _failures.size()
	await test_viewer_initial_layout_and_ui_refresh()
	_report_async("viewer_initial_layout_and_ui_refresh", before)
	before = _failures.size()
	await test_viewer_pointer_release_over_panel()
	_report_async("viewer_pointer_release_over_panel", before)
	before = _failures.size()
	await test_greybox_drill_actual_mesh_envelope()
	_report_async("greybox_drill_actual_mesh_envelope", before)
	print("TESTS checks=%d failures=%d" % [_checks, _failures.size()])
	if _failures.is_empty():
		print("RESULT PASS")
		quit(0)
	else:
		for failure in _failures:
			print("FAILURE: " + failure)
		print("RESULT FAIL")
		quit(1)

func _report_async(name: String, before: int) -> void:
	if _failures.size() == before:
		print("PASS " + name)
	else:
		print("FAIL " + name)

func _run(name: String, fn: Callable) -> void:
	var before := _failures.size()
	fn.call()
	if _failures.size() == before:
		print("PASS " + name)
	else:
		print("FAIL " + name)

func _check(condition: bool, what: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(what)

func test_initial_state_and_guards() -> void:
	var doc = DocScript.new()
	_check(doc.run_state == "editing", "initial run_state is editing")
	_check(doc.obstacle_count() == 0, "new document starts with an empty scene")
	_check(doc.commitment_hash() == DocScript.new().commitment_hash(), "empty layout hash is stable")
	_check(doc.undo().ok == false, "undo on empty history is rejected")
	_check(doc.redo().ok == false, "redo on empty history is rejected")
	_check(doc.can_edit(), "editing state allows edits")
	_check(doc.validate_gates().valid, "default gates valid")

func test_undo_redo_depth_ge_50() -> void:
	var doc = DocScript.new()
	for i in 80:
		var res: Dictionary = doc.add_obstacle("hard_rock",
			Vector3(float(i % 10) - 5.0, 0.0, float(i / 10) - 4.0), Vector3.ZERO, Vector3(1.0, 1.0, 1.0))
		_check(bool(res.get("ok", false)), "add #%d accepted" % i)
	_check(doc.obstacle_count() == 80, "80 objects added")
	var undone := 0
	for i in 50:
		if bool(doc.undo().get("ok", false)):
			undone += 1
	_check(undone == 50, "at least 50 consecutive undos available (got %d)" % undone)
	_check(doc.obstacle_count() == 30, "50 undos removed exactly 50 objects")
	var redone := 0
	for i in 50:
		if bool(doc.redo().get("ok", false)):
			redone += 1
	_check(redone == 50, "redo restores 50 steps (got %d)" % redone)
	_check(doc.obstacle_count() == 80, "redo restores the object count")
	doc.undo()
	var before_new_hash := doc.commitment_hash()
	doc.add_obstacle("void", Vector3(0.0, 0.0, 0.0), Vector3.ZERO, Vector3(3.0, 3.0, 3.0))
	_check(doc.redo().ok == false, "new edit clears the redo stack")
	_check(doc.commitment_hash() != before_new_hash, "new edit changed the layout hash")

func test_gate_editing_and_validation() -> void:
	var doc = DocScript.new()
	_check(doc.gate_position("entry").is_equal_approx(Vector3(0.0, 0.0, 15.0)), "default entry at front centre")
	_check(doc.gate_position("exit").is_equal_approx(Vector3(0.0, 0.0, -15.0)), "default exit at back centre")
	_check(DocScript.GATE_DIAMETER_M == 0.30, "gate diameter pinned to 0.30 m")
	# Edge margin: 15.0 - 14.86 = 0.14 < 0.15 must be rejected and must not move the gate.
	var reject_margin: Dictionary = doc.set_gate("entry", "front", 14.86, 0.0)
	_check(reject_margin.ok == false, "edge margin violation rejected")
	_check(str(reject_margin.get("errors", [])).find("0.15") != -1, "rejection reason mentions the 0.15 m margin")
	_check(doc.gates.entry.u == 0.0 and doc.gates.entry.v == 0.0, "rejected set left entry unchanged")
	# Exactly 0.15 m margin is the legal boundary.
	var accept_margin: Dictionary = doc.set_gate("entry", "front", 14.85, 0.0)
	_check(accept_margin.ok == true, "centre at exactly 0.15 m from the edge is accepted")
	# Return entry to centre; same-face overlap must be rejected without touching the other gate.
	doc.set_gate("entry", "front", 0.0, 0.0)
	var overlap_reject: Dictionary = doc.set_gate("exit", "front", 0.2, 0.0)
	_check(overlap_reject.ok == false, "same-face overlapping circle rejected")
	_check(doc.gates.exit.face == "back", "rejected overlap left exit on its old face")
	_check(doc.gates.entry.u == 0.0, "rejected overlap never auto-moved the entry gate")
	var accept_touch: Dictionary = doc.set_gate("exit", "front", 0.3, 0.0)
	_check(accept_touch.ok == true, "same-face separation of exactly 0.30 m accepted")
	var reject_touch: Dictionary = doc.set_gate("exit", "front", 0.29, 0.0)
	_check(reject_touch.ok == false, "same-face separation of 0.29 m rejected")
	_check(doc.gates.exit.u == 0.3, "rejected 0.29 m set kept the previous value")
	# All six faces can host the exit circle (same face as entry is only rejected when overlapping).
	doc.set_gate("entry", "top", 0.0, 0.0)
	for face in DocScript.FACES:
		var res: Dictionary = doc.set_gate("exit", face, 0.0, 0.0)
		if face == "top":
			_check(res.ok == false, "same-face zero separation rejected")
		else:
			_check(res.ok == true, "exit circle settable on face " + face)
	# Face-local u/v mapping for two different faces.
	doc.set_gate("exit", "front", 3.0, 2.0)
	_check(doc.gate_position("exit").is_equal_approx(Vector3(3.0, 2.0, 15.0)), "front face u/v maps to (x, y)")
	doc.set_gate("exit", "right", 3.0, 2.0)
	_check(doc.gate_position("exit").is_equal_approx(Vector3(15.0, 2.0, 3.0)), "right face u/v maps to (z, y)")
	var bad_face: Dictionary = doc.set_gate("exit", "diagonal", 0.0, 0.0)
	_check(bad_face.ok == false, "unknown face rejected")
	_check(doc.validate_gates().valid, "final gate pair validates")
	_check(doc.validate_gates().pending_authority.size() >= 1, "authority-pending checks are listed")

func test_forbidden_edits_running_paused_locked() -> void:
	var doc = DocScript.new()
	doc.add_obstacle("water", Vector3.ZERO, Vector3.ZERO, Vector3(6.0, 4.0, 2.0))
	var object_id: int = doc.obstacles[0].object_id
	var hash_before := doc.commitment_hash()
	_check(doc.set_run_state_for_testing("running"), "test hook sets running state")
	_check(doc.add_obstacle("void", Vector3(5.0, 0.0, 0.0), Vector3.ZERO, Vector3(2.0, 2.0, 2.0)).ok == false, "add rejected while running")
	_check(doc.remove_obstacle(object_id).ok == false, "delete rejected while running")
	_check(doc.update_obstacle(object_id, {"position": Vector3(1.0, 1.0, 1.0)}).ok == false, "move rejected while running")
	_check(doc.set_gate("entry", "left", 0.0, 0.0).ok == false, "gate edit rejected while running")
	_check(doc.undo().ok == false, "undo rejected while running")
	_check(doc.randomize_layout(7, 5).ok == false, "random re-layout rejected while running")
	_check(doc.commitment_hash() == hash_before, "layout hash unchanged while running")
	_check(doc.set_run_state_for_testing("paused"), "test hook sets paused state")
	_check(doc.add_obstacle("void", Vector3(5.0, 0.0, 0.0), Vector3.ZERO, Vector3(2.0, 2.0, 2.0)).ok == false, "add rejected while paused")
	_check(doc.update_obstacle(object_id, {"position": Vector3(1.0, 1.0, 1.0)}).ok == false, "move rejected while paused")
	_check(doc.undo().ok == false, "undo rejected while paused")
	_check(doc.set_gate("entry", "left", 0.0, 0.0).ok == false, "gate edit rejected while paused")
	_check(doc.commitment_hash() == hash_before, "layout hash unchanged while paused")
	_check(doc.set_run_state_for_testing("locked"), "test hook sets locked state")
	_check(doc.add_obstacle("void", Vector3(5.0, 0.0, 0.0), Vector3.ZERO, Vector3(2.0, 2.0, 2.0)).ok == false, "add rejected while locked")
	_check(doc.set_run_state_for_testing("editing"), "test hook sets editing state")
	_check(doc.update_obstacle(object_id, {"position": Vector3(1.0, 1.0, 1.0)}).ok == true, "editing state allows edits")
	_check(doc.set_run_state_for_testing("stopped"), "test hook sets stopped state")
	_check(doc.update_obstacle(object_id, {"position": Vector3(2.0, 2.0, 2.0)}).ok == true, "stopped state allows edits")

func test_random_layout_bounds_reproducible() -> void:
	var doc = DocScript.new()
	for seed_value in [1, 2, 3, 17, 42]:
		var res: Dictionary = doc.randomize_layout(int(seed_value), 12)
		_check(bool(res.get("ok", false)), "randomize accepted for seed %d" % seed_value)
		_check(doc.obstacle_count() == 12, "randomize created 12 objects for seed %d" % seed_value)
		for obstacle in doc.obstacles:
			var kind: String = obstacle.kind
			_check(DocScript.KINDS.has(kind), "random kind registered: " + kind)
			var limits: Array = DocScript.KIND_SIZE_LIMITS[kind]
			var size: Vector3 = obstacle.size
			_check(size.x >= float(limits[0][0]) - 0.000001 and size.x <= float(limits[0][1]) + 0.000001, "size.x within kind range (%s seed %d)" % [kind, seed_value])
			_check(size.y >= float(limits[1][0]) - 0.000001 and size.y <= float(limits[1][1]) + 0.000001, "size.y within kind range (%s seed %d)" % [kind, seed_value])
			_check(size.z >= float(limits[2][0]) - 0.000001 and size.z <= float(limits[2][1]) + 0.000001, "size.z within kind range (%s seed %d)" % [kind, seed_value])
			var half: Vector3 = doc.world_half_extent(size, obstacle.rotation_deg)
			var position: Vector3 = obstacle.position
			_check(abs(position.x) + half.x <= 15.0 + 0.000001, "center+x half extent inside cube (%s seed %d)" % [kind, seed_value])
			_check(abs(position.y) + half.y <= 15.0 + 0.000001, "center+y half extent inside cube (%s seed %d)" % [kind, seed_value])
			_check(abs(position.z) + half.z <= 15.0 + 0.000001, "center+z half extent inside cube (%s seed %d)" % [kind, seed_value])
			_check(obstacle.priority == DocScript.KIND_PRIORITY[kind], "material priority fixed for kind " + kind)
	var doc_a = DocScript.new()
	var doc_b = DocScript.new()
	var doc_c = DocScript.new()
	doc_a.randomize_layout(12345, 8)
	doc_b.randomize_layout(12345, 8)
	doc_c.randomize_layout(999, 8)
	_check(doc_a.commitment_hash() == doc_b.commitment_hash(), "same seed reproduces the identical layout hash")
	_check(doc_a.commitment_hash() != doc_c.commitment_hash(), "different seed produces a different layout hash")
	_check(doc_a.random_seed == 12345, "seed retained (viewer-only post-hoc reproduction record)")
	_check(doc_a.random_record().get("layout_hash", "") == doc_a.commitment_hash(), "random record binds seed and layout hash")

func test_run_bridge_disabled_and_esc_stop() -> void:
	var doc = DocScript.new()
	_check(doc.control_bridge_connected == false, "control authority bridge is 未连接 by default")
	_check(doc.request_run().ok == false, "run stays disabled without the authority/mode bridge")
	_check(doc.request_continue().ok == false, "continue stays disabled without the authority/mode bridge")
	_check(doc.request_pause().ok == false, "pause stays disabled without the authority/mode bridge")
	_check(doc.link_state.source == "未连接", "source label default is 未连接")
	_check(doc.link_state.topology == "未连接", "topology label default is 未连接")
	_check(doc.link_state.baud == "未连接", "baud label default is 未连接")
	_check(doc.link_state.age == "未连接", "data-age label default is 未连接")
	_check(doc.link_state.ai == "未连接", "AI label default is 未连接")
	_check(doc.set_link_state("baud", "9600") == false, "link labels cannot be fabricated without the bridge")
	_check(doc.request_stop("Esc").ok == false, "stop request outside run/pause is rejected")
	var seen: Array = []
	doc.stop_requested.connect(func(source: String) -> void: seen.append(source))
	doc.set_run_state_for_testing("running")
	var stop_res: Dictionary = doc.request_stop("Esc")
	_check(bool(stop_res.get("ok", false)) and bool(stop_res.get("requested", false)), "running stop request emitted")
	_check(stop_res.get("acknowledged", true) == false, "stop request does not fake a board acknowledgement")
	_check(seen.size() == 1 and String(seen[0]) == "Esc", "stop_requested signal carries the source")
	_check(doc.run_state == "running", "state waits for the real authority confirmation")
	_check(doc.is_motion_active() == false, "no fake motion or timeline in the viewer")
	doc.set_run_state_for_testing("paused")
	_check(doc.request_stop("Esc").ok == true, "stop request also valid from paused")

func test_viewer_initial_layout_and_ui_refresh() -> void:
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var shell = scene.shell
	var root_size: Vector2 = shell._root.size
	var left: Rect2 = shell._left_panel.get_global_rect()
	var right: Rect2 = shell._right_panel.get_global_rect()
	var top: Rect2 = shell._top_strip.get_global_rect()
	var bottom: Rect2 = shell._bottom_panel.get_global_rect()
	print("UI_LAYOUT root=%s left=%s right=%s top=%s bottom=%s" % [root_size, left, right, top, bottom])
	_check(right.position.x >= left.end.x, "initial right panel does not cover left toolbar")
	_check(top.position.x >= left.end.x, "initial top bar starts after left toolbar")
	_check(bottom.position.x >= left.end.x and bottom.position.y > top.end.y, "initial timeline placed below central viewport")
	var central_w: float = maxf(0.0, minf(right.position.x, root_size.x) - maxf(left.end.x, 0.0))
	var central_h: float = maxf(0.0, minf(bottom.position.y, root_size.y) - maxf(top.end.y, 0.0))
	var central_ratio := central_w * central_h / maxf(1.0, root_size.x * root_size.y) * 100.0
	print("UI_LAYOUT central_ratio=%.2f%%" % central_ratio)
	_check(central_ratio >= 60.0, "central 3D viewport area is at least 60%% (got %.2f%%)" % central_ratio)
	_check(bool(scene.document.add_obstacle("hard_rock").get("ok", false)), "runtime hard-rock add accepted")
	await process_frame
	_check(not shell._undo_button.disabled, "undo becomes enabled after an edit")
	_check(shell._history_label.text == "撤销 1 / 重做 0", "history label refreshes after an edit (got %s)" % shell._history_label.text)
	_check(shell._redo_button.disabled, "redo stays disabled before any undo")
	_check(bool(scene.document.add_obstacle("water").get("ok", false)), "overlapping water add accepted")
	await process_frame
	_check(shell._overlap_label.text != "无重叠警告", "overlapping edit refreshes the visible warning")
	_check(shell._overlap_label.text.find("重叠") != -1, "overlap label reports the overlap (got %s)" % shell._overlap_label.text)
	shell._on_undo_pressed()
	await process_frame
	_check(shell._history_label.text == "撤销 1 / 重做 1", "undo refreshes the history label (got %s)" % shell._history_label.text)
	_check(not shell._redo_button.disabled, "redo is enabled after one undo")
	_check(shell._overlap_label.text == "无重叠警告", "undo refreshes the overlap warning")
	shell._on_undo_pressed()
	await process_frame
	_check(shell._undo_button.disabled, "undo is disabled again when history is empty")
	_check(shell._history_label.text == "撤销 0 / 重做 2", "history label follows the second undo (got %s)" % shell._history_label.text)
	scene.queue_free()
	await process_frame


func _collect_drill_meshes(node: Node, meshes: Array) -> void:
	# Label3D is an annotation, never a physical mesh in the envelope.
	if node is MeshInstance3D:
		meshes.append(node)
	for child in node.get_children():
		_collect_drill_meshes(child, meshes)


func _measure_drill_mesh(instance: MeshInstance3D, drill: Node3D) -> Dictionary:
	var relative := drill.global_transform.affine_inverse() * instance.global_transform
	var points: Array[Vector3] = []
	var faces: Array = []
	for surface in instance.mesh.get_surface_count():
		var arrays: Array = instance.mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		var start := points.size()
		for vertex in vertices:
			points.append(relative * vertex)
		var count := indices.size() if not indices.is_empty() else vertices.size()
		for offset in range(0, count, 3):
			if offset + 2 >= count:
				break
			var tri: Array[int] = []
			for corner in 3:
				tri.append(start + (indices[offset + corner] if not indices.is_empty() else offset + corner))
			faces.append(tri)
	var minimum := Vector3(INF, INF, INF)
	var maximum := Vector3(-INF, -INF, -INF)
	var max_radius := 0.0
	var max_capsule_distance := 0.0
	var max_pivot_distance := 0.0
	var welded: Dictionary = {}
	var ids: Array[int] = []
	for point in points:
		minimum = minimum.min(point)
		maximum = maximum.max(point)
		var radial := Vector2(point.x, point.y).length()
		max_radius = maxf(max_radius, radial)
		var nearest := Vector3(0.0, 0.0, clampf(point.z, -0.4, 0.4))
		max_capsule_distance = maxf(max_capsule_distance, point.distance_to(nearest))
		max_pivot_distance = maxf(max_pivot_distance, point.length())
		# Weld coincident seam/cap duplicates, preserving 1um geometric resolution.
		var key := Vector3i(roundi(point.x * 1000000.0), roundi(point.y * 1000000.0), roundi(point.z * 1000000.0))
		if not welded.has(key):
			welded[key] = welded.size()
		ids.append(int(welded[key]))
	var edges: Dictionary = {}
	var signed_volume := 0.0
	var triangles := 0
	for tri in faces:
		var a := ids[tri[0]]
		var b := ids[tri[1]]
		var c := ids[tri[2]]
		if a == b or b == c or a == c:
			continue  # Coincident cone apex/centre triangles have zero area.
		triangles += 1
		signed_volume += points[tri[0]].dot(points[tri[1]].cross(points[tri[2]])) / 6.0
		for edge in [[a, b], [b, c], [c, a]]:
			var key := "%d:%d" % [mini(edge[0], edge[1]), maxi(edge[0], edge[1])]
			var record: Array = edges.get(key, [0, 0])
			record[0] += 1
			record[1] += 1 if edge[0] < edge[1] else -1
			edges[key] = record
	var closed := not edges.is_empty()
	for record in edges.values():
		closed = closed and record[0] == 2 and record[1] == 0
	var rear_radius := 0.0
	var front_radius := 0.0
	for point in points:
		if absf(point.z - minimum.z) <= 0.000002:
			rear_radius = maxf(rear_radius, Vector2(point.x, point.y).length())
		if absf(point.z - maximum.z) <= 0.000002:
			front_radius = maxf(front_radius, Vector2(point.x, point.y).length())
	return {"minimum": minimum, "maximum": maximum, "radius": max_radius,
		"capsule_distance": max_capsule_distance, "pivot_distance": max_pivot_distance,
		"closed": closed, "volume": absf(signed_volume), "signed_volume": signed_volume, "triangles": triangles,
		"vertices": points.size(), "rear_radius": rear_radius, "front_radius": front_radius}


func test_greybox_drill_actual_mesh_envelope() -> void:
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	# Exercise the actual retained fallback, with all greybox geometry oracles
	# unchanged. The B drill is tested independently by asset integration tests.
	var integrated: Node3D = scene._drill_root
	integrated.get_parent().remove_child(integrated)
	integrated.free()
	scene._build_drill_greybox()
	var drill: Node3D = scene._drill_root
	_check(drill.global_transform.basis == Basis.IDENTITY, "static greybox world basis has unit scale and no shear/reflection")
	var meshes: Array = []
	_collect_drill_meshes(drill, meshes)
	_check(meshes.size() == 2, "greybox uses exactly two physical solid mesh instances; labels excluded")
	var measurements: Array = []
	var minimum := Vector3(INF, INF, INF)
	var maximum := Vector3(-INF, -INF, -INF)
	var max_radius := 0.0
	var max_capsule_distance := 0.0
	var max_pivot_distance := 0.0
	const TOL := 0.000002  # 2um bound for float32 mesh+transform arithmetic, not gate clearance.
	for mesh in meshes:
		var measured := _measure_drill_mesh(mesh, drill)
		measurements.append(measured)
		minimum = minimum.min(measured.minimum)
		maximum = maximum.max(measured.maximum)
		max_radius = maxf(max_radius, measured.radius)
		max_capsule_distance = maxf(max_capsule_distance, measured.capsule_distance)
		max_pivot_distance = maxf(max_pivot_distance, measured.pivot_distance)
		_check(measured.vertices > 0 and measured.triangles > 0, "actual surface contains vertices and nondegenerate triangles")
		_check(measured.closed, "actual solid mesh is closed with paired opposite oriented edges after 1um seam welding")
		_check(measured.volume > 0.0001, "closed actual mesh encloses nonzero solid volume")
	_check(absf(maximum.z - minimum.z - 0.8) <= TOL, "whole actual mesh length is 0.80m")
	_check(absf(minimum.z + 0.4) <= TOL and absf(maximum.z - 0.4) <= TOL, "whole actual mesh ends at local z=-.4 and +.4")
	_check((minimum + maximum).length() / 2.0 <= TOL, "actual mesh AABB centre coincides with the drill pivot")
	_check(absf(2.0 * max_radius - 0.24) <= TOL, "maximum actual diameter remains 0.24m")
	_check(max_capsule_distance <= 0.12 + TOL, "every transformed vertex lies in default h=.4/r=.12 capsule within numeric tolerance")
	_check(max_pivot_distance <= 0.52 + TOL, "every transformed vertex lies within R_body=.52m")
	measurements.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.maximum.z < b.maximum.z)
	if measurements.size() == 2:
		var body: Dictionary = measurements[0]
		var head: Dictionary = measurements[1]
		_check(absf(body.maximum.z - body.minimum.z - 0.58) <= TOL, "actual body length is .58m")
		_check(absf(head.maximum.z - head.minimum.z - 0.22) <= TOL, "actual conical head length remains .22m")
		_check(absf(body.maximum.z - 0.18) <= TOL and absf(head.minimum.z - 0.18) <= TOL, "actual body/head meet at z=.18 without gap or overlap")
		_check(absf(body.front_radius - 0.12) <= TOL and absf(head.rear_radius - 0.12) <= TOL, "actual seam has matching .12m radius")
		_check(head.front_radius <= TOL and head.rear_radius > 0.12 - TOL, "actual cone narrows to a forward +Z tip")
		_check(body.rear_radius > 0.12 - TOL and body.front_radius > 0.12 - TOL, "actual body retains full-diameter end caps")
		_check(absf(body.volume / (PI * 0.12 * 0.12 * 0.58) - 1.0) < 0.005, "actual closed cylinder volume matches dimensions within polygon discretization")
		_check(absf(head.volume / (PI * 0.12 * 0.12 * 0.22 / 3.0) - 1.0) < 0.005, "actual closed cone volume matches dimensions within polygon discretization")
		_check(body.signed_volume * head.signed_volume > 0.0, "both closed components use consistent surface winding")
	print("GREYBOX_MESH " + JSON.stringify({"minimum": [minimum.x, minimum.y, minimum.z],
		"maximum": [maximum.x, maximum.y, maximum.z], "length_m": maximum.z - minimum.z,
		"diameter_m": 2.0 * max_radius, "max_capsule_distance_m": max_capsule_distance,
		"max_pivot_distance_m": max_pivot_distance, "numeric_tolerance_m": TOL,
		"mesh_measurements": measurements}))
	_check(scene.document.control_bridge_connected == false and not scene.document.is_motion_active(), "mesh fix leaves authority bridge disconnected and motion inactive")
	scene.queue_free()
	await process_frame

func test_viewer_pointer_release_over_panel() -> void:
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var shell = scene.shell
	var to_window: Transform2D = root.get_final_transform()
	var right: Rect2 = shell._right_panel.get_global_rect()
	var window_center: Vector2 = to_window * Vector2(960.0, 540.0)
	var window_panel: Vector2 = to_window * Vector2(right.position.x + 40.0, 500.0)
	var window_return: Vector2 = to_window * Vector2(1100.0, 600.0)
	var warmup := InputEventMouseMotion.new()
	warmup.position = window_center
	root.push_input(warmup)
	await process_frame
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_RIGHT
	press.pressed = true
	press.position = window_center
	root.push_input(press)
	await process_frame
	_check(scene._orbiting, "right-drag starts over the 3D view")
	var motion := InputEventMouseMotion.new()
	motion.position = window_panel
	motion.relative = window_panel - window_center
	motion.button_mask = MOUSE_BUTTON_MASK_RIGHT
	root.push_input(motion)
	await process_frame
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_RIGHT
	release.pressed = false
	release.position = window_panel
	root.push_input(release)
	await process_frame
	_check(not scene._orbiting, "RMB release over the right panel ends the orbit")
	var yaw_hold: float = scene._yaw_deg
	var back := InputEventMouseMotion.new()
	back.position = window_return
	back.relative = window_return - window_panel
	root.push_input(back)
	await process_frame
	_check(is_equal_approx(scene._yaw_deg, yaw_hold), "camera does not keep orbiting after the release over the panel")
	_check(bool(scene.document.add_obstacle("water").get("ok", false)), "water add accepted for the drag case")
	scene.document.select_object(1)
	await process_frame
	var lpress := InputEventMouseButton.new()
	lpress.button_index = MOUSE_BUTTON_LEFT
	lpress.pressed = true
	lpress.position = window_center
	root.push_input(lpress)
	await process_frame
	_check(scene._dragging, "left-drag starts on the object under the pointer")
	var lmotion := InputEventMouseMotion.new()
	lmotion.position = window_panel
	lmotion.relative = window_panel - window_center
	lmotion.button_mask = MOUSE_BUTTON_MASK_LEFT
	root.push_input(lmotion)
	await process_frame
	var lrelease := InputEventMouseButton.new()
	lrelease.button_index = MOUSE_BUTTON_LEFT
	lrelease.pressed = false
	lrelease.position = window_panel
	root.push_input(lrelease)
	await process_frame
	_check(not scene._dragging, "LMB release over the right panel ends the object drag")
	var position_before: Vector3 = scene.document.obstacle_by_id(1).position
	var return_motion := InputEventMouseMotion.new()
	return_motion.position = window_return
	return_motion.relative = window_return - window_panel
	root.push_input(return_motion)
	await process_frame
	_check(scene.document.obstacle_by_id(1).position.is_equal_approx(position_before), "returning motion after the release no longer drags the object")
	scene.queue_free()
	await process_frame

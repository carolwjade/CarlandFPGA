extends SceneTree
## Independent headless matrix for the taskbook G02/G06 36 directed face pairs.
##
## This suite exercises the real staged SceneDocument and the real shell gate
## controls through their OptionButton/SpinBox signals. It is not native OS UI,
## not a continuous motion/CCD test, and not G02/G06 formal acceptance. Expected
## face coordinates and normals below are explicit literals, not derived from
## production helpers or constants.

const DocScript = preload("res://editor/scene_document.gd")
const FACE_ORDER := ["top", "bottom", "front", "back", "left", "right"]
const ENTRY_U := 1.25
const ENTRY_V := -2.5
const EXIT_U := -3.75
const EXIT_V := 4.5

var _checks := 0
var _failures: Array = []
var _rows: Array = []

func _initialize() -> void:
	print("== test_gate_face_pairs (independent 36-row headless matrix) ==")
	print("ENGINE %s" % Engine.get_version_info().string)
	print("DISPLAY_SERVER %s" % DisplayServer.get_name())
	_run("matrix_cardinality", test_matrix_cardinality)
	_run("edge_margin_boundaries", test_edge_margin_boundaries)
	_run("same_face_tangent_and_overlap_negatives", test_same_face_tangent_and_overlap_negatives)
	_run("editor_numeric_tolerance_policy_six_faces", test_editor_numeric_tolerance_policy_six_faces)
	_run("all_36_directed_pairs", test_all_36_directed_pairs)
	_viewer_tests.call_deferred()

func _viewer_tests() -> void:
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var before := _failures.size()
	await test_real_shell_signal_wiring(scene)
	_report_async("real_shell_signal_wiring", before)
	scene.queue_free()
	await process_frame
	await test_all_36_shell_pairs()
	_finish()

func _finish() -> void:
	var same_face := 0
	for row in _rows:
		if bool(row.same_face):
			same_face += 1
	_check(_rows.size() == 36, "machine matrix contains exactly 36 rows")
	_check(same_face == 6, "machine matrix contains exactly six same-face rows")
	print("PAIR_SUMMARY rows=%d same_face=%d cross_face=%d" % [_rows.size(), same_face, _rows.size() - same_face])
	print("PAIR_MATRIX " + JSON.stringify(_rows, "", true, true))
	print("TESTS checks=%d failures=%d" % [_checks, _failures.size()])
	if _failures.is_empty():
		print("RESULT PASS")
		quit(0)
	else:
		for failure in _failures:
			print("FAILURE: " + failure)
		print("RESULT FAIL")
		quit(1)

func _run(name: String, function: Callable) -> void:
	var before := _failures.size()
	function.call()
	if _failures.size() == before:
		print("PASS " + name)
	else:
		print("FAIL " + name)

func _report_async(name: String, before: int) -> void:
	if _failures.size() == before:
		print("PASS " + name)
	else:
		print("FAIL " + name)

func _check(condition: bool, what: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(what)

func test_matrix_cardinality() -> void:
	_check(FACE_ORDER == ["top", "bottom", "front", "back", "left", "right"], "six faces are in the pinned explicit order")
	var seen: Dictionary = {}
	var same_face := 0
	var cross_face := 0
	for entry_face in FACE_ORDER:
		for exit_face in FACE_ORDER:
			var pair_id := "entry_%s__exit_%s" % [entry_face, exit_face]
			_check(not seen.has(pair_id), "directed pair id is unique: " + pair_id)
			seen[pair_id] = true
			if entry_face == exit_face:
				same_face += 1
			else:
				cross_face += 1
	_check(seen.size() == 36, "cartesian matrix has 36 unique ordered pairs")
	_check(same_face == 6, "cartesian matrix has six same-face rows")
	_check(cross_face == 30, "cartesian matrix has 30 cross-face rows")

func test_edge_margin_boundaries() -> void:
	for face in FACE_ORDER:
		var document = DocScript.new()
		var at_edge: Dictionary = document.set_gate("entry", face, 14.85, -14.85)
		_check(bool(at_edge.get("ok", false)), face + " accepts the exact 0.15m edge margin")
		_check(_vec_exact(document.gate_position("entry"), _expected_center(face, 14.85, -14.85)),
			face + " edge position uses the explicit face mapping")
		var before_hash: String = document.commitment_hash()
		var before_gates := _gate_state(document)
		var over_u: Dictionary = document.set_gate("entry", face, 14.850001, -14.85)
		_check(not bool(over_u.get("ok", false)), face + " rejects u beyond the 0.15m edge margin")
		_check(_reason(over_u).find("0.15") != -1, face + " u overrun gives the edge-margin reason")
		var over_v: Dictionary = document.set_gate("entry", face, 14.85, 14.850001)
		_check(not bool(over_v.get("ok", false)), face + " rejects v beyond the 0.15m edge margin")
		_check(_reason(over_v).find("0.15") != -1, face + " v overrun gives the edge-margin reason")
		_check(document.commitment_hash() == before_hash, face + " invalid edges do not mutate the layout hash")
		_check(_gate_state(document) == before_gates, face + " invalid edges preserve both gate dictionaries")

func test_same_face_tangent_and_overlap_negatives() -> void:
	for face in FACE_ORDER:
		var document = DocScript.new()
		_check(bool(document.set_gate("entry", face, ENTRY_U, ENTRY_V).get("ok", false)), face + " same-face entry accepted")
		_check(bool(document.set_gate("exit", face, ENTRY_U + 0.30, ENTRY_V).get("ok", false)),
			face + " exact 0.30m tangent is legal")
		var tangent_id: String = document.commitment_hash()
		var tangent_gates := _gate_state(document)
		var coincident: Dictionary = document.set_gate("exit", face, ENTRY_U, ENTRY_V)
		_check(not bool(coincident.get("ok", false)), face + " coincident same-face circles are rejected")
		_check(_reason(coincident).find("重叠") != -1, face + " coincident rejection has an overlap reason")
		var overlapping: Dictionary = document.set_gate("exit", face, ENTRY_U + 0.299, ENTRY_V)
		_check(not bool(overlapping.get("ok", false)), face + " 0.299m same-face separation is rejected")
		_check(_reason(overlapping).find("0.30") != -1, face + " overlap rejection states the 0.30m threshold")
		_check(document.commitment_hash() == tangent_id, face + " overlap rejections preserve the layout hash")
		_check(_gate_state(document) == tangent_gates, face + " overlap rejections do not auto-move either circle")

func test_editor_numeric_tolerance_policy_six_faces() -> void:
	# These scalar document checks deliberately preserve the editor's 1e-9m
	# tolerance. Python's strict/exact policy rejects both near-boundary cases.
	# Vector3 visualization precision is not an oracle for scalar validity.
	for face in FACE_ORDER:
		var document = DocScript.new()
		_check(bool(document.set_gate("exit", face, -3.75, 4.5).get("ok", false)), face + " policy setup separates exit first")
		_check(bool(document.set_gate("entry", face, 0.0, 0.0).get("ok", false)), face + " policy setup entry accepted")
		var tangent: Dictionary = document.set_gate("exit", face, 0.30, 0.0)
		_check(bool(tangent.get("ok", false)), face + " editor accepts tangent separation 0.30")
		var near_overlap: Dictionary = document.set_gate("exit", face, 0.2999999995, 0.0)
		_check(bool(near_overlap.get("ok", false)), face + " editor 1e-9m tolerance accepts separation 0.2999999995")
		_check(float(document.gates.exit.u) == 0.2999999995, face + " tolerated separation remains unmodified")
		var before_hash: String = document.commitment_hash()
		var before_gates := _gate_state(document)
		var interior: Dictionary = document.set_gate("exit", face, 0.299999, 0.0)
		_check(not bool(interior.get("ok", false)) and _reason(interior).find("重叠") != -1, face + " editor rejects clearly interior separation")
		_check(document.commitment_hash() == before_hash and _gate_state(document) == before_gates, face + " interior rejection preserves accepted near-boundary state")
		var edge: Dictionary = document.set_gate("entry", face, 14.85, 0.0)
		_check(bool(edge.get("ok", false)), face + " editor accepts edge coordinate 14.85")
		var near_edge: Dictionary = document.set_gate("entry", face, 14.8500000005, 0.0)
		_check(bool(near_edge.get("ok", false)), face + " editor 1e-9m tolerance accepts coordinate 14.8500000005")
		_check(float(document.gates.entry.u) == 14.8500000005, face + " tolerated coordinate remains unmodified")
		before_hash = document.commitment_hash()
		before_gates = _gate_state(document)
		var overrun: Dictionary = document.set_gate("entry", face, 14.850001, 0.0)
		_check(not bool(overrun.get("ok", false)) and _reason(overrun).find("0.15") != -1, face + " editor rejects clear edge overrun")
		_check(document.commitment_hash() == before_hash and _gate_state(document) == before_gates, face + " overrun rejection preserves accepted near-boundary state")
		print("EDITOR_POLICY_ROW " + JSON.stringify({"face":face,"policy":"editor_1e-9_m_tolerance","setup_ok":true,"tangent_0.30":tangent.ok,"separation_0.2999999995":near_overlap.ok,"separation_0.299999":interior.ok,"coordinate_14.85":edge.ok,"coordinate_14.8500000005":near_edge.ok,"coordinate_14.850001":overrun.ok}))

func test_all_36_directed_pairs() -> void:
	for entry_face in FACE_ORDER:
		for exit_face in FACE_ORDER:
			var row_index := _rows.size()
			var row_id := "entry_%s__exit_%s" % [entry_face, exit_face]
			var checks_before := _checks
			var failures_before := _failures.size()
			_exercise_pair(row_id, entry_face, exit_face)
			var row := {
				"row": row_index,
				"row_id": row_id,
				"entry_index": FACE_ORDER.find(entry_face),
				"exit_index": FACE_ORDER.find(exit_face),
				"entry_face": entry_face,
				"exit_face": exit_face,
				"entry_role": "entry_blue",
				"exit_role": "exit_red",
				"same_face": entry_face == exit_face,
				"entry_center": _vec(_expected_center(entry_face, ENTRY_U, ENTRY_V)),
				"entry_normal": _vec(_expected_normal(entry_face)),
				"entry_tangent_u": _vec(_expected_tangent(entry_face, "u")),
				"entry_tangent_v": _vec(_expected_tangent(entry_face, "v")),
				"expected_entry_abi_fixture": _expected_abi_fixture(entry_face),
				"exit_center": _vec(_expected_center(exit_face, EXIT_U, EXIT_V)),
				"exit_normal": _vec(_expected_normal(exit_face)),
				"exit_tangent_u": _vec(_expected_tangent(exit_face, "u")),
				"exit_tangent_v": _vec(_expected_tangent(exit_face, "v")),
				"expected_exit_abi_fixture": _expected_abi_fixture(exit_face),
				"abi_evidence": "fixture labels only; actual Gate.abi_face asserted in Python",
				"checks": _checks - checks_before,
				"result": "pass" if _failures.size() == failures_before else "fail",
				"evidence": "raw/godot-adapted/stdout.txt#" + row_id,
			}
			_rows.append(row)
			print("PAIR_ROW " + JSON.stringify(row, "", true, true))

func _exercise_pair(row_id: String, entry_face: String, exit_face: String) -> void:
	var document = DocScript.new()
	var changes := [0]
	document.gates_changed.connect(func() -> void: changes[0] += 1)
	var entry_result: Dictionary = document.set_gate("entry", entry_face, ENTRY_U, ENTRY_V)
	var exit_result: Dictionary = document.set_gate("exit", exit_face, EXIT_U, EXIT_V)
	_check(bool(entry_result.get("ok", false)), row_id + " accepts blue entry")
	_check(bool(exit_result.get("ok", false)), row_id + " accepts red exit")
	_check(bool(entry_result.get("valid", false)) and bool(exit_result.get("valid", false)), row_id + " reports both gates valid")
	_check(entry_result.get("pending_authority", []).size() == 2 and exit_result.get("pending_authority", []).size() == 2,
		row_id + " preserves the two world-authority pending checks")
	_check(bool(document.validate_gates().get("valid", false)), row_id + " combined gate pair validates")
	_check(changes[0] == 2, row_id + " emits exactly two accepted gate-change signals")
	_check(document.gate_label("entry") != document.gate_label("exit"), row_id + " entry and exit roles have distinct labels")
	_check(DocScript.GATE_DIAMETER_M == 0.30 and DocScript.GATE_RADIUS_M == 0.15,
		row_id + " configuration declares a shared 0.30m circle diameter")
	_check(DocScript.MIN_SAME_FACE_SEPARATION_M == 0.30, row_id + " same-face threshold is exactly 0.30m")

	_check(String(document.gates.entry.face) == entry_face, row_id + " entry face is stored")
	_check(String(document.gates.exit.face) == exit_face, row_id + " exit face is stored")
	_check(absf(float(document.gates.entry.u) - ENTRY_U) < 1e-12 and absf(float(document.gates.entry.v) - ENTRY_V) < 1e-12,
		row_id + " entry u/v are unchanged")
	_check(absf(float(document.gates.exit.u) - EXIT_U) < 1e-12 and absf(float(document.gates.exit.v) - EXIT_V) < 1e-12,
		row_id + " exit u/v are unchanged")
	_check(_vec_exact(document.gate_position("entry"), _expected_center(entry_face, ENTRY_U, ENTRY_V)),
		row_id + " blue entry center matches the independent face mapping")
	_check(_vec_exact(document.gate_position("exit"), _expected_center(exit_face, EXIT_U, EXIT_V)),
		row_id + " red exit center matches the independent face mapping")
	_check(_vec_exact(document.gate_normal("entry"), _expected_normal(entry_face)),
		row_id + " blue entry normal matches the independent outward face axis")
	_check(_vec_exact(document.gate_normal("exit"), _expected_normal(exit_face)),
		row_id + " red exit normal matches the independent outward face axis")
	var entry_tangents: Dictionary = document.face_tangents(entry_face)
	var exit_tangents: Dictionary = document.face_tangents(exit_face)
	_check(_vec_exact(entry_tangents.u, _expected_tangent(entry_face, "u"))
		and _vec_exact(entry_tangents.v, _expected_tangent(entry_face, "v")),
		row_id + " blue entry face basis matches explicit u/v tangents")
	_check(_vec_exact(exit_tangents.u, _expected_tangent(exit_face, "u"))
		and _vec_exact(exit_tangents.v, _expected_tangent(exit_face, "v")),
		row_id + " red exit face basis matches explicit u/v tangents")
	_check(_expected_abi_fixture(entry_face) != _expected_abi_fixture(exit_face) or entry_face == exit_face,
		row_id + " expected ABI fixture labels are distinct on cross-face rows; not a production ABI observation")

	var exported: Dictionary = document.export_layout_text()
	_check(bool(exported.get("ok", false)), row_id + " geometry-only export succeeds")
	var imported = DocScript.new()
	var imported_result: Dictionary = imported.apply_layout_text(String(exported.get("text", "")))
	_check(bool(imported_result.get("ok", false)), row_id + " geometry-only import succeeds")
	_check(String(imported_result.get("layout_hash", "")) == document.commitment_hash(),
		row_id + " save/open layout hash is preserved")
	_check(_gate_state(imported) == _gate_state(document), row_id + " save/open preserves both explicit gate faces and centers")
	_check(imported.random_seed == 0 and not imported.seed_known, row_id + " save/open does not reveal or restore a scene seed")
	_check(not imported.control_bridge_connected, row_id + " save/open does not restore control authority")

	var before_hash: String = document.commitment_hash()
	var before_gates := _gate_state(document)
	var before_undo: int = document.undo_depth()
	var entry_overrun: Dictionary = document.set_gate("entry", entry_face, 14.850001, ENTRY_V)
	var exit_overrun: Dictionary = document.set_gate("exit", exit_face, EXIT_U, -14.850001)
	_check(not bool(entry_overrun.get("ok", false)), row_id + " rejects blue entry outside the edge margin")
	_check(not bool(exit_overrun.get("ok", false)), row_id + " rejects red exit outside the edge margin")
	_check(_reason(entry_overrun).find("0.15") != -1 and _reason(exit_overrun).find("0.15") != -1,
		row_id + " invalid edge inputs give readable 0.15m reasons")
	_check(document.commitment_hash() == before_hash, row_id + " invalid inputs preserve the layout hash")
	_check(_gate_state(document) == before_gates, row_id + " invalid inputs preserve both gate positions")
	_check(document.undo_depth() == before_undo, row_id + " invalid inputs add no undo step")

func test_real_shell_signal_wiring(scene) -> void:
	var shell = scene.shell
	var document = scene.document
	_check(shell != null and document != null, "real viewer exposes shell and SceneDocument")
	if shell == null or document == null:
		return
	_check(DisplayServer.get_name() == "headless", "UI-path checks run on the headless display server")

	for face in FACE_ORDER:
		_signal_gate_choice(shell, 0)
		_signal_face_choice(shell, face)
		_signal_spin(shell, "u", ENTRY_U)
		_signal_spin(shell, "v", ENTRY_V)
		_check(String(document.gates.entry.face) == face, "shell signal selects blue entry face " + face)
		_check(_vec_exact(document.gate_position("entry"), _expected_center(face, ENTRY_U, ENTRY_V)),
			"shell signal entry center is explicit for " + face)
		_check(String(shell.active_gate) == "entry", "shell remains on the blue entry role")

	for face in FACE_ORDER:
		_signal_gate_choice(shell, 1)
		_signal_face_choice(shell, face)
		_signal_spin(shell, "u", EXIT_U)
		_signal_spin(shell, "v", EXIT_V)
		_check(String(document.gates.exit.face) == face, "shell signal selects red exit face " + face)
		_check(_vec_exact(document.gate_position("exit"), _expected_center(face, EXIT_U, EXIT_V)),
			"shell signal exit center is explicit for " + face)
		_check(String(shell.active_gate) == "exit", "shell remains on the red exit role")

	_signal_gate_choice(shell, 0)
	_signal_face_choice(shell, "top")
	_signal_spin(shell, "u", ENTRY_U)
	_signal_spin(shell, "v", ENTRY_V)
	_signal_gate_choice(shell, 1)
	_signal_face_choice(shell, "right")
	_signal_spin(shell, "u", EXIT_U)
	_signal_spin(shell, "v", EXIT_V)
	await process_frame
	_check(String(document.gates.entry.face) == "top" and String(document.gates.exit.face) == "right",
		"shell signal path sets a representative top-to-right directed pair")
	_check(_vec_exact(document.gate_position("entry"), Vector3(1.25, 15.0, -2.5)),
		"shell signal entry top center is exact")
	_check(_vec_exact(document.gate_position("exit"), Vector3(15.0, 4.5, -3.75)),
		"shell signal exit right center is exact")
	_check(shell._gate_status_label.text.find("有效") != -1, "shell reports accepted geometry as valid")

	var entry_node: Node3D = scene._gate_root.get_node_or_null("Gate_entry") as Node3D
	var exit_node: Node3D = scene._gate_root.get_node_or_null("Gate_exit") as Node3D
	_check(entry_node != null and exit_node != null, "real viewer builds both gate visuals")
	if entry_node != null and exit_node != null:
		_check(entry_node.position.is_equal_approx(Vector3(1.25, 15.0, -2.5)), "entry visual uses the exact top-face center")
		_check(exit_node.position.is_equal_approx(Vector3(15.0, 4.5, -3.75)), "exit visual uses the exact right-face center")
		var entry_disc := _gate_disc(entry_node)
		var exit_disc := _gate_disc(exit_node)
		_check(entry_disc != null and exit_disc != null, "both gate visuals contain the circle disc")
		if entry_disc != null and exit_disc != null:
			var entry_mesh: CylinderMesh = entry_disc.mesh as CylinderMesh
			var exit_mesh: CylinderMesh = exit_disc.mesh as CylinderMesh
			_check(is_equal_approx(entry_mesh.top_radius, 0.15) and is_equal_approx(entry_mesh.bottom_radius, 0.15),
				"blue entry disc has the explicit 0.15m radius")
			_check(is_equal_approx(exit_mesh.top_radius, 0.15) and is_equal_approx(exit_mesh.bottom_radius, 0.15),
				"red exit disc has the equal 0.15m radius")
			_check(is_equal_approx(entry_mesh.top_radius, exit_mesh.top_radius)
				and is_equal_approx(entry_mesh.bottom_radius, exit_mesh.bottom_radius),
				"entry and exit discs have equal diameters")
			var entry_color: Color = entry_disc.material_override.albedo_color
			var exit_color: Color = exit_disc.material_override.albedo_color
			_check(entry_color.b > entry_color.r, "entry circle material is blue-dominant")
			_check(exit_color.r > exit_color.b, "exit circle material is red-dominant")
		var entry_label := _gate_label(entry_node)
		var exit_label := _gate_label(exit_node)
		_check(entry_label != null and entry_label.text.find("0.30m") != -1, "entry visual labels its 0.30m diameter")
		_check(exit_label != null and exit_label.text.find("0.30m") != -1, "exit visual labels its equal 0.30m diameter")

	_signal_face_choice(shell, "top")
	_signal_spin(shell, "u", ENTRY_U)
	var before_hash: String = document.commitment_hash()
	var before_gates := _gate_state(document)
	var permanent_help_before: String = shell._hint_label.text
	var action_status_before: String = shell._action_status_label.text
	_signal_spin(shell, "v", ENTRY_V)
	_check(bool(document.validate_gates().get("valid", false)),
		"coincident same-face signal edit is rejected and document remains valid")
	_check(document.commitment_hash() == before_hash, "rejected shell overlap edit preserves the layout hash")
	_check(_gate_state(document) == before_gates, "rejected shell overlap edit does not auto-move either circle")
	_check(shell._gate_status_label.text.find("拒绝") != -1, "shell displays the rejection reason")
	# Explicit frozen reviewed-UI interface: current feedback is ActionStatus;
	# Hint remains permanent help. An arbitrary nonempty label cannot pass.
	_check(shell._gate_status_label.text.begins_with("拒绝: "), "rejection label uses the explicit reason prefix")
	var expected_feedback: String = "圈心设置被拒绝，未移动任何圈：" + shell._gate_status_label.text.trim_prefix("拒绝: ")
	_check(shell._action_status_label.text == expected_feedback, "current action status contains the exact rejection and unchanged-circle feedback")
	_check(shell._action_status_label.text != action_status_before, "rejection produces fresh action feedback")
	_check(shell._hint_label.text == permanent_help_before and permanent_help_before == "左键选择 · 右键环绕 · 中键平移 · 滚轮缩放 · 双击聚焦 · R旋转 · S缩放 · Esc 停止请求", "permanent help remains unchanged and distinct from rejection feedback")
	print("REJECTION_FEEDBACK " + JSON.stringify({"action_status_text":shell._action_status_label.text,"gate_status_text":shell._gate_status_label.text,"permanent_help_text":shell._hint_label.text,"action_changed":shell._action_status_label.text != action_status_before}))

	_check(not document.is_motion_active(), "viewer still reports no motion")
	_check(not document.control_bridge_connected, "control bridge remains disconnected")

func test_all_36_shell_pairs() -> void:
	for row in _rows:
		var scene = load("res://viewer/main.tscn").instantiate()
		root.add_child(scene)
		await process_frame
		await process_frame
		var shell = scene.shell
		var document = scene.document
		var before := _failures.size()
		# Fresh viewer per directed pair; set separated u/v before selecting a
		# face so temporary default (0,0) coincidence does not reject the face.
		_signal_gate_choice(shell, 0)
		_signal_spin(shell, "u", ENTRY_U)
		_signal_spin(shell, "v", ENTRY_V)
		_signal_face_choice(shell, String(row.entry_face))
		_signal_gate_choice(shell, 1)
		_signal_spin(shell, "u", EXIT_U)
		_signal_spin(shell, "v", EXIT_V)
		_signal_face_choice(shell, String(row.exit_face))
		await process_frame
		_check(String(document.gates.entry.face) == row.entry_face, row.row_id + " real shell entry selection")
		_check(String(document.gates.exit.face) == row.exit_face, row.row_id + " real shell exit selection")
		_check(shell._gate_status_label.text.find("有效") != -1, row.row_id + " shell gives valid feedback")
		for which in ["entry", "exit"]:
			var face: String = row.entry_face if which == "entry" else row.exit_face
			var u: float = ENTRY_U if which == "entry" else EXIT_U
			var v: float = ENTRY_V if which == "entry" else EXIT_V
			var node: Node3D = scene._gate_root.get_node("Gate_" + which)
			_check(_vec_exact(document.gate_position(which), _expected_center(face, u, v)), row.row_id + " " + which + " document coordinates")
			_check(node.position.is_equal_approx(_expected_center(face, u, v)), row.row_id + " " + which + " visual coordinates")
			_check((node.basis * Vector3.UP).is_equal_approx(_expected_normal(face)), row.row_id + " " + which + " visual outward plane normal")
			var disc := _gate_disc(node)
			_check(disc != null, row.row_id + " " + which + " circle node exists")
			if disc != null:
				var mesh: CylinderMesh = disc.mesh as CylinderMesh
				_check(is_equal_approx(mesh.top_radius, 0.15) and is_equal_approx(mesh.bottom_radius, 0.15), row.row_id + " " + which + " 0.300m disc diameter")
				var color: Color = disc.material_override.albedo_color
				_check(color.b > color.r if which == "entry" else color.r > color.b, row.row_id + " " + which + " blue/red role material")
		if bool(row.same_face):
			_signal_spin(shell, "u", ENTRY_U)
			var before_hash: String = document.commitment_hash()
			var before_gates := _gate_state(document)
			_signal_spin(shell, "v", ENTRY_V)
			_check(document.commitment_hash() == before_hash and _gate_state(document) == before_gates, row.row_id + " same-face shell overlap preserves both gates")
			_check(shell._gate_status_label.text.find("拒绝") != -1, row.row_id + " same-face shell overlap gives rejection")
		row["headless_signal_result"] = "pass" if _failures.size() == before else "fail"
		row["headless_signal_evidence"] = "raw/godot-adapted/stdout.txt#UI_PAIR_ROW:" + row.row_id
		row["native_os_mouse"] = "not_run"
		print("UI_PAIR_ROW " + JSON.stringify({"row_id": row.row_id, "result": row.headless_signal_result, "same_face_overlap_rejection": bool(row.same_face)}))
		scene.queue_free()
		await process_frame

func _signal_gate_choice(shell, index: int) -> void:
	shell._which_option.select(index)
	shell._which_option.item_selected.emit(index)

func _signal_face_choice(shell, face: String) -> void:
	var index: int = FACE_ORDER.find(face)
	shell._face_option.select(index)
	shell._face_option.item_selected.emit(index)

func _signal_spin(shell, field: String, value: float) -> void:
	if field == "u":
		shell._gate_u.set_value_no_signal(value)
		shell._gate_u.value_changed.emit(value)
	else:
		shell._gate_v.set_value_no_signal(value)
		shell._gate_v.value_changed.emit(value)

func _gate_disc(node: Node3D) -> MeshInstance3D:
	for child in node.get_children():
		if child is MeshInstance3D and child.mesh is CylinderMesh:
			var mesh: CylinderMesh = child.mesh
			if mesh.top_radius > 0.1:
				return child
	return null

func _gate_label(node: Node3D) -> Label3D:
	for child in node.get_children():
		if child is Label3D:
			return child
	return null

func _gate_state(document) -> String:
	return JSON.stringify(document.gates, "", true, true)

func _reason(result: Dictionary) -> String:
	if result.has("reason"):
		return String(result.reason)
	return "; ".join(result.get("errors", []))

func _vec(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func _vec_exact(actual: Vector3, expected: Vector3) -> bool:
	return absf(actual.x - expected.x) <= 1e-12 and absf(actual.y - expected.y) <= 1e-12 and absf(actual.z - expected.z) <= 1e-12

func _expected_center(face: String, u: float, v: float) -> Vector3:
	match face:
		"top":
			return Vector3(u, 15.0, v)
		"bottom":
			return Vector3(u, -15.0, v)
		"front":
			return Vector3(u, v, 15.0)
		"back":
			return Vector3(u, v, -15.0)
		"right":
			return Vector3(15.0, v, u)
		"left":
			return Vector3(-15.0, v, u)
		_:
			return Vector3(999.0, 999.0, 999.0)

func _expected_normal(face: String) -> Vector3:
	match face:
		"top":
			return Vector3(0.0, 1.0, 0.0)
		"bottom":
			return Vector3(0.0, -1.0, 0.0)
		"front":
			return Vector3(0.0, 0.0, 1.0)
		"back":
			return Vector3(0.0, 0.0, -1.0)
		"right":
			return Vector3(1.0, 0.0, 0.0)
		"left":
			return Vector3(-1.0, 0.0, 0.0)
		_:
			return Vector3.ZERO

func _expected_tangent(face: String, axis: String) -> Vector3:
	match face:
		"top", "bottom":
			return Vector3(1.0, 0.0, 0.0) if axis == "u" else Vector3(0.0, 0.0, 1.0)
		"front", "back":
			return Vector3(1.0, 0.0, 0.0) if axis == "u" else Vector3(0.0, 1.0, 0.0)
		"right", "left":
			return Vector3(0.0, 0.0, 1.0) if axis == "u" else Vector3(0.0, 1.0, 0.0)
		_:
			return Vector3.ZERO

func _expected_abi_fixture(face: String) -> String:
	match face:
		"top":
			return "+Y"
		"bottom":
			return "-Y"
		"front":
			return "+Z"
		"back":
			return "-Z"
		"right":
			return "+X"
		"left":
			return "-X"
		_:
			return "?"

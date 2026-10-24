extends SceneTree
## G02 private layout persistence: strict codec, bounded file I/O, transactional
## document replacement, and the existing viewer/UI refresh path.
##
## Headless only. This is not native UI, OS isolation, physics, controller or G02
## formal acceptance. Run from the simulator project:
##   godot --headless --path . --script res://tests/test_layout_persistence.gd

const DocScript = preload("res://editor/scene_document.gd")
const CODEC_PATH := "res://editor/layout_codec.gd"
const STORE_PATH := "res://editor/layout_store.gd"
const SCENE_PATH := "res://viewer/main.tscn"
const MAX_FILE_BYTES := 1048576
const MAX_OBJECTS := 30
const CONTRACT_ID := "DEEPEYE-HUMAN-LOCK-20261014/revision1"
const REQUIREMENTS_SHA256 := "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"

var _checks := 0
var _failures: Array = []
var _codec_script = null
var _store_script = null
var _test_dir := ""
var _persistence_ready := false

func _initialize() -> void:
	print("== test_layout_persistence (G02 headless) ==")
	_codec_script = load(CODEC_PATH)
	_store_script = load(STORE_PATH)
	_check(_codec_script != null, "layout codec script exists")
	_check(_store_script != null, "layout store script exists")
	_test_dir = OS.get_user_data_dir().path_join("layout-persistence-tests-%d" % Time.get_ticks_usec())
	_check(DirAccess.make_dir_recursive_absolute(_test_dir) == OK, "isolated test directory created")
	if _codec_script != null:
		_run("codec_strict_schema_and_limits", test_codec_strict_schema_and_limits)
	if _codec_script != null and _store_script != null:
		_run("store_bounds_and_save_as", test_store_bounds_and_save_as)
	if _codec_script != null:
		_run("gate_face_pair_combinations", test_gate_face_pair_combinations)
	_scene_tests.call_deferred()

func _scene_tests() -> void:
	var scene = load(SCENE_PATH).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var shell = scene.shell
	var document = scene.document
	_check(document != null, "real viewer document exists")
	_check(shell != null, "real shell exists")
	_check(_has_member(shell, "_save_button"), "Shell has a save-layout button")
	_check(_has_member(shell, "_open_button"), "Shell has an open-layout button")
	_check(_has_member(shell, "_file_dialog"), "Shell owns an explicit FileDialog")
	_check(_has_member(shell, "_layout_store"), "Shell owns the bounded layout store")
	_check(_has_member(shell, "_layout_source_label"), "Shell displays layout source/seed provenance")
	_check(document.has_method("export_layout_text"), "SceneDocument exposes versioned export")
	_check(document.has_method("apply_layout_text"), "SceneDocument exposes transactional import")
	_check(shell.has_method("_on_file_selected"), "Shell has the real file_selected handler")
	_check(shell.has_method("_on_file_dialog_canceled"), "Shell has the real cancel handler")
	_persistence_ready = (_codec_script != null and _store_script != null
		and document.has_method("export_layout_text") and document.has_method("apply_layout_text")
		and _has_member(shell, "_save_button") and _has_member(shell, "_open_button")
		and _has_member(shell, "_file_dialog") and _has_member(shell, "_layout_store"))
	if _persistence_ready:
		var before := _failures.size()
		await test_scene_roundtrip_and_viewer()
		_report_async("scene_roundtrip_and_viewer", before)
		before = _failures.size()
		await test_transactional_rejections()
		_report_async("transactional_rejections", before)
		before = _failures.size()
		await test_state_gating_and_cancel()
		_report_async("state_gating_and_cancel", before)
		before = _failures.size()
		await test_save_as_failures()
		_report_async("save_as_failures", before)
	else:
		print("SKIP persistence runtime tests until the selected six-file feature exists")
	scene.queue_free()
	await process_frame
	_finish()

func _finish() -> void:
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

func _has_member(target: Object, member_name: String) -> bool:
	for property in target.get_property_list():
		if String(property.name) == member_name:
			return true
	return false

func _build_valid_document():
	var document = DocScript.new()
	var definitions := [
		["water", Vector3(-6.0, -6.0, 0.0), Vector3.ZERO, Vector3(6.0, 4.0, 2.0)],
		["hard_rock", Vector3(4.0, 0.0, 0.0), Vector3(0.0, 30.0, 0.0), Vector3(3.0, 3.0, 3.0)],
		["fault", Vector3(0.0, 5.0, -5.0), Vector3.ZERO, Vector3(8.0, 1.0, 6.0)],
		["void", Vector3(6.0, 6.0, 6.0), Vector3(0.0, 0.0, 15.0), Vector3(4.0, 3.0, 3.0)],
		["casing", Vector3(-2.0, -2.0, 7.0), Vector3.ZERO, Vector3(0.8, 0.8, 8.0)],
	]
	for definition in definitions:
		var result: Dictionary = document.add_obstacle(definition[0], definition[1], definition[2], definition[3])
		_check(bool(result.get("ok", false)), "valid fixture object accepted")
	var entry_result: Dictionary = document.set_gate("entry", "top", 1.25, -2.5)
	var exit_result: Dictionary = document.set_gate("exit", "right", 3.5, 2.0)
	_check(bool(entry_result.get("ok", false)), "valid fixture entry gate accepted")
	_check(bool(exit_result.get("ok", false)), "valid fixture exit gate accepted")
	return document

func _parse_object(text: String) -> Dictionary:
	var value = JSON.parse_string(text)
	_check(value is Dictionary, "test fixture is a JSON object")
	return value if value is Dictionary else {}

func _stringify(data: Dictionary) -> String:
	return JSON.stringify(data, "", true, true)

func _decode(text: String) -> Dictionary:
	return _codec_script.decode(text)

func _reason(result: Dictionary) -> String:
	if result.has("reason"):
		return String(result.reason)
	return "; ".join(result.get("errors", []))

func _expect_reject(text: String, needle: String, label: String) -> void:
	var result := _decode(text)
	_check(not bool(result.get("ok", false)), label + " is rejected")
	var reason := _reason(result)
	_check(reason.find(needle) != -1, label + " reason mentions " + needle + " (got " + reason + ")")
	_check(reason.length() <= 512, label + " reason is bounded")
func test_codec_strict_schema_and_limits() -> void:
	var document = _build_valid_document()
	var exported: Dictionary = document.export_layout_text()
	_check(bool(exported.get("ok", false)), "document export succeeds")
	if not bool(exported.get("ok", false)):
		return
	var text := String(exported.text)
	var decoded := _decode(text)
	_check(bool(decoded.get("ok", false)), "valid file decodes")
	_check(String(decoded.get("layout_hash", "")) == document.commitment_hash(), "file hash equals document commitment hash")
	_check(decoded.get("obstacles", []).size() == 5, "all five object kinds survive decode")
	_check(String(decoded.get("gates", {}).get("entry", {}).get("face", "")) == "top", "entry face survives decode")
	_check(String(decoded.get("gates", {}).get("exit", {}).get("face", "")) == "right", "exit face survives decode")
	var parsed := _parse_object(text)
	_check(typeof(parsed.get("schema")) == TYPE_FLOAT, "Godot 4.7.2 parses JSON numbers as float")
	_check(typeof(JSON.parse_string("1")) == TYPE_FLOAT and JSON.parse_string("1") == 1.0, "integer JSON literal is an exact float")
	_check(int(parsed.get("schema")) == 1, "schema is version 1")
	_check(String(parsed.get("contract")) == CONTRACT_ID, "contract id is pinned")
	_check(String(parsed.get("requirements_sha256")) == REQUIREMENTS_SHA256, "requirements hash is pinned")
	_check(String(parsed.get("units")) == "m", "units are metres")
	for forbidden in ["run_state", "control_bridge_connected", "link_state", "random_seed", "seed_known",
			"layout_origin", "route", "asset_path", "model", "boot", "ai_lease", "sensor", "control"]:
		_check(text.find("\"" + forbidden + "\"") == -1, "saved file excludes forbidden field " + forbidden)

	var empty_document = DocScript.new()
	var empty_export: Dictionary = empty_document.export_layout_text()
	_check(bool(empty_export.get("ok", false)), "empty layout exports")
	var empty_decoded := _decode(String(empty_export.get("text", "")))
	_check(bool(empty_decoded.get("ok", false)) and empty_decoded.get("obstacles", []).is_empty(), "empty layout round-trips")

	var max_document = DocScript.new()
	for index in MAX_OBJECTS:
		var position := Vector3(-10.0 + float(index % 5) * 4.0, 0.0, -10.0 + float(index / 5) * 4.0)
		_check(bool(max_document.add_obstacle("hard_rock", position, Vector3.ZERO, Vector3.ONE).get("ok", false)), "30-object fixture add")
	var max_export: Dictionary = max_document.export_layout_text()
	var max_decoded := _decode(String(max_export.get("text", "")))
	_check(bool(max_decoded.get("ok", false)) and max_decoded.get("obstacles", []).size() == MAX_OBJECTS, "30 objects accepted")
	var thirty_one := _parse_object(String(max_export.get("text", "")))
	var extra_obstacle: Dictionary = thirty_one.layout.obstacles[0].duplicate(true)
	extra_obstacle["object_id"] = 31.0
	thirty_one.layout.obstacles.append(extra_obstacle)
	_expect_reject(_stringify(thirty_one), "30", "31 objects")

	var bad_schema := _parse_object(text)
	bad_schema["schema"] = 2
	_expect_reject(_stringify(bad_schema), "schema", "unknown schema")
	var bad_contract := _parse_object(text)
	bad_contract["contract"] = "other"
	_expect_reject(_stringify(bad_contract), "contract", "wrong contract")
	var bad_requirements := _parse_object(text)
	bad_requirements["requirements_sha256"] = "0".repeat(64)
	_expect_reject(_stringify(bad_requirements), "requirements_sha256", "wrong requirements hash")
	var bad_units := _parse_object(text)
	bad_units["units"] = "mm"
	_expect_reject(_stringify(bad_units), "units", "wrong units")
	var missing_contract := _parse_object(text)
	missing_contract.erase("contract")
	_expect_reject(_stringify(missing_contract), "contract", "missing contract")
	var extra_top := _parse_object(text)
	extra_top["run_state"] = "running"
	_expect_reject(_stringify(extra_top), "run_state", "forged run state")
	var extra_layout := _parse_object(text)
	extra_layout.layout["route"] = [[0, 0, 0]]
	_expect_reject(_stringify(extra_layout), "route", "forged layout route")
	var extra_object := _parse_object(text)
	extra_object.layout.obstacles[0]["asset_path"] = "res://truth.glb"
	_expect_reject(_stringify(extra_object), "asset_path", "forged object asset")
	var extra_gate := _parse_object(text)
	extra_gate.layout.gates.entry["sensor_truth"] = true
	_expect_reject(_stringify(extra_gate), "sensor_truth", "forged gate truth")
	var missing_object_key := _parse_object(text)
	missing_object_key.layout.obstacles[0].erase("rotation_deg")
	_expect_reject(_stringify(missing_object_key), "rotation_deg", "missing object field")

	var bad_id_fraction := _parse_object(text)
	bad_id_fraction.layout.obstacles[0]["object_id"] = 1.5
	_expect_reject(_stringify(bad_id_fraction), "object_id", "fractional id")
	var bad_id_string := _parse_object(text)
	bad_id_string.layout.obstacles[0]["object_id"] = "1"
	_expect_reject(_stringify(bad_id_string), "object_id", "string id")
	var bad_id_bool := _parse_object(text)
	bad_id_bool.layout.obstacles[0]["object_id"] = true
	_expect_reject(_stringify(bad_id_bool), "object_id", "boolean id")
	var bad_id_huge := _parse_object(text)
	bad_id_huge.layout.obstacles[0]["object_id"] = 9007199254740992.0
	_expect_reject(_stringify(bad_id_huge), "object_id", "unsafe huge id")
	var duplicate_id := _parse_object(text)
	duplicate_id.layout.obstacles[1]["object_id"] = duplicate_id.layout.obstacles[0]["object_id"]
	_expect_reject(_stringify(duplicate_id), "object_id", "duplicate id")
	var bad_kind := _parse_object(text)
	bad_kind.layout.obstacles[0]["kind"] = "script"
	_expect_reject(_stringify(bad_kind), "kind", "unknown kind")
	var bad_priority := _parse_object(text)
	bad_priority.layout.obstacles[0]["priority"] = 99
	_expect_reject(_stringify(bad_priority), "priority", "invalid priority")
	var bool_number := _parse_object(text)
	bool_number.layout.obstacles[0].position.x = true
	_expect_reject(_stringify(bool_number), "position.x", "boolean coordinate")
	var size_low := _parse_object(text)
	size_low.layout.obstacles[0].size.x = 2.99
	_expect_reject(_stringify(size_low), "尺寸", "size below kind range")
	var size_high := _parse_object(text)
	size_high.layout.obstacles[0].size.x = 10.01
	_expect_reject(_stringify(size_high), "尺寸", "size above kind range")
	var position_out := _parse_object(text)
	position_out.layout.obstacles[0].position.x = 15.1
	_expect_reject(_stringify(position_out), "位置", "position outside cube")
	var gate_margin := _parse_object(text)
	gate_margin.layout.gates.entry.u = 14.86
	_expect_reject(_stringify(gate_margin), "0.15", "gate edge-margin violation")
	var gate_overlap := _parse_object(text)
	gate_overlap.layout.gates.exit.face = "top"
	gate_overlap.layout.gates.exit.u = 1.25
	gate_overlap.layout.gates.exit.v = -2.5
	_expect_reject(_stringify(gate_overlap), "重叠", "same-face gate overlap")
	var wrong_hash := _parse_object(text)
	wrong_hash["layout_hash"] = "0".repeat(64)
	_expect_reject(_stringify(wrong_hash), "layout_hash", "wrong layout hash")
	var upper_hash := _parse_object(text)
	upper_hash["layout_hash"] = String(upper_hash.layout_hash).to_upper()
	_expect_reject(_stringify(upper_hash), "layout_hash", "uppercase layout hash")
	_expect_reject("{\"schema\":", "JSON", "truncated JSON")
	_expect_reject("{\"value\":NaN}", "JSON", "NaN literal")
	var infinity_data := _parse_object(text)
	infinity_data.layout.obstacles[0].size.x = INF
	_expect_reject(_stringify(infinity_data), "有限", "infinite number")
	_expect_reject("[".repeat(40) + "0" + "]".repeat(40), "嵌套", "excessive nesting")
	_expect_reject("{\"padding\":\"" + "a".repeat(MAX_FILE_BYTES) + "\"}", "1 MiB", "oversized text")
func test_store_bounds_and_save_as() -> void:
	var store = _store_script.new()
	var default_dir := String(store.default_layout_dir())
	_check(default_dir.begins_with(OS.get_user_data_dir()), "default layout directory is viewer-private user data")
	var relative_result: Dictionary = store.save_new("relative.json", "{}")
	_check(not bool(relative_result.get("ok", false)), "relative save path is rejected")
	var relative_read: Dictionary = store.read_text("relative.json")
	_check(not bool(relative_read.get("ok", false)), "relative read path is rejected")

	var existing_path := _path("existing.json")
	_write_text(existing_path, "ORIGINAL")
	var existing_result: Dictionary = store.save_new(existing_path, "REPLACEMENT")
	_check(not bool(existing_result.get("ok", false)) and String(existing_result.get("code", "")) == "already_exists", "Save As refuses an existing target")
	_check(_read_text(existing_path) == "ORIGINAL", "existing target bytes stay unchanged")

	var new_path := _path("new/layout.json")
	var new_result: Dictionary = store.save_new(new_path, "{\"ok\":true}\n")
	_check(bool(new_result.get("ok", false)), "Save As creates a new file and parent directory")
	_check(_read_text(new_path) == "{\"ok\":true}\n", "new file re-read matches")
	var reread: Dictionary = store.read_text(new_path)
	_check(bool(reread.get("ok", false)) and String(reread.get("text", "")) == "{\"ok\":true}\n", "bounded read returns exact text")

	var invalid_utf8_path := _path("invalid-utf8.json")
	_write_bytes(invalid_utf8_path, PackedByteArray([0x7b, 0x22, 0x78, 0x22, 0x3a, 0x22, 0xff, 0x22, 0x7d]))
	var invalid_utf8: Dictionary = store.read_text(invalid_utf8_path)
	_check(not bool(invalid_utf8.get("ok", false)) and String(invalid_utf8.get("code", "")) == "invalid_utf8", "invalid UTF-8 is rejected")

	var oversized_path := _path("oversized.json")
	var oversized_bytes := PackedByteArray()
	oversized_bytes.resize(MAX_FILE_BYTES + 1)
	oversized_bytes.fill(0x78)
	_write_bytes(oversized_path, oversized_bytes)
	var oversized: Dictionary = store.read_text(oversized_path)
	_check(not bool(oversized.get("ok", false)) and String(oversized.get("code", "")) == "too_large", "oversized file is rejected before allocation")

	var blocker_path := _path("blocker")
	_write_text(blocker_path, "not a directory")
	var blocked_target := blocker_path.path_join("layout.json")
	var blocked_result: Dictionary = store.save_new(blocked_target, "{}")
	_check(not bool(blocked_result.get("ok", false)), "write into a non-directory parent fails")
	_check(not FileAccess.file_exists(blocked_target), "failed write publishes no target")

func test_gate_face_pair_combinations() -> void:
	var faces := ["top", "bottom", "front", "back", "left", "right"]
	var accepted := 0
	for entry_face in faces:
		for exit_face in faces:
			var source = DocScript.new()
			source.add_obstacle("hard_rock", Vector3.ZERO, Vector3.ZERO, Vector3(3.0, 3.0, 3.0))
			var helper_face: String = "top" if entry_face != "top" else "bottom"
			_check(bool(source.set_gate("exit", helper_face, 0.0, 0.0).get("ok", false)), "helper gate accepted")
			_check(bool(source.set_gate("entry", entry_face, 0.0, 0.0).get("ok", false)), "entry face accepted " + entry_face)
			var separation := 0.5 if entry_face == exit_face else 0.0
			_check(bool(source.set_gate("exit", exit_face, separation, 0.0).get("ok", false)), "exit face accepted " + exit_face)
			var exported: Dictionary = source.export_layout_text()
			var target = DocScript.new()
			var applied: Dictionary = target.apply_layout_text(String(exported.get("text", "")))
			if bool(applied.get("ok", false)):
				accepted += 1
			_check(bool(applied.get("ok", false)), "face pair %s->%s applies" % [entry_face, exit_face])
			_check(String(target.gates.entry.face) == entry_face and String(target.gates.exit.face) == exit_face,
				"face pair %s->%s preserves faces" % [entry_face, exit_face])
	_check(accepted == 36, "all 36 directed face pairs accepted (got %d)" % accepted)
	var same_face_source = DocScript.new()
	same_face_source.set_gate("entry", "top", 0.0, 0.0)
	same_face_source.set_gate("exit", "top", 0.5, 0.0)
	var same_face_export: Dictionary = same_face_source.export_layout_text()
	var too_close := _parse_object(String(same_face_export.get("text", "")))
	too_close.layout.gates.exit.u = 0.29
	_expect_reject(_stringify(too_close), "0.30", "same-face separation below 0.30")
func test_scene_roundtrip_and_viewer() -> void:
	var scene = load(SCENE_PATH).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var document = scene.document
	var shell = scene.shell
	for definition in [
		["water", Vector3(-6.0, -6.0, 0.0), Vector3.ZERO, Vector3(6.0, 4.0, 2.0)],
		["hard_rock", Vector3(4.0, 0.0, 0.0), Vector3(0.0, 30.0, 0.0), Vector3(3.0, 3.0, 3.0)],
		["fault", Vector3(0.0, 5.0, -5.0), Vector3.ZERO, Vector3(8.0, 1.0, 6.0)],
		["void", Vector3(6.0, 6.0, 6.0), Vector3(0.0, 0.0, 15.0), Vector3(4.0, 3.0, 3.0)],
		["casing", Vector3(-2.0, -2.0, 7.0), Vector3.ZERO, Vector3(0.8, 0.8, 8.0)],
	]:
		_check(bool(document.add_obstacle(definition[0], definition[1], definition[2], definition[3]).get("ok", false)), "scene fixture add")
	document.set_gate("entry", "top", 1.25, -2.5)
	document.set_gate("exit", "right", 3.5, 2.0)
	await process_frame
	var expected_hash := document.commitment_hash()
	var source_before := String(document.layout_origin)
	var seed_known_before: bool = document.seed_known
	var save_path := _path("scene-roundtrip.json")
	_select_dialog_action(shell, "save")
	shell._on_file_selected(save_path)
	await process_frame
	_check(bool(shell.last_file_result.get("ok", false)), "Save As through Shell handler succeeds")
	_check(FileAccess.file_exists(save_path), "Save As creates the selected file")
	_check(document.commitment_hash() == expected_hash, "Save As does not mutate document geometry")
	_check(String(document.layout_origin) == source_before and bool(document.seed_known) == seed_known_before, "Save As does not change seed provenance")
	var saved_text := _read_text(save_path)
	_check(saved_text.find("\"run_state\"") == -1 and saved_text.find("\"control_bridge_connected\"") == -1, "saved file excludes runtime/control state")

	document.randomize_layout(77, 7)
	document.select_object(int(document.obstacles[0].object_id))
	await process_frame
	_check(document.seed_known and document.random_seed == 77, "random generation records its real seed")
	_check(document.undo_depth() > 0, "mutated scene has prior history before open")
	var camera_before: Transform3D = scene._camera.global_transform
	var drill_before: Transform3D = scene._drill_root.global_transform
	_select_dialog_action(shell, "open")
	shell._on_file_selected(save_path)
	await process_frame
	await process_frame
	_check(bool(shell.last_file_result.get("ok", false)), "Open through Shell handler succeeds")
	_check(scene.document == document, "Open keeps the original SceneDocument instance")
	_check(document.commitment_hash() == expected_hash, "reopened commitment hash equals saved hash")
	_check(document.obstacle_count() == 5, "reopened object count equals saved count")
	_check(document.selected_id == -1, "successful Open clears selection")
	_check(document.undo_depth() == 0 and document.redo_depth() == 0, "successful Open clears undo/redo history")
	_check(not document.seed_known, "file layout reports an unknown seed")
	_check(String(document.layout_origin).find("文件布局") != -1, "file layout source is recorded")
	_check(shell._layout_source_label.text.find("文件布局") != -1 and shell._layout_source_label.text.find("未知") != -1,
		"UI shows file source and unknown seed")
	_check(document.control_bridge_connected == false, "Open leaves control bridge disconnected")
	_check(document.link_state.source == "未连接" and document.link_state.topology == "未连接", "Open leaves link labels unchanged")
	_check(shell._run_button.disabled and shell._pause_button.disabled and shell._continue_button.disabled, "Run/pause/continue stay disabled")
	_check(scene._camera.global_transform.is_equal_approx(camera_before), "Open does not move the camera")
	_check(scene._drill_root.global_transform.is_equal_approx(drill_before) and not document.is_motion_active(), "Open does not move the static drill or fake motion")
	_check_viewer_matches(document, scene, "successful Open")
	var reloaded_file: Dictionary = document.export_layout_text()
	_check(bool(reloaded_file.get("ok", false)) and _decode(String(reloaded_file.get("text", ""))).get("layout_hash", "") == expected_hash,
		"re-export after Open preserves the same commitment")
	scene.queue_free()
	await process_frame
func test_transactional_rejections() -> void:
	var scene = load(SCENE_PATH).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var document = scene.document
	var shell = scene.shell
	document.add_obstacle("water", Vector3(-4.0, -4.0, 0.0), Vector3.ZERO, Vector3(6.0, 4.0, 2.0))
	document.set_gate("entry", "front", 1.0, 1.0)
	document.set_gate("exit", "back", -1.0, 1.0)
	var valid_export: Dictionary = document.export_layout_text()
	var valid_path := _path("transaction-valid.json")
	_write_text(valid_path, String(valid_export.get("text", "")))
	_select_dialog_action(shell, "open")
	shell._on_file_selected(valid_path)
	await process_frame
	_check(bool(shell.last_file_result.get("ok", false)), "transaction fixture opens")
	document.add_obstacle("void", Vector3(3.0, 3.0, 3.0), Vector3.ZERO, Vector3(2.0, 2.0, 2.0))
	document.select_object(int(document.obstacles[1].object_id))
	await process_frame
	var baseline := _document_state(document)
	var viewer_baseline := _viewer_state(scene)
	var label_baseline := String(shell._layout_source_label.text)
	var valid_text := _read_text(valid_path)
	var cases: Array = []
	cases.append(["truncated", "{\"schema\":", "JSON"])
	cases.append(["invalid-utf8", PackedByteArray([0x7b, 0x22, 0xff, 0x22, 0x7d]), "UTF-8"])
	var oversized := PackedByteArray()
	oversized.resize(MAX_FILE_BYTES + 1)
	oversized.fill(0x78)
	cases.append(["oversized", oversized, "1 MiB"])
	var forged := _parse_object(valid_text)
	forged["control_bridge_connected"] = true
	cases.append(["forged-control", _stringify(forged), "control_bridge_connected"])
	var duplicate := _parse_object(valid_text)
	duplicate.layout.obstacles[1]["object_id"] = duplicate.layout.obstacles[0]["object_id"]
	cases.append(["duplicate-id", _stringify(duplicate), "object_id"])
	var overlap := _parse_object(valid_text)
	overlap.layout.gates.exit.face = "front"
	overlap.layout.gates.exit.u = 1.0
	overlap.layout.gates.exit.v = 1.0
	cases.append(["gate-overlap", _stringify(overlap), "重叠"])
	var bad_hash := _parse_object(valid_text)
	bad_hash["layout_hash"] = "f".repeat(64)
	cases.append(["bad-hash", _stringify(bad_hash), "layout_hash"])
	for test_case in cases:
		var case_path := _path("reject-%s.json" % String(test_case[0]))
		if test_case[1] is PackedByteArray:
			_write_bytes(case_path, test_case[1])
		else:
			_write_text(case_path, String(test_case[1]))
		_select_dialog_action(shell, "open")
		shell._on_file_selected(case_path)
		await process_frame
		_check(not bool(shell.last_file_result.get("ok", false)), "reject case %s fails" % test_case[0])
		_check(_reason(shell.last_file_result).find(String(test_case[2])) != -1,
			"reject case %s has bounded reason mentioning %s (got %s)" % [test_case[0], test_case[2], _reason(shell.last_file_result)])
		_check(_reason(shell.last_file_result).length() <= 512, "reject case %s reason is bounded" % test_case[0])
		_check(_document_state(document) == baseline, "reject case %s preserves document/history/selection/run/link state" % test_case[0])
		_check(_viewer_state(scene) == viewer_baseline, "reject case %s preserves viewer nodes/transforms" % test_case[0])
		_check(String(shell._layout_source_label.text) == label_baseline, "reject case %s preserves source label" % test_case[0])

	document.randomize_layout(55, 4)
	await process_frame
	_check(document.seed_known and document.random_seed == 55, "failure sequence can be preceded by a real random seed")
	var random_state := _document_state(document)
	_select_dialog_action(shell, "open")
	shell._on_file_selected(_path("transaction-valid.json").path_join("bad-parent.json"))
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)), "missing file open fails")
	_check(_document_state(document) == random_state, "failed open preserves prior real seed provenance")
	_check(document.undo().get("ok", false), "undo works after a real random generation")
	_check(document.layout_origin.find("文件布局") != -1 and not document.seed_known, "undo does not inherit a stale random seed")
	_check(document.redo().get("ok", false), "redo works after provenance check")
	_check(document.layout_origin == "随机布局" and document.seed_known and document.random_seed == 55, "redo restores the matching real seed provenance")
	scene.queue_free()
	await process_frame
func test_state_gating_and_cancel() -> void:
	var scene = load(SCENE_PATH).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var document = scene.document
	var shell = scene.shell
	document.add_obstacle("hard_rock", Vector3.ZERO, Vector3.ZERO, Vector3(3.0, 3.0, 3.0))
	var exported: Dictionary = document.export_layout_text()
	var valid_path := _path("state-gate-valid.json")
	_write_text(valid_path, String(exported.get("text", "")))
	for state in ["locked", "running", "paused"]:
		document.set_run_state_for_testing(state)
		await process_frame
		var state_before := _document_state(document)
		_check(shell._save_button.disabled and shell._open_button.disabled, "file buttons are disabled in " + state)
		_select_dialog_action(shell, "open")
		shell._on_file_selected(valid_path)
		await process_frame
		_check(not bool(shell.last_file_result.get("ok", false)), "Open rejected in " + state)
		_check(_document_state(document) == state_before, "state rejection preserves document in " + state)
	document.set_run_state_for_testing("editing")
	await process_frame
	_check(not shell._save_button.disabled and not shell._open_button.disabled, "file buttons enable again in editing state")
	_select_dialog_action(shell, "open")
	document.set_run_state_for_testing("locked")
	var before_dialog_state := _document_state(document)
	shell._on_file_selected(valid_path)
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)), "state change after dialog selection still rejects Open")
	_check(_document_state(document) == before_dialog_state, "late state rejection preserves document")
	document.set_run_state_for_testing("editing")
	await process_frame
	var before_cancel := _document_state(document)
	_select_dialog_action(shell, "save")
	shell._on_file_dialog_canceled()
	await process_frame
	_check(bool(shell.last_file_result.get("canceled", false)), "cancel is reported as canceled")
	_check(_document_state(document) == before_cancel, "cancel preserves document/history/selection")
	_check(shell._layout_source_label.text.find("未修改") == -1, "cancel feedback does not claim a document change")
	scene.queue_free()
	await process_frame

func test_save_as_failures() -> void:
	var scene = load(SCENE_PATH).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var document = scene.document
	var shell = scene.shell
	document.add_obstacle("hard_rock", Vector3.ZERO, Vector3.ZERO, Vector3(3.0, 3.0, 3.0))
	await process_frame
	var state_before := _document_state(document)
	var viewer_before := _viewer_state(scene)
	var existing_path := _path("save-existing.json")
	_write_text(existing_path, "ORIGINAL")
	_select_dialog_action(shell, "save")
	shell._on_file_selected(existing_path)
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)), "Save As existing target fails")
	_check(_reason(shell.last_file_result).find("已存在") != -1, "Save As existing failure is explicit")
	_check(_read_text(existing_path) == "ORIGINAL", "Save As failure preserves old target bytes")
	_check(_document_state(document) == state_before and _viewer_state(scene) == viewer_before, "Save As failure preserves document/viewer")

	var directory_target := _path("save-directory")
	_check(DirAccess.make_dir_recursive_absolute(directory_target) == OK, "directory target fixture created")
	_select_dialog_action(shell, "save")
	shell._on_file_selected(directory_target)
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)), "Save As directory target fails")
	_check(_document_state(document) == state_before, "directory failure preserves document")

	var blocker_path := _path("save-parent-blocker")
	_write_text(blocker_path, "not a directory")
	var blocked_target := blocker_path.path_join("layout.json")
	_select_dialog_action(shell, "save")
	shell._on_file_selected(blocked_target)
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)), "Save As write failure fails")
	_check(not FileAccess.file_exists(blocked_target), "write failure creates no target")
	_check(_document_state(document) == state_before and _viewer_state(scene) == viewer_before, "write failure preserves document/viewer")

	var success_path := _path("nested/success.json")
	_select_dialog_action(shell, "save")
	shell._on_file_selected(success_path)
	await process_frame
	_check(bool(shell.last_file_result.get("ok", false)), "Save As succeeds after failures")
	_check(FileAccess.file_exists(success_path), "successful Save As publishes new target")
	_check(_document_state(document) == state_before, "successful Save As does not mutate document")
	scene.queue_free()
	await process_frame

func _select_dialog_action(shell, action: String) -> void:
	shell._dialog_action = action

func _write_text(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	_check(file != null, "write test fixture opened: " + path)
	if file == null:
		return
	_check(file.store_string(text), "write test fixture stored: " + path)
	file.close()

func _write_bytes(path: String, bytes: PackedByteArray) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	_check(file != null, "write byte fixture opened: " + path)
	if file == null:
		return
	_check(file.store_buffer(bytes), "write byte fixture stored: " + path)
	file.close()

func _read_text(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var text := file.get_as_text()
	file.close()
	return text

func _path(name: String) -> String:
	return _test_dir.path_join(name)

func _document_state(document) -> String:
	return var_to_str({
		"hash": document.commitment_hash(),
		"count": document.obstacle_count(),
		"selected": document.selected_id,
		"undo": document.undo_depth(),
		"redo": document.redo_depth(),
		"seed": document.random_seed,
		"seed_known": document.seed_known,
		"origin": document.layout_origin,
		"run_state": document.run_state,
		"bridge": document.control_bridge_connected,
		"link": JSON.stringify(document.link_state, "", true, true),
		"gates": JSON.stringify(document.gates, "", true, true),
	})

func _viewer_state(scene) -> String:
	var meshes: Array = []
	for child in scene._obstacle_root.get_children():
		if child is MeshInstance3D:
			meshes.append([child.position, child.rotation_degrees, child.mesh.size])
	var gates: Array = []
	for child in scene._gate_root.get_children():
		gates.append([child.name, child.position, child.quaternion])
	var drill: Transform3D = scene._drill_root.global_transform
	return var_to_str({"meshes": meshes, "gates": gates, "drill": drill, "camera": scene._camera.global_transform})

func _check_viewer_matches(document, scene, label: String) -> void:
	var meshes: Array = []
	for child in scene._obstacle_root.get_children():
		if child is MeshInstance3D:
			meshes.append(child)
	_check(meshes.size() == document.obstacle_count(), label + " rebuilds one mesh per obstacle")
	for index in mini(meshes.size(), document.obstacle_count()):
		var obstacle: Dictionary = document.obstacles[index]
		var mesh_node: MeshInstance3D = meshes[index]
		_check(mesh_node.position.is_equal_approx(obstacle.position), label + " mesh position matches object %d" % index)
		_check(mesh_node.rotation_degrees.is_equal_approx(obstacle.rotation_deg), label + " mesh rotation matches object %d" % index)
		_check((mesh_node.mesh as BoxMesh).size.is_equal_approx(obstacle.size), label + " mesh size matches object %d" % index)
	var entry_node: Node3D = scene._gate_root.get_node_or_null("Gate_entry") as Node3D
	var exit_node: Node3D = scene._gate_root.get_node_or_null("Gate_exit") as Node3D
	_check(entry_node != null and entry_node.position.is_equal_approx(document.gate_position("entry")), label + " rebuilds entry gate transform")
	_check(exit_node != null and exit_node.position.is_equal_approx(document.gate_position("exit")), label + " rebuilds exit gate transform")
	_check(not scene._selection_box.visible, label + " hides the selection box after selection reset")

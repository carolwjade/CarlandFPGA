extends Node
## Fresh targeted review regressions; same scene adds actual launcher save only
## when every regression passes. No production fault switches or old81 rerun.
const Store = preload("res://editor/layout_store.gd")
const Document = preload("res://editor/scene_document.gd")
const Shell = preload("res://ui/shell.gd")
class BeforeStore extends "res://editor/layout_store.gd":
	func _new_bridge():
		return load("res://tests/fixtures/before/bridge.gd").new()
var failures: Array = []
var records: Array = []
var checks: int = 0
var frames: int = 0
var owned_root: String = ""

func _ready() -> void:
	call_deferred("_run")

func _process(_delta: float) -> void:
	frames += 1

func _check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)
		printerr("FAIL: " + label)

func _units(value: String) -> int:
	return value.to_utf16_buffer().size() / 2

func _save_progress() -> void:
	var out = FileAccess.open(OS.get_user_data_dir().path_join("review-progress.json"), FileAccess.WRITE)
	out.store_string(JSON.stringify({"godot_process_id": OS.get_process_id(), "checks": checks, "failures": failures, "records": records}, "\t"))
	out.close()

func _reap(store, label: String) -> void:
	var deadline: int = Time.get_ticks_msec() + 9000
	while store.has_unresolved_save() and Time.get_ticks_msec() < deadline:
		await get_tree().process_frame
	_check(not store.has_unresolved_save(), label + ": worker terminal and reaped")
	records.append({"label": label, "evidence": store.save_evidence()})
	_save_progress()
	if store.has_unresolved_save():
		# Preserve actual unresolved work for the owning JobObject supervisor.
		# No replay, bare PID stop, live join or false normal completion.
		while true:
			await get_tree().process_frame

func _namespace_case(target: String, parent: String, label: String) -> void:
	var store = Store.new()
	var result: Dictionary = await store.save_new_async(target, "new namespace diagnostic")
	var launches: int = 0 if store._bridge == null else store._bridge.launch_count
	_check(result.get("code", "") == "invalid_path", label + ": invalid_path")
	_check(launches == 0, label + ": zero helper launches")
	_check(not DirAccess.dir_exists_absolute(parent), label + ": zero parents created")
	records.append({"label": label, "target": target, "parent": parent, "target_units": _units(target), "parent_units": _units(parent), "helper_launches": launches, "parent_created": DirAccess.dir_exists_absolute(parent), "result": result, "evidence": store.save_evidence()})
	_save_progress()
	if store.has_unresolved_save():
		await _reap(store, label + ": diagnostic unexpected worker")

func _run() -> void:
	owned_root = OS.get_user_data_dir().path_join("review-regression")
	DirAccess.make_dir_recursive_absolute(owned_root)
	var con_parent: String = owned_root.path_join("space-parent")
	await _namespace_case(con_parent.path_join("CON .json"), con_parent, "reserved stem trailing space")
	var com_parent: String = owned_root.path_join("sup-parent")
	await _namespace_case(com_parent.path_join("COM¹.json"), com_parent, "reserved COM superscript")
	var base: String = owned_root.path_join("temp-parent")
	var pad: int = 219 - _units(base) - 1
	if pad < 1 or pad > 255:
		printerr("SETUP: fresh owned root too long for parent219 fixture")
		get_tree().quit(2)
		return
	var long_parent: String = base.path_join("p".repeat(pad))
	await _namespace_case(long_parent.path_join("a"), long_parent, "source temp parent+41 boundary")
	var document = Document.new()
	document.add_obstacle("water", Vector3(2, 1, 0))
	var shell = Shell.new()
	var main_node = Node.new()
	get_tree().root.add_child(main_node)
	get_tree().root.add_child(shell)
	shell.bind_editor(main_node, document)
	var empty_original: Dictionary = shell.last_file_result.duplicate(true)
	shell._on_file_dialog_canceled()
	_check(shell.last_file_result == empty_original, "actionless canceled signal is ignored")
	shell._dialog_action = "open"
	shell._on_file_dialog_canceled()
	_check(shell.last_file_result.get("code") == "canceled", "normal new dialog cancellation remains effective")
	var before_store = BeforeStore.new()
	shell._layout_store = before_store
	var target: String = owned_root.path_join("unknown-alias.json").replace("/", "\\")
	shell._dialog_action = "save"
	shell.call_deferred("_on_file_selected", target)
	var deadline: int = Time.get_ticks_msec() + 8000
	while shell.last_file_result.get("code", "") != "outcome_unknown" and Time.get_ticks_msec() < deadline:
		await get_tree().process_frame
	_check(shell.last_file_result.get("code", "") == "outcome_unknown", "fresh diagnostic reaches unknown")
	await _reap(before_store, "original before-publish diagnostic")
	var original: Dictionary = shell.last_file_result.duplicate(true)
	shell._on_file_dialog_canceled()
	_check(shell.last_file_result == original, "post-reap actionless cancellation preserves unknown")
	var before_count: int = before_store._bridge.launch_count
	var alias: String = target.replace("\\", "/")
	# Explicit fresh root-authorized diagnostic operation, not automatic replay of
	# any old01-08 request. Fixed before-publish fixture cannot commit either call.
	var alias_result: Dictionary = await before_store.save_new_async(alias, "new alias-fence diagnostic")
	_check(alias_result.get("code", "") == "outcome_unknown", "slash alias remains unknown")
	_check(before_store._bridge.launch_count == before_count, "same-target slash alias cannot launch second helper")
	if before_store.has_unresolved_save():
		await _reap(before_store, "alias diagnostic unexpected extra worker")
	records.append({"label": "slash-alias", "original_display_path": target, "alias_display_path": alias, "launches_before": before_count, "launches_after": before_store._bridge.launch_count, "result": alias_result, "evidence": before_store.save_evidence()})
	_save_progress()
	var actual_smoke: Dictionary = {"executed": false}
	if failures.is_empty():
		var store = Store.new()
		var exported: Dictionary = document.export_layout_text()
		var smoke_target: String = owned_root.path_join("launcher-save/新布局😀.json")
		var saved: Dictionary = await store.save_new_async(smoke_target, String(exported.get("text", "")))
		var read: Dictionary = store.read_text(smoke_target)
		var reopened = Document.new()
		var decoded: Dictionary = reopened.apply_layout_text(String(read.get("text", "")))
		var evidence: Dictionary = store.save_evidence()
		_check(bool(saved.get("ok", false)) and bool(read.get("ok", false)) and bool(decoded.get("ok", false)), "actual source-launcher safe save and reopen")
		_check(decoded.get("layout_hash", "") == exported.get("layout_hash", "missing"), "actual source-launcher reopened codec hash")
		_check(int(evidence.get("original_exit", -1)) == 0 and bool(evidence.get("worker_completed", false)) and bool(evidence.get("cleanup_consumed", false)), "actual source-launcher helper exit/reap/cleanup")
		_check(not OS.get_environment("DEEPEYE_LAYOUT_RUNTIME").is_empty() and frames > 5, "actual source-launcher runtime binding and advancing frames")
		_check(not OS.has_environment("OPENAI_API_KEY") and not OS.has_environment("FPGA_HMAC_KEY"), "actual source-launcher credentials filtered")
		actual_smoke = {"executed": true, "saved": saved, "reopened_layout_hash": decoded.get("layout_hash", ""), "evidence": evidence, "target": smoke_target}
		records.append({"label": "actual launcher save", "evidence": evidence})
	var report: Dictionary = {"godot_process_id": OS.get_process_id(), "python_runtime_binding": JSON.parse_string(OS.get_environment("DEEPEYE_LAYOUT_RUNTIME")), "frames": frames, "checks": checks, "failures": failures, "records": records, "actual_launcher_smoke": actual_smoke, "scope": "new three review findings plus source-launcher smoke; old81 not rerun", "G02": "open", "G03": "not_run", "R03": "not_run", "all29": "not_run"}
	var out = FileAccess.open(OS.get_user_data_dir().path_join("review-evidence.json"), FileAccess.WRITE)
	out.store_string(JSON.stringify(report, "\t"))
	out.close()
	shell.queue_free()
	main_node.queue_free()
	await get_tree().process_frame
	print("REVIEW_CHECKS=%d FAILURES=%d" % [checks, failures.size()])
	get_tree().quit(0 if failures.is_empty() else 1)

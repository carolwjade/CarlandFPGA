extends SceneTree

var checks := 0
var failures: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		print("FAIL_CHECK " + label)
	else:
		print("PASS_CHECK " + label)

func _state(document) -> String:
	return var_to_str({
		"hash": document.commitment_hash(),
		"count": document.obstacle_count(),
		"selected": document.selected_id,
		"undo": document.undo_depth(),
		"redo": document.redo_depth(),
		"seed": document.random_seed,
		"seed_known": document.seed_known,
		"origin": document.layout_origin,
		"run": document.run_state,
		"bridge": document.control_bridge_connected,
		"link": JSON.stringify(document.link_state, "", true, true),
	})

func _run() -> void:
	var packed = load("res://viewer/main.tscn")
	var scene = packed.instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var document = scene.document
	var shell = scene.shell
	document.add_obstacle("hard_rock", Vector3.ZERO, Vector3.ZERO, Vector3(3.0, 3.0, 3.0))
	await process_frame
	var dir := OS.get_user_data_dir().path_join("flow-counterexample-%d" % Time.get_ticks_usec())
	_check(DirAccess.make_dir_recursive_absolute(dir) == OK, "isolated probe directory")

	var late_save := dir.path_join("late-state-save.json")
	shell._dialog_action = "save"
	document.set_run_state_for_testing("locked")
	await process_frame
	var before_late := _state(document)
	shell._on_file_selected(late_save)
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)), "save after dialog-open state change is rejected")
	_check(not FileAccess.file_exists(late_save), "late-state save creates no target")
	_check(_state(document) == before_late, "late-state save preserves document/history/seed/run/link")

	document.set_run_state_for_testing("editing")
	await process_frame
	var first_target := dir.path_join("first.json")
	shell._dialog_action = "save"
	shell._on_file_selected(first_target)
	await process_frame
	_check(bool(shell.last_file_result.get("ok", false)) and FileAccess.file_exists(first_target), "first save succeeds")
	var before_stale := _state(document)
	var stale_target := dir.path_join("stale-second-callback.json")
	shell._file_dialog.file_selected.emit(stale_target)
	await process_frame
	_check(not bool(shell.last_file_result.get("ok", false)) and String(shell.last_file_result.get("code", "")) == "no_action", "stale second callback has no retained action")
	_check(not FileAccess.file_exists(stale_target), "stale callback creates no file")
	_check(_state(document) == before_stale, "stale callback preserves document and provenance")

	var before_cancel := _state(document)
	shell._file_dialog.canceled.emit()
	await process_frame
	_check(bool(shell.last_file_result.get("canceled", false)), "cancel signal after success reports canceled")
	_check(_state(document) == before_cancel, "cancel after success does not change document/provenance")
	_check(FileAccess.file_exists(first_target), "cancel leaves prior saved target intact")

	print("COUNTEREXAMPLE_FLOW checks=%d failures=%d" % [checks, failures.size()])
	if failures.is_empty():
		print("COUNTEREXAMPLE_FLOW_RESULT PASS")
		scene.queue_free()
		await process_frame
		quit(0)
	else:
		for f in failures:
			print("COUNTEREXAMPLE_FLOW_FAIL " + f)
		scene.queue_free()
		await process_frame
		quit(1)

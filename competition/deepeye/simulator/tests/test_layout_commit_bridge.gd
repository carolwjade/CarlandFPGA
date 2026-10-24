extends SceneTree
## New focused caller checks only; fault adapters are separate pinned test files.
const Store = preload("res://editor/layout_store.gd")
const Document = preload("res://editor/scene_document.gd")
const Shell = preload("res://ui/shell.gd")

class BeforeStore extends "res://editor/layout_store.gd":
	func _new_bridge():
		return load("res://tests/fixtures/before/bridge.gd").new()
class LossStore extends "res://editor/layout_store.gd":
	func _new_bridge():
		return load("res://tests/fixtures/loss/bridge.gd").new()
class DelayStore extends "res://editor/layout_store.gd":
	func _new_bridge():
		return load("res://tests/fixtures/delay/bridge.gd").new()
class TrailingStore extends "res://editor/layout_store.gd":
	func _new_bridge():
		return load("res://tests/fixtures/trailing/bridge.gd").new()
class SplitStore extends "res://editor/layout_store.gd":
	func _new_bridge():
		return load("res://tests/fixtures/split/bridge.gd").new()

var checks := 0
var failures: Array = []
var records: Array = []
var targets := ""

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)
		printerr("FAIL: " + label)

func capture(store, label: String) -> void:
	var e: Dictionary = store.save_evidence()
	check(bool(e.get("worker_completed", false)) and bool(e.get("reaped", false)), label + ": completed owner reaped")
	if int(e.get("original_exit", -1)) >= 0:
		check(bool(e.get("cleanup_consumed", false)) and bool(e.get("cleanup_attempted", false)), label + ": cleanup consumed once")
		check(int(e.get("cleanup_prior_exit", -1)) >= 0, label + ": exact exit before cleanup")
		check(int(e.get("cleanup_after_exit_query", 0)) == -1, label + ": original map absent after cleanup")
	records.append({"label": label, "evidence": e})
	var progress := FileAccess.open(targets.path_join("bridge-progress.json"), FileAccess.WRITE)
	progress.store_string(JSON.stringify({"checks": checks, "failures": failures, "records": records}, "\t"))
	progress.close()

func wait_reap(store, label: String) -> void:
	var deadline := Time.get_ticks_msec() + 9000
	while store.has_unresolved_save() and Time.get_ticks_msec() < deadline:
		await process_frame
	check(not store.has_unresolved_save(), label + ": terminal within fixture budget")
	capture(store, label)

func document_state(document) -> Dictionary:
	return {"text": document.export_layout_text(), "snapshot": document.status_snapshot(), "selection": document.selected_id, "events": document.events.duplicate(true), "link": document.link_state.duplicate(true), "run": document.run_state, "control": document.control_bridge_connected}

func _run() -> void:
	targets = OS.get_environment("DEEPEYE_TEST_ROOT")
	if OS.get_environment("DEEPEYE_TEST_CASE") == "late-cancel":
		await _run_late_cancel()
		return
	check(not targets.is_empty(), "owned targets configured")
	var binding := OS.get_environment("DEEPEYE_LAYOUT_RUNTIME")
	var unavailable = Store.new()
	OS.set_environment("DEEPEYE_LAYOUT_RUNTIME", "")
	var missing: Dictionary = await unavailable.save_new_async(targets.path_join("no-runtime/n.json"), "x")
	check(missing.get("code") == "helper_unavailable" and not DirAccess.dir_exists_absolute(targets.path_join("no-runtime")), "missing runtime zero launch/parents")
	OS.set_environment("DEEPEYE_LAYOUT_RUNTIME", JSON.stringify({"executable": OS.get_executable_path()}))
	var mismatch: Dictionary = await unavailable.save_new_async(targets.path_join("bad-runtime/n.json"), "x")
	check(mismatch.get("code") == "helper_unavailable" and not DirAccess.dir_exists_absolute(targets.path_join("bad-runtime")), "mismatched runtime zero launch/parents")
	check(unavailable._bridge.launch_count == 0, "untrusted runtime launch count zero")
	OS.set_environment("DEEPEYE_LAYOUT_RUNTIME", binding)
	var store = Store.new()
	for suffix in ["../escape.json", "./dot.json", "CON.json", "NUL.json", "bad:stream", "bad?.json"]:
		var invalid: Dictionary = await store.save_new_async(targets.path_join(suffix), "x")
		check(invalid.get("code") == "invalid_path" and (store._bridge == null or store._bridge.launch_count == 0), "invalid namespace rejects prelaunch: " + suffix)
	store = Store.new()
	var over: Dictionary = await store.save_new_async(targets.path_join("over-limit.json"), "x".repeat(1048577))
	check(over.get("code") == "too_large" and store._bridge == null, "overlimit rejects before worker")
	var doc = Document.new()
	doc.add_obstacle("water", Vector3(2, 1, 0))
	var exported: Dictionary = doc.export_layout_text()
	check(bool(exported.ok), "real layout codec export")
	var target := targets.path_join("层😀/new/几何😀.json")
	var text := String(exported.text)
	var saved: Dictionary = await store.save_new_async(target, text)
	check(bool(saved.get("ok", false)), "actual nested Unicode/nonBMP save")
	check(FileAccess.get_file_as_bytes(target) == text.to_utf8_buffer(), "exact actual UTF8 bytes")
	var read: Dictionary = store.read_text(target)
	var reopened = Document.new()
	var decoded: Dictionary = reopened.apply_layout_text(String(read.get("text", "")))
	check(bool(read.get("ok", false)) and bool(decoded.get("ok", false)) and String(decoded.get("layout_hash", "")) == String(exported.layout_hash), "real reopen codec commitment hash")
	capture(store, "unicode-codec")
	var empty_path := targets.path_join("empty.json")
	var empty: Dictionary = store.save_new(empty_path, "")
	check(bool(empty.get("ok", false)) and FileAccess.get_file_as_bytes(empty_path).is_empty(), "safe synchronous worker compatibility")
	capture(store, "sync-empty")
	var limit_path := targets.path_join("limit.json")
	var at_limit: Dictionary = await store.save_new_async(limit_path, "x".repeat(1048576))
	check(bool(at_limit.get("ok", false)) and FileAccess.get_file_as_bytes(limit_path).size() == 1048576, "exact1MiB accepted")
	capture(store, "exact-limit")
	var sentinel_path := targets.path_join("sentinel.json")
	var sentinel := FileAccess.open(sentinel_path, FileAccess.WRITE)
	sentinel.store_string("SENTINEL\n")
	sentinel.close()
	var existing: Dictionary = await store.save_new_async(sentinel_path, "replacement")
	check(not bool(existing.get("ok", true)) and FileAccess.get_file_as_string(sentinel_path) == "SENTINEL\n", "existing sentinel preserved")
	capture(store, "existing-file")
	var dir_path := targets.path_join("sentinel-dir")
	DirAccess.make_dir_absolute(dir_path)
	var existing_dir: Dictionary = await store.save_new_async(dir_path, "replacement")
	check(not bool(existing_dir.get("ok", true)) and DirAccess.dir_exists_absolute(dir_path), "sentinel directory preserved")
	capture(store, "existing-directory")
	var before_store = BeforeStore.new()
	var shell = Shell.new()
	root.add_child(shell)
	var main_node := Node.new()
	root.add_child(main_node)
	shell.bind_editor(main_node, doc)
	shell._layout_store = before_store
	var before := document_state(doc)
	var before_target := targets.path_join("watchdog-before.json")
	shell._dialog_action = "save"
	shell.call_deferred("_on_file_selected", before_target)
	var frames := 0
	var start := Time.get_ticks_msec()
	while not shell._file_save_pending and Time.get_ticks_msec() - start < 1500:
		await process_frame
	while shell._file_save_pending and Time.get_ticks_msec() - start < 7000:
		frames += 1
		if frames == 2:
			check(shell._save_button.disabled and shell._open_button.disabled and shell._save_pending_label.text.contains("正在保存"), "pending hint and Save/Open inhibition")
			check(document_state(doc) == before, "pending preserves geometry/history/selection/run/link/control")
			shell.call_deferred("_on_file_selected", targets.path_join("second-refused.json"))
		await process_frame
	var elapsed := Time.get_ticks_msec() - start
	check(frames > 5, "await advances frames")
	check(elapsed >= 4900 and elapsed < 6500 and shell.last_file_result.get("code") == "outcome_unknown", "finite UI deadline unknown")
	check(before_store.has_unresolved_save() and before_store._bridge.launch_count == 1 and not FileAccess.file_exists(targets.path_join("second-refused.json")), "one retained slot refuses repeated shell request")
	check(document_state(doc) == before and doc.can_edit(), "unknown preserves state and ordinary editing availability")
	var other_store = Store.new()
	var refused: Dictionary = await other_store.save_new_async(targets.path_join("other-refused.json"), "x")
	check(refused.get("code") == "save_pending" and other_store._bridge.launch_count == 0, "process-wide owner refuses second store")
	doc.add_obstacle("hard_rock", Vector3(6, 0, 0))
	var state_after_edit := document_state(doc)
	await wait_reap(before_store, "watchdog-before")
	check(int(before_store.save_evidence().get("original_exit", -1)) == 124 and not FileAccess.file_exists(before_target), "fixture watchdog124 before publication")
	check(document_state(doc) == state_after_edit, "late terminal notice never reapplies old geometry over a later edit")
	records.append({"label": "responsive-shell", "frames": frames, "elapsed_msec": elapsed, "last_file_result": shell.last_file_result.duplicate(true)})
	shell.queue_free()
	main_node.queue_free()
	await process_frame
	var loss_store = LossStore.new()
	var loss_target := targets.path_join("lost-response.json")
	var lost: Dictionary = await loss_store.save_new_async(loss_target, "真实提交😀")
	check(lost.get("code") == "outcome_unknown" and FileAccess.get_file_as_string(loss_target) == "真实提交😀", "injected response loss preserves actual committed bytes")
	var loss_count: int = loss_store._bridge.launch_count
	var no_replay: Dictionary = await loss_store.save_new_async(loss_target, "DO NOT REPLACE")
	check(not bool(no_replay.get("ok", true)) and loss_store._bridge.launch_count == loss_count, "unknown never retransmits/replays")
	await wait_reap(loss_store, "watchdog-after-publication")
	check(int(loss_store.save_evidence().get("original_exit", -1)) == 124 and FileAccess.get_file_as_string(loss_target) == "真实提交😀", "watchdog124 after publication preserves target")
	var fenced: Dictionary = await loss_store.save_new_async(loss_target, "DO NOT REPLACE")
	check(fenced.get("code") == "outcome_unknown" and loss_store._bridge.launch_count == loss_count, "unknown path remains fenced after reap")
	var delay_store = DelayStore.new()
	var delay_target := targets.path_join("delayed-known.json")
	var delayed: Dictionary = await delay_store.save_new_async(delay_target, "late geometry")
	check(delayed.get("code") == "outcome_unknown", "late trusted frame retains original unknown")
	await wait_reap(delay_store, "delayed-trusted-frame")
	var late: Array = delay_store.take_late_save_results()
	check(late.size() == 1 and bool(late[0].result.get("ok", false)) and int(late[0].original_exit) == 0, "late committed response recorded separately")
	check(String(delay_store.save_evidence().get("visible_result", {}).get("code", "")) == "outcome_unknown" and FileAccess.get_file_as_string(delay_target) == "late geometry", "late success does not replace original unknown")
	var trailing_store = TrailingStore.new()
	var trailing_path := targets.path_join("trailing-frame.json")
	var trailing: Dictionary = await trailing_store.save_new_async(trailing_path, "retained despite trailing")
	check(trailing.get("code") == "outcome_unknown" and FileAccess.get_file_as_string(trailing_path) == "retained despite trailing", "post-frame trailing stdout rejects claimed success and retains commit")
	capture(trailing_store, "trailing-frame")
	var split_store = SplitStore.new()
	var split_path := targets.path_join("split-frame.json")
	var split: Dictionary = await split_store.save_new_async(split_path, "split bytes 😀")
	check(bool(split.get("ok", false)) and FileAccess.get_file_as_string(split_path) == "split bytes 😀", "split header/body bytes accumulate without loss")
	check(int(split_store.save_evidence().get("partial_reads", 0)) >= 2, "actual partial reads observed")
	capture(split_store, "split-frame")
	var report := {"godot_process_id": OS.get_process_id(), "checks": checks, "failures": failures, "records": records, "test_only_adapters": ["before", "loss", "delay", "trailing", "split"], "G02": "open", "G03": "not_run", "R03": "not_run", "all29": "not_run"}
	var output := FileAccess.open(targets.path_join("bridge-evidence.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	output.close()
	print("CALLER_CHECKS=%d FAILURES=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

func _run_late_cancel() -> void:
	var store = BeforeStore.new()
	var doc = Document.new()
	var shell = Shell.new()
	var main_node := Node.new()
	root.add_child(main_node)
	root.add_child(shell)
	shell.bind_editor(main_node, doc)
	shell._layout_store = store
	shell._dialog_action = "save"
	shell.call_deferred("_on_file_selected", targets.path_join("late-cancel.json"))
	var deadline := Time.get_ticks_msec() + 7000
	while shell.last_file_result.get("code", "") != "outcome_unknown" and Time.get_ticks_msec() < deadline:
		await process_frame
	check(shell.last_file_result.get("code", "") == "outcome_unknown" and store.has_unresolved_save(), "unknown remains unresolved before late cancellation")
	var original: Dictionary = shell.last_file_result.duplicate(true)
	shell._on_file_dialog_canceled()
	check(shell.last_file_result == original, "late cancelled signal cannot replace unknown result")
	await wait_reap(store, "late-cancel-watchdog")
	var report := {"godot_process_id": OS.get_process_id(), "checks": checks, "failures": failures, "records": records, "case": "late-cancel"}
	var output := FileAccess.open(targets.path_join("bridge-evidence.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	output.close()
	shell.queue_free()
	main_node.queue_free()
	await process_frame
	print("LATE_CANCEL_CHECKS=%d FAILURES=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

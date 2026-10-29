extends RefCounted
## Private opt-in controls. Object capabilities are confined to each call's stack.
const PresenterSource = preload("res://viewer/asset_presenter.gd")
const ForeignProbe = preload("res://runtime/managed_writer_foreign_probe.gd")
var _run_id: String = ""
var _configured: bool = false
var _pre: bool = false
var _frozen: bool = false
var _unlocked: bool = false
var _refrozen: bool = false
var _final: bool = false
var _first_token_id: int = 0
var _random_calls: int = 0

func configure(config: Dictionary) -> bool:
	if _configured or config.size() != 3 or not config.has("schema") or not config.has("enabled") or not config.has("run_id"):
		return false
	if not config.schema is int or config.schema != 1 or not config.enabled is bool or not config.enabled or not config.run_id is String or config.run_id.is_empty():
		return false
	_run_id = config.run_id
	_configured = true
	return true

func _report(stage: String, test_case: String, passed: bool, counts: Dictionary = {}) -> bool:
	for count in counts.values():
		if not count is int or count < 0:
			return false
	print("DEEYE_MANAGED_WRITER_CONTROL " + JSON.stringify({"schema": 1, "run_id": _run_id,
		"stage": stage, "case": test_case, "passed": passed, "counts": counts}))
	return passed

func run_pre_admission(bridge: Object) -> bool:
	if not _configured or _pre:
		return false
	var context: Dictionary = bridge._managed_control_context(self, "pre_admission")
	if context.is_empty():
		return false
	var presenter: Object = context.presenter
	var unbound: RefCounted = PresenterSource.new()
	var denied_frame: Node3D = unbound.create_frame()
	var denied_drill: Node3D = unbound.create_drill()
	var ok: bool = _report("pre_admission", "unbound_denied", denied_frame == null and denied_drill == null and not unbound._owned_can_mutate())
	var wrong_main: Node3D = Node3D.new()
	var wrong: bool = presenter._owned_bind_main(wrong_main)
	wrong_main.free()
	ok = _report("pre_admission", "wrong_main_bind_denied", not wrong) and ok
	var workspace: Node3D = context.workspace
	var canary: Node3D = Node3D.new()
	canary.name = "ManagedUnregisteredCanary"
	workspace.add_child(canary)
	var refused: Dictionary = bridge._managed_control_probe(self)
	workspace.remove_child(canary)
	canary.free()
	ok = _report("pre_admission", "unregistered_node_refused", not refused.get("ok", true) and refused.get("code", "") == "unregistered_managed_node") and ok
	var observer: Node = Node.new()
	observer.name = "ManagedForeignObserverCanary"
	observer.set_script(ForeignProbe)
	workspace.add_child(observer)
	var foreign: Dictionary = bridge._managed_control_probe(self)
	workspace.remove_child(observer)
	observer.free()
	ok = _report("pre_admission", "foreign_observer_script_refused", not foreign.get("ok", true) and foreign.get("code", "") == "foreign_node_script") and ok
	var clean: Dictionary = bridge._managed_control_probe(self)
	ok = ok and bool(clean.get("ok", false))
	context.clear()
	_pre = ok
	return _report("pre_admission", "pre_admission_complete", ok)

func run_frozen(bridge: Object) -> bool:
	if not _pre or _frozen:
		return false
	var context: Dictionary = bridge._managed_control_context(self, "frozen")
	if context.is_empty():
		return false
	var token: RefCounted = context.token
	_first_token_id = token.get_instance_id()
	var doc_generation: int = context.document_generation
	var geometry_generation: int = context.geometry_generation
	var qualified: bool = bridge._managed_control_qualified(self, token, doc_generation, geometry_generation)
	var ok: bool = _report("frozen", "same_original_coverage", qualified)
	var wrong_token: RefCounted = RefCounted.new()
	var bad_token: bool = bridge._managed_control_qualified(self, wrong_token, doc_generation, geometry_generation)
	var bad_generation: bool = bridge._managed_control_qualified(self, token, doc_generation + 1, geometry_generation)
	var bad_geometry: bool = bridge._managed_control_qualified(self, token, doc_generation, geometry_generation + 1)
	ok = _report("frozen", "wrong_token_generation_denied", not bad_token and not bad_generation and not bad_geometry) and ok
	var before: Dictionary = bridge._managed_control_fingerprint(self)
	var presenter: Object = context.presenter
	var count_before: int = presenter._owned_refusal_count()
	var frame: Node3D = presenter.create_frame()
	var drill: Node3D = presenter.create_drill()
	var direct: Node3D = presenter._create("obstacle", "water")
	var synced: Dictionary = presenter.sync_obstacles(context.obstacles, context.document.obstacles)
	if not context.document.obstacles.is_empty():
		presenter._remove(int(context.document.obstacles[0].object_id))
	var count_after: int = presenter._owned_refusal_count()
	var after: Dictionary = bridge._managed_control_fingerprint(self)
	var denied: bool = frame == null and drill == null and direct == null and not synced.get("ok", true)
	denied = denied and not before.is_empty() and before == after and count_after >= count_before + 4
	ok = _report("frozen", "presenter_mutations_denied", denied, {"refusals": count_after - count_before}) and ok
	var camera: Camera3D = context.camera
	var original: Transform3D = camera.transform
	context.main.set_camera_view("front")
	if camera.transform == original:
		context.main.set_camera_view("back")
	var camera_changed: bool = camera.transform != original
	var camera_after: Dictionary = bridge._managed_control_fingerprint(self)
	var processing: bool = context.main.is_processing() and context.main.shell.is_processing()
	ok = _report("frozen", "camera_remains_live", camera_changed and processing and after == camera_after) and ok
	context.clear()
	_frozen = ok
	return _report("frozen", "frozen_complete", ok)

func after_unlock(bridge: Object) -> bool:
	if not _frozen or _unlocked or _random_calls != 0:
		return false
	var context: Dictionary = bridge._managed_control_context(self, "post_unlock")
	if context.is_empty():
		return false
	var document: Object = context.document
	var before_generation: int = document._owned_generation(bridge)
	var editable: bool = document.can_edit()
	_random_calls += 1
	var result: Dictionary = document.randomize_layout(20261024, 1) if editable else {"ok": false}
	var after_generation: int = document._owned_generation(bridge)
	var ok: bool = _report("post_unlock", "legal_edit_and_random_once", editable and bool(result.get("ok", false)) and result.get("count", 0) == 1 and after_generation == before_generation + 1 and bool(context.get("legal_edit_consumed", false)), {"random_calls": _random_calls})
	var invalid: bool = bridge._managed_control_old_invalid(self)
	ok = _report("post_unlock", "old_coverage_retired", invalid) and ok
	context.clear()
	_unlocked = ok
	return _report("post_unlock", "post_unlock_complete", ok)

func after_refreeze(bridge: Object) -> bool:
	if not _unlocked or _refrozen:
		return false
	var context: Dictionary = bridge._managed_control_context(self, "refreeze")
	if context.is_empty():
		return false
	var token: RefCounted = context.token
	var qualified: bool = bridge._managed_control_qualified(self, token, int(context.document_generation), int(context.geometry_generation))
	var old_invalid: bool = bridge._managed_control_old_invalid(self)
	var ok: bool = token.get_instance_id() != _first_token_id and qualified and old_invalid
	context.clear()
	_refrozen = ok
	ok = _report("refreeze", "new_token_coverage", ok)
	return _report("refreeze", "refreeze_complete", ok)

func run_final_content(bridge: Object) -> bool:
	if not _refrozen or _final:
		return false
	var context: Dictionary = bridge._managed_control_context(self, "final_content")
	if context.is_empty():
		return false
	context.clear()
	var result: Dictionary = bridge._managed_control_poison_mesh(self)
	var ok: bool = _report("final_content", "same_mesh_content_change_detected", bool(result.get("changed", false)) and bool(result.get("detected", false)), {"surfaces": int(result.get("surfaces", 0)), "vertices": int(result.get("vertices", 0)), "array_mesh": int(result.get("array_mesh", 0)), "primitive_mesh": int(result.get("primitive_mesh", 0))})
	ok = _report("final_content", "issued_coverage_sticky_invalid", bool(result.get("sticky", false))) and ok
	_final = ok
	return _report("final_content", "final_content_complete", ok)

func status() -> Dictionary:
	return {"pre_admission": _pre, "frozen": _frozen, "post_unlock": _unlocked,
		"refreeze": _refrozen, "final_content": _final, "random_calls": _random_calls}

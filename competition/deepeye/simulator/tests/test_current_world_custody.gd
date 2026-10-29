extends SceneTree
## New current-Main custody/mode integration control; no freeze or motion grant.
var checks := 0
var failures: Array = []
var resources: Dictionary = {}

func _initialize() -> void:
	_run.call_deferred()

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _gates_closed(scene) -> bool:
	return scene.shell._run_button.disabled and scene.shell._pause_button.disabled and scene.shell._continue_button.disabled and not scene.document.control_bridge_connected and not scene.document.is_motion_active()

func _new_main():
	var packed = load("res://viewer/main.tscn")
	if packed == null:
		return null
	var scene = packed.instantiate()
	root.add_child(scene)
	return scene

func _run() -> void:
	var scene = _new_main()
	if scene == null:
		check(false, "original Main loads")
		_finish()
		return
	await process_frame
	await process_frame
	var drill: Node3D = scene.get("_drill_root")
	var body = drill.get_node_or_null("DrillPDC")
	resources = {"target": str(drill.name), "path": str(drill.get_path()),
		"asset_id": "" if body == null else body.get_meta("asset_id", ""),
		"mesh_count": drill.find_children("*", "MeshInstance3D", true, false).size(),
		"presenter": scene._asset_presenter.report()}
	check(resources.target == "DrillPresentation" and resources.asset_id == "drill_pdc_v1" and resources.mesh_count == 28, "actual original body resource retained")
	check(resources.presenter.state == "ready", "no hidden resource fallback")
	check(_gates_closed(scene), "custody/presentation never opens Run/control")
	check(scene.document.can_edit(), "unattached current editor remains usable")
	var missing := false
	for method in ["_owned_startup_status", "_owned_attach_world_bridge", "_owned_world_references", "_owned_drain_and_lock", "_owned_apply_drill_global", "_owned_validate_custody", "_owned_custody_contains", "_authority_renderer_allowed"]:
		var exists: bool = scene.has_method(method)
		check(exists, "current Main custody API " + method)
		missing = missing or not exists
	for path in ["world_motion_bridge.gd", "owned_world_start.gd", "managed_writer_controls.gd", "managed_writer_foreign_probe.gd"]:
		var exists := ResourceLoader.exists("res://runtime/" + path)
		check(exists, "current runtime source " + path)
		missing = missing or not exists
	check(scene.document.has_method("_owned_lock_geometry"), "current original document lock capability")
	check(scene._asset_presenter.has_method("_owned_is_frozen"), "current original presenter custody capability")
	check(scene.shell.has_method("_owned_freeze_ready"), "current original shell idle/freeze gate")
	if missing:
		scene.free()
		_finish()
		return
	check(scene._owned_startup_status().ok, "original Main custody startup completed")
	check(scene._owned_custody_contains(drill), "original body anchor source registered")
	check(scene.bind_authority_renderer("run-renderer-canary"), "unattached renderer mode remains usable")
	var canary := RefCounted.new()
	check(not scene._owned_attach_world_bridge(canary), "world refuses prebound renderer")
	check(_gates_closed(scene), "prebound renderer never grants Run")
	scene.free()
	# This canary checks participant identity/mode guards only. It never calls
	# lock/freeze or claims the real world bridge/source profile is qualified.
	scene = _new_main()
	drill = scene.get("_drill_root")
	var direct = load("res://viewer/authority_pose_bridge.gd").new()
	check(direct.bind_target(drill, "run-direct-canary"), "unattached direct presentation may bind")
	canary = RefCounted.new()
	check(scene._owned_attach_world_bridge(canary), "original participants accept one capability identity")
	check(not scene.bind_authority_renderer("other"), "renderer bind refuses attached world")
	var late_direct = load("res://viewer/authority_pose_bridge.gd").new()
	check(not late_direct.bind_target(drill, "late"), "public direct bind refuses attached world")
	var before: Transform3D = drill.global_transform
	var frame := {"run_id": "run-direct-canary", "authority_revision": 1, "pose_revision": 1,
		"position_m": [1, 2, 3], "orientation_xyzw": [0, 0, 0, 1], "stopped": true}
	check(not scene.present_authority_frame(frame).get("accepted", true), "Main presentation refuses attached world")
	check(not direct.apply_frame(frame).get("accepted", true), "retained direct bridge cannot bypass world mode")
	check(drill.global_transform == before, "mode refusal leaves original native pose unchanged")
	check(not scene._owned_apply_drill_global(canary, RefCounted.new(), Transform3D(Basis.IDENTITY, Vector3(1, 2, 3)), "1"), "wrong retained token cannot write original drill")
	check(drill.global_transform == before and _gates_closed(scene), "sole writer rejection preserves pose and Run gates")
	scene.free()
	# This additional source control is intentionally not executed by the earlier
	# RED (which returned at missing interfaces); Root owns post-merge release.
	scene = _new_main()
	drill = scene.get("_drill_root")
	direct = load("res://viewer/authority_pose_bridge.gd").new()
	check(direct.bind_target(drill, "run-direct-canary"), "retain original Main before reparent canary")
	var original_parent: Node = drill.get_parent()
	var foreign_parent := Node3D.new()
	root.add_child(foreign_parent)
	drill.reparent(foreign_parent)
	before = drill.global_transform
	check(not direct.apply_frame(frame).get("accepted", true), "reparent cannot escape retained original Main")
	check(drill.global_transform == before, "reparent refusal leaves actual pose unchanged")
	drill.reparent(original_parent)
	check(not direct.apply_frame(frame).get("accepted", true), "restored parent cannot revive retired direct owner")
	foreign_parent.free()
	scene.free()
	_finish()

func _finish() -> void:
	print(JSON.stringify({"checks": checks, "failures": failures, "actual_resources": resources,
		"freeze_qualified": false, "movement_authorized": false}))
	quit(0 if failures.is_empty() else 1)

extends SceneTree
var checks := 0
var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: "+message)

func _run() -> void:
	var mode := FileAccess.get_file_as_string("res://failure-mode.txt").strip_edges()
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var doc = scene.document
	_check(doc.add_obstacle("water",Vector3(2,3,4)).ok,"document remains usable under " + mode)
	var id := int(doc.obstacles[0].object_id)
	var presenter = scene._asset_presenter
	_check(presenter.report().state == "degraded", "failure explicitly degrades presentation")
	_check(not presenter.report().diagnostics.is_empty(), "persistent diagnostic retained")
	_check(presenter.obstacle_node(id) == null, "failed water cannot be adopted as valid asset")
	_check(scene._fallback_obstacles.has(id), "visible actual greybox substitutes failed water")
	var fallback: MeshInstance3D = scene._fallback_obstacles[id]
	_check(fallback.visible and fallback.mesh is BoxMesh and fallback.position == Vector3(2,3,4), "fallback preserves placement and is visible")
	_check("资源加载失败" in scene._obstacle_labels[id].text, "fallback label explicitly names resource failure")
	_check("资源加载失败" in scene.shell._presentation_label.text, "persistent UI report marks degraded")
	var before_calls = presenter.report().factory_calls
	var before_events: int = doc.events.size()
	for i in 5:
		scene._sync_obstacles()
	_check(before_calls == presenter.report().factory_calls, "no repeated failed factory allocation")
	_check(before_events == doc.events.size(), "observer failure log deduplicated")
	_check(scene._fallback_obstacles[id] == fallback,"repeated sync preserves fallback identity")
	_check(not doc.control_bridge_connected and not doc.is_motion_active(),"no live bridge or motion")
	_check(scene.shell._run_button.disabled and scene.shell._continue_button.disabled and scene.shell._pause_button.disabled,"run controls stay disabled")
	if mode == "missing-file":
		_check(scene._drill_root.name == "DrillGreybox", "missing fixed dependency uses real drill fallback without preload parse error")
	else:
		_check(scene._drill_root.get_node_or_null("DrillPDC") != null,"valid drill survives one failed obstacle")
		var replacement_doc = load("res://editor/scene_document.gd").new()
		replacement_doc.add_obstacle("hard_rock",Vector3(2,3,4))
		_check(doc.apply_layout_text(replacement_doc.export_layout_text().text).ok,"valid open changes kind with reused ID")
		var replacement: Node3D = presenter.obstacle_node(id)
		_check(replacement != null and replacement.get_meta("asset_id","") == "obstacle_hard_rock_v1", "kind replacement adopts valid B geometry")
		_check(not scene._fallback_obstacles.has(id) and not is_instance_valid(fallback), "old failed-kind fallback is freed, no stale geometry")
		_check(presenter.report().state == "degraded", "failure history remains visible until restart")
	doc.reset_layout()
	_check(scene._obstacle_root.get_child_count() == 0,"clear frees all roots and labels")
	print("ASSET_FAILURE mode=%s checks=%d failures=%d report=%s"%[mode,checks,failures,JSON.stringify(presenter.report())])
	scene.free()
	quit(1 if failures else 0)

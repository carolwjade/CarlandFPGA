extends SceneTree
var checks: int = 0
var failures: int = 0
func _initialize() -> void: call_deferred("_run")
func check(ok: bool, label: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ")+label)
	if not ok: failures += 1
func _run() -> void:
	var mode := FileAccess.get_file_as_string("res://review-mode.txt").strip_edges()
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	var doc = scene.document
	check(doc.add_obstacle("water",Vector3(2,3,4)).ok,"document add remains usable")
	var id: int = doc.obstacles[0].object_id
	var presenter = scene._asset_presenter
	var report: Dictionary = presenter.report()
	var asset: Node3D = presenter.obstacle_node(id)
	var fallback: MeshInstance3D = scene._fallback_obstacles.get(id,null)
	check(report.state=="degraded","invalid startup/factory/schema degrades report")
	check(not report.diagnostics.is_empty(),"failure records persistent diagnostic")
	check(asset==null,"invalid or empty asset rejected")
	check(fallback!=null and fallback.visible and fallback.mesh is BoxMesh,"real visible fallback preserves document object")
	check("资源加载失败" in scene._obstacle_labels[id].text,"object label explicitly discloses fallback")
	check("资源加载失败" in scene.shell._presentation_label.text,"shell explicitly discloses degraded presentation")
	var calls: Dictionary = report.factory_calls
	var events: int = doc.events.size()
	for i in 6: scene._sync_obstacles()
	check(calls==presenter.report().factory_calls and events==doc.events.size(),"no failed-factory retries or repeated logs")
	check(not doc.control_bridge_connected and not doc.is_motion_active() and scene.shell._run_button.disabled and scene.shell._pause_button.disabled and scene.shell._continue_button.disabled,"failure grants no authority or motion")
	if mode in ["null","collider","empty-visual","bad-license"]:
		var newdoc = load("res://editor/scene_document.gd").new()
		newdoc.add_obstacle("hard_rock",Vector3(2,3,4))
		check(doc.apply_layout_text(newdoc.export_layout_text().text).ok,"parameter open with same ID new kind succeeds")
		var repaired: Node3D = presenter.obstacle_node(id)
		check(repaired!=null and repaired.get_meta("asset_id")=="obstacle_hard_rock_v1","valid kind repairs geometry")
		check(not scene._fallback_obstacles.has(id),"recovery frees fallback rather than hiding stale geometry")
		check(presenter.report().state=="degraded","failure history remains truthful until restart")
	# A transformed parent must affect fallback label and pick just as valid geometry.
	if mode=="null":
		doc.reset_layout()
		doc.add_obstacle("water",Vector3(2,3,4))
		id = doc.obstacles[0].object_id
		scene._world.transform = Transform3D(Basis(Quaternion(Vector3.UP,.5)),Vector3(7,2,-4))
		scene._sync_obstacles()
		fallback = scene._fallback_obstacles[id]
		var world_bounds := AABB(fallback.global_transform*Vector3(-3,-2,-1),Vector3.ZERO)
		for v in [Vector3(-3,-2,-1),Vector3(-3,-2,1),Vector3(-3,2,-1),Vector3(-3,2,1),Vector3(3,-2,-1),Vector3(3,-2,1),Vector3(3,2,-1),Vector3(3,2,1)]:
			world_bounds = world_bounds.expand(fallback.global_transform*v)
		var actual_label: Label3D = scene._obstacle_labels[id]
		var expected_label := Vector3(world_bounds.get_center().x,world_bounds.end.y+.7,world_bounds.get_center().z)
		print("FALLBACK_LABEL actual="+str(actual_label.global_position)+" expected="+str(expected_label))
		check(actual_label.global_position.distance_to(expected_label)<.00002,"fallback label honors full parent world transform")
		var world_center: Vector3 = fallback.global_position
		var screen: Vector2 = scene._camera.unproject_position(world_center)
		var picked: int = scene._pick_object(screen)
		print("FALLBACK_PICK actual=%d expected=%d world_center=%s"%[picked,id,str(world_center)])
		check(picked==id,"fallback remains selectable at its displayed transformed position")
	doc.reset_layout()
	check(scene._obstacle_root.get_child_count()==0,"clear leaves no obstacle roots or labels")
	print("FAILURE_REVIEW mode=%s checks=%d failures=%d report=%s"%[mode,checks,failures,JSON.stringify(presenter.report())])
	scene.free()
	quit(1 if failures else 0)

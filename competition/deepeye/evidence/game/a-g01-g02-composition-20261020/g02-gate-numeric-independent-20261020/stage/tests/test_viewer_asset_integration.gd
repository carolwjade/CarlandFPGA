extends SceneTree
## Presentation only. Geometry comparisons use 1e-5 m arithmetic tolerance;
## this is not physical clearance, board, GPU timing or formal G01 acceptance.

var checks := 0
var failures := 0
const KINDS := ["water", "hard_rock", "fault", "void", "casing"]
const BASE := [Vector3(6,4,2), Vector3(3,3,3), Vector3(8,1,6), Vector3(4,3,3), Vector3(.8,.8,8)]
const SIZES := [Vector3(7,3,3), Vector3(2,4,3), Vector3(9,1.5,4), Vector3(3,4,5), Vector3(1.2,.6,9)]

func _initialize() -> void:
	call_deferred("_run")

func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: " + message)

func _run() -> void:
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var presenter = scene.get("_asset_presenter")
	_check(presenter != null, "actual viewer binds asset presenter")
	if presenter == null:
		scene.free()
		_finish()
		return
	_check(scene.document.obstacle_count() == 0, "initial document remains empty")
	_check(presenter.report().state == "ready", "pinned presentation has zero fallbacks")
	var frames := _assets(scene._world, "frame_workspace_v1")
	var drills := _assets(scene._drill_root, "drill_pdc_v1")
	_check(frames.size() == 1, "exactly one B frame attached")
	_check(drills.size() == 1, "actual static B drill attached")
	var direct_boxes := 0
	for child in scene._world.get_children():
		if child is MeshInstance3D and child.mesh is BoxMesh:
			direct_boxes += 1
	_check(direct_boxes == 9, "only eight corners and selection box; no duplicate A edge bars")
	if drills.size() == 1:
		_test_drill(drills[0], presenter)
	var doc = scene.document
	for kind in KINDS:
		_check(doc.add_obstacle(kind, Vector3(2,-3,4)).ok, "add real " + kind)
	for i in KINDS.size():
		var id := int(doc.obstacles[i].object_id)
		_check(doc.update_obstacle(id, {"size":SIZES[i], "rotation_deg":Vector3(15,37,-20)}).ok, "legal rotated nonuniform " + KINDS[i])
		var node = presenter.obstacle_node(id)
		_check(node != null, "one B instance for " + KINDS[i])
		if node == null:
			continue
		_check(node.get_meta("asset_id") == "obstacle_" + KINDS[i] + "_v1", "correct kind identity")
		_check(node.get_node_or_null("Visual") != null and node.get_node_or_null("Collision") != null, "Visual and Collision preserved")
		_check(_safe(node), "all collision objects/shape/scripts disabled")
		var rotation := Basis.from_euler(Vector3(15,37,-20) * PI / 180.0)
		var scale: Vector3 = SIZES[i] / BASE[i]
		var wanted := Basis(rotation.x*scale.x, rotation.y*scale.y, rotation.z*scale.z)
		_check(node.transform.basis.is_equal_approx(wanted) and node.position.is_equal_approx(Vector3(2,-3,4)), "rotation columns scale with original generator pivot")
		_check(_bounds_contain_vertices(node, presenter.world_visual_bounds(node)), "world bounds contain actual transformed vertices " + KINDS[i])
		var label: Label3D = scene._obstacle_labels[id]
		var box: AABB = presenter.world_visual_bounds(node)
		_check(absf(label.global_position.y - box.end.y - .7) < .00001, "label above actual rotated visual bounds")
	_test_parent_bounds(scene, presenter)
	_test_picking(presenter)
	await _test_history_and_files(scene)
	await _test_focus(scene, drills)
	_test_budget(scene)
	_check(not doc.control_bridge_connected and not doc.is_motion_active(), "presentation grants no control or motion")
	_check(scene.shell._run_button.disabled and scene.shell._pause_button.disabled and scene.shell._continue_button.disabled, "all run controls disabled")
	_check(presenter.report().state == "ready", "successful integration finishes without fallback")
	scene.queue_free()
	await process_frame
	_finish()

func _finish() -> void:
	print("VIEWER_ASSET_INTEGRATION checks=%d failures=%d" % [checks,failures])
	quit(1 if failures else 0)

func _assets(node: Node, asset_id: String) -> Array:
	var found: Array = []
	if node.get_meta("asset_id", "") == asset_id:
		found.append(node)
	for child in node.get_children():
		found.append_array(_assets(child, asset_id))
	return found

func _safe(node: Node) -> bool:
	if node.get_script() != null:
		return false
	if node is CollisionObject3D and (node.collision_layer != 0 or node.collision_mask != 0):
		return false
	if node is CollisionShape3D and not node.disabled:
		return false
	for child in node.get_children():
		if not _safe(child):
			return false
	return true

func _bounds_contain_vertices(node: Node3D, bounds: AABB) -> bool:
	for mesh in node.find_children("*", "MeshInstance3D", true, false):
		for vertex in mesh.mesh.get_faces():
			var point: Vector3 = mesh.global_transform * vertex
			if not bounds.grow(.00001).has_point(point):
				return false
	return true

func _test_drill(drill: Node3D, presenter) -> void:
	var meshes := drill.find_children("*", "MeshInstance3D", true, false)
	_check(meshes.size() == 28, "B drill has 28 actual mesh parts")
	_check(drill.find_children("Blade*", "MeshInstance3D", true, false).size() == 6, "six drill blades")
	_check(drill.find_children("CutterStud*", "MeshInstance3D", true, false).size() == 18, "eighteen cutter studs")
	_check(drill.global_transform == Transform3D.IDENTITY, "actual drill preserves unit scale and +Z orientation at origin")
	_check(_safe(drill), "drill collision presentation stays disabled")
	var bounds: AABB = presenter.local_visual_bounds(drill)
	_check(absf(bounds.size.z - .8) < .000002, "actual axial length .80m")
	var positive_closed := true
	var max_radial := 0.0
	for mesh in meshes:
		var volume := 0.0
		var edges := {}
		var faces: PackedVector3Array = mesh.mesh.get_faces()
		var relative: Transform3D = drill.global_transform.affine_inverse()*mesh.global_transform
		for index in range(0, faces.size(), 3):
			var a: Vector3 = relative*faces[index]
			var b: Vector3 = relative*faces[index+1]
			var c: Vector3 = relative*faces[index+2]
			if (b-a).cross(c-a).length_squared() < 1e-20:
				continue
			volume -= a.dot(b.cross(c))/6.0
			for pair in [[a,b],[b,c],[c,a]]:
				var first: Vector3i = Vector3i((pair[0]*1000000.0).round())
				var second: Vector3i = Vector3i((pair[1]*1000000.0).round())
				var forward := str(first) + ":" + str(second)
				var backward := str(second) + ":" + str(first)
				if edges.has(backward):
					edges[backward] -= 1
				else:
					edges[forward] = int(edges.get(forward,0))+1
		for count in edges.values():
			if count != 0:
				positive_closed = false
		positive_closed = positive_closed and volume > 0.0
		for vertex in faces:
			var point: Vector3 = relative*vertex
			max_radial = maxf(max_radial, Vector2(point.x,point.y).length())
	_check(positive_closed, "each actual B component closed and positive clockwise volume with 1um seam weld")
	_check(max_radial <= .120002, "actual drill vertices contained within nominal .24m diameter")

func _test_parent_bounds(scene, presenter) -> void:
	var water = presenter.obstacle_node(scene.document.obstacles[0].object_id)
	var metadata = water.get_meta("geometry_bounds_m").duplicate(true)
	var local_box: AABB = presenter.local_visual_bounds(water)
	_check(local_box.get_center().length() > .00001, "water measured local centre is nonzero")
	var mesh = water.find_children("*", "MeshInstance3D", true, false)[0]
	var vertex: Vector3 = mesh.mesh.get_faces()[17]
	var parent_transform := Transform3D(Basis.from_euler(Vector3(.2,-.3,.1)), Vector3(-2,1,3))
	scene._world.transform = parent_transform
	var asset_point: Vector3 = water.global_transform.affine_inverse()*mesh.global_transform*vertex
	var r := Basis.from_euler(Vector3(15,37,-20)*PI/180.0)
	var expected: Vector3 = parent_transform*(Vector3(2,-3,4) + r*((SIZES[0]/BASE[0])*asset_point))
	_check((mesh.global_transform*vertex).distance_to(expected) < .00001, "parent * (position + rotation * nominal scale * vertex), no recenter")
	_check(_bounds_contain_vertices(water,presenter.world_visual_bounds(water)), "world bounds include transformed parent")
	_check(water.get_meta("geometry_bounds_m") == metadata, "asset-local metadata unchanged by placement")
	scene._world.transform = Transform3D.IDENTITY

func _test_picking(presenter) -> void:
	var parent := Node3D.new()
	root.add_child(parent)
	var other = load("res://viewer/asset_presenter.gd").new()
	# Distances from z=10 are 7 for the nearer 4m-deep object, 7.5 for
	# the farther 1m-deep object. Normalizing local rays reverses this order.
	var items := [{"object_id":101,"kind":"fault","position":Vector3(0,0,1),"rotation_deg":Vector3.ZERO,"size":Vector3(8,1,4)},
		{"object_id":102,"kind":"fault","position":Vector3(0,0,2),"rotation_deg":Vector3.ZERO,"size":Vector3(8,1,1)}]
	other.sync_obstacles(parent,items)
	_check(other.pick_obstacle(Vector3(0,0,10),Vector3.FORWARD) == 101, "nearest pick preserves world ray t across different scales")
	_check(other.pick_obstacle(Vector3(0,0,1),Vector3.RIGHT) == 101, "ray starting inside returns positive exit")
	_check(other.pick_obstacle(Vector3(0,2,10),Vector3.FORWARD) == -1, "parallel-axis miss")
	_check(other.pick_obstacle(Vector3(0,0,10),Vector3.BACK) == -1, "all behind ray miss")
	items = [{"object_id":103,"kind":"water","position":Vector3.ZERO,"rotation_deg":Vector3.ZERO,"size":Vector3(6,4,2)}]
	other.sync_obstacles(parent,items)
	var box: AABB = other.local_visual_bounds(other.obstacle_node(103))
	_check(other.pick_obstacle(box.get_center()+Vector3(0,0,10),Vector3.FORWARD) == 103, "ray through shifted water local centre")
	other.obstacle_node(103).scale = Vector3.ZERO
	_check(other.pick_obstacle(Vector3(0,0,10),Vector3.FORWARD) == -1, "singular transform rejected before inverse")
	parent.free()

func _test_history_and_files(scene) -> void:
	var doc = scene.document
	var presenter = scene._asset_presenter
	var id := int(doc.obstacles[0].object_id)
	var original = presenter.obstacle_node(id)
	var old_position: Vector3 = original.position
	doc.select_object(id)
	doc.update_obstacle(id, {"position":Vector3(3,-3,4)})
	_check(presenter.obstacle_node(id) == original and original.position.x == 3, "transform edit reuses original instance")
	doc.undo()
	_check(original.position.is_equal_approx(old_position), "undo restores visual placement")
	doc.redo()
	_check(original.position.x == 3, "redo restores visual placement")
	var hash_before: String = doc.commitment_hash()
	var path := ProjectSettings.globalize_path("res://integration-layout.json")
	scene.shell._dialog_action = "save"
	scene.shell._on_file_selected(path)
	_check(scene.shell.last_file_result.get("ok",false), "nonempty save through shell")
	var text := FileAccess.get_file_as_string(path)
	for forbidden in ["res://","seed","material","collision","runtime"]:
		_check(not forbidden in text, "layout excludes " + forbidden)
	doc.reset_layout()
	scene.shell._dialog_action = "open"
	scene.shell._on_file_selected(path)
	await process_frame
	_check(scene.shell.last_file_result.get("ok",false) and doc.commitment_hash() == hash_before, "nonempty parameter round trip preserves commitment")
	for i in KINDS.size():
		var node = presenter.obstacle_node(doc.obstacles[i].object_id)
		_check(node != null and node.get_meta("asset_id") == "obstacle_"+KINDS[i]+"_v1", "reopen rebuilds each kind and ID")
	var previous = presenter.obstacle_node(doc.obstacles[0].object_id)
	var before: Transform3D = previous.transform
	var bad := FileAccess.open(ProjectSettings.globalize_path("res://invalid-layout.json"),FileAccess.WRITE)
	bad.store_string("{broken")
	bad.close()
	scene.shell._dialog_action = "open"
	scene.shell._on_file_selected(ProjectSettings.globalize_path("res://invalid-layout.json"))
	scene.shell._on_file_dialog_canceled()
	_check(doc.commitment_hash() == hash_before and presenter.obstacle_node(doc.obstacles[0].object_id) == previous and previous.transform == before, "invalid open and cancellation preserve exact visuals")
	# Same ID with changed kind must replace the node, never retain stale geometry.
	var changed: Array = doc.obstacles.duplicate(true)
	changed[0].kind = "hard_rock"
	changed[0].size = Vector3(3,3,3)
	var old_instance := previous.get_instance_id()
	presenter.sync_obstacles(scene._obstacle_root,changed)
	_check(presenter.obstacle_node(changed[0].object_id).get_instance_id() != old_instance, "reused ID changed kind replaces node")
	scene._sync_obstacles()

func _test_focus(scene, drills: Array) -> void:
	if drills.is_empty():
		return
	var drill: Node3D = drills[0]
	var transform_before: Transform3D = drill.global_transform
	var gates_before: String = var_to_str(scene.document.gates)
	var hash_before: String = scene.document.commitment_hash()
	var found := false
	for button in scene.shell._root.find_children("*","Button",true,false):
		if button.text == "聚焦钻头":
			found = true
	_check(found, "drill-focus camera button exists in shell")
	for rect in [Vector2i(1920,1080), Vector2i(1280,720)]:
		root.content_scale_size = rect
		root.size = rect
		await process_frame
		scene.shell._request_drill_focus()
		var box: AABB = scene._asset_presenter.world_visual_bounds(drill)
		var center := box.get_center()
		var radius := box.size.length()*.5
		var view_rect: Rect2 = scene._camera.get_viewport().get_visible_rect()
		var fits := true
		for offset in [scene._camera.global_basis.x*radius,-scene._camera.global_basis.x*radius,scene._camera.global_basis.y*radius,-scene._camera.global_basis.y*radius]:
			var point: Vector2 = scene._camera.unproject_position(center+offset)
			fits = fits and view_rect.grow(-10).has_point(point)
		_check(fits, "actual-scale drill sphere projects inside active viewport with margin " + str(rect))
	_check(scene._camera.near == .02 and scene._distance >= .5, "drill focus uses close-up near and finite minimum distance")
	_check(drill.global_transform == transform_before and var_to_str(scene.document.gates) == gates_before and scene.document.commitment_hash() == hash_before, "camera focus changes no geometry/gates/document")
	scene.document.select_object(-1)
	scene.focus_selected()
	_check(scene._distance == 52.0, "scene focus retains 52m reset")

func _test_budget(scene) -> void:
	var presenter = scene._asset_presenter
	var doc = scene.document
	doc.reset_layout()
	var cold_start := Time.get_ticks_usec()
	for i in 30:
		doc.add_obstacle(KINDS[i%5],Vector3((i%5)-2,0,(i/5)-2))
	var cold_us := Time.get_ticks_usec()-cold_start
	_check(doc.obstacle_count() == 30, "30 real mixed-kind document objects")
	var ids := []
	var mesh_ids := []
	var triangles := 0
	var mesh_count := 0
	for obstacle in doc.obstacles:
		var node = presenter.obstacle_node(obstacle.object_id)
		ids.append(node.get_instance_id())
		for mesh in node.find_children("*","MeshInstance3D",true,false):
			mesh_ids.append([mesh.mesh.get_instance_id(),mesh.material_override.get_instance_id()])
			triangles += mesh.mesh.get_faces().size()/3
			mesh_count += 1
	var calls = presenter.report().factory_calls.duplicate(true)
	var no_op: Array = []
	var transform_only: Array = []
	for i in 100:
		var start := Time.get_ticks_usec()
		scene._sync_obstacles()
		no_op.append(Time.get_ticks_usec()-start)
		start = Time.get_ticks_usec()
		doc.update_obstacle(int(doc.obstacles[0].object_id), {"rotation_deg":Vector3(0,i,0)},false)
		transform_only.append(Time.get_ticks_usec()-start)
	_check(presenter.report().factory_calls == calls, "100 no-op and transform updates make zero new factory calls")
	var after_mesh_ids := []
	var after_ids := []
	for obstacle in doc.obstacles:
		var node = presenter.obstacle_node(obstacle.object_id)
		after_ids.append(node.get_instance_id())
		for mesh in node.find_children("*","MeshInstance3D",true,false):
			after_mesh_ids.append([mesh.mesh.get_instance_id(),mesh.material_override.get_instance_id()])
	_check(ids == after_ids and mesh_ids == after_mesh_ids, "transform-only updates preserve roots, meshes and materials")
	no_op.sort()
	transform_only.sort()
	print("CPU_PRESENTATION " + JSON.stringify({"cold_create_us":cold_us,"noop_samples_us":no_op,"transform_samples_us":transform_only,"noop_median_us":no_op[50],"noop_max_us":no_op[-1],"transform_median_us":transform_only[50],"transform_max_us":transform_only[-1],"obstacle_meshes":mesh_count,"obstacle_triangles":triangles,"A_gates_meshes":6,"A_tick_meshes":15,"A_obstacle_labels":30,"factory_calls":calls}))
	for cycle in 10:
		doc.reset_layout()
		_check(scene._obstacle_root.get_child_count() == 0, "clear leaves no accumulated roots/labels cycle %d"%cycle)
		for i in 30:
			doc.add_obstacle(KINDS[i%5],Vector3.ZERO)
		_check(scene._obstacle_root.get_child_count() == 60, "one root and A label per ID cycle %d"%cycle)
	doc.reset_layout()
	_check(scene._obstacle_root.get_child_count() == 0, "final clear has no node growth")

extends SceneTree
var checks: int = 0
var failures: int = 0
const P = preload("res://viewer/asset_presenter.gd")
const B = preload("res://world/asset_library.gd")
const KINDS = ["water","hard_rock","fault","void","casing"]
const BASES = [Vector3(6,4,2),Vector3(3,3,3),Vector3(8,1,6),Vector3(4,3,3),Vector3(.8,.8,8)]
func _initialize() -> void: call_deferred("_run")
func check(ok: bool, label: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures += 1
func item(id: int, kind: String, pos: Vector3, rot: Vector3, size: Vector3) -> Dictionary:
	return {"object_id":id,"kind":kind,"position":pos,"rotation_deg":rot,"size":size}
func _run() -> void:
	var parent := Node3D.new()
	root.add_child(parent)
	# Rigid parent with nonuniform scale; child rotation creates global shear.
	var pr := Basis(Quaternion(Vector3.UP,.57)*Quaternion(Vector3.RIGHT,-.23)*Quaternion(Vector3.BACK,.19))
	parent.transform = Transform3D(Basis(pr.x*.7,pr.y*1.9,pr.z*1.3),Vector3(4,-2,7))
	var presenter = P.new()
	var items: Array = []
	var rotation := Vector3(23,-47,19)
	var q := Quaternion(Vector3.UP,deg_to_rad(rotation.y))*Quaternion(Vector3.RIGHT,deg_to_rad(rotation.x))*Quaternion(Vector3.BACK,deg_to_rad(rotation.z))
	for i in 5:
		items.append(item(i+1,KINDS[i],Vector3(i*2-4,-1,i-2),rotation,BASES[i]*Vector3(.55,1.6,1.2)))
	check(presenter.sync_obstacles(parent,items).ok,"all five real assets under transformed nonuniform parent")
	var resources: Array = []
	for i in 5:
		var node: Node3D = presenter.obstacle_node(i+1)
		var local_bounds: AABB = presenter.local_visual_bounds(node)
		var actual_bounds: AABB = presenter.world_visual_bounds(node)
		var vertex_ok := true
		var inside := true
		for mesh in node.find_children("*","MeshInstance3D",true,false):
			resources.append([node.get_instance_id(),mesh.mesh.get_instance_id(),mesh.material_override.get_instance_id()])
			for v in mesh.mesh.get_faces():
				var asset_local: Vector3 = mesh.transform * v
				var ancestor: Node = mesh.get_parent()
				while ancestor != node:
					asset_local = ancestor.transform * asset_local
					ancestor = ancestor.get_parent()
				var expected: Vector3 = parent.transform * (items[i].position + q * (asset_local*Vector3(.55,1.6,1.2)))
				var actual: Vector3 = mesh.global_transform * v
				vertex_ok = vertex_ok and actual.distance_to(expected) < .000015
				inside = inside and actual_bounds.grow(.000015).has_point(actual)
		check(vertex_ok,"independent quaternion transform of actual vertices "+KINDS[i])
		check(inside,"world visual bounds contain all actual vertices "+KINDS[i])
		check(node.position.is_equal_approx(items[i].position),"generator pivot retained "+KINDS[i])
		if i == 0: check(local_bounds.get_center().length()>.001,"water asymmetric local bounds preserved")
	var calls: Dictionary = presenter.report().factory_calls
	for round in 25:
		items[0].position.x += .01
		presenter.sync_obstacles(parent,items)
	var after: Array = []
	for i in 5:
		var node: Node3D = presenter.obstacle_node(i+1)
		for mesh in node.find_children("*","MeshInstance3D",true,false):
			after.append([node.get_instance_id(),mesh.mesh.get_instance_id(),mesh.material_override.get_instance_id()])
	check(after==resources and calls==presenter.report().factory_calls,"25 updates retain actual mesh/material instances and factories")
	# Reconcile reused identity through kind replacement, deletion and recovery.
	var old_id: int = presenter.obstacle_node(1).get_instance_id()
	items[0].kind = "casing"; items[0].size = Vector3(.8,.8,8)
	check(presenter.sync_obstacles(parent,items).ok,"changed kind reconciles")
	check(presenter.obstacle_node(1).get_instance_id()!=old_id and presenter.obstacle_node(1).get_meta("asset_id")=="obstacle_casing_v1","ID reuse replaces geometry")
	items[0].kind = "invalid"
	check(not presenter.sync_obstacles(parent,items).ok and presenter.obstacle_node(1)==null,"invalid kind removes stale previous geometry")
	items[0].kind = "hard_rock"; items[0].size = Vector3(3,3,3)
	check(presenter.sync_obstacles(parent,items).ok and presenter.obstacle_node(1)!=null,"kind repair recreates live geometry")
	presenter.sync_obstacles(parent,[])
	check(parent.get_child_count()==0 and presenter._nodes.is_empty() and presenter._failed_kinds.is_empty(),"clear empties success and failure caches")
	# Parent-space ray maps to world ray without normalizing inverse-local direction.
	var near_item := item(41,"fault",Vector3(0,0,6),Vector3.ZERO,Vector3(8,1,3))
	var far_item := item(42,"fault",Vector3.ZERO,Vector3.ZERO,Vector3(8,1,9))
	presenter.sync_obstacles(parent,[far_item,near_item])
	var origin: Vector3 = parent.global_transform * Vector3(0,0,25)
	var direction: Vector3 = (parent.global_basis*Vector3.FORWARD).normalized()
	check(presenter.pick_obstacle(origin,direction)==41,"nearest world t under rotated scaled translated parent")
	var t: float = presenter.obstacle_ray_t(41,origin,direction)
	check(absf(t-17.5*parent.global_basis.z.length())<.00002,"world ray distance retained under anisotropic parent")
	check(presenter.pick_obstacle(origin,-direction)==-1,"away ray misses under transformed parent")
	check(presenter.pick_obstacle(parent.global_transform*Vector3(0,3,25),direction)==-1,"parallel-axis miss under transformed parent")
	presenter.sync_obstacles(parent,[])
	for cycle in 12:
		presenter.sync_obstacles(parent,[near_item,far_item])
		presenter.sync_obstacles(parent,[])
		check(parent.get_child_count()==0 and presenter._nodes.is_empty(),"no cache/node growth cycle %d"%cycle)
	parent.free()
	_test_validation()
	await _test_actual_viewer()
	print("INDEPENDENT checks=%d failures=%d"%[checks,failures])
	quit(1 if failures else 0)
func _test_validation() -> void:
	var p = P.new()
	for mode in ["missing_visual","missing_license","bad_bounds_type","nan_bounds","zero_envelope","nan_transform","layer","mask","shape","polygon"]:
		var asset: Node3D = B.create_obstacle("water")
		match mode:
			"missing_visual": asset.get_node("Visual").free()
			"missing_license": asset.set_meta("source_license","")
			"bad_bounds_type": asset.set_meta("geometry_bounds_m",{"min":[],"max":Vector3.ONE})
			"nan_bounds": asset.set_meta("geometry_bounds_m",{"min":Vector3(NAN,0,0),"max":Vector3.ONE})
			"zero_envelope": asset.set_meta("declared_envelope",{"bounds_min":Vector3.ZERO,"bounds_max":Vector3.ZERO})
			"nan_transform": asset.get_node("Visual").position.x = NAN
			"layer": asset.find_children("*","CollisionObject3D",true,false)[0].collision_layer = 1
			"mask": asset.find_children("*","CollisionObject3D",true,false)[0].collision_mask = 1
			"shape": asset.find_children("*","CollisionShape3D",true,false)[0].disabled = false
			"polygon":
				var poly := CollisionPolygon3D.new()
				poly.disabled = false
				asset.get_node("Collision").add_child(poly)
		check(not p._validate_asset(asset).is_empty(),"reject malformed asset "+mode)
		asset.free()
func _test_actual_viewer() -> void:
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	var doc = scene.document
	var add: Dictionary = doc.add_obstacle("water",Vector3(2,-1,3))
	var id: int = add.id
	var nodes_before: int = scene._obstacle_root.get_child_count()
	var original = scene._asset_presenter.obstacle_node(id)
	var encoded: String = doc.export_layout_text()
	check(not encoded.contains("res://") and not encoded.contains("geometry_bounds_m") and not encoded.contains("factory_calls"),"export stays parameter-only")
	var invalid: Dictionary = doc.apply_layout_text(encoded.replace('"water"','"res://evil.gd"'))
	check(not invalid.ok and scene._asset_presenter.obstacle_node(id)==original and scene._obstacle_root.get_child_count()==nodes_before,"resource-path injection rejected without scene mutation")
	var hash_before: String = doc.commitment_hash()
	var transformed := Transform3D(Basis(Quaternion(Vector3.UP,.4)),Vector3(3,2,-4))
	scene._world.transform = transformed
	doc.update_obstacle(id,{"rotation_deg":Vector3(17,28,9),"size":Vector3(4,3,1.4)})
	var box: AABB = scene._asset_presenter.world_visual_bounds(original)
	var label: Label3D = scene._obstacle_labels[id]
	check(label.global_position.distance_to(Vector3(box.get_center().x,box.end.y+.7,box.get_center().z))<.00002,"actual viewer label follows transformed world visual bounds")
	check(not doc.control_bridge_connected and not doc.is_motion_active() and scene.shell._run_button.disabled and scene.shell._pause_button.disabled and scene.shell._continue_button.disabled,"no presentation authority or running state")
	check(hash_before!=doc.commitment_hash(),"transform remains document parameter change")
	scene.free()
	await process_frame

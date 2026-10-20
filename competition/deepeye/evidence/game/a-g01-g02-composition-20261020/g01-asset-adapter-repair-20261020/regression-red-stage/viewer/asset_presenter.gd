class_name DeepEyeAssetPresenter
extends RefCounted
## Observer presentation only. Disabled B envelopes are never authority shapes.
## Document parameters stay in SceneDocument; no resources/control truth exported.

const FACTORY_PATH := "res://world/asset_library.gd"
const REQUIRED_FILES := [FACTORY_PATH, "res://world/drill_geometry.gd", "res://world/obstacle_geometry.gd", "res://world/frame_geometry.gd"]
const KINDS := ["water", "hard_rock", "fault", "void", "casing"]
var _factory: Script
var _load_attempted := false
var _diagnostics: Array[String] = []
var _nodes := {}
var _kinds := {}
var _failed_kinds := {}
var _factory_calls := {"frame":0,"drill":0,"obstacle":0}
var _frame: Node3D
var _drill: Node3D

func _diagnose(message: String) -> void:
	if not _diagnostics.has(message):
		_diagnostics.append(message)

func _ensure_factory() -> bool:
	if _load_attempted:
		return _factory != null
	_load_attempted = true
	for path in REQUIRED_FILES:
		if not FileAccess.file_exists(path):
			_diagnose("资源加载失败·开发灰盒: 缺少固定资源 " + path)
			return false
	var resource = load(FACTORY_PATH)
	if not resource is Script or not resource.can_instantiate():
		_diagnose("资源加载失败·开发灰盒: 固定工厂脚本不可用")
		return false
	var methods := {}
	for method in resource.get_script_method_list():
		methods[String(method.name)] = int(method.flags)
	for name in ["create_frame", "create_drill", "create_obstacle"]:
		if not methods.has(name) or (methods[name] & METHOD_FLAG_STATIC) == 0:
			_diagnose("资源加载失败·开发灰盒: 工厂缺少静态方法 " + name)
			return false
	_factory = resource
	return true

func create_frame() -> Node3D:
	if is_instance_valid(_frame):
		return _frame
	_frame = _create("frame")
	return _frame

func create_drill() -> Node3D:
	if is_instance_valid(_drill):
		return _drill
	_drill = _create("drill")
	return _drill

func _create(category: String, kind: String = "") -> Node3D:
	if not _ensure_factory():
		return null
	_factory_calls[category] += 1
	var result = _factory.call("create_obstacle", kind) if category == "obstacle" else _factory.call("create_" + category)
	var error := "工厂没有返回 Node3D"
	if result is Node3D:
		error = _validate_asset(result)
		var wanted := "obstacle_" + kind + "_v1" if category == "obstacle" else ("drill_pdc_v1" if category == "drill" else "frame_workspace_v1")
		if error.is_empty() and result.get_meta("asset_id", "") != wanted:
			error = "资源种类标识不匹配"
	if not error.is_empty():
		_diagnose("资源加载失败·开发灰盒: " + category + ("/"+kind if not kind.is_empty() else "") + ": " + error)
		if result is Node and result.get_parent() == null:
			result.free()
		return null
	return result as Node3D

func _validate_asset(asset: Node3D) -> String:
	if asset.get_parent() != null:
		return "资源已附着到其它父节点"
	if not asset.get_node_or_null("Visual") is Node3D or not asset.get_node_or_null("Collision") is Node3D:
		return "缺少 Visual/Collision 子节点"
	if asset.get_meta("asset_contract_version",0) != 1 or String(asset.get_meta("source_license", "")).is_empty():
		return "版本或来源许可缺失"
	var measured = asset.get_meta("geometry_bounds_m",null)
	var declared = asset.get_meta("declared_envelope",null)
	if not measured is Dictionary or not declared is Dictionary:
		return "局部边界或名义包络缺失"
	for bounds in [measured, {"min":declared.get("bounds_min"),"max":declared.get("bounds_max")}]:
		if not bounds.get("min") is Vector3 or not bounds.get("max") is Vector3:
			return "边界类型错误"
		var low: Vector3 = bounds.min
		var high: Vector3 = bounds.max
		if not low.is_finite() or not high.is_finite() or not _positive(high-low):
			return "边界非有限或没有正体积"
	var radius = asset.get_meta("pivot_bound_radius_m",null)
	if not (radius is float or radius is int) or not is_finite(float(radius)) or float(radius) <= 0.0:
		return "枢轴半径无效"
	return _validate_tree(asset)

func _validate_tree(node: Node) -> String:
	if node.get_script() != null:
		return "资源节点附有脚本"
	if node is Node3D and not node.transform.is_finite():
		return "资源节点变换非有限"
	if node is CollisionObject3D and (node.collision_layer != 0 or node.collision_mask != 0):
		return "碰撞层或掩码已启用"
	if node is CollisionShape3D and not node.disabled:
		return "碰撞形状已启用"
	if node is CollisionPolygon3D and not node.disabled:
		return "碰撞多边形已启用"
	for child in node.get_children():
		var error := _validate_tree(child)
		if not error.is_empty():
			return error
	return ""

func _positive(size: Vector3) -> bool:
	return size.is_finite() and size.x > 0.0 and size.y > 0.0 and size.z > 0.0

func _obstacle_transform(obstacle: Dictionary, base_size: Vector3) -> Transform3D:
	var scale: Vector3 = obstacle.size / base_size
	var rotation := Basis.from_euler(obstacle.rotation_deg * (PI / 180.0))
	return Transform3D(Basis(rotation.x*scale.x, rotation.y*scale.y, rotation.z*scale.z), obstacle.position)

func sync_obstacles(parent: Node3D, obstacles: Array) -> Dictionary:
	var live := {}
	var failed: Array[int] = []
	for obstacle in obstacles:
		var id := int(obstacle.object_id)
		var kind := String(obstacle.kind)
		live[id] = true
		if _nodes.has(id) and _kinds[id] != kind:
			_remove(id)
		if _failed_kinds.has(id) and _failed_kinds[id] != kind:
			_failed_kinds.erase(id)
		if not _nodes.has(id) and not _failed_kinds.has(id):
			var node: Node3D
			if KINDS.has(kind):
				node = _create("obstacle",kind)
			else:
				_diagnose("资源加载失败·开发灰盒: 未知障碍种类 " + kind)
			if node != null:
				_nodes[id] = node
				_kinds[id] = kind
				parent.add_child(node)
			else:
				_failed_kinds[id] = kind
		var asset: Node3D = obstacle_node(id)
		if asset == null:
			failed.append(id)
			continue
		var envelope: Dictionary = asset.get_meta("declared_envelope")
		var base_size: Vector3 = envelope.bounds_max-envelope.bounds_min
		if not _positive(obstacle.size) or not obstacle.position.is_finite() or not obstacle.rotation_deg.is_finite():
			_diagnose("资源加载失败·开发灰盒: 障碍 #%d 参数无效" % id)
			_remove(id)
			_failed_kinds[id] = kind
			failed.append(id)
			continue
		asset.transform = _obstacle_transform(obstacle,base_size)
	for id in _nodes.keys():
		if not live.has(id):
			_remove(id)
	for id in _failed_kinds.keys():
		if not live.has(id):
			_failed_kinds.erase(id)
	return {"ok":failed.is_empty(),"failed_ids":failed,"diagnostics":_diagnostics.duplicate()}

func _remove(id: int) -> void:
	var node: Node3D = _nodes[id]
	if is_instance_valid(node):
		node.get_parent().remove_child(node)
		node.free()
	_nodes.erase(id)
	_kinds.erase(id)

func obstacle_node(object_id: int) -> Node3D:
	return _nodes.get(object_id,null)

func local_visual_bounds(asset: Node3D) -> AABB:
	var measured: Dictionary = asset.get_meta("geometry_bounds_m")
	return AABB(measured.min, measured.max-measured.min)

func world_visual_bounds(asset: Node3D) -> AABB:
	var local := local_visual_bounds(asset)
	var world := AABB(asset.global_transform*local.get_endpoint(0),Vector3.ZERO)
	for corner in range(1,8):
		world = world.expand(asset.global_transform*local.get_endpoint(corner))
	return world

func obstacle_ray_t(object_id: int, ray_origin_world: Vector3, ray_direction_world: Vector3) -> float:
	var node := obstacle_node(object_id)
	if node == null or not node.global_transform.is_finite() or absf(node.global_basis.determinant()) < 1e-12:
		return -1.0
	var inverse := node.global_transform.affine_inverse()
	# Keep local direction unnormalized: t remains world-ray distance.
	return _ray_aabb_t(inverse*ray_origin_world, inverse.basis*ray_direction_world, local_visual_bounds(node))

func pick_obstacle(ray_origin_world: Vector3, ray_direction_world: Vector3) -> int:
	var nearest := -1
	var nearest_t := INF
	for id in _nodes:
		var t := obstacle_ray_t(id,ray_origin_world,ray_direction_world)
		if t >= 0.0 and t < nearest_t:
			nearest = id
			nearest_t = t
	return nearest

func _ray_aabb_t(origin: Vector3, direction: Vector3, box: AABB) -> float:
	var low := -INF
	var high := INF
	for axis in 3:
		if absf(direction[axis]) < 1e-12:
			if origin[axis] < box.position[axis] or origin[axis] > box.end[axis]:
				return -1.0
		else:
			var t1: float = (box.position[axis]-origin[axis])/direction[axis]
			var t2: float = (box.end[axis]-origin[axis])/direction[axis]
			low = maxf(low,minf(t1,t2))
			high = minf(high,maxf(t1,t2))
	if high < maxf(low,0.0):
		return -1.0
	return low if low > 0.0 else high

func report() -> Dictionary:
	return {"state":"ready" if _diagnostics.is_empty() and _factory != null else "degraded", "diagnostics":_diagnostics.duplicate(),"factory_calls":_factory_calls.duplicate()}

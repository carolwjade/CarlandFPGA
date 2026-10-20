class_name DeepEyeViewerMain
extends Node3D
## G02 viewer foundation (A-only, viewer baseline):
##  - 12-edge hollow cube frame + corner ticks over the frozen [-15,15]^3 work cube,
##    blue entry / red exit 0.30 m circles with text and direction arrows.
##  - Editing via the SceneDocument: click select, drag move (0.25 m snap, axis lock),
##    R rotate / S scale / F focus, numeric fields, copy/delete, undo/redo, random
##    layout, six-face gate picking.
##  - Camera: RMB orbit, MMB pan, wheel zoom, six views, isometric, focus. Mouse
##    input over any UI panel never moves the camera (_unhandled_input + hover check).
##  - No physics bodies, no drill motion, no timeline, no fabricated link state.
##    Run/continue remain disabled; Esc only emits stop_requested via the document.

const DocScript = preload("res://editor/scene_document.gd")

var document
var shell

var _camera: Camera3D
var _world: Node3D
var _obstacle_root: Node3D
var _gate_root: Node3D
var _ticks_root: Node3D
var _drill_root: Node3D
var _selection_box: MeshInstance3D
var _material_cache: Dictionary = {}

var _focus_point := Vector3.ZERO
var _yaw_deg := 35.0
var _pitch_deg := 24.0
var _distance := 52.0
var _orbiting := false
var _panning := false
var _dragging := false
var _drag_moved := false
var _drag_checkpoint_pushed := false
var _drag_plane_y := 0.0
var _drag_offset := Vector3.ZERO
var _drag_object_id := -1

func _ready() -> void:
	document = DocScript.new()
	_world = $World
	_obstacle_root = Node3D.new()
	_obstacle_root.name = "Obstacles"
	_world.add_child(_obstacle_root)
	_gate_root = Node3D.new()
	_gate_root.name = "Gates"
	_world.add_child(_gate_root)
	_build_frame()
	_build_ticks()
	_build_drill_greybox()
	_selection_box = MeshInstance3D.new()
	_selection_box.name = "SelectionBox"
	var selection_mesh := BoxMesh.new()
	selection_mesh.size = Vector3.ONE
	_selection_box.mesh = selection_mesh
	var selection_material := StandardMaterial3D.new()
	selection_material.albedo_color = Color(0.2, 0.95, 1.0, 0.30)
	selection_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	selection_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	selection_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	_selection_box.material_override = selection_material
	_selection_box.visible = false
	_world.add_child(_selection_box)
	_camera = $Camera3D
	shell = $Shell
	shell.bind_editor(self, document)
	document.layout_changed.connect(_sync_obstacles)
	document.gates_changed.connect(_sync_gates)
	document.selection_changed.connect(_on_selection_changed)
	_sync_obstacles()
	_sync_gates()
	apply_camera()
	document.log_event("系统", "World 视图就绪：12条边+角标+坐标刻度；障碍为开发灰盒；蓝/红圈0.30m；无物理、无运动（运行禁用）")

# ---------------------------------------------------------------------------
# Input (camera + editing). Esc is global; everything else ignores UI hover.
# ---------------------------------------------------------------------------

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		document.request_stop("Esc")
		get_viewport().set_input_as_handled()

func _pointer_over_ui() -> bool:
	var viewport := get_viewport()
	return viewport != null and viewport.gui_get_hovered_control() != null

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.pressed and _pointer_over_ui():
			return
		_handle_mouse_button(event)
	elif event is InputEventMouseMotion:
		if _pointer_over_ui():
			return
		_handle_mouse_motion(event)

func _unhandled_key_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	if document == null:
		return
	if event.keycode == KEY_F:
		focus_selected()
		return
	if document.selected_id == -1 or not document.can_edit():
		return
	var focus_owner := get_viewport().gui_get_focus_owner()
	if focus_owner is LineEdit or focus_owner is SpinBox or focus_owner is TextEdit:
		return
	var obstacle: Dictionary = document.obstacle_by_id(document.selected_id)
	if obstacle.is_empty():
		return
	match event.keycode:
		KEY_R:
			var rotation: Vector3 = obstacle.rotation_deg
			var step := -15.0 if event.shift_pressed else 15.0
			rotation.y = wrapf(rotation.y + step, -180.0, 180.0)
			document.update_obstacle(document.selected_id, {"rotation_deg": rotation})
		KEY_S:
			var factor := 0.9 if event.shift_pressed else 1.1
			document.update_obstacle(document.selected_id, {"size": obstacle.size * factor})

func _handle_mouse_button(event: InputEventMouseButton) -> void:
	match event.button_index:
		MOUSE_BUTTON_LEFT:
			if event.pressed:
				if event.double_click:
					_focus_at_screen_point(event.position)
				else:
					_left_press(event.position)
			else:
				_left_release()
		MOUSE_BUTTON_RIGHT:
			_orbiting = event.pressed
		MOUSE_BUTTON_MIDDLE:
			_panning = event.pressed
		MOUSE_BUTTON_WHEEL_UP:
			if event.pressed:
				_distance = clampf(_distance * 0.89, 1.5, 260.0)
				apply_camera()
		MOUSE_BUTTON_WHEEL_DOWN:
			if event.pressed:
				_distance = clampf(_distance * 1.12, 1.5, 260.0)
				apply_camera()

func _handle_mouse_motion(event: InputEventMouseMotion) -> void:
	if _orbiting:
		_yaw_deg = wrapf(_yaw_deg + event.relative.x * 0.28, -180.0, 180.0)
		_pitch_deg = clampf(_pitch_deg + event.relative.y * 0.28, -89.5, 89.5)
		apply_camera()
	elif _panning:
		var right := _camera.global_transform.basis.x
		var up := _camera.global_transform.basis.y
		var pan_scale := _distance * 0.0016
		_focus_point -= right * event.relative.x * pan_scale
		_focus_point += up * event.relative.y * pan_scale
		apply_camera()
	elif _dragging and _drag_object_id >= 0:
		var hit = _ray_plane_y_at(event.position, _drag_plane_y)
		if hit != null:
			var obstacle: Dictionary = document.obstacle_by_id(_drag_object_id)
			if obstacle.is_empty():
				return
			var target: Vector3 = hit + _drag_offset
			target = _apply_axis_lock(target, obstacle.position)
			if shell != null and shell.snap_enabled:
				target = target.snapped(Vector3(0.25, 0.25, 0.25))
			if not _drag_checkpoint_pushed:
				document.push_undo_checkpoint()
				_drag_checkpoint_pushed = true
			var result: Dictionary = document.update_obstacle(_drag_object_id, {"position": target}, false)
			if bool(result.get("ok", false)):
				_drag_moved = true

func _left_press(screen_pos: Vector2) -> void:
	var mode: String = shell.pick_mode if shell != null else "select"
	if mode == "gate":
		_pick_face_and_set_gate(screen_pos)
		return
	if mode == "add":
		var hit = _ray_plane_y_at(screen_pos, 0.0)
		if hit != null:
			var result: Dictionary = document.add_obstacle(shell.current_kind(), hit)
			if bool(result.get("ok", false)):
				document.select_object(int(result.get("id", -1)))
		return
	var picked := _pick_object(screen_pos)
	if picked >= 0:
		document.select_object(picked)
		_dragging = true
		_drag_moved = false
		_drag_checkpoint_pushed = false
		_drag_object_id = picked
		var obstacle: Dictionary = document.obstacle_by_id(picked)
		_drag_plane_y = obstacle.position.y
		var hit_point = _ray_plane_y_at(screen_pos, _drag_plane_y)
		_drag_offset = Vector3.ZERO if hit_point == null else obstacle.position - hit_point
	else:
		document.select_object(-1)

func _left_release() -> void:
	if _dragging and _drag_moved:
		document.log_event("操作", "拖拽移动完成（0.25m吸附=%s，轴锁定=%s）" % [
			"开" if shell != null and shell.snap_enabled else "关",
			shell.axis_lock if shell != null else "free"])
	_dragging = false
	_drag_object_id = -1
	_drag_moved = false
	_drag_checkpoint_pushed = false

func _apply_axis_lock(target: Vector3, current: Vector3) -> Vector3:
	var lock_mode: String = shell.axis_lock if shell != null else "free"
	match lock_mode:
		"x":
			target.y = current.y
			target.z = current.z
		"y":
			target.x = current.x
			target.z = current.z
		"z":
			target.x = current.x
			target.y = current.y
	return target

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

func apply_camera() -> void:
	if _camera == null:
		return
	var yaw := deg_to_rad(_yaw_deg)
	var pitch := deg_to_rad(_pitch_deg)
	var direction := Vector3(cos(pitch) * sin(yaw), sin(pitch), cos(pitch) * cos(yaw))
	_camera.position = _focus_point + direction * _distance
	_camera.look_at(_focus_point, Vector3.UP)

func set_camera_view(view_name: String) -> void:
	match view_name:
		"top":
			_yaw_deg = 0.0
			_pitch_deg = 89.4
		"bottom":
			_yaw_deg = 0.0
			_pitch_deg = -89.4
		"front":
			_yaw_deg = 0.0
			_pitch_deg = 0.0
		"back":
			_yaw_deg = 180.0
			_pitch_deg = 0.0
		"left":
			_yaw_deg = -90.0
			_pitch_deg = 0.0
		"right":
			_yaw_deg = 90.0
			_pitch_deg = 0.0
		"iso":
			_yaw_deg = 45.0
			_pitch_deg = 35.264
		_:
			return
	apply_camera()
	document.log_event("操作", "相机切换: %s（仅相机；世界/传感器未改变）" % view_name)

func focus_selected() -> void:
	if document == null:
		return
	var obstacle: Dictionary = document.obstacle_by_id(document.selected_id) if document.selected_id != -1 else {}
	if obstacle.is_empty():
		_focus_point = Vector3.ZERO
		_distance = 52.0
		document.log_event("操作", "聚焦场景中心（无选中对象）")
	else:
		_focus_point = obstacle.position
		var extent: Vector3 = obstacle.size
		_distance = clampf(maxf(extent.x, maxf(extent.y, extent.z)) * 2.6 + 6.0, 3.0, 120.0)
		document.log_event("操作", "聚焦选中对象 #%d" % document.selected_id)
	apply_camera()

func _focus_at_screen_point(screen_pos: Vector2) -> void:
	var picked := _pick_object(screen_pos)
	if picked >= 0:
		document.select_object(picked)
		focus_selected()
		return
	var hit = _ray_plane_y_at(screen_pos, 0.0)
	if hit != null:
		_focus_point = hit
		apply_camera()

# ---------------------------------------------------------------------------
# Picking (pure math, no physics bodies)
# ---------------------------------------------------------------------------

func _ray(screen_pos: Vector2) -> Dictionary:
	return {
		"from": _camera.project_ray_origin(screen_pos),
		"dir": _camera.project_ray_normal(screen_pos),
	}

func _pick_object(screen_pos: Vector2) -> int:
	var ray := _ray(screen_pos)
	var from: Vector3 = ray["from"]
	var direction: Vector3 = ray["dir"]
	var best_id := -1
	var best_t := INF
	for obstacle in document.obstacles:
		var half: Vector3 = document.world_half_extent(obstacle.size, obstacle.rotation_deg)
		var t := _ray_hits_aabb(from, direction, obstacle.position, half)
		if t >= 0.0 and t < best_t:
			best_t = t
			best_id = int(obstacle.object_id)
	return best_id

func _ray_hits_aabb(from: Vector3, direction: Vector3, center: Vector3, half: Vector3) -> float:
	var origin := from - center
	var tmin := -INF
	var tmax := INF
	if absf(direction.x) < 0.000000001:
		if absf(origin.x) > half.x:
			return -1.0
	else:
		var t1 := (-half.x - origin.x) / direction.x
		var t2 := (half.x - origin.x) / direction.x
		tmin = maxf(tmin, minf(t1, t2))
		tmax = minf(tmax, maxf(t1, t2))
	if absf(direction.y) < 0.000000001:
		if absf(origin.y) > half.y:
			return -1.0
	else:
		var t3 := (-half.y - origin.y) / direction.y
		var t4 := (half.y - origin.y) / direction.y
		tmin = maxf(tmin, minf(t3, t4))
		tmax = minf(tmax, maxf(t3, t4))
	if absf(direction.z) < 0.000000001:
		if absf(origin.z) > half.z:
			return -1.0
	else:
		var t5 := (-half.z - origin.z) / direction.z
		var t6 := (half.z - origin.z) / direction.z
		tmin = maxf(tmin, minf(t5, t6))
		tmax = minf(tmax, maxf(t5, t6))
	if tmax < maxf(tmin, 0.0):
		return -1.0
	return tmin if tmin > 0.0 else tmax

func _ray_plane_y_at(screen_pos: Vector2, plane_y: float):
	var ray := _ray(screen_pos)
	var from: Vector3 = ray["from"]
	var direction: Vector3 = ray["dir"]
	if absf(direction.y) < 0.000001:
		return null
	var t := (plane_y - from.y) / direction.y
	if t <= 0.0:
		return null
	return from + direction * t

func _pick_face(screen_pos: Vector2) -> Dictionary:
	var ray := _ray(screen_pos)
	var from: Vector3 = ray["from"]
	var direction: Vector3 = ray["dir"]
	var best := {}
	var best_t := INF
	for face in DocScript.FACES:
		var normal: Vector3 = DocScript.FACE_NORMALS[face]
		var denom := direction.dot(normal)
		if absf(denom) < 0.000000001:
			continue
		var t := (DocScript.CUBE_HALF - from.dot(normal)) / denom
		if t <= 0.0 or t >= best_t:
			continue
		var point := from + direction * t
		var inside := true
		for axis in 3:
			if absf(point[axis]) > DocScript.CUBE_HALF + 0.000001:
				inside = false
				break
		if inside:
			best_t = t
			best = {"face": face, "point": point}
	return best

func _face_uv(face: String, point: Vector3) -> Vector2:
	match face:
		"top", "bottom":
			return Vector2(point.x, point.z)
		"front", "back":
			return Vector2(point.x, point.y)
		"left", "right":
			return Vector2(point.z, point.y)
		_:
			return Vector2.ZERO

func _pick_face_and_set_gate(screen_pos: Vector2) -> void:
	var hit := _pick_face(screen_pos)
	if hit.is_empty():
		document.log_event("提示", "未命中立方体面：圈心未改变（不自动移动任何圈）")
		return
	var uv := _face_uv(String(hit["face"]), hit["point"])
	var result: Dictionary = document.set_gate(shell.active_gate, String(hit["face"]),
		snappedf(uv.x, 0.05), snappedf(uv.y, 0.05))
	if shell != null:
		shell.on_gate_result(result, "拾取")

# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------

func _flat_material(color: Color, emission_energy: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.85
	if emission_energy > 0.0:
		material.emission_enabled = true
		material.emission = color
		material.emission_energy_multiplier = emission_energy
	return material

func _build_frame() -> void:
	var edge_material := _flat_material(Color(0.55, 0.62, 0.72), 0.05)
	var corner_material := _flat_material(Color(0.35, 0.85, 0.95), 0.4)
	var half := DocScript.CUBE_HALF
	var thickness := 0.07
	for axis in 3:
		for a in [-1.0, 1.0]:
			for b in [-1.0, 1.0]:
				var size := Vector3.ZERO
				var offset := Vector3.ZERO
				match axis:
					0:
						size = Vector3(half * 2.0, thickness, thickness)
						offset = Vector3(0.0, a * half, b * half)
					1:
						size = Vector3(thickness, half * 2.0, thickness)
						offset = Vector3(a * half, 0.0, b * half)
					_:
						size = Vector3(thickness, thickness, half * 2.0)
						offset = Vector3(a * half, b * half, 0.0)
				var edge := MeshInstance3D.new()
				var mesh := BoxMesh.new()
				mesh.size = size
				edge.mesh = mesh
				edge.material_override = edge_material
				edge.position = offset
				_world.add_child(edge)
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				var corner := MeshInstance3D.new()
				var mesh := BoxMesh.new()
				mesh.size = Vector3(0.36, 0.36, 0.36)
				corner.mesh = mesh
				corner.material_override = corner_material
				corner.position = Vector3(sx * half, sy * half, sz * half)
				_world.add_child(corner)

func _build_ticks() -> void:
	_ticks_root = Node3D.new()
	_ticks_root.name = "Ticks"
	_world.add_child(_ticks_root)
	var material := _flat_material(Color(0.75, 0.8, 0.85), 0.0)
	for value in range(-10, 11, 5):
		_add_tick(Vector3(float(value), -DocScript.CUBE_HALF, DocScript.CUBE_HALF), "X=%d" % value, material)
		_add_tick(Vector3(DocScript.CUBE_HALF, -DocScript.CUBE_HALF, float(value)), "Z=%d" % value, material)
		_add_tick(Vector3(-DocScript.CUBE_HALF, float(value), DocScript.CUBE_HALF), "Y=%d" % value, material)

func _add_tick(position: Vector3, text: String, material: Material) -> void:
	var mark := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(0.18, 0.18, 0.18)
	mark.mesh = mesh
	mark.material_override = material
	mark.position = position
	_ticks_root.add_child(mark)
	var label := Label3D.new()
	label.text = text
	label.font_size = 28
	label.pixel_size = 0.012
	label.modulate = Color(0.8, 0.85, 0.9)
	label.outline_size = 6
	label.position = position + Vector3(0.0, 0.45, 0.0)
	_ticks_root.add_child(label)

func set_ticks_visible(visible_state: bool) -> void:
	if _ticks_root != null:
		_ticks_root.visible = visible_state
		document.log_event("操作", "坐标刻度显示: %s" % ("开" if visible_state else "关"))

func _build_drill_greybox() -> void:
	_drill_root = Node3D.new()
	_drill_root.name = "DrillGreybox"
	_world.add_child(_drill_root)
	var body_material := StandardMaterial3D.new()
	body_material.albedo_color = Color(0.62, 0.66, 0.72)
	body_material.metallic = 0.8
	body_material.roughness = 0.4
	var body := MeshInstance3D.new()
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = 0.12
	cylinder.bottom_radius = 0.12
	# Complete greybox is .80m about the pivot: body[-.40,.18], head[.18,.40].
	cylinder.height = 0.58
	body.mesh = cylinder
	body.material_override = body_material
	body.quaternion = Quaternion(Vector3.UP, Vector3.BACK)
	body.position = Vector3(0.0, 0.0, -0.11)
	_drill_root.add_child(body)
	var tip := MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = 0.12
	cone.height = 0.22
	tip.mesh = cone
	tip.material_override = body_material
	tip.quaternion = Quaternion(Vector3.UP, Vector3.BACK)
	tip.position = Vector3(0.0, 0.0, 0.29)
	_drill_root.add_child(tip)
	var label := Label3D.new()
	label.text = "开发灰盒·钻头（静态；无运动）"
	label.font_size = 30
	label.pixel_size = 0.009
	label.modulate = Color(0.95, 0.9, 0.6)
	label.outline_size = 8
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.position = Vector3(0.0, 0.8, 0.0)
	_drill_root.add_child(label)

func _kind_material(kind: String) -> StandardMaterial3D:
	if _material_cache.has(kind):
		return _material_cache[kind]
	var material := StandardMaterial3D.new()
	match kind:
		"water":
			material.albedo_color = Color(0.15, 0.42, 0.85, 0.55)
			material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		"hard_rock":
			material.albedo_color = Color(0.46, 0.43, 0.38)
			material.roughness = 0.95
		"fault":
			material.albedo_color = Color(0.72, 0.45, 0.22, 0.8)
			material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			material.roughness = 0.9
		"void":
			material.albedo_color = Color(0.09, 0.09, 0.12)
			material.roughness = 1.0
		"casing":
			material.albedo_color = Color(0.72, 0.75, 0.78)
			material.metallic = 0.85
			material.roughness = 0.35
		_:
			material.albedo_color = Color(0.6, 0.6, 0.6)
	_material_cache[kind] = material
	return material

func _sync_obstacles() -> void:
	for child in _obstacle_root.get_children():
		_obstacle_root.remove_child(child)
		child.free()
	for obstacle in document.obstacles:
		var box := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = obstacle.size
		box.mesh = mesh
		box.material_override = _kind_material(String(obstacle.kind))
		box.position = obstacle.position
		box.rotation_degrees = obstacle.rotation_deg
		_obstacle_root.add_child(box)
		var label := Label3D.new()
		label.text = "开发灰盒·" + String(DocScript.KIND_LABELS[String(obstacle.kind)])
		label.font_size = 30
		label.pixel_size = 0.009
		label.modulate = Color(0.95, 0.9, 0.6)
		label.outline_size = 8
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.position = obstacle.position + Vector3(0.0, obstacle.size.y * 0.5 + 0.7, 0.0)
		_obstacle_root.add_child(label)
	_sync_selection_box()

func _on_selection_changed(_object_id: int) -> void:
	_sync_selection_box()

func _sync_selection_box() -> void:
	if _selection_box == null:
		return
	var obstacle: Dictionary = document.obstacle_by_id(document.selected_id) if document.selected_id != -1 else {}
	if obstacle.is_empty():
		_selection_box.visible = false
		return
	_selection_box.visible = true
	_selection_box.position = obstacle.position
	_selection_box.rotation_degrees = obstacle.rotation_deg
	_selection_box.scale = obstacle.size * 1.08 + Vector3(0.15, 0.15, 0.15)

func _sync_gates() -> void:
	for child in _gate_root.get_children():
		_gate_root.remove_child(child)
		child.free()
	for which in ["entry", "exit"]:
		_build_gate_visual(which)

func _build_gate_visual(which: String) -> void:
	var is_entry := which == "entry"
	var color := Color(0.15, 0.45, 1.0, 1.0) if is_entry else Color(1.0, 0.25, 0.2, 1.0)
	var gate_node := Node3D.new()
	gate_node.name = "Gate_" + which
	gate_node.position = document.gate_position(which)
	gate_node.quaternion = Quaternion(Vector3.UP, document.gate_normal(which))
	_gate_root.add_child(gate_node)
	var ring_material := StandardMaterial3D.new()
	ring_material.albedo_color = color
	ring_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring_material.emission_enabled = true
	ring_material.emission = color
	ring_material.emission_energy_multiplier = 1.4
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.135
	torus.outer_radius = 0.165
	ring.mesh = torus
	ring.material_override = ring_material
	gate_node.add_child(ring)
	var disc := MeshInstance3D.new()
	var disc_mesh := CylinderMesh.new()
	disc_mesh.top_radius = 0.15
	disc_mesh.bottom_radius = 0.15
	disc_mesh.height = 0.005
	var disc_material := StandardMaterial3D.new()
	disc_material.albedo_color = Color(color.r, color.g, color.b, 0.22)
	disc_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	disc_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	disc.mesh = disc_mesh
	disc.material_override = disc_material
	gate_node.add_child(disc)
	var label := Label3D.new()
	label.text = "进入（蓝圈 0.30m）" if is_entry else "离开（红圈 0.30m）"
	label.font_size = 34
	label.pixel_size = 0.009
	label.modulate = color
	label.outline_size = 8
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.position = Vector3(0.0, 0.34, 0.0)
	gate_node.add_child(label)
	var local_direction := Vector3(0.0, -1.0, 0.0) if is_entry else Vector3(0.0, 1.0, 0.0)
	var arrow := MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = 0.05
	cone.height = 0.5
	arrow.mesh = cone
	arrow.material_override = ring_material
	arrow.quaternion = Quaternion(Vector3.UP, local_direction)
	arrow.position = local_direction * 0.45
	gate_node.add_child(arrow)

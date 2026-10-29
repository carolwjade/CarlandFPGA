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
##  - B presentation collision bodies/shapes stay disabled; no authority physics,
##    autonomous drill motion, timeline or fabricated link state.
##    Explicit renderer-only frames and token-owned frozen-world publications
##    use exclusive entry modes; neither enables production Run.
##    Run/continue remain disabled; Esc only emits stop_requested via the document.

const DocScript = preload("res://editor/scene_document.gd")
const PresenterScript = preload("res://viewer/asset_presenter.gd")
const AuthorityPoseBridgeScript = preload("res://viewer/authority_pose_bridge.gd")

var document: RefCounted
var shell: CanvasLayer

var _camera: Camera3D
var _world: Node3D
var _obstacle_root: Node3D
var _gate_root: Node3D
var _ticks_root: Node3D
var _drill_root: Node3D
var _authority_pose_bridge = null
var _selection_box: MeshInstance3D
var _material_cache: Dictionary = {}
var _asset_presenter: RefCounted
var _obstacle_labels: Dictionary = {}
var _fallback_obstacles: Dictionary = {}
var _reported_asset_diagnostics: Array[String] = []

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
var _owned_world_bridge: Object
var _owned_geometry_token: RefCounted
var _owned_geometry_generation := 0
var _owned_pose_revision: String = "0"
var _owned_nodes: Dictionary = {}
var _owned_resources: Dictionary = {}
var _owned_custody_error: String = ""
var _owned_ready_completed := false
var _owned_first_failure: Dictionary = {}
var _owned_sync_pending: String = ""
var _owned_source_main: Script
var _owned_source_shell: Script

func _ready() -> void:
	# Keep camera, UI and input alive even when SceneTree is paused.
	process_mode = Node.PROCESS_MODE_ALWAYS
	document = DocScript.new()
	_world = get_node_or_null("World")
	_camera = get_node_or_null("Camera3D")
	shell = get_node_or_null("Shell")
	if not is_instance_valid(_world) or not is_instance_valid(_camera) or not is_instance_valid(shell):
		_owned_fail("ready", "fixed_scene_mismatch")
		return
	_owned_source_main = get_script()
	_owned_source_shell = shell.get_script()
	# The approved scene has exactly one empty fixed World. Never census-adopt.
	if _world.get_parent() != self or _world.get_child_count(true) != 0 or _camera.get_parent() != self or shell.get_parent() != self or _owned_source_main == null or _owned_source_shell == null:
		_owned_fail("ready", "fixed_scene_mismatch")
		return
	_owned_record_fixed(self, "fixed_main")
	_owned_record_fixed(_world, "fixed_world")
	_obstacle_root = Node3D.new()
	_obstacle_root.name = "Obstacles"
	if not _owned_attach_managed(_world, _obstacle_root, "main_source_attach"):
		return
	_gate_root = Node3D.new()
	_gate_root.name = "Gates"
	if not _owned_attach_managed(_world, _gate_root, "main_source_attach"):
		return
	_asset_presenter = PresenterScript.new()
	if not _asset_presenter._owned_bind_main(self):
		_owned_fail("ready", "presenter_bind_refused")
		return
	if not _build_frame() or not _build_ticks() or not _build_drill():
		return
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
	if not _owned_attach_managed(_world, _selection_box, "main_source_attach"):
		return
	shell.bind_editor(self, document)
	document.layout_changed.connect(_sync_obstacles)
	document.gates_changed.connect(_sync_gates)
	document.selection_changed.connect(_on_selection_changed)
	if not _owned_sync_obstacles_checked() or not _owned_sync_gates_checked():
		return
	apply_camera()
	document.log_event("系统", "World 观察视图：边框立方体+角标+坐标刻度；蓝/红圈0.30m；权威未连接、无运动（运行禁用）")
	_owned_ready_completed = true

# Presentation is a separate entry mode, never permission to move a world.
# Retained direct bridges call this same narrow original-target guard.
func _authority_renderer_allowed(target: Node3D) -> bool:
	if not is_instance_valid(target) or target != _drill_root or not is_inside_tree():
		return false
	if not _owned_startup_status().get("ok", false):
		return false
	return _owned_world_bridge == null and _owned_geometry_token == null and target.get_parent() == _world and _world.get_parent() == self

func bind_authority_renderer(run_id: String) -> bool:
	if _authority_pose_bridge != null or not _authority_renderer_allowed(_drill_root):
		return false
	var bridge = AuthorityPoseBridgeScript.new()
	if not bridge.bind_target(_drill_root, run_id):
		return false
	_authority_pose_bridge = bridge
	return true

func present_authority_frame(frame: Variant) -> Dictionary:
	if not _authority_renderer_allowed(_drill_root):
		return {"accepted": false, "error": "renderer_world_mode_refused"}
	if _authority_pose_bridge == null:
		return {"accepted": false, "error": "renderer_unbound"}
	return _authority_pose_bridge.apply_frame(frame)

func read_authority_presentation() -> Dictionary:
	if _authority_pose_bridge == null or not _authority_renderer_allowed(_drill_root):
		return {}
	return _authority_pose_bridge.readback()

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
				_distance = clampf(_distance * 0.89, 0.5, 260.0)
				apply_camera()
		MOUSE_BUTTON_WHEEL_DOWN:
			if event.pressed:
				_distance = clampf(_distance * 1.12, 0.5, 260.0)
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

func focus_drill() -> void:
	if _asset_presenter == null or _drill_root == null:
		return
	var drill := _drill_root.get_node_or_null("DrillPDC") as Node3D
	var bounds := AABB(_drill_root.global_position-Vector3(.12,.12,.4),Vector3(.24,.24,.8))
	if drill != null:
		bounds = _asset_presenter.world_visual_bounds(drill)
	_focus_point = bounds.get_center()
	var rect := _camera.get_viewport().get_visible_rect().size
	var aspect := rect.x/maxf(rect.y,1.0)
	var fixed_half_fov := deg_to_rad(_camera.fov)*.5
	var vertical := fixed_half_fov
	var horizontal := atan(tan(vertical)*aspect)
	if _camera.keep_aspect == Camera3D.KEEP_WIDTH:
		horizontal = fixed_half_fov
		vertical = atan(tan(horizontal)/aspect)
	_distance = maxf(.5,1.25*bounds.size.length()*.5/sin(minf(vertical,horizontal)))
	_camera.near = .02
	apply_camera()
	document.log_event("操作", "聚焦钻头（实际比例；仅相机，权威未连接）")

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
	var best_id: int = _asset_presenter.pick_obstacle(from,direction)
	var best_t: float = _asset_presenter.obstacle_ray_t(best_id,from,direction) if best_id >= 0 else INF
	for obstacle in document.obstacles:
		if not _fallback_obstacles.has(int(obstacle.object_id)):
			continue
		var fallback: MeshInstance3D = _fallback_obstacles[int(obstacle.object_id)]
		if not fallback.global_transform.is_finite() or absf(fallback.global_basis.determinant()) < 1e-12:
			continue
		var inverse := fallback.global_transform.affine_inverse()
		var local_bounds: AABB = fallback.mesh.get_aabb()
		# Do not normalize: the local ray retains the same world parameter t
		# as the asset-presenter ray, even under nonuniform scale and shear.
		var t := _ray_hits_aabb(inverse*from, inverse.basis*direction, local_bounds.get_center(),local_bounds.size*.5)
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

func _build_frame() -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var frame: Node3D = _asset_presenter.create_frame()
	if not is_instance_valid(frame):
		return _owned_fail("build", "frame_creation_refused")
	if not _owned_attach_managed(_world, frame, "main_source_attach"):
		return false
	return _build_corners()

func _build_frame_greybox() -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var edge_material := _flat_material(Color(0.55, 0.62, 0.72), 0.05)
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
				if not _owned_attach_managed(_world, edge, "main_source_attach"):
					return false
	return true

func _build_corners() -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var corner_material := _flat_material(Color(0.35, 0.85, 0.95), 0.4)
	var half := DocScript.CUBE_HALF
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				var corner := MeshInstance3D.new()
				corner.name = "Corner_%d_%d_%d" % [int(sx), int(sy), int(sz)]
				var mesh := BoxMesh.new()
				mesh.size = Vector3(0.36, 0.36, 0.36)
				corner.mesh = mesh
				corner.material_override = corner_material
				corner.position = Vector3(sx * half, sy * half, sz * half)
				if not _owned_attach_managed(_world, corner, "main_source_attach"):
					return false
	return true

func _build_ticks() -> bool:
	if not _owned_accept_geometry_writer():
		return false
	_ticks_root = Node3D.new()
	_ticks_root.name = "Ticks"
	if not _owned_attach_managed(_world, _ticks_root, "main_source_attach"):
		return false
	var material := _flat_material(Color(0.75, 0.8, 0.85), 0.0)
	for value in range(-10, 11, 5):
		if not _add_tick(Vector3(float(value), -DocScript.CUBE_HALF, DocScript.CUBE_HALF), "X=%d" % value, material):
			return false
		if not _add_tick(Vector3(DocScript.CUBE_HALF, -DocScript.CUBE_HALF, float(value)), "Z=%d" % value, material):
			return false
		if not _add_tick(Vector3(-DocScript.CUBE_HALF, float(value), DocScript.CUBE_HALF), "Y=%d" % value, material):
			return false
	return true

func _add_tick(position: Vector3, text: String, material: Material) -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var mark := MeshInstance3D.new()
	mark.name = "Mark_" + text.replace("=", "_").replace("-", "m")
	var mesh := BoxMesh.new()
	mesh.size = Vector3(0.18, 0.18, 0.18)
	mark.mesh = mesh
	mark.material_override = material
	mark.position = position
	if not _owned_attach_managed(_ticks_root, mark, "main_source_attach"):
		return false
	var label := Label3D.new()
	label.text = text
	label.font_size = 28
	label.pixel_size = 0.012
	label.modulate = Color(0.8, 0.85, 0.9)
	label.outline_size = 6
	label.position = position + Vector3(0.0, 0.45, 0.0)
	if not _owned_attach_managed(_ticks_root, label, "main_source_attach"):
		return false
	return true

func set_ticks_visible(visible_state: bool) -> void:
	if _ticks_root != null:
		_ticks_root.visible = visible_state
		document.log_event("操作", "坐标刻度显示: %s" % ("开" if visible_state else "关"))

func _build_drill() -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var drill: Node3D = _asset_presenter.create_drill()
	if not is_instance_valid(drill):
		return _owned_fail("build", "drill_creation_refused")
	_drill_root = Node3D.new()
	_drill_root.name = "DrillPresentation"
	if not _owned_attach_managed(_world, _drill_root, "main_source_attach"):
		return false
	if not _owned_attach_managed(_drill_root, drill, "main_source_attach"):
		return false
	var label := _asset_label("实体钻头·静态观察（权威未连接）")
	label.position = Vector3(0,.8,0)
	if not _owned_attach_managed(_drill_root, label, "main_source_attach"):
		return false
	return true

func _build_drill_greybox() -> bool:
	if not _owned_accept_geometry_writer():
		return false
	_drill_root = Node3D.new()
	_drill_root.name = "DrillGreybox"
	if not _owned_attach_managed(_world, _drill_root, "main_source_attach"):
		return false
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
	if not _owned_attach_managed(_drill_root, body, "main_source_attach"):
		return false
	var tip := MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = 0.12
	cone.height = 0.22
	tip.mesh = cone
	tip.material_override = body_material
	tip.quaternion = Quaternion(Vector3.UP, Vector3.BACK)
	tip.position = Vector3(0.0, 0.0, 0.29)
	if not _owned_attach_managed(_drill_root, tip, "main_source_attach"):
		return false
	var label := Label3D.new()
	label.text = "资源加载失败·开发灰盒·钻头（静态；无运动）"
	label.font_size = 30
	label.pixel_size = 0.009
	label.modulate = Color(0.95, 0.9, 0.6)
	label.outline_size = 8
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.position = Vector3(0.0, 0.8, 0.0)
	if not _owned_attach_managed(_drill_root, label, "main_source_attach"):
		return false
	return true

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
	_owned_sync_obstacles_checked()

func _owned_sync_begin(stage: String) -> bool:
	if not _owned_sync_pending.is_empty():
		return _owned_fail("sync", "sync_incomplete")
	if not _owned_accept_geometry_writer():
		return false
	_owned_sync_pending = stage
	return true

func _owned_sync_obstacles_checked() -> bool:
	if not _owned_sync_begin("obstacles"):
		return false
	if not _owned_sync_obstacles_body():
		return false
	_owned_sync_pending = ""
	return true

func _owned_sync_obstacles_body() -> bool:
	var result: Dictionary = _asset_presenter.sync_obstacles(_obstacle_root, document.obstacles)
	if not result.has("ok") or not result.ok is bool or not result.ok:
		return _owned_fail("obstacles", "presenter_sync_refused")
	if not result.has("failed_ids") or not result.failed_ids is Array:
		return _owned_fail("obstacles", "presenter_result_shape")
	for failed_id in result.failed_ids:
		if not failed_id is int:
			return _owned_fail("obstacles", "presenter_result_shape")
	if not result.failed_ids.is_empty():
		return _owned_fail("obstacles", "presenter_sync_refused")
	if result.has("refused") and (not result.refused is bool or result.refused):
		return _owned_fail("obstacles", "presenter_sync_refused")
	var live := {}
	for obstacle in document.obstacles:
		var id := int(obstacle.object_id)
		live[id] = true
		var asset: Node3D = _asset_presenter.obstacle_node(id)
		if not is_instance_valid(asset) or asset.get_parent() != _obstacle_root or not _owned_custody_contains(asset):
			return _owned_fail("obstacles", "asset_reference_refused")
		if _fallback_obstacles.has(id) and not _remove_presentation_node(_fallback_obstacles, id):
			return false
		var bounds: AABB = _asset_presenter.world_visual_bounds(asset)
		if not _obstacle_labels.has(id):
			var fresh_label := _asset_label("")
			if not _owned_attach_managed(_obstacle_root, fresh_label, "main_source_attach"):
				return false
			_obstacle_labels[id] = fresh_label
		var label: Label3D = _obstacle_labels[id]
		if not is_instance_valid(label) or label.get_parent() != _obstacle_root:
			return _owned_fail("obstacles", "asset_reference_refused")
		label.text = String(DocScript.KIND_LABELS[String(obstacle.kind)])
		label.global_position = Vector3(bounds.get_center().x,bounds.end.y+.7,bounds.get_center().z)
	for nodes in [_obstacle_labels,_fallback_obstacles]:
		for id in nodes.keys():
			if not live.has(id) and not _remove_presentation_node(nodes, id):
				return false
	_report_presentation()
	_sync_selection_box()
	return true

func _asset_label(text: String) -> Label3D:
	var label := Label3D.new()
	label.text = text
	label.font_size = 30
	label.pixel_size = .009
	label.modulate = Color(.95,.9,.6)
	label.outline_size = 8
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	return label

func _remove_presentation_node(nodes: Dictionary, id: int) -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var node: Node = nodes[id]
	if not _owned_forget_managed_subtree(node):
		return false
	node.get_parent().remove_child(node)
	node.free()
	nodes.erase(id)
	return true

func _report_presentation() -> void:
	var report: Dictionary = _asset_presenter.report()
	for diagnostic in report.diagnostics:
		if not _reported_asset_diagnostics.has(diagnostic):
			_reported_asset_diagnostics.append(diagnostic)
			document.log_event("资源",diagnostic)
	if shell != null:
		shell.set_presentation_report(report)

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
	_owned_sync_gates_checked()

func _owned_sync_gates_checked() -> bool:
	if not _owned_sync_begin("gates"):
		return false
	if not _owned_sync_gates_body():
		return false
	_owned_sync_pending = ""
	return true

func _owned_sync_gates_body() -> bool:
	for child in _gate_root.get_children():
		if not _owned_forget_managed_subtree(child):
			return false
		_gate_root.remove_child(child)
		child.free()
	for which in ["entry", "exit"]:
		if not _build_gate_visual(which):
			return false
	return true

func _build_gate_visual(which: String) -> bool:
	if not _owned_accept_geometry_writer():
		return false
	var is_entry := which == "entry"
	var color := Color(0.15, 0.45, 1.0, 1.0) if is_entry else Color(1.0, 0.25, 0.2, 1.0)
	var gate_node := Node3D.new()
	gate_node.name = "Gate_" + which
	gate_node.position = document.gate_position(which)
	gate_node.quaternion = Quaternion(Vector3.UP, document.gate_normal(which))
	if not _owned_attach_managed(_gate_root, gate_node, "main_source_attach"):
		return false
	var ring_material := StandardMaterial3D.new()
	ring_material.albedo_color = color
	ring_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring_material.emission_enabled = true
	ring_material.emission = color
	ring_material.emission_energy_multiplier = 1.4
	var ring := MeshInstance3D.new()
	ring.name = "Ring"
	var torus := TorusMesh.new()
	torus.inner_radius = 0.135
	torus.outer_radius = 0.165
	ring.mesh = torus
	ring.material_override = ring_material
	if not _owned_attach_managed(gate_node, ring, "main_source_attach"):
		return false
	var disc := MeshInstance3D.new()
	disc.name = "Disc"
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
	if not _owned_attach_managed(gate_node, disc, "main_source_attach"):
		return false
	var label := Label3D.new()
	label.text = "进入（蓝圈 0.30m）" if is_entry else "离开（红圈 0.30m）"
	label.font_size = 34
	label.pixel_size = 0.009
	label.modulate = color
	label.outline_size = 8
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.position = Vector3(0.0, 0.34, 0.0)
	if not _owned_attach_managed(gate_node, label, "main_source_attach"):
		return false
	var local_direction := Vector3(0.0, -1.0, 0.0) if is_entry else Vector3(0.0, 1.0, 0.0)
	var arrow := MeshInstance3D.new()
	arrow.name = "DirectionArrow"
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = 0.05
	cone.height = 0.5
	arrow.mesh = cone
	arrow.material_override = ring_material
	arrow.quaternion = Quaternion(Vector3.UP, local_direction)
	arrow.position = local_direction * 0.45
	if not _owned_attach_managed(gate_node, arrow, "main_source_attach"):
		return false

# Owned-world hooks retain actual same-process objects. Wire IDs/state labels
# never satisfy the bridge/token checks, and no production link flag is changed.
	return true

func _owned_attach_world_bridge(bridge: Object) -> bool:
	if not is_instance_valid(bridge) or _owned_world_bridge != null or _authority_pose_bridge != null or not _owned_startup_status().ok:
		return false
	if not document._owned_attach_bridge(bridge):
		return _owned_fail("bridge", "document_bind_refused")
	_owned_world_bridge = bridge
	if not _asset_presenter._owned_bind_bridge(self, bridge):
		return _owned_fail("bridge", "presenter_bridge_refused")
	return true

func _owned_world_references(bridge: Object) -> Dictionary:
	if bridge != _owned_world_bridge or not _owned_startup_status().ok:
		return {}
	return {"main": self, "document": document, "workspace": _world,
		"drill": _drill_root, "presenter": _asset_presenter, "camera": _camera,
		"shell": shell, "obstacles": _obstacle_root, "gates": _gate_root,
		"selection": _selection_box, "ticks": _ticks_root}

func _owned_drain_and_lock(bridge: Object, token: RefCounted) -> bool:
	if bridge != _owned_world_bridge or token == null or _owned_geometry_token != null or not _owned_writer_open():
		return false
	# Direct signals and synchronous sync have no deferred geometry writer.
	if not _owned_sync_obstacles_checked() or not _owned_sync_gates_checked() or not _owned_startup_status().ok:
		return false
	_owned_geometry_token = token
	if not _asset_presenter._owned_freeze(self, bridge, token):
		return _owned_fail("bridge", "presenter_lock_refused")
	if not document._owned_lock_geometry(bridge, token):
		return _owned_fail("bridge", "document_lock_refused")
	_owned_pose_revision = "0"
	_dragging = false
	_drag_object_id = -1
	return true

func _owned_unlock_world(bridge: Object, token: RefCounted) -> bool:
	if bridge != _owned_world_bridge or token == null or token != _owned_geometry_token:
		return false
	# Bridge retires coverage first. Main denies until every participant agrees.
	if not _asset_presenter._owned_thaw(self, bridge, token):
		return false
	if not document._owned_unlock_geometry(bridge, token):
		return false
	_owned_geometry_token = null
	return true

func _owned_geometry_revision(bridge: Object) -> int:
	return _owned_geometry_generation if bridge == _owned_world_bridge else -1

func _owned_apply_drill_global(bridge: Object, token: RefCounted, desired: Transform3D, revision: String) -> bool:
	if bridge != _owned_world_bridge or token == null or token != _owned_geometry_token:
		return false
	if not document._owned_is_locked(bridge, token) or not is_instance_valid(_drill_root) or not desired.is_finite():
		return false
	# Sole post-freeze pose write. Asset/pivot/child-local transforms are untouched.
	_drill_root.global_transform = desired
	_owned_pose_revision = revision
	return true

func _owned_drill_readback(bridge: Object, token: RefCounted) -> Dictionary:
	if bridge != _owned_world_bridge or token == null or token != _owned_geometry_token or not is_instance_valid(_drill_root):
		return {}
	return {"local": _drill_root.transform, "global": _drill_root.global_transform,
		"pose_revision": _owned_pose_revision, "node": _drill_root}

func _diag_timing_mark(code: int, arg0: int = 0, arg1: int = 0) -> void:
	if is_instance_valid(_owned_world_bridge):
		_owned_world_bridge._diag_timing_mark(code, arg0, arg1)

func _process(_delta: float) -> void:
	_diag_timing_mark(19)
	_process_diag_core(_delta)
	_diag_timing_mark(20)

func _process_diag_core(_delta: float) -> void:
	if is_instance_valid(_owned_world_bridge) and _owned_world_bridge._owned_startup_complete():
		_owned_world_bridge.call("audit_frame")


func _owned_fail(stage: String, code: String, variant_type: int = 0, slot_code: int = 0) -> bool:
	if _owned_first_failure.is_empty():
		var stages := ["ready", "build", "sync", "obstacles", "gates", "custody", "bridge"]
		var codes := ["fixed_scene_mismatch", "presenter_bind_refused", "frame_creation_refused", "drill_creation_refused", "sync_incomplete", "presenter_sync_refused", "presenter_result_shape", "asset_reference_refused", "document_bind_refused", "presenter_bridge_refused", "presenter_lock_refused", "document_lock_refused", "fresh_node_custody_refused", "fresh_resource_custody_refused", "source_commit_refused", "resource_refused", "node_refused", "attach_refused", "forget_refused", "unknown"]
		_owned_first_failure = {"stage":stage if stages.has(stage) else "custody",
			"code":code if codes.has(code) else "unknown", "variant_type":maxi(0, variant_type),
			"slot_code":slot_code if slot_code >= 0 and slot_code <= 5 else 0}
		_owned_custody_error = _owned_first_failure.code
	return false

func _owned_startup_status() -> Dictionary:
	var status := {"ok":false, "ready_completed":_owned_ready_completed,
		"failed":not _owned_first_failure.is_empty(), "stage":"", "code":"",
		"variant_type":0, "slot_code":0}
	if not _owned_first_failure.is_empty():
		for key in _owned_first_failure:
			status[key] = _owned_first_failure[key]
		return status
	if not _owned_sync_pending.is_empty():
		status.stage = "sync"
		status.code = "sync_incomplete"
		return status
	if not _owned_ready_completed:
		status.stage = "ready"
		status.code = "ready_incomplete"
		return status
	status.stage = "ready"
	status.code = "references_incomplete"
	if not _owned_live_participants():
		return status
	var report: Dictionary = _asset_presenter.report()
	if report.get("state", "") != "ready":
		status.code = "presenter_incomplete"
		return status
	status.ok = true
	status.stage = ""
	status.code = ""
	return status

func _owned_live_participants() -> bool:
	if not is_inside_tree() or not _owned_nodes.has(get_instance_id()) or get_parent() != _owned_nodes[get_instance_id()].parent:
		return false
	for participant in [document, _world, _camera, shell, _drill_root, _ticks_root, _gate_root, _obstacle_root, _selection_box, _asset_presenter]:
		if not is_instance_valid(participant):
			return false
	if get_script() != _owned_source_main or document.get_script() != DocScript or _asset_presenter.get_script() != PresenterScript:
		return false
	if _world != get_node_or_null("World") or _camera != get_node_or_null("Camera3D") or shell != get_node_or_null("Shell"):
		return false
	if _world.get_parent() != self or _camera.get_parent() != self or shell.get_parent() != self or shell.get_script() != _owned_source_shell:
		return false
	for node in [_drill_root, _ticks_root, _gate_root, _obstacle_root, _selection_box]:
		if node.get_parent() != _world or not _owned_custody_contains(node):
			return false
	return _asset_presenter._owned_main == self and shell._main == self and shell._document == document and shell._initialized

func _owned_accept_geometry_writer() -> bool:
	if _owned_geometry_token != null:
		_owned_world_bridge.call("local_fault", "mutation")
		return false
	if not _owned_writer_open():
		return false
	_owned_geometry_generation += 1
	return true


# Source-owned custody is established by the fixed creation/attachment sites,
# never by validation's census. These references are private local capabilities.
func _owned_accept_presenter_binding(presenter: Object) -> bool:
	return presenter != null and presenter == _asset_presenter and _owned_geometry_token == null

func _owned_presenter_binding_matches(presenter: Object, bridge: Object) -> bool:
	return presenter == _asset_presenter and bridge != null and bridge == _owned_world_bridge

func _owned_presenter_mutation_allowed(presenter: Object) -> bool:
	return presenter != null and presenter == _asset_presenter and _owned_geometry_token == null and document != null and document.can_edit() and _owned_custody_error.is_empty()

func _owned_presenter_parent_matches(presenter: Object, parent: Node3D) -> bool:
	return presenter == _asset_presenter and parent == _obstacle_root and _owned_custody_contains(parent)

func _owned_presenter_lock_matches(presenter: Object, bridge: Object, token: RefCounted) -> bool:
	return presenter == _asset_presenter and bridge != null and bridge == _owned_world_bridge and token != null and token == _owned_geometry_token

func _owned_writer_open() -> bool:
	return _owned_geometry_token == null and document != null and document.can_edit() and _owned_custody_error.is_empty()

func _owned_observer(node: Node) -> bool:
	return node == _camera or node == _selection_box or node is Label3D or node is Light3D or not node is Node3D or (_ticks_root != null and (node == _ticks_root or _ticks_root.is_ancestor_of(node)))

func _owned_walk(node: Node, result: Array) -> void:
	result.append(node)
	for child: Node in node.get_children(true):
		_owned_walk(child, result)

func _owned_custody_contains(node: Node) -> bool:
	return is_instance_valid(node) and _owned_nodes.has(node.get_instance_id()) and _owned_nodes[node.get_instance_id()].node == node

func _owned_record_fixed(node: Node, origin: String) -> void:
	_owned_nodes[node.get_instance_id()] = {"node":node,"parent":node.get_parent(),"origin":origin,
		"local":node.transform if node is Node3D else null,"bindings":{},"resources":[]}

func _owned_register_fresh_subtree(node: Node, origin: String) -> bool:
	if not _owned_writer_open():
		return false
	if not is_instance_valid(node) or node.get_parent() != null or not ["main_source_attach", "presenter_factory_return"].has(origin):
		return _owned_fail("custody", "node_refused")
	var fresh: Array = []
	_owned_walk(node, fresh)
	for item: Node in fresh:
		if _owned_custody_contains(item) or item.get_script() != null:
			return _owned_fail("custody", "node_refused")
	# Validate every resource before registering any part of the factory return.
	for item: Node in fresh:
		var resources: Array = _owned_node_resources(item)
		for resource: Resource in resources:
			if _owned_resource_fingerprint(resource).is_empty():
				return _owned_fail("custody", "resource_refused")
	for item: Node in fresh:
		_owned_record_fixed(item, origin)
		_owned_nodes[item.get_instance_id()].bindings = _owned_node_bindings(item)
		_owned_nodes[item.get_instance_id()].resources = _owned_node_resources(item)
	if not _owned_refresh_resource_records([]):
		return _owned_fail("custody", "fresh_resource_custody_refused")
	return true

func _owned_attach_managed(parent: Node, node: Node, origin: String) -> bool:
	if not _owned_writer_open():
		return false
	if not _owned_custody_contains(parent) or not is_instance_valid(node) or node.get_parent() != null:
		return _owned_fail("custody", "attach_refused")
	if not ["main_source_attach", "presenter_obstacle_attach"].has(origin):
		return _owned_fail("custody", "attach_refused")
	if not _owned_custody_contains(node) and not _owned_register_fresh_subtree(node, "main_source_attach"):
		return _owned_fail("custody", "fresh_node_custody_refused")
	var retained: Dictionary = _owned_nodes[node.get_instance_id()]
	if retained.parent != null:
		return _owned_fail("custody", "attach_refused")
	parent.add_child(node)
	if not is_instance_valid(node) or node.get_parent() != parent:
		return _owned_fail("custody", "attach_refused")
	retained.parent = parent
	return _owned_commit_managed_subtree(node)

func _owned_forget_managed_subtree(node: Node) -> bool:
	if not _owned_writer_open():
		return false
	if not _owned_custody_contains(node) or node == self or node == _world:
		return _owned_fail("custody", "forget_refused")
	var removed: Array = []
	_owned_walk(node, removed)
	for item: Node in removed:
		if not _owned_custody_contains(item):
			return _owned_fail("custody", "forget_refused")
	for item: Node in removed:
		_owned_nodes.erase(item.get_instance_id())
	if not _owned_refresh_resource_records([]):
		return _owned_fail("custody", "forget_refused")
	return true

func _owned_commit_managed_subtree(node: Node) -> bool:
	if not _owned_writer_open():
		return false
	if not _owned_custody_contains(node):
		return _owned_fail("custody", "source_commit_refused")
	var changed: Array = []
	_owned_walk(node, changed)
	var sanctioned: Array = []
	for item: Node in changed:
		if not _owned_custody_contains(item) or item.get_parent() != _owned_nodes[item.get_instance_id()].parent:
			return _owned_fail("custody", "source_commit_refused")
		var resources: Array = _owned_node_resources(item)
		for resource: Resource in resources:
			if _owned_resource_fingerprint(resource).is_empty():
				return _owned_fail("custody", "resource_refused")
			sanctioned.append(resource)
	for item: Node in changed:
		var retained: Dictionary = _owned_nodes[item.get_instance_id()]
		retained.local = item.transform if item is Node3D else null
		retained.bindings = _owned_node_bindings(item)
		retained.resources = _owned_node_resources(item)
	if not _owned_refresh_resource_records(sanctioned):
		return _owned_fail("custody", "source_commit_refused")
	return true

func _owned_node_bindings(node: Node) -> Dictionary:
	var bindings: Dictionary = {}
	if node is MeshInstance3D:
		bindings.mesh = node.mesh
		bindings.material_override = node.material_override
		bindings.material_overlay = node.material_overlay
		if node.mesh != null:
			for surface: int in node.mesh.get_surface_count():
				bindings["surface_override_" + str(surface)] = node.get_surface_override_material(surface)
				bindings["surface_material_" + str(surface)] = node.mesh.surface_get_material(surface)
	if node is CollisionShape3D:
		bindings.shape = node.shape
	return bindings

func _owned_node_resources(node: Node) -> Array:
	var result: Array = []
	for value: Variant in _owned_node_bindings(node).values():
		_owned_collect_resources(value, result)
	return result

func _owned_collect_resources(value: Variant, result: Array) -> void:
	if value is Resource:
		if result.has(value):
			return
		result.append(value)
		for property: Dictionary in value.get_property_list():
			if (int(property.usage) & PROPERTY_USAGE_STORAGE) != 0:
				var actual: Variant = value.get(property.name)
				if typeof(actual) in [TYPE_OBJECT, TYPE_ARRAY, TYPE_DICTIONARY]:
					_owned_collect_resources(actual, result)
	elif value is Array:
		for item: Variant in value:
			if typeof(item) in [TYPE_OBJECT, TYPE_ARRAY, TYPE_DICTIONARY]:
				_owned_collect_resources(item, result)
	elif value is Dictionary:
		for item: Variant in value.values():
			if typeof(item) in [TYPE_OBJECT, TYPE_ARRAY, TYPE_DICTIONARY]:
				_owned_collect_resources(item, result)

func _owned_encode_storage(value: Variant, ancestors: Array) -> Dictionary:
	# ID0 identity excludes freed Objects that compare equal to validated null.
	if typeof(value) == TYPE_OBJECT:
		if is_same(value, type_convert(null, TYPE_OBJECT)):
			return {"ok":true,"value":null}
		if not is_instance_valid(value):
			return {"ok":false}
	if value is Resource:
		if ancestors.has(value) or value.get_script() != null:
			return {"ok":false}
		if not (value is ArrayMesh or value is BoxMesh or value is CylinderMesh or value is TorusMesh or value is BoxShape3D or value is SphereShape3D or value is CapsuleShape3D or value is CylinderShape3D or value is StandardMaterial3D):
			return {"ok":false}
		var next: Array = ancestors.duplicate()
		next.append(value)
		var properties: Dictionary = {}
		for property: Dictionary in value.get_property_list():
			if (int(property.usage) & PROPERTY_USAGE_STORAGE) == 0:
				continue
			var actual: Variant = value.get(property.name)
			if typeof(actual) not in [TYPE_OBJECT, TYPE_ARRAY, TYPE_DICTIONARY, TYPE_RID, TYPE_CALLABLE, TYPE_SIGNAL]:
				properties[String(property.name)] = actual
				continue
			var encoded: Dictionary = _owned_encode_storage(actual, next)
			if not encoded.get("ok", false):
				return {"ok":false}
			properties[String(property.name)] = encoded.value
		var descriptor: Dictionary = {"id":value.get_instance_id(),"class":value.get_class(),"properties":properties}
		if value is Mesh:
			var surfaces: Array = []
			for surface: int in value.get_surface_count():
				var arrays: Array = value.surface_get_arrays(surface)
				var encoded: Dictionary = _owned_encode_storage(arrays, next)
				if not encoded.get("ok", false):
					return {"ok":false}
				var blend_shapes: Dictionary = _owned_encode_storage(value.surface_get_blend_shape_arrays(surface), next)
				if not blend_shapes.get("ok", false):
					return {"ok":false}
				var primitive: int = value.surface_get_primitive_type(surface) if value is ArrayMesh else Mesh.PRIMITIVE_TRIANGLES
				surfaces.append({"primitive":primitive,"arrays":encoded.value,"blend_shapes":blend_shapes.value})
			descriptor.surfaces = surfaces
		return {"ok":true,"value":descriptor}
	if value is Array:
		var items: Array = []
		for item: Variant in value:
			if typeof(item) not in [TYPE_OBJECT, TYPE_ARRAY, TYPE_DICTIONARY, TYPE_RID, TYPE_CALLABLE, TYPE_SIGNAL]:
				items.append(item)
				continue
			var encoded: Dictionary = _owned_encode_storage(item, ancestors)
			if not encoded.get("ok", false):
				return {"ok":false}
			items.append(encoded.value)
		return {"ok":true,"value":items}
	if value is Dictionary:
		var items: Array = []
		var keys: Array = value.keys()
		keys.sort()
		for key: Variant in keys:
			if not (key is String or key is StringName or key is int):
				return {"ok":false}
			var actual: Variant = value[key]
			if typeof(actual) not in [TYPE_OBJECT, TYPE_ARRAY, TYPE_DICTIONARY, TYPE_RID, TYPE_CALLABLE, TYPE_SIGNAL]:
				items.append([key, actual])
				continue
			var encoded: Dictionary = _owned_encode_storage(actual, ancestors)
			if not encoded.get("ok", false):
				return {"ok":false}
			items.append([key, encoded.value])
		return {"ok":true,"value":items}
	if typeof(value) in [TYPE_OBJECT, TYPE_RID, TYPE_CALLABLE, TYPE_SIGNAL]:
		return {"ok":false}
	return {"ok":true,"value":value}

func _owned_resource_fingerprint(resource: Resource) -> String:
	if not is_instance_valid(resource):
		return ""
	var encoded: Dictionary = _owned_encode_storage(resource, [])
	if not encoded.get("ok", false):
		return ""
	var serialized: PackedByteArray = var_to_bytes(encoded.value)
	if serialized.is_empty():
		return ""
	var context: HashingContext = HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK:
		return ""
	if context.update("DEEYE_RESOURCE_DESCRIPTOR_NATIVE_V2\n".to_ascii_buffer()) != OK:
		return ""
	if context.update(serialized) != OK:
		return ""
	var digest: PackedByteArray = context.finish()
	if digest.size() != 32:
		return ""
	return digest.hex_encode()

func _owned_refresh_resource_records(sanctioned: Array) -> bool:
	var resources: Dictionary = {}
	for retained: Dictionary in _owned_nodes.values():
		for resource: Resource in retained.resources:
			var key: int = resource.get_instance_id()
			if not resources.has(key):
				var fingerprint: String = _owned_resource_fingerprint(resource)
				if fingerprint.is_empty():
					return false
				if _owned_resources.has(key) and _owned_resources[key].fingerprint != fingerprint and not sanctioned.has(resource):
					return false
				resources[key] = {"resource":resource,"fingerprint":fingerprint,"consumers":[],"consumer_set":{}}
			resources[key].consumers.append(retained.node)
			resources[key].consumer_set[retained.node] = true
	_owned_resources = resources
	return true

func _owned_custody_failure(code: String) -> Dictionary:
	return {"ok":false,"code":code,"required_count":0,"mesh_count":0,"shape_count":0}

func _owned_validate_custody(bridge: Object, token: RefCounted) -> Dictionary:
	_diag_timing_mark(9)
	var result: Dictionary = _owned_validate_custody_diag_core(bridge, token)
	_diag_timing_mark(10)
	return result

func _owned_validate_custody_diag_core(bridge: Object, token: RefCounted) -> Dictionary:
	if bridge == null or bridge != _owned_world_bridge or token == null or token != _owned_geometry_token or not document._owned_is_locked(bridge, token) or not _asset_presenter._owned_is_frozen(self, bridge, token):
		return _owned_custody_failure("participant_lock_mismatch")
	if not _owned_custody_error.is_empty():
		return _owned_custody_failure(_owned_custody_error)
	var actual: Array = []
	_owned_walk(self, actual)
	var actual_set: Dictionary = {}
	for node: Node in actual:
		actual_set[node] = true
	# Script checks precede all class/custody classification, including observers.
	for node: Node in actual:
		var script: Script = node.get_script()
		if script != null and not ((node == self and script == _owned_source_main) or (node == shell and script == _owned_source_shell)):
			return _owned_custody_failure("foreign_node_script")
	for node: Node in actual:
		if not _owned_observer(node) and not _owned_custody_contains(node):
			return _owned_custody_failure("unregistered_managed_node")
	var required_count: int = 0
	var mesh_count: int = 0
	var shape_count: int = 0
	for retained: Dictionary in _owned_nodes.values():
		var node: Node = retained.node
		if not is_instance_valid(node) or not actual_set.has(node) or node.get_parent() != retained.parent:
			return _owned_custody_failure("managed_parent_identity_changed")
		if not _owned_observer(node):
			required_count += 1
			if node is Node3D and node != _drill_root and node.transform != retained.local:
				return _owned_custody_failure("managed_local_changed")
		if _owned_node_bindings(node) != retained.bindings or _owned_node_resources(node) != retained.resources:
			return _owned_custody_failure("managed_resource_identity_changed")
		if node is MeshInstance3D:
			mesh_count += 1
		if node is CollisionShape3D:
			shape_count += 1
	# Recompute consumers from the actual complete native tree, not the registry.
	var global_nodes: Array = []
	_owned_walk(get_tree().root, global_nodes)
	var current_consumers: Dictionary = {}
	for node: Node in global_nodes:
		var resources: Array = _owned_node_resources(node)
		for resource: Resource in resources:
			if not current_consumers.has(resource):
				current_consumers[resource] = {}
			current_consumers[resource][node] = true
	var resource_fingerprints: Dictionary = {}
	_diag_timing_mark(11)
	for retained: Dictionary in _owned_resources.values():
		var resource: Resource = retained.resource
		var fresh: String = _owned_resource_fingerprint(resource)
		if not is_instance_valid(resource) or fresh != retained.fingerprint:
			_diag_timing_mark(12, 0, _owned_resources.size())
			return _owned_custody_failure("managed_resource_content_changed")
		resource_fingerprints[resource] = fresh
		var consumers: Dictionary = current_consumers.get(resource, {})
		var observer_consumer: bool = false
		var geometry_consumer: bool = false
		for node: Node in consumers:
			if not _owned_custody_contains(node):
				_diag_timing_mark(12, 0, _owned_resources.size())
				return _owned_custody_failure("outside_resource_consumer")
			observer_consumer = observer_consumer or _owned_observer(node)
			geometry_consumer = geometry_consumer or not _owned_observer(node)
		if (resource is Mesh or resource is Shape3D) and observer_consumer and geometry_consumer:
			_diag_timing_mark(12, 0, _owned_resources.size())
			return _owned_custody_failure("observer_geometry_resource_alias")
		if consumers.size() != retained.consumer_set.size():
			_diag_timing_mark(12, 0, _owned_resources.size())
			return _owned_custody_failure("resource_consumer_set_changed")
		for node: Node in consumers:
			if not retained.consumer_set.has(node):
				_diag_timing_mark(12, 0, _owned_resources.size())
				return _owned_custody_failure("resource_consumer_set_changed")
	_diag_timing_mark(12, 1, _owned_resources.size())
	return {"ok":true,"code":"ready","required_count":required_count,"mesh_count":mesh_count,"shape_count":shape_count,"resource_fingerprints":resource_fingerprints}

func _owned_coverage_context(bridge: Object, token: RefCounted, doc_gen: int, geom_gen: int) -> Dictionary:
	if doc_gen != document._owned_generation(bridge) or geom_gen != _owned_geometry_generation:
		return {}
	var validation: Dictionary = _owned_validate_custody(bridge, token)
	if not validation.get("ok", false):
		return {}
	var context: Dictionary = _owned_world_references(bridge)
	context.token = token
	context.document_generation = doc_gen
	context.geometry_generation = geom_gen
	var members: Array = []
	for retained: Dictionary in _owned_nodes.values():
		members.append(retained.node)
	context.members = members
	return context

func _owned_frozen_fingerprint(bridge: Object, token: RefCounted) -> Dictionary:
	var validation: Dictionary = _owned_validate_custody(bridge, token)
	if not validation.get("ok", false):
		return {}
	var nodes: Array = []
	for retained: Dictionary in _owned_nodes.values():
		var node: Node = retained.node
		if not _owned_observer(node):
			nodes.append({"node":node,"parent":node.get_parent(),"local":node.transform if node is Node3D else null,"bindings":_owned_node_bindings(node)})
	var resources: Array = []
	for retained: Dictionary in _owned_resources.values():
		resources.append({"resource":retained.resource,"fingerprint":validation.resource_fingerprints[retained.resource],"consumers":retained.consumers.duplicate()})
	return {"nodes":nodes,"resources":resources,"document_generation":document._owned_generation(bridge),"geometry_generation":_owned_geometry_generation,"presenter":_asset_presenter._owned_frozen_state(self, bridge, token)}

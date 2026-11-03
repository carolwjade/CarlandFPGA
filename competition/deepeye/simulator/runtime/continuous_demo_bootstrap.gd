extends SceneTree
## Candidate 801: explicit Root-launched live mode. No default scene changes.
## Private geometry is written only below Root's claimed output directory.
## This UI submits operator intent; only Root may execute actual board changes.

const ABI := "DEEPEYE-CONTINUOUS-BOOTSTRAP-801-v1"
const HOST_ABI := "DEEPEYE-CONTINUOUS-HOST-801-v1"
const CONTRACT := "DEEPEYE-HUMAN-LOCK-20261014/revision2"
const REQUIREMENTS_SHA256 := "2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d"
const CLAIM := ".continuous-bootstrap-801.claim"
const MATERIALS := ["water", "hard_rock", "fault", "void", "casing"]
const HOST_MAX_AGE_MS := 3000
const Dashboard = preload("res://runtime/continuous_dashboard_view.gd")

class MouseWitness extends Node:
	var host: Object
	func _input(event: InputEvent) -> void:
		if is_instance_valid(host):
			host.observe_mouse(event)

var _config: Dictionary = {}
var _main: Node
var _layer: CanvasLayer
var _panel: PanelContainer
var _toggle: Button
var _scroll: ScrollContainer
var _dashboard = Dashboard.new()
var _body: VBoxContainer
var _labels: Dictionary = {}
var _start: Button
var _pause: Button
var _resume: Button
var _stop: Button
var _speed: HSlider
var _confirm: CheckBox
var _mode_choice: OptionButton
var _claimed := false
var _start_attempted := false
var _bind_called := false
var _bound := false
var _drag_seen := false
var _gate_setup_seen := false
var _left_held := false
var _mouse_travel := 0.0
var _requested_speed := 0.1
var _latched_initial_speed := 0.1
var _initial_speed_latched := false
var _terminal_complete_observed := false
var _requested_paused := true
var _stop_latched := false
var _intent_seq := 0
var _last_intent_tick := 0
var _host_seq := -1
var _pending_text := "拖动障碍并设置蓝红圈，然后开始"
var _fatal := ""
var _source_objects := 0
var _source_pieces := 0
var _editor_text_simplified := false

func _initialize() -> void:
	call_deferred("_boot")

func _boot() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2 or args[0] != "--root-live-config":
		_fail_startup("root_live_config_argument_required")
		return
	if not ordinary_absolute_path(args[1], false) or not FileAccess.file_exists(args[1]):
		_fail_startup("config_requires_ordinary_absolute_file")
		return
	var parsed := read_json_file(args[1], 65536)
	if not parsed.ok or not parsed.value is Dictionary:
		_fail_startup("config_json_invalid")
		return
	var checked := validate_config(parsed.value)
	if not checked.ok:
		_fail_startup(checked.reason)
		return
	_config = parsed.value
	var claim := claim_output(_config.output_directory)
	if not claim.ok:
		_fail_startup(claim.reason)
		return
	_claimed = true
	var scene: PackedScene = load("res://viewer/main.tscn")
	if scene == null:
		_fail_startup("actual_main_scene_missing")
		return
	_main = scene.instantiate()
	root.add_child(_main)
	current_scene = _main
	if not _main.is_node_ready():
		await _main.ready
	if not _main.has_method("bind_continuous_live") or not _main.has_method("read_continuous_live_state") or not bool(_main.get("_owned_ready_completed")):
		_fail_startup("actual_main_ready_or_794_api_refused")
		return
	var document: Object = _main.get("document")
	if document == null or not document.can_edit():
		_fail_startup("initial_document_not_editable")
		return
	# Restore geometry only; fresh mouse interaction is still required below.
	if _config.has("initial_layout_file"):
		var prior := FileAccess.get_file_as_string(_config.initial_layout_file)
		var imported: Dictionary = document.apply_layout_text(prior)
		if not imported.get("ok",false):
			_fail_startup("initial_geometry_import_refused")
			return
	_requested_speed = float(_config.get("initial_speed_m_s",0.1))
	_latched_initial_speed = _requested_speed
	# Sibling of Main: never claim or register these controls as old custody.
	_build_panel()
	document.layout_changed.connect(_on_layout_changed)
	document.gates_changed.connect(_on_gates_changed)
	document.stop_requested.connect(_on_document_stop)
	_apply_optional_camera()
	auto_accept_quit = false
	root.close_requested.connect(_on_window_close)
	var timer := Timer.new()
	timer.wait_time = 0.25
	timer.process_mode = Node.PROCESS_MODE_ALWAYS
	_layer.add_child(timer)
	timer.timeout.connect(_refresh_status)
	timer.start()
	_refresh_status()

func _fail_startup(reason: String) -> void:
	# Only fixed error codes, never config bytes or token values.
	printerr("continuous_bootstrap_801: " + reason)
	if _claimed:
		write_json_atomic(_config.output_directory, "bootstrap_error.json", {"abi":ABI,"reason":reason,"world_epoch":_config.world_epoch,"formal_acceptance":"not_run"}, false)
	quit(1)

static func finite_number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value))

static func integer_number(value: Variant) -> bool:
	return finite_number(value) and float(value) == floor(float(value)) and absf(float(value)) <= 9007199254740991.0

static func ordinary_absolute_path(value: Variant, directory: bool) -> bool:
	if not value is String or value.is_empty() or value != value.strip_edges():
		return false
	var path: String = value.replace("\\", "/")
	if not path.is_absolute_path() or "://" in path or path.begins_with("//") or path.split("/").has("..") or path.split("/").has("."):
		return false
	if directory and not DirAccess.dir_exists_absolute(path):
		return false
	if not directory and not DirAccess.dir_exists_absolute(path.get_base_dir()):
		return false
	# Refuse observable symbolic/reparse links. A restricted child may open its
	# owned leaf while an ancestor directory cannot be enumerated. Root must
	# preflight ownership/ACLs and those unobservable ancestors before launch.
	var cursor := path.trim_suffix("/")
	while cursor.get_base_dir() != cursor and not cursor.get_file().is_empty():
		var parent := DirAccess.open(cursor.get_base_dir())
		if parent == null:
			break
		if parent.is_link(cursor.get_file()):
			return false
		cursor = cursor.get_base_dir()
	return true

static func validate_config(config: Dictionary) -> Dictionary:
	for key in ["port", "token", "world_epoch", "output_directory", "host_status_file"]:
		if not config.has(key):
			return {"ok":false,"reason":"config_required_fields"}
	if not integer_number(config.port) or config.port < 1024 or config.port > 65535:
		return {"ok":false,"reason":"config_port"}
	if not config.token is String or config.token.length() < 32 or config.token.length() > 128 or "\n" in config.token or "\r" in config.token:
		return {"ok":false,"reason":"config_token_length_or_format"}
	if not config.world_epoch is String or config.world_epoch.is_empty() or config.world_epoch.length() > 160 or "\n" in config.world_epoch or config.token in config.world_epoch:
		return {"ok":false,"reason":"config_epoch"}
	if not ordinary_absolute_path(config.output_directory, true) or not ordinary_absolute_path(config.host_status_file, false):
		return {"ok":false,"reason":"config_ordinary_existing_paths"}
	var out: String = config.output_directory.replace("\\", "/").trim_suffix("/")
	var status: String = config.host_status_file.replace("\\", "/")
	if status.get_base_dir().to_lower() == out.to_lower() and (status.get_file() in ["frozen.json", "operator_intent.json", "bootstrap_error.json", ".frozen.private.prepared.json"] or status.get_file().begins_with(".")):
		return {"ok":false,"reason":"host_status_output_collision"}
	if config.has("require_box_only") and not config.require_box_only is bool:
		return {"ok":false,"reason":"config_box_policy"}
	if config.has("admission_mode") and not config.admission_mode in ["BOARD_PWM","PC_DIRECT"]:
		return {"ok":false,"reason":"config_admission_mode"}
	if config.has("initial_layout_file") and (not ordinary_absolute_path(config.initial_layout_file,false) or not FileAccess.file_exists(config.initial_layout_file)):
		return {"ok":false,"reason":"config_initial_layout"}
	if config.has("initial_speed_m_s") and (not finite_number(config.initial_speed_m_s) or config.initial_speed_m_s<0.0 or config.initial_speed_m_s>0.25):
		return {"ok":false,"reason":"config_initial_speed"}
	if config.has("camera"):
		var camera: Variant = config.camera
		if not camera is Dictionary or not camera.get("focus_m") is Array or camera.focus_m.size() != 3:
			return {"ok":false,"reason":"config_camera"}
		for value in camera.focus_m:
			if not finite_number(value):
				return {"ok":false,"reason":"config_camera"}
		for key in ["yaw_deg", "pitch_deg", "distance_m"]:
			if not finite_number(camera.get(key)):
				return {"ok":false,"reason":"config_camera"}
		if absf(camera.pitch_deg) > 89.5 or camera.distance_m < 0.5 or camera.distance_m > 260.0:
			return {"ok":false,"reason":"config_camera_bounds"}
	return {"ok":true}

static func claim_output(output: String) -> Dictionary:
	if not ordinary_absolute_path(output, true):
		return {"ok":false,"reason":"output_not_ordinary_existing_directory"}
	for name in ["frozen.json", "operator_intent.json", "bootstrap_error.json", ".frozen.private.prepared.json"]:
		if FileAccess.file_exists(output.path_join(name)) or DirAccess.dir_exists_absolute(output.path_join(name)):
			return {"ok":false,"reason":"output_has_prior_801_artifacts"}
	# Atomic directory creation is the exclusive create primitive. Never remove it.
	if DirAccess.make_dir_absolute(output.path_join(CLAIM)) != OK:
		return {"ok":false,"reason":"output_already_claimed_or_unwritable"}
	return {"ok":true}

static func read_json_file(path: String, maximum_bytes: int) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"ok":false}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > maximum_bytes:
		return {"ok":false}
	var parser := JSON.new()
	var contents := file.get_as_text()
	file.close()
	var error := parser.parse(contents)
	return {"ok":error == OK,"value":parser.data if error == OK else null}

static func write_json_atomic(output: String, name: String, data: Dictionary, replace: bool) -> Dictionary:
	if name.get_file() != name or name.is_empty() or not ordinary_absolute_path(output, true) or not DirAccess.dir_exists_absolute(output.path_join(CLAIM)):
		return {"ok":false,"reason":"output_write_scope"}
	var final := output.path_join(name)
	var temporary := output.path_join("." + name + ".801.tmp")
	var directory := DirAccess.open(output)
	if directory == null or directory.is_link(name) or directory.is_link(temporary.get_file()) or FileAccess.file_exists(temporary) or DirAccess.dir_exists_absolute(temporary) or DirAccess.dir_exists_absolute(final):
		return {"ok":false,"reason":"output_path_refused"}
	if not replace and FileAccess.file_exists(final):
		return {"ok":false,"reason":"output_first_create_required"}
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return {"ok":false,"reason":"output_open_failed"}
	file.store_string(JSON.stringify(data, "\t") + "\n")
	file.flush()
	var error := file.get_error()
	file.close()
	if error != OK:
		return {"ok":false,"reason":"output_write_failed_preserved_temporary"}
	if DirAccess.rename_absolute(temporary, final) != OK:
		return {"ok":false,"reason":"output_rename_failed_preserved_temporary"}
	return {"ok":true}

static func vector_array(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

static func matrix_rows(value: Basis) -> Array:
	return [[value.x.x,value.y.x,value.z.x],[value.x.y,value.y.y,value.z.y],[value.x.z,value.y.z,value.z.z]]

static func piece_from_shape(shape: Shape3D, pose: Transform3D, material: String) -> Dictionary:
	if not MATERIALS.has(material) or not pose.is_finite():
		return {"ok":false,"reason":"source_material_or_transform"}
	var scale := Vector3(pose.basis.x.length(),pose.basis.y.length(),pose.basis.z.length())
	if minf(scale.x,minf(scale.y,scale.z)) <= 0.0:
		return {"ok":false,"reason":"source_nonpositive_scale"}
	var rotation := Basis(pose.basis.x/scale.x,pose.basis.y/scale.y,pose.basis.z/scale.z)
	if absf(rotation.x.dot(rotation.y)) > 0.000001 or absf(rotation.x.dot(rotation.z)) > 0.000001 or absf(rotation.y.dot(rotation.z)) > 0.000001 or absf(rotation.determinant()-1.0) > 0.000001:
		return {"ok":false,"reason":"source_shear_or_reflection_unsupported"}
	var half := Vector3.ZERO
	var kind := ""
	if shape is BoxShape3D:
		kind = "box"
		half = shape.size * scale * 0.5
	elif shape is CylinderShape3D:
		kind = "cylinder"
		# Godot axial Y -> 793 axial Z. X,-Z,Y is right-handed; radial
		# sign is immaterial to an elliptical cylinder. No box substitution.
		half = Vector3(shape.radius*scale.x,shape.radius*scale.z,shape.height*scale.y*0.5)
		rotation = Basis(rotation.x,-rotation.z,rotation.y)
	else:
		return {"ok":false,"reason":"source_shape_unsupported"}
	if not half.is_finite() or minf(half.x,minf(half.y,half.z)) <= 0.0:
		return {"ok":false,"reason":"source_dimensions"}
	return {"ok":true,"piece":{"material":material,"kind":kind,"centre":vector_array(pose.origin),"dimensions":vector_array(half),"matrix":matrix_rows(rotation)}}

static func collect_shapes(node: Node, result: Array) -> void:
	if node is CollisionShape3D and node.shape != null:
		result.append(node)
	for child in node.get_children():
		collect_shapes(child,result)

static func capture_private(main: Node, box_only: bool = false) -> Dictionary:
	if not main.is_inside_tree():
		return {"ok":false,"reason":"source_actual_tree_required"}
	var document: Object = main.get("document")
	if document == null or not document.can_edit():
		return {"ok":false,"reason":"editable_export_required"}
	var exported: Dictionary = document.export_layout_text()
	if not exported.get("ok",false) or not exported.get("text") is String:
		return {"ok":false,"reason":"complete_document_export_failed"}
	var presenter: Object = main.get("_asset_presenter")
	var obstacle_root: Node = main.get("_obstacle_root")
	if presenter == null or obstacle_root == null:
		return {"ok":false,"reason":"actual_presenter_unavailable"}
	var all_shapes: Array = []
	collect_shapes(obstacle_root,all_shapes)
	var pieces: Array = []
	var provenance: Array = []
	var seen: Dictionary = {}
	for obstacle: Dictionary in document.obstacles:
		var asset: Node3D = presenter.obstacle_node(int(obstacle.object_id))
		if not is_instance_valid(asset) or not asset.is_inside_tree() or asset.get_parent() != obstacle_root:
			return {"ok":false,"reason":"source_actual_asset_missing"}
		var shapes: Array = []
		collect_shapes(asset,shapes)
		# Exact compatibility with Main794's complete single-envelope contract.
		if shapes.size() != 1 or seen.has(shapes[0]) or not all_shapes.has(shapes[0]):
			return {"ok":false,"reason":"complete_actual_envelope_required"}
		var collision: CollisionShape3D = shapes[0]
		var built := piece_from_shape(collision.shape,collision.global_transform,String(obstacle.kind))
		if not built.ok:
			return built
		if box_only and built.piece.kind != "box":
			return {"ok":false,"reason":"root_requested_box_only_demo"}
		seen[collision] = true
		pieces.append(built.piece)
		provenance.append({"object_id":obstacle.object_id,"shape_class":collision.shape.get_class(),"disabled_presentation_envelope":collision.disabled})
	if pieces.size() != all_shapes.size() or pieces.size() != document.obstacles.size():
		return {"ok":false,"reason":"source_complete_world_count_mismatch"}
	var gates: Dictionary = {}
	for which in ["entry","exit"]:
		gates[which] = {"center":vector_array(document.gate_position(which)),"normal":vector_array(document.gate_normal(which)),"diameter_m":0.5,"radius_m":0.25}
	return {"ok":true,"layout_text":exported.text,"private_pieces":pieces,"private_piece_provenance":provenance,"object_count":document.obstacles.size(),"piece_count":pieces.size(),"public_gates":gates,"units":"m","geometry_qualification":"nominal_engineering_collision_envelope; not exact visual mesh; PDE/G03 not qualified","cylinder_convention":"793 radial local X/Y, axial local Z; Godot X,-Z,Y remap; native794 retains conservative cylinder bounding box"}

func observe_mouse(event: InputEvent) -> void:
	if _start_attempted:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_left_held = event.pressed
		if event.pressed:
			_mouse_travel = 0.0
	elif event is InputEventMouseMotion and _left_held:
		_mouse_travel += event.relative.length()

func _on_layout_changed() -> void:
	if not _start_attempted and _left_held and _mouse_travel >= 2.0 and bool(_main.get("_dragging")):
		_drag_seen = true
	_refresh_setup()

func _on_gates_changed() -> void:
	if not _start_attempted:
		_gate_setup_seen = true
	_refresh_setup()

func _refresh_setup() -> void:
	if _start == null:
		return
	_labels.setup.text = "障碍拖动 %s   蓝红圈设置 %s" % ["✓" if _drag_seen else "—","✓" if _gate_setup_seen else "—"]
	_start.disabled = _start_attempted or not _drag_seen or not _gate_setup_seen or not _confirm.button_pressed

func _on_start() -> void:
	if _start_attempted or not _drag_seen or not _gate_setup_seen or not _confirm.button_pressed:
		return
	_start_attempted = true
	_refresh_setup()
	_confirm.disabled = true
	_mode_choice.disabled = true
	var admission_mode := _selected_admission_mode()
	var snapshot := capture_private(_main,bool(_config.get("require_box_only",false)))
	if not snapshot.ok:
		_latch_error(snapshot.reason)
		return
	snapshot.erase("ok")
	snapshot.merge({"abi":ABI,"world_epoch":_config.world_epoch,"admission_mode":admission_mode,"contract":CONTRACT,"requirements_sha256":REQUIREMENTS_SHA256,"stage":"prepared_not_installed","formal_acceptance":"not_run","G03":"not_run","all29":"not_run","operator_setup":{"mouse_drag_change_observed":_drag_seen,"gate_change_observed":_gate_setup_seen,"human_confirmation":true,"note":"UI event observation, not a hardware-input attestation"}})
	var prepared := write_json_atomic(_config.output_directory,".frozen.private.prepared.json",snapshot,false)
	if not prepared.ok:
		_latch_error(prepared.reason)
		return
	# The sole call site. No retry, automatic freeze, target, pose or RPC write.
	_bind_called = true
	var installed: Dictionary = _main.bind_continuous_live(int(_config.port),_config.token,admission_mode,_config.world_epoch)
	var clean: Dictionary = {"ok":installed.get("ok",false),"formal_acceptance":"not_run"}
	for key in ["abi","port","reason"]:
		if installed.has(key):
			clean[key] = installed[key]
	snapshot.native_install_result = clean
	snapshot.stage = "installed_awaiting_root_board_receipt" if clean.ok else "native_install_failed_no_retry"
	var written := write_json_atomic(_config.output_directory,"frozen.json",snapshot,false)
	if not written.ok:
		_latch_error(written.reason)
		return
	_source_objects = int(snapshot.object_count)
	_source_pieces = int(snapshot.piece_count)
	if not clean.ok:
		_latch_error("native_install_failed_no_retry")
		return
	_bound = true
	_requested_paused = false
	_pause.disabled = false
	_resume.disabled = false
	_stop.disabled = false
	_pending_text = "准备采样"
	_emit_intent("start")
	_refresh_status()

func _emit_intent(action: String) -> void:
	if not _bound or _stop_latched and action != "stop":
		return
	var next_seq := _intent_seq + 1
	var tick := maxi(Time.get_ticks_usec(),_last_intent_tick+1)
	var intent := {"abi":ABI,"world_epoch":_config.world_epoch,"seq":next_seq,"emitted_tick_usec":str(tick),"action":action,"requested_speed_m_s":_requested_speed,"requested_paused":_requested_paused,"stop_latched":_stop_latched,"actual_board_action_performed":false}
	var result := write_json_atomic(_config.output_directory,"operator_intent.json",intent,true)
	if not result.ok:
		_latch_error(result.reason)
		return
	_intent_seq = next_seq
	_last_intent_tick = tick
	_pending_text = "设置已提交"

func request_speed(value: float) -> void:
	if _stop_latched or not is_finite(value) or value < 0.0 or value > 0.25:
		return
	_requested_speed = value
	if _bound:
		_emit_intent("next_initial_speed" if _initial_speed_latched else "set_initial_speed")
	_refresh_status()

func request_pause() -> void:
	if not _bound or _stop_latched:
		return
	_requested_paused = true
	_emit_intent("pause")
	_refresh_status()

func request_resume() -> void:
	if not _bound or _stop_latched:
		return
	_requested_paused = false
	_emit_intent("resume")
	_refresh_status()

func request_stop() -> void:
	if not _bound or _stop_latched:
		return
	_stop_latched = true
	_requested_paused = true
	_emit_intent("stop")
	_pause.disabled = true
	_resume.disabled = true
	_stop.disabled = true
	_speed.editable = false
	_refresh_status()

func _on_document_stop(source: String) -> void:
	if source == "human_ui":
		request_pause()
	else:
		request_stop()

func _on_window_close() -> void:
	if _bound:
		request_stop()
	else:
		quit()

func _latch_error(reason: String) -> void:
	_fatal = reason
	_pending_text = "无法继续，请检查设置"
	if _claimed:
		write_json_atomic(_config.output_directory,"bootstrap_error.json",{"abi":ABI,"world_epoch":_config.world_epoch,"reason":reason,"native_bind_attempted":_bind_called,"formal_acceptance":"not_run"},false)
	if _start != null:
		_start.disabled = true
		_refresh_status()

func _apply_optional_camera() -> void:
	if not _config.has("camera"):
		return
	var camera: Dictionary = _config.camera
	_main.set("_focus_point",Vector3(camera.focus_m[0],camera.focus_m[1],camera.focus_m[2]))
	_main.set("_yaw_deg",float(camera.yaw_deg))
	_main.set("_pitch_deg",float(camera.pitch_deg))
	_main.set("_distance",float(camera.distance_m))
	_main.apply_camera()

func _build_panel() -> void:
	_layer = CanvasLayer.new()
	_layer.name = "ContinuousDashboard990"
	_layer.layer = 50
	_layer.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(_layer)
	var witness := MouseWitness.new()
	witness.host = self
	witness.process_mode = Node.PROCESS_MODE_ALWAYS
	_layer.add_child(witness)
	var surface := Control.new()
	surface.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	surface.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(surface)
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Microsoft YaHei UI","Microsoft YaHei","Noto Sans CJK SC"])
	var theme := Theme.new()
	theme.default_font = font
	theme.default_font_size = 18
	surface.theme = theme
	_toggle = _button("收起面板",_toggle_dashboard)
	_toggle.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	surface.add_child(_toggle)
	_panel = PanelContainer.new()
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	surface.add_child(_panel)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.025,0.05,0.075,0.96)
	style.border_color = Color(0.15,0.65,0.8)
	style.set_border_width_all(2)
	style.set_corner_radius_all(10)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	_panel.add_theme_stylebox_override("panel",style)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_panel.add_child(_scroll)
	_body = VBoxContainer.new()
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation",8)
	_scroll.add_child(_body)
	_add_label("connection","准备")
	_add_label("setup","")
	_mode_choice = OptionButton.new()
	_mode_choice.add_item("实板控制")
	_mode_choice.add_item("PC直控")
	_mode_choice.select(1 if _config.get("admission_mode","BOARD_PWM")=="PC_DIRECT" else 0)
	_body.add_child(_mode_choice)
	_mode_choice.item_selected.connect(func(_index: int): _refresh_status())
	_confirm = CheckBox.new()
	_confirm.text = "确认当前障碍和蓝红圈设置"
	_body.add_child(_confirm)
	_confirm.toggled.connect(func(_value: bool): _refresh_setup())
	_start = _button("开始",_on_start)
	_body.add_child(_start)
	var speed_row := HBoxContainer.new()
	_body.add_child(speed_row)
	var speed_title := Label.new()
	speed_title.text = "初始速度"
	_labels.speed_title = speed_title
	speed_row.add_child(speed_title)
	_speed = HSlider.new()
	_speed.min_value = 0.0
	_speed.max_value = 0.25
	_speed.step = 0.005
	_speed.value = _requested_speed
	_speed.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_speed.custom_minimum_size.x = 190
	speed_row.add_child(_speed)
	_labels.speed_request = Label.new()
	speed_row.add_child(_labels.speed_request)
	_speed.value_changed.connect(request_speed)
	_add_label("initial","")
	var actions := HBoxContainer.new()
	_body.add_child(actions)
	_pause = _button("暂停",request_pause)
	_resume = _button("继续",request_resume)
	_stop = _button("停止",request_stop)
	for button: Button in [_pause,_resume,_stop]:
		button.disabled = true
		actions.add_child(button)
	_add_label("pending","")
	_add_label("edit_error","")
	for group: Array in [["motion","运动"],["channel","通道"],["source","传感"],["codec","编码"],["ai","AI"],["gate","出口进近"],["board","指令与实板"],["latency","链路耗时"]]:
		var title := Label.new()
		title.text = group[1]
		title.modulate = Color(0.4,0.85,0.95)
		title.add_theme_font_size_override("font_size",20)
		_body.add_child(title)
		_add_label(group[0],"—")
	surface.resized.connect(_fit_panel)
	_suppress_legacy_status()
	_refresh_setup()
	call_deferred("_fit_panel")

func _toggle_dashboard() -> void:
	_panel.visible = not _panel.visible
	_toggle.text = "收起面板" if _panel.visible else "展开面板"

func _suppress_legacy_status() -> void:
	var shell: Object = _main.get("shell")
	if shell == null: return
	for key in ["_right_scroll","_right_panel","_top_band","_bottom_band","_gate_status_label","_presentation_label","_action_status_label","_layout_source_label","_run_button","_pause_button","_continue_button","_stop_button","_lock_button","_unlock_button","_demo_root"]:
		var node: Variant = shell.get(key)
		if node is CanvasItem: node.visible = false
	if not _editor_text_simplified:
		_simplify_editor_text(shell)
		_editor_text_simplified = true

func _simplify_editor_text(node: Node) -> void:
	if node is Label:
		var names := {
			"地质体类型（允许尺寸见任务书8.4）":"地质体类型",
			"选中对象（数值编辑）":"对象编辑",
			"撤销 / 重做（≥50步）":"撤销 / 重做",
			"私有布局文件（仅几何）":"布局文件",
			"随机布局（仅查看器内保留种子）":"随机布局",
			"入口/离开圈（直径0.50m·贴面·距边≥0.25m）":"钻入 / 钻出位置 · 直径0.50m"}
		if names.has(node.text):node.text=names[node.text]
	if node is OptionButton:
		for i in range(node.item_count):
			if node.get_item_text(i)=="入口（蓝圈）":node.set_item_text(i,"钻入位置")
			elif node.get_item_text(i)=="离开（红圈）":node.set_item_text(i,"钻出位置")
	for child in node.get_children():_simplify_editor_text(child)

func _editing_error() -> String:
	var document: Object = _main.get("document")
	if document != null:
		var validation: Dictionary = document.validate_gates()
		var errors: Array = validation.get("errors",[])
		if not errors.is_empty(): return _safe_text(errors[0])
	var shell: Object = _main.get("shell")
	if shell != null:
		for key in ["_gate_status_label","_action_status_label"]:
			var label: Variant = shell.get(key)
			if label is Label and ("拒绝" in label.text or "失败" in label.text or "无效" in label.text):
				return _safe_text(label.text)
	return ""

func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size.y = 38
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(callback)
	return button

func _add_label(key: String, text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(label)
	_labels[key] = label
	return label

func _fit_panel() -> void:
	if _panel == null: return
	var viewport_size := root.get_visible_rect().size
	var width := minf(560.0,maxf(320.0,viewport_size.x-32.0))
	_panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	_panel.offset_left = -width-12.0
	_panel.offset_right = -12.0
	_panel.offset_top = 68.0
	_panel.offset_bottom = maxf(120.0,viewport_size.y-12.0)
	_toggle.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	_toggle.offset_left = -80.0
	_toggle.offset_right = 80.0
	_toggle.offset_top = 12.0
	_toggle.offset_bottom = 52.0

func _safe_text(value: Variant) -> String:
	if value == null or not typeof(value) in [TYPE_STRING,TYPE_INT,TYPE_FLOAT,TYPE_BOOL]:
		return "—"
	if typeof(value) == TYPE_FLOAT and not is_finite(value):
		return "—"
	var result := str(value)
	var secret: String = _config.get("token","")
	if not secret.is_empty():
		result = result.replace(secret,"[已隐藏]")
	return result.replace("\n"," ").replace("\r"," ").substr(0,96)

func _host_status() -> Dictionary:
	if not ordinary_absolute_path(_config.host_status_file,false): return {}
	var loaded := read_json_file(_config.host_status_file,65536)
	# Identity/freshness/terminal validation belongs to the display-only model.
	# Pass a foreign record through so it can invalidate a previously cached end.
	return loaded.value if loaded.ok and loaded.value is Dictionary else {}

func _selected_admission_mode() -> String:
	return "PC_DIRECT" if _mode_choice!=null and _mode_choice.selected==1 else "BOARD_PWM"

func _refresh_status() -> void:
	if _labels.is_empty(): return
	_suppress_legacy_status()
	_labels.speed_request.text = "%.3f m/s" % _requested_speed
	var native: Dictionary = _main.read_continuous_live_state() if _bound else {}
	var metrics: Dictionary = {}
	if _main.has_method("read_continuous_visual_metrics"):
		metrics = _main.read_continuous_visual_metrics()
	var view: Dictionary = _dashboard.update(str(_config.world_epoch),str(_config.get("operation_id","")),_host_status(),native,int(Time.get_unix_time_from_system()*1000.0),metrics,not _fatal.is_empty())
	var host: Dictionary = view.host
	var fresh: bool = view.fresh
	if (fresh or view.complete) and host.get("initial_speed_latched",false) == true:
		_initial_speed_latched = true
		if finite_number(host.get("latched_initial_speed_m_s")):
			_latched_initial_speed = float(host.latched_initial_speed_m_s)
	_labels.speed_title.text = "下次初始" if _initial_speed_latched else "初始速度"
	_labels.initial.text = "本次初始 %.3f m/s   下次初始 %.3f m/s" % [_latched_initial_speed if _initial_speed_latched else _requested_speed,_requested_speed]
	_labels.connection.text = "%s · %s\n%s" % ["PC直控" if _selected_admission_mode()=="PC_DIRECT" else "实板控制",view.state,view.connection]
	for key in ["motion","channel","source","codec","ai","gate","board","latency"]:
		_labels[key].text = view.rows[key]
	var pending := ""
	var operator: Dictionary = Dashboard.dictionary(host.get("operator"))
	if Dashboard.integer(operator.get("ack_seq")) and int(operator.ack_seq)==_intent_seq and _intent_seq>0:
		if operator.get("state") in ["preference_saved","next_initial_stored"]:
			pending = "下次初始速度已保存"
		elif operator.get("state") == "failed": pending = "设置未完成"
	if _requested_paused and _bound and not _stop_latched:
		pending = "已暂停" if Dashboard.finite(native.get("speed_m_s")) and native.speed_m_s==0 else "暂停中"
	if _stop_latched: pending = "已停止" if Dashboard.dictionary(host.get("board")).get("stop_acknowledged")==true else "停止中"
	if view.complete:
		_terminal_complete_observed = true
		pending = "已完成 · 实板已停止"
	elif not str(native.get("fault","")).is_empty(): pending = "已停止"
	if not _fatal.is_empty(): pending = "无法继续，请检查设置"
	_labels.pending.text = pending
	_labels.pending.visible = not pending.is_empty()
	_labels.edit_error.text = _editing_error()
	_labels.edit_error.visible = not _labels.edit_error.text.is_empty()
	_labels.setup.visible = not _start_attempted
	_confirm.visible = not _start_attempted
	_start.visible = not _start_attempted
	_fit_panel()

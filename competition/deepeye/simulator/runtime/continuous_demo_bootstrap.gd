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

class MouseWitness extends Node:
	var host: Object
	func _input(event: InputEvent) -> void:
		if is_instance_valid(host):
			host.observe_mouse(event)

var _config: Dictionary = {}
var _main: Node
var _layer: CanvasLayer
var _panel: PanelContainer
var _body: VBoxContainer
var _labels: Dictionary = {}
var _start: Button
var _pause: Button
var _resume: Button
var _stop: Button
var _speed: HSlider
var _confirm: CheckBox
var _claimed := false
var _start_attempted := false
var _bind_called := false
var _bound := false
var _drag_seen := false
var _gate_setup_seen := false
var _left_held := false
var _mouse_travel := 0.0
var _requested_speed := 0.1
var _requested_paused := true
var _stop_latched := false
var _intent_seq := 0
var _last_intent_tick := 0
var _host_seq := -1
var _pending_text := "先用鼠标拖拽障碍、设置蓝红门，再确认并开始。"
var _fatal := ""
var _source_objects := 0
var _source_pieces := 0

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
	var error := parser.parse(file.get_as_text())
	file.close()
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
	_labels.setup.text = "鼠标拖拽障碍：%s    蓝红门设置：%s" % ["已观察" if _drag_seen else "等待操作","已观察" if _gate_setup_seen else "等待操作"]
	_start.disabled = _start_attempted or not _drag_seen or not _gate_setup_seen or not _confirm.button_pressed

func _on_start() -> void:
	if _start_attempted or not _drag_seen or not _gate_setup_seen or not _confirm.button_pressed:
		return
	_start_attempted = true
	_refresh_setup()
	_confirm.disabled = true
	var snapshot := capture_private(_main,bool(_config.get("require_box_only",false)))
	if not snapshot.ok:
		_latch_error(snapshot.reason)
		return
	snapshot.erase("ok")
	snapshot.merge({"abi":ABI,"world_epoch":_config.world_epoch,"contract":CONTRACT,"requirements_sha256":REQUIREMENTS_SHA256,"stage":"prepared_not_installed","formal_acceptance":"not_run","G03":"not_run","all29":"not_run","operator_setup":{"mouse_drag_change_observed":_drag_seen,"gate_change_observed":_gate_setup_seen,"human_confirmation":true,"note":"UI event observation, not a hardware-input attestation"}})
	var prepared := write_json_atomic(_config.output_directory,".frozen.private.prepared.json",snapshot,false)
	if not prepared.ok:
		_latch_error(prepared.reason)
		return
	# The sole call site. No retry, automatic freeze, target, pose or RPC write.
	_bind_called = true
	var installed: Dictionary = _main.bind_continuous_live(int(_config.port),_config.token)
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
	_pending_text = "已冻结原生场景；等待 Root 的真实板卡回执。尚未开始前进。"
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
	_pending_text = "操作请求 #%d 已提交，等待 Root 实板确认。" % _intent_seq

func request_speed(value: float) -> void:
	if _stop_latched or not is_finite(value) or value < 0.0 or value > 0.25:
		return
	_requested_speed = value
	if _bound:
		_emit_intent("set_speed")
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
	_pending_text = "启动/交接失败，保留现场；由 Root 处理，不能重试此输出目录。"
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
	_layer.name = "ContinuousLivePanel801"
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
	theme.default_font_size = 20
	surface.theme = theme
	_panel = PanelContainer.new()
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	surface.add_child(_panel)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.025,0.05,0.075,0.96)
	style.border_color = Color(0.15,0.65,0.8)
	style.set_border_width_all(2)
	style.set_corner_radius_all(10)
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 10
	style.content_margin_bottom = 12
	_panel.add_theme_stylebox_override("panel",style)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",7)
	_panel.add_child(column)
	var collapse := Button.new()
	collapse.text = "实板闭环演示  ·  点击折叠 / 展开"
	collapse.add_theme_font_size_override("font_size",22)
	column.add_child(collapse)
	_body = VBoxContainer.new()
	_body.add_theme_constant_override("separation",7)
	column.add_child(_body)
	collapse.pressed.connect(func(): _body.visible = not _body.visible; _fit_panel())
	_add_label("connection","Root：未连接  |  实板：等待")
	_add_label("setup","")
	_confirm = CheckBox.new()
	_confirm.text = "已完成鼠标摆放和蓝红圈设置，确认开始"
	_body.add_child(_confirm)
	_confirm.toggled.connect(func(_value: bool): _refresh_setup())
	_start = _button("开始实板闭环演示",_on_start)
	_body.add_child(_start)
	var speed_row := HBoxContainer.new()
	_body.add_child(speed_row)
	var speed_title := Label.new()
	speed_title.text = "请求速度"
	speed_row.add_child(speed_title)
	_speed = HSlider.new()
	_speed.min_value = 0.0
	_speed.max_value = 0.25
	_speed.step = 0.005
	_speed.value = 0.1
	_speed.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_speed.custom_minimum_size.x = 230
	speed_row.add_child(_speed)
	_labels.speed_request = Label.new()
	speed_row.add_child(_labels.speed_request)
	_speed.value_changed.connect(request_speed)
	var actions := HBoxContainer.new()
	_body.add_child(actions)
	_pause = _button("请求暂停",request_pause)
	_resume = _button("请求继续",request_resume)
	_stop = _button("停止实板演示",request_stop)
	for button: Button in [_pause,_resume,_stop]:
		button.disabled = true
		actions.add_child(button)
	_add_label("motion","实际速度：等待  |  阶段：等待")
	_add_label("source","传感源：等待真实采样；E4 / 原始 / 压缩字节：等待")
	_add_label("board","板卡 PWM：等待  |  AI 风险 / 方向：等待")
	_add_label("pending",_pending_text)
	var note := _add_label("note","模拟传感器 → 实板编码上传 → PC AI → 实板控制 → 虚拟钻头")
	note.add_theme_font_size_override("font_size",16)
	note.modulate = Color(0.75,0.82,0.9)
	surface.resized.connect(_fit_panel)
	_refresh_setup()
	call_deferred("_fit_panel")

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
	if _panel == null:
		return
	var viewport_size := root.get_visible_rect().size
	var width := minf(780.0,maxf(320.0,viewport_size.x-32.0))
	_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	_panel.offset_left = -width*0.5
	_panel.offset_right = width*0.5
	_panel.offset_bottom = -16.0
	_panel.offset_top = -16.0-maxf(_panel.get_combined_minimum_size().y,46.0)

func _safe_text(value: Variant) -> String:
	if value == null or not typeof(value) in [TYPE_STRING,TYPE_INT,TYPE_FLOAT,TYPE_BOOL]:
		return "等待"
	if typeof(value) == TYPE_FLOAT and not is_finite(value):
		return "等待"
	var result := str(value)
	var secret: String = _config.get("token","")
	if not secret.is_empty():
		result = result.replace(secret,"[已隐藏]")
	return result.replace("\n"," ").replace("\r"," ").substr(0,96)

func _host_status() -> Dictionary:
	if not ordinary_absolute_path(_config.host_status_file,false):
		return {}
	var loaded := read_json_file(_config.host_status_file,65536)
	if not loaded.ok or not loaded.value is Dictionary:
		return {}
	var host: Dictionary = loaded.value
	if host.get("abi") != HOST_ABI or host.get("world_epoch") != _config.world_epoch or not integer_number(host.get("status_seq")) or host.status_seq < _host_seq or not integer_number(host.get("updated_unix_ms")):
		return {}
	var age := int(Time.get_unix_time_from_system()*1000.0)-int(host.updated_unix_ms)
	if age < -1000 or age > HOST_MAX_AGE_MS:
		return {}
	_host_seq = int(host.status_seq)
	return host

func _refresh_status() -> void:
	if _labels.is_empty():
		return
	_labels.speed_request.text = "%.3f m/s" % _requested_speed
	var native: Dictionary = _main.read_continuous_live_state() if _bound else {}
	var host := _host_status()
	var fresh: bool = not host.is_empty() and host.get("connected",false) == true
	var board: Dictionary = host.get("board",{}) if fresh and host.get("board") is Dictionary else {}
	_labels.connection.text = "Root：%s  |  实板：%s" % ["已连接" if fresh else "未连接 / 等待新状态","已连接" if board.get("connected",false) == true else "未连接 / 等待"]
	var actual := "等待原生就绪"
	var phase := "等待开始"
	if native.get("ready",false) == true:
		if finite_number(native.get("speed_m_s")):
			actual = "%.4f m/s" % float(native.speed_m_s)
		phase = _safe_text(native.get("phase"))
	_labels.motion.text = "请求：%.3f m/s%s  |  实际：%s  |  阶段：%s" % [_requested_speed,"（暂停）" if _requested_paused else "",actual,phase]
	var source: Dictionary = host.get("source",{}) if fresh and host.get("source") is Dictionary else {}
	var counts := "等待"
	if source.get("channel_counts") is Array and source.channel_counts.size() == 4:
		var valid := true
		var values: Array[String] = []
		for number in source.channel_counts:
			if number == null: values.append("—")
			elif integer_number(number) and number >= 0 and number <= 4095: values.append(str(int(number)))
			else: valid = false
		if valid: counts = " / ".join(values)
	_labels.source.text = "源采样：%s  |  C0 / C1 / C2 / C3：%s\n编码上传：%s B  /  还原：%s  /  模式：%s" % [_safe_text(source.get("sample_count")),counts,_safe_text(source.get("e4_bytes")),_safe_text(source.get("raw_bytes")),_safe_text(source.get("compressed_bytes"))]
	var ai: Dictionary = host.get("ai",{}) if fresh and host.get("ai") is Dictionary else {}
	_labels.board.text = "板卡 PWM：%s  |  AI 风险：%s  /  方向：%s" % [_safe_text(board.get("pwm")) if board.get("connected",false) == true else "等待",_safe_text(ai.get("risk")),_safe_text(ai.get("direction"))]
	var pending := _pending_text
	var operator: Dictionary = host.get("operator",{}) if fresh and host.get("operator") is Dictionary else {}
	if integer_number(operator.get("ack_seq")) and int(operator.ack_seq) == _intent_seq and _intent_seq > 0:
		if operator.get("state") == "applied":
			pending = "Root 已确认请求 #%d；实际速度见原生读数。" % _intent_seq
		elif operator.get("state") == "failed":
			pending = "Root 报告请求 #%d 失败：%s" % [_intent_seq,_safe_text(operator.get("detail"))]
	if _stop_latched:
		pending = "已请求停止；等待 Root 实板 STOP 回执。"
		if board.get("stop_acknowledged",false) == true and operator.get("state") == "applied" and operator.get("ack_seq") == _intent_seq:
			pending = "Root 报告实板 STOP 已确认。此场景不再重启。"
	if not str(native.get("fault","")).is_empty():
		pending = "原生保护停止：%s；实板状态由 Root 单独确认。" % _safe_text(native.fault)
	if not _fatal.is_empty():
		pending = "交接失败：%s。保留现场，由 Root 处理。" % _safe_text(_fatal)
	_labels.pending.text = pending
	_labels.note.text = "模拟传感器 → 实板编码上传 → PC AI → 实板控制 → 虚拟钻头（%d 障碍 / %d 源体）" % [_source_objects,_source_pieces] if _bound else "布局未冻结；源几何为名义工程包络，非精确网格 / PDE 合格结果。G03 / all29：not_run"
	_fit_panel()

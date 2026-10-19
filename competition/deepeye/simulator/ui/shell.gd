class_name EditorShell
extends CanvasLayer
## G02 shell UI: left Chinese toolbar / central 3D viewport (>=60% at 1080p) /
## right link+authority status / bottom event timeline.
##
## The central region is intentionally left empty so the 3D view shows through.
## Mouse input over any panel is consumed by the Control tree, and main.gd only
## moves the camera in _unhandled_input, so UI input can never move the camera.
## Run/continue/pause buttons stay disabled until a real authority+mode bridge is
## connected; the "停止" button and global Esc only emit stop_requested.

const DocScript = preload("res://editor/scene_document.gd")
const LayoutStoreScript = preload("res://editor/layout_store.gd")

var pick_mode := "select" ## "select" | "add" | "gate"
var axis_lock := "free" ## "free" | "x" | "y" | "z"
var snap_enabled := true
var active_gate := "entry"

var _main: Node = null
var _document = null
var _root: Control
var _left_panel: PanelContainer
var _right_panel: PanelContainer
var _top_strip: PanelContainer
var _bottom_panel: PanelContainer
var _updating := false
var _initialized := false
var _layout_store = null
var _dialog_action := ""
var last_file_result: Dictionary = {}

var _pick_buttons: Dictionary = {}
var _kind_option: OptionButton
var _snap_check: CheckButton
var _axis_option: OptionButton
var _selected_label: Label
var _position_spins: Array = []
var _rotation_spins: Array = []
var _size_spins: Array = []
var _undo_button: Button
var _redo_button: Button
var _history_label: Label
var _save_button: Button
var _open_button: Button
var _layout_source_label: Label
var _file_dialog: FileDialog
var _seed_spin: SpinBox
var _count_spin: SpinBox
var _which_option: OptionButton
var _face_option: OptionButton
var _gate_u: SpinBox
var _gate_v: SpinBox
var _gate_status_label: Label
var _status_labels: Dictionary = {}
var _run_button: Button
var _pause_button: Button
var _continue_button: Button
var _stop_button: Button
var _lock_button: Button
var _unlock_button: Button
var _run_state_label: Label
var _pending_label: Label
var _overlap_label: Label
var _events_log: RichTextLabel
var _hint_label: Label
var _ratio_label: Label
var _ticks_check: CheckButton

func _ready() -> void:
	if _initialized:
		return
	_initialized = true
	_build_ui()

func bind_editor(main_node: Node, document) -> void:
	_main = main_node
	_document = document
	if _layout_store == null:
		_layout_store = LayoutStoreScript.new()
	_document.layout_changed.connect(_on_document_changed)
	_document.gates_changed.connect(_on_gates_changed)
	_document.state_changed.connect(_on_state_changed)
	_document.event_logged.connect(_on_event_logged)
	_document.selection_changed.connect(_on_selection_changed)
	for event in _document.events:
		_append_event(event)
	_refresh_all()

# ---------------------------------------------------------------------------
# UI construction
# ---------------------------------------------------------------------------

func _build_ui() -> void:
	_root = Control.new()
	_root.name = "ShellRoot"
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC"])
	var theme := Theme.new()
	theme.default_font = font
	theme.default_font_size = 15
	_root.theme = theme
	add_child(_root)
	_root.resized.connect(_on_root_resized)

	_left_panel = PanelContainer.new()
	_left_panel.name = "LeftToolbar"
	_left_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_left_panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_left_panel.add_child(scroll)
	var left_box := VBoxContainer.new()
	left_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_box.add_theme_constant_override("separation", 8)
	scroll.add_child(left_box)
	_build_left(left_box)

	_right_panel = PanelContainer.new()
	_right_panel.name = "RightStatus"
	_right_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_right_panel)
	var right_box := VBoxContainer.new()
	right_box.add_theme_constant_override("separation", 8)
	_right_panel.add_child(right_box)
	_build_right(right_box)
	_build_file_dialog()

	_top_strip = PanelContainer.new()
	_top_strip.name = "TopBar"
	_top_strip.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_top_strip)
	var top_box := HBoxContainer.new()
	top_box.add_theme_constant_override("separation", 14)
	_top_strip.add_child(top_box)
	for key in ["source", "topology", "baud", "age"]:
		var label := Label.new()
		label.text = _top_label(key)
		top_box.add_child(label)
		_status_labels[key] = label
	_run_state_label = Label.new()
	_run_state_label.text = "状态: 编辑中"
	top_box.add_child(_run_state_label)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top_box.add_child(spacer)
	_ratio_label = Label.new()
	_ratio_label.text = "3D视口: --"
	top_box.add_child(_ratio_label)

	_bottom_panel = PanelContainer.new()
	_bottom_panel.name = "EventTimeline"
	_bottom_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_bottom_panel)
	var bottom_box := VBoxContainer.new()
	bottom_box.add_theme_constant_override("separation", 2)
	_bottom_panel.add_child(bottom_box)
	var events_title := Label.new()
	events_title.text = "事件时间线（状态机/编辑/链路；未连接事件不伪造）"
	bottom_box.add_child(events_title)
	_events_log = RichTextLabel.new()
	_events_log.bbcode_enabled = true
	_events_log.scroll_following = true
	_events_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bottom_box.add_child(_events_log)
	_relayout(_root.size)

func _build_left(box: VBoxContainer) -> void:
	box.add_child(_title("编辑工具"))
	var group := ButtonGroup.new()
	var tool_row := HBoxContainer.new()
	box.add_child(tool_row)
	_pick_buttons["select"] = _tool_button("选择", group, true, "左键选择/拖拽移动对象")
	_pick_buttons["add"] = _tool_button("添加", group, false, "左键在 y=0 平面点击摆放当前类型")
	_pick_buttons["gate"] = _tool_button("拾取圈心", group, false, "左键点击立方体面设置所选圈心")
	for key in ["select", "add", "gate"]:
		tool_row.add_child(_pick_buttons[key])

	box.add_child(_title("地质体类型（允许尺寸见任务书8.4）"))
	_kind_option = OptionButton.new()
	for i in DocScript.KINDS.size():
		_kind_option.add_item(DocScript.KIND_LABELS[DocScript.KINDS[i]], i)
	box.add_child(_kind_option)
	var op_row := HBoxContainer.new()
	box.add_child(op_row)
	op_row.add_child(_button("添加物体", _on_add_pressed))
	op_row.add_child(_button("复制", _on_duplicate_pressed))
	op_row.add_child(_button("删除", _on_delete_pressed))
	var opt_row := HBoxContainer.new()
	box.add_child(opt_row)
	_snap_check = CheckButton.new()
	_snap_check.text = "0.25m 网格吸附"
	_snap_check.button_pressed = true
	_snap_check.toggled.connect(func(pressed: bool) -> void: snap_enabled = pressed)
	opt_row.add_child(_snap_check)
	_axis_option = OptionButton.new()
	for i in ["自由", "轴X", "轴Y", "轴Z"].size():
		_axis_option.add_item(["自由", "轴X", "轴Y", "轴Z"][i], i)
	_axis_option.item_selected.connect(func(index: int) -> void: axis_lock = ["free", "x", "y", "z"][index])
	opt_row.add_child(_axis_option)

	box.add_child(_title("选中对象（数值编辑）"))
	_selected_label = Label.new()
	_selected_label.text = "未选择"
	box.add_child(_selected_label)
	box.add_child(_spin_row("位置 X/Y/Z", ["m", "m", "m"], 0.25, 15.0, _position_spins, _on_position_changed))
	box.add_child(_spin_row("旋转 X/Y/Z", ["°", "°", "°"], 5.0, 180.0, _rotation_spins, _on_rotation_changed))
	box.add_child(_spin_row("尺寸 X/Y/Z", ["m", "m", "m"], 0.5, 20.0, _size_spins, _on_size_changed))

	box.add_child(_title("撤销 / 重做（≥50步）"))
	var hist_row := HBoxContainer.new()
	box.add_child(hist_row)
	_undo_button = _button("撤销", _on_undo_pressed)
	_redo_button = _button("重做", _on_redo_pressed)
	hist_row.add_child(_undo_button)
	hist_row.add_child(_redo_button)
	_history_label = Label.new()
	_history_label.text = "撤销 0 / 重做 0"
	box.add_child(_history_label)

	box.add_child(_title("私有布局文件（仅几何）"))
	var file_row := HBoxContainer.new()
	box.add_child(file_row)
	_save_button = _button("保存布局…", _on_save_layout_pressed)
	_open_button = _button("打开布局…", _on_open_layout_pressed)
	_save_button.tooltip_text = "另存为新的本地 JSON；不覆盖已有文件"
	_open_button.tooltip_text = "严格校验后替换当前几何；失败不改变当前布局"
	file_row.add_child(_save_button)
	file_row.add_child(_open_button)
	_layout_source_label = Label.new()
	_layout_source_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_layout_source_label.text = "布局来源: 初始默认 · 种子未知"
	box.add_child(_layout_source_label)

	box.add_child(_title("随机布局（仅查看器内保留种子）"))
	var rand_row := HBoxContainer.new()
	box.add_child(rand_row)
	_seed_spin = _spin(0.0, 999999.0, 1.0, 1.0)
	_count_spin = _spin(1.0, 30.0, 1.0, 10.0)
	rand_row.add_child(_small_label("种子"))
	rand_row.add_child(_seed_spin)
	rand_row.add_child(_small_label("数量"))
	rand_row.add_child(_count_spin)
	var rand_row2 := HBoxContainer.new()
	box.add_child(rand_row2)
	rand_row2.add_child(_button("随机生成", _on_random_pressed))
	rand_row2.add_child(_button("清空空场", _on_clear_pressed))

	box.add_child(_title("入口/离开圈（直径0.30m·贴面·距边≥0.15m）"))
	_which_option = OptionButton.new()
	_which_option.add_item("入口（蓝圈）", 0)
	_which_option.add_item("离开（红圈）", 1)
	_which_option.item_selected.connect(_on_gate_which_selected)
	box.add_child(_which_option)
	_face_option = OptionButton.new()
	for i in DocScript.FACES.size():
		_face_option.add_item(DocScript.FACE_LABELS[DocScript.FACES[i]], i)
	_face_option.item_selected.connect(func(_index: int) -> void: _apply_gate_edit("面"))
	box.add_child(_face_option)
	var uv_row := HBoxContainer.new()
	box.add_child(uv_row)
	uv_row.add_child(_small_label("u"))
	_gate_u = _spin(-14.85, 14.85, 0.05, 0.0)
	_gate_v = _spin(-14.85, 14.85, 0.05, 0.0)
	uv_row.add_child(_gate_u)
	uv_row.add_child(_small_label("v"))
	uv_row.add_child(_gate_v)
	_gate_u.value_changed.connect(func(_value: float) -> void: _apply_gate_edit("u"))
	_gate_v.value_changed.connect(func(_value: float) -> void: _apply_gate_edit("v"))
	_gate_status_label = Label.new()
	_gate_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_gate_status_label.text = "几何有效（编辑器）· 初始化空间/路线：待权威"
	box.add_child(_gate_status_label)

	box.add_child(_title("相机"))
	var cam_grid := GridContainer.new()
	cam_grid.columns = 4
	box.add_child(cam_grid)
	for view in [["顶", "top"], ["底", "bottom"], ["前", "front"], ["后", "back"],
			["左", "left"], ["右", "right"], ["等轴测", "iso"]]:
		var view_name: String = view[1]
		var cam_button := _button(view[0], func() -> void: _request_camera(view_name))
		cam_grid.add_child(cam_button)
	cam_grid.add_child(_button("聚焦选中", func() -> void: _request_focus()))
	_ticks_check = CheckButton.new()
	_ticks_check.text = "坐标刻度"
	_ticks_check.button_pressed = true
	_ticks_check.toggled.connect(_on_ticks_toggled)
	box.add_child(_ticks_check)
	_hint_label = Label.new()
	_hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint_label.text = "左键选择 · 右键环绕 · 中键平移 · 滚轮缩放 · 双击聚焦 · R旋转 · S缩放 · Esc 停止请求"
	box.add_child(_hint_label)

func _build_right(box: VBoxContainer) -> void:
	box.add_child(_title("链路与权威状态（未连接不伪造）"))
	for row in [["工况来源", "source"], ["控制拓扑", "topology"], ["实际波特率", "baud"],
			["数据年龄", "age"], ["AI 状态", "ai"], ["权威桥", "bridge"]]:
		var label := Label.new()
		label.text = row[0] + ": 未连接"
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(label)
		_status_labels[row[1]] = label
	box.add_child(_title("运行控制（桥未连接=禁用）"))
	var run_row := HBoxContainer.new()
	box.add_child(run_row)
	_run_button = _button("运行", _on_run_pressed)
	_pause_button = _button("暂停", _on_pause_pressed)
	_continue_button = _button("继续", _on_continue_pressed)
	run_row.add_child(_run_button)
	run_row.add_child(_pause_button)
	run_row.add_child(_continue_button)
	for button in [_run_button, _pause_button, _continue_button]:
		button.disabled = true
		button.tooltip_text = "未连接控制权威/模式桥：运行与继续保持禁用"
	var stop_row := HBoxContainer.new()
	box.add_child(stop_row)
	_stop_button = _button("停止（等同 Esc）", _on_stop_pressed)
	stop_row.add_child(_stop_button)
	box.add_child(_title("布局锁定"))
	var lock_row := HBoxContainer.new()
	box.add_child(lock_row)
	_lock_button = _button("锁定布局", _on_lock_pressed)
	_unlock_button = _button("解锁", _on_unlock_pressed)
	lock_row.add_child(_lock_button)
	lock_row.add_child(_unlock_button)
	box.add_child(_title("编辑警告（重叠按优先级解析）"))
	_overlap_label = Label.new()
	_overlap_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_overlap_label.text = "无重叠警告"
	box.add_child(_overlap_label)
	box.add_child(_title("权威待办（编辑器不替代）"))
	_pending_label = Label.new()
	_pending_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_pending_label.text = "-"
	box.add_child(_pending_label)
	var greybox_note := Label.new()
	greybox_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	greybox_note.text = "开发灰盒：临时图元替换件，非最终画质、非最终资产（B 交付前可见标注）。"
	box.add_child(greybox_note)

func _build_file_dialog() -> void:
	_file_dialog = FileDialog.new()
	_file_dialog.name = "LayoutFileDialog"
	_file_dialog.access = FileDialog.ACCESS_FILESYSTEM
	_file_dialog.use_native_dialog = false
	_file_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	_file_dialog.add_filter("*.json", "DeepEye 私有布局 JSON")
	_file_dialog.file_selected.connect(_on_file_selected)
	_file_dialog.canceled.connect(_on_file_dialog_canceled)
	add_child(_file_dialog)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _title(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 16)
	return label

func _small_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	return label

func _button(text: String, handler: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.pressed.connect(handler)
	return button

func _tool_button(text: String, group: ButtonGroup, pressed: bool, tooltip: String) -> Button:
	var button := Button.new()
	button.text = text
	button.toggle_mode = true
	button.button_group = group
	button.button_pressed = pressed
	button.tooltip_text = tooltip
	button.toggled.connect(_on_tool_toggled.bind(button))
	return button

func _on_tool_toggled(is_pressed: bool, button: Button) -> void:
	if not is_pressed:
		return
	match button.text:
		"选择":
			pick_mode = "select"
		"添加":
			pick_mode = "add"
		_:
			pick_mode = "gate"

func _spin(minimum: float, maximum: float, step: float, value: float) -> SpinBox:
	var spin := SpinBox.new()
	spin.min_value = minimum
	spin.max_value = maximum
	spin.step = step
	spin.value = value
	spin.allow_greater = false
	spin.allow_lesser = false
	spin.custom_minimum_size = Vector2(60, 0)
	return spin

func _spin_row(caption: String, units: Array, step: float, limit: float, spins: Array, handler: Callable) -> VBoxContainer:
	var wrapper := VBoxContainer.new()
	wrapper.add_theme_constant_override("separation", 2)
	var caption_label := Label.new()
	caption_label.text = caption
	wrapper.add_child(caption_label)
	var row := HBoxContainer.new()
	wrapper.add_child(row)
	for unit in units:
		var spin := _spin(-limit, limit, step, 0.0)
		spin.value_changed.connect(handler)
		row.add_child(spin)
		spins.append(spin)
	return wrapper

func _top_label(key: String) -> String:
	match key:
		"source":
			return "工况来源: 未连接"
		"topology":
			return "控制拓扑: 未连接"
		"baud":
			return "实际baud: 未连接"
		"age":
			return "数据年龄: 未连接"
		_:
			return key

func _on_root_resized() -> void:
	_relayout(_root.size)

func _relayout(viewport_size: Vector2) -> void:
	if viewport_size.x < 100.0 or viewport_size.y < 100.0:
		return
	var left_w := clampf(viewport_size.x * 0.13, 210.0, 330.0)
	left_w = maxf(left_w, _left_panel.get_combined_minimum_size().x)
	var right_w := clampf(viewport_size.x * 0.14, 220.0, 400.0)
	var bottom_h := clampf(viewport_size.y * 0.09, 84.0, 180.0)
	var top_h := 30.0
	_anchor(_left_panel, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, left_w, 0.0)
	_anchor(_right_panel, 1.0, 0.0, 1.0, 1.0, -right_w, 0.0, 0.0, 0.0)
	_anchor(_top_strip, 0.0, 0.0, 1.0, 0.0, left_w, 0.0, -right_w, top_h)
	_anchor(_bottom_panel, 0.0, 1.0, 1.0, 1.0, left_w, -bottom_h, -right_w, 0.0)
	var central := (viewport_size.x - left_w - right_w) * (viewport_size.y - top_h - bottom_h)
	var ratio := central / maxf(1.0, viewport_size.x * viewport_size.y) * 100.0
	_ratio_label.text = "3D视口: %.1f%%" % ratio

func _anchor(control: Control, al: float, at: float, ar: float, ab: float, ol: float, ot: float, or_: float, ob: float) -> void:
	control.anchor_left = al
	control.anchor_top = at
	control.anchor_right = ar
	control.anchor_bottom = ab
	control.offset_left = ol
	control.offset_top = ot
	control.offset_right = or_
	control.offset_bottom = ob

# ---------------------------------------------------------------------------
# Document refresh
# ---------------------------------------------------------------------------

func _on_document_changed() -> void:
	_refresh_all()

func _on_gates_changed() -> void:
	_sync_gate_controls()

func _on_state_changed(_state: String) -> void:
	_refresh_all()

func _on_selection_changed(_object_id: int) -> void:
	_refresh_selection_fields()

func _on_event_logged(event: Dictionary) -> void:
	_append_event(event)

func _append_event(event: Dictionary) -> void:
	var color := "#d8d8d8"
	match String(event.get("level", "")):
		"警示":
			color = "#ff8866"
		"操作":
			color = "#cfe8ff"
		"系统":
			color = "#9fb4d0"
		"状态":
			color = "#a8e6a0"
		"测试":
			color = "#c9b6ff"
	var line := "[color=%s]#%d %s [%s] %s[/color]" % [
		color, int(event.get("seq", 0)), str(event.get("time", "")), str(event.get("level", "")), str(event.get("text", ""))]
	_events_log.append_text(line + "\n")

func _refresh_all() -> void:
	if _document == null:
		return
	var snapshot: Dictionary = _document.status_snapshot()
	_status_labels["source"].text = "工况来源: " + snapshot.source
	_status_labels["topology"].text = "控制拓扑: " + snapshot.topology
	_status_labels["baud"].text = "实际波特率: " + snapshot.baud
	_status_labels["age"].text = "数据年龄: " + snapshot.age
	_status_labels["ai"].text = "AI 状态: " + snapshot.ai
	_status_labels["bridge"].text = "权威桥: " + snapshot.bridge
	if _run_state_label != null:
		_run_state_label.text = "状态: " + snapshot.run_state_cn
	_history_label.text = "撤销 %d / 重做 %d" % [snapshot.undo_depth, snapshot.redo_depth]
	_undo_button.disabled = snapshot.undo_depth == 0 or not snapshot.can_edit
	_redo_button.disabled = snapshot.redo_depth == 0 or not snapshot.can_edit
	if _save_button != null:
		_save_button.disabled = not snapshot.can_edit
	if _open_button != null:
		_open_button.disabled = not snapshot.can_edit
	if _layout_source_label != null:
		var seed_text := "种子 %d" % int(snapshot.random_seed) if bool(snapshot.seed_known) else "种子未知"
		_layout_source_label.text = "布局来源: %s · %s" % [String(snapshot.layout_origin), seed_text]
	if snapshot.gate_valid:
		_gate_status_label.text = "几何有效（编辑器）· 初始化空间/路线：待权威"
	else:
		_gate_status_label.text = "当前圈心无效: " + "; ".join(snapshot.gate_errors)
	var pending: Array = snapshot.authority_pending
	_pending_label.text = "\n".join(pending)
	var warnings: Array = _document.overlap_warnings()
	if warnings.is_empty():
		_overlap_label.text = "无重叠警告"
	else:
		_overlap_label.text = "%d 条重叠警告（首条）：%s" % [warnings.size(), warnings[0]]
	_sync_gate_controls()
	_refresh_selection_fields()

func _refresh_selection_fields() -> void:
	if _document == null:
		return
	_updating = true
	var selected_id: int = _document.selected_id
	if selected_id == -1:
		_selected_label.text = "未选择（对象数 %d）" % _document.obstacle_count()
		for spin in _position_spins + _rotation_spins + _size_spins:
			spin.value = 0.0
	else:
		var obstacle: Dictionary = _document.obstacle_by_id(selected_id)
		if obstacle.is_empty():
			_selected_label.text = "未选择（对象数 %d）" % _document.obstacle_count()
		else:
			_selected_label.text = "已选 #%d %s" % [selected_id, DocScript.KIND_LABELS.get(String(obstacle.kind), String(obstacle.kind))]
			_position_spins[0].value = obstacle.position.x
			_position_spins[1].value = obstacle.position.y
			_position_spins[2].value = obstacle.position.z
			_rotation_spins[0].value = obstacle.rotation_deg.x
			_rotation_spins[1].value = obstacle.rotation_deg.y
			_rotation_spins[2].value = obstacle.rotation_deg.z
			_size_spins[0].value = obstacle.size.x
			_size_spins[1].value = obstacle.size.y
			_size_spins[2].value = obstacle.size.z
	_updating = false

func _sync_gate_controls() -> void:
	if _document == null:
		return
	_updating = true
	var gate: Dictionary = _document.gates.get(active_gate, {})
	var face_index: int = DocScript.FACES.find(String(gate.get("face", "front")))
	_face_option.selected = maxi(0, face_index)
	_gate_u.value = float(gate.get("u", 0.0))
	_gate_v.value = float(gate.get("v", 0.0))
	_updating = false

func _configure_file_dialog(action: String) -> bool:
	_dialog_action = action
	var layout_dir: String = _layout_store.default_layout_dir()
	if not DirAccess.dir_exists_absolute(layout_dir):
		DirAccess.make_dir_recursive_absolute(layout_dir)
	_file_dialog.current_dir = layout_dir
	_file_dialog.current_file = ""
	if action == "save":
		var stamp := Time.get_datetime_string_from_system().replace(":", "-").replace(" ", "_")
		_file_dialog.title = "另存私有布局（仅几何，不覆盖）"
		_file_dialog.file_mode = FileDialog.FILE_MODE_SAVE_FILE
		_file_dialog.current_file = "layout-%s.json" % stamp
	else:
		_file_dialog.title = "打开私有布局（严格校验）"
		_file_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	_file_dialog.popup_centered_ratio(0.72)
	return true

func _on_save_layout_pressed() -> void:
	if _document == null or _layout_store == null:
		_set_file_failure("unavailable", "布局文件服务不可用")
		return
	if not _document.can_edit():
		_set_file_failure("edit_blocked", _document.edit_block_reason())
		return
	_configure_file_dialog("save")

func _on_open_layout_pressed() -> void:
	if _document == null or _layout_store == null:
		_set_file_failure("unavailable", "布局文件服务不可用")
		return
	if not _document.can_edit():
		_set_file_failure("edit_blocked", _document.edit_block_reason())
		return
	_configure_file_dialog("open")

func _on_file_selected(path: String) -> void:
	var action := _dialog_action
	_dialog_action = ""
	if _file_dialog != null:
		_file_dialog.hide()
	if _document == null or _layout_store == null:
		_set_file_failure("unavailable", "布局文件服务不可用")
		return
	if not _document.can_edit():
		_set_file_failure("edit_blocked", _document.edit_block_reason())
		return
	match action:
		"save":
			var exported: Dictionary = _document.export_layout_text()
			if not bool(exported.get("ok", false)):
				_set_file_failure(String(exported.get("code", "export_failed")), _result_reason(exported))
				return
			var stored: Dictionary = _layout_store.save_new(path, String(exported.get("text", "")))
			if not bool(stored.get("ok", false)):
				_set_file_failure(String(stored.get("code", "save_failed")), _result_reason(stored))
				return
			last_file_result = {
				"ok": true,
				"action": "save",
				"path": String(stored.get("path", path)),
				"bytes": int(stored.get("bytes", 0)),
				"layout_hash": String(exported.get("layout_hash", "")),
				"count": int(exported.get("count", 0)),
			}
			_set_hint("已另存为新文件（仅几何，hash %s）" % String(exported.get("layout_hash", "")).substr(0, 12))
		"open":
			var read_result: Dictionary = _layout_store.read_text(path)
			if not bool(read_result.get("ok", false)):
				_set_file_failure(String(read_result.get("code", "read_failed")), _result_reason(read_result))
				return
			var applied: Dictionary = _document.apply_layout_text(String(read_result.get("text", "")))
			if not bool(applied.get("ok", false)):
				_set_file_failure(String(applied.get("code", "layout_rejected")), _result_reason(applied))
				return
			last_file_result = {
				"ok": true,
				"action": "open",
				"path": String(read_result.get("path", path)),
				"bytes": int(read_result.get("bytes", 0)),
				"layout_hash": String(applied.get("layout_hash", "")),
				"count": int(applied.get("count", 0)),
				"seed_known": false,
				"layout_origin": String(applied.get("layout_origin", "文件布局")),
			}
			_set_hint("已打开布局文件；编辑历史已重置，种子未知（hash %s）"
				% String(applied.get("layout_hash", "")).substr(0, 12))
		_:
			_set_file_failure("no_action", "未选择布局文件操作")

func _on_file_dialog_canceled() -> void:
	_dialog_action = ""
	last_file_result = {
		"ok": false,
		"canceled": true,
		"code": "canceled",
		"reason": "已取消布局文件操作",
		"errors": ["已取消布局文件操作"],
	}
	_set_hint("已取消布局文件操作；当前布局未改变")

func _result_reason(result: Dictionary) -> String:
	if result.has("reason"):
		return String(result.reason).substr(0, 512)
	var errors: Array = result.get("errors", [])
	if not errors.is_empty():
		return String(errors[0]).substr(0, 512)
	return "布局文件操作失败"

func _set_file_failure(code: String, reason: String) -> void:
	var bounded := reason.substr(0, 512)
	last_file_result = {
		"ok": false,
		"canceled": false,
		"code": code,
		"reason": bounded,
		"errors": [bounded],
	}
	_set_hint("布局文件操作失败：" + bounded)

# ---------------------------------------------------------------------------
# Edit actions
# ---------------------------------------------------------------------------

func _current_kind() -> String:
	return DocScript.KINDS[maxi(0, _kind_option.selected)]

func current_kind() -> String:
	return _current_kind()

func on_gate_result(result: Dictionary, changed: String) -> void:
	_on_gate_result(result, changed)

func _on_add_pressed() -> void:
	if _document == null:
		return
	_document.add_obstacle(_current_kind())

func _on_duplicate_pressed() -> void:
	if _document == null:
		return
	var result: Dictionary = _document.duplicate_obstacle(_document.selected_id)
	if bool(result.get("ok", false)):
		_document.select_object(int(result.get("id", -1)))
	else:
		_set_hint("复制被拒绝：" + String(result.get("reason", "")))

func _on_delete_pressed() -> void:
	if _document == null:
		return
	_document.remove_obstacle(_document.selected_id)

func _on_undo_pressed() -> void:
	if _document != null:
		_document.undo()

func _on_redo_pressed() -> void:
	if _document != null:
		_document.redo()

func _on_random_pressed() -> void:
	if _document == null:
		return
	var result: Dictionary = _document.randomize_layout(int(_seed_spin.value), int(_count_spin.value))
	if not bool(result.get("ok", false)):
		_set_hint("随机布局被拒绝：" + String(result.get("reason", "")))

func _on_clear_pressed() -> void:
	if _document != null:
		_document.reset_layout()

func _on_position_changed(_value: float) -> void:
	if _updating or _document == null or _document.selected_id == -1:
		return
	_document.update_obstacle(_document.selected_id, {"position": Vector3(
		_position_spins[0].value, _position_spins[1].value, _position_spins[2].value)})

func _on_rotation_changed(_value: float) -> void:
	if _updating or _document == null or _document.selected_id == -1:
		return
	_document.update_obstacle(_document.selected_id, {"rotation_deg": Vector3(
		_rotation_spins[0].value, _rotation_spins[1].value, _rotation_spins[2].value)})

func _on_size_changed(_value: float) -> void:
	if _updating or _document == null or _document.selected_id == -1:
		return
	var limit_result: Dictionary = _document.update_obstacle(_document.selected_id, {"size": Vector3(
		_size_spins[0].value, _size_spins[1].value, _size_spins[2].value)})
	if not bool(limit_result.get("ok", false)):
		_set_hint("尺寸被拒绝：" + String(limit_result.get("reason", "")))

func _apply_gate_edit(changed: String) -> void:
	if _updating or _document == null:
		return
	var face: String = DocScript.FACES[maxi(0, _face_option.selected)]
	var result: Dictionary = _document.set_gate(active_gate, face, _gate_u.value, _gate_v.value)
	_on_gate_result(result, changed)

func _on_gate_result(result: Dictionary, changed: String) -> void:
	if _document == null:
		return
	if bool(result.get("ok", false)):
		_gate_status_label.text = "几何有效（编辑器）· 初始化空间/路线：待权威"
		_set_hint("圈心已更新（%s）" % changed)
	else:
		var errors: Array = result.get("errors", [result.get("reason", "被拒绝")])
		_gate_status_label.text = "拒绝: " + String(errors[0])
		_set_hint("圈心设置被拒绝，未移动任何圈：" + String(errors[0]))
	_sync_gate_controls()

func _set_hint(text: String) -> void:
	if _hint_label != null:
		_hint_label.text = text

func _on_run_pressed() -> void:
	if _document != null:
		_document.request_run()
	_refresh_all()

func _on_pause_pressed() -> void:
	if _document != null:
		_document.request_pause()

func _on_continue_pressed() -> void:
	if _document != null:
		_document.request_continue()

func _on_gate_which_selected(index: int) -> void:
	active_gate = "entry" if index == 0 else "exit"
	_sync_gate_controls()

func _on_ticks_toggled(pressed: bool) -> void:
	if _main != null and _main.has_method("set_ticks_visible"):
		_main.set_ticks_visible(pressed)

func _on_stop_pressed() -> void:
	if _document != null:
		_document.request_stop("停止按钮")

func _on_lock_pressed() -> void:
	if _document != null:
		_document.lock_layout()

func _on_unlock_pressed() -> void:
	if _document != null:
		_document.unlock_layout()

func _request_camera(view_name: String) -> void:
	if _main != null and _main.has_method("set_camera_view"):
		_main.set_camera_view(view_name)

func _request_focus() -> void:
	if _main != null and _main.has_method("focus_selected"):
		_main.focus_selected()

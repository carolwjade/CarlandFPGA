extends SceneTree
## G02 responsive UI-fit regression (headless only).
##
## This test instantiates the real viewer scene and measures the actual container
## rectangles. It is a layout/status regression, not native DPI, OS input, game
## quality or G02/H01-H15 acceptance. Run from the simulator project:
##   godot --headless --path . --script res://tests/test_g02_ui_fit.gd

const SCENE_PATH := "res://viewer/main.tscn"
const REQUIREMENTS_SHA256 := "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
const TOL := 1.5

var _checks := 0
var _failures: Array = []
var _scene = null
var _shell = null

func _initialize() -> void:
	print("== test_g02_ui_fit (G02 responsive layout regression) ==")
	print("CONTRACT DEEPEYE-HUMAN-LOCK-20261014/revision1 requirements_sha256=%s" % REQUIREMENTS_SHA256)
	_run_tests.call_deferred()

func _run_tests() -> void:
	_scene = load(SCENE_PATH).instantiate()
	root.add_child(_scene)
	await process_frame
	await process_frame
	_shell = _scene.shell
	_check(_shell != null, "real viewer shell exists")
	_check(_scene.document != null, "real viewer document exists")
	_check(int(ProjectSettings.get_setting("display/window/size/window_width_override", 0)) != 1280,
		"project no longer forces the 1280-pixel window width")
	_check(int(ProjectSettings.get_setting("display/window/size/window_height_override", 0)) != 720,
		"project no longer forces the 720-pixel window height")
	_check(String(ProjectSettings.get_setting("display/window/stretch/mode", "")) == "canvas_items",
		"project keeps canvas_items stretch")
	var default_root = _shell.get("_root") if _shell != null else null
	_check(default_root != null and absf(default_root.size.y - 1080.0) <= TOL,
		"default logical height remains the 1080-pixel baseline")
	_check(default_root != null and int(default_root.theme.default_font_size) >= 15,
		"body font size remains at least 15 logical pixels")
	if _shell != null:
		var title_probe = _shell._title("UI_FIT_TITLE")
		_check(title_probe.get_theme_font_size("font_size") >= 16,
			"section title font size remains at least 16 logical pixels")
		title_probe.free()
	if _shell == null:
		await _finish()
		return

	await _test_layout(Vector2i(1920, 1080), true)
	await _test_layout(Vector2i(2560, 1440), true)
	await _test_layout(Vector2i(1280, 720), false)
	await _test_scroll_reachability()
	await _test_help_and_status()
	await _test_action_status_height()
	await _test_action_status_tooltip()
	await _test_file_dialog()
	await _test_open_dialog_geometry()
	await _test_authority_and_input()
	await _finish()

func _set_logical_size(size: Vector2i) -> void:
	root.size = size
	root.content_scale_size = size
	root.content_scale_factor = 1.0
	await process_frame
	await process_frame
	await process_frame

func _test_layout(size: Vector2i, require_sixty: bool) -> void:
	await _set_logical_size(size)
	var root_control = _shell.get("_root")
	var left_panel = _shell.get("_left_panel")
	var right_panel = _shell.get("_right_panel")
	var top_band = _shell.get("_top_band")
	var bottom_band = _shell.get("_bottom_band")
	var top_strip = _shell.get("_top_strip")
	var bottom_panel = _shell.get("_bottom_panel")
	var central = _shell.get("_central_viewport")
	var left_scroll = _shell.get("_left_scroll")
	var right_scroll = _shell.get("_right_scroll")
	var top_flow = _shell.get("_top_flow")
	_check(root_control != null, "shell root exists at %s" % size)
	_check(left_panel != null and right_panel != null, "side panels exist at %s" % size)
	_check(top_band != null and bottom_band != null, "full-width top/bottom bands exist at %s" % size)
	_check(top_strip != null and bottom_panel != null, "existing top/bottom content containers exist at %s" % size)
	_check(central != null, "real CentralViewport control exists at %s" % size)
	_check(left_scroll != null and right_scroll != null, "side scroll containers exist at %s" % size)
	_check(top_flow != null, "top flow container exists at %s" % size)
	if root_control == null or left_panel == null or right_panel == null or top_band == null \
			or bottom_band == null or top_strip == null or bottom_panel == null or central == null \
			or left_scroll == null or right_scroll == null or top_flow == null:
		return

	var root_rect: Rect2 = root_control.get_global_rect()
	var left: Rect2 = left_panel.get_global_rect()
	var right: Rect2 = right_panel.get_global_rect()
	var top: Rect2 = top_band.get_global_rect()
	var bottom: Rect2 = bottom_band.get_global_rect()
	var top_content: Rect2 = top_strip.get_global_rect()
	var bottom_content: Rect2 = bottom_panel.get_global_rect()
	var central_rect: Rect2 = central.get_global_rect()
	var central_area: float = maxf(0.0, central_rect.size.x) * maxf(0.0, central_rect.size.y)
	var ratio: float = central_area / maxf(1.0, root_rect.size.x * root_rect.size.y) * 100.0
	print("UI_FIT size=%s requested=%s root=%s left=%s central=%s right=%s top=%s bottom=%s ratio=%.6f%%" % [
		size, root.get_visible_rect().size, root_rect, left, central_rect, right, top, bottom, ratio])

	_check(absf(root_rect.size.x - float(size.x)) <= TOL and absf(root_rect.size.y - float(size.y)) <= TOL,
		"logical root measures the requested size at %s (got %s)" % [size, root_rect.size])
	_check(absf(left.position.x) <= TOL, "left toolbar starts at x=0 at %s" % size)
	_check(left.end.x <= central_rect.position.x + TOL, "central starts after the left toolbar at %s" % size)
	_check(central_rect.end.x <= right.position.x + TOL, "right panel starts after the central slot at %s" % size)
	_check(absf(right.end.x - root_rect.end.x) <= TOL, "right panel ends at the root width at %s" % size)
	_check(absf(top.position.x) <= TOL and absf(top.end.x - root_rect.end.x) <= TOL,
		"top band spans the full client width at %s" % size)
	_check(absf(bottom.position.x) <= TOL and absf(bottom.end.x - root_rect.end.x) <= TOL,
		"bottom band spans the full client width at %s" % size)
	_check(central_rect.position.y >= top.end.y - TOL and central_rect.end.y <= bottom.position.y + TOL,
		"central slot sits between the top and bottom bands at %s" % size)
	_check(_rect_contains(top, top_content) and _rect_contains(bottom, bottom_content),
		"top/bottom content stays inside its full-width band at %s" % size)
	_check(top_content.position.x >= left.end.x - TOL and top_content.end.x <= right.position.x + TOL,
		"top content avoids the side toolbars at %s" % size)
	_check(bottom_content.position.x >= left.end.x - TOL and bottom_content.end.x <= right.position.x + TOL,
		"bottom content avoids the side toolbars at %s" % size)
	_check(central.mouse_filter == Control.MOUSE_FILTER_IGNORE,
		"central 3D slot ignores mouse input at %s" % size)
	_check(left_panel.mouse_filter == Control.MOUSE_FILTER_STOP and right_panel.mouse_filter == Control.MOUSE_FILTER_STOP,
		"side panels consume mouse input at %s" % size)
	_check(left_scroll.mouse_filter == Control.MOUSE_FILTER_STOP or left_scroll.get_parent().mouse_filter == Control.MOUSE_FILTER_STOP,
		"left scroll region consumes mouse input at %s" % size)
	_check(right_scroll.mouse_filter == Control.MOUSE_FILTER_STOP or right_scroll.get_parent().mouse_filter == Control.MOUSE_FILTER_STOP,
		"right scroll region consumes mouse input at %s" % size)
	_check(left_scroll.horizontal_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED,
		"left side panel forbids horizontal scrolling at %s" % size)
	_check(right_scroll.horizontal_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED,
		"right side panel forbids horizontal scrolling at %s" % size)
	_check(left_scroll.vertical_scroll_mode == ScrollContainer.SCROLL_MODE_AUTO,
		"left side panel auto-scrolls vertically at %s" % size)
	_check(right_scroll.vertical_scroll_mode == ScrollContainer.SCROLL_MODE_AUTO,
		"right side panel auto-scrolls vertically at %s" % size)
	_check(left_scroll.get_child(0).get_combined_minimum_size().x <= left_scroll.size.x + TOL,
		"left content minimum width fits its viewport at %s" % size)
	_check(right_scroll.get_child(0).get_combined_minimum_size().x <= right_scroll.size.x + TOL,
		"right content minimum width fits its viewport at %s" % size)
	_check(_top_labels_inside(top_strip, top_flow), "top labels stay inside the top strip without overlap at %s" % size)
	if require_sixty:
		_check(ratio >= 60.0, "measured central area is at least 60%% at %s (got %.6f%%)" % [size, ratio])
	else:
		_check(central_rect.size.x > 0.0 and central_rect.size.y > 0.0,
			"smaller client keeps a positive central area at %s" % size)

func _top_labels_inside(top_strip: Control, top_flow: Control) -> bool:
	var container: Rect2 = top_strip.get_global_rect()
	var labels: Array = []
	for child in top_flow.get_children():
		if child is Label and child.visible:
			labels.append(child)
	for label in labels:
		if not _rect_contains(container, label.get_global_rect()):
			return false
	for i in range(labels.size()):
		for j in range(i + 1, labels.size()):
			var intersection: Rect2 = labels[i].get_global_rect().intersection(labels[j].get_global_rect())
			if intersection.size.x > TOL and intersection.size.y > TOL:
				return false
	return true

func _test_scroll_reachability() -> void:
	await _set_logical_size(Vector2i(1920, 1080))
	var left_scroll = _shell.get("_left_scroll")
	var right_scroll = _shell.get("_right_scroll")
	var gate_label = _shell.get("_gate_status_label")
	var pending_label = _shell.get("_pending_label")
	var overlap_label = _shell.get("_overlap_label")
	_check(left_scroll != null and right_scroll != null, "scroll containers exist for reachability probe")
	_check(gate_label != null and pending_label != null and overlap_label != null,
		"scroll content labels exist for reachability probe")
	if left_scroll == null or right_scroll == null or gate_label == null or pending_label == null or overlap_label == null:
		return
	var left_text := String(gate_label.text)
	var right_text := String(pending_label.text)
	var overlap_text := String(overlap_label.text)
	var hash_before: String = _scene.document.commitment_hash()
	var long_left := "UI_FIT_LEFT_LONG_STATUS_LINE\n".repeat(80)
	var long_right := "UI_FIT_RIGHT_LONG_PENDING_LINE\n".repeat(90)
	gate_label.text = long_left
	pending_label.text = long_right
	await process_frame
	await process_frame
	await process_frame
	var left_bar: VScrollBar = left_scroll.get_v_scroll_bar()
	var right_bar: VScrollBar = right_scroll.get_v_scroll_bar()
	_check(left_bar.max_value > left_bar.page, "left side content overflows vertically")
	_check(right_bar.max_value > right_bar.page, "right side content overflows vertically")
	_check(not left_scroll.get_h_scroll_bar().visible, "left side does not need a horizontal scrollbar")
	_check(not right_scroll.get_h_scroll_bar().visible, "right side does not need a horizontal scrollbar")
	left_scroll.scroll_vertical = int(left_bar.max_value)
	right_scroll.scroll_vertical = int(right_bar.max_value)
	await process_frame
	await process_frame
	var left_content: Control = left_scroll.get_child(0)
	var right_content: Control = right_scroll.get_child(0)
	_check(left_content.get_global_rect().end.y <= left_scroll.get_global_rect().end.y + 8.0,
		"left content bottom is reachable by vertical scrolling")
	_check(right_content.get_global_rect().end.y <= right_scroll.get_global_rect().end.y + 8.0,
		"right content bottom is reachable by vertical scrolling")
	_check(_scene.document.commitment_hash() == hash_before, "scroll probe does not change document geometry")
	# No explicit newlines: wrapping must constrain a long status token as well
	# as the multiline overflow exercised above.
	gate_label.text = "长状态UI_FIT_NO_BREAK_".repeat(60)
	pending_label.text = "长原因UI_FIT_NO_BREAK_".repeat(60)
	await process_frame
	await process_frame
	await process_frame
	for pair in [[gate_label, left_scroll], [pending_label, right_scroll]]:
		var label: Label = pair[0]
		var scroll: ScrollContainer = pair[1]
		_check(label.get_line_count() > 1, "long status wraps without explicit newlines")
		_check(label.size.x <= scroll.size.x + TOL and label.get_combined_minimum_size().x <= scroll.size.x + TOL,
			"wrapped long status fits the scroll viewport horizontally")
		_check(not scroll.get_h_scroll_bar().visible, "long wrapped status needs no horizontal scrollbar")
		print("UI_FIT_WRAP label=%s size=%s minimum=%s viewport=%s lines=%d" % [
			label.name, label.size, label.get_combined_minimum_size(), scroll.size, label.get_line_count()])
	gate_label.text = left_text
	pending_label.text = right_text
	overlap_label.text = overlap_text
	left_scroll.scroll_vertical = 0
	right_scroll.scroll_vertical = 0
	await process_frame
	await process_frame

func _test_help_and_status() -> void:
	var hint = _shell.get("_hint_label")
	var action = _shell.get("_action_status_label")
	_check(hint != null, "permanent camera/control help label exists")
	_check(action != null, "dedicated transient action-status label exists")
	if hint == null or action == null:
		return
	var baseline_hint := String(hint.text)
	var hash_before: String = _scene.document.commitment_hash()
	_check(baseline_hint.find("Esc") != -1 and baseline_hint.find("左键") != -1,
		"permanent help retains camera/control instructions")
	_shell._set_hint("UI_FIT_STATUS_SUCCESS")
	await process_frame
	_check(String(hint.text) == baseline_hint, "success status does not replace permanent help")
	_check(String(action.text).find("UI_FIT_STATUS_SUCCESS") != -1, "success status appears in action label")
	_shell._on_file_dialog_canceled()
	await process_frame
	_check(String(hint.text) == baseline_hint, "cancel status does not replace permanent help")
	_check(String(action.text).find("取消") != -1, "cancel status appears in action label")
	_shell._set_file_failure("ui_fit_probe", "UI_FIT_FAILURE")
	await process_frame
	_check(String(hint.text) == baseline_hint, "failure status does not replace permanent help")
	_check(String(action.text).find("失败") != -1 and String(action.text).find("UI_FIT_FAILURE") != -1,
		"failure status appears in action label")
	_check(_scene.document.commitment_hash() == hash_before, "help/status probe does not change document geometry")
	var bottom_panel = _shell.get("_bottom_panel")
	if bottom_panel != null:
		_check(_rect_contains(bottom_panel.get_global_rect(), action.get_global_rect()),
			"action status stays inside the bottom timeline panel")

func _test_action_status_height() -> void:
	# Removing the visible height bound must fail on the accepted maximum reason;
	# dropping the tooltip must fail full diagnostic access, even if geometry fits.
	var action: Label = _shell.get("_action_status_label")
	var hint: Label = _shell.get("_hint_label")
	var help_before := String(hint.text)
	var hash_before: String = _scene.document.commitment_hash()
	var reasons := ["文件不可读", "边".repeat(512), "多行原因\n".repeat(110).substr(0, 512)]
	for size in [Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(1280, 720)]:
		await _set_logical_size(size)
		_shell._set_hint("")
		for i in range(8):
			await process_frame
		var bottom_before: float = _shell._bottom_band.size.y
		for reason in reasons:
			_shell._set_file_failure("ui_fit_status_height", reason)
			for i in range(8):
				await process_frame
			var expected := "布局文件操作失败：" + String(reason)
			_check(String(action.text) == expected, "accepted diagnostic remains intact at %s" % size)
			_check(action.get_visible_line_count() == 1 and action.size.y >= float(action.get_line_height()),
				"bounded status still displays one readable font-height line at %s" % size)
			_check(String(action.get_tooltip()).replace("\n", "").c_unescape() == expected and action.mouse_filter != Control.MOUSE_FILTER_IGNORE,
				"full diagnostic is available to pointer tooltip at %s" % size)
			_check(String(_shell.last_file_result.reason) == String(reason), "accepted reason remains intact in file result at %s" % size)
			_check(absf(_shell._bottom_band.size.y - bottom_before) <= TOL,
				"normal/max/multiline status cannot grow bottom band at %s" % size)
			_check(_rect_contains(_shell._bottom_panel.get_global_rect(), action.get_global_rect()),
				"status remains contained in bottom panel at %s" % size)
			_check(String(hint.text) == help_before, "long diagnostic preserves permanent help at %s" % size)
			var central: Rect2 = _shell._central_viewport.get_global_rect()
			var ratio: float = central.get_area() / _shell._root.get_global_rect().get_area() * 100.0
			if size.y >= 1080:
				_check(ratio >= 60.0, "maximum accepted status preserves 60 percent central area at %s" % size)
			else:
				_check(central.size.x > 0.0 and central.size.y > 0.0, "maximum accepted status keeps positive 720p central area")
			print("UI_FIT_STATUS size=%s chars=%d lines=%d visible_lines=%d status=%s bottom=%.1f ratio=%.6f%%" % [
				size, expected.length(), action.get_line_count(), action.get_visible_line_count(), action.get_global_rect(), _shell._bottom_band.size.y, ratio])
		_shell._set_hint("")
		for i in range(8):
			await process_frame
		_check(String(action.text).is_empty() and String(action.get_tooltip()).is_empty(),
			"clearing status removes visible text and stale diagnostic tooltip at %s" % size)
		_check(absf(_shell._bottom_band.size.y - bottom_before) <= TOL, "cleared status restores stable bottom height at %s" % size)
	_check(_scene.document.commitment_hash() == hash_before, "status height probe leaves document geometry unchanged")
	_check(_shell._run_button.disabled and _shell._pause_button.disabled and _shell._continue_button.disabled,
		"status height probe preserves disconnected authority; no Run invoked")

func _test_action_status_tooltip() -> void:
	var action: Label = _shell._action_status_label
	for size in [Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(1280, 720)]:
		await _set_logical_size(size)
		_shell._set_file_failure("ui_fit_tooltip", "边".repeat(512))
		var motion := InputEventMouseMotion.new()
		motion.position = root.get_final_transform() * Vector2(1.0, 1.0)
		root.push_input(motion)
		await process_frame
		motion.position = root.get_final_transform() * action.get_global_rect().get_center()
		root.push_input(motion)
		await create_timer(0.8).timeout
		var popup = _find_visible_tooltip(root)
		_check(popup != null, "synthetic hover opens full diagnostic tooltip at %s" % size)
		if popup != null:
			var rect := Rect2(Vector2(popup.position), Vector2(popup.size))
			_check(_rect_contains(Rect2(Vector2.ZERO, Vector2(size)), rect),
				"full maximum diagnostic tooltip stays within client at %s" % size)
			print("UI_FIT_TOOLTIP size=%s rect=%s chars=%d" % [size, rect, action.get_tooltip().length()])
	_shell._set_hint("")
	var leave := InputEventMouseMotion.new()
	leave.position = root.get_final_transform() * Vector2(1.0, 1.0)
	root.push_input(leave)
	await process_frame

func _find_visible_tooltip(node: Node):
	if node is PopupPanel and node.visible:
		return node
	for child in node.get_children(true):
		var found = _find_visible_tooltip(child)
		if found != null:
			return found
	return null

func _test_file_dialog() -> void:
	await _set_logical_size(Vector2i(1920, 1080))
	var dialog = _shell.get("_file_dialog")
	_check(dialog != null, "explicit in-engine FileDialog exists")
	if dialog == null:
		return
	_check(dialog.use_native_dialog == false, "FileDialog remains deterministic in-engine")
	_check(_has_callable(_shell, "_prepare_file_dialog"), "dialog preparation helper exists")
	_check(_has_callable(_shell, "_dialog_target_size"), "measured dialog target helper exists")
	if not _has_callable(_shell, "_prepare_file_dialog") or not _has_callable(_shell, "_dialog_target_size"):
		return
	_shell._prepare_file_dialog("save")
	await process_frame
	_check(String(dialog.title).find("另存私有布局") != -1, "final Save title is Chinese after mode configuration (got %s)" % dialog.title)
	_check(dialog.file_mode == FileDialog.FILE_MODE_SAVE_FILE, "Save mode is FILE_MODE_SAVE_FILE")
	_check(String(dialog.current_file).ends_with(".json"), "Save current_file ends in .json")
	_check(dialog.min_size.x >= 960 and dialog.min_size.y >= 600, "Save dialog minimum size is at least 960x600")
	var save_target: Vector2i = _shell._dialog_target_size(Vector2(_shell._root.size))
	_check(save_target.x >= 960 and save_target.x <= 1440 and save_target.y >= 600 and save_target.y <= 900,
		"Save target is bounded to the measured 960..1440 x 600..900 range (got %s)" % save_target)
	_check(save_target.x <= int(_shell._root.size.x) and save_target.y <= int(_shell._root.size.y),
		"Save target fits inside the current client rectangle")
	if _has_callable(_shell, "_configure_file_dialog"):
		_shell._configure_file_dialog("save")
		await process_frame
		var save_rect := Rect2(Vector2(dialog.position), Vector2(dialog.size))
		_check(save_rect.size.x >= 960.0 and save_rect.size.y >= 600.0,
			"opened Save dialog keeps its minimum measured size (got %s)" % save_rect.size)
		_check(save_rect.position.x >= -TOL and save_rect.position.y >= -TOL
			and save_rect.end.x <= float(root.size.x) + TOL and save_rect.end.y <= float(root.size.y) + TOL,
			"opened Save dialog stays inside the client work area (got %s)" % save_rect)
		dialog.hide()
	_shell._prepare_file_dialog("open")
	await process_frame
	_check(String(dialog.title).find("打开私有布局") != -1, "final Open title is Chinese after mode configuration (got %s)" % dialog.title)
	_check(dialog.file_mode == FileDialog.FILE_MODE_OPEN_FILE, "Open mode is FILE_MODE_OPEN_FILE")
	_check(String(dialog.current_file) == "", "Open mode clears the stale filename")
	var open_target: Vector2i = _shell._dialog_target_size(Vector2(_shell._root.size))
	_check(open_target.x >= 960 and open_target.x <= 1440 and open_target.y >= 600 and open_target.y <= 900,
		"Open target is bounded to the measured 960..1440 x 600..900 range (got %s)" % open_target)
	_check(String(dialog.title).find("Save a File") == -1 and String(dialog.title).find("Open a File") == -1,
		"dialog never exposes the generic English title")

func _test_open_dialog_geometry() -> void:
	var dialog = _shell.get("_file_dialog")
	if dialog == null or not _has_callable(_shell, "_configure_file_dialog"):
		return
	for logical_size in [Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(1280, 720)]:
		await _set_logical_size(logical_size)
		for action in ["save", "open"]:
			_check(_shell._configure_file_dialog(action), "dialog opens for %s at %s" % [action, logical_size])
			await process_frame
			await process_frame
			var rect := Rect2(Vector2(dialog.position), Vector2(dialog.size))
			var local_bounds := Rect2(Vector2.ZERO, Vector2(dialog.size))
			var ok: Button = dialog.get_ok_button()
			var cancel: Button = dialog.get_cancel_button()
			_check(_rect_contains(Rect2(Vector2.ZERO, Vector2(root.size)), rect),
				"opened %s dialog stays inside %s" % [action, logical_size])
			_check(_rect_contains(local_bounds, ok.get_global_rect()) and _rect_contains(local_bounds, cancel.get_global_rect()),
				"opened %s dialog action buttons fit at %s" % [action, logical_size])
			_check(ok.visible and cancel.visible and ok.size.x > 0.0 and cancel.size.x > 0.0,
				"opened %s dialog action buttons remain visible at %s" % [action, logical_size])
			var expected_title: String = "另存私有布局" if action == "save" else "打开私有布局"
			_check(String(dialog.title).contains(expected_title),
				"opened %s dialog retains its final Chinese title at %s" % [action, logical_size])
			print("UI_FIT_DIALOG size=%s action=%s rect=%s ok=%s cancel=%s title=%s" % [
				logical_size, action, rect, ok.get_global_rect(), cancel.get_global_rect(), dialog.title])
			dialog.hide()
			await process_frame

func _test_authority_and_input() -> void:
	await _set_logical_size(Vector2i(1920, 1080))
	var run_button = _shell.get("_run_button")
	var pause_button = _shell.get("_pause_button")
	var continue_button = _shell.get("_continue_button")
	var central = _shell.get("_central_viewport")
	var left_scroll = _shell.get("_left_scroll")
	_check(run_button != null and pause_button != null and continue_button != null, "run/pause/continue controls exist")
	if run_button == null or pause_button == null or continue_button == null or central == null or left_scroll == null:
		return
	_check(run_button.disabled and pause_button.disabled and continue_button.disabled,
		"Run/pause/continue remain disabled without a real authority bridge")
	_check(String(run_button.tooltip_text).find("未连接控制权威") != -1,
		"disabled Run retains the disconnected-authority tooltip")
	_check(_scene.document.control_bridge_connected == false and not _scene.document.is_motion_active(),
		"authority remains disconnected and motion inactive")

	var to_window: Transform2D = root.get_final_transform()
	var central_point: Vector2 = to_window * central.get_global_rect().get_center()
	var panel_point: Vector2 = to_window * left_scroll.get_global_rect().get_center()
	var distance_before: float = float(_scene._distance)
	var warmup := InputEventMouseMotion.new()
	warmup.position = central_point
	root.push_input(warmup)
	await process_frame
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	wheel.position = panel_point
	root.push_input(wheel)
	await process_frame
	_check(is_equal_approx(float(_scene._distance), distance_before),
		"wheel over the left panel does not move the camera")
	var orbit_press := InputEventMouseButton.new()
	orbit_press.button_index = MOUSE_BUTTON_RIGHT
	orbit_press.pressed = true
	orbit_press.position = panel_point
	root.push_input(orbit_press)
	await process_frame
	_check(not bool(_scene._orbiting), "right press over the left panel does not start camera orbit")
	var orbit_release := InputEventMouseButton.new()
	orbit_release.button_index = MOUSE_BUTTON_RIGHT
	orbit_release.pressed = false
	orbit_release.position = panel_point
	root.push_input(orbit_release)
	await process_frame
	var right_scroll = _shell.get("_right_scroll")
	if right_scroll != null:
		var right_point: Vector2 = to_window * right_scroll.get_global_rect().get_center()
		wheel.position = right_point
		root.push_input(wheel)
		await process_frame
		_check(is_equal_approx(float(_scene._distance), distance_before),
			"wheel over the right panel does not move the camera")
		orbit_press.position = right_point
		root.push_input(orbit_press)
		await process_frame
		_check(not bool(_scene._orbiting), "right press over the right panel does not start camera orbit")
		orbit_release.position = right_point
		root.push_input(orbit_release)
		await process_frame
	var central_motion := InputEventMouseMotion.new()
	central_motion.position = central_point
	root.push_input(central_motion)
	await process_frame
	wheel.position = central_point
	root.push_input(wheel)
	await process_frame
	_check(not is_equal_approx(float(_scene._distance), distance_before),
		"wheel over the central slot still reaches the free camera")

func _has_callable(object, method_name: String) -> bool:
	return object != null and object.has_method(method_name)

func _rect_contains(outer: Rect2, inner: Rect2) -> bool:
	return inner.position.x >= outer.position.x - TOL and inner.position.y >= outer.position.y - TOL \
		and inner.end.x <= outer.end.x + TOL and inner.end.y <= outer.end.y + TOL

func _check(condition: bool, what: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(what)
		print("UI_FIT_CHECK_FAIL " + what)

func _finish() -> void:
	if _scene != null:
		_scene.queue_free()
		_scene = null
		await process_frame
		await process_frame
	print("UI_FIT checks=%d failures=%d" % [_checks, _failures.size()])
	if _failures.is_empty():
		print("UI_FIT_RESULT PASS")
		quit(0)
	else:
		for failure in _failures:
			print("UI_FIT_FAILURE: " + failure)
		print("UI_FIT_RESULT FAIL")
		quit(1)

extends SceneTree
var checks := 0
var failures: Array = []
func _initialize():
	run.call_deferred()
func check(ok: bool, why: String):
	checks += 1
	if not ok:
		failures.append(why)
		print("EXTRA_FAIL ", why)
func settle():
	for i in range(8):
		await process_frame
func popup_in(node: Node):
	if node is PopupPanel and node.visible:
		return node
	for child in node.get_children(true):
		var found = popup_in(child)
		if found != null:
			return found
	return null
func motion_at(point: Vector2, relative := Vector2.ZERO):
	var event := InputEventMouseMotion.new()
	event.position = root.get_final_transform() * point
	event.relative = relative
	root.push_input(event)
	await process_frame
func run():
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	root.content_scale_factor = 1.0
	await settle()
	var shell = scene.shell
	var action: Label = shell._action_status_label
	var saved_hash: String = scene.document.commitment_hash()
	var saved_help: String = shell._hint_label.text
	var before_bottom: float = shell._bottom_band.size.y
	# The focused suite tests multiline reasons and CJK popup geometry, but does
	# not combine literal backslash-n, actual line breaks and tabs at the bound.
	var reason := "文\\n\n\t\\末".repeat(100).substr(0,512)
	check(reason.length()==512, "mixed escape boundary reaches accepted maximum")
	shell._set_file_failure("independent_mixed_boundary",reason)
	await settle()
	var expected := "布局文件操作失败：" + reason
	check(action.text==expected and String(shell.last_file_result.reason)==reason, "mixed diagnostic retains complete accepted raw strings")
	check(action.get_tooltip().replace("\n", "").c_unescape()==expected, "literal slash-n, actual newline and tab remain distinct in tooltip roundtrip")
	check(action.get_theme_font_size("font_size")==15, "status retains the 15px body font")
	check(action.size.y==24.0 and action.get_visible_line_count()==1, "status retains a visible 24px single line")
	check(shell._bottom_band.size.y==before_bottom, "mixed diagnostic cannot expand bottom band")
	await motion_at(Vector2.ONE)
	await motion_at(action.get_global_rect().get_center())
	await create_timer(0.8).timeout
	var popup = popup_in(root)
	check(popup!=null, "mixed diagnostic opens real engine tooltip")
	if popup!=null:
		var rect := Rect2(Vector2(popup.position),Vector2(popup.size))
		check(Rect2(Vector2.ZERO,Vector2(root.size)).grow(1.5).encloses(rect), "mixed max tooltip remains contained in 720p client")
		print("EXTRA_POPUP ", rect)
	await motion_at(Vector2.ONE)
	await settle()
	var distance: float = scene._distance
	var yaw: float = scene._yaw_deg
	var pitch: float = scene._pitch_deg
	var focus: Vector3 = scene._focus_point
	var point := action.get_global_rect().get_center()
	await motion_at(point)
	check(root.gui_get_hovered_control()==action, "synthetic pointer actually targets ActionStatus")
	for button in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN,MOUSE_BUTTON_RIGHT,MOUSE_BUTTON_MIDDLE,MOUSE_BUTTON_LEFT]:
		var press := InputEventMouseButton.new()
		press.button_index = button
		press.pressed = true
		press.position = root.get_final_transform() * point
		root.push_input(press)
		await process_frame
		await motion_at(point,Vector2(25,17))
		check(not scene._orbiting and not scene._panning and not scene._dragging, "status press does not start scene gesture: %s" % button)
		press.pressed = false
		root.push_input(press)
		await process_frame
		check(scene._distance==distance and scene._yaw_deg==yaw and scene._pitch_deg==pitch and scene._focus_point==focus, "status gesture leaves camera unchanged: %s" % button)
	check(scene.document.commitment_hash()==saved_hash, "status mouse input leaves document geometry unchanged")
	check(shell._hint_label.text==saved_help, "mixed reason and mouse input preserve permanent help")
	shell._set_hint("")
	await settle()
	check(action.text.is_empty() and action.get_tooltip().is_empty(), "clearing mixed status removes stale tooltip")
	check(shell._run_button.disabled and shell._pause_button.disabled and shell._continue_button.disabled, "authority remains disabled; no Run invoked")
	print("EXTRA_RESULT checks=%d failures=%d" % [checks,failures.size()])
	scene.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)

extends SceneTree
var scene
var shell
var failures: Array = []
var checks := 0
func _initialize():
	run.call_deferred()
func check(ok: bool, message: String):
	checks += 1
	if not ok:
		failures.append(message)
		print("BOUNDARY_FAIL ", message)
func settle():
	for i in range(8):
		await process_frame
func resize_client(value: Vector2i):
	root.size = value
	root.content_scale_size = value
	root.content_scale_factor = 1.0
	await settle()
func contains(outer: Rect2, inner: Rect2) -> bool:
	return outer.grow(1.5).encloses(inner)
func geometry(label: String):
	var central: Rect2 = shell._central_viewport.get_global_rect()
	var ratio: float = central.size.x * central.size.y / (shell._root.size.x * shell._root.size.y) * 100.0
	print("BOUNDARY_GEOMETRY label=%s root=%s central=%s ratio=%.6f bottom=%s" % [label, shell._root.size, central, ratio, shell._bottom_band.get_global_rect()])
	return ratio
func run():
	scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await settle()
	shell = scene.shell
	print("BOUNDARY_ORIGIN main=%s shell=%s doc=%s root=%s" % [scene.get_script().resource_path, shell.get_script().resource_path, scene.document.get_script().resource_path, ProjectSettings.globalize_path("res://")])
	await resize_client(Vector2i(1920,1080))
	check(geometry("initial1080") >= 60.0, "initial 1080 central area >=60 percent")
	var before: String = scene.document.commitment_hash()
	var transform := root.get_final_transform()
	var distance: float = scene._distance
	for point in [Vector2(10,10),Vector2(1910,10),Vector2(10,1070),Vector2(1910,1070)]:
		var wheel := InputEventMouseButton.new()
		wheel.button_index = MOUSE_BUTTON_WHEEL_UP
		wheel.pressed = true
		wheel.position = transform * point
		root.push_input(wheel)
		await process_frame
		check(is_equal_approx(scene._distance,distance),"wheel over band gutter leaves camera unchanged at %s" % point)
		var press := InputEventMouseButton.new()
		press.button_index = MOUSE_BUTTON_RIGHT
		press.pressed = true
		press.position = transform * point
		root.push_input(press)
		await process_frame
		check(not scene._orbiting,"right press over band gutter leaves orbit off at %s" % point)
		press.pressed = false
		root.push_input(press)
		await process_frame
	check(scene.document.commitment_hash()==before,"band input leaves scene geometry unchanged")
	# FileDialog is a subwindow; exercise an already-open dialog across a client resize.
	await resize_client(Vector2i(2560,1440))
	shell._configure_file_dialog("open")
	await settle()
	var dialog: FileDialog = shell._file_dialog
	var initial := Rect2(Vector2(dialog.position),Vector2(dialog.size))
	print("BOUNDARY_DIALOG before_resize root=%s dialog=%s" % [root.size,initial])
	check(contains(Rect2(Vector2.ZERO,Vector2(root.size)),initial),"dialog initially contained at 1440")
	await resize_client(Vector2i(1280,720))
	var shrunk := Rect2(Vector2(dialog.position),Vector2(dialog.size))
	print("BOUNDARY_DIALOG after_resize root=%s dialog=%s" % [root.size,shrunk])
	check(contains(Rect2(Vector2.ZERO,Vector2(root.size)),shrunk),"already-open dialog remains contained after client shrinks")
	dialog.hide()
	await resize_client(Vector2i(1920,1080))
	# Exercise the documented 512-character failure-reason bound without changing product files.
	shell._set_file_failure("review_boundary","边".repeat(512))
	await settle()
	var status: Label = shell._action_status_label
	print("BOUNDARY_STATUS chars=%s lines=%s rect=%s" % [status.text.length(),status.get_line_count(),status.get_global_rect()])
	check(geometry("bounded512_reason1080") >= 60.0,"512-character failure reason retains 60 percent central area")
	check(shell._hint_label.text.contains("右键环绕"),"permanent camera help survives error status")
	check(shell._run_button.disabled and shell._pause_button.disabled and shell._continue_button.disabled,"control buttons remain disabled; no Run invoked")
	print("BOUNDARY_RESULT checks=%d failures=%d" % [checks,failures.size()])
	scene.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)

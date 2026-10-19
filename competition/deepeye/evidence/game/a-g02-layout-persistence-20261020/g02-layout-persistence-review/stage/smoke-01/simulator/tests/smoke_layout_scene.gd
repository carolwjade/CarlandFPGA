extends SceneTree
func _initialize() -> void:
	_smoke.call_deferred()
func _smoke() -> void:
	var packed = load("res://viewer/main.tscn")
	if packed == null:
		print("SCENE_SMOKE_FAIL missing main.tscn")
		quit(1)
		return
	var scene = packed.instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	if scene.document == null or scene.shell == null or scene.shell._file_dialog == null:
		print("SCENE_SMOKE_FAIL missing document/shell/file dialog")
		quit(1)
		return
	print("SCENE_SMOKE_PASS document=1 shell=1 file_dialog=1")
	scene.queue_free()
	await process_frame
	quit(0)

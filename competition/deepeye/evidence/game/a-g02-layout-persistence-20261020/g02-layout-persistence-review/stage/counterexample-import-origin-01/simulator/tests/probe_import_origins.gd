extends SceneTree

func _initialize() -> void:
	_origin.call_deferred()

func _source(path: String) -> void:
	var script = load(path)
	if script == null:
		print("ORIGIN_FAIL path=%s" % path)
		return
	print("ORIGIN path=%s resource_path=%s global=%s" % [path, script.resource_path, ProjectSettings.globalize_path(script.resource_path)])

func _origin() -> void:
	print("PROJECT_LOCAL=%s" % ProjectSettings.globalize_path("res://"))
	print("ENGINE_EXE=%s" % OS.get_executable_path())
	_source("res://editor/layout_codec.gd")
	_source("res://editor/layout_store.gd")
	_source("res://editor/scene_document.gd")
	_source("res://ui/shell.gd")
	_source("res://viewer/main.gd")
	print("ORIGIN_SCENE=%s" % ProjectSettings.globalize_path("res://viewer/main.tscn"))
	quit(0)

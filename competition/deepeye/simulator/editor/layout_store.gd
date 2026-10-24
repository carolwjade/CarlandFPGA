class_name LayoutStore
extends RefCounted
## Bounded local file boundary for private layout JSON.
##
## Stored values stay in explicit absolute filesystem paths selected by the user.
## The default is viewer-private user data. This class performs no directory
## scanning, automatic loading, network access, resource loading or execution.

const MAX_FILE_BYTES := 1048576


func default_layout_dir() -> String:
	return OS.get_user_data_dir().path_join("layouts")

func read_text(path: String) -> Dictionary:
	var path_result := _absolute_path(path)
	if not bool(path_result.get("ok", false)):
		return path_result
	var normalized_path := String(path_result.path)
	if DirAccess.dir_exists_absolute(normalized_path):
		return _fail("is_directory", "所选路径是目录，不是布局文件")
	if not FileAccess.file_exists(normalized_path):
		return _fail("not_found", "布局文件不存在或不可访问")
	var file := FileAccess.open(normalized_path, FileAccess.READ)
	if file == null:
		return _fail("io_error", "无法打开布局文件: " + error_string(FileAccess.get_open_error()))
	var declared_length := file.get_length()
	if declared_length > MAX_FILE_BYTES:
		file.close()
		return _fail("too_large", "布局文件超过 1 MiB 上限")
	var raw := file.get_buffer(declared_length)
	var length_after_read := file.get_length()
	var read_error := file.get_error()
	file.close()
	if read_error != OK:
		return _fail("io_error", "读取布局文件失败: " + error_string(read_error))
	if length_after_read > MAX_FILE_BYTES or raw.size() > MAX_FILE_BYTES:
		return _fail("too_large", "布局文件超过 1 MiB 上限")
	if raw.size() != declared_length:
		return _fail("io_error", "布局文件在读取期间被截断")
	var text := raw.get_string_from_utf8()
	if text.to_utf8_buffer() != raw:
		return _fail("invalid_utf8", "布局文件不是有效 UTF-8")
	return {"ok": true, "text": text, "bytes": raw.size(), "path": normalized_path}

const BridgeScript = preload("res://editor/layout_commit_bridge.gd")
var _bridge = null

func _new_bridge():
	return BridgeScript.new()

func _save_begin(path: String, text: String) -> Dictionary:
	if path.replace("\\", "/").split("/").has("..") or path.replace("\\", "/").split("/").has("."):
		return _fail("invalid_path", "布局文件必须使用受支持的本地绝对路径")
	var path_result := _absolute_path(path)
	if not bool(path_result.get("ok", false)):
		return path_result
	if text.to_utf8_buffer().size() > MAX_FILE_BYTES:
		return _fail("too_large", "布局文件超过 1 MiB 上限")
	if _bridge == null:
		_bridge = _new_bridge()
	return _bridge.begin(String(path_result.path), text)

func save_new(path: String, text: String) -> Dictionary:
	var started := _save_begin(path, text)
	if not bool(started.get("ok", false)):
		return started
	return _bridge.wait_sync()

func save_new_async(path: String, text: String) -> Dictionary:
	var started := _save_begin(path, text)
	if not bool(started.get("ok", false)):
		return started
	var tree = Engine.get_main_loop()
	if not (tree is SceneTree):
		# A worker has started: absence of a SceneTree cannot imply cancellation.
		return _bridge.wait_sync()
	return await _bridge.wait_async(tree)

func has_unresolved_save() -> bool:
	if _bridge == null:
		return false
	_bridge.poll()
	return _bridge.has_unresolved()

func take_late_save_results() -> Array:
	return [] if _bridge == null else _bridge.take_late_results()

func save_evidence() -> Dictionary:
	return {} if _bridge == null else _bridge.evidence()

func _absolute_path(path: String) -> Dictionary:
	if path.is_empty() or path.to_utf8_buffer().has(0) or not path.is_absolute_path():
		return _fail("invalid_path", "布局文件必须位于显式绝对本地路径")
	var normalized := path.simplify_path()
	if not normalized.is_absolute_path():
		return _fail("invalid_path", "布局文件必须位于显式绝对本地路径")
	return {"ok": true, "path": normalized}

func _fail(code: String, reason: String) -> Dictionary:
	return {"ok": false, "code": code, "reason": reason, "errors": [reason]}

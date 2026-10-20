class_name LayoutStore
extends RefCounted
## Bounded local file boundary for private layout JSON.
##
## Stored values stay in explicit absolute filesystem paths selected by the user.
## The default is viewer-private user data. This class performs no directory
## scanning, automatic loading, network access, resource loading or execution.

const MAX_FILE_BYTES := 1048576
const MAX_TEMP_ATTEMPTS := 16

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

func save_new(path: String, text: String) -> Dictionary:
	var path_result := _absolute_path(path)
	if not bool(path_result.get("ok", false)):
		return path_result
	var normalized_path := String(path_result.path)
	if text.to_utf8_buffer().size() > MAX_FILE_BYTES:
		return _fail("too_large", "布局文件超过 1 MiB 上限")
	if FileAccess.file_exists(normalized_path) or DirAccess.dir_exists_absolute(normalized_path):
		return _fail("already_exists", "目标文件已存在；本版本仅支持另存为新文件")
	var parent := normalized_path.get_base_dir()
	if parent.is_empty() or not parent.is_absolute_path():
		return _fail("invalid_path", "布局文件必须位于显式绝对本地路径")
	if not DirAccess.dir_exists_absolute(parent):
		var make_error := DirAccess.make_dir_recursive_absolute(parent)
		if make_error != OK:
			return _fail("io_error", "无法创建布局目录: " + error_string(make_error))
	var temp_result := _unused_temp_path(normalized_path)
	if not bool(temp_result.get("ok", false)):
		return temp_result
	var temp_path := String(temp_result.path)
	if FileAccess.file_exists(temp_path) or DirAccess.dir_exists_absolute(temp_path):
		return _fail("temp_unavailable", "无法取得未占用的临时布局文件路径")
	var file := FileAccess.open(temp_path, FileAccess.WRITE)
	if file == null:
		return _fail("io_error", "无法写入临时布局文件: " + error_string(FileAccess.get_open_error()))
	var stored := file.store_string(text)
	if stored:
		file.flush()
	var write_error := file.get_error()
	file.close()
	if not stored or write_error != OK:
		_remove_temp(temp_path)
		return _fail("io_error", "写入临时布局文件失败: " + error_string(write_error))
	var verify := read_text(temp_path)
	if not bool(verify.get("ok", false)) or String(verify.get("text", "")) != text:
		_remove_temp(temp_path)
		var detail := String(verify.get("reason", "临时文件内容不一致"))
		return _fail("verify_failed", "临时布局文件重读校验失败: " + detail)
	if FileAccess.file_exists(normalized_path) or DirAccess.dir_exists_absolute(normalized_path):
		_remove_temp(temp_path)
		return _fail("already_exists", "目标文件已存在；本版本仅支持另存为新文件")
	var rename_error := DirAccess.rename_absolute(temp_path, normalized_path)
	if rename_error != OK:
		_remove_temp(temp_path)
		return _fail("publish_failed", "发布布局文件失败: " + error_string(rename_error))
	return {
		"ok": true,
		"path": normalized_path,
		"bytes": text.to_utf8_buffer().size(),
	}

func _unused_temp_path(target_path: String, stamp_usec: int = -1) -> Dictionary:
	var stamp := Time.get_ticks_usec() if stamp_usec < 0 else stamp_usec
	var base := "%s.deepeye-tmp-%d-%d" % [target_path, OS.get_process_id(), stamp]
	for attempt in range(0, MAX_TEMP_ATTEMPTS + 1):
		var candidate := base if attempt == 0 else base + "-" + str(attempt)
		if not FileAccess.file_exists(candidate) and not DirAccess.dir_exists_absolute(candidate):
			return {"ok": true, "path": candidate}
	return _fail("temp_unavailable", "无法取得未占用的临时布局文件路径")

func _remove_temp(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)

func _absolute_path(path: String) -> Dictionary:
	if path.is_empty() or path.to_utf8_buffer().has(0) or not path.is_absolute_path():
		return _fail("invalid_path", "布局文件必须位于显式绝对本地路径")
	var normalized := path.simplify_path()
	if not normalized.is_absolute_path():
		return _fail("invalid_path", "布局文件必须位于显式绝对本地路径")
	return {"ok": true, "path": normalized}

func _fail(code: String, reason: String) -> Dictionary:
	return {"ok": false, "code": code, "reason": reason, "errors": [reason]}

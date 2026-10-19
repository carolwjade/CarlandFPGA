extends SceneTree

func _initialize() -> void:
	_probe.call_deferred()

func _write(path: String, text: String) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	var ok := f.store_string(text)
	f.close()
	return ok

func _read_hex(path: String) -> String:
	if not FileAccess.file_exists(path):
		return "ABSENT"
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return "UNREADABLE"
	var raw := f.get_buffer(f.get_length())
	f.close()
	return raw.hex_encode()

func _probe() -> void:
	var dir := OS.get_user_data_dir().path_join("rename-existing-%d" % Time.get_ticks_usec())
	var mk := DirAccess.make_dir_recursive_absolute(dir)
	print("PROBE_DIR_ERR=%d" % mk)
	var target := dir.path_join("target.txt")
	var temp := dir.path_join("temp.txt")
	print("WRITE_TARGET=%s" % str(_write(target, "OLD\\n")))
	print("WRITE_TEMP=%s" % str(_write(temp, "NEW\\n")))
	var err := DirAccess.rename_absolute(temp, target)
	print("RENAME_EXISTING_ERR=%d" % err)
	print("RENAME_EXISTING_NAME=%s" % error_string(err))
	print("TARGET_AFTER_HEX=%s" % _read_hex(target))
	print("TEMP_AFTER_EXISTS=%s" % str(FileAccess.file_exists(temp)))

	var target_dir := dir.path_join("existing-dir")
	print("MAKE_DIR=%d" % DirAccess.make_dir_recursive_absolute(target_dir))
	var temp2 := dir.path_join("temp2.txt")
	print("WRITE_TEMP2=%s" % str(_write(temp2, "NEW2\\n")))
	var err2 := DirAccess.rename_absolute(temp2, target_dir)
	print("RENAME_DIR_EXISTING_ERR=%d" % err2)
	print("RENAME_DIR_EXISTING_NAME=%s" % error_string(err2))
	print("TARGET_DIR_STILL=%s" % str(DirAccess.dir_exists_absolute(target_dir)))
	print("TEMP2_AFTER_EXISTS=%s" % str(FileAccess.file_exists(temp2)))

	var target_new := dir.path_join("new-target.txt")
	var temp3 := dir.path_join("temp3.txt")
	print("WRITE_TEMP3=%s" % str(_write(temp3, "NEW3\\n")))
	var err3 := DirAccess.rename_absolute(temp3, target_new)
	print("RENAME_NEW_ERR=%d" % err3)
	print("RENAME_NEW_NAME=%s" % error_string(err3))
	print("NEW_TARGET_HEX=%s" % _read_hex(target_new))
	print("TEMP3_AFTER_EXISTS=%s" % str(FileAccess.file_exists(temp3)))
	quit(0)

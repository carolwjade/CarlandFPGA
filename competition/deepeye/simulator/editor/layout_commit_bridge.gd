extends RefCounted
## Viewer-private one-job owner. Only its worker touches child pipes.
## Unknown is retained evidence; neither timeout nor exit124 permits replay.

const PROTOCOL := "deepeye-layout-commit/1"
const MAX_PAYLOAD := 1048576
const MAX_METADATA := 4096
const MAX_RESPONSE := 16384
const MAX_STDERR := 4096
const UI_WAIT_MSEC := 5000
const GODOT_SHA256 := "ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424"
# Replaced only when the reviewed source-tree bundle is assembled.
const BUNDLE_SHA256 := "9e9c766ec7ad0268810c0b22ad26144fd481ef6984a6295e68608ec30c04f9de"
const RUNTIME_SHA256 := "2572eb57f5771bdb1ea4343e48591ca61650ef5dd828193d08c05d259a17d784"
const BOOTSTRAP := "exec(bytes.fromhex('696d706f7274206f732c20746872656164696e670a5f6c61796f75745f7761746368646f67203d20746872656164696e672e54696d657228362e302c206c616d6264613a206f732e5f657869742831323429290a5f6c61796f75745f7761746368646f672e6461656d6f6e203d20547275650a5f6c61796f75745f7761746368646f672e737461727428290a696d706f727420686173686c69622c206a736f6e2c2072652c207379730a646566205f756e69717565287061697273293a0a20202020726573756c74203d207b7d0a20202020666f72206b65792c2076616c756520696e2070616972733a0a20202020202020206966206b657920696e20726573756c743a0a20202020202020202020202072616973652056616c75654572726f7228226475706c696361746522290a2020202020202020726573756c745b6b65795d203d2076616c75650a2020202072657475726e20726573756c740a7472793a0a202020206966206c656e287379732e617267762920213d2035206f72207379732e617267765b315d20213d20222d2d62756e646c6522206f72207379732e617267765b335d20213d20222d2d62756e646c652d736861323536223a0a202020202020202072616973652056616c75654572726f722822617267756d656e747322290a2020202062756e646c655f706174682c2062756e646c655f736861203d207379732e617267765b325d2c207379732e617267765b345d0a202020206966206e6f74206f732e706174682e69736162732862756e646c655f7061746829206f72206e6f742072652e66756c6c6d6174636828225b302d39612d665d7b36347d222c2062756e646c655f736861293a0a202020202020202072616973652056616c75654572726f72282262696e64696e6722290a2020202077697468206f70656e2862756e646c655f706174682c2022726222292061732073747265616d3a0a2020202020202020726177203d2073747265616d2e726561642838313933290a202020206966206c656e2872617729203e2038313932206f7220686173686c69622e73686132353628726177292e686578646967657374282920213d2062756e646c655f7368613a0a202020202020202072616973652056616c75654572726f72282262756e646c655f70696e22290a2020202062756e646c65203d206a736f6e2e6c6f616473287261772e6465636f646528227574662d3822292c206f626a6563745f70616972735f686f6f6b3d5f756e69717565290a20202020696620747970652862756e646c6529206973206e6f742064696374206f72207365742862756e646c652920213d207b22736368656d61222c202268656c706572222c20226c656166227d206f7220747970652862756e646c655b22736368656d61225d29206973206e6f7420696e74206f722062756e646c655b22736368656d61225d20213d20313a0a202020202020202072616973652056616c75654572726f72282262756e646c655f736368656d6122290a20202020666f72206e616d652c2066696c656e616d6520696e2028282268656c706572222c20226c61796f75745f636f6d6d69745f636c692e707922292c2028226c656166222c20226c61796f75745f636f6d6d69745f77696e646f77732e70792229293a0a2020202020202020656e747279203d2062756e646c655b6e616d655d0a20202020202020206966207479706528656e74727929206973206e6f742064696374206f722073657428656e7472792920213d207b2270617468222c2022736861323536227d206f7220656e7472795b2270617468225d20213d2066696c656e616d65206f72207479706528656e7472795b22736861323536225d29206973206e6f7420737472206f72206e6f742072652e66756c6c6d6174636828225b302d39612d665d7b36347d222c20656e7472795b22736861323536225d293a0a20202020202020202020202072616973652056616c75654572726f72282262756e646c655f656e74727922290a2020202068656c7065725f70617468203d206f732e706174682e6a6f696e286f732e706174682e6469726e616d652862756e646c655f70617468292c2062756e646c655b2268656c706572225d5b2270617468225d290a2020202077697468206f70656e2868656c7065725f706174682c2022726222292061732073747265616d3a0a202020202020202068656c7065725f726177203d2073747265616d2e7265616428313331303733290a202020206966206c656e2868656c7065725f72617729203e20313331303732206f7220686173686c69622e7368613235362868656c7065725f726177292e686578646967657374282920213d2062756e646c655b2268656c706572225d5b22736861323536225d3a0a202020202020202072616973652056616c75654572726f72282268656c7065725f70696e22290a6578636570742042617365457863657074696f6e3a0a202020207379732e7374646572722e777269746528227072655f6c6561665f72656a65637465643a626f6f7473747261705f62696e64696e673b206c6561665f63616c6c65643d66616c73655c6e22290a202020207379732e657869742832290a6578656328636f6d70696c652868656c7065725f7261772c2068656c7065725f706174682c20226578656322292c207b225f5f6e616d655f5f223a20225f5f6d61696e5f5f222c20225f5f66696c655f5f223a2068656c7065725f706174682c20225f6c61796f75745f7761746368646f67223a205f6c61796f75745f7761746368646f677d290a'))"

var _thread: Thread
var _mutex := Mutex.new()
var _shared: Dictionary = {}
var _job: Dictionary = {}
var _late: Array = []
static var _unknown_paths: Dictionary = {}
var launch_count := 0
static var _active_owner = null
static var _engine_verified := false
static var _engine_mutex := Mutex.new()

func _fail(code: String, reason: String) -> Dictionary:
	return {"ok": false, "code": code, "reason": reason, "errors": [reason]}

func _unknown() -> Dictionary:
	var result := _fail("outcome_unknown", "保存结果未知，文件可能已写入；请检查目标文件，勿自动重试")
	result.merge({"operation_id": _job.get("operation_id", ""), "path": _job.get("path", ""), "bytes": _job.get("bytes", 0)})
	return result

func _bundle_spec() -> Dictionary:
	return {"path": "res://native/layout_commit_bundle.json", "sha256": BUNDLE_SHA256}

func _runtime_preflight() -> Dictionary:
	if OS.get_name() != "Windows" or OS.has_feature("standalone"):
		return _fail("helper_unavailable", "此安装尚未配置安全布局保存，请使用已配置的源项目启动器")
	var runtime_path := ProjectSettings.globalize_path("res://native/layout_runtime.json")
	if not FileAccess.file_exists(runtime_path) or FileAccess.get_sha256(runtime_path) != RUNTIME_SHA256:
		return _fail("helper_unavailable", "安全布局保存运行环境不可用")
	var runtime = JSON.parse_string(FileAccess.get_file_as_string(runtime_path))
	var binding_text := OS.get_environment("DEEPEYE_LAYOUT_RUNTIME")
	if binding_text.is_empty():
		return _fail("helper_unavailable", "请通过已配置的源项目启动器打开应用")
	var binding_parser := JSON.new()
	if binding_parser.parse(binding_text) != OK:
		return _fail("helper_unavailable", "安全布局保存运行环境不匹配")
	var binding = binding_parser.data
	if not (runtime is Dictionary) or not (binding is Dictionary):
		return _fail("helper_unavailable", "请通过已配置的源项目启动器打开应用")
	var python := String(binding.get("executable", ""))
	if not python.is_absolute_path() or not FileAccess.file_exists(python) or not runtime.get("executable_sha256", []).has(FileAccess.get_sha256(python)):
		return _fail("helper_unavailable", "安全布局保存运行环境不匹配")
	for entry in runtime.get("dependencies", []):
		var origin := String(binding.get(String(entry.get("origin", "")), ""))
		var file_path := origin.path_join(String(entry.get("path", "")))
		if not origin.is_absolute_path() or not FileAccess.file_exists(file_path) or FileAccess.get_sha256(file_path) != String(entry.get("sha256", "")):
			return _fail("helper_unavailable", "安全布局保存运行环境不匹配")
	var spec := _bundle_spec()
	var bundle_path := ProjectSettings.globalize_path(String(spec.path))
	if not bundle_path.is_absolute_path() or not FileAccess.file_exists(bundle_path) or FileAccess.get_sha256(bundle_path) != String(spec.sha256):
		return _fail("helper_unavailable", "安全布局保存组件不可用")
	var bundle = JSON.parse_string(FileAccess.get_file_as_string(bundle_path))
	if not (bundle is Dictionary) or int(bundle.get("schema", 0)) != 1 or bundle.keys().size() != 3:
		return _fail("helper_unavailable", "安全布局保存组件不匹配")
	for key in ["helper", "leaf"]:
		var entry = bundle.get(key, {})
		if not (entry is Dictionary) or entry.keys().size() != 2:
			return _fail("helper_unavailable", "安全布局保存组件不匹配")
		var name := String(entry.get("path", ""))
		if name != name.get_file() or name.is_empty():
			return _fail("helper_unavailable", "安全布局保存组件不匹配")
		var file_path := bundle_path.get_base_dir().path_join(name)
		if not FileAccess.file_exists(file_path) or FileAccess.get_sha256(file_path) != String(entry.get("sha256", "")):
			return _fail("helper_unavailable", "安全布局保存组件不匹配")
	var args := PackedStringArray(["-I", "-S", "-B", "-u", "-c", BOOTSTRAP, "--bundle", bundle_path, "--bundle-sha256", String(spec.sha256)])
	var command_units := python.to_utf16_buffer().size() / 2 + 3
	for arg in args:
		command_units += arg.to_utf16_buffer().size() / 2 + 3
	if command_units > 8192:
		return _fail("helper_unavailable", "布局保存组件路径过长")
	return {"ok": true, "python": python, "args": args}

func begin(path: String, text: String) -> Dictionary:
	poll()
	if _active_owner != null and _active_owner != self:
		_active_owner.poll()
		if _active_owner.has_unresolved():
			return _fail("save_pending", "上次保存尚未结束，请稍候")
	if has_unresolved():
		return _fail("save_pending", "上次保存尚未结束，请稍候")
	var windows_path := path.replace("/", "\\")
	var drive := RegEx.new()
	drive.compile("^[A-Za-z]:\\\\")
	if drive.search(windows_path) == null or windows_path.to_utf16_buffer().size() / 2 >= 260 or windows_path.to_utf8_buffer().has(0):
		return _fail("invalid_path", "布局文件必须使用受支持的本地绝对路径")
	for segment in windows_path.substr(3).split("\\"):
		if segment.is_empty() or segment in [".", ".."] or segment.ends_with(".") or segment.ends_with(" ") or segment.contains(":") or segment.to_utf16_buffer().size() / 2 > 255:
			return _fail("invalid_path", "布局文件必须使用受支持的本地绝对路径")
		for code in segment.to_utf32_buffer().to_int32_array():
			if code < 32 or code in [34, 60, 62, 124, 63, 42]:
				return _fail("invalid_path", "布局文件必须使用受支持的本地绝对路径")
		var reserved := segment.get_slice(".", 0).rstrip(" ").to_upper()
		if reserved in ["CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"] or (reserved.length() == 4 and (reserved.begins_with("COM") or reserved.begins_with("LPT")) and reserved.substr(3) in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "¹", "²", "³"]):
			return _fail("invalid_path", "布局文件必须使用受支持的本地绝对路径")
	var parent := windows_path.substr(0, windows_path.rfind("\\"))
	if parent.length() == 2:
		parent += "\\"
	if parent.to_utf16_buffer().size() / 2 + 41 >= 260:
		return _fail("invalid_path", "布局文件必须使用受支持的本地绝对路径")
	var path_key := windows_path.to_lower()
	if _unknown_paths.has(path_key):
		return _fail("outcome_unknown", "此路径已有未知保存结果；请先检查文件并选择新的路径")
	var payload := text.to_utf8_buffer()
	if payload.size() > MAX_PAYLOAD:
		return _fail("too_large", "布局文件超过 1 MiB 上限")
	var preflight := _runtime_preflight()
	if not bool(preflight.get("ok", false)):
		return preflight
	var operation := Crypto.new().generate_random_bytes(16).hex_encode()
	var digest := _sha(payload)
	var metadata := JSON.stringify({"protocol": PROTOCOL, "operation_id": operation, "target": windows_path, "payload_bytes": payload.size(), "payload_sha256": digest}).to_utf8_buffer()
	if metadata.size() < 1 or metadata.size() > MAX_METADATA:
		return _fail("invalid_path", "布局文件路径过长")
	var frame := "DLC1".to_utf8_buffer()
	_append_u32(frame, metadata.size())
	frame.append_array(metadata)
	frame.append_array(payload)
	_job = {"path": path, "path_key": path_key, "operation_id": operation, "bytes": payload.size(), "digest": digest, "started_msec": Time.get_ticks_msec(), "reaped": false, "unknown_returned": false, "cleanup_attempted": false}
	_shared = {"done": false, "launched": false, "pid": -1}
	_thread = Thread.new()
	_active_owner = self # Retain unresolved worker even if its store/shell is released.
	var error := _thread.start(_worker.bind({"path": path, "frame": frame, "python": preflight.python, "args": preflight.args}))
	if error != OK:
		_job["reaped"] = true
		_thread = null
		return _fail("helper_unavailable", "无法启动安全布局保存")
	return {"ok": true, "pending": true, "operation_id": operation}

func _sha(raw: PackedByteArray) -> String:
	var hashing := HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	if not raw.is_empty():
		hashing.update(raw)
	return hashing.finish().hex_encode()

func _append_u32(raw: PackedByteArray, value: int) -> void:
	for shift in [24, 16, 8, 0]:
		raw.append((value >> shift) & 255)

func _u32(raw: PackedByteArray, offset: int) -> int:
	return (int(raw[offset]) << 24) | (int(raw[offset + 1]) << 16) | (int(raw[offset + 2]) << 8) | int(raw[offset + 3])

func _share(values: Dictionary) -> void:
	_mutex.lock()
	_shared.merge(values, true)
	_mutex.unlock()

func _read_exact(pipe: FileAccess, count: int) -> Dictionary:
	var bytes := PackedByteArray()
	var partial_reads := 0
	while bytes.size() < count:
		var wanted := count - bytes.size()
		var chunk := pipe.get_buffer(wanted)
		if chunk.is_empty():
			break # Before a complete frame, zero is unknown; no EOF/error inference.
		if chunk.size() < wanted:
			partial_reads += 1
		bytes.append_array(chunk) # Keep every partial byte; never restart a read/frame.
	return {"bytes": bytes, "partial_reads": partial_reads}

func _drain_after_exit(pipe: FileAccess, limit: int) -> Dictionary:
	# Only after exact original exit and with no other writer in this pinned bundle.
	# Godot loses the Win32 error code: zero is this scope's endpoint, not a general
	# EOF proof. Never use eof_reached(), flush(), get_line() or unchecked NOWAIT.
	var bytes := PackedByteArray()
	while bytes.size() <= limit:
		var chunk := pipe.get_buffer(1)
		if chunk.is_empty():
			return {"bytes": bytes, "overflow": false}
		bytes.append_array(chunk)
	return {"bytes": bytes, "overflow": true}

func _worker(request: Dictionary) -> void:
	_engine_mutex.lock()
	if not _engine_verified:
		_engine_verified = FileAccess.get_sha256(OS.get_executable_path()) == GODOT_SHA256
	var engine_ok := _engine_verified
	_engine_mutex.unlock()
	if not engine_ok:
		_share({"done": true, "result": _fail("helper_unavailable", "安全布局保存运行环境不匹配")})
		return
	# The parent directory is a separate, non-atomic convenience step. Never remove it.
	var parent := String(request.path).get_base_dir()
	if not DirAccess.dir_exists_absolute(parent):
		var made := DirAccess.make_dir_recursive_absolute(parent)
		if made != OK:
			_share({"done": true, "result": _fail("io_error", "无法创建布局目录")})
			return
	var process := OS.execute_with_pipe(String(request.python), request.args, true)
	if process.is_empty():
		_share({"done": true, "result": _fail("helper_unavailable", "无法启动安全布局保存组件")})
		return
	var pid := int(process.pid)
	_share({"launched": true, "pid": pid})
	var pipe: FileAccess = process.stdio
	var errors: FileAccess = process.stderr
	# A false return has no partial count. Never retransmit any byte.
	var valid: bool = pipe.store_buffer(request.frame)
	var header := _read_exact(pipe, 8)
	var output: PackedByteArray = header.bytes
	var partial_reads := int(header.partial_reads)
	if output.size() == 8 and output.slice(0, 4).get_string_from_ascii() == "DLR1":
		var count := _u32(output, 4)
		if count >= 1 and count <= MAX_RESPONSE:
			var body := _read_exact(pipe, count)
			output.append_array(body.bytes)
			partial_reads += int(body.partial_reads)
			if body.bytes.size() != count:
				valid = false
		else:
			valid = false
	else:
		valid = false
	var original_exit := -1
	while original_exit < 0:
		original_exit = OS.get_process_exit_code(pid)
		if original_exit < 0:
			OS.delay_msec(2)
	# This exact helper and test adapters spawn no children/extra writers and emit
	# at most4096 stderr bytes. Do not generalize this wait-before-drain ordering.
	var trailing := _drain_after_exit(pipe, MAX_RESPONSE + 8 - output.size())
	if not trailing.bytes.is_empty() or bool(trailing.overflow):
		valid = false
	output.append_array(trailing.bytes)
	var stderr_result := _drain_after_exit(errors, MAX_STDERR)
	var diagnostic: PackedByteArray = stderr_result.bytes
	if bool(stderr_result.overflow):
		valid = false
		diagnostic.resize(MAX_STDERR)
	pipe.close()
	errors.close()
	_share({"done": true, "output": output, "diagnostic_bytes": diagnostic.size(), "diagnostic": diagnostic.get_string_from_utf8(), "transport_valid": valid, "original_exit": original_exit, "partial_reads": partial_reads, "stdout_trailing_bytes": trailing.bytes.size(), "stderr_overflow": stderr_result.overflow})

func _decode_result(shared: Dictionary) -> Dictionary:
	if shared.has("result"):
		return shared.result
	if not bool(shared.get("transport_valid", false)) or int(shared.get("original_exit", -1)) != 0:
		return _unknown()
	var raw: PackedByteArray = shared.get("output", PackedByteArray())
	if raw.size() < 9 or raw.slice(0, 4).get_string_from_ascii() != "DLR1":
		return _unknown()
	var count := _u32(raw, 4)
	if count < 1 or count > MAX_RESPONSE or raw.size() != count + 8:
		return _unknown()
	var bytes := raw.slice(8)
	var text := bytes.get_string_from_utf8()
	if text.to_utf8_buffer() != bytes:
		return _unknown()
	var result = JSON.parse_string(text)
	if not (result is Dictionary) or String(result.get("protocol", "")) != PROTOCOL or String(result.get("operation_id", "")) != String(_job.operation_id) or String(result.get("payload_sha256", "")) != String(_job.digest) or result.get("payload_bytes", -1) != _job.bytes or result.get("leaf_called") != true:
		return _unknown()
	var state := String(result.get("state", ""))
	if not ["committed", "already_exists", "failed_before_publish", "outcome_unknown"].has(state) or not (result.get("ok") is bool) or not (result.get("publish_attempted") is bool) or not (result.get("publication_confirmed") is bool) or not (result.get("cleanup") is Dictionary) or not (result.get("close_errors") is Array):
		return _unknown()
	if bool(result.ok) != (state == "committed") or (state == "committed" and (not bool(result.publish_attempted) or not bool(result.publication_confirmed) or not result.close_errors.is_empty())) or (state == "already_exists" and (not bool(result.publish_attempted) or bool(result.publication_confirmed))) or (state == "failed_before_publish" and bool(result.publication_confirmed)):
		return _unknown()
	result["path"] = _job.path
	result["bytes"] = _job.bytes
	if state == "outcome_unknown":
		result["code"] = "outcome_unknown"
		result["reason"] = _unknown().reason
	elif state == "already_exists":
		result["code"] = "already_exists"
		result["reason"] = "目标文件已存在；本版本仅支持另存为新文件"
	elif state == "failed_before_publish":
		result["reason"] = "布局保存失败，目标未发布"
	if not bool(result.ok):
		result["errors"] = [result.reason]
	return result

func poll() -> Dictionary:
	if _job.is_empty():
		return {"pending": false, "unresolved": false}
	_mutex.lock()
	var shared := _shared.duplicate(true)
	_mutex.unlock()
	if bool(shared.get("launched", false)) and not bool(_job.get("launch_counted", false)):
		launch_count += 1
		_job["launch_counted"] = true
		_job["diagnostic_pid"] = int(shared.pid)
	if not bool(_job.reaped) and bool(shared.get("done", false)) and _thread != null and not _thread.is_alive():
		_thread.wait_to_finish() # Only this completed owner can be joined.
		_thread = null
		_job["worker_completed"] = true
		_job["reaped"] = true
		_job["original_exit"] = int(shared.get("original_exit", -1))
		_job["diagnostic"] = shared.get("diagnostic", "")
		_job["partial_reads"] = int(shared.get("partial_reads", 0))
		_job["stdout_trailing_bytes"] = int(shared.get("stdout_trailing_bytes", 0))
		_job["stderr_overflow"] = bool(shared.get("stderr_overflow", false))
		var result := _decode_result(shared)
		_job["terminal_result"] = result
		# Exclusive original map entry; never shared/released/killed before this point.
		if bool(shared.get("launched", false)) and int(_job.original_exit) >= 0 and not bool(_job.cleanup_attempted):
			var observed := OS.get_process_exit_code(int(shared.pid))
			if observed >= 0:
				_job["cleanup_prior_exit"] = observed
				_job["cleanup_attempted"] = true # Consume original-map cleanup before the call.
				_job["cleanup_consumed"] = true
				_job["cleanup_result"] = OS.kill(int(shared.pid))
				_job["cleanup_after_exit_query"] = OS.get_process_exit_code(int(shared.pid))
				# FAILED may mean TerminateProcess rejected an exited original object.
				# Source attempts both CloseHandle calls without checking their returns.
				# Map removal is observable; kernel handle-close success is not verified.
		if bool(_job.unknown_returned):
			_late.append({"operation_id": _job.operation_id, "result": result.duplicate(true), "original_exit": _job.original_exit, "worker_completed": true, "cleanup_attempted": _job.cleanup_attempted})
		elif String(result.get("code", "")) == "outcome_unknown":
			_unknown_paths[String(_job.path_key)] = true
	return {"pending": not bool(_job.reaped) and not bool(_job.unknown_returned), "unresolved": not bool(_job.reaped), "result": _job.get("visible_result", _job.get("terminal_result", {}))}

func has_unresolved() -> bool:
	return not _job.is_empty() and not bool(_job.get("reaped", false))

func _expire() -> Dictionary:
	_job["unknown_returned"] = true
	_unknown_paths[String(_job.path_key)] = true
	var result := _unknown()
	_job["visible_result"] = result
	return result.duplicate(true)

func wait_sync() -> Dictionary:
	var deadline := Time.get_ticks_msec() + UI_WAIT_MSEC
	while true:
		var state := poll()
		if not bool(state.unresolved):
			return state.result
		if Time.get_ticks_msec() >= deadline:
			return _expire()
		OS.delay_msec(2)
	return _unknown()

func wait_async(tree: SceneTree) -> Dictionary:
	var deadline := Time.get_ticks_msec() + UI_WAIT_MSEC
	while true:
		var state := poll()
		if not bool(state.unresolved):
			return state.result
		if Time.get_ticks_msec() >= deadline:
			return _expire()
		await tree.process_frame
	return _unknown()

func take_late_results() -> Array:
	poll()
	var results := _late.duplicate(true)
	_late.clear()
	return results

func evidence() -> Dictionary:
	poll()
	return _job.duplicate(true)

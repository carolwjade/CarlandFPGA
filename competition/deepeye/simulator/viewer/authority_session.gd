extends SceneTree
## Finite renderer-only filesystem session. No control, networking or physics.
const MAX_BYTES := 4096
var _directory := ""
var _bootstrap: Dictionary = {}
var _scene
var _expected := 1
var _started := 0
var _active := false
var _done := false

func _initialize() -> void:
	_start.call_deferred()

func _object(path: String, limit: int = MAX_BYTES) -> Variant:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > limit:
		return null
	var raw := file.get_buffer(limit + 1)
	file.close()
	if raw.size() > limit:
		return null
	var value = JSON.parse_string(raw.get_string_from_utf8())
	return value if typeof(value) == TYPE_DICTIONARY else null

func _keys(value: Dictionary, keys: Array) -> bool:
	if value.size() != keys.size():
		return false
	for key in keys:
		if not value.has(key):
			return false
	return true

func _integer(value: Variant, low: int, high: int) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value)) and value >= low and value <= high and value == floor(value)

func _valid_run(value: Variant) -> bool:
	if typeof(value) != TYPE_STRING or value.length() < 1 or value.length() > 128:
		return false
	for i in value.length():
		if value.unicode_at(i) < 32 or value.unicode_at(i) == 127:
			return false
	return true

func _write(name: String, document: Dictionary) -> bool:
	var raw := JSON.stringify(document).to_utf8_buffer()
	var dest := _directory.path_join(name)
	var temp := dest + ".tmp"
	if raw.size() > MAX_BYTES or FileAccess.file_exists(dest) or FileAccess.file_exists(temp):
		return false
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return false
	file.store_buffer(raw)
	file.flush()
	var error := file.get_error()
	file.close()
	return error == OK and DirAccess.rename_absolute(temp, dest) == OK

func _gates_closed() -> bool:
	return _scene != null and _scene.shell._run_button.disabled and _scene.shell._continue_button.disabled and _scene.shell._pause_button.disabled and not _scene.document.control_bridge_connected and not _scene.document.is_motion_active()

func _start() -> void:
	_started = Time.get_ticks_msec()
	var args := OS.get_cmdline_user_args()
	if args.size() != 2 or args[0] != "--session-dir" or not args[1].is_absolute_path():
		print("RENDERER_SESSION bootstrap_arguments_invalid")
		quit(2)
		return
	_directory = args[1]
	var boot = _object(_directory.path_join("bootstrap.json"), 1024)
	if boot == null or not _keys(boot, ["schema", "run_id", "nonce", "max_messages", "lifetime_ms"]):
		print("RENDERER_SESSION bootstrap_invalid")
		quit(2)
		return
	if not _integer(boot.schema, 1, 1) or not _valid_run(boot.run_id) or typeof(boot.nonce) != TYPE_STRING or boot.nonce.length() != 32 or not boot.nonce.is_valid_hex_number(false) or not _integer(boot.max_messages, 2, 16) or not _integer(boot.lifetime_ms, 1, 8000):
		print("RENDERER_SESSION bootstrap_values_invalid")
		quit(2)
		return
	_bootstrap = boot
	var packed = load("res://viewer/main.tscn")
	if packed == null:
		quit(2)
		return
	_scene = packed.instantiate()
	root.add_child(_scene)
	if not _scene.bind_authority_renderer(boot.run_id) or not _gates_closed():
		_finish("gates_open", 2)
		return
	var target: Node3D = _scene.get("_drill_root")
	var body = target.get_node_or_null("DrillPDC")
	var report: Dictionary = _scene._asset_presenter.report()
	var asset := {"target": str(target.name), "asset_id": "" if body == null else body.get_meta("asset_id", ""),
		"mesh_count": target.find_children("*", "MeshInstance3D", true, false).size(),
		"state": report.state, "diagnostics": report.diagnostics}
	if not _write("ready.json", {"nonce": boot.nonce, "run_id": boot.run_id, "asset": asset, "gates_closed": _gates_closed()}):
		_finish("ack_failed", 2)
		return
	_active = true

func _process(_delta: float) -> bool:
	if not _active or _done:
		return false
	if Time.get_ticks_msec() - _started >= int(_bootstrap.lifetime_ms):
		_finish("timeout", 1)
		return false
	if not _gates_closed():
		_finish("gates_open", 2)
		return false
	if _expected > int(_bootstrap.max_messages):
		_finish("message_limit", 1)
		return false
	var path := _directory.path_join("frame-%06d.json" % _expected)
	if not FileAccess.file_exists(path):
		return false
	var sequence := _expected
	_expected += 1  # Consume before any parse/application/publication; never retry.
	var message = _object(path)
	var accepted := false
	var error := "message_invalid"
	var closing := false
	if message != null:
		var kind = message.get("kind")
		var fields := ["sequence", "nonce", "run_id", "kind", "frame"] if kind == "frame" else ["sequence", "nonce", "run_id", "kind"]
		if _keys(message, fields) and _integer(message.get("sequence"), sequence, sequence) and message.get("nonce") == _bootstrap.nonce and message.get("run_id") == _bootstrap.run_id:
			if kind == "frame":
				var reply: Dictionary = _scene.present_authority_frame(message.frame)
				accepted = reply.get("accepted", false)
				error = reply.get("error", "")
			elif kind == "close":
				accepted = true
				error = ""
				closing = true
	var ack := {"sequence": sequence, "nonce": _bootstrap.nonce, "run_id": _bootstrap.run_id,
		"accepted": accepted, "error": error, "native": _scene.read_authority_presentation(), "gates_closed": _gates_closed()}
	if not _write("ack-%06d.json" % sequence, ack):
		_finish("ack_failed", 2)
	elif closing:
		_finish("closed", 0)
	return false

func _finish(status: String, code: int) -> void:
	if _done:
		return
	_done = true
	_active = false
	var native: Dictionary = {} if _scene == null else _scene.read_authority_presentation()
	var terminal := {"nonce": _bootstrap.get("nonce", ""), "run_id": _bootstrap.get("run_id", ""),
		"status": status, "last_sequence": _expected - 1, "native": native, "gates_closed": _gates_closed()}
	var saved := _write("terminal.json", terminal)
	print(JSON.stringify({"renderer_terminal": terminal, "terminal_saved": saved}))
	quit(code if saved else 2)

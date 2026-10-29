extends SceneTree
## New owned process startup. No secret is read from argv, environment or file.
const BridgeScript = preload("res://runtime/world_motion_bridge.gd")
const LayoutCodecScript = preload("res://editor/layout_codec.gd")
var _bridge
var _startup_started := false
var _startup_refused := false
var _run_id: String = ""
var _original_main

func _initialize() -> void:
	call_deferred("_start_owned_world")

func _start_owned_world() -> void:
	_bridge = BridgeScript.new()
	_bridge._diag_timing_arm()
	# The original parent has written <=2048 bytes and closed the empty pipe.
	# This is pre-activation startup, not a hard deadline claim for a kernel read.
	var raw := OS.read_string_from_stdin(2049).to_utf8_buffer()
	# The original native writer emits compact ASCII JSON, including escapes.
	# Refuse decoded non-ASCII instead of accepting UTF-8 replacement text.
	for byte in raw:
		if byte > 127:
			print("DEEYE_OWNED_BOOTSTRAP_REFUSED bytes=", raw.size())
			quit(81)
			return
	var checked: Dictionary = _bridge.decode_bootstrap(raw)
	if not checked.get("ok", false):
		print("DEEYE_OWNED_BOOTSTRAP_REFUSED bytes=", raw.size())
		quit(81)
		return
	print("DEEYE_OWNED_BOOTSTRAP_ACCEPTED bytes=", raw.size())
	var boot: Dictionary = checked.value
	_run_id = boot.run_id
	var file := FileAccess.open("res://owned-input/layout.json", FileAccess.READ)
	if file == null:
		quit(82)
		return
	var layout_length: int = file.get_length()
	if layout_length < 1 or layout_length > LayoutCodecScript.MAX_FILE_BYTES:
		file.close()
		quit(82)
		return
	var layout_raw := file.get_buffer(layout_length)
	var layout_read_error: int = file.get_error()
	var layout_length_after: int = file.get_length()
	file.close()
	if layout_read_error != OK or layout_length_after != layout_length or layout_raw.size() != layout_length or _bridge.sha256(layout_raw) != boot.raw_layout_sha256:
		quit(83)
		return
	var text := layout_raw.get_string_from_utf8()
	if text.to_utf8_buffer() != layout_raw:
		quit(84)
		return
	var scene = load("res://viewer/main.tscn")
	if not scene is PackedScene:
		quit(85)
		return
	# Exactly one actual product Main/document/presenter is constructed here.
	_original_main = scene.instantiate() as Node3D
	if _original_main == null:
		quit(86)
		return
	root.add_child(_original_main)
	var status: Dictionary = _original_main._owned_startup_status()
	if not status.get("ok", false) is bool or not status.get("ok", false):
		_refuse_startup(status)
		quit(88)
		return
	if _original_main.document == null or not _original_main.document.can_edit():
		quit(87)
		return
	var applied: Dictionary = _original_main.document.apply_layout_text(text)
	status = _original_main._owned_startup_status()
	if not applied.get("ok", false) is bool or not applied.get("ok", false) or not status.get("ok", false) is bool or not status.get("ok", false):
		_refuse_startup(status if not status.get("ok", false) else {"stage":"layout", "code":"layout_apply_refused", "variant_type":0, "slot_code":0})
		quit(88)
		return
	var started: Variant = _bridge.start_original(_original_main, boot, layout_raw)
	status = _original_main._owned_startup_status()
	if not started is bool or not started or not _bridge._owned_startup_complete() or not status.get("ok", false) is bool or not status.get("ok", false):
		_refuse_startup(_bridge._owned_startup_failure() if not started or not _bridge._owned_startup_complete() else status)
		quit(88)
		return
	_startup_started = true

func _process(_delta: float) -> bool:
	if _startup_started and is_instance_valid(_bridge) and _bridge._owned_startup_complete():
		_bridge.pump()
	return false

func _refuse_startup(failure: Dictionary) -> void:
	if _startup_refused:
		return
	_startup_refused = true
	print("DEEYE_OWNED_STARTUP_REFUSED ", JSON.stringify({"schema":1, "run_id":_run_id,
		"stage":failure.get("stage", "startup"), "code":failure.get("code", "startup_incomplete"),
		"variant_type":failure.get("variant_type", 0), "slot_code":failure.get("slot_code", 0)}))

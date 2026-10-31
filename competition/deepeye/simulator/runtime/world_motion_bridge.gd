extends RefCounted
## Private same-original-Main bridge. Hashes/IDs/labels never create authority.
const MAGIC := "DEYWRL01"
const CONTROL_MAX := 16384
const UI_STATUS_MAX := 8192
const PAYLOAD_MAX := 65536
const SNAPSHOT_MAX := 134217728
const CHUNK_MAX := 45056
const CHUNKS_MAX := 3072
const PUBLICATION_MAX := 16
const IO_MAX := 65536
const FRAMES_MAX := 8
const NODE_MAX := 4096
const SURFACE_MAX := 64
const VERTEX_MAX := 1000000
const INDEX_MAX := 3000000
const U64_MAX := "18446744073709551615"
const SOURCE_FILES := ["res://viewer/main.gd", "res://editor/scene_document.gd",
	"res://viewer/asset_presenter.gd", "res://editor/layout_codec.gd", "res://ui/shell.gd",
	"res://world/asset_library.gd", "res://world/drill_geometry.gd", "res://world/obstacle_geometry.gd",
	"res://world/frame_geometry.gd", "res://runtime/world_motion_bridge.gd", "res://runtime/owned_world_start.gd"]
# Separate from the unchanged wire writer inventory. Every loaded dependency
# and the fixed scene/project configuration participates in source closure.
const PROFILE_EXTRA := ["res://editor/gate_numeric.gd", "res://editor/gate_json_numbers.gd",
	"res://editor/layout_store.gd", "res://editor/layout_commit_bridge.gd",
	"res://runtime/managed_writer_controls.gd", "res://runtime/managed_writer_foreign_probe.gd",
	"res://viewer/authority_pose_bridge.gd", "res://viewer/authority_session.gd"]
const PROFILE_CONFIG := ["res://project.godot", "res://viewer/main.tscn"]

enum OwnedStartup { NEW, STARTING, STARTED, FAILED }
var _owned_startup_state := OwnedStartup.NEW
var _owned_first_failure: Dictionary = {}

var _main
var _refs: Dictionary = {}
var _boot: Dictionary = {}
var _key := PackedByteArray()
var _crypto := Crypto.new()
var _socket: StreamPeerTCP
var _connected_once := false
var _hello_sent := false
var _faulted := false
var _ui_status_display_records := 0 # Observation only; never reset on freeze/edit.
var _state := "ACQUIRING"
var _in_seq := PackedByteArray([0,0,0,0,0,0,0,0])
var _out_seq := PackedByteArray([0,0,0,0,0,0,0,0])
var _rx := PackedByteArray()
var _tx := PackedByteArray()
var _tx_offset := 0
var _outbox: Array = []
var _snapshot_raw := PackedByteArray()
var _snapshot_cursor := -1
var _snapshot_sha := ""
var _snapshot_chunks := 0
var _snapshot_counts: Dictionary = {}
var _freeze: Dictionary = {}
var _token: RefCounted
var _last_epoch := "0"
var _source_pins: Dictionary = {}
var _catalog: Array = []
var _catalog_sha := ""
var _writer_sha := ""
var _scalar_width := 0
var _required: Array = []
var _immutable_meshes: Array = []
var _immutable_shapes: Array = []
var _mesh_payloads: Dictionary = {}
var _static_digest := ""
var _doc_generation := -1
var _geometry_generation := -1
var _raw_generation := -1
var _raw_layout := PackedByteArray()
var _pose_local: Transform3D
var _pose_global: Transform3D
var _pose_revision := "0"
var _initialized := false
var _publication: Dictionary = {}
var _seen_operations: Dictionary = {}
var _query_consumed := false
var _editable_pending := false
var _edit_pending := ""
var _stop_pending := ""
var _audit_busy := false
var _capture_error := ""
var _json_text := ""
var _json_index := 0
var _json_error := false
var _freeze_operation := ""
var _geometry_identity := ""
var _stop_received := false
var _admission_stopped := false
var _publication_count := 0
var _publication_operations: Dictionary = {}
var _queried_publications: Dictionary = {}
var _fixture := {"withhold_first_publish_ack": false, "edit_once_after_unlock": false}
var _fixture_ack_consumed := false
var _fixture_edit_consumed := false
var _retired_freeze_id := "none"
var _retired_epoch := "0"
var _profile_pins: Dictionary = {}
var _profile_scripts: Dictionary = {}
var _coverage: Dictionary = {}
var _retired_coverage: Dictionary = {}
var _coverage_invalid: bool = false
var _controls: RefCounted
var _controls_phase: String = ""
var _controls_barrier: bool = false
var _controls_poison_consumed: bool = false
var _coverage_turn_valid: bool = false
var _coverage_resources_turn: Dictionary = {}

# Private bounded metadata recorder. No controller-facing observations.
var _diag_timing_rows := PackedInt64Array()
var _diag_timing_armed := false
var _diag_timing_flushed := false
var _diag_timing_count := 0
var _diag_timing_overflow := false
var _diag_timing_dropped := 0

func _diag_timing_arm() -> void:
	_diag_timing_rows.resize(2048 * 5)
	_diag_timing_count = 0
	_diag_timing_overflow = false
	_diag_timing_dropped = 0
	_diag_timing_flushed = false
	_diag_timing_armed = true

func _diag_timing_mark(code: int, arg0: int = 0, arg1: int = 0) -> void:
	if not _diag_timing_armed:
		return
	if _diag_timing_count >= 2048:
		_diag_timing_overflow = true
		_diag_timing_dropped += 1
		return
	var offset: int = _diag_timing_count * 5
	_diag_timing_rows[offset] = _diag_timing_count + 1
	_diag_timing_rows[offset + 1] = code
	_diag_timing_rows[offset + 2] = Time.get_ticks_usec()
	_diag_timing_rows[offset + 3] = arg0
	_diag_timing_rows[offset + 4] = arg1
	_diag_timing_count += 1

func _diag_timing_flush_once() -> void:
	if not _diag_timing_armed or _diag_timing_flushed:
		return
	# Freeze before allocating rows, encoding JSON or printing.
	_diag_timing_armed = false
	_diag_timing_flushed = true
	if _diag_timing_count < 2048:
		var offset: int = _diag_timing_count * 5
		_diag_timing_rows[offset] = _diag_timing_count + 1
		_diag_timing_rows[offset + 1] = 22
		_diag_timing_rows[offset + 2] = Time.get_ticks_usec()
		_diag_timing_rows[offset + 3] = 0
		_diag_timing_rows[offset + 4] = 0
		_diag_timing_count += 1
	else:
		_diag_timing_overflow = true
		_diag_timing_dropped += 1
	var rows: Array = []
	for index in _diag_timing_count:
		var offset: int = index * 5
		rows.append([_diag_timing_rows[offset], _diag_timing_rows[offset + 1], _diag_timing_rows[offset + 2], _diag_timing_rows[offset + 3], _diag_timing_rows[offset + 4]])
	print("DEEYE_AUDIT_TIMING_TRACE ", JSON.stringify({"schema":1, "run_id":String(_boot.run_id),
		"unit":"ticks_usec", "capacity":2048, "count":_diag_timing_count,
		"overflow":_diag_timing_overflow, "dropped":_diag_timing_dropped, "rows":rows}))

func sha256(raw: PackedByteArray) -> String:
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK or context.update(raw) != OK:
		return ""
	return context.finish().hex_encode()

func _exact(value, keys: Array) -> bool:
	if not value is Dictionary or value.size() != keys.size():
		return false
	for key in keys:
		if not value.has(key):
			return false
	return true

func _hex(value, count: int) -> bool:
	if not value is String or value.length() != count:
		return false
	for c in value:
		if not "0123456789abcdef".contains(c):
			return false
	return true

func _u64(value) -> bool:
	if not value is String or value.is_empty() or value.length() > 20:
		return false
	if value.length() > 1 and value[0] == "0":
		return false
	for c in value:
		if not "0123456789".contains(c):
			return false
	return value.length() < 20 or value <= U64_MAX

func _label(value) -> bool:
	if not value is String or value.is_empty():
		return false
	var encoded: PackedByteArray = value.to_utf8_buffer()
	return encoded.size() <= 256 and not encoded.has(0)

func _next_decimal(value: String) -> String:
	if not _u64(value) or value == U64_MAX:
		return ""
	var result := value
	var index := result.length() - 1
	while index >= 0 and result[index] == "9":
		result = result.substr(0, index) + "0" + result.substr(index + 1)
		index -= 1
	if index < 0:
		return "1" + result
	result = result.substr(0, index) + str(int(result[index]) + 1) + result.substr(index + 1)
	return result

func _increment_sequence(value: PackedByteArray) -> PackedByteArray:
	var result := value.duplicate()
	for index in range(7, -1, -1):
		if result[index] < 255:
			result[index] += 1
			return result
		result[index] = 0
	return PackedByteArray()

func _be(value: int, width: int) -> PackedByteArray:
	var bytes := PackedByteArray()
	bytes.resize(width)
	for index in width:
		bytes[width - index - 1] = (value >> (index * 8)) & 255
	return bytes

func _object_id(value: Object) -> String:
	var native_id: int = value.get_instance_id()
	if native_id >= 0:
		return str(native_id)
	# ObjectID is an unsigned bit identity; do not turn an int64 carrier's high
	# bit into a negative wire value. This encoding grants no object capability.
	var decimal := "0"
	for byte in _be(native_id, 8):
		var carry: int = byte
		var next := ""
		for index in range(decimal.length() - 1, -1, -1):
			var number: int = int(decimal[index]) * 256 + carry
			next = str(number % 10) + next
			carry = int(number / 10)
		while carry > 0:
			next = str(carry % 10) + next
			carry = int(carry / 10)
		decimal = next
	return decimal

func _u32(raw: PackedByteArray, offset: int) -> int:
	var value := 0
	for index in 4:
		value = (value << 8) | raw[offset + index]
	return value

func decode_bootstrap(raw: PackedByteArray) -> Dictionary:
	if raw.is_empty() or raw.size() > 2048:
		return {"ok": false}
	var parsed := _strict_json(raw)
	if not parsed.ok or not _exact(parsed.value, ["protocol","address","port","key_hex","launch_challenge","run_id","source_bundle_sha256","engine_sha256","raw_layout_sha256"]):
		return {"ok": false}
	var value: Dictionary = parsed.value
	if value.protocol != MAGIC or value.address != "127.0.0.1" or not value.port is int or value.port < 1 or value.port > 65535 or not _label(value.run_id):
		return {"ok": false}
	for field in ["key_hex","launch_challenge","source_bundle_sha256","engine_sha256","raw_layout_sha256"]:
		if not _hex(value[field], 64):
			return {"ok": false}
	return {"ok": true, "value": value}

func start_original(main: Node3D, boot: Dictionary, raw_layout: PackedByteArray) -> bool:
	if _owned_startup_state != OwnedStartup.NEW:
		return false
	_owned_startup_state = OwnedStartup.STARTING
	if not is_instance_valid(main) or not main.is_inside_tree() or main.get_parent() != main.get_tree().root:
		return _owned_startup_fail("references_refused")
	var main_status: Dictionary = main._owned_startup_status()
	if not main_status.get("ok", false) is bool or not main_status.get("ok", false):
		return _owned_startup_fail("main_incomplete")
	_main = main
	if not _main._owned_attach_world_bridge(self):
		return _owned_startup_fail("participant_bind_refused")
	_refs = _main._owned_world_references(self)
	_refs["native_root"] = _main.get_parent()
	if not _owned_prepared_references():
		return _owned_startup_fail("references_refused")
	if not _exact(boot, ["protocol","address","port","key_hex","launch_challenge","run_id","source_bundle_sha256","engine_sha256","raw_layout_sha256"]) or not _hex(boot.key_hex, 64) or boot.protocol != MAGIC or boot.address != "127.0.0.1" or not boot.port is int or boot.port < 1 or boot.port > 65535 or not _label(boot.run_id):
		return _owned_startup_fail("bootstrap_refused")
	_boot = boot.duplicate(true)
	_key = String(_boot.key_hex).hex_decode()
	_boot.erase("key_hex")
	boot.erase("key_hex")
	_raw_layout = raw_layout.duplicate()
	_raw_generation = _refs.document._owned_generation(self)
	var native_vector_bytes := PackedVector3Array([Vector3.ZERO]).to_byte_array().size()
	_scalar_width = int(native_vector_bytes * 8 / 3)
	if _scalar_width != 32 and _scalar_width != 64:
		return _owned_startup_fail("scalar_refused")
	for path in SOURCE_FILES:
		var file := FileAccess.open(path, FileAccess.READ)
		if file == null:
			return _owned_startup_fail("acquisition_refused")
		_source_pins[path] = sha256(file.get_buffer(file.get_length()))
		file.close()
	_catalog = _fixed_catalog()
	_catalog_sha = _source_pins["res://world/asset_library.gd"]
	_writer_sha = _writer_digest()
	var fixture_file := FileAccess.open("res://owned-input/diagnostic-case.json", FileAccess.READ)
	if fixture_file == null or fixture_file.get_length() > 256:
		return _owned_startup_fail("acquisition_refused")
	var fixture_raw := fixture_file.get_buffer(fixture_file.get_length())
	fixture_file.close()
	var fixture_value := _strict_json(fixture_raw)
	if not fixture_value.ok or not _exact(fixture_value.value, ["withhold_first_publish_ack","edit_once_after_unlock"]):
		return _owned_startup_fail("acquisition_refused")
	if not fixture_value.value.withhold_first_publish_ack is bool or not fixture_value.value.edit_once_after_unlock is bool:
		return _owned_startup_fail("acquisition_refused")
	_fixture = fixture_value.value
	if not _load_managed_controls() or not _pin_source_profile():
		return _owned_startup_fail("source_profile_refused")
	_refs.document.owned_edit_requested.connect(_on_edit_request)
	_refs.document.stop_requested.connect(_on_stop_request)
	_refs.document.layout_changed.connect(_on_document_changed)
	_refs.document.gates_changed.connect(_on_document_changed)
	_socket = StreamPeerTCP.new()
	_connected_once = true
	if _socket.connect_to_host("127.0.0.1", int(_boot.port)) != OK:
		local_fault("channel_fault")
		return _owned_startup_fail("socket_refused")
	_owned_startup_state = OwnedStartup.STARTED
	return true

func _load_managed_controls() -> bool:
	var path: String = "res://owned-input/managed-writer-controls.json"
	if not FileAccess.file_exists(path):
		return true
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > 1024:
		return false
	var raw: PackedByteArray = file.get_buffer(file.get_length())
	file.close()
	var parsed: Dictionary = _strict_json(raw)
	if not parsed.ok or not _exact(parsed.value, ["schema", "enabled", "run_id"]):
		return false
	var config: Dictionary = parsed.value
	if not config.schema is int or config.schema != 1 or not config.enabled is bool or not config.run_id is String or config.run_id != _boot.run_id:
		return false
	if not config.enabled:
		return true
	var source: Script = load("res://runtime/managed_writer_controls.gd")
	if source == null or not source.can_instantiate():
		return false
	_controls = source.new()
	return _controls != null and _controls.configure(config)

func _pin_source_profile() -> bool:
	for path in SOURCE_FILES + PROFILE_EXTRA + PROFILE_CONFIG:
		var file: FileAccess = FileAccess.open(path, FileAccess.READ)
		if file == null or file.get_length() > 1048576:
			return false
		var raw: PackedByteArray = file.get_buffer(file.get_length())
		file.close()
		_profile_pins[path] = sha256(raw)
		if path.ends_with(".gd") and (not path.contains("managed_writer_") or _controls != null):
			var script: Script = load(path)
			if script == null or sha256(script.source_code.to_utf8_buffer()) != _profile_pins[path]:
				return false
			_profile_scripts[path] = script
	return _source_profile_current()

func _source_profile_current() -> bool:
	_diag_timing_mark(5)
	var result: bool = _source_profile_current_diag_core()
	_diag_timing_mark(6)
	return result

func _source_profile_current_diag_core() -> bool:
	if not _owned_prepared_references():
		return false
	# One profile pass per synchronous turn, never per node; no execution of
	# arbitrary source or dynamic class discovery grants writer coverage.
	if _profile_pins.size() != SOURCE_FILES.size() + PROFILE_EXTRA.size() + PROFILE_CONFIG.size():
		return false
	for path in _profile_pins:
		if FileAccess.get_sha256(path) != _profile_pins[path]:
			return false
	for path in _profile_scripts:
		var script: Script = _profile_scripts[path]
		if script.resource_path != path or sha256(script.source_code.to_utf8_buffer()) != _profile_pins[path]:
			return false
	for pair in [[_main,"res://viewer/main.gd"], [_refs.document,"res://editor/scene_document.gd"],
		[_refs.presenter,"res://viewer/asset_presenter.gd"], [_refs.shell,"res://ui/shell.gd"],
		[self,"res://runtime/world_motion_bridge.gd"], [_main.get_tree(),"res://runtime/owned_world_start.gd"]]:
		if pair[0].get_script() != _profile_scripts[pair[1]]:
			return false
	var store: Object = _refs.shell._layout_store
	if store == null or store.get_script() != _profile_scripts["res://editor/layout_store.gd"]:
		return false
	if store._bridge != null and store._bridge.get_script() != _profile_scripts["res://editor/layout_commit_bridge.gd"]:
		return false
	if _refs.presenter._factory != _profile_scripts["res://world/asset_library.gd"]:
		return false
	if _controls != null and _controls.get_script() != _profile_scripts["res://runtime/managed_writer_controls.gd"]:
		return false
	for setting in ProjectSettings.get_property_list():
		if String(setting.name).begins_with("autoload/"):
			return false
	if not GDExtensionManager.get_loaded_extensions().is_empty():
		return false
	return true

func _managed_walk(node: Node, nodes: Array) -> bool:
	if not is_instance_valid(node) or nodes.size() >= NODE_MAX:
		return false
	nodes.append(node)
	for child in node.get_children(true):
		if not _managed_walk(child, nodes):
			return false
	return true

func _managed_candidate_validation() -> Dictionary:
	_diag_timing_mark(7)
	var result: Dictionary = _managed_candidate_validation_diag_core()
	_diag_timing_mark(8)
	return result

func _managed_candidate_validation_diag_core() -> Dictionary:
	if not _original_references() or not _source_profile_current():
		return {"ok": false, "code": "source_profile"}
	var tree: SceneTree = _main.get_tree()
	var root: Window = tree.root
	if root.get_script() != null or root.get_child_count(true) != 1 or root.get_child(0, true) != _main or not tree.get_processed_tweens().is_empty():
		return {"ok": false, "code": "unknown_root_or_tween"}
	if root.process_thread_group != Node.PROCESS_THREAD_GROUP_INHERIT and root.process_thread_group != Node.PROCESS_THREAD_GROUP_MAIN_THREAD:
		return {"ok": false, "code": "unknown_root_thread"}
	var readiness: Dictionary = _refs.shell._owned_freeze_ready(_main, _refs.document)
	if not readiness.get("ok", false):
		return readiness
	var nodes: Array = []
	if not _managed_walk(_main, nodes):
		return {"ok": false, "code": "node_budget"}
	# All observer scripts are checked before custody, including internal nodes.
	for node in nodes:
		var script: Script = node.get_script()
		if script != null and not ((node == _main and script == _profile_scripts["res://viewer/main.gd"]) or (node == _refs.shell and script == _profile_scripts["res://ui/shell.gd"])):
			return {"ok": false, "code": "foreign_node_script"}
		if node.process_thread_group != Node.PROCESS_THREAD_GROUP_INHERIT and node.process_thread_group != Node.PROCESS_THREAD_GROUP_MAIN_THREAD:
			return {"ok": false, "code": "unknown_process_thread"}
		if node is AnimationPlayer or node is AnimationTree or node is Skeleton3D or node is GPUParticles3D or node is CPUParticles3D:
			return {"ok": false, "code": "active_geometry_engine"}
		if _role(node) != "observer":
			if not _main._owned_custody_contains(node):
				return {"ok": false, "code": "unregistered_managed_node"}
			if not node is Node3D or node.top_level or node.is_scale_disabled() or node.is_physics_processing() or node.is_physics_processing_internal():
				return {"ok": false, "code": "unqualified_geometry_flags"}
			if node is CollisionObject3D and (node.collision_layer != 0 or node.collision_mask != 0):
				return {"ok": false, "code": "physics_enabled"}
			if node is CollisionShape3D and not node.disabled:
				return {"ok": false, "code": "physics_enabled"}
	return _main._owned_validate_custody(self, _token)

func _issue_managed_coverage() -> bool:
	if _coverage_invalid or not _coverage.is_empty():
		return false
	var validation: Dictionary = _managed_candidate_validation()
	if not validation.get("ok", false):
		return false
	var context: Dictionary = _main._owned_coverage_context(self, _token, _doc_generation, _geometry_generation)
	if context.is_empty() or not context.get("members") is Array:
		return false
	var members: Dictionary = {}
	for node in context.members:
		members[node] = true
	_coverage = {"main": _main, "document": _refs.document, "presenter": _refs.presenter,
		"workspace": _refs.workspace, "drill": _refs.drill, "token": _token,
		"document_generation": _doc_generation, "geometry_generation": _geometry_generation,
		"epoch": _freeze.world_epoch, "members": members, "valid": true, "retired": false}
	_coverage_turn_valid = true
	_coverage_resources_turn = validation.resource_fingerprints
	return true

func _coverage_qualified(token: RefCounted, doc_generation: int, geometry_generation: int) -> bool:
	if _coverage_invalid or _coverage.is_empty() or not _coverage.get("valid", false) or _coverage.get("retired", true):
		return false
	if token == null or token != _token or token != _coverage.token or doc_generation != _doc_generation or geometry_generation != _geometry_generation:
		return false
	if _coverage.main != _main or _coverage.document != _refs.document or _coverage.presenter != _refs.presenter or _coverage.workspace != _refs.workspace or _coverage.drill != _refs.drill:
		return false
	return _refs.document._owned_is_locked(self, token) and _refs.presenter._owned_is_frozen(_main, self, token) and _refs.document._owned_generation(self) == doc_generation and _main._owned_geometry_revision(self) == geometry_generation

func _refresh_managed_coverage() -> bool:
	_coverage_turn_valid = false
	_coverage_resources_turn = {}
	if not _coverage_qualified(_token, _doc_generation, _geometry_generation):
		return false
	var validation: Dictionary = _managed_candidate_validation()
	if not validation.get("ok", false):
		return false
	_coverage_turn_valid = true
	_coverage_resources_turn = validation.resource_fingerprints
	return true

func _retire_managed_coverage() -> void:
	_coverage_turn_valid = false
	_coverage_resources_turn = {}
	if not _coverage.is_empty():
		_coverage["valid"] = false
		_coverage["retired"] = true
		_retired_coverage = _coverage
		_coverage = {}

func _run_managed_phase(phase: String, method: String) -> bool:
	if _controls == null:
		return true
	if _controls_barrier or not _controls_phase.is_empty() or _publication.get("state", "") == "APPLYING":
		return false
	_controls_barrier = true
	_controls_phase = phase
	var result: bool = _controls.call(method, self)
	_controls_phase = ""
	_controls_barrier = false
	return result

func _managed_control_context(actor: Object, phase: String) -> Dictionary:
	if actor != _controls or not _controls_barrier or phase != _controls_phase or _publication.get("state", "") == "APPLYING":
		return {}
	if phase == "post_unlock":
		if not _freeze.is_empty() or _token != null or not _refs.document.can_edit():
			return {}
	elif _freeze.is_empty() or _token == null or not _refs.document._owned_is_locked(self, _token):
		return {}
	if phase == "final_content" and (not _stop_received or not _admission_stopped or _state != "BOUND_STOPPED"):
		return {}
	return {"main": _main, "document": _refs.document, "presenter": _refs.presenter,
		"workspace": _refs.workspace, "drill": _refs.drill, "camera": _refs.camera,
		"obstacles": _refs.obstacles, "token": _token, "document_generation": _doc_generation,
		"geometry_generation": _geometry_generation, "epoch": _freeze.get("world_epoch", "0"),
		"legal_edit_consumed": _fixture_edit_consumed}

func _managed_control_probe(actor: Object) -> Dictionary:
	if actor != _controls or not _controls_barrier or _controls_phase != "pre_admission" or not _coverage.is_empty():
		return {"ok": false, "code": "control_phase"}
	return _managed_candidate_validation()

func _managed_control_qualified(actor: Object, token: RefCounted, doc_generation: int, geometry_generation: int) -> bool:
	return actor == _controls and _controls_barrier and ["frozen", "refreeze"].has(_controls_phase) and _coverage_qualified(token, doc_generation, geometry_generation)

func _managed_control_fingerprint(actor: Object) -> Dictionary:
	if actor != _controls or not _controls_barrier or _controls_phase != "frozen":
		return {}
	return _main._owned_frozen_fingerprint(self, _token)

func _managed_control_old_invalid(actor: Object) -> bool:
	return actor == _controls and _controls_barrier and ["post_unlock", "refreeze"].has(_controls_phase) and not _retired_coverage.is_empty() and not _retired_coverage.valid and _retired_coverage.retired and _retired_coverage.token != _token

func _managed_control_poison_mesh(actor: Object) -> Dictionary:
	if actor != _controls or not _controls_barrier or _controls_phase != "final_content" or _controls_poison_consumed or not _stop_received or not _admission_stopped or _state != "BOUND_STOPPED" or _publication.get("state", "") == "APPLYING":
		return {}
	var stages: Dictionary = _controls.status()
	if not stages.get("refreeze", false) or _coverage.is_empty() or _coverage.epoch != _freeze.world_epoch or not _refresh_managed_coverage():
		return {}
	_controls_poison_consumed = true
	for retained in _immutable_meshes:
		var mesh: Mesh = retained.mesh
		if not mesh is ArrayMesh or mesh.get_surface_count() != 1:
			continue
		var arrays: Array = mesh.surface_get_arrays(0)
		if arrays.size() != Mesh.ARRAY_MAX or not arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array or arrays[Mesh.ARRAY_VERTEX].is_empty():
			continue
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX].duplicate()
		var primitive: int = mesh.surface_get_primitive_type(0)
		var material: Material = mesh.surface_get_material(0)
		var old_count: int = mesh.get_surface_count()
		var original_vertex: Vector3 = vertices[0]
		vertices[0] += Vector3(0.001, 0.0, 0.0)
		arrays[Mesh.ARRAY_VERTEX] = vertices
		mesh.clear_surfaces()
		mesh.add_surface_from_arrays(primitive, arrays)
		mesh.surface_set_material(0, material)
		var observed: Array = mesh.surface_get_arrays(0)
		var observed_vertices: PackedVector3Array = observed[Mesh.ARRAY_VERTEX]
		var changed: bool = retained.node.mesh == mesh and mesh.get_surface_count() == old_count and observed_vertices.size() == vertices.size() and observed_vertices[0] == vertices[0] and observed_vertices[0] != original_vertex
		var detected: bool = not _refresh_managed_coverage()
		if detected:
			local_fault("mutation")
		var sticky: bool = _faulted and _coverage_invalid and not audit_frame() and not _coverage_qualified(_token, _doc_generation, _geometry_generation)
		return {"changed": changed, "detected": detected, "sticky": sticky, "surfaces": old_count, "vertices": vertices.size(), "array_mesh": 1, "primitive_mesh": 0}
	# A bounded random1 may be fault/casing and therefore contain no ArrayMesh.
	# Use an already captured original CylinderMesh; never replace a resource or
	# rerandomize to manufacture the desired probe class.
	for retained in _immutable_meshes:
		var mesh: Mesh = retained.mesh
		if not mesh is CylinderMesh or mesh.get_surface_count() != 1:
			continue
		var before_arrays: Array = mesh.surface_get_arrays(0)
		var old_count: int = mesh.get_surface_count()
		var original_height: float = mesh.height
		mesh.height = original_height + 0.001
		var after_arrays: Array = mesh.surface_get_arrays(0)
		var observed_vertices: PackedVector3Array = after_arrays[Mesh.ARRAY_VERTEX]
		var changed: bool = retained.node.mesh == mesh and mesh.get_surface_count() == old_count and mesh.height != original_height and var_to_bytes(after_arrays) != var_to_bytes(before_arrays)
		var detected: bool = not _refresh_managed_coverage()
		if detected:
			local_fault("mutation")
		var sticky: bool = _faulted and _coverage_invalid and not audit_frame() and not _coverage_qualified(_token, _doc_generation, _geometry_generation)
		return {"changed": changed, "detected": detected, "sticky": sticky, "surfaces": old_count, "vertices": observed_vertices.size(), "array_mesh": 0, "primitive_mesh": 1}
	return {}

func _writer_digest() -> String:
	var raw := "DEY-WRITERS-1\n".to_utf8_buffer()
	var relative: Array = []
	for path in SOURCE_FILES:
		relative.append(String(path).trim_prefix("res://"))
	relative.sort()
	for path in relative:
		raw.append_array(String(path).to_utf8_buffer())
		raw.append(0)
		raw.append_array(String(_source_pins["res://" + path]).hex_decode())
	return sha256(raw)

func _on_document_changed() -> void:
	if _freeze.is_empty():
		_editable_pending = true

func _on_edit_request(kind: String) -> void:
	if _edit_pending.is_empty():
		_edit_pending = kind

func _on_stop_request(source: String) -> void:
	_stop_pending = "human_escape" if source == "Esc" else "human_ui"

func local_fault(_code: String) -> void:
	if not _faulted:
		var fault_enum: int = 0
		match _code:
			"channel_fault": fault_enum = 1
			"instance_lost": fault_enum = 2
			"malformed": fault_enum = 3
			"mutation": fault_enum = 4
			"over_budget": fault_enum = 5
			"sequence": fault_enum = 6
			"source_mismatch": fault_enum = 7
			"startup_refused": fault_enum = 8
		_diag_timing_mark(21, fault_enum)
	local_fault_diag_core(_code)

func local_fault_diag_core(_code: String) -> void:
	_faulted = true
	_state = "INVALIDATED"
	_coverage_invalid = true
	_coverage_turn_valid = false
	_coverage_resources_turn = {}
	if not _coverage.is_empty():
		_coverage["valid"] = false
	# Keep lock, original references, partial frame and publication memory.
	# No reconnect/reapply/unlock or unsolicited new logical frame is attempted.

func _queue(kind: String, epoch: String, operation: String, body: Dictionary) -> bool:
	if _faulted or _outbox.size() >= 8:
		return false
	var message := {"type": kind, "run_id": _boot.run_id, "world_epoch": epoch,
		"operation_id": operation, "body": body}
	var raw := JSON.stringify(message).to_utf8_buffer()
	if raw.size() > PAYLOAD_MAX or (kind != "SNAPSHOT_CHUNK" and raw.size() > CONTROL_MAX):
		local_fault("over_budget")
		return false
	_outbox.append(raw)
	return true

func _frame(raw: PackedByteArray) -> PackedByteArray:
	var framed := MAGIC.to_ascii_buffer()
	framed.append(71)
	framed.append_array(_out_seq)
	framed.append_array(_be(raw.size(), 4))
	framed.append_array(raw)
	framed.append_array(_crypto.hmac_digest(HashingContext.HASH_SHA256, _key, framed))
	_out_seq = _increment_sequence(_out_seq)
	if _out_seq.is_empty():
		local_fault("sequence")
	return framed

func pump() -> void:
	_diag_timing_mark(1)
	pump_diag_core()
	_diag_timing_mark(2)
	if _initialized and _pose_revision == "0" and _tx.is_empty() and _outbox.is_empty() and not _faulted:
		_diag_timing_flush_once()

func pump_diag_core() -> void:
	if not _owned_startup_complete():
		return
	if _socket == null or _faulted:
		return
	if _socket.poll() != OK:
		local_fault("channel_fault")
		return
	var status := _socket.get_status()
	if status == StreamPeerTCP.STATUS_CONNECTING:
		return
	if status != StreamPeerTCP.STATUS_CONNECTED:
		local_fault("channel_fault")
		return
	if not _hello_sent:
		_hello_sent = true
		_state = "AUTHENTICATED"
		_queue("HELLO", "0", "hello", _hello())
	if not audit_frame():
		return
	var bytes_used := 0
	var frames_used := 0
	var available := _socket.get_available_bytes()
	if available > 0:
		var received: Array = _socket.get_partial_data(mini(available, IO_MAX))
		if received.size() != 2 or received[0] != OK or not received[1] is PackedByteArray or received[1].size() > mini(available, IO_MAX):
			local_fault("channel_fault")
			return
		_rx.append_array(received[1])
		bytes_used += received[1].size()
	if _rx.size() > (PAYLOAD_MAX + 53) * 2:
		local_fault("over_budget")
		return
	while frames_used < FRAMES_MAX and _rx.size() >= 21:
		if _rx.slice(0,8).get_string_from_ascii() != MAGIC or _rx[8] != 82 or _rx.slice(9,17) != _in_seq:
			local_fault("malformed")
			return
		var length := _u32(_rx, 17)
		if length < 2 or length > PAYLOAD_MAX:
			local_fault("over_budget")
			return
		if _rx.size() < 21 + length + 32:
			break
		var signed_raw := _rx.slice(0, 21 + length)
		var mac := _rx.slice(21 + length, 53 + length)
		if not _crypto.constant_time_compare(_crypto.hmac_digest(HashingContext.HASH_SHA256, _key, signed_raw), mac):
			local_fault("malformed")
			return
		var payload := _rx.slice(21, 21 + length)
		_rx = _rx.slice(53 + length)
		_in_seq = _increment_sequence(_in_seq)
		if _in_seq.is_empty():
			local_fault("sequence")
			return
		frames_used += 1
		_handle(payload)
		if _faulted or not audit_frame():
			return
	if _editable_pending and _freeze.is_empty():
		_editable_pending = false
		_send_editable("editable", "")
	if not _freeze.is_empty() and not _edit_pending.is_empty():
		_queue("EDIT_REQUEST", _freeze.world_epoch, "human-edit", {"freeze_id": _freeze.freeze_id,
			"request_kind": _edit_pending, "document_generation": str(_refs.document._owned_generation(self))})
		_edit_pending = ""
	if not _freeze.is_empty() and not _stop_pending.is_empty():
		_queue("STOP_NOTICE", _freeze.world_epoch, "human-stop", {"freeze_id": _freeze.freeze_id,
			"source": _stop_pending, "pose_revision": _pose_revision})
		_stop_pending = ""
	_feed_snapshot()
	if not _freeze.is_empty() and _snapshot_cursor == -1 and _outbox.is_empty() and _tx.is_empty():
		_queue("WORLD_STATUS", _freeze.world_epoch, "status-" + str(Engine.get_process_frames()),
			{"freeze_identity": _freeze.duplicate(true), "state": _state, "pose_revision": _pose_revision,
			"geometry_audit_digest": _static_digest, "engine_tick": str(Engine.get_process_frames())})
	while bytes_used < IO_MAX and frames_used < FRAMES_MAX:
		if _tx.is_empty():
			if _outbox.is_empty():
				break
			_tx = _frame(_outbox.pop_front())
			_tx_offset = 0
		var remaining := mini(IO_MAX - bytes_used, _tx.size() - _tx_offset)
		var sent: Array = _socket.put_partial_data(_tx.slice(_tx_offset, _tx_offset + remaining))
		if sent.size() != 2 or sent[0] != OK or not sent[1] is int or sent[1] < 0 or sent[1] > remaining:
			local_fault("channel_fault")
			return
		if sent[1] == 0:
			break
		_tx_offset += sent[1]
		bytes_used += sent[1]
		if _tx_offset == _tx.size():
			_diag_timing_mark(18, _tx.size())
			_tx = PackedByteArray()
			_tx_offset = 0
			frames_used += 1

func _hello() -> Dictionary:
	return {"launch_challenge": _boot.launch_challenge, "engine_pid": str(OS.get_process_id()),
		"engine_version": str(Engine.get_version_info().get("string", "unknown")),
		"engine_sha256": _boot.engine_sha256, "source_bundle_sha256": _boot.source_bundle_sha256,
		"scalar_width": _scalar_width, "main_instance_id": _object_id(_main),
		"document_instance_id": _object_id(_refs.document), "workspace_instance_id": _object_id(_refs.workspace),
		"drill_root_instance_id": _object_id(_refs.drill), "document_generation": str(_refs.document._owned_generation(self)),
		"geometry_generation": str(_main._owned_geometry_revision(self)), "raw_layout_sha256": _boot.raw_layout_sha256}

func _strict_json(raw: PackedByteArray) -> Dictionary:
	if raw.has(0):
		return {"ok": false, "value": null}
	_json_text = raw.get_string_from_utf8()
	_json_index = 0
	_json_error = _json_text.to_utf8_buffer() != raw
	var value = _json_value(0)
	_json_space()
	return {"ok": not _json_error and _json_index == _json_text.length(), "value": value}

func _json_space() -> void:
	while _json_index < _json_text.length() and " \t\r\n".contains(_json_text[_json_index]):
		_json_index += 1

func _json_value(depth: int):
	_json_space()
	if _json_error or depth > 32 or _json_index >= _json_text.length():
		_json_error = true
		return null
	var c := _json_text[_json_index]
	if c == "\"":
		return _json_string()
	if c == "{" or c == "[":
		var object := c == "{"
		var result = {} if object else []
		_json_index += 1
		_json_space()
		var end := "}" if object else "]"
		if _json_index < _json_text.length() and _json_text[_json_index] == end:
			_json_index += 1
			return result
		while not _json_error:
			_json_space()
			var key := ""
			if object:
				if _json_index >= _json_text.length() or _json_text[_json_index] != "\"":
					break
				key = _json_string()
				_json_space()
				if result.has(key) or _json_index >= _json_text.length() or _json_text[_json_index] != ":":
					break
				_json_index += 1
			var item = _json_value(depth + 1)
			if object:
				result[key] = item
			else:
				result.append(item)
			_json_space()
			if _json_index >= _json_text.length():
				break
			if _json_text[_json_index] == end:
				_json_index += 1
				return result
			if _json_text[_json_index] != ",":
				break
			_json_index += 1
		_json_error = true
		return null
	for literal in ["true", "false", "null"]:
		if _json_text.substr(_json_index, literal.length()) == literal:
			_json_index += literal.length()
			return true if literal == "true" else (false if literal == "false" else null)
	var start := _json_index
	while _json_index < _json_text.length() and "0123456789.eE+-".contains(_json_text[_json_index]):
		_json_index += 1
	var token := _json_text.substr(start, _json_index - start)
	var pattern := RegEx.new()
	pattern.compile("^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$")
	if token.is_empty() or token.length() > 2048 or pattern.search(token) == null:
		_json_error = true
		return null
	var parsed = JSON.parse_string(token)
	if not token.contains(".") and not token.to_lower().contains("e") and token.is_valid_int() and token.length() <= 18:
		parsed = token.to_int()
	if not (parsed is int or parsed is float) or not is_finite(float(parsed)):
		_json_error = true
	return parsed

func _json_string() -> String:
	_json_index += 1
	var result := ""
	while _json_index < _json_text.length():
		var c := _json_text[_json_index]
		_json_index += 1
		if c == "\"":
			return result
		if c.unicode_at(0) < 32:
			break
		if c != "\\":
			result += c
			continue
		if _json_index >= _json_text.length():
			break
		var escaped := _json_text[_json_index]
		_json_index += 1
		var map := {"\"":"\"", "\\":"\\", "/":"/", "b":"\b", "f":"\f", "n":"\n", "r":"\r", "t":"\t"}
		if map.has(escaped):
			result += map[escaped]
			continue
		if escaped != "u":
			break
		var code := _json_hex4()
		if code <= 0:
			break
		if code >= 0xd800 and code <= 0xdbff:
			if _json_text.substr(_json_index, 2) != "\\u":
				break
			_json_index += 2
			var low := _json_hex4()
			if low < 0xdc00 or low > 0xdfff:
				break
			code = 0x10000 + (code - 0xd800) * 1024 + low - 0xdc00
		elif code >= 0xdc00 and code <= 0xdfff:
			break
		result += String.chr(code)
	_json_error = true
	return ""

func _json_hex4() -> int:
	if _json_index + 4 > _json_text.length():
		return -1
	var text := _json_text.substr(_json_index, 4).to_lower()
	for c in text:
		if not "0123456789abcdef".contains(c):
			return -1
	_json_index += 4
	return text.hex_to_int()

func _real(value: float) -> String:
	var buffer := StreamPeerBuffer.new()
	buffer.big_endian = true
	if _scalar_width == 32:
		buffer.put_float(value)
	else:
		buffer.put_double(value)
	return buffer.data_array.hex_encode()

func _f64(value: float) -> String:
	var buffer := StreamPeerBuffer.new()
	buffer.big_endian = true
	buffer.put_double(value)
	return buffer.data_array.hex_encode()

func _decode_f64(value) -> float:
	if not _hex(value, 16):
		return NAN
	var buffer := StreamPeerBuffer.new()
	buffer.big_endian = true
	buffer.data_array = String(value).hex_decode()
	return buffer.get_double()

func _vector(value: Vector3) -> Array:
	return [_real(value.x), _real(value.y), _real(value.z)]

func _transform(value: Transform3D) -> Dictionary:
	return {"basis_columns": [_vector(value.basis.x), _vector(value.basis.y), _vector(value.basis.z)],
		"origin": _vector(value.origin)}

func _f64_vector(value: Vector3) -> Array:
	return [_f64(value.x), _f64(value.y), _f64(value.z)]

func _decode_transform(record) -> Dictionary:
	if not _exact(record, ["basis_columns","origin"]) or not record.basis_columns is Array or record.basis_columns.size() != 3 or not record.origin is Array or record.origin.size() != 3:
		return {"ok": false}
	var rows: Array = record.basis_columns.duplicate(true)
	rows.append(record.origin)
	var vectors: Array[Vector3] = []
	for row in rows:
		if not row is Array or row.size() != 3:
			return {"ok": false}
		var numbers: Array = []
		for field in row:
			var number := _decode_f64(field)
			if not is_finite(number):
				return {"ok": false}
			numbers.append(number)
		var vector := Vector3(numbers[0], numbers[1], numbers[2])
		if not vector.is_finite():
			return {"ok": false}
		vectors.append(vector)
	var value := Transform3D(Basis(vectors[0], vectors[1], vectors[2]), vectors[3])
	return {"ok": value.is_finite() and value.basis.determinant() != 0.0, "value": value}

func _tree_bytes(value) -> PackedByteArray:
	var raw := PackedByteArray()
	match typeof(value):
		TYPE_NIL:
			raw.append(0)
		TYPE_BOOL:
			raw.append(2 if value else 1)
		TYPE_STRING:
			var text: PackedByteArray = value.to_utf8_buffer()
			raw.append(3)
			raw.append_array(_be(text.size(), 8))
			raw.append_array(text)
		TYPE_INT:
			raw.append(4)
			raw.append_array(_be(value, 8))
		TYPE_ARRAY:
			raw.append(5)
			raw.append_array(_be(value.size(), 8))
			for item in value:
				raw.append_array(_tree_bytes(item))
		TYPE_DICTIONARY:
			var keys: Array = value.keys()
			keys.sort()
			raw.append(6)
			raw.append_array(_be(keys.size(), 8))
			for key in keys:
				raw.append_array(_tree_bytes(String(key)))
				raw.append_array(_tree_bytes(value[key]))
		_:
			_capture_error = "malformed"
	return raw

func _fixed_catalog() -> Array:
	var catalog: Array = []
	for kind in ["water","hard_rock","fault","void","casing"]:
		catalog.append({"kind": kind, "part_ids": ["Visual/SolidMesh#surface0",
			"Collision/EnvelopeCylinder" if kind == "casing" else "Collision/EnvelopeBox"]})
	var parts: Array = []
	for part in ["Collar","Joint","BodyMatrix","HeadPDC"]:
		parts.append("Visual/" + part + "#surface0")
	for blade in 6:
		parts.append("Visual/Blade" + str(blade) + "#surface0")
		for stud in 3:
			parts.append("Visual/CutterStud_" + str(blade) + "_" + str(stud) + "#surface0")
	parts.append("Collision/EnvelopeCapsule")
	catalog.append({"kind": "drill", "part_ids": parts})
	return catalog

func _catalog_parts(kind: String) -> Array:
	for row in _catalog:
		if row.kind == kind:
			return row.part_ids.duplicate()
	return []

func _raw_document() -> PackedByteArray:
	return _refs.document._owned_raw_layout(self)

func _normalized() -> Dictionary:
	var objects: Array = []
	for obstacle in _refs.document.obstacles:
		objects.append({"object_id": str(obstacle.object_id), "kind": String(obstacle.kind),
			"priority": str(obstacle.priority), "position_bits": _vector(obstacle.position),
			"rotation_deg_bits": _vector(obstacle.rotation_deg), "size_bits": _vector(obstacle.size)})
	var gates: Array = []
	for which in ["entry","exit"]:
		var gate: Dictionary = _refs.document.gates[which]
		gates.append({"face": String(gate.face), "u_bits": _f64(float(gate.u)), "v_bits": _f64(float(gate.v))})
	return {"scalar_width": _scalar_width, "objects": objects, "gates": gates}

func _walk(node: Node, result: Array) -> void:
	if result.size() >= NODE_MAX or not is_instance_valid(node):
		_capture_error = "over_budget"
		return
	result.append(node)
	for child in node.get_children():
		_walk(child, result)

func _role(node: Node) -> String:
	if node == _main:
		return "ancestor"
	if node == _refs.workspace:
		return "workspace"
	if node == _refs.drill:
		return "drill_pose"
	if node == _refs.selection or node == _refs.camera or node is Light3D or node is Label3D or not node is Node3D:
		return "observer"
	if _refs.ticks == node or _refs.ticks.is_ancestor_of(node):
		return "observer"
	return "geometry"

func _flags(node: Node) -> Dictionary:
	var script = node.get_script()
	var script_sha = null
	var guarded: bool = _coverage_turn_valid and not _coverage_invalid and not _coverage.is_empty() and _coverage.get("valid", false) and _coverage.members.has(node)
	if script != null:
		var path := String(script.resource_path)
		if (node == _main and path == "res://viewer/main.gd") or (node == _refs.shell and path == "res://ui/shell.gd"):
			script_sha = _source_pins[path]
		else:
			_capture_error = "source_mismatch"
	var role := _role(node)
	var animation := node is AnimationPlayer or node is AnimationTree or node is Skeleton3D or node is GPUParticles3D or node is CPUParticles3D
	var physics := node.is_physics_processing() or node.is_physics_processing_internal()
	if node is CollisionObject3D:
		physics = physics or node.collision_layer != 0 or node.collision_mask != 0
	if node is CollisionShape3D:
		physics = physics or not node.disabled
	if role != "observer" and not ["Node3D","MeshInstance3D","StaticBody3D","CollisionShape3D","Marker3D"].has(node.get_class()):
		_capture_error = "source_mismatch"
	if animation or (role != "observer" and physics):
		_capture_error = "mutation"
	return {"script_sha256": script_sha, "processing": node.is_processing() or node.is_processing_internal(),
		"top_level": node.top_level if node is Node3D else false,
		"disable_scale": node.is_scale_disabled() if node is Node3D else false,
		"unguarded_geometry_writer": script != null and not guarded and role != "observer",
		"physics_active": physics, "geometry_write_guarded": guarded, "animation_active": animation}

func _node_record(node: Node) -> Dictionary:
	var role := _role(node)
	var local = _transform(node.transform) if node is Node3D else null
	var global_value = _transform(node.global_transform) if node is Node3D else null
	if node is Node3D and (not node.transform.is_finite() or not node.global_transform.is_finite()):
		_capture_error = "malformed"
	if role != "observer" and node != _main and not node.get_parent() is Node3D:
		_capture_error = "source_mismatch"
	return {"node_id": _object_id(node), "parent_id": null if node == _main else _object_id(node.get_parent()),
		"role": role, "path": String(_main.get_path_to(node)), "class_name": node.get_class(),
		"local": local, "global_transform": global_value, "flags": _flags(node)}

func _analytic(node: CollisionShape3D, part_id: String) -> Dictionary:
	if not node.disabled or node.shape == null:
		_capture_error = "mutation"
		return {}
	var shape: Shape3D = node.shape
	if shape.get_script() != null:
		_capture_error = "source_mismatch"
		return {}
	if not is_finite(float(shape.margin)) or shape.margin < 0.0:
		_capture_error = "malformed"
		return {}
	var kind := ""
	var dimensions: Array = []
	# Boxes/ellipsoids carry native XYZ half extents (axis field unused=0).
	# Godot CylinderShape3D and CapsuleShape3D have native local-Y axis=1.
	var axis := 0
	if shape is BoxShape3D:
		kind = "box"
		dimensions = _f64_vector(shape.size * 0.5)
	elif shape is SphereShape3D:
		kind = "ellipsoid"
		dimensions = [_f64(shape.radius), _f64(shape.radius), _f64(shape.radius)]
	elif shape is CylinderShape3D:
		kind = "cylinder"
		axis = 1
		dimensions = [_f64(shape.radius), _f64(shape.radius), _f64(shape.height * 0.5)]
	elif shape is CapsuleShape3D:
		kind = "capsule"
		axis = 1
		dimensions = [_f64(maxf(0.0, shape.height * 0.5 - shape.radius)), _f64(shape.radius), _f64(0.0)]
	else:
		_capture_error = "source_mismatch"
		return {}
	var descriptor := "DEY-ANALYTIC-1".to_ascii_buffer()
	descriptor.append({"box":1,"ellipsoid":2,"cylinder":3,"capsule":4}[kind])
	descriptor.append(axis)
	descriptor.append(1 if node.disabled else 0)
	for dimension in dimensions:
		descriptor.append_array(String(dimension).hex_decode())
	descriptor.append_array(_f64(float(shape.margin)).hex_decode())
	return {"part_id": part_id, "node_id": _object_id(node), "kind": kind,
		"global_transform": _transform(node.global_transform), "dimensions": dimensions,
		"axis": str(axis), "vertices": [], "indices": [], "geometry_sha256": sha256(descriptor),
		"shape_disabled": node.disabled, "shape_margin_bits": _f64(float(shape.margin))}

func _mesh_surface(node: MeshInstance3D, surface: int, part_id: String, unique: Dictionary) -> Dictionary:
	var mesh: Mesh = node.mesh
	if mesh == null or mesh.get_script() != null or node.get_blend_shape_count() != 0 or node.skin != null:
		_capture_error = "source_mismatch"
		return {}
	if mesh is ArrayMesh:
		if mesh.surface_get_primitive_type(surface) != Mesh.PRIMITIVE_TRIANGLES:
			_capture_error = "source_mismatch"
			return {}
	elif not (mesh is BoxMesh or mesh is CylinderMesh or mesh is TorusMesh) or surface != 0:
		# These fixed source primitives have the documented triangle surface.
		# Unknown Resource subclasses/custom mesh writers refuse the whole freeze.
		_capture_error = "source_mismatch"
		return {}
	var arrays: Array = mesh.surface_get_arrays(surface)
	if arrays.size() != Mesh.ARRAY_MAX or not arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array:
		_capture_error = "malformed"
		return {}
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var native_indices = arrays[Mesh.ARRAY_INDEX]
	var indices: Array = []
	if native_indices == null or native_indices.size() == 0:
		for index in vertices.size():
			indices.append(index)
	else:
		if not native_indices is PackedInt32Array:
			_capture_error = "malformed"
			return {}
		for index in native_indices:
			indices.append(index)
	if vertices.is_empty() or indices.is_empty() or indices.size() % 3 != 0 or vertices.size() > VERTEX_MAX or indices.size() > INDEX_MAX:
		_capture_error = "over_budget"
		return {}
	var payload := "DEY-MESH-1".to_ascii_buffer()
	payload.append(_scalar_width)
	payload.append_array(_be(vertices.size(),4))
	payload.append_array(_be(indices.size(),4))
	var encoded_vertices: Array = []
	for vertex in vertices:
		if not vertex.is_finite():
			_capture_error = "malformed"
			return {}
		var row := _vector(vertex)
		encoded_vertices.append(row)
		for coordinate in row:
			payload.append_array(String(coordinate).hex_decode())
	var encoded_indices: Array = []
	for index in indices:
		if index < 0 or index >= vertices.size():
			_capture_error = "malformed"
			return {}
		encoded_indices.append(str(index))
		payload.append_array(_be(index,4))
	var geometry_sha := sha256(payload)
	var node_id := _object_id(node)
	if not _mesh_payloads.has(node_id):
		_mesh_payloads[node_id] = []
	_mesh_payloads[node_id].append(geometry_sha)
	if not unique.has(geometry_sha):
		unique[geometry_sha] = {"vertices": vertices.size(), "indices": indices.size()}
	return {"part_id": part_id, "node_id": _object_id(node), "kind": "mesh",
		"global_transform": _transform(node.global_transform), "dimensions": [], "axis": "0",
		"vertices": encoded_vertices, "indices": encoded_indices, "geometry_sha256": geometry_sha,
		"shape_disabled": null, "shape_margin_bits": null}

func _parts(root: Node3D, unique: Dictionary, covered: Dictionary) -> Array:
	var nodes: Array = []
	_walk(root, nodes)
	var parts: Array = []
	for node in nodes:
		if node is MeshInstance3D:
			if node.mesh == null or node.mesh.get_surface_count() == 0:
				_capture_error = "source_mismatch"
				continue
			for surface in node.mesh.get_surface_count():
				parts.append(_mesh_surface(node, surface, String(root.get_path_to(node)) + "#surface" + str(surface), unique))
			covered[node.get_instance_id()] = true
		elif node is CollisionShape3D:
			parts.append(_analytic(node, String(root.get_path_to(node))))
			covered[node.get_instance_id()] = true
		elif node is CollisionPolygon3D:
			_capture_error = "source_mismatch"
	return parts

func _capture_snapshot() -> Dictionary:
	_capture_error = ""
	if not _refresh_managed_coverage():
		_capture_error = "mutation"
		return {}
	var normalized := _normalized()
	var raw := _raw_document()
	if raw.is_empty() or raw.size() > 1048576 or normalized.objects.size() > 30:
		_capture_error = "over_budget"
		return {}
	var nodes: Array = []
	_walk(_main, nodes)
	var node_records: Array = []
	_required = []
	_immutable_meshes = []
	_immutable_shapes = []
	_mesh_payloads = {}
	var required_ids: Array = []
	for node in nodes:
		var record := _node_record(node)
		node_records.append(record)
		if record.role != "observer":
			_required.append({"node": node, "parent": node.get_parent(), "role": record.role})
			required_ids.append(record.node_id)
		if node is MeshInstance3D:
			_immutable_meshes.append({"node": node, "mesh": node.mesh, "surfaces": node.mesh.get_surface_count() if node.mesh != null else 0})
		if node is CollisionShape3D:
			_immutable_shapes.append({"node": node, "shape": node.shape})
	var manifest: Array = []
	for obstacle in _refs.document.obstacles:
		var expected := _catalog_parts(String(obstacle.kind))
		if expected.is_empty():
			_capture_error = "source_mismatch"
		manifest.append({"object_id": str(obstacle.object_id), "kind": String(obstacle.kind), "priority": str(obstacle.priority), "part_ids": expected})
	var unique: Dictionary = {}
	var covered: Dictionary = {}
	var objects: Array = []
	for obstacle in _refs.document.obstacles:
		var asset: Node3D = _refs.presenter.obstacle_node(int(obstacle.object_id))
		if asset == null:
			_capture_error = "instance_lost"
			return {}
		var rotation := Basis.from_euler(obstacle.rotation_deg * (PI / 180.0)).get_rotation_quaternion()
		objects.append({"object_id": str(obstacle.object_id), "root_node_id": _object_id(asset),
			"root_affine": _transform(asset.global_transform), "proposed_quaternion": [_f64(rotation.x),_f64(rotation.y),_f64(rotation.z),_f64(rotation.w)],
			"parts": _parts(asset, unique, covered)})
	var drill_asset: Node3D = _refs.drill.get_node_or_null("DrillPDC")
	if drill_asset == null or _refs.presenter.report().get("state") != "ready":
		_capture_error = "source_mismatch"
		return {}
	var drill_parts := _parts(drill_asset, unique, covered)
	var presentation: Array = []
	for node in nodes:
		if covered.has(node.get_instance_id()):
			continue
		if node is MeshInstance3D:
			if node.mesh == null:
				_capture_error = "source_mismatch"
				continue
			for surface in node.mesh.get_surface_count():
				presentation.append(_mesh_surface(node, surface, String(_main.get_path_to(node)) + "#surface" + str(surface), unique))
		elif node is CollisionShape3D:
			presentation.append(_analytic(node, String(_main.get_path_to(node))))
		elif node is CollisionPolygon3D:
			_capture_error = "source_mismatch"
	var vertices := 0
	var indices := 0
	for info in unique.values():
		vertices += info.vertices
		indices += info.indices
	if unique.size() > SURFACE_MAX or vertices > VERTEX_MAX or indices > INDEX_MAX:
		_capture_error = "over_budget"
	_snapshot_counts = {"nodes": str(nodes.size()), "objects": str(objects.size()), "surfaces": str(unique.size()),
		"unique_vertices": str(vertices), "indices": str(indices), "required_geometry_nodes": str(required_ids.size()),
		"observer_nodes": str(nodes.size() - required_ids.size())}
	var canonical: PackedByteArray = _refs.document._canon(_refs.document._layout_dict()).to_utf8_buffer()
	var snapshot := {"canonical_companion": {"raw_layout_bytes_base64": Marshalls.raw_to_base64(raw),
		"raw_sha256": sha256(raw), "normalized_value_bits": normalized,
		"canonical_utf8_base64": Marshalls.raw_to_base64(canonical), "legacy_layout_sha256": sha256(canonical),
		"document_source_sha256": _source_pins["res://editor/scene_document.gd"], "canonical_source_sha256": _source_pins["res://editor/layout_codec.gd"]},
		"inventory_counts": _snapshot_counts, "independent_object_manifest": manifest, "nodes": node_records,
		"assets": {"catalog_source_sha256": _catalog_sha, "catalog": _catalog, "objects": objects, "presentation_parts": presentation},
		"workspace": {"units": "m", "transform": _transform(_refs.workspace.global_transform), "gates": normalized.gates},
		"drill": {"root_node_id": _object_id(_refs.drill), "root_affine": _transform(_refs.drill.global_transform),
			"part_ids": _catalog_parts("drill"), "parts": drill_parts},
		"immutability_audit": {"writer_inventory_sha256": _writer_sha, "document_generation": str(_doc_generation),
			"geometry_generation": str(_geometry_generation), "required_node_ids": required_ids}}
	var immutable := "DEY-IMMUTABLE-1".to_ascii_buffer()
	immutable.append_array(_tree_bytes(snapshot))
	_freeze.immutable_payload_sha256 = sha256(immutable)
	_static_digest = _static_state_digest()
	_freeze.geometry_state_sha256 = _static_digest
	snapshot["freeze_identity"] = _freeze.duplicate(true)
	_coverage_turn_valid = false
	_coverage_resources_turn = {}
	return snapshot

func _owned_startup_complete() -> bool:
	# Acquisition only: TCP/HELLO, freeze and numerical readiness remain separate.
	return _owned_startup_state == OwnedStartup.STARTED

func _owned_startup_failure() -> Dictionary:
	if not _owned_first_failure.is_empty():
		return _owned_first_failure.duplicate()
	if _owned_startup_state == OwnedStartup.STARTING:
		return {"stage":"bridge", "code":"startup_incomplete", "variant_type":0, "slot_code":0}
	return {"stage":"", "code":"", "variant_type":0, "slot_code":0}

func _owned_startup_fail(code: String) -> bool:
	if _owned_first_failure.is_empty():
		var codes := ["references_refused", "main_incomplete", "participant_bind_refused", "bootstrap_refused", "scalar_refused", "source_profile_refused", "socket_refused", "acquisition_refused"]
		_owned_first_failure = {"stage":"bridge", "code":code if codes.has(code) else "acquisition_refused", "variant_type":0, "slot_code":0}
	_owned_startup_state = OwnedStartup.FAILED
	local_fault("startup_refused")
	return false

func _owned_prepared_references() -> bool:
	if _owned_startup_state != OwnedStartup.STARTING and _owned_startup_state != OwnedStartup.STARTED:
		return false
	if not is_instance_valid(_main) or not _main.is_inside_tree():
		return false
	for key in ["main","document","workspace","drill","presenter","camera","shell","obstacles","gates","selection","ticks","native_root"]:
		if not _refs.has(key) or not is_instance_valid(_refs[key]):
			return false
	if not _refs.native_root is Node or not _refs.document is RefCounted or not _refs.presenter is RefCounted:
		return false
	if _refs.main != _main or _main.get_parent() != _refs.native_root or _main.get_tree().root != _refs.native_root:
		return false
	var current: Dictionary = _main._owned_world_references(self)
	for key in ["main","document","workspace","drill","presenter","camera","shell","obstacles","gates","selection","ticks"]:
		if not current.has(key) or not is_instance_valid(current[key]) or current[key] != _refs[key]:
			return false
	for key in ["workspace","camera","shell"]:
		if not _refs[key] is Node or _refs[key].get_parent() != _main:
			return false
	for key in ["drill","obstacles","gates","selection","ticks"]:
		if not _refs[key] is Node or _refs[key].get_parent() != _refs.workspace:
			return false
	return true

func _original_references() -> bool:
	return _owned_startup_complete() and _owned_prepared_references()

func _shape_identity(node: CollisionShape3D) -> Dictionary:
	var part := _analytic(node, "audit")
	if part.is_empty():
		return {}
	return {"resource_id": _object_id(node.shape), "kind": part.kind,
		"dimensions": part.dimensions, "axis": part.axis, "geometry_sha256": part.geometry_sha256}

func _static_native_tree(value, depth: int = 0) -> Dictionary:
	if depth > 32:
		_capture_error = "malformed"
		return {"ok": false}
	match typeof(value):
		TYPE_NIL:
			return {"ok": true, "value": [0]}
		TYPE_BOOL:
			return {"ok": true, "value": [2 if value else 1]}
		TYPE_STRING:
			return {"ok": true, "value": [3, value]}
		TYPE_INT:
			return {"ok": true, "value": [4, value]}
		TYPE_ARRAY:
			var children: Array = []
			for item in value:
				var encoded: Dictionary = _static_native_tree(item, depth + 1)
				if not encoded.get("ok", false):
					_capture_error = "malformed"
					return {"ok": false}
				children.append(encoded.value)
			return {"ok": true, "value": [5, children]}
		TYPE_DICTIONARY:
			var keys: Array = value.keys()
			for key in keys:
				if typeof(key) != TYPE_STRING:
					_capture_error = "malformed"
					return {"ok": false}
			keys.sort()
			var pairs: Array = []
			for key in keys:
				var encoded: Dictionary = _static_native_tree(value[key], depth + 1)
				if not encoded.get("ok", false):
					_capture_error = "malformed"
					return {"ok": false}
				pairs.append([key, encoded.value])
			return {"ok": true, "value": [6, pairs]}
		_:
			_capture_error = "malformed"
			return {"ok": false}

func _static_native_digest(value) -> String:
	var canonical: Dictionary = _static_native_tree(value)
	if not canonical.get("ok", false):
		return ""
	var serialized: PackedByteArray = var_to_bytes(canonical.value)
	if serialized.is_empty():
		_capture_error = "malformed"
		return ""
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK:
		_capture_error = "malformed"
		return ""
	if context.update("DEEYE_STATIC_STATE_NATIVE_V2\n".to_ascii_buffer()) != OK or context.update(serialized) != OK:
		_capture_error = "malformed"
		return ""
	var digest: PackedByteArray = context.finish()
	if digest.size() != 32:
		_capture_error = "malformed"
		return ""
	return digest.hex_encode()

func _static_state_digest() -> String:
	_diag_timing_mark(13)
	var result: String = _static_state_digest_diag_core()
	_diag_timing_mark(14)
	return result

func _static_state_digest_diag_core() -> String:
	var rows: Array = []
	for retained in _required:
		var node: Node = retained.node
		if not is_instance_valid(node) or node.get_parent() != retained.parent:
			_capture_error = "instance_lost"
			return ""
		var row := {"node_id": _object_id(node), "parent_id": _object_id(node.get_parent()),
			"class": node.get_class(), "path": String(_main.get_path_to(node)), "flags": _flags(node)}
		if node != _refs.drill:
			row["local"] = _transform(node.transform)
			# Descendants move globally only because their original drill parent moves.
			if not _refs.drill.is_ancestor_of(node):
				row["global"] = _transform(node.global_transform)
		if node is CollisionShape3D:
			row["shape"] = _shape_identity(node)
		rows.append(row)
	var resources: Array = []
	for retained in _immutable_meshes:
		var node: MeshInstance3D = retained.node
		if not is_instance_valid(node) or node.mesh != retained.mesh or node.mesh == null or node.mesh.get_surface_count() != retained.surfaces:
			_capture_error = "mutation"
			return ""
		resources.append({"node_id": _object_id(node), "mesh_id": _object_id(node.mesh), "surface_count": str(retained.surfaces)})
		# Fresh original resource bytes, including surfaces and material/shape
		# storage: a same-instance/same-surface-count mutation cannot reuse cache.
		# The table was recomputed from original resources once in this same
		# synchronous refresh; never reuse it across audit/capture turns.
		var fresh: String = _coverage_resources_turn.get(node.mesh, "")
		if fresh.is_empty():
			_capture_error = "mutation"
			return ""
		resources[-1]["fresh_resource_sha256"] = fresh
	var shape_resources: Array = []
	for retained in _immutable_shapes:
		var node: CollisionShape3D = retained.node
		if not is_instance_valid(node) or node.shape != retained.shape:
			_capture_error = "mutation"
			return ""
		shape_resources.append({"node_id": _object_id(node), "descriptor": _shape_identity(node)})
	var current_nodes: Array = []
	_walk(_main, current_nodes)
	var required_now: Array = []
	var meshes_now: Array = []
	var shapes_now: Array = []
	for node in current_nodes:
		if _role(node) != "observer":
			required_now.append(_object_id(node))
		_flags(node)
		if node is MeshInstance3D:
			meshes_now.append(_object_id(node))
		if node is CollisionShape3D:
			shapes_now.append(_object_id(node))
	var expected_ids: Array = []
	for retained in _required:
		expected_ids.append(_object_id(retained.node))
	if required_now != expected_ids:
		_capture_error = "mutation"
		return ""
	var mesh_ids: Array = []
	var shape_ids: Array = []
	for retained in _immutable_meshes:
		mesh_ids.append(_object_id(retained.node))
	for retained in _immutable_shapes:
		shape_ids.append(_object_id(retained.node))
	if meshes_now != mesh_ids or shapes_now != shape_ids:
		_capture_error = "mutation"
		return ""
	return _static_native_digest({"nodes": rows, "mesh_resources": resources, "shape_resources": shape_resources,
		"document": _normalized(), "document_generation": str(_refs.document._owned_generation(self)),
		"geometry_generation": str(_main._owned_geometry_revision(self))})

func audit_frame() -> bool:
	_diag_timing_mark(3, int(_audit_busy), int(_freeze.is_empty()))
	var result: bool = audit_frame_diag_core()
	_diag_timing_mark(4)
	return result

func audit_frame_diag_core() -> bool:
	if not _owned_startup_complete():
		return false
	if _faulted:
		return false
	if not _original_references():
		local_fault("instance_lost")
		return false
	if _freeze.is_empty() or _audit_busy:
		return true
	_audit_busy = true
	_capture_error = ""
	var valid: bool = _refresh_managed_coverage() and _refs.document._owned_is_locked(self, _token)
	valid = valid and _refs.document._owned_generation(self) == _doc_generation and _main._owned_geometry_revision(self) == _geometry_generation
	valid = valid and _static_state_digest() == _static_digest and _capture_error.is_empty()
	if valid and _publication.get("state", "") != "APPLYING":
		var pose: Dictionary = _main._owned_drill_readback(self, _token)
		valid = not pose.is_empty() and pose.node == _refs.drill and pose.pose_revision == _pose_revision
		valid = valid and _transform(pose.local) == _transform(_pose_local) and _transform(pose.global) == _transform(_pose_global)
	_audit_busy = false
	_coverage_turn_valid = false
	_coverage_resources_turn = {}
	if not valid:
		local_fault("mutation")
	return valid

func _refuse(operation: String, code: String) -> void:
	_queue("REFUSAL", "0" if _freeze.is_empty() else _freeze.world_epoch, operation,
		{"refused_operation_id": operation, "code": code, "owner_state": _state})

func _handle(raw: PackedByteArray) -> void:
	var parsed := _strict_json(raw)
	if raw.size() > CONTROL_MAX or not parsed.ok or not _exact(parsed.value, ["type","run_id","world_epoch","operation_id","body"]):
		local_fault("malformed")
		return
	var message: Dictionary = parsed.value
	if message.run_id != _boot.run_id or not _u64(message.world_epoch) or not _label(message.operation_id) or not message.type is String or not message.body is Dictionary:
		local_fault("malformed")
		return
	var bodies := {
		"FREEZE_REQUEST": ["expected_document_generation","expected_raw_sha256","snapshot_limits_sha256","model_policy_sha256"],
		"INITIAL_VIEW": ["freeze_id","geometry_identity","pose_revision","desired_pose","desired_transform"],
		"PUBLISH_VIEW": ["freeze_id","geometry_identity","expected_previous_revision","pose_revision","desired_pose","desired_transform","numerical_receipt_digest"],
		"QUERY_VIEW": ["freeze_id","publication_operation_id","payload_digest","expected_pose_revision"],
		"UI_STATUS": ["freeze_id","status_base64"],
		"STOP": ["freeze_id","reason_code","expected_pose_revision"],
		"UNLOCK_FOR_EDIT": ["retired_freeze_id","retired_epoch","expected_pose_revision","retirement_record_digest"]}
	if not bodies.has(message.type) or not _exact(message.body, bodies[message.type]):
		if message.type == "UI_STATUS":
			local_fault("malformed")
		else:
			_refuse(message.operation_id, "malformed")
		return
	if _seen_operations.has(message.operation_id) or _seen_operations.size() >= 8192:
		if message.type == "UI_STATUS":
			local_fault("malformed")
		else:
			_refuse(message.operation_id, "duplicate_publish")
		return
	_seen_operations[message.operation_id] = true
	if message.type == "FREEZE_REQUEST":
		_begin_freeze(message)
		return
	if _freeze.is_empty() or message.world_epoch != _freeze.world_epoch:
		if message.type == "UI_STATUS":
			local_fault("malformed")
		else:
			_refuse(message.operation_id, "stale_epoch")
		return
	if not audit_frame():
		return
	match message.type:
		"UI_STATUS":
			_ui_status(message)
		"INITIAL_VIEW", "PUBLISH_VIEW":
			_publish(message, raw)
		"QUERY_VIEW":
			_query(message)
		"STOP":
			_stop(message)
		"UNLOCK_FOR_EDIT":
			_unlock(message)

func _ui_status(message: Dictionary) -> void:
	# The original authenticated run/sequence/operation/epoch/audit gates ran.
	# This record can only update the already-owned fixed display controls.
	var body: Dictionary = message.body
	if not _label(body.freeze_id) or body.freeze_id != _freeze.freeze_id or not body.status_base64 is String or body.status_base64.length() > 10924:
		local_fault("malformed")
		return
	var encoded: String = body.status_base64
	var raw := Marshalls.base64_to_raw(encoded)
	if raw.size() < 1 or raw.size() > UI_STATUS_MAX or Marshalls.raw_to_base64(raw) != encoded:
		local_fault("malformed")
		return
	var parsed := _strict_json(raw)
	if not parsed.ok or not _exact(parsed.value, ["connection","coordinator_ready","stages","data"]):
		local_fault("malformed")
		return
	var status: Dictionary = parsed.value
	if not status.connection is String or not ["disconnected","pending","connected","failed"].has(status.connection) or typeof(status.coordinator_ready) != TYPE_BOOL or not _exact(status.stages, ["sensor","board_compression","upload_decode","ai_decision","board_readback","motion"]) or not status.data is Dictionary:
		local_fault("malformed")
		return
	for stage in status.stages.values():
		if not stage is String or not ["pending","observed","failed","disconnected"].has(stage):
			local_fault("malformed")
			return
	var data_keys := ["raw","encoded","decoded","source_time","reconstruction_error","compression_ratio","quality_note","board","build","latency","codec_mode","e0_match"]
	for key in status.data:
		var value: Variant = status.data[key]
		if not data_keys.has(key) or not [TYPE_NIL,TYPE_BOOL,TYPE_INT,TYPE_FLOAT,TYPE_STRING].has(typeof(value)):
			local_fault("malformed")
			return
		if typeof(value) == TYPE_FLOAT and not is_finite(value):
			local_fault("malformed")
			return
		if typeof(value) == TYPE_STRING:
			if value.length() > 160:
				local_fault("malformed")
				return
			for index in range(value.length()):
				if value.unicode_at(index) < 32:
					local_fault("malformed")
					return
	status["coordinator_ready"] = false
	var applied: bool = _main.present_demo30h_status(status)
	if _ui_status_display_records >= 32:
		return
	_ui_status_display_records += 1
	var labels: Dictionary = _refs.shell._demo_data_labels
	var display := {"schema": 1, "operation_id": message.operation_id,
		"status_sha256": sha256(raw), "applied": applied,
		"connection_label": _ui_status_display_label(_refs.shell._demo_connection),
		"raw_label": _ui_status_display_label(labels.get("raw")),
		"decoded_label": _ui_status_display_label(labels.get("decoded")),
		"reconstruction_label": _ui_status_display_label(labels.get("reconstruction_error"))}
	var record := JSON.stringify(display)
	if record.to_utf8_buffer().size() <= 8192:
		print("DEEPEYE_UI_STATUS_DISPLAY " + record)

func _ui_status_display_label(value: Variant) -> Variant:
	if not value is Label or not is_instance_valid(value):
		return null
	var label: Label = value
	return label.text.substr(0, 200)

func _begin_freeze(message: Dictionary) -> void:
	var body: Dictionary = message.body
	var epoch: String = message.world_epoch
	var epoch_new := epoch != "0" and (epoch.length() > _last_epoch.length() or (epoch.length() == _last_epoch.length() and epoch > _last_epoch))
	var raw := _raw_document()
	if not _freeze.is_empty() or _token != null or not epoch_new or not _u64(body.expected_document_generation) or body.expected_document_generation != str(_refs.document._owned_generation(self)):
		_refuse(message.operation_id, "stale_epoch")
		return
	for field in ["expected_raw_sha256","snapshot_limits_sha256","model_policy_sha256"]:
		if not _hex(body[field],64):
			_refuse(message.operation_id, "malformed")
			return
	if sha256(raw) != body.expected_raw_sha256:
		_refuse(message.operation_id, "source_mismatch")
		return
	var idle: Dictionary = _refs.shell._owned_freeze_ready(_main, _refs.document)
	if not idle.get("ok", false):
		_refuse(message.operation_id, "mutation")
		return
	_token = RefCounted.new()
	if not _main._owned_drain_and_lock(self, _token):
		if _main._owned_geometry_token == _token:
			local_fault("mutation")
		else:
			_token = null
			_refuse(message.operation_id, "mutation")
		return
	_doc_generation = _refs.document._owned_generation(self)
	_geometry_generation = _main._owned_geometry_revision(self)
	# No yield occurs between generation/raw validation, lock and full capture.
	if body.expected_document_generation != str(_doc_generation) or sha256(_raw_document()) != body.expected_raw_sha256:
		local_fault("mutation")
		return
	_freeze = {"freeze_id": _crypto.generate_random_bytes(24).hex_encode(), "world_epoch": epoch,
		"document_generation": str(_doc_generation), "geometry_generation": str(_geometry_generation),
		"main_instance_id": _object_id(_main), "document_instance_id": _object_id(_refs.document),
		"workspace_instance_id": _object_id(_refs.workspace), "drill_root_instance_id": _object_id(_refs.drill),
		"source_bundle_sha256": _boot.source_bundle_sha256, "immutable_payload_sha256": "", "geometry_state_sha256": ""}
	_freeze_operation = message.operation_id
	_last_epoch = epoch
	_state = "FREEZING"
	_pose_local = _refs.drill.transform
	_pose_global = _refs.drill.global_transform
	_pose_revision = "0"
	_initialized = false
	_publication = {}
	_query_consumed = false
	_geometry_identity = ""
	_stop_received = false
	_admission_stopped = false
	_queried_publications = {}
	if _controls != null:
		var stages: Dictionary = _controls.status()
		if not stages.get("pre_admission", false) and not _run_managed_phase("pre_admission", "run_pre_admission"):
			local_fault("mutation")
			return
	if not _issue_managed_coverage():
		local_fault("source_mismatch")
		return
	if _controls != null:
		var stages: Dictionary = _controls.status()
		var control_ok: bool = _run_managed_phase("refreeze", "after_refreeze") if stages.get("post_unlock", false) else _run_managed_phase("frozen", "run_frozen")
		if not control_ok:
			local_fault("mutation")
			return
	var snapshot := _capture_snapshot()
	if not _capture_error.is_empty() or snapshot.is_empty():
		local_fault("source_mismatch")
		return
	_snapshot_raw = JSON.stringify(snapshot).to_utf8_buffer()
	if _snapshot_raw.size() > SNAPSHOT_MAX:
		local_fault("over_budget")
		return
	_snapshot_sha = sha256(_snapshot_raw)
	_snapshot_chunks = ceili(float(_snapshot_raw.size()) / float(CHUNK_MAX))
	if _snapshot_chunks < 1 or _snapshot_chunks > CHUNKS_MAX or not audit_frame():
		local_fault("over_budget")
		return
	_snapshot_cursor = -2
	# Only a fully captured, audited new frozen epoch receives a fresh quota.
	_publication_count = 0
	_publication_operations = {}
	_state = "FROZEN"

func _feed_snapshot() -> void:
	if _snapshot_cursor == -1 or _outbox.size() >= 2 or _freeze.is_empty():
		return
	if _snapshot_cursor == -2:
		if _queue("SNAPSHOT_BEGIN", _freeze.world_epoch, _freeze_operation, {"freeze_identity": _freeze.duplicate(true),
			"raw_layout_sha256": sha256(_raw_document()), "snapshot_bytes": str(_snapshot_raw.size()),
			"snapshot_sha256": _snapshot_sha, "chunk_count": str(_snapshot_chunks), "inventory_counts": _snapshot_counts}):
			_snapshot_cursor = 0
		return
	if _snapshot_cursor < _snapshot_chunks:
		var offset := _snapshot_cursor * CHUNK_MAX
		var chunk := _snapshot_raw.slice(offset, mini(offset + CHUNK_MAX, _snapshot_raw.size()))
		if _queue("SNAPSHOT_CHUNK", _freeze.world_epoch, _freeze_operation, {"freeze_id": _freeze.freeze_id,
			"chunk_index": str(_snapshot_cursor), "offset": str(offset), "decoded_length": str(chunk.size()),
			"chunk_sha256": sha256(chunk), "data_base64": Marshalls.raw_to_base64(chunk)}):
			_snapshot_cursor += 1
		return
	if _queue("SNAPSHOT_END", _freeze.world_epoch, _freeze_operation, {"freeze_identity": _freeze.duplicate(true),
		"snapshot_sha256": _snapshot_sha, "decoded_total": str(_snapshot_raw.size()), "chunks": str(_snapshot_chunks), "geometry_audit_digest": _static_digest}):
		_snapshot_cursor = -1

func _valid_desired_pose(value) -> bool:
	if not _exact(value, ["position_m","orientation_xyzw","speed_m_s"]) or not value.position_m is Array or value.position_m.size() != 3 or not value.orientation_xyzw is Array or value.orientation_xyzw.size() != 4:
		return false
	for item in value.position_m + value.orientation_xyzw + [value.speed_m_s]:
		if not is_finite(_decode_f64(item)):
			return false
	var norm := 0.0
	for item in value.orientation_xyzw:
		var scalar := _decode_f64(item)
		norm += scalar * scalar
	return norm > 0.0 and is_finite(norm) and _decode_f64(value.speed_m_s) >= 0.0

func _publish(message: Dictionary, raw: PackedByteArray) -> void:
	var initial_kind: int = int(message.type == "INITIAL_VIEW")
	_diag_timing_mark(15, initial_kind)
	_publish_diag_core(message, raw)
	_diag_timing_mark(16, initial_kind)

func _publication_resolved() -> bool:
	if _publication.get("state", "") != "APPLIED" or not _publication.get("readback_validated", false) or not _publication.get("readback") is Dictionary:
		return false
	var actual: Dictionary = _publication.readback
	return actual.get("state", "") == "APPLIED" and actual.get("freeze_identity", {}) == _freeze and actual.get("publication_operation_id", "") == _publication.operation_id and actual.get("pose_revision", "") == _pose_revision and _publication.intent_revision == _pose_revision and actual.get("drill_root_instance_id", "") == _object_id(_refs.drill)

func _reserve_noninitial_publication(message: Dictionary) -> bool:
	var body: Dictionary = message.body
	if _publication_operations.has(message.operation_id):
		_refuse(message.operation_id, "duplicate_publish")
		return false
	if not _publication.is_empty() and not _publication_resolved():
		_refuse(message.operation_id, "unknown_effect")
		return false
	if not _initialized or body.geometry_identity != _geometry_identity or body.expected_previous_revision != _pose_revision or body.pose_revision != _next_decimal(_pose_revision) or not _hex(body.numerical_receipt_digest,64):
		_refuse(message.operation_id, "stale_revision")
		return false
	if _publication_count >= PUBLICATION_MAX:
		_refuse(message.operation_id, "over_budget")
		return false
	# Reserve before pose/transform decoding, allocation, hashing or native write.
	# A failed reservation remains APPLYING; it is never cleared for another try.
	# First poison the existing record, before any new dictionary allocation.
	_publication["state"] = "APPLYING"
	_publication["readback_validated"] = false
	_publication_count += 1
	_publication["operation_id"] = message.operation_id
	_publication["payload_digest"] = ""
	_publication["intent_revision"] = body.pose_revision
	_publication_operations[message.operation_id] = true
	return true

func _publish_diag_core(message: Dictionary, raw: PackedByteArray) -> void:
	var body: Dictionary = message.body
	var initial: bool = message.type == "INITIAL_VIEW"
	if _controls_barrier or not _controls_phase.is_empty() or _admission_stopped or _queried_publications.has(message.operation_id):
		_refuse(message.operation_id, "unknown_effect")
		return
	if _state != "FROZEN" and _state != "BOUND_STOPPED":
		_refuse(message.operation_id, "unknown_effect")
		return
	if body.freeze_id != _freeze.freeze_id or not _hex(body.geometry_identity,64) or not _u64(body.pose_revision):
		_refuse(message.operation_id, "malformed")
		return
	if initial and not _valid_desired_pose(body.desired_pose):
		_refuse(message.operation_id, "malformed")
		return
	if _publication.get("state", "") == "APPLYING":
		_refuse(message.operation_id, "unknown_effect")
		return
	if initial:
		if _initialized or body.pose_revision != "0":
			_refuse(message.operation_id, "duplicate_publish")
			return
	else:
		if not _reserve_noninitial_publication(message):
			return
		if not _valid_desired_pose(body.desired_pose):
			_refuse(message.operation_id, "malformed")
			return
	var decoded := _decode_transform(body.desired_transform)
	if not decoded.ok or body.desired_transform.origin != body.desired_pose.position_m:
		_refuse(message.operation_id, "malformed")
		return
	# Persist in retained memory BEFORE the only fallible original node write.
	# A script/runtime/allocation failure leaves APPLYING, never a false ACK.
	if initial:
		_publication_operations[message.operation_id] = true
		_publication = {"state": "APPLYING", "operation_id": message.operation_id,
			"payload_digest": "", "intent_revision": body.pose_revision, "readback_validated": false}
	_publication["payload_digest"] = sha256(raw)
	_publication["desired_pose"] = body.desired_pose.duplicate(true)
	_publication["desired_transform"] = body.desired_transform.duplicate(true)
	_query_consumed = false
	if not _main._owned_apply_drill_global(self, _token, decoded.value, body.pose_revision):
		_refuse(message.operation_id, "unknown_effect")
		return
	var actual: Dictionary = _main._owned_drill_readback(self, _token)
	if actual.is_empty() or actual.node != _refs.drill or actual.pose_revision != body.pose_revision:
		return
	_pose_local = actual.local
	_pose_global = actual.global
	_pose_revision = actual.pose_revision
	_geometry_identity = body.geometry_identity
	_initialized = true
	var readback := _view_body(message.operation_id, _publication.payload_digest, "APPLIED", actual)
	_publication["readback"] = readback.duplicate(true)
	_publication["state"] = "APPLIED"
	_state = "BOUND_STOPPED"
	if audit_frame():
		_publication["readback_validated"] = true
		if not initial and _fixture.withhold_first_publish_ack and not _fixture_ack_consumed:
			_fixture_ack_consumed = true
		else:
			_queue("VIEW_READBACK", _freeze.world_epoch, message.operation_id, readback)

func _view_body(operation: String, digest: String, state: String, actual: Dictionary) -> Dictionary:
	return {"freeze_identity": _freeze.duplicate(true), "publication_operation_id": operation,
		"payload_digest": digest, "state": state, "pose_revision": actual.pose_revision,
		"drill_root_instance_id": _object_id(_refs.drill), "local_transform": _transform(actual.local),
		"global_transform": _transform(actual.global), "engine_tick": str(Engine.get_process_frames()),
		"geometry_audit_digest": _static_digest}

func _query(message: Dictionary) -> void:
	var body: Dictionary = message.body
	if _query_consumed or body.freeze_id != _freeze.freeze_id or not _label(body.publication_operation_id) or not _hex(body.payload_digest,64) or not _u64(body.expected_pose_revision):
		_refuse(message.operation_id, "unknown_effect")
		return
	if _publication_operations.has(body.publication_operation_id) and body.publication_operation_id != _publication.get("operation_id", ""):
		# It was seen in this epoch, but is no longer the current publication.
		# Never turn an old known effect into a false NOT_SEEN answer or replay it.
		_refuse(message.operation_id, "unknown_effect")
		return
	_query_consumed = true
	_queried_publications[body.publication_operation_id] = true
	var actual: Dictionary = _main._owned_drill_readback(self, _token)
	if actual.is_empty():
		return
	var observed := "NOT_SEEN"
	if not _publication.is_empty() and body.publication_operation_id == _publication.operation_id:
		if body.payload_digest != _publication.payload_digest or body.expected_pose_revision != _publication.intent_revision:
			_refuse(message.operation_id, "unknown_effect")
			return
		observed = "APPLIED" if _publication_resolved() else "APPLYING_UNKNOWN"
	_queue("VIEW_READBACK", _freeze.world_epoch, message.operation_id,
		_view_body(body.publication_operation_id, body.payload_digest, observed, actual))

func _stop(message: Dictionary) -> void:
	var body: Dictionary = message.body
	if body.freeze_id != _freeze.freeze_id or not _label(body.reason_code):
		_refuse(message.operation_id, "stale_revision")
		return
	# Veto first, even if Root has not yet learned an actually applied revision.
	_admission_stopped = true
	_stop_received = true
	_state = "BOUND_STOPPED"
	if not _u64(body.expected_pose_revision):
		_refuse(message.operation_id, "malformed")
		return
	if body.reason_code == "managed_writer_content_probe" and _controls != null:
		# This handler has received the current epoch's actual STOP above. A
		# retired epoch's flags are never a capability for this final effect.
		if body.expected_pose_revision != _pose_revision or not _run_managed_phase("final_content", "run_final_content"):
			local_fault("mutation")
		return
	_queue("STOPPED", _freeze.world_epoch, message.operation_id, {"freeze_identity": _freeze.duplicate(true),
		"pose_revision": _pose_revision, "last_publication_operation_id": _publication.get("operation_id", "none"),
		"publication_state": "NONE" if _publication.is_empty() else ("APPLIED" if _publication_resolved() else "APPLYING_UNKNOWN")})

func _unlock(message: Dictionary) -> void:
	var body: Dictionary = message.body
	if not _stop_received or not _admission_stopped or _state != "BOUND_STOPPED" or _snapshot_cursor != -1 or body.retired_freeze_id != _freeze.freeze_id or body.retired_epoch != _freeze.world_epoch or body.expected_pose_revision != _pose_revision or not _hex(body.retirement_record_digest,64):
		_refuse(message.operation_id, "stale_epoch")
		return
	if not _publication.is_empty() and not _publication_resolved():
		_refuse(message.operation_id, "unknown_effect")
		return
	var retired: String = _freeze.freeze_id
	var old_epoch: String = _freeze.world_epoch
	_retired_freeze_id = retired
	_retired_epoch = old_epoch
	_retire_managed_coverage()
	if not _main._owned_unlock_world(self, _token):
		local_fault("mutation")
		return
	_token = null
	_freeze = {}
	_required = []
	_immutable_meshes = []
	_immutable_shapes = []
	_mesh_payloads = {}
	_snapshot_raw = PackedByteArray()
	_state = "EDITABLE"
	if _fixture.edit_once_after_unlock and not _fixture_edit_consumed:
		_fixture_edit_consumed = true
		if _refs.document.obstacles.is_empty():
			local_fault("source_mismatch")
			return
		var first: Dictionary = _refs.document.obstacles[0]
		var changed: Dictionary = _refs.document.update_obstacle(int(first.object_id), {"position": first.position + Vector3(0.25,0.0,0.0)})
		if not changed.get("ok", false):
			local_fault("mutation")
			return
		_refs.document.log_event("诊断", "固定诊断fixture：解锁后由原文档写者编辑一次；不作为可见UI验收")
	if _controls != null and not _run_managed_phase("post_unlock", "after_unlock"):
		local_fault("mutation")
		return
	_editable_pending = false
	_send_editable(message.operation_id, retired, old_epoch)

func _send_editable(operation: String, retired: String, epoch: String = "") -> void:
	var raw := _raw_document()
	if raw.is_empty():
		local_fault("malformed")
		return
	_queue("EDITABLE", _retired_epoch if epoch.is_empty() else epoch, operation, {"retired_freeze_id": _retired_freeze_id if retired.is_empty() else retired,
		"document_generation": str(_refs.document._owned_generation(self)),
		"geometry_generation": str(_main._owned_geometry_revision(self)), "raw_layout_sha256": sha256(raw)})

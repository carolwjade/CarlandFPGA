class_name LayoutCodec
extends RefCounted

const GateNumericScript = preload("res://editor/gate_numeric.gd")
const GateJsonNumbersScript = preload("res://editor/gate_json_numbers.gd")
## Strict, versioned, geometry-only private layout codec.
##
## The file is plain JSON data, never a Godot Resource. This codec performs no
## filesystem I/O and never calls load(), ResourceLoader or eval. The hash is the
## existing seed-free SceneDocument commitment hash: canonical sorted JSON with
## six-decimal float formatting, not a signature or permission token.

const SCHEMA_VERSION := 1
const CONTRACT_ID := "DEEPEYE-HUMAN-LOCK-20261014/revision1"
const REQUIREMENTS_SHA256 := "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
const UNITS := "m"
const MAX_OBJECTS := 30
const MAX_FILE_BYTES := 1048576
const MAX_JSON_DEPTH := 32
const MAX_SAFE_INTEGER := 9007199254740991.0
const CUBE_HALF := 15.0
const GATE_EDGE_LIMIT := 14.85
const MIN_SAME_FACE_SEPARATION := 0.30
const EPSILON := 0.000000001
const KINDS := ["water", "hard_rock", "fault", "void", "casing"]
const FACES := ["top", "bottom", "front", "back", "left", "right"]
const KIND_PRIORITY := {"casing": 5, "fault": 4, "void": 3, "water": 2, "hard_rock": 1}
const KIND_SIZE_LIMITS := {
	"water": [[3.0, 10.0], [2.0, 8.0], [1.0, 4.0]],
	"hard_rock": [[1.0, 6.0], [1.0, 6.0], [1.0, 6.0]],
	"fault": [[4.0, 15.0], [0.5, 2.0], [3.0, 10.0]],
	"void": [[2.0, 8.0], [2.0, 8.0], [2.0, 8.0]],
	"casing": [[0.5, 1.5], [0.5, 1.5], [3.0, 20.0]],
}
const TOP_FIELDS := ["schema", "contract", "requirements_sha256", "units", "layout", "layout_hash"]
const LAYOUT_FIELDS := ["obstacles", "gates"]
const OBSTACLE_FIELDS := ["object_id", "kind", "position", "rotation_deg", "size", "priority"]
const VECTOR_FIELDS := ["x", "y", "z"]
const GATE_FIELDS := ["face", "u", "v"]

static func encode(layout: Dictionary) -> Dictionary:
	var normalized := _normalize_layout(layout)
	if not bool(normalized.get("ok", false)):
		return normalized
	var packed_layout := _pack_normalized(normalized)
	var layout_hash := _canon(packed_layout).sha256_text()
	var file_data := {
		"schema": SCHEMA_VERSION,
		"contract": CONTRACT_ID,
		"requirements_sha256": REQUIREMENTS_SHA256,
		"units": UNITS,
		"layout": packed_layout,
		"layout_hash": layout_hash,
	}
	var text := JSON.stringify(file_data, "  ", true, true) + "\n"
	if text.to_utf8_buffer().size() > MAX_FILE_BYTES:
		return _fail("编码后的布局超过 1 MiB 上限")
	return {
		"ok": true,
		"text": text,
		"layout_hash": layout_hash,
		"count": normalized.obstacles.size(),
	}

static func decode(text: String) -> Dictionary:
	if text.is_empty():
		return _fail("布局文件为空")
	if text.to_utf8_buffer().size() > MAX_FILE_BYTES:
		return _fail("布局文件超过 1 MiB 上限")
	if _exceeds_depth(text):
		return _fail("JSON 嵌套超过 %d 层上限" % MAX_JSON_DEPTH)
	var parser := JSON.new()
	var parse_error := parser.parse(text)
	if parse_error != OK:
		var message := parser.get_error_message().substr(0, 160)
		return _fail("JSON 解析失败（第 %d 行）: %s" % [parser.get_error_line() + 1, message])
	var data = parser.get_data()
	if not (data is Dictionary):
		return _fail("布局文件根节点必须是 JSON 对象")
	var restored_numbers: Dictionary = GateJsonNumbersScript.restore(text, data)
	if not restored_numbers.ok:
		return _fail(String(restored_numbers.reason))
	var field_error := _check_fields(data, TOP_FIELDS, "文件")
	if field_error != "":
		return _fail(field_error)
	var schema_result := _read_integer(data.get("schema"), "schema", 0.0, MAX_SAFE_INTEGER)
	if not bool(schema_result.get("ok", false)):
		return schema_result
	if int(schema_result.value) != SCHEMA_VERSION:
		return _fail("schema 仅支持 %d" % SCHEMA_VERSION)
	if String(data.get("contract", "")) != CONTRACT_ID:
		return _fail("contract 不受支持")
	if String(data.get("requirements_sha256", "")) != REQUIREMENTS_SHA256:
		return _fail("requirements_sha256 与锁定合同不一致")
	if String(data.get("units", "")) != UNITS:
		return _fail("units 必须为 m")
	if not (data.get("layout") is Dictionary):
		return _fail("layout 必须是对象")
	var provided_hash := String(data.get("layout_hash", ""))
	if not _is_lower_sha256(provided_hash):
		return _fail("layout_hash 必须是小写 64 位十六进制 SHA256")
	var normalized := _normalize_layout(data.layout)
	if not bool(normalized.get("ok", false)):
		return normalized
	var packed_layout := _pack_normalized(normalized)
	var expected_hash := _canon(packed_layout).sha256_text()
	if provided_hash != expected_hash:
		return _fail("layout_hash 与规范几何不一致")
	return {
		"ok": true,
		"obstacles": normalized.obstacles,
		"gates": normalized.gates,
		"layout_hash": expected_hash,
		"count": normalized.obstacles.size(),
	}

static func _normalize_layout(layout: Dictionary) -> Dictionary:
	var field_error := _check_fields(layout, LAYOUT_FIELDS, "layout")
	if field_error != "":
		return _fail(field_error)
	if not (layout.get("obstacles") is Array):
		return _fail("layout.obstacles 必须是数组")
	var packed_obstacles: Array = layout.obstacles
	if packed_obstacles.size() > MAX_OBJECTS:
		return _fail("对象数量超过 30 个上限")
	var normalized_obstacles: Array = []
	var object_ids: Dictionary = {}
	for index in packed_obstacles.size():
		var packed = packed_obstacles[index]
		var context := "obstacles[%d]" % index
		if not (packed is Dictionary):
			return _fail("%s 必须是对象" % context)
		field_error = _check_fields(packed, OBSTACLE_FIELDS, context)
		if field_error != "":
			return _fail(field_error)
		var id_result := _read_integer(packed.get("object_id"), context + ".object_id", 1.0, MAX_SAFE_INTEGER)
		if not bool(id_result.get("ok", false)):
			return id_result
		var object_id := int(id_result.value)
		if object_ids.has(object_id):
			return _fail("%s.object_id 重复" % context)
		object_ids[object_id] = true
		var kind := String(packed.get("kind", ""))
		if not KINDS.has(kind):
			return _fail("%s.kind 不受支持" % context)
		var position_result := _read_vec3(packed.get("position"), context + ".position")
		if not bool(position_result.get("ok", false)):
			return position_result
		var rotation_result := _read_vec3(packed.get("rotation_deg"), context + ".rotation_deg")
		if not bool(rotation_result.get("ok", false)):
			return rotation_result
		var size_result := _read_vec3(packed.get("size"), context + ".size")
		if not bool(size_result.get("ok", false)):
			return size_result
		var position: Vector3 = position_result.value
		var rotation: Vector3 = rotation_result.value
		var size: Vector3 = size_result.value
		var position_problem := _validate_position(position)
		if position_problem != "":
			return _fail("%s: %s" % [context, position_problem])
		var size_problem := _validate_size(kind, size)
		if size_problem != "":
			return _fail("%s: %s" % [context, size_problem])
		var priority_result := _read_integer(packed.get("priority"), context + ".priority", 1.0, 5.0)
		if not bool(priority_result.get("ok", false)):
			return priority_result
		var priority := int(priority_result.value)
		if priority != int(KIND_PRIORITY[kind]):
			return _fail("%s.priority 与 kind 的固定材料优先级不一致" % context)
		normalized_obstacles.append({
			"object_id": object_id,
			"kind": kind,
			"position": position,
			"rotation_deg": rotation,
			"size": size,
			"priority": priority,
		})
	if not (layout.get("gates") is Dictionary):
		return _fail("layout.gates 必须是对象")
	var packed_gates: Dictionary = layout.gates
	field_error = _check_fields(packed_gates, ["entry", "exit"], "layout.gates")
	if field_error != "":
		return _fail(field_error)
	var normalized_gates: Dictionary = {}
	for which in ["entry", "exit"]:
		var gate_result := _read_gate(packed_gates.get(which), "gates." + which)
		if not bool(gate_result.get("ok", false)):
			return gate_result
		normalized_gates[which] = gate_result.gate
	var gate_problem := _validate_gate_geometry(normalized_gates)
	if gate_problem != "":
		return _fail(gate_problem)
	return {"ok": true, "obstacles": normalized_obstacles, "gates": normalized_gates}

static func _read_gate(value, context: String) -> Dictionary:
	if not (value is Dictionary):
		return _fail("%s 必须是对象" % context)
	var field_error := _check_fields(value, GATE_FIELDS, context)
	if field_error != "":
		return _fail(field_error)
	var face := String(value.get("face", ""))
	if not FACES.has(face):
		return _fail("%s.face 不受支持" % context)
	var u_result := _read_number(value.get("u"), context + ".u")
	if not bool(u_result.get("ok", false)):
		return u_result
	var v_result := _read_number(value.get("v"), context + ".v")
	if not bool(v_result.get("ok", false)):
		return v_result
	return {"ok": true, "gate": {"face": face, "u": float(u_result.value), "v": float(v_result.value)}}

static func _read_vec3(value, context: String) -> Dictionary:
	if not (value is Dictionary):
		return _fail("%s 必须是对象" % context)
	var field_error := _check_fields(value, VECTOR_FIELDS, context)
	if field_error != "":
		return _fail(field_error)
	var x_result := _read_number(value.get("x"), context + ".x")
	if not bool(x_result.get("ok", false)):
		return x_result
	var y_result := _read_number(value.get("y"), context + ".y")
	if not bool(y_result.get("ok", false)):
		return y_result
	var z_result := _read_number(value.get("z"), context + ".z")
	if not bool(z_result.get("ok", false)):
		return z_result
	return {"ok": true, "value": Vector3(float(x_result.value), float(y_result.value), float(z_result.value))}

static func _read_number(value, label: String) -> Dictionary:
	var value_type := typeof(value)
	if value_type != TYPE_INT and value_type != TYPE_FLOAT:
		return _fail("%s 必须是数值" % label)
	var number := float(value)
	if not is_finite(number):
		return _fail("%s 必须是有限数值" % label)
	return {"ok": true, "value": number}

static func _read_integer(value, label: String, minimum: float, maximum: float) -> Dictionary:
	var number_result := _read_number(value, label)
	if not bool(number_result.get("ok", false)):
		return number_result
	var number := float(number_result.value)
	if number != floorf(number):
		return _fail("%s 必须是正整数，禁止小数截断" % label)
	if number < minimum or number > maximum:
		return _fail("%s 超出安全整数范围" % label)
	return {"ok": true, "value": int(number)}

static func _validate_size(kind: String, size: Vector3) -> String:
	var limits: Array = KIND_SIZE_LIMITS[kind]
	var axes := ["X", "Y", "Z"]
	var values := [size.x, size.y, size.z]
	for index in 3:
		var low := float(limits[index][0])
		var high := float(limits[index][1])
		if float(values[index]) < low - EPSILON or float(values[index]) > high + EPSILON:
			return "%s 的 %s 尺寸 %.3fm 超出允许范围 %.2f–%.2fm" % [kind, axes[index], float(values[index]), low, high]
	return ""

static func _validate_position(position: Vector3) -> String:
	if (absf(position.x) > CUBE_HALF + EPSILON or absf(position.y) > CUBE_HALF + EPSILON
			or absf(position.z) > CUBE_HALF + EPSILON):
		return "位置超出工作立方体（中心须在 ±15m 内）"
	return ""

static func _validate_gate_geometry(gates: Dictionary) -> String:
	for which in ["entry", "exit"]:
		var gate: Dictionary = gates[which]
		if not GateNumericScript.valid_coordinate(float(gate.u)) or not GateNumericScript.valid_coordinate(float(gate.v)):
			return "%s: 圈心距面边不足0.15m（|u|、|v| 须 ≤ %.2fm）" % [which, GATE_EDGE_LIMIT]
	if String(gates.entry.face) == String(gates.exit.face):
		var du := float(gates.entry.u) - float(gates.exit.u)
		var dv := float(gates.entry.v) - float(gates.exit.v)
		var separation := sqrt(du * du + dv * dv)
		if GateNumericScript.circles_overlap(float(gates.entry.u), float(gates.entry.v), float(gates.exit.u), float(gates.exit.v)):
			return "同面两圈重叠：圈心距 %.3fm < 0.30m" % separation
	return ""

static func _pack_normalized(normalized: Dictionary) -> Dictionary:
	var packed_obstacles: Array = []
	for obstacle in normalized.obstacles:
		packed_obstacles.append({
			"object_id": int(obstacle.object_id),
			"kind": String(obstacle.kind),
			"position": {"x": float(obstacle.position.x), "y": float(obstacle.position.y), "z": float(obstacle.position.z)},
			"rotation_deg": {"x": float(obstacle.rotation_deg.x), "y": float(obstacle.rotation_deg.y), "z": float(obstacle.rotation_deg.z)},
			"size": {"x": float(obstacle.size.x), "y": float(obstacle.size.y), "z": float(obstacle.size.z)},
			"priority": int(obstacle.priority),
		})
	return {"obstacles": packed_obstacles, "gates": normalized.gates.duplicate(true)}

static func _check_fields(data: Dictionary, allowed: Array, context: String) -> String:
	for key in data.keys():
		var name := String(key)
		if not allowed.has(name):
			return "%s 含不支持的字段: %s" % [context, _safe_field(name)]
	for name in allowed:
		if not data.has(name):
			return "%s 缺少字段: %s" % [context, _safe_field(name)]
	return ""

static func _safe_field(name: String) -> String:
	var safe := name.replace("\n", "?").replace("\r", "?").replace("\t", "?")
	if safe.length() > 32:
		safe = safe.substr(0, 32) + "…"
	return safe

static func _is_lower_sha256(value: String) -> bool:
	if value.length() != 64:
		return false
	for index in value.length():
		var character := value[index]
		if not ((character >= "0" and character <= "9") or (character >= "a" and character <= "f")):
			return false
	return true

static func _exceeds_depth(text: String) -> bool:
	var depth := 0
	var in_string := false
	var escaped := false
	for index in text.length():
		var character := text[index]
		if in_string:
			if escaped:
				escaped = false
			elif character == "\\":
				escaped = true
			elif character == "\"":
				in_string = false
			continue
		if character == "\"":
			in_string = true
		elif character == "{" or character == "[":
			depth += 1
			if depth > MAX_JSON_DEPTH:
				return true
		elif character == "}" or character == "]":
			depth -= 1
	return false

static func _canon(value) -> String:
	match typeof(value):
		TYPE_DICTIONARY:
			var keys: Array = value.keys()
			keys.sort()
			var parts: Array = []
			for key in keys:
				parts.append(JSON.stringify(str(key)) + ":" + _canon(value[key]))
			return "{" + ",".join(parts) + "}"
		TYPE_ARRAY:
			var parts: Array = []
			for item in value:
				parts.append(_canon(item))
			return "[" + ",".join(parts) + "]"
		TYPE_STRING, TYPE_STRING_NAME:
			return JSON.stringify(String(value))
		TYPE_BOOL:
			return "true" if bool(value) else "false"
		TYPE_INT:
			return str(int(value))
		TYPE_FLOAT:
			var number := float(value)
			if is_zero_approx(number):
				number = 0.0
			return String.num(number, 6)
		TYPE_VECTOR3:
			var vector: Vector3 = value
			return _canon({"x": vector.x, "y": vector.y, "z": vector.z})
		_:
			return JSON.stringify(str(value))

static func _fail(reason: String) -> Dictionary:
	return {"ok": false, "reason": reason, "errors": [reason]}

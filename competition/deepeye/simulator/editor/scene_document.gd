class_name SceneDocument
extends RefCounted
## G02 editing foundation document: single owner of editor data and state.
##
## Contract: competition/deepeye/docs/resource_contract.json (frozen by A).
##  - Work cube is centred [-15, 15]^3 metres, forward is local +Z.
##  - Gates are blue entry / red exit circles, diameter 0.30 m, on any of the six
##    faces, circle centre at least 0.15 m from the face edges; same-face circles
##    must not overlap (centre separation < 0.30 m is rejected).
##  - Edits are allowed only in "editing" and "stopped"; "running", "paused" and
##    "locked" reject every mutation. The document never auto-moves the other gate.
##  - Run/continue stay disabled until a real authority+mode bridge exists; the
##    viewer never fabricates motion, timelines, board acknowledgements or live
##    link labels (source/topology/baud/age default to 未连接).
##  - Random layouts are kept viewer-only: the seed and the layout hash are stored
##    here for post-hoc reproduction; only the seed-free commitment hash is the
##    value a controller could receive.
##  - Editor gate checks are geometry-only: the 1 m initialization/alignment space
##    and global route reachability remain pending world_authority ("待权威").
##
## Headless tests: tests/test_editor_document.gd (SceneTree, non-zero exit = fail).

signal layout_changed
signal gates_changed
signal state_changed(state: String)
signal event_logged(event: Dictionary)
signal stop_requested(source: String)
signal selection_changed(object_id: int)

const CUBE_HALF := 15.0
const GATE_DIAMETER_M := 0.30
const GATE_RADIUS_M := 0.15
const GATE_EDGE_MARGIN_M := 0.15
const MIN_SAME_FACE_SEPARATION_M := 0.30
const UNDO_CAPACITY := 64
const MAX_OBJECTS := 30
const EDITABLE_STATES := ["editing", "stopped"]
const ALL_STATES := ["editing", "locked", "running", "paused", "stopped"]
const KINDS := ["water", "hard_rock", "fault", "void", "casing"]
const FACES := ["top", "bottom", "front", "back", "left", "right"]

const KIND_LABELS := {
	"water": "水层",
	"hard_rock": "硬岩",
	"fault": "断层带",
	"void": "溶洞",
	"casing": "套管",
}
## Editable size ranges (metres) per axis, from taskbook section 8.4.
const KIND_SIZE_LIMITS := {
	"water": [[3.0, 10.0], [2.0, 8.0], [1.0, 4.0]],
	"hard_rock": [[1.0, 6.0], [1.0, 6.0], [1.0, 6.0]],
	"fault": [[4.0, 15.0], [0.5, 2.0], [3.0, 10.0]],
	"void": [[2.0, 8.0], [2.0, 8.0], [2.0, 8.0]],
	"casing": [[0.5, 1.5], [0.5, 1.5], [3.0, 20.0]],
}
const KIND_DEFAULTS := {
	"water": Vector3(6.0, 4.0, 2.0),
	"hard_rock": Vector3(3.0, 3.0, 3.0),
	"fault": Vector3(8.0, 1.0, 6.0),
	"void": Vector3(4.0, 3.0, 3.0),
	"casing": Vector3(0.8, 0.8, 8.0),
}
## Fixed material priority for overlap resolution (forced no-entry wins).
const KIND_PRIORITY := {"casing": 5, "fault": 4, "void": 3, "water": 2, "hard_rock": 1}
const FACE_LABELS := {
	"top": "顶(+Y)",
	"bottom": "底(-Y)",
	"front": "前(+Z)",
	"back": "后(-Z)",
	"left": "左(-X)",
	"right": "右(+X)",
}
const FACE_NORMALS := {
	"top": Vector3(0.0, 1.0, 0.0),
	"bottom": Vector3(0.0, -1.0, 0.0),
	"front": Vector3(0.0, 0.0, 1.0),
	"back": Vector3(0.0, 0.0, -1.0),
	"left": Vector3(-1.0, 0.0, 0.0),
	"right": Vector3(1.0, 0.0, 0.0),
}

var run_state := "editing"
var obstacles: Array = []
var gates := {
	"entry": {"face": "front", "u": 0.0, "v": 0.0},
	"exit": {"face": "back", "u": 0.0, "v": 0.0},
}
var selected_id := -1
var random_seed := 0
var control_bridge_connected := false
var link_state := {
	"source": "未连接",
	"topology": "未连接",
	"baud": "未连接",
	"age": "未连接",
	"ai": "未连接",
}
var events: Array = []

var _undo: Array = []
var _redo: Array = []
var _next_id := 1
var _event_seq := 1

func _init() -> void:
	log_event("系统", "场景文档就绪：初始状态 编辑中（viewer 基线，控制未使能）")

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

func can_edit() -> bool:
	return EDITABLE_STATES.has(run_state)

func edit_block_reason() -> String:
	match run_state:
		"running":
			return "运行中禁止编辑：先停止并生成新run_id"
		"paused":
			return "暂停中禁止编辑"
		"locked":
			return "布局已锁定：先解锁再编辑"
		_:
			return "当前状态禁止编辑"

func state_name_cn() -> String:
	match run_state:
		"editing":
			return "编辑中"
		"locked":
			return "布局已锁定"
		"running":
			return "运行中"
		"paused":
			return "已暂停"
		"stopped":
			return "已停止"
		_:
			return run_state

func kind_label(kind: String) -> String:
	return KIND_LABELS.get(kind, kind)

func gate_label(which: String) -> String:
	return "入口蓝圈" if which == "entry" else "离开红圈"

func obstacle_count() -> int:
	return obstacles.size()

func undo_depth() -> int:
	return _undo.size()

func redo_depth() -> int:
	return _redo.size()

# ---------------------------------------------------------------------------
# Obstacles
# ---------------------------------------------------------------------------

func add_obstacle(kind: String, position: Vector3 = Vector3.ZERO, rotation_deg: Vector3 = Vector3.ZERO,
		size: Vector3 = Vector3.ZERO) -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	if not KINDS.has(kind):
		return _reject("未知地质体类型: " + kind)
	var use_size: Vector3 = size
	if use_size.is_equal_approx(Vector3.ZERO):
		use_size = KIND_DEFAULTS[kind]
	var size_problem := _validate_size(kind, use_size)
	if size_problem != "":
		return _reject(size_problem)
	var position_problem := _validate_position(position)
	if position_problem != "":
		return _reject(position_problem)
	var previous := _snapshot()
	var object_id := _next_id
	_next_id += 1
	obstacles.append({
		"object_id": object_id,
		"kind": kind,
		"position": position,
		"rotation_deg": rotation_deg,
		"size": use_size,
		"priority": KIND_PRIORITY[kind],
	})
	_push_undo(previous)
	log_event("操作", "添加%s #%d" % [kind_label(kind), object_id])
	emit_signal("layout_changed")
	return {"ok": true, "id": object_id, "reason": ""}

func remove_obstacle(object_id: int) -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	var index := _index_of(object_id)
	if index < 0:
		return _reject("对象不存在: #%d" % object_id)
	var previous := _snapshot()
	obstacles.remove_at(index)
	if selected_id == object_id:
		selected_id = -1
		emit_signal("selection_changed", -1)
	_push_undo(previous)
	log_event("操作", "删除对象 #%d" % object_id)
	emit_signal("layout_changed")
	return {"ok": true, "reason": ""}

func update_obstacle(object_id: int, changes: Dictionary, record_history: bool = true) -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	var obstacle := obstacle_by_id(object_id)
	if obstacle.is_empty():
		return _reject("对象不存在: #%d" % object_id)
	var next_position: Vector3 = obstacle.position
	var next_rotation: Vector3 = obstacle.rotation_deg
	var next_size: Vector3 = obstacle.size
	if changes.has("position"):
		next_position = changes["position"]
	if changes.has("rotation_deg"):
		next_rotation = changes["rotation_deg"]
	if changes.has("size"):
		next_size = changes["size"]
	var size_problem := _validate_size(obstacle.kind, next_size)
	if size_problem != "":
		return _reject(size_problem)
	var position_problem := _validate_position(next_position)
	if position_problem != "":
		return _reject(position_problem)
	var previous := _snapshot()
	obstacle["position"] = next_position
	obstacle["rotation_deg"] = next_rotation
	obstacle["size"] = next_size
	if record_history:
		_push_undo(previous)
	emit_signal("layout_changed")
	return {"ok": true, "reason": ""}

func duplicate_obstacle(object_id: int) -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	var obstacle := obstacle_by_id(object_id)
	if obstacle.is_empty():
		return _reject("对象不存在: #%d" % object_id)
	var limit := CUBE_HALF
	var offset := Vector3(0.5, 0.0, 0.0)
	if absf(obstacle.position.x + offset.x) > limit:
		offset = Vector3(0.0, 0.5, 0.0)
	if absf(obstacle.position.y + offset.y) > limit:
		offset = Vector3(0.0, 0.0, 0.5)
	return add_obstacle(obstacle.kind, obstacle.position + offset, obstacle.rotation_deg, obstacle.size)

func reset_layout() -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	var previous := _snapshot()
	obstacles = []
	_next_id = 1
	random_seed = 0
	if selected_id != -1:
		selected_id = -1
		emit_signal("selection_changed", -1)
	_push_undo(previous)
	log_event("操作", "清空为 空场")
	emit_signal("layout_changed")
	return {"ok": true, "reason": ""}

func obstacle_by_id(object_id: int) -> Dictionary:
	for obstacle in obstacles:
		if int(obstacle.object_id) == object_id:
			return obstacle
	return {}

## Conservative world-AABB overlap warnings with fixed material priority: the
## editor only reports; forced no-entry materials win, nothing is auto-moved.
func overlap_warnings() -> Array:
	var warnings: Array = []
	for i in obstacles.size():
		for j in range(i + 1, obstacles.size()):
			var a: Dictionary = obstacles[i]
			var b: Dictionary = obstacles[j]
			var half_a: Vector3 = world_half_extent(a.size, a.rotation_deg)
			var half_b: Vector3 = world_half_extent(b.size, b.rotation_deg)
			if (absf(a.position.x - b.position.x) < half_a.x + half_b.x
					and absf(a.position.y - b.position.y) < half_a.y + half_b.y
					and absf(a.position.z - b.position.z) < half_a.z + half_b.z):
				var higher: Dictionary = a if int(a.priority) >= int(b.priority) else b
				warnings.append("#%d %s 与 #%d %s 重叠：按材料优先级由 %s 解析（强制禁入优先）" % [
					int(a.object_id), kind_label(String(a.kind)), int(b.object_id), kind_label(String(b.kind)),
					kind_label(String(higher.kind))])
	return warnings

func select_object(object_id: int) -> void:
	if object_id != -1 and obstacle_by_id(object_id).is_empty():
		return
	selected_id = object_id
	emit_signal("selection_changed", selected_id)

# ---------------------------------------------------------------------------
# Random layout (viewer-only, reproducible)
# ---------------------------------------------------------------------------

func randomize_layout(seed_value: int, count: int) -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	if count < 1 or count > MAX_OBJECTS:
		return _reject("对象数量须在 1..%d（当前 %d）" % [MAX_OBJECTS, count])
	var previous := _snapshot()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var generated: Array = []
	for i in count:
		var kind: String = KINDS[rng.randi_range(0, KINDS.size() - 1)]
		var limits: Array = KIND_SIZE_LIMITS[kind]
		var size := Vector3(
			snappedf(rng.randf_range(float(limits[0][0]), float(limits[0][1])), 0.01),
			snappedf(rng.randf_range(float(limits[1][0]), float(limits[1][1])), 0.01),
			snappedf(rng.randf_range(float(limits[2][0]), float(limits[2][1])), 0.01))
		var rotation := Vector3(0.0, snappedf(rng.randf_range(0.0, 359.0), 1.0), 0.0)
		var half := world_half_extent(size, rotation)
		var axis_range := Vector3(CUBE_HALF - half.x, CUBE_HALF - half.y, CUBE_HALF - half.z)
		var position := Vector3(
			clampf(snappedf(rng.randf_range(-axis_range.x, axis_range.x), 0.01), -axis_range.x, axis_range.x),
			clampf(snappedf(rng.randf_range(-axis_range.y, axis_range.y), 0.01), -axis_range.y, axis_range.y),
			clampf(snappedf(rng.randf_range(-axis_range.z, axis_range.z), 0.01), -axis_range.z, axis_range.z))
		generated.append({
			"object_id": i + 1,
			"kind": kind,
			"position": position,
			"rotation_deg": rotation,
			"size": size,
			"priority": KIND_PRIORITY[kind],
		})
	obstacles = generated
	_next_id = count + 1
	random_seed = seed_value
	if selected_id != -1:
		selected_id = -1
		emit_signal("selection_changed", -1)
	_push_undo(previous)
	var hash := commitment_hash()
	log_event("操作", "随机生成 %d 个对象（种子 %d；布局hash %s；仅查看器内保留，控制器只得承诺hash）" % [count, seed_value, hash.substr(0, 12)])
	emit_signal("layout_changed")
	return {"ok": true, "seed": seed_value, "count": count, "layout_hash": hash}

func random_record() -> Dictionary:
	return {
		"seed": random_seed,
		"count": obstacles.size(),
		"layout_hash": commitment_hash(),
		"scope": "viewer-only post-hoc reproduction; controller receives the seed-free commitment hash",
	}

## Seed-free commitment hash over obstacles + gates (canonical UTF-8 JSON).
func commitment_hash() -> String:
	return _canon(_layout_dict()).sha256_text()

func layout_hash() -> String:
	return commitment_hash()

## Conservative world-space half extent of a rotated box (corner transform, 8 samples).
func world_half_extent(size: Vector3, rotation_deg: Vector3) -> Vector3:
	var basis := Basis.from_euler(Vector3(
		deg_to_rad(rotation_deg.x), deg_to_rad(rotation_deg.y), deg_to_rad(rotation_deg.z)))
	var half := Vector3.ZERO
	for sx in [-0.5, 0.5]:
		for sy in [-0.5, 0.5]:
			for sz in [-0.5, 0.5]:
				var corner: Vector3 = basis * Vector3(size.x * float(sx), size.y * float(sy), size.z * float(sz))
				half.x = maxf(half.x, absf(corner.x))
				half.y = maxf(half.y, absf(corner.y))
				half.z = maxf(half.z, absf(corner.z))
	return half

# ---------------------------------------------------------------------------
# Gates (blue entry / red exit circles)
# ---------------------------------------------------------------------------

func set_gate(which: String, face: String, u: float, v: float) -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	if not gates.has(which):
		return _reject("未知的门: " + which)
	if not FACES.has(face):
		return _reject("未知面: " + face)
	var candidate := {"face": face, "u": float(u), "v": float(v)}
	var backup: Dictionary = gates[which]
	if candidate == backup:
		return {"ok": true, "valid": true, "pending_authority": validate_gates().pending_authority}
	var previous := _snapshot()
	gates[which] = candidate
	var result := validate_gates()
	if not result.valid:
		gates[which] = backup
		log_event("警告", "圈心设置被拒绝（%s）: %s" % [gate_label(which), "; ".join(result.errors)])
		return {"ok": false, "errors": result.errors, "reason": result.errors[0]}
	_push_undo(previous)
	log_event("操作", "设置%s：面 %s, u=%.3f, v=%.3f（编辑器几何有效；初始化空间/路线校验待权威）"
		% [gate_label(which), FACE_LABELS[face], u, v])
	emit_signal("gates_changed")
	return {"ok": true, "valid": true, "pending_authority": result.pending_authority}

func validate_gates() -> Dictionary:
	var errors: Array = []
	var limit := CUBE_HALF - GATE_EDGE_MARGIN_M
	for which in ["entry", "exit"]:
		var gate: Dictionary = gates.get(which, {})
		var label := gate_label(which)
		if gate.is_empty() or not FACES.has(gate.get("face", "")):
			errors.append("%s: 未知面" % label)
			continue
		if absf(float(gate.u)) > limit + 0.000000001 or absf(float(gate.v)) > limit + 0.000000001:
			errors.append("%s: 圈心距面边不足0.15m（|u|、|v| 须 ≤ %.2fm）" % [label, limit])
	if FACES.has(gates.get("entry", {}).get("face", "")) and gates["entry"].face == gates["exit"].face:
		var du := float(gates.entry.u) - float(gates.exit.u)
		var dv := float(gates.entry.v) - float(gates.exit.v)
		var separation := sqrt(du * du + dv * dv)
		if separation < MIN_SAME_FACE_SEPARATION_M - 0.000000001:
			errors.append("同面两圈重叠：圈心距 %.3fm < 0.30m" % separation)
	var pending := [
		"起止端内侧1m初始化/对准空间与禁入体重叠：待 world_authority 复核",
		"离线全图路线可达性：编辑器不校验、不提供给控制器",
	]
	return {"valid": errors.is_empty(), "errors": errors, "pending_authority": pending}

func gate_position(which: String) -> Vector3:
	var gate: Dictionary = gates.get(which, {})
	var u := float(gate.get("u", 0.0))
	var v := float(gate.get("v", 0.0))
	match String(gate.get("face", "")):
		"top":
			return Vector3(u, CUBE_HALF, v)
		"bottom":
			return Vector3(u, -CUBE_HALF, v)
		"front":
			return Vector3(u, v, CUBE_HALF)
		"back":
			return Vector3(u, v, -CUBE_HALF)
		"right":
			return Vector3(CUBE_HALF, v, u)
		"left":
			return Vector3(-CUBE_HALF, v, u)
		_:
			return Vector3.ZERO

func gate_normal(which: String) -> Vector3:
	var gate: Dictionary = gates.get(which, {})
	return FACE_NORMALS.get(String(gate.get("face", "")), Vector3.UP)

## Face-local tangent directions: local u/v in the face plane (u along X or Z; v along Z or Y).
func face_tangents(face: String) -> Dictionary:
	match face:
		"top", "bottom":
			return {"u": Vector3(1.0, 0.0, 0.0), "v": Vector3(0.0, 0.0, 1.0)}
		"front", "back":
			return {"u": Vector3(1.0, 0.0, 0.0), "v": Vector3(0.0, 1.0, 0.0)}
		"left", "right":
			return {"u": Vector3(0.0, 0.0, 1.0), "v": Vector3(0.0, 1.0, 0.0)}
		_:
			return {"u": Vector3.RIGHT, "v": Vector3.UP}

# ---------------------------------------------------------------------------
# Undo / redo
# ---------------------------------------------------------------------------

func undo() -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	if _undo.is_empty():
		return {"ok": false, "reason": "没有可撤销的操作", "errors": ["没有可撤销的操作"]}
	var current := _snapshot()
	var previous: String = _undo.pop_back()
	_redo.append(current)
	while _redo.size() > UNDO_CAPACITY:
		_redo.pop_front()
	_restore(previous)
	log_event("操作", "撤销（剩余 %d 步）" % _undo.size())
	emit_signal("layout_changed")
	emit_signal("gates_changed")
	return {"ok": true, "reason": ""}

func redo() -> Dictionary:
	if not can_edit():
		return _reject(edit_block_reason())
	if _redo.is_empty():
		return {"ok": false, "reason": "没有可重做的操作", "errors": ["没有可重做的操作"]}
	var current := _snapshot()
	var next: String = _redo.pop_back()
	_undo.append(current)
	while _undo.size() > UNDO_CAPACITY:
		_undo.pop_front()
	_restore(next)
	log_event("操作", "重做（剩余 %d 步）" % _redo.size())
	emit_signal("layout_changed")
	emit_signal("gates_changed")
	return {"ok": true, "reason": ""}

## Explicit checkpoint for grouped edits (e.g. one drag = one undo step).
func push_undo_checkpoint() -> void:
	if not can_edit():
		return
	_push_undo(_snapshot())

# ---------------------------------------------------------------------------
# Run state machine (no motion implementation in this viewer baseline)
# ---------------------------------------------------------------------------

func set_run_state_for_testing(state: String) -> bool:
	## Test hook only. It changes the state label and gating; it cannot start any
	## motion, timeline or authority bridge, because none exists in this build.
	if not ALL_STATES.has(state):
		return false
	run_state = state
	log_event("测试", "状态注入(仅测试钩子): " + state_name_cn())
	emit_signal("state_changed", run_state)
	return true

func lock_layout() -> Dictionary:
	if run_state != "editing":
		return _reject("仅编辑中可锁定布局")
	run_state = "locked"
	log_event("状态", "布局已锁定：禁止编辑，运行仍需真实权威桥")
	emit_signal("state_changed", run_state)
	return {"ok": true, "reason": ""}

func unlock_layout() -> Dictionary:
	if run_state != "locked":
		return _reject("仅布局锁定状态可解锁")
	run_state = "editing"
	log_event("状态", "已解锁，返回编辑中")
	emit_signal("state_changed", run_state)
	return {"ok": true, "reason": ""}

func request_run() -> Dictionary:
	return _bridge_disabled("运行")

func request_continue() -> Dictionary:
	return _bridge_disabled("继续")

func request_pause() -> Dictionary:
	return _bridge_disabled("暂停")

func _bridge_disabled(action: String) -> Dictionary:
	var reason := "未连接控制权威/模式桥：%s保持禁用（viewer 无模拟运动、无时间线）" % action
	log_event("警示", reason)
	return {"ok": false, "reason": reason, "acknowledged": false}

## Global Esc path: emits stop_requested only. It never fakes a board
## acknowledgement and never jumps the state ahead of the real authority.
func request_stop(source: String) -> Dictionary:
	if run_state == "running" or run_state == "paused":
		emit_signal("stop_requested", source)
		log_event("警示", "已发出停止请求（来源: %s）；等待真实权威确认，未伪造板端确认" % source)
		return {"ok": true, "requested": true, "acknowledged": false,
			"note": "等待真实权威确认（viewer 不伪造板端确认/状态跳变）"}
	var reason := "当前未处于运行/暂停状态（%s）" % state_name_cn()
	log_event("提示", "停止请求忽略：" + reason)
	return {"ok": false, "reason": reason, "acknowledged": false}

func is_motion_active() -> bool:
	## The viewer baseline has no drill motion at all; this is always false and
	## exists so callers/tests can assert that no fake motion is displayed.
	return false

## Link labels may only be updated by a real authority/mode bridge handshake.
func set_link_state(key: String, value: String) -> bool:
	if not control_bridge_connected:
		log_event("警示", "拒绝伪造链路状态 %s=%s（未连接真实桥）" % [key, value])
		return false
	if not link_state.has(key):
		return false
	link_state[key] = value
	emit_signal("state_changed", run_state)
	return true

func status_snapshot() -> Dictionary:
	var validation := validate_gates()
	return {
		"run_state": run_state,
		"run_state_cn": state_name_cn(),
		"can_edit": can_edit(),
		"edit_block_reason": edit_block_reason(),
		"source": link_state.source,
		"topology": link_state.topology,
		"baud": link_state.baud,
		"age": link_state.age,
		"ai": link_state.ai,
		"bridge": "已连接" if control_bridge_connected else "未连接",
		"selected_id": selected_id,
		"obstacle_count": obstacles.size(),
		"undo_depth": _undo.size(),
		"redo_depth": _redo.size(),
		"random_seed": random_seed,
		"gate_valid": validation.valid,
		"gate_errors": validation.errors,
		"authority_pending": validation.pending_authority,
	}

# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

func log_event(level: String, text: String) -> void:
	var event := {
		"seq": _event_seq,
		"time": Time.get_time_string_from_system(),
		"level": level,
		"text": text,
		"state": run_state,
	}
	_event_seq += 1
	events.append(event)
	if events.size() > 256:
		events.pop_front()
	emit_signal("event_logged", event)

func recent_events(count: int) -> Array:
	if count <= 0:
		return []
	return events.slice(maxi(0, events.size() - count))

# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

func _index_of(object_id: int) -> int:
	for i in obstacles.size():
		if int(obstacles[i].object_id) == object_id:
			return i
	return -1

func _validate_size(kind: String, size: Vector3) -> String:
	if not KIND_SIZE_LIMITS.has(kind):
		return "未知地质体类型: " + kind
	var limits: Array = KIND_SIZE_LIMITS[kind]
	var axes := ["X", "Y", "Z"]
	var values := [size.x, size.y, size.z]
	for i in 3:
		var low := float(limits[i][0])
		var high := float(limits[i][1])
		if float(values[i]) < low - 0.000001 or float(values[i]) > high + 0.000001:
			return "%s 的 %s 尺寸 %.3fm 超出允许范围 %.2f–%.2fm" % [kind_label(kind), axes[i], float(values[i]), low, high]
	return ""

func _validate_position(position: Vector3) -> String:
	if absf(position.x) > CUBE_HALF + 0.000000001 or absf(position.y) > CUBE_HALF + 0.000000001 or absf(position.z) > CUBE_HALF + 0.000000001:
		return "位置超出工作立方体（中心须在 ±15m 内，当前 %s）" % str(position)
	return ""

func _reject(reason: String) -> Dictionary:
	log_event("警示", "编辑被拒绝: " + reason)
	return {"ok": false, "reason": reason, "errors": [reason]}

func _push_undo(previous: String) -> void:
	_undo.append(previous)
	while _undo.size() > UNDO_CAPACITY:
		_undo.pop_front()
	_redo.clear()

func _layout_dict() -> Dictionary:
	var packed_obstacles: Array = []
	for obstacle in obstacles:
		packed_obstacles.append({
			"object_id": int(obstacle.object_id),
			"kind": String(obstacle.kind),
			"position": {"x": float(obstacle.position.x), "y": float(obstacle.position.y), "z": float(obstacle.position.z)},
			"rotation_deg": {"x": float(obstacle.rotation_deg.x), "y": float(obstacle.rotation_deg.y), "z": float(obstacle.rotation_deg.z)},
			"size": {"x": float(obstacle.size.x), "y": float(obstacle.size.y), "z": float(obstacle.size.z)},
			"priority": int(obstacle.priority),
		})
	return {
		"obstacles": packed_obstacles,
		"gates": {
			"entry": {"face": String(gates.entry.face), "u": float(gates.entry.u), "v": float(gates.entry.v)},
			"exit": {"face": String(gates.exit.face), "u": float(gates.exit.u), "v": float(gates.exit.v)},
		},
	}

func _snapshot() -> String:
	return JSON.stringify(_layout_dict())

func _restore(snapshot: String) -> void:
	var parsed = JSON.parse_string(snapshot)
	if not (parsed is Dictionary):
		return
	var restored: Array = []
	for packed in parsed.get("obstacles", []):
		restored.append({
			"object_id": int(packed.object_id),
			"kind": String(packed.kind),
			"position": _vec3(packed.position),
			"rotation_deg": _vec3(packed.rotation_deg),
			"size": _vec3(packed.size),
			"priority": int(packed.priority),
		})
	obstacles = restored
	_next_id = 1
	for obstacle in obstacles:
		_next_id = maxi(_next_id, int(obstacle.object_id) + 1)
	var restored_gates = parsed.get("gates", {})
	for which in ["entry", "exit"]:
		if restored_gates.has(which):
			gates[which] = {
				"face": String(restored_gates[which].face),
				"u": float(restored_gates[which].u),
				"v": float(restored_gates[which].v),
			}
	if selected_id != -1 and obstacle_by_id(selected_id).is_empty():
		selected_id = -1
		emit_signal("selection_changed", -1)

func _vec3(data: Dictionary) -> Vector3:
	return Vector3(float(data.get("x", 0.0)), float(data.get("y", 0.0)), float(data.get("z", 0.0)))

## Canonical JSON serialisation (sorted object keys, fixed float formatting).
func _canon(value) -> String:
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
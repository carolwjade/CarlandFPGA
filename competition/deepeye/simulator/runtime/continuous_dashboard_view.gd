extends RefCounted
## Display only. Never writes telemetry, intents, clocks or motion state.

const HOST_ABI := "DEEPEYE-CONTINUOUS-HOST-801-v1"
const MAX_AGE_MS := 3000
var _identity := ""
var _last_seq := -1
var _terminal: Dictionary = {}

static func finite(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value))

static func integer(value: Variant) -> bool:
	return finite(value) and float(value) == floor(float(value))

static func numeric(value: Variant, digits: int = 3) -> String:
	if not finite(value): return "—"
	return ("%.*f" % [digits,float(value)]) if digits > 0 else str(int(value))

static func text(value: Variant) -> String:
	if not value is String or value.is_empty(): return "—"
	return value.replace("\n"," ").replace("\r"," ").substr(0,96)

static func values(value: Variant, size: int, digits: int = 3) -> String:
	if not value is Array or value.size() != size: return "—"
	var parts: Array[String] = []
	for v: Variant in value: parts.append(numeric(v,digits))
	return " / ".join(parts)

static func counts(value: Variant) -> String:
	if not value is Array or value.size() != 4: return "—"
	var parts: Array[String] = []
	for v: Variant in value:
		parts.append(str(int(v)) if integer(v) and v >= 0 and v <= 4095 else "—")
	return " / ".join(parts)

static func dictionary(value: Variant) -> Dictionary:
	return value if value is Dictionary else {}

static func take(telemetry: Dictionary, key: String, fallback: Variant = null) -> Variant:
	return telemetry[key] if telemetry.has(key) else fallback

static func phase_name(phase: Variant, complete: bool, fault: String) -> String:
	if complete: return "已完成"
	if not fault.is_empty(): return "已停止"
	return {"INITIAL_OUTSIDE":"准备","ENTRY_CROSSING":"钻入","INSIDE":"钻进","EXIT_CROSSING":"钻出","ARRIVED":"已停止"}.get(phase,"准备")

static func angles(q: Variant) -> Array:
	if not q is Array or q.size() != 4: return [null,null]
	var norm := 0.0
	for v: Variant in q:
		if not finite(v): return [null,null]
		norm += float(v)*float(v)
	if absf(norm-1.0) > 0.001: return [null,null]
	var forward := Vector3(2.0*(q[0]*q[2]+q[3]*q[1]),2.0*(q[1]*q[2]-q[3]*q[0]),1.0-2.0*(q[0]*q[0]+q[1]*q[1]))
	return [rad_to_deg(atan2(forward.x,forward.z)),rad_to_deg(atan2(forward.y,Vector2(forward.x,forward.z).length()))]

func update(epoch: String, operation: String, raw_host: Dictionary, native: Dictionary, now_ms: int, metrics: Dictionary = {}, local_fault: bool = false) -> Dictionary:
	var key := epoch + "\n" + operation
	if key != _identity:
		_identity = key
		_last_seq = -1
		_terminal.clear()
	var valid: bool = raw_host.get("abi") == HOST_ABI and raw_host.get("world_epoch") == epoch and integer(raw_host.get("status_seq")) and int(raw_host.get("status_seq",-1)) >= _last_seq and integer(raw_host.get("updated_unix_ms"))
	if not operation.is_empty(): valid = valid and raw_host.get("operation_id") == operation
	var fault: String = str(native.get("fault",""))
	var terminal_native: bool = native.get("phase") == "ARRIVED" and finite(native.get("speed_m_s")) and float(native.speed_m_s) == 0.0 and fault in ["","operator_stop"]
	if native.has("world_epoch") and native.world_epoch != epoch: terminal_native = false
	if local_fault: terminal_native = false
	var board: Dictionary = dictionary(raw_host.get("board"))
	var acknowledged: bool = board.get("stop_acknowledged") == true
	var terminal_host: bool = valid and not operation.is_empty() and raw_host.get("complete") == true and acknowledged and not raw_host.get("failure",false)
	if (not raw_host.is_empty() and not terminal_host) or not terminal_native:
		_terminal.clear()
	if terminal_native and terminal_host:
		if _terminal.is_empty() or int(raw_host.status_seq) > int(_terminal.host.status_seq):
			_terminal = {"host":raw_host.duplicate(true),"native":native.duplicate(true),"metrics":metrics.duplicate(true)}
	if valid: _last_seq = int(raw_host.status_seq)
	var age: int = now_ms-int(raw_host.updated_unix_ms) if valid else MAX_AGE_MS+1
	var fresh: bool = valid and age >= -1000 and age <= MAX_AGE_MS and raw_host.get("connected") == true
	var complete: bool = terminal_native and not _terminal.is_empty()
	var host: Dictionary = _terminal.host.duplicate(true) if complete else (raw_host.duplicate(true) if fresh else {})
	var display_native: Dictionary = _terminal.native.duplicate(true) if complete else native.duplicate(true)
	var display_metrics: Dictionary = _terminal.metrics.duplicate(true) if complete else metrics.duplicate(true)
	var connection := "已结束 · 实板已停止" if complete else ("在线" if fresh else "数据中断")
	if host.is_empty() and native.is_empty(): connection = "准备"
	return {"host":host,"native":display_native,"fresh":fresh and not complete,"complete":complete,"connection":connection,
		"state":phase_name(display_native.get("phase"),complete,fault),"rows":make_rows(host,display_native,display_metrics),
		"original_host_updated_unix_ms":host.get("updated_unix_ms")}

static func make_rows(host: Dictionary, native: Dictionary, metrics: Dictionary) -> Dictionary:
	var t: Dictionary = dictionary(host.get("telemetry"))
	var source: Dictionary = dictionary(host.get("source"))
	var ai: Dictionary = dictionary(host.get("ai"))
	var rows: Dictionary = {}
	var orientation := angles(native.get("orientation_xyzw"))
	rows.motion = "实际 %s m/s   目标 %s m/s\nXYZ  %s m\n航向 %s°   俯仰 %s°" % [numeric(native.get("speed_m_s"),4),numeric(native.get("target_speed_m_s"),4),values(native.get("position_m"),3,3),numeric(orientation[0],2),numeric(orientation[1],2)]
	var physical: Variant = take(t,"sensor_values")
	var units: Variant = take(t,"sensor_units")
	var feature_parts: Array[String] = []
	for lane in range(4):
		var val: Variant = physical[lane] if physical is Array and physical.size()==4 else null
		var unit_name: String = text(units[lane]) if units is Array and units.size()==4 else "—"
		feature_parts.append("C%d  %s%s" % [lane,numeric(val,4),(" "+unit_name) if finite(val) and unit_name!="—" else ""])
	rows.source = "%s\n12-bit  %s\n采样 #%s   源龄 %s ms" % ["  ·  ".join(feature_parts),counts(take(t,"source_counts",source.get("channel_counts"))),numeric(take(t,"sample_number",source.get("sample_count")),0),numeric(take(t,"source_age_ms"),1)]
	var modes: Variant = take(t,"codec_modes")
	var codec := "—"
	if modes is Array:
		var names: Array[String] = []
		for mode: Variant in modes: names.append(text(mode))
		codec = " / ".join(names)
	elif modes is String: codec = text(modes)
	var lossless: Variant = take(t,"lossless_match")
	var match_text := "一致" if lossless == true else ("不一致" if lossless == false else "—")
	rows.codec = "E4 %s B   载荷 %s B   采样值 %s B\n编码 %s\n无损匹配 %s   值压缩比 %s" % [numeric(take(t,"wire_bytes",source.get("e4_bytes")),0),numeric(take(t,"payload_bytes"),0),numeric(take(t,"raw_baseline_bytes"),0),codec,match_text,numeric(take(t,"compression_ratio"),3)]
	rows.ai = "风险 %s   不确定度 %s\n方向 %s\n限速 %s m/s   避让 %s 次" % [numeric(take(t,"ai_risk",ai.get("risk")),4),numeric(take(t,"ai_uncertainty"),4),values(take(t,"ai_direction_world"),3,3),numeric(take(t,"ai_speed_limit_m_s"),4),numeric(take(t,"avoidance_count"),0)]
	var gate_state: String = text(take(t,"gate_control_state"))
	var gate_label: String = {"TRACKING_REFERENCE":"门前对准","YIELD_TO_OBSERVED_AVOIDANCE":"避障优先","READY":"对准","AVAILABLE":"进近","UNSOLVED":"需调整"}.get(gate_state,"—")
	rows.gate = "%s   剩余 %s m   所需 %s m\n孔径余量 %s m" % [gate_label,numeric(take(t,"gate_remaining_m"),3),numeric(take(t,"gate_required_m"),3),numeric(take(t,"gate_projection_margin_m"),4)]
	rows.board = "指令  速度 %s   偏航 %s   俯仰 %s\n高电平 %s μs\n周期 %s μs\n时钟 %s MHz   PC指令 #%s" % [numeric(take(t,"command_speed_code"),0),numeric(take(t,"command_yaw_q"),0),numeric(take(t,"command_pitch_q"),0),values(take(t,"pwm_high_us"),3,2),values(take(t,"pwm_period_us"),3,2),numeric(float(t.fabric_clock_hz)/1000000.0 if finite(t.get("fabric_clock_hz")) else null,2),numeric(host.get("pc_command_seq"),0)]
	rows.latency = "采样→解码 %s ms   AI计算 %s ms\n控制往返 %s ms   采样→控制受理 %s ms" % [numeric(take(t,"sample_to_decode_ms"),2),numeric(take(t,"ai_compute_ms"),2),numeric(take(t,"board_roundtrip_ms"),2),numeric(take(t,"sample_to_motion_ms"),2)]
	rows.channel = "行程 %s m   通道长度 %s m\n通道直径 %s m" % [numeric(metrics.get("travelled_m"),3),numeric(metrics.get("channel_length_m"),3),numeric(metrics.get("channel_diameter_m"),3)]
	return rows

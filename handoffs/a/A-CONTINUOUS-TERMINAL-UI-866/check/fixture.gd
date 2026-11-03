extends RefCounted
class TextStub extends RefCounted:
	var text := ""
class MainStub extends RefCounted:
	var native: Dictionary
	func read_continuous_live_state() -> Dictionary:return native
var _labels: Dictionary={}
var _main=MainStub.new()
var _bound=true
var host_fixture: Dictionary={}
var _requested_speed=.185
var _latched_initial_speed=.1
var _initial_speed_latched=true
var _terminal_complete_observed=false
var _requested_paused=false
var _intent_seq=19
var _stop_latched=false
var _fatal=""
var _pending_text: String="等待确认"
var _source_objects=2
var _source_pieces=2
func _init() -> void:
	for key in ["speed_request","speed_title","connection","motion","source","board","pending","note"]:_labels[key]=TextStub.new()
func _host_status() -> Dictionary:return host_fixture
func _fit_panel() -> void:pass
func _safe_text(value) -> String:return str(value)
static func finite_number(value) -> bool:return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value))
static func integer_number(value) -> bool:return finite_number(value) and floor(float(value))==float(value)
func _refresh_status() -> void:
	if _labels.is_empty():
		return
	_labels.speed_request.text = "%.3f m/s" % _requested_speed
	var native: Dictionary = _main.read_continuous_live_state() if _bound else {}
	var host := _host_status()
	var fresh: bool = not host.is_empty() and host.get("connected",false) == true
	if fresh and host.get("initial_speed_latched",false) == true:
		_initial_speed_latched = true
		if finite_number(host.get("latched_initial_speed_m_s")):
			_latched_initial_speed = float(host.latched_initial_speed_m_s)
	_labels.speed_title.text = "下次初始" if _initial_speed_latched else "初始速度"
	var board: Dictionary = host.get("board",{}) if fresh and host.get("board") is Dictionary else {}
	_labels.connection.text = "Root：%s  |  实板：%s" % ["已连接" if fresh else "未连接 / 等待新状态","已连接" if board.get("connected",false) == true else "未连接 / 等待"]
	var actual := "等待原生就绪"
	var phase := "等待开始"
	# ready=false after a planned STOP does not erase actual terminal readback.
	if not native.is_empty():
		if finite_number(native.get("speed_m_s")):
			actual = "%.4f m/s" % float(native.speed_m_s)
		phase = _safe_text(native.get("phase"))
	_labels.motion.text = "本次初始设置：%.3f m/s%s\n当前：%s（PC AI / 实板）  |  阶段：%s" % [_latched_initial_speed if _initial_speed_latched else _requested_speed,"（暂停）" if _requested_paused else "",actual,phase]
	var source: Dictionary = host.get("source",{}) if fresh and host.get("source") is Dictionary else {}
	var counts := "等待"
	if source.get("channel_counts") is Array and source.channel_counts.size() == 4:
		var valid := true
		var values: Array[String] = []
		for number in source.channel_counts:
			if number == null: values.append("—")
			elif integer_number(number) and number >= 0 and number <= 4095: values.append(str(int(number)))
			else: valid = false
		if valid: counts = " / ".join(values)
	_labels.source.text = "源采样：%s  |  C0 / C1 / C2 / C3：%s\n编码上传：%s B  /  还原：%s  /  模式：%s" % [_safe_text(source.get("sample_count")),counts,_safe_text(source.get("e4_bytes")),_safe_text(source.get("raw_bytes")),_safe_text(source.get("compressed_bytes"))]
	var ai: Dictionary = host.get("ai",{}) if fresh and host.get("ai") is Dictionary else {}
	_labels.board.text = "板卡 PWM：%s  |  AI 风险：%s  /  方向：%s" % [_safe_text(board.get("pwm")) if board.get("connected",false) == true else "等待",_safe_text(ai.get("risk")),_safe_text(ai.get("direction"))]
	var pending := _pending_text
	var operator: Dictionary = host.get("operator",{}) if fresh and host.get("operator") is Dictionary else {}
	if integer_number(operator.get("ack_seq")) and int(operator.ack_seq) == _intent_seq and _intent_seq > 0:
		if operator.get("state") == "applied":
			pending = "Root 已确认请求 #%d；实际速度见原生读数。" % _intent_seq
		elif operator.get("state") in ["preference_saved","next_initial_stored"]:
			pending = "下次初始速度已保存；本次继续由 PC AI / 实板控制。"
		elif operator.get("state") == "failed":
			pending = "Root 报告请求 #%d 失败：%s" % [_intent_seq,_safe_text(operator.get("detail"))]
	if _stop_latched:
		pending = "已请求停止；等待 Root 实板 STOP 回执。"
		if board.get("stop_acknowledged",false) == true and operator.get("state") == "applied" and operator.get("ack_seq") == _intent_seq:
			pending = "Root 报告实板 STOP 已确认。此场景不再重启。"
	var native_fault := str(native.get("fault",""))
	var terminal_arrived: bool = native.get("phase") == "ARRIVED" and native_fault in ["","operator_stop"]
	if terminal_arrived and fresh and host.get("complete",false) == true and board.get("stop_acknowledged",false) == true:
		_terminal_complete_observed = true
	# Retain an actually observed final receipt after the host has exited and
	# live telemetry ages out. This flag is display-only and never drives motion.
	var terminal_complete: bool = terminal_arrived and _terminal_complete_observed
	if terminal_complete:
		pending = "完整出圈已完成；实板STOP已确认"
	if not native_fault.is_empty() and not (terminal_complete and native_fault == "operator_stop"):
		pending = "原生保护停止：%s；实板状态由 Root 单独确认。" % _safe_text(native.fault)
	if not _fatal.is_empty():
		pending = "交接失败：%s。保留现场，由 Root 处理。" % _safe_text(_fatal)
	_labels.pending.text = pending
	_labels.note.text = "模拟传感器 → 实板编码上传 → PC AI → 实板控制 → 虚拟钻头（%d 障碍 / %d 源体）" % [_source_objects,_source_pieces] if _bound else "布局未冻结；源几何为名义工程包络，非精确网格 / PDE 合格结果。G03 / all29：not_run"
	_fit_panel()

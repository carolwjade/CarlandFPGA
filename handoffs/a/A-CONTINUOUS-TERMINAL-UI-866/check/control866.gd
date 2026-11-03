extends SceneTree
const Before=preload("res://fixture_before.gd")
const After=preload("res://fixture.gd")
func _initialize() -> void:
	var actual: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://actual.json"))
	var old=Before.new();old._main.native=actual.native;old.host_fixture=actual.host
	old._refresh_status()
	var fixed=After.new();fixed._main.native=actual.native;fixed.host_fixture=actual.host
	fixed._refresh_status()
	var green: bool=fixed._labels.motion.text.contains("ARRIVED") and fixed._labels.motion.text.contains("0.0000 m/s") and fixed._labels.pending.text=="完整出圈已完成；实板STOP已确认"
	var old_red: bool=old._labels.motion.text.contains("等待原生就绪") and old._labels.pending.text.contains("原生保护停止：operator_stop")
	var completed_text: String=fixed._labels.pending.text
	fixed.host_fixture={};fixed._refresh_status()
	var stale_keeps_known_terminal: bool=fixed._labels.pending.text==completed_text
	var missing_ack=After.new();missing_ack._main.native=actual.native;missing_ack.host_fixture=actual.host.duplicate(true)
	missing_ack.host_fixture.board.stop_acknowledged=false;missing_ack._refresh_status()
	var ack_required: bool=missing_ack._labels.pending.text!=completed_text
	fixed._main.native=actual.native.duplicate(true);fixed._main.native.fault="volume_guard_rejected";fixed._refresh_status()
	var real_fault_visible: bool=fixed._labels.pending.text.contains("volume_guard_rejected") and fixed._labels.pending.text!=completed_text
	var passed: bool=old_red and green and stale_keeps_known_terminal and ack_required and real_fault_visible
	print(JSON.stringify({"passed":passed,"actual835_old_red":old_red,"actual835_fixed_green":green,"verified_terminal_survives_stale_host":stale_keeps_known_terminal,"board_ack_required":ack_required,"genuine_other_fault_visible":real_fault_visible,"before_motion":old._labels.motion.text,"before_pending":old._labels.pending.text,"after_pending":completed_text,"scope":"one isolated actual835 display control; RefCounted label stubs, no UI/motion/board","formal_all29":"not_run"}))
	quit(0 if passed else 1)

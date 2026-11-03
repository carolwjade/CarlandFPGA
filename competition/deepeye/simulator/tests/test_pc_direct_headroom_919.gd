extends SceneTree

var failures := 0
var checks := 0

class HeadroomRunner:
	extends "res://runtime/continuous_live_runner.gd"
	func _rpc_state() -> Dictionary:
		return {"phase":"ENTERED","fault":"","running":true,"deadline_usec":str(_deadline_us),"target_speed_m_s":_target_speed,"direct":_direct.public_fields()}

func check(value: bool, message: String) -> void:
	checks+=1
	if not value:
		failures+=1
		printerr(message)

func wire(command: Dictionary) -> Dictionary:
	var text := JSON.stringify(command)
	return {"abi":"unused","token":"unused","seq":1,"op":"apply_pc_direct","command_json":text,"command_sha256":text.sha256_text()}

func _init() -> void:
	call_deferred("run")

func run() -> void:
	var policy=load("res://runtime/live_pc_direct_admission.gd").new("HEADROOM919")
	var stamp := Time.get_ticks_usec()
	var source_at := "43935620505597"
	var snapshot := {"tick_usec":str(stamp),"revision":"0","position_m":[1,2,3],"orientation_xyzw":[0,0,0,1]}
	var fields := {"world_epoch":"HEADROOM919","source_witness":policy.make_snapshot(snapshot,stamp),"board_sense_seq":290,"board_receipt_sha256":"a".repeat(64),"board_frame_sha256":"b".repeat(64),"source_record_sha256":"c".repeat(64),"source_acquisition_qpc_ns":source_at,"source_segment_id":"native-0","source_position_m":[1,2,3],"source_orientation_xyzw":[0,0,0,1],"board_binding":{"boot_id":"1dc765dc-6e81-412d-b350-9f6691749e48","build_id":"d".repeat(32),"request_hash":"e".repeat(64)}}
	check(policy.observe(fields,stamp).ok,"source registers")
	var command := {"abi":"DEEPEYE-LIVE-PC-DIRECT-COMMAND-884-v1","mode":"PC_DIRECT","world_epoch":"HEADROOM919","profile":"fast_9600","command_seq":649,"first_send_qpc_ns":str(int(source_at)+1000000000),"source_acquisition_qpc_ns":source_at,"board_sense_seq":290,"board_receipt_sha256":fields.board_receipt_sha256,"board_frame_sha256":fields.board_frame_sha256,"source_record_sha256":fields.source_record_sha256,"ai_result_sha256":"f".repeat(64),"speed_code":2,"yaw_q":-548,"pitch_q":0,"ttl_ms":3000,"native_deadline_usec":str(stamp+1400000)}
	var first := wire(command)
	check(policy.admit(first.command_json,first.command_sha256,stamp,false).ok,"original command accepted")
	var accepted: Dictionary=policy.public_fields().duplicate(true)
	command.command_seq=650
	var late := wire(command)
	var rejected: Dictionary=policy.admit(late.command_json,late.command_sha256,stamp+1324543,false)
	check(not rejected.ok and rejected.get("reason")=="pc_admission_headroom" and rejected.get("admission_applied")==false,"late valid update is explicit no-admission")
	check(policy.public_fields()==accepted,"late rejection preserves command649 identity")
	command.native_deadline_usec=str(stamp+1600000)
	late=wire(command)
	check(policy.admit(late.command_json,late.command_sha256,stamp+1324543,false).get("reason")=="pc_original_observation_deadline","future ceiling remains fatal")
	command.native_deadline_usec=str(stamp+1400000)
	command.yaw_q=15000
	late=wire(command)
	check(policy.admit(late.command_json,late.command_sha256,stamp+1324543,false).get("reason")=="pc_combined_curvature_or_pause","malformed motion is never hidden by headroom")
	command.yaw_q=-548
	command.native_deadline_usec=str(Time.get_ticks_usec()+80000)
	var runner := HeadroomRunner.new()
	runner._admission_mode="PC_DIRECT"
	runner._initial_published=true
	runner._phase="ENTERED"
	runner._direct=policy
	runner._target_speed=0.025
	runner._deadline_us=stamp+1400000
	var response: Dictionary=runner.apply_pc_direct(wire(command))
	check(not response.ok and response.get("reason")=="pc_admission_headroom" and response.get("admission_applied")==false and response.get("state",{}).get("deadline_usec")==str(stamp+1400000),"runner returns held actual state on known no-admission")
	check(runner._target_speed==0.025 and runner._deadline_us==stamp+1400000 and policy.public_fields()==accepted,"rejection neither changes motion nor extends grant")
	runner.free()
	print(JSON.stringify({"new_headroom_controls":checks,"failures":failures,"actual_board":false,"old_suites_rerun":false}))
	quit(2 if failures else 0)

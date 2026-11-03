extends SceneTree

const HELPER := "res://runtime/live_pc_direct_admission.gd"
var checks := 0
var failed := false

class ArrivedRunner:
	extends "res://runtime/continuous_live_runner.gd"
	func _rpc_state() -> Dictionary:
		return {"phase":"ARRIVED","fault":"","running":false,"speed_m_s":0.0}

func _init() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failed=true
		printerr("PC_DIRECT_883: " + message)

func hashed(value: Dictionary) -> Array:
	var text := JSON.stringify(value)
	return [text,text.sha256_text()]

func run() -> void:
	if not FileAccess.file_exists(HELPER):
		printerr("PC_DIRECT_883: missing explicit direct admission; board PWM is the only current route")
		quit(2)
		return
	var script: Script=load(HELPER)
	check(script!=null,"admission script loads")
	var fixture_path := ProjectSettings.globalize_path("res://").path_join("../../../handoffs/a/A-CONTINUOUS-ACTUAL-835/ACTUAL_FIRST_CHAIN.json").simplify_path()
	var fixture: Array=JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	check(fixture.size()==4,"actual835 public fixture is complete")
	var source: Dictionary=fixture[1].source
	var board: Dictionary=fixture[1].actual_board.response
	var observation: Dictionary=fixture[1].public_observation
	var epoch: String=source.world_epoch
	var policy=script.new(epoch)
	var stamp := 1000000
	var snapshot := {"tick_usec":str(stamp),"revision":"0","position_m":source.position_m,"orientation_xyzw":source.orientation_xyzw}
	var witness: String=policy.make_snapshot(snapshot,stamp)
	check(witness.length()==32,"native mints an actual-pose witness")
	var fields := {"world_epoch":epoch,"source_witness":witness,"board_sense_seq":1,"board_receipt_sha256":fixture[1].actual_board.response_sha256,"board_frame_sha256":observation.board_frame_sha256,"source_record_sha256":observation.source_record_sha256,"source_acquisition_qpc_ns":source.at_qpc_ns,"source_segment_id":source.segment_id,"source_position_m":source.position_m,"source_orientation_xyzw":source.orientation_xyzw,"board_binding":{"boot_id":board.boot_id,"build_id":board.build_id,"request_hash":board.request_hash}}
	var altered: Dictionary=fields.duplicate(true)
	altered.source_position_m[0]+=0.1
	check(not policy.observe(altered,stamp+200000).ok,"foreign source pose is refused")
	check(policy.observe(fields,stamp+200000).ok,"original genuine E4 association registers")
	check(not policy.observe(fields,stamp+200001).ok,"source replay is refused")
	var newer: Dictionary=fields.duplicate(true)
	newer.board_sense_seq=2
	newer.source_witness=policy.make_snapshot(snapshot,stamp+200010)
	check(policy.observe(newer,stamp+200020).ok,"new increasing observation is registered")
	var command := {"abi":"DEEPEYE-LIVE-PC-DIRECT-COMMAND-884-v1","mode":"PC_DIRECT","world_epoch":epoch,"profile":"fast_9600","command_seq":1,"first_send_qpc_ns":str(int(source.at_qpc_ns)+300000000),"source_acquisition_qpc_ns":source.at_qpc_ns,"board_sense_seq":1,"board_receipt_sha256":fields.board_receipt_sha256,"board_frame_sha256":fields.board_frame_sha256,"source_record_sha256":fields.source_record_sha256,"ai_result_sha256":"a".repeat(64),"speed_code":2,"yaw_q":0,"pitch_q":0,"ttl_ms":3000,"native_deadline_usec":str(stamp+1400000)}
	var wire := hashed(command)
	var accepted: Dictionary=policy.admit(wire[0],wire[1],stamp+300000,false)
	check(accepted.ok and accepted.speed_m_s==0.025,"older still-fresh original observation drives a genuine host target")
	check(accepted.native_deadline_usec<=stamp+1500000,"original native acquisition caps command expiry")
	var previous: Dictionary=policy.public_fields().duplicate(true)
	check(not policy.admit(wire[0],wire[1],stamp+300001,false).ok,"duplicate command never renews deadline")
	check(policy.public_fields()==previous,"rejected duplicate cannot mutate actual command identity")
	command.command_seq=2
	command.speed_code=3
	wire=hashed(command)
	var three: Dictionary=policy.admit(wire[0],wire[1],stamp+300005,false)
	check(three.ok and three.speed_m_s==0.0375,"FAST target matches existing exact code/80 client mapping")
	command.command_seq=3
	command.native_deadline_usec=str(stamp+1600000)
	wire=hashed(command)
	check(not policy.admit(wire[0],wire[1],stamp+300010,false).ok,"requested deadline cannot exceed original observation ceiling")
	command.native_deadline_usec=str(stamp+1400000)
	command.world_epoch="FOREIGN"
	wire=hashed(command)
	check(not policy.admit(wire[0],wire[1],stamp+300020,false).ok,"foreign epoch refused")
	command.world_epoch=epoch
	command.yaw_q=15000
	wire=hashed(command)
	check(not policy.admit(wire[0],wire[1],stamp+300030,false).ok,"unsafe combined curvature refused")
	command.yaw_q=0
	command.speed_code=0
	wire=hashed(command)
	check(policy.admit(wire[0],wire[1],stamp+300040,true).ok,"explicit zero host pause does not fabricate PWM")
	command.command_seq=4
	command.speed_code=2
	wire=hashed(command)
	check(not policy.admit(wire[0],wire[1],stamp+1600000,false).ok,"old observation cannot be made fresh by heartbeat")
	var runner_script: Script=load("res://runtime/continuous_live_runner.gd")
	var runner=runner_script.new()
	check(not runner.apply_pc_direct({}).ok,"default board-only instance excludes direct admission")
	var dummy := Node3D.new()
	root.add_child(dummy)
	runner._drill=dummy
	root.add_child(runner)
	runner.set_physics_process(false)
	var default_state: Dictionary=runner.state()
	var original_keys := ["ready","tick_usec","read_now_usec","revision","position_m","orientation_xyzw","speed_m_s","target_speed_m_s","yaw_curvature_per_m","pitch_curvature_per_m","phase","history","fault","running","board_request_seq","board_receipt_sha256","deadline_usec","operator_request","formal_acceptance","abi"]
	check(default_state.size()==original_keys.size(),"default BOARD state has no direct fields")
	for key in original_keys:check(default_state.has(key),"default822 original state key: "+key)
	runner.free()
	dummy.free()
	var bootstrap: Script=load("res://runtime/continuous_demo_bootstrap.gd")
	check(bootstrap!=null,"dual-mode bootstrap parser loads")
	var terminal := ArrivedRunner.new()
	terminal._admission_mode="PC_DIRECT"
	terminal._initial_published=true
	terminal._phase="ARRIVED"
	for method in ["observe_pc","apply_pc_direct"]:
		var final: Dictionary=terminal.call(method,{})
		check(not final.ok and final.get("reason")=="already_arrived" and final.get("state",{}).get("phase")=="ARRIVED","known terminal race returns actual arrival without granting a command")
	terminal.free()
	print(JSON.stringify({"new_direct_controls":checks,"actual_board":false,"actual_UI":false,"old_suites_rerun":false,"passed":not failed}))
	quit(2 if failed else 0)

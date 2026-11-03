extends SceneTree

var checks := 0
var failed := false
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failed = true
		printerr("DASHBOARD990: " + message)
func _init() -> void:
	call_deferred("run")
func run() -> void:
	var script: Script = load("res://runtime/continuous_dashboard_view.gd")
	if script == null:
		printerr("DASHBOARD990: helper absent")
		quit(1)
		return
	var model = script.new()
	var host := {"abi":"DEEPEYE-CONTINUOUS-HOST-801-v1","world_epoch":"e","operation_id":"op","status_seq":1,"updated_unix_ms":10000,"connected":true,"complete":false,"board":{"connected":true,"stop_acknowledged":false},"telemetry":{"sensor_values":[2.3,0.02,-0.01,null],"sensor_units":["log10Ωm","log10Ωm","log10Ωm","g"],"source_counts":[3000,2000,2001,null],"sample_number":12,"ai_risk":0.4,"pwm_high_us":[1250,1260,325],"pwm_period_us":[10000,10000,10000]}}
	var native := {"phase":"INSIDE","speed_m_s":0.1875,"target_speed_m_s":0.2,"position_m":[1,2,3],"orientation_xyzw":[0,0,0,1],"fault":"","ready":true}
	var live: Dictionary = model.update("e","op",host,native,11000,{})
	check(live.fresh and not live.complete,"fresh running data")
	check("3000 / 2000 / 2001 / —" in live.rows.source,"12bit counts and null C3")
	check("—" in live.rows.codec,"missing data stays missing")
	var stale: Dictionary = model.update("e","op",host,native,15000,{})
	check(not stale.fresh and stale.host.is_empty(),"stale running host cleared")
	host.complete=true;host.board.stop_acknowledged=true;host.status_seq=2
	native.phase="ARRIVED";native.speed_m_s=0.;native.fault="operator_stop";native.ready=false
	var done: Dictionary = model.update("e","op",host,native,15000,{"travelled_m":4.2})
	check(done.complete and done.connection=="已结束 · 实板已停止","real terminal becomes ended")
	var cached: Dictionary = model.update("e","op",{},native,50000,{})
	check(cached.complete and "3000 / 2000 / 2001 / —" in cached.rows.source,"terminal retains values")
	check(cached.host.updated_unix_ms==10000 and not cached.fresh,"original time never refreshed")
	check(not model.update("e","op",host,native,50000,{},true).complete,"local failure invalidates completion")
	model.update("e","op",host,native,15000,{})
	var foreign := host.duplicate(true);foreign.operation_id="other"
	check(not model.update("e","op",foreign,native,50000,{}).complete,"foreign op clears terminal")
	model.update("e","op",host,native,15000,{})
	native.fault="workspace_or_aperture"
	check(not model.update("e","op",{},native,50000,{}).complete,"genuine fault clears cache")
	native.fault="operator_stop";host.board.stop_acknowledged=false
	check(not model.update("e","op",host,native,50000,{}).complete,"unknown STOP cannot complete")
	check(not model.update("new","newop",{},native,50000,{}).complete,"new run clears cache")
	print(JSON.stringify({"checks":checks,"passed":not failed,"source_model_board_ui_executed":false}))
	quit(1 if failed else 0)

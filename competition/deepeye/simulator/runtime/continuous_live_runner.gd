extends Node
## Default-off, independent live demonstration. Root supplies actual PWM target.
## No hidden geometry is returned by public state/RPC. No span-boundary stop.
const Law = preload("res://runtime/canonical_live_motion.gd")
const Guard = preload("res://runtime/continuous_volume_guard.gd")
const DirectAdmission = preload("res://runtime/live_pc_direct_admission.gd")
const ABI := "DEEPEYE-CONTINUOUS-NATIVE-794-v1"
const LIVE_LAYER := 1073741824
const MAX_LINE := 8192
signal safety_fault(reason: String)
signal operator_stop_requested(reason: String)

var _main: Node3D
var _drill: Node3D
var _server := TCPServer.new()
var _peer: StreamPeerTCP
var _token := ""
var _rx := PackedByteArray()
var _tx := PackedByteArray()
var _hello := false
var _seq := 0
var _board_seq := 0
var _receipt := ""
var _deadline_us := 0
var _last_wall_us := 0
var _accepted_tick_us := 0
var _revision := 0
var _speed := 0.0
var _target_speed := 0.0
var _ky := 0.0
var _kp := 0.0
var _pose := Transform3D.IDENTITY
var _entry: Dictionary
var _exit_gate: Dictionary
var _entered := false
var _exiting := false
var _phase := "INITIAL_OUTSIDE"
var _history: Array = ["INITIAL_OUTSIDE"]
var _fault := ""
var _running := false
var _ready_frames := 0
var _initial_published := false
var _geometry: Node3D
var _doc_generation := -1
var _lock: RefCounted
var _operator_request := ""
var _admission_mode := "BOARD_PWM"
var _direct: RefCounted

func install(main: Node3D, drill: Node3D, frozen_shapes: Array, entry: Dictionary,
		exit_gate: Dictionary, port: int, token: String, admission_mode: String="BOARD_PWM", world_epoch: String="") -> Dictionary:
	if _main != null or not is_instance_valid(main) or not is_instance_valid(drill) or token.length()<32 or token.length()>128 or port<1024 or port>65535:
		return {"ok":false,"reason":"install_arguments"}
	if not admission_mode in ["BOARD_PWM","PC_DIRECT"] or (admission_mode=="PC_DIRECT" and (world_epoch.is_empty() or world_epoch.length()>128)):
		return {"ok":false,"reason":"frozen_admission_mode_or_epoch"}
	for gate: Dictionary in [entry,exit_gate]:
		if not gate.has("center") or not gate.has("normal") or not gate.center is Vector3 or not gate.normal is Vector3 or not gate.normal in Guard.NORMALS:
			return {"ok":false,"reason":"public_gate"}
	if _server.listen(port,"127.0.0.1") != OK:return {"ok":false,"reason":"loopback_listen"}
	_main=main;_drill=drill;_token=token;_entry=entry.duplicate();_exit_gate=exit_gate.duplicate()
	_admission_mode=admission_mode
	if _admission_mode=="PC_DIRECT":_direct=DirectAdmission.new(world_epoch)
	_geometry=Node3D.new();_geometry.name="ContinuousFrozenCollision794"
	add_child(_geometry)
	for item: Dictionary in frozen_shapes:
		if not _clone_envelope(item):
			fail("frozen_shape_invalid");return {"ok":false,"reason":_fault}
	_lock=RefCounted.new()
	if not main.document._owned_attach_bridge(self) or not main.document._owned_lock_geometry(self,_lock):
		fail("document_lock");return {"ok":false,"reason":_fault}
	_doc_generation=main.document._owned_generation(self)
	main.document.stop_requested.connect(request_operator_stop)
	_pose=Transform3D(Basis(Quaternion(Vector3.BACK,-entry.normal)),entry.center+entry.normal*0.62)
	if not Guard.workspace(_pose,_entry,_exit_gate,false).ok:
		fail("initial_portal");return {"ok":false,"reason":_fault}
	# Wait for actual cloned colliders to enter physics before publishing start.
	_last_wall_us=Time.get_ticks_usec()
	set_physics_process(true)
	return {"ok":true,"abi":ABI,"port":port,"formal_acceptance":"not_run"}

func _clone_envelope(item: Dictionary) -> bool:
	if not item.get("shape") is Shape3D or not item.get("transform") is Transform3D:return false
	var shape: Shape3D=item.shape
	var pose: Transform3D=item.transform
	var size := Vector3.ZERO
	if shape is BoxShape3D:size=shape.size
	elif shape is CylinderShape3D:size=Vector3(shape.radius*2.0,shape.height,shape.radius*2.0)
	else:return false
	# Exact boxes; conservative complete casing box. Bake positive nonuniform
	# asset scale into dimensions, so physics never relies on scaled-body shapes.
	var scale := pose.basis.get_scale()
	if minf(scale.x,minf(scale.y,scale.z))<=0.0:return false
	var built := BoxShape3D.new();built.size=size*scale+Vector3.ONE*0.00001;built.margin=0.0
	var body := StaticBody3D.new();body.collision_layer=LIVE_LAYER;body.collision_mask=0
	var node := CollisionShape3D.new();node.shape=built;body.add_child(node)
	_geometry.add_child(body);body.global_transform=Transform3D(pose.basis.orthonormalized(),pose.origin)
	return true

func fail(reason: String) -> void:
	if _fault.is_empty():_fault=reason;safety_fault.emit(reason)
	_running=false;_speed=0.0

func request_operator_stop(source: String) -> void:
	# UI pause requests actual zero PWM through Root; it is not a fabricated ack.
	_operator_request="pause" if source=="human_ui" else "stop"
	operator_stop_requested.emit(_operator_request)
	if _operator_request=="stop":fail("operator_stop")

func _physics_process(_delta: float) -> void:
	var now := Time.get_ticks_usec()
	# Move FIRST on every physics frame. RPC/AI/source waits never suspend this.
	if _ready_frames<2:
		_ready_frames+=1;_last_wall_us=now
		if _ready_frames==2 and _fault.is_empty():
			var initial: Dictionary=Guard.probe(_drill.get_world_3d().direct_space_state,_pose,_pose,0.0,0.0,_entry,_exit_gate,false,LIVE_LAYER)
			if not initial.ok:fail("initial_volume_guard")
			elif not _main._continuous_pose_write(self,_pose,"0"):fail("initial_write")
			else:_initial_published=true;_accepted_tick_us=now
	elif _running and _fault.is_empty():
		if now>=_deadline_us:fail("pc_direct_observation_or_command_expired" if _admission_mode=="PC_DIRECT" else "real_board_grant_expired")
		elif now-_last_wall_us>250000:fail("native_frame_stall")
		else:
			var cursor := _last_wall_us
			while cursor<now and _fault.is_empty():
				var end := mini(now,cursor+8333)
				if not _advance(float(end-cursor)*0.000001,end):break
				cursor=end
	_last_wall_us=now
	_poll_rpc()

func _advance(seconds: float, tick: int) -> bool:
	if not is_instance_valid(_drill) or not _main._continuous_owner_valid(self,_lock,_doc_generation):
		fail("owner_or_geometry_changed");return false
	var acceleration := 0.0 if is_equal_approx(_target_speed,_speed) else (0.25 if _target_speed>_speed else -0.25)
	var ramp := absf(_target_speed-_speed)/0.25
	var dt_ns := int(round(seconds*1000000000.0))
	var ramp_ns := int(round(minf(seconds,ramp)*1000000000.0))
	var reached := _speed+acceleration*float(ramp_ns)*0.000000001
	var q := _pose.basis.get_rotation_quaternion()
	var span := {"dt_ns":str(dt_ns),"start_position_m":[_pose.origin.x,_pose.origin.y,_pose.origin.z],"start_orientation_xyzw":[q.x,q.y,q.z,q.w],"start_speed_m_s":_speed,"target_speed_m_s":reached,"acceleration_m_s2":acceleration,"ramp_ns":str(ramp_ns),"yaw_curvature_per_m":_ky,"pitch_curvature_per_m":_kp}
	var sampled: Dictionary=Law.sample_span(span,dt_ns)
	if not sampled.get("ok",false):fail("canonical_law_"+str(sampled.get("reason")));return false
	var p: Array=sampled.position_m;var rot: Array=sampled.orientation_xyzw
	var desired := Transform3D(Basis(Quaternion(rot[0],rot[1],rot[2],rot[3])),Vector3(p[0],p[1],p[2]))
	var checked: Dictionary=Guard.probe(_drill.get_world_3d().direct_space_state,_pose,desired,0.25*seconds,sqrt(_ky*_ky+_kp*_kp),_entry,_exit_gate,_entered,LIVE_LAYER)
	if not checked.ok:fail(str(checked.reason));return false
	if not _main._continuous_pose_write(self,desired,str(_revision+1)):
		fail("pose_write_rejected");return false
	_pose=desired;_speed=sampled.speed_m_s;_revision+=1;_accepted_tick_us=tick
	_update_phase()
	return true

func _update_phase() -> void:
	var inward: float=(_pose.origin-_entry.center).dot(_entry.normal)
	if not _entered:
		if inward-Guard.support(_pose,_entry.normal)<=0.0 and _phase=="INITIAL_OUTSIDE":
			_phase="ENTRY_CROSSING";_history.append(_phase)
		var wholly_inside := true
		for n: Vector3 in Guard.NORMALS:
			if _pose.origin.dot(n)-15.0+Guard.support(_pose,n,0.01)>0.0:wholly_inside=false
		if wholly_inside:
			_entered=true;_phase="INSIDE";_history.append("ENTERED")
	else:
		var outward: float=(_pose.origin-_exit_gate.center).dot(_exit_gate.normal)
		if outward+Guard.support(_pose,_exit_gate.normal)>0.0 and not _exiting:
			_exiting=true;_phase="EXIT_CROSSING";_history.append(_phase)
		if _exiting and outward-Guard.support(_pose,_exit_gate.normal)>0.0:
			if _phase!="ARRIVED":_history.append("ARRIVED")
			_phase="ARRIVED"

func state() -> Dictionary:
	# A stationary drill can still be observed at a new actual acquisition time.
	# Read the real node now; never relabel a cached physics write as a new read.
	var observed: Transform3D=_drill.global_transform
	var acquired_us := Time.get_ticks_usec()
	if _initial_published and (not _main._continuous_owner_valid(self,_lock,_doc_generation) or not observed.is_equal_approx(_pose)):
		fail("observed_pose_or_owner_changed")
	var q := observed.basis.get_rotation_quaternion()
	var value := {"abi":ABI,"ready":_initial_published and _fault.is_empty(),"tick_usec":str(acquired_us),"read_now_usec":str(Time.get_ticks_usec()),"revision":str(_revision),"position_m":[observed.origin.x,observed.origin.y,observed.origin.z],"orientation_xyzw":[q.x,q.y,q.z,q.w],"speed_m_s":_speed,"target_speed_m_s":_target_speed,"yaw_curvature_per_m":_ky,"pitch_curvature_per_m":_kp,"phase":_phase,"history":_history.duplicate(),"fault":_fault,"running":_running,"board_request_seq":_board_seq,"board_receipt_sha256":_receipt,"deadline_usec":str(_deadline_us),"operator_request":_operator_request,"formal_acceptance":"not_run"}
	if _admission_mode=="PC_DIRECT":value.merge(_direct.public_fields())
	return value

func _rpc_state() -> Dictionary:
	var value := state()
	if _admission_mode=="PC_DIRECT":value.source_witness=_direct.make_snapshot(value,Time.get_ticks_usec())
	return value

func apply_target(r: Dictionary) -> Dictionary:
	if _admission_mode!="BOARD_PWM":return {"ok":false,"reason":"admission_mode_mismatch"}
	if not _initial_published or not _fault.is_empty():return {"ok":false,"reason":"not_ready_or_fault"}
	for key in ["speed_m_s","yaw_curvature_per_m","pitch_curvature_per_m"]:
		if not Law._number(r.get(key)):return {"ok":false,"reason":"target_numeric"}
	var v: float=r.speed_m_s;var ky: float=r.yaw_curvature_per_m;var kp: float=r.pitch_curvature_per_m
	var end: int=Law._ns(r.get("native_deadline_usec"))
	var now := Time.get_ticks_usec()
	var bs=r.get("board_request_seq")
	if not (typeof(bs)==TYPE_INT or typeof(bs)==TYPE_FLOAT) or float(bs)!=floor(float(bs)) or bs<=_board_seq or bs>4294967295 or v<0.0 or v>0.25 or ky*ky+kp*kp>0.25 or (v==0.0 and (ky!=0.0 or kp!=0.0)) or end<=now+100000 or end>now+12000000:
		return {"ok":false,"reason":"target_bounds_or_real_grant"}
	var receipt=r.get("board_receipt_sha256","")
	if not receipt is String or receipt.length()!=64 or not receipt.is_valid_hex_number(false):return {"ok":false,"reason":"actual_receipt_digest"}
	_target_speed=v;_ky=ky;_kp=kp;_deadline_us=end;_board_seq=int(bs);_receipt=receipt
	_running=true;_operator_request=""
	return {"ok":true,"state":_rpc_state()}

func observe_pc(r: Dictionary) -> Dictionary:
	if _admission_mode!="PC_DIRECT":return {"ok":false,"reason":"admission_mode_mismatch"}
	if _phase=="ARRIVED":return {"ok":false,"reason":"already_arrived","state":_rpc_state()}
	if not _initial_published or not _fault.is_empty():return {"ok":false,"reason":"not_ready_or_fault"}
	if r.size()!=DirectAdmission.OBS_FIELDS.size()+4:return {"ok":false,"reason":"pc_observation_fields"}
	var fields: Dictionary={}
	for key in DirectAdmission.OBS_FIELDS:
		if not r.has(key):return {"ok":false,"reason":"pc_observation_fields"}
		fields[key]=r[key]
	var checked: Dictionary=_direct.observe(fields,Time.get_ticks_usec())
	if not checked.ok:return checked
	return {"ok":true,"state":_rpc_state()}

func apply_pc_direct(r: Dictionary, paused: bool=false) -> Dictionary:
	if _admission_mode!="PC_DIRECT":return {"ok":false,"reason":"admission_mode_mismatch"}
	if _phase=="ARRIVED":return {"ok":false,"reason":"already_arrived","state":_rpc_state()}
	if not _initial_published or not _fault.is_empty():return {"ok":false,"reason":"not_ready_or_fault"}
	if r.size()!=6 or not r.has("command_json") or not r.has("command_sha256"):return {"ok":false,"reason":"pc_command_fields"}
	var checked: Dictionary=_direct.admit(r.command_json,r.command_sha256,Time.get_ticks_usec(),paused)
	if not checked.ok:
		if checked.get("reason")=="pc_admission_headroom":checked["state"]=_rpc_state()
		return checked
	_target_speed=checked.speed_m_s;_ky=checked.yaw_curvature_per_m;_kp=checked.pitch_curvature_per_m
	_deadline_us=checked.native_deadline_usec;_running=true;_operator_request=""
	return {"ok":true,"state":_rpc_state()}

func _dispatch(r: Dictionary) -> Dictionary:
	if r.get("abi")!=ABI or r.get("token")!=_token:return {"ok":false,"reason":"identity"}
	var seq=r.get("seq")
	if not (typeof(seq)==TYPE_INT or typeof(seq)==TYPE_FLOAT) or float(seq)!=floor(float(seq)) or seq<=_seq or seq>9007199254740991:return {"ok":false,"reason":"monotonic_seq"}
	_seq=int(seq)
	if not _hello:
		if r.get("op")!="hello":return {"ok":false,"reason":"hello_required"}
		_hello=true;return {"ok":true,"state":_rpc_state()}
	match r.get("op"):
		"state":return {"ok":true,"state":_rpc_state()}
		"apply":return apply_target(r)
		"observe_pc":return observe_pc(r)
		"apply_pc_direct":return apply_pc_direct(r)
		"pause_pc_direct":return apply_pc_direct(r,true)
		"pause":
			if r.get("speed_m_s")!=0.0:return {"ok":false,"reason":"pause_requires_actual_zero_target"}
			return apply_target(r)
		"stop":
			operator_stop_requested.emit("live_rpc_stop")
			fail("operator_stop");return {"ok":true,"state":_rpc_state(),"board_stop_acknowledged":false}
	return {"ok":false,"reason":"operation"}

func _poll_rpc() -> void:
	if _peer==null:
		if _server.is_connection_available():_peer=_server.take_connection();_peer.set_no_delay(true)
		return
	_peer.poll()
	if _peer.get_status()!=StreamPeerTCP.STATUS_CONNECTED:
		fail("controller_disconnected");return
	if not _tx.is_empty():
		var sent: Array=_peer.put_partial_data(_tx.slice(0,4096))
		if sent[0]!=OK:fail("rpc_write");return
		_tx=_tx.slice(sent[1]);return
	var available := _peer.get_available_bytes()
	if available>0:
		if _rx.size()+available>MAX_LINE:fail("rpc_input_bound");return
		var got: Array=_peer.get_partial_data(available)
		if got[0]!=OK:fail("rpc_read");return
		_rx.append_array(got[1])
	var newline := _rx.find(10)
	if newline<0:return
	var raw := _rx.slice(0,newline);_rx=_rx.slice(newline+1)
	var decoded=JSON.parse_string(raw.get_string_from_utf8())
	if not decoded is Dictionary:fail("rpc_json");return
	var result: Dictionary=_dispatch(decoded)
	result["seq"]=decoded.get("seq");result["abi"]=ABI
	_tx=(JSON.stringify(result)+"\n").to_utf8_buffer()
	if _tx.size()>16384:fail("rpc_output_bound")

func _exit_tree() -> void:
	_server.stop()
	if _peer!=null:_peer.disconnect_from_host()

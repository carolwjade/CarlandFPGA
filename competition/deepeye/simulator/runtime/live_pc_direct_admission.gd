extends RefCounted
## Explicit live PC_DIRECT admission. No geometry, motion writer or board IO.
const COMMAND_ABI := "DEEPEYE-LIVE-PC-DIRECT-COMMAND-884-v1"
const MAX_AGE_US := 1500000
const MAX_TTL_MS := 3000
const FAST_ROM := [0,128234,512938,1154111,2051753,3205865,4616446,6283496,8207015,10387004,12823462,15516389,18465785,21671651,25133986,28852790,32828063,37059806,41548017,46292698,51293849]
const OBS_FIELDS := ["world_epoch","source_witness","board_sense_seq","board_receipt_sha256","board_frame_sha256","source_record_sha256","source_acquisition_qpc_ns","source_segment_id","source_position_m","source_orientation_xyzw","board_binding"]
const COMMAND_FIELDS := ["abi","mode","world_epoch","profile","command_seq","first_send_qpc_ns","source_acquisition_qpc_ns","board_sense_seq","board_receipt_sha256","board_frame_sha256","source_record_sha256","ai_result_sha256","speed_code","yaw_q","pitch_q","ttl_ms","native_deadline_usec"]

var _epoch: String
var _witnesses: Dictionary={}
var _observations: Dictionary={}
var _binding: Dictionary={}
var _max_sense := 0
var _latest: Dictionary={}
var _command_seq := 0
var _command_sha := ""

func _init(epoch: String) -> void:
	_epoch=epoch

static func _bad(reason: String) -> Dictionary:
	return {"ok":false,"reason":reason}

static func _integer(value: Variant, low: int, high: int) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)==floor(float(value)) and value>=low and value<=high

static func _time(value: Variant) -> int:
	if not value is String or not value.is_valid_int():return -1
	var parsed: int=value.to_int()
	return parsed if parsed>=0 and str(parsed)==value else -1

static func _hex(value: Variant, size: int=64) -> bool:
	return value is String and value.length()==size and value.is_valid_hex_number(false)

static func _keys(value: Dictionary, expected: Array) -> bool:
	if value.size()!=expected.size():return false
	for key in expected:
		if not value.has(key):return false
	return true

static func _vector(value: Variant, size: int) -> bool:
	if not value is Array or value.size()!=size:return false
	for item in value:
		if not typeof(item) in [TYPE_INT,TYPE_FLOAT] or not is_finite(float(item)):return false
	return true

static func _same(a: Array, b: Array) -> bool:
	if a.size()!=b.size():return false
	for i in a.size():
		if absf(float(a[i])-float(b[i]))>0.000001:return false
	return true

func _prune(now: int) -> void:
	# Only expired credentials are dropped; there is no total operation budget.
	for key in _witnesses.keys():
		if now-int(_witnesses[key].tick)>MAX_AGE_US:_witnesses.erase(key)
	for key in _observations.keys():
		if now-int(_observations[key].native_tick)>=MAX_AGE_US:_observations.erase(key)

func make_snapshot(snapshot: Dictionary, now: int) -> String:
	_prune(now)
	var tick := _time(snapshot.get("tick_usec"))
	if tick<0 or tick>now or now-tick>MAX_AGE_US or not _vector(snapshot.get("position_m"),3) or not _vector(snapshot.get("orientation_xyzw"),4) or _time(snapshot.get("revision"))<0:return ""
	var token := Crypto.new().generate_random_bytes(16).hex_encode()
	if token.length()!=32 or _witnesses.has(token):return ""
	_witnesses[token]={"tick":tick,"revision":snapshot.revision,"position_m":snapshot.position_m.duplicate(),"orientation_xyzw":snapshot.orientation_xyzw.duplicate()}
	return token

func observe(fields: Dictionary, now: int) -> Dictionary:
	_prune(now)
	if not _keys(fields,OBS_FIELDS) or fields.get("world_epoch")!=_epoch:return _bad("pc_observation_fields_or_epoch")
	var token=fields.get("source_witness")
	if not _hex(token,32) or not _witnesses.has(token):return _bad("pc_original_native_witness_required")
	var witness: Dictionary=_witnesses[token]
	if now<int(witness.tick) or now-int(witness.tick)>=MAX_AGE_US:return _bad("pc_observation_expired")
	if not _integer(fields.get("board_sense_seq"),_max_sense+1,4294967295):return _bad("pc_observation_monotonic_seq")
	for key in ["board_receipt_sha256","board_frame_sha256","source_record_sha256"]:
		if not _hex(fields.get(key)):return _bad("pc_observation_digest")
	if _time(fields.get("source_acquisition_qpc_ns"))<0 or fields.get("source_segment_id")!="native-"+str(witness.revision):return _bad("pc_original_source_time_or_segment")
	if not _vector(fields.get("source_position_m"),3) or not _vector(fields.get("source_orientation_xyzw"),4) or not _same(fields.source_position_m,witness.position_m) or not _same(fields.source_orientation_xyzw,witness.orientation_xyzw):return _bad("pc_original_source_pose")
	var binding=fields.get("board_binding")
	if not binding is Dictionary or not _keys(binding,["boot_id","build_id","request_hash"]) or not binding.get("boot_id") is String or binding.boot_id.length()!=36 or not _hex(binding.get("build_id"),32) or not _hex(binding.get("request_hash")):return _bad("pc_actual_board_binding")
	if not _binding.is_empty() and _binding!=binding:return _bad("pc_board_binding_changed")
	var seq: int=int(fields.board_sense_seq)
	var saved: Dictionary=fields.duplicate(true)
	saved.native_tick=int(witness.tick)
	_observations[seq]=saved
	_binding=binding.duplicate(true)
	_max_sense=seq
	_latest=saved.duplicate(true)
	_witnesses.erase(token)
	return {"ok":true}

func admit(text: Variant, digest: Variant, now: int, paused: bool) -> Dictionary:
	_prune(now)
	if not text is String or text.length()>4096 or not _hex(digest) or text.sha256_text()!=digest:return _bad("pc_command_digest")
	var command=JSON.parse_string(text)
	if not command is Dictionary or not _keys(command,COMMAND_FIELDS):return _bad("pc_command_fields")
	# The wire schema is flat canonical ASCII, integer codes and decimal times.
	# Reject duplicate canonical keys instead of trusting JSON's last-key wins.
	for key in COMMAND_FIELDS:
		if text.count('"'+key+'":')!=1:return _bad("pc_command_noncanonical_keys")
	if command.get("abi")!=COMMAND_ABI or command.get("mode")!="PC_DIRECT" or command.get("world_epoch")!=_epoch or command.get("profile")!="fast_9600":return _bad("pc_command_identity_or_profile")
	if not _integer(command.get("command_seq"),_command_seq+1,9007199254740991) or not _integer(command.get("board_sense_seq"),1,4294967295):return _bad("pc_command_monotonic_seq")
	var source_seq: int=int(command.board_sense_seq)
	if not _observations.has(source_seq):return _bad("pc_original_registered_observation_required")
	var observation: Dictionary=_observations[source_seq]
	for key in ["board_receipt_sha256","board_frame_sha256","source_record_sha256","source_acquisition_qpc_ns"]:
		if command.get(key)!=observation[key]:return _bad("pc_command_original_observation_binding")
	if not _hex(command.get("ai_result_sha256")):return _bad("pc_actual_ai_digest")
	var acquired := _time(command.get("source_acquisition_qpc_ns"))
	var issued := _time(command.get("first_send_qpc_ns"))
	var deadline := _time(command.get("native_deadline_usec"))
	if acquired<0 or issued<acquired or issued-acquired>MAX_AGE_US*1000 or not _integer(command.get("ttl_ms"),1,MAX_TTL_MS):return _bad("pc_original_issue_or_ttl")
	var ttl: int=int(command.ttl_ms)
	if now<int(observation.native_tick) or deadline<0 or deadline>int(observation.native_tick)+MAX_AGE_US or deadline>now+ttl*1000:return _bad("pc_original_observation_deadline")
	if not _integer(command.get("speed_code"),0,20) or not _integer(command.get("yaw_q"),-15000,15000) or not _integer(command.get("pitch_q"),-15000,15000):return _bad("pc_motion_codes")
	var code: int=int(command.speed_code)
	var yaw: int=int(command.yaw_q)
	var pitch: int=int(command.pitch_q)
	if yaw*yaw+pitch*pitch>FAST_ROM[code] or (paused and (code!=0 or yaw!=0 or pitch!=0)):return _bad("pc_combined_curvature_or_pause")
	# A valid but late update has no admission side effect. The caller may keep
	# its previous live grant; this does not renew it or relax the original age.
	if deadline<=now+100000:return {"ok":false,"reason":"pc_admission_headroom","admission_applied":false}
	var speed := float(code)/80.0
	var ky := 0.0 if code==0 else float(yaw)*PI/(180000.0*speed)
	var kp := 0.0 if code==0 else float(pitch)*PI/(180000.0*speed)
	_command_seq=int(command.command_seq)
	_command_sha=digest
	return {"ok":true,"speed_m_s":speed,"yaw_curvature_per_m":ky,"pitch_curvature_per_m":kp,"native_deadline_usec":deadline}

func public_fields() -> Dictionary:
	# Observation fields describe newest actual input, not a relabelled command.
	# The exact pc_command_sha256 binds the command's own original observation.
	return {"admission_mode":"PC_DIRECT","action_source":"pc_direct_host","world_epoch":_epoch,"source_witness":"","board_observation_seq":_max_sense,"board_observation_sha256":_latest.get("board_receipt_sha256",""),"source_record_sha256":_latest.get("source_record_sha256",""),"observation_native_tick_usec":str(_latest.get("native_tick",0)),"pc_command_seq":_command_seq,"pc_command_sha256":_command_sha}

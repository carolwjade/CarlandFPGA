extends SceneTree
## NEW isolated software custody fixture; real bridge handlers/native Node3D only.
## Does not freeze original Main, create Root executor/BOOT, or grant movement.

class Probe extends "res://runtime/world_motion_bridge.gd":
	var replies: Array = []
	var refusals: Array = []
	var audit_ok := true
	func audit_frame() -> bool:
		return audit_ok
	func _refuse(operation: String, code: String) -> void:
		refusals.append({"operation": operation, "code": code})
	func _queue(kind: String, epoch: String, operation: String, body: Dictionary) -> bool:
		replies.append({"type": kind, "epoch": epoch, "operation": operation, "body": body.duplicate(true)})
		return true

class SoftwareMain extends RefCounted:
	var bridge: Probe
	var drill: Node3D
	var token: RefCounted
	var revision := "0"
	var writes := 0
	var reject_write := false
	var omit_readback := false
	var fail_post_audit := false
	func _owned_apply_drill_global(actor: RefCounted, key: RefCounted, value: Transform3D, next_revision: String) -> bool:
		if actor != bridge or key != token or reject_write:
			return false
		drill.global_transform = value
		revision = next_revision
		writes += 1
		if fail_post_audit:
			bridge.audit_ok = false
		return true
	func _owned_drill_readback(actor: RefCounted, key: RefCounted) -> Dictionary:
		if actor != bridge or key != token or omit_readback:
			return {}
		return {"node": drill, "local": drill.transform, "global": drill.global_transform, "pose_revision": revision}

var checks := 0
var failures: Array = []
var fixtures: Array = []

func _initialize() -> void:
	call_deferred("_run")

func _expect(ok: bool, name: String) -> void:
	checks += 1
	if not ok:
		failures.append(name)
		printerr("FAIL ", name)

func _fixture() -> Probe:
	var p := Probe.new()
	var main := SoftwareMain.new()
	var node := Node3D.new()
	root.add_child(node)
	main.bridge = p
	main.drill = node
	main.token = RefCounted.new()
	p._main = main
	p._token = main.token
	p._refs = {"drill": node}
	p._boot = {"run_id": "software-sequential-publication"}
	p._freeze = {"freeze_id": "e".repeat(48), "world_epoch": "1"}
	p._state = "FROZEN"
	p._scalar_width = 32
	fixtures.append(p)
	_send(p, _message(p, "initial", "0", "0", Vector3.ZERO, true))
	return p

func _message(p: Probe, operation: String, previous: String, revision: String, position: Vector3, initial: bool = false) -> Dictionary:
	var pose := {"position_m": p._f64_vector(position),
		"orientation_xyzw": [p._f64(0.), p._f64(0.), p._f64(0.), p._f64(1.)], "speed_m_s": p._f64(0.)}
	var body := {"freeze_id": p._freeze.freeze_id, "geometry_identity": "a".repeat(64),
		"pose_revision": revision, "desired_pose": pose,
		"desired_transform": {"basis_columns": [p._f64_vector(Vector3.RIGHT), p._f64_vector(Vector3.UP), p._f64_vector(Vector3.BACK)], "origin": pose.position_m.duplicate()}}
	if not initial:
		body["expected_previous_revision"] = previous
		body["numerical_receipt_digest"] = "b".repeat(64)
	return {"type": "INITIAL_VIEW" if initial else "PUBLISH_VIEW", "run_id": p._boot.run_id,
		"world_epoch": p._freeze.world_epoch, "operation_id": operation, "body": body}

func _send(p: Probe, message: Dictionary) -> void:
	p._handle(JSON.stringify(message).to_utf8_buffer())

func _count(p: Probe) -> int:
	var value: Variant = p.get("_publication_count")
	return int(value) if value is int else -1

func _last_code(p: Probe) -> String:
	return "" if p.refusals.is_empty() else str(p.refusals.back().code)

func _test_two_actual_transforms() -> void:
	var p := _fixture()
	_expect(p._initialized and _count(p) == 0, "INITIAL_VIEW is separate from noninitial quota")
	_send(p, _message(p, "step1", "0", "1", Vector3(1., 0.5, 0.)))
	var first: Dictionary = p.replies.back().body
	_send(p, _message(p, "step2", "1", "2", Vector3(2., 0.5, 0.)))
	_expect(p._main.drill.global_position == Vector3(2., 0.5, 0.) and p._pose_revision == "2", "second sequential publication changes actual native Node3D/revision")
	_expect(_count(p) == 2 and p._main.writes == 3, "exactly two noninitial reservations and native writes")
	_expect(first.pose_revision == "1" and p.replies.back().body.pose_revision == "2" and first.global_transform != p.replies.back().body.global_transform, "two distinct original native getter records")

func _test_cap() -> void:
	var p := _fixture()
	for i in range(1, 17):
		_send(p, _message(p, "cap" + str(i), str(i - 1), str(i), Vector3(float(i), 0., 0.)))
	_expect(_count(p) == 16 and p._pose_revision == "16", "sixteen sequential noninitial effects allowed")
	_send(p, _message(p, "cap17", "16", "17", Vector3(17., 0., 0.)))
	_expect(_last_code(p) == "over_budget" and _count(p) == 16 and p._main.drill.global_position.x == 16., "seventeenth refuses without write or quota reset")

func _test_decode_reserves_before_failure() -> void:
	var p := _fixture()
	var bad := _message(p, "bad-transform", "0", "1", Vector3.ONE)
	bad.body.desired_transform["basis_columns"] = []
	_send(p, bad)
	_expect(_count(p) == 1 and p._publication.get("state", "") == "APPLYING", "fallible transform decode retains consumed reservation")
	_send(p, _message(p, "after-bad", "0", "1", Vector3.ONE))
	_expect(_last_code(p) == "unknown_effect" and p._main.writes == 1 and _count(p) == 1, "failed decode cannot resume or replay an effect")
	var q := _fixture()
	var invalid := _message(q, "bad-pose", "0", "1", Vector3.ONE)
	invalid.body.desired_pose["orientation_xyzw"] = [q._f64(0.),q._f64(0.),q._f64(0.),q._f64(0.)]
	_send(q, invalid)
	_expect(_count(q) == 1 and q._publication.get("state", "") == "APPLYING" and q._main.writes == 1, "pose decode failure also consumes before fallible work")

func _test_unknown_write_and_readback() -> void:
	for missing in [false, true]:
		var p := _fixture()
		p._main.reject_write = not missing
		p._main.omit_readback = missing
		_send(p, _message(p, "unknown", "0", "1", Vector3.ONE))
		_expect(p._publication.get("state", "") == "APPLYING" and _count(p) == 1, "unknown write/getter stays retained " + str(missing))
		p._main.reject_write = false
		p._main.omit_readback = false
		_send(p, _message(p, "after-unknown", "0", "1", Vector3(2.,0.,0.)))
		_expect(_last_code(p) == "unknown_effect" and _count(p) == 1, "unknown cannot admit next after flags restore " + str(missing))

func _test_audit_and_stop() -> void:
	var p := _fixture()
	p._main.fail_post_audit = true
	_send(p, _message(p, "audit-effect", "0", "1", Vector3.ONE))
	_expect(not p._publication.get("readback_validated", false), "getter alone is not an audited APPLIED prerequisite")
	p.audit_ok = true
	p._main.fail_post_audit = false
	_send(p, _message(p, "after-audit", "1", "2", Vector3(2.,0.,0.)))
	_expect(_last_code(p) == "unknown_effect" and _count(p) == 1, "failed post audit is not resumable")
	var q := _fixture()
	_send(q, _message(q, "before-stop", "0", "1", Vector3.ONE))
	_send(q, {"type":"STOP", "run_id":q._boot.run_id, "world_epoch":"1", "operation_id":"stop", "body":{"freeze_id":q._freeze.freeze_id,"reason_code":"software-stop","expected_pose_revision":"1"}})
	_send(q, _message(q, "after-stop", "1", "2", Vector3(2.,0.,0.)))
	_expect(q._admission_stopped and q._stop_received and _last_code(q) == "unknown_effect" and _count(q) == 1 and q._main.drill.global_position == Vector3.ONE, "STOP permanently disables admission within original frozen epoch")

func _test_ids_revisions_and_queries() -> void:
	var p := _fixture()
	var first := _message(p, "unique1", "0", "1", Vector3.ONE)
	_send(p, first)
	_send(p, first)
	_expect(_last_code(p) == "duplicate_publish" and _count(p) == 1 and p._main.writes == 2, "original operation replay refuses without effect")
	_send(p, _message(p, "stale", "0", "2", Vector3(2.,0.,0.)))
	_expect(_last_code(p) == "stale_revision" and _count(p) == 1, "actual previous revision required without consuming quota")
	_send(p, _message(p, "unique2", "1", "2", Vector3(2.,0.,0.)))
	_send(p, {"type":"QUERY_VIEW","run_id":p._boot.run_id,"world_epoch":"1","operation_id":"old-query","body":{"freeze_id":p._freeze.freeze_id,"publication_operation_id":"unique1","payload_digest":"c".repeat(64),"expected_pose_revision":"1"}})
	_expect(_last_code(p) == "unknown_effect" and p._pose_revision == "2" and _count(p) == 2, "known older publication query refuses rather than false NOT_SEEN")
	var old_epoch := _message(p, "old-epoch", "2", "3", Vector3(3.,0.,0.))
	old_epoch["world_epoch"] = "0"
	_send(p, old_epoch)
	_expect(_last_code(p) == "stale_epoch" and _count(p) == 2, "old epoch cannot adopt current quota or node")
	var fresh := _fixture()
	_expect(_count(fresh) == 0 and fresh._pose_revision == "0", "fresh software frozen fixture begins separate quota")

func _run() -> void:
	_test_two_actual_transforms()
	_test_cap()
	_test_decode_reserves_before_failure()
	_test_unknown_write_and_readback()
	_test_audit_and_stop()
	_test_ids_revisions_and_queries()
	for p: Probe in fixtures:
		p._main.bridge = null
		p._main.drill.free()
		p._main = null
		p._refs = {}
	fixtures.clear()
	print(JSON.stringify({"scope":"isolated_software_bridge_native_Node3D_only", "checks":checks,"failures":failures,"actual_original_Main_freeze":false,"Root_executor_or_BOOT":false,"motion_authority":false}))
	quit(0 if failures.is_empty() else 1)

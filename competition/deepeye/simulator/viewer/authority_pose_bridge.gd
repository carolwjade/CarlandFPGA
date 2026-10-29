extends RefCounted
## Renderer-only adapter. Trusted local integration owns this object and target.
## No networking, controller endpoint, movement planning or action authorization.

const FIELDS := ["run_id", "authority_revision", "pose_revision", "position_m", "orientation_xyzw", "stopped"]
const MAX_REVISION := 9007199254740991
const MAX_POSITION := 3.4028234663852886e38
const RUN_META := &"deepeye_authority_run_id"
const STATE_META := &"deepeye_authority_revision"
const POSE_META := &"deepeye_authority_pose_revision"
const STOP_META := &"deepeye_authority_stopped"

var _target: Node3D
var _run_id := ""
var _bound := false
var _last: Dictionary = {}

func _valid_run(value: Variant) -> bool:
	if typeof(value) != TYPE_STRING or value.length() < 1 or value.length() > 128:
		return false
	for i in value.length():
		if value.unicode_at(i) < 32 or value.unicode_at(i) == 127:
			return false
	return true

func bind_target(target: Node3D, run_id: String) -> bool:
	if _bound or not is_instance_valid(target) or not target.is_inside_tree() or not _valid_run(run_id):
		return false
	_target = target
	_run_id = run_id
	_bound = true
	return true

func _revision(value: Variant) -> bool:
	# Godot JSON parses integer tokens as doubles. Require an exact integer value.
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	return is_finite(float(value)) and value >= 0 and value <= MAX_REVISION and value == floor(value)

func _numbers(value: Variant, size: int) -> bool:
	if typeof(value) != TYPE_ARRAY or value.size() != size:
		return false
	for number in value:
		if (typeof(number) != TYPE_INT and typeof(number) != TYPE_FLOAT) or not is_finite(float(number)):
			return false
	return true

func _reject(reason: String) -> Dictionary:
	return {"accepted": false, "error": reason}

func apply_frame(frame: Variant) -> Dictionary:
	if not _bound or not is_instance_valid(_target) or not _target.is_inside_tree():
		return _reject("target_unavailable")
	if typeof(frame) != TYPE_DICTIONARY or frame.size() != FIELDS.size():
		return _reject("frame_whitelist")
	for key in FIELDS:
		if not frame.has(key):
			return _reject("frame_whitelist")
	if not _valid_run(frame.run_id) or frame.run_id != _run_id:
		return _reject("run_mismatch")
	if not _revision(frame.authority_revision) or not _revision(frame.pose_revision):
		return _reject("revision_invalid")
	if not _numbers(frame.position_m, 3) or not _numbers(frame.orientation_xyzw, 4) or typeof(frame.stopped) != TYPE_BOOL:
		return _reject("pose_invalid")
	for component in frame.position_m:
		if abs(component) > MAX_POSITION:
			return _reject("native_position_overflow")
	var q = frame.orientation_xyzw
	# Quaternion components of a unit quaternion cannot exceed 1+tolerance;
	# bound first so hostile huge finite components cannot overflow norm math.
	for component in q:
		if abs(component) > 1.000001:
			return _reject("quaternion_invalid")
	var norm_squared: float = q[0]*q[0] + q[1]*q[1] + q[2]*q[2] + q[3]*q[3]
	if abs(sqrt(norm_squared) - 1.0) > 0.000001:
		return _reject("quaternion_invalid")
	if not _last.is_empty():
		if frame.authority_revision <= _last.authority_revision or frame.pose_revision < _last.pose_revision:
			return _reject("revision_stale")
		if frame.pose_revision == _last.pose_revision and (frame.position_m != _last.position_m or frame.orientation_xyzw != _last.orientation_xyzw):
			return _reject("same_revision_geometry_changed")
	var p = frame.position_m
	var native_pose := Transform3D(Basis(Quaternion(q[0], q[1], q[2], q[3]).normalized()), Vector3(p[0], p[1], p[2]))
	if not native_pose.is_finite():
		return _reject("native_pose_invalid")
	# Check representability under the current parent before any target mutation.
	var parent := _target.get_parent_node_3d()
	if parent != null and not _target.is_set_as_top_level():
		var parent_pose: Transform3D = parent.global_transform
		if not parent_pose.is_finite() or parent_pose.basis.determinant() == 0.0:
			return _reject("parent_transform_invalid")
		if not (parent_pose.affine_inverse() * native_pose).is_finite():
			return _reject("local_pose_invalid")
	var saved: Dictionary = frame.duplicate(true)
	# All input validation/allocation precedes this presentation update. This is
	# not the Python motion commit or a cross-process transaction/authority ACK.
	_target.global_transform = native_pose
	_target.set_meta(RUN_META, _run_id)
	_target.set_meta(STATE_META, int(frame.authority_revision))
	_target.set_meta(POSE_META, int(frame.pose_revision))
	_target.set_meta(STOP_META, frame.stopped)
	_last = saved
	return {"accepted": true, "native": readback()}

func readback() -> Dictionary:
	if _last.is_empty() or not is_instance_valid(_target) or not _target.is_inside_tree():
		return {}
	var actual: Transform3D = _target.global_transform
	var q := actual.basis.orthonormalized().get_rotation_quaternion()
	return {"run_id": _target.get_meta(RUN_META),
		"authority_revision": _target.get_meta(STATE_META),
		"pose_revision": _target.get_meta(POSE_META),
		"position_m": [actual.origin.x, actual.origin.y, actual.origin.z],
		"orientation_xyzw": [q.x, q.y, q.z, q.w],
		"stopped": _target.get_meta(STOP_META)}

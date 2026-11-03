extends RefCounted
## Explicit engineering demo guard; never changes motion_cast UNKNOWN semantics.
const Cast = preload("res://physics/motion_cast.gd")
const HALF := 0.4
const RADIUS := 0.12
const HALF_CUBE := 15.0
const GATE_RADIUS := 0.25
const NORMALS := [Vector3.RIGHT,Vector3.LEFT,Vector3.UP,Vector3.DOWN,Vector3.BACK,Vector3.FORWARD]

static func support(pose: Transform3D, normal: Vector3, inflation: float = 0.0) -> float:
	return HALF*absf(pose.basis.z.dot(normal))+RADIUS+inflation

static func portal_fits(pose: Transform3D, gate: Dictionary, inflation: float = 0.0) -> bool:
	var n: Vector3 = gate.normal
	var offset: Vector3 = pose.origin-gate.center
	var tangent := offset-n*offset.dot(n)
	var axis := pose.basis.z
	var projected_axis := axis-n*axis.dot(n)
	# Entire capsule projection contained in the circle: conservative, full 3D,
	# no arbitrary 5-degree acceptance rule and no centre-point-only crossing.
	return maxf((tangent+HALF*projected_axis).length(),(tangent-HALF*projected_axis).length())+RADIUS+inflation <= GATE_RADIUS

static func workspace(pose: Transform3D, entry: Dictionary, exit_gate: Dictionary,
		entered: bool, inflation: float = 0.0) -> Dictionary:
	for normal: Vector3 in NORMALS:
		if pose.origin.dot(normal)-HALF_CUBE+support(pose,normal,inflation) <= 0.0:
			continue
		var gate: Dictionary = exit_gate if entered else entry
		if normal != gate.normal or not portal_fits(pose,gate,inflation):
			return {"ok":false,"reason":"workspace_or_aperture"}
		var direction: float = pose.basis.z.dot(normal)
		if (not entered and direction >= 0.0) or (entered and direction <= 0.0):
			return {"ok":false,"reason":"portal_direction"}
	return {"ok":true}

static func probe(space: PhysicsDirectSpaceState3D, before: Transform3D, after: Transform3D,
		distance_bound: float, curvature: float, entry: Dictionary, exit_gate: Dictionary,
		entered: bool, collision_mask: int) -> Dictionary:
	var angle := before.basis.get_rotation_quaternion().angle_to(after.basis.get_rotation_quaternion())
	# Rotation of the complete .8m centreline + curved-centre chord deviation.
	# Radius balls are orientation invariant. These positive inflations enclose
	# every intermediate capsule, not merely endpoint poses.
	var inflation := 0.0005+HALF*angle+curvature*distance_bound*distance_bound/8.0
	if inflation > 0.01:
		return {"ok":false,"reason":"frame_rotation_expansion"}
	var first := workspace(before,entry,exit_gate,entered,inflation)
	var last := workspace(after,entry,exit_gate,entered,inflation)
	if not first.ok or not last.ok:
		return {"ok":false,"reason":"workspace_or_aperture"}
	# Endpoint supports inflated by the entire centre displacement cover face
	# and circle changes during this short interval as well.
	var face_guard := workspace(before,entry,exit_gate,entered,inflation+before.origin.distance_to(after.origin))
	if not face_guard.ok:return face_guard
	var result: Dictionary = Cast.query(space,before,after.origin-before.origin,inflation,0.0,collision_mask,[],64)
	var clear: bool = result.get("query_complete",false) and result.get("fractions_valid",false) and result.get("initial_count",-1)==0 and result.get("endpoint_count",-1)==0 and result.fractions.size()==2 and result.fractions[0]==1.0 and result.fractions[1]==1.0
	return {"ok":clear,"reason":"demo_engine_no_hit" if clear else "volume_guard_rejected",
		"original_query_status":result.get("status","unknown"),"formal_clearance":"not_run",
		"rotation_inflation_m":inflation,"query":result}

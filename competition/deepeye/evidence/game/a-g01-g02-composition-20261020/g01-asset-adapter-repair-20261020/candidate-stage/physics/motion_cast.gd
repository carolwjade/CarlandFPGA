extends RefCounted
## Authority-internal fixed-orientation translation probe. NEVER motion permission.
## No-hit remains UNKNOWN: this backend's contact precision is not certified.

const HALF_SEGMENT_M := 0.4
const BASE_RADIUS_M := 0.12
const SHAPE_TO_BODY := Basis(Vector3.RIGHT, Vector3.BACK, Vector3.DOWN)

static func _f32_up(value: float) -> float:
	# Positive finite sizes only. Avoid inward radius/height storage rounding.
	var bytes := PackedByteArray()
	bytes.resize(4)
	bytes.encode_float(0, value)
	if bytes.decode_float(0) < value:
		bytes.encode_u32(0, bytes.decode_u32(0) + 1)
	return bytes.decode_float(0)

static func expanded_capsule(rho: float = 0.0005, numeric_guard: float = 0.0) -> Dictionary:
	if not is_finite(rho) or not is_finite(numeric_guard) or rho < 0.0 or numeric_guard < 0.0 or rho > 0.01 or numeric_guard > 0.01:
		return {"valid": false, "reason": "expansion must be finite in [0,.01]m per component"}
	var requested_radius := BASE_RADIUS_M + rho + numeric_guard
	var shape := CapsuleShape3D.new()
	shape.radius = _f32_up(requested_radius)
	# Spherical expansion changes BOTH radius and total height. The nominal
	# centreline remains .8m; outward binary32 height may add a recorded few nm.
	shape.height = _f32_up(2.0 * (HALF_SEGMENT_M + shape.radius))
	shape.margin = 0.0
	var actual_half := (shape.height - 2.0 * shape.radius) / 2.0
	return {"valid": shape.radius >= requested_radius and actual_half >= HALF_SEGMENT_M,
		"shape": shape, "rho_m": rho, "numeric_guard_m": numeric_guard,
		"requested_radius_m": requested_radius, "radius_m": shape.radius,
		"height_m": shape.height, "half_segment_m": actual_half,
		"segment_outward_quantization_m": actual_half - HALF_SEGMENT_M}

static func _valid_pose(pose: Transform3D) -> bool:
	if not pose.origin.is_finite():
		return false
	if maxf(absf(pose.origin.x), maxf(absf(pose.origin.y), absf(pose.origin.z))) > 32.0:
		return false
	var b := pose.basis
	if not b.x.is_finite() or not b.y.is_finite() or not b.z.is_finite():
		return false
	# Bound the accepted rotation residue; this is not a certified pose error bound.
	return absf(b.x.length_squared() - 1.0) <= 0.000002 and absf(b.y.length_squared() - 1.0) <= 0.000002 and absf(b.z.length_squared() - 1.0) <= 0.000002 and absf(b.x.dot(b.y)) <= 0.000002 and absf(b.x.dot(b.z)) <= 0.000002 and absf(b.y.dot(b.z)) <= 0.000002 and absf(b.determinant() - 1.0) <= 0.000004

static func _ids(hits: Array) -> Array:
	var ids: Array = []
	for hit in hits:
		ids.append({"collider_id": hit.get("collider_id", 0), "shape_index": hit.get("shape", -1)})
	return ids

static func query(space: PhysicsDirectSpaceState3D, body_pose: Transform3D, motion: Vector3,
		rho: float = 0.0005, numeric_guard: float = 0.0, collision_mask: int = 1,
		exclude: Array = [], max_results: int = 32) -> Dictionary:
	var result := {"status": "unknown", "motion_authorized": false,
		"reason": "invalid request or unavailable space", "query_complete": false,
		"query_kind": "fixed_orientation_expanded_translation", "query_margin_m": 0.0,
		"backend_clearance_gate": "blocked_unfrozen_contact_precision"}
	if space == null or not _valid_pose(body_pose) or not motion.is_finite() or motion.length() > 64.0 or collision_mask <= 0 or collision_mask > 4294967295 or max_results < 1 or max_results > 256 or exclude.size() > 256:
		return result
	var valid_exclude: Array[RID] = []
	for rid in exclude:
		if typeof(rid) != TYPE_RID or not rid.is_valid():
			result.reason = "invalid exclusion RID"
			return result
		valid_exclude.append(rid)
	var built := expanded_capsule(rho, numeric_guard)
	if not built.valid:
		result.reason = built.reason
		return result
	var parameters := PhysicsShapeQueryParameters3D.new()
	parameters.shape = built.shape
	parameters.transform = body_pose * Transform3D(SHAPE_TO_BODY, Vector3.ZERO)
	parameters.margin = 0.0
	parameters.collision_mask = collision_mask
	parameters.exclude = valid_exclude
	parameters.collide_with_bodies = true
	parameters.collide_with_areas = false
	var initial := space.intersect_shape(parameters, max_results)
	parameters.motion = motion
	var cast := space.cast_motion(parameters)
	# Endpoint query is diagnostic only; it cannot replace the swept query.
	parameters.motion = Vector3.ZERO
	parameters.transform.origin += motion
	var ending := space.intersect_shape(parameters, max_results)
	var fractions_valid := cast.size() == 2
	if fractions_valid:
		fractions_valid = is_finite(cast[0]) and is_finite(cast[1]) and cast[0] >= 0.0 and cast[0] <= cast[1] and cast[1] <= 1.0
	var at_limit := initial.size() >= max_results or ending.size() >= max_results
	result.merge({"initial_count": initial.size(), "endpoint_count": ending.size(),
		"initial_objects": _ids(initial), "endpoint_objects": _ids(ending),
		"at_result_limit": at_limit, "max_results": max_results,
		"query_complete": fractions_valid and not at_limit,
		"fractions": Array(cast), "fractions_valid": fractions_valid,
		"collision_mask": collision_mask, "exclude_count": exclude.size(),
		"radius_m": built.radius_m, "height_m": built.height_m,
		"half_segment_m": built.half_segment_m,
		"rho_m": rho, "numeric_guard_m": numeric_guard,
		"segment_outward_quantization_m": built.segment_outward_quantization_m,
		"shape_axis_world": [parameters.transform.basis.y.x, parameters.transform.basis.y.y, parameters.transform.basis.y.z],
		"axis_mapping_residue": parameters.transform.basis.y.distance_to(body_pose.basis.z),
		"basis_orthogonality_residue": absf(body_pose.basis.x.dot(body_pose.basis.z))}, true)
	if not initial.is_empty() or not ending.is_empty() or (fractions_valid and cast[0] < 1.0):
		result.status = "collision_attempt"
		result.reason = "reject entire requested step; safe fraction is diagnostic, not allowed progress"
	elif not fractions_valid:
		result.reason = "invalid/empty/nonfinite cast result"
	elif at_limit:
		result.reason = "overlap query may be truncated"
	else:
		result.reason = "no hit in requested filter; backend contact/transform error bound is not frozen"
	# No branch returns CLEAR, applies a fraction or creates an authority grant.
	return result

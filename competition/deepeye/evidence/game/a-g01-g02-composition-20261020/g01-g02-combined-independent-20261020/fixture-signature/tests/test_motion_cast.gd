extends SceneTree
## Real engine query probe. No motion authority, full CCD or G06 acceptance.

const SHAPE_TO_BODY := Basis(Vector3.RIGHT, Vector3.BACK, Vector3.DOWN)
const ADAPTER := "res://physics/motion_cast.gd"
var _adapter = null
var _world: Node3D
var _fixture: Node3D
var _checks := 0
var _failures: Array = []
var _rows: Array = []
var _fixture_metadata: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _check(ok: bool, message: String) -> void:
	_checks += 1
	if not ok:
		_failures.append(message)

func _vec(v: Vector3) -> Array:
	return [v.x, v.y, v.z]

func _box(size: Vector3, position: Vector3, layer: int = 1) -> StaticBody3D:
	var shape := BoxShape3D.new()
	shape.size = size
	return _body(shape, Transform3D(Basis.IDENTITY, position), layer)

func _body(shape: Shape3D, pose: Transform3D, layer: int = 1) -> StaticBody3D:
	shape.margin = 0.0
	var body := StaticBody3D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	body.transform = pose
	var collider := CollisionShape3D.new()
	collider.shape = shape
	body.add_child(collider)
	_fixture.add_child(body)
	var metadata := {"type": shape.get_class(), "position": _vec(body.global_position),
		"basis_columns": [_vec(body.global_basis.x), _vec(body.global_basis.y), _vec(body.global_basis.z)], "layer": layer,
		"shape_margin": shape.margin}
	if shape is BoxShape3D:
		metadata["size"] = _vec(shape.size)
	elif shape is CapsuleShape3D or shape is CylinderShape3D:
		metadata["radius"] = shape.radius
		metadata["height"] = shape.height
	_fixture_metadata.append(metadata)
	return body

func _reset() -> void:
	if is_instance_valid(_fixture):
		_fixture.free()
	_fixture = Node3D.new()
	_world.add_child(_fixture)
	_fixture_metadata = []

func _sync() -> void:
	await physics_frame
	await physics_frame
	await process_frame

func _raw(pose: Transform3D, motion: Vector3, rho: float, mask: int, exclude: Array[RID], limit: int) -> Dictionary:
	var shape := CapsuleShape3D.new()
	shape.radius = 0.12 + rho
	shape.height = 1.04 + 2.0 * rho
	shape.margin = 0.0
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = shape
	query.transform = pose * Transform3D(SHAPE_TO_BODY, Vector3.ZERO)
	query.margin = 0.0
	query.collision_mask = mask
	query.exclude = exclude
	var space := _world.get_world_3d().direct_space_state
	var initial := space.intersect_shape(query, limit)
	query.motion = motion
	var fraction := space.cast_motion(query)
	query.motion = Vector3.ZERO
	query.transform.origin += motion
	var ending := space.intersect_shape(query, limit)
	return {"initial_count": initial.size(), "endpoint_count": ending.size(),
		"fractions": Array(fraction), "radius_readback": shape.radius, "height_readback": shape.height}

func _probe(label: String, pose: Transform3D, motion: Vector3, rho: float = 0.0005,
		contact_fraction: float = -1.0, mask: int = 1, exclude: Array[RID] = [], limit: int = 32) -> Dictionary:
	await _sync()
	var raw := _raw(pose, motion, rho, mask, exclude, limit)
	var result: Dictionary = {}
	if _adapter != null:
		result = _adapter.query(_world.get_world_3d().direct_space_state, pose, motion,
			rho, 0.0, mask, exclude, limit)
		_check(result.get("motion_authorized", true) == false, label + ": never grants motion")
		_check(result.get("status", "") in ["collision_attempt", "unknown"], label + ": no certified CLEAR in uncalibrated prototype")
		var adapter_hit: bool = result.initial_count > 0 or result.endpoint_count > 0 or (result.fractions_valid and result.fractions[0] < 1.0)
		_check(result.status == ("collision_attempt" if adapter_hit else "unknown"), label + ": adapter preserves its own hit evidence despite raw/adapter shape differences")
	var raw_hit: bool = raw.initial_count > 0 or raw.endpoint_count > 0 or (
		raw.fractions.size() == 2 and float(raw.fractions[0]) < 1.0)
	var missed := contact_fraction >= 0.0 and not raw_hit
	var error_m = null
	if contact_fraction >= 0.0 and raw.fractions.size() == 2 and raw.initial_count == 0 and motion.length() > 0.0:
		error_m = (float(raw.fractions[0]) - contact_fraction) * motion.length()
	var row := {"label": label, "body_origin": _vec(pose.origin), "body_axis": _vec(pose.basis.z),
		"motion": _vec(motion), "rho": rho, "mask": mask, "exclude_count": exclude.size(),
		"result_limit": limit, "analytic_contact_fraction": contact_fraction,
		"fixture_shapes": _fixture_metadata.duplicate(true),
		"raw": raw, "raw_missed_contact": missed, "raw_safe_fraction_error_m": error_m,
		"adapter": result}
	_rows.append(row)
	print("CAST_PROBE " + JSON.stringify(row))
	return row

func _run() -> void:
	_world = Node3D.new()
	root.add_child(_world)
	_check(FileAccess.file_exists(ADAPTER), "RED: query adapter source exists")
	if FileAccess.file_exists(ADAPTER):
		_adapter = load(ADAPTER)
	print("CAST_ENV " + JSON.stringify({"version": Engine.get_version_info(),
		"physics_engine_setting": ProjectSettings.get_setting("physics/3d/physics_engine"),
		"server_class": PhysicsServer3D.get_class(), "shape_to_body_y": _vec(SHAPE_TO_BODY.y)}))
	_check(SHAPE_TO_BODY * Vector3.UP == Vector3.BACK, "native capsule +Y maps exactly to body +Z")
	if _adapter != null:
		for rho in [0.0, 0.0005, 0.001]:
			var built: Dictionary = _adapter.expanded_capsule(rho, 0.0)
			_check(built.get("valid", false), "expanded capsule accepts finite rho")
			_check(built.radius_m >= 0.12 + rho, "radius rounds outward from requested spherical expansion")
			_check(built.half_segment_m >= 0.4 and built.half_segment_m - 0.4 < 0.000001, "actual half-segment never shrinks and only has reported float quantization")
			_check(absf(built.height_m - (1.04 + 2.0 * rho)) < 0.000001, "height also expands by twice rho")
			_check(built.shape.margin == 0.0, "explicit shape expansion does not rely on query margin")
		var guarded: Dictionary = _adapter.expanded_capsule(0.0005, 0.0007)
		_check(guarded.radius_m >= 0.1212 and guarded.height_m >= 1.0424, "separate requested numeric guard explicitly expands both actual radius and height")
	# Independent broad-plane support oracles: a=1, h=.4,R=.1205, motion length2.
	for name in ["head", "tail", "side", "oblique"]:
		_reset()
		var pose := Transform3D.IDENTITY
		var motion := Vector3(0, 0, 2)
		var expected := (1.0 - 0.4 - 0.1205) / 2.0
		if name == "tail":
			_box(Vector3(10, 10, 0.01), Vector3(0, 0, -1.005))
			motion.z = -2.0
		elif name == "side":
			_box(Vector3(0.01, 10, 10), Vector3(1.005, 0, 0))
			motion = Vector3(2, 0, 0)
			expected = (1.0 - 0.1205) / 2.0
		else:
			_box(Vector3(10, 10, 0.01), Vector3(0, 0, 1.005))
			if name == "oblique":
				pose.basis = Basis(Quaternion(Vector3.BACK, Vector3(0.6, 0, 0.8)))
				expected = (1.0 - 0.4 * 0.8 - 0.1205) / 2.0
		var row := await _probe(name, pose, motion, 0.0005, expected)
		_check(row.raw.initial_count == 0 and row.raw.endpoint_count == 0, name + ": endpoints do not replace swept thin-layer query")
		if _adapter != null:
			_check(row.adapter.status == "collision_attempt", name + ": actual swept attempt rejects the entire requested step")
	_reset()
	_box(Vector3(10, 10, 0.01), Vector3(5, -3, 8.005))
	await _probe("translated_diagonal_motion", Transform3D(Basis.IDENTITY, Vector3(5, -3, 7)), Vector3(2, 1, 2), 0.0005, 0.23975)
	# Broad overlap, contained obstacle, zero motion, and explicit filtering/count caps.
	_reset()
	_box(Vector3(2, 2, 2), Vector3.ZERO)
	var overlap := await _probe("initial_surrounded", Transform3D.IDENTITY, Vector3(0, 0, 2), 0.0005, 0.0)
	_check(overlap.raw.initial_count == 1, "independent initial overlap detects surrounding solid")
	_check(overlap.raw.fractions == [1.0, 1.0], "actual cast can report full fraction while initially surrounded")
	if _adapter != null:
		_check(overlap.adapter.status == "collision_attempt", "initial overlap never trusts cast alone")
	await _probe("zero_motion_overlap", Transform3D.IDENTITY, Vector3.ZERO, 0.0005, 0.0)
	_reset()
	_box(Vector3(0.02, 0.02, 0.02), Vector3.ZERO)
	await _probe("small_obstacle_inside_capsule", Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0)
	_reset()
	var empty := await _probe("zero_motion_empty_space", Transform3D.IDENTITY, Vector3.ZERO)
	if _adapter != null:
		_check(empty.adapter.status == "unknown", "no-hit zero-motion space remains uncertified unknown")
	_reset()
	var filtered := _box(Vector3(10, 10, 0.01), Vector3(0, 0, 1.005), 2)
	var ignored := await _probe("mask_ignores_layer2", Transform3D.IDENTITY, Vector3(0, 0, 2), 0.0005, -1.0, 1)
	_check(ignored.raw.fractions == [1.0, 1.0] and ignored.raw.initial_count == 0 and ignored.raw.endpoint_count == 0, "explicit mask excludes layer2 from actual query")
	var selected := await _probe("mask_selects_layer2", Transform3D.IDENTITY, Vector3(0, 0, 2), 0.0005, 0.23975, 2)
	_check(selected.raw.fractions[0] < 1.0, "explicit mask selects layer2 in actual swept query")
	var excluded := await _probe("exclude_selected_body", Transform3D.IDENTITY, Vector3(0, 0, 2), 0.0005, -1.0, 2, [filtered.get_rid()])
	_check(excluded.raw.fractions == [1.0, 1.0] and excluded.raw.initial_count == 0 and excluded.raw.endpoint_count == 0, "explicit RID exclusion removes the selected actual body")
	if _adapter != null:
		_check(excluded.adapter.status == "unknown", "filtered no-hit is not whole-world clearance")
	_reset()
	for i in 9:
		_box(Vector3(0.02, 0.02, 0.02), Vector3(0, 0, (i - 4) * 0.05))
	var limited := await _probe("nine_overlapping_objects_limit4", Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0, 1, [], 4)
	_check(limited.raw.initial_count == 4, "raw query reaches explicit result cap with nine actual objects")
	if _adapter != null:
		_check(limited.adapter.get("query_complete", true) == false, "result cap cannot claim complete object enumeration")
	var full_list := await _probe("nine_overlapping_objects_limit16", Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0, 1, [], 16)
	_check(full_list.raw.initial_count == 9, "all nine actual physics objects appear with a larger query cap")
	# Independent parallel-cylinder/capsule contact oracles.
	for kind in ["cylinder", "capsule"]:
		_reset()
		var shape: Shape3D
		var expected: float
		if kind == "cylinder":
			var cylinder := CylinderShape3D.new()
			cylinder.radius = 0.1
			cylinder.height = 0.5
			shape = cylinder
			expected = (1.0 - 0.1 - 0.1205) / 2.0
		else:
			var capsule := CapsuleShape3D.new()
			capsule.radius = 0.08
			capsule.height = 0.56
			shape = capsule
			expected = (1.0 - 0.08 - 0.1205) / 2.0
		_body(shape, Transform3D(SHAPE_TO_BODY, Vector3(1, 0, 0)))
		await _probe("parallel_" + kind, Transform3D.IDENTITY, Vector3(2, 0, 0), 0.0005, expected)
	# Micrometre contact perturbations, with zero and rotation-only rho separately.
	for rho in [0.0, 0.0005]:
		var radius: float = 0.12 + rho
		for microns in [-1000.0, -100.0, -10.0, -2.0, -1.0, 0.0, 1.0, 2.0, 10.0, 100.0, 1000.0]:
			_reset()
			var near_x: float = radius + microns * 0.000001
			_box(Vector3(0.3 - near_x, 0.4, 0.01), Vector3((0.3 + near_x) / 2.0, 0, 1.005))
			var expected := -1.0
			if near_x <= radius:
				expected = (1.0 - 0.4 - sqrt(maxf(0.0, radius * radius - near_x * near_x))) / 2.0
			await _probe("grazing_rho_%s_um_%s" % [rho, microns], Transform3D.IDENTITY, Vector3(0, 0, 2), rho, expected)
	_reset()
	_box(Vector3(0.2, 0.4, 0.01), Vector3(0.2, 0, 1.005))
	await _probe("eccentric_cap_x_0.1", Transform3D.IDENTITY, Vector3(0, 0, 2), 0.0005, (0.6 - sqrt(0.1205 * 0.1205 - 0.1 * 0.1)) / 2.0)
	# Exact endpoint and initial contact perturbed by +/-1um.
	for microns in [-1.0, 0.0, 1.0]:
		_reset()
		var endpoint_near: float = 2.0 + 0.52 + microns * 0.000001
		_box(Vector3(10, 10, 0.01), Vector3(0, 0, endpoint_near + 0.005))
		var expected := (endpoint_near - 0.52) / 2.0 if microns <= 0.0 else -1.0
		await _probe("endpoint_um_%s" % microns, Transform3D.IDENTITY, Vector3(0, 0, 2), 0.0, expected)
		_reset()
		_box(Vector3(10, 10, 0.01), Vector3(0, 0, 0.525 + microns * 0.000001))
		await _probe("initial_contact_um_%s" % microns, Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0 if microns <= 0.0 else -1.0)
	if _adapter != null:
		var space := _world.get_world_3d().direct_space_state
		for bad in [Transform3D(Basis.from_scale(Vector3(2, 1, 1)), Vector3.ZERO), Transform3D(Basis.IDENTITY, Vector3(INF, 0, 0))]:
			_check(_adapter.query(space, bad, Vector3.ZERO).status == "unknown", "invalid transform is rejected before query")
		_check(_adapter.query(space, Transform3D.IDENTITY, Vector3.ZERO, -1.0).status == "unknown", "negative expansion rejected")
		_check(_adapter.query(space, Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0, 0).status == "unknown", "empty collision mask rejected")
		_check(_adapter.query(space, Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0, 1, [], 0).status == "unknown", "invalid query result cap rejected")
		_check(_adapter.query(space, Transform3D.IDENTITY, Vector3.ZERO, 0.0, 0.0, 1, ["not a RID"]).status == "unknown", "untyped invalid exclusion fails closed instead of script exception")
	var misses := 0
	var late_error := 0.0
	var early_error := 0.0
	for row in _rows:
		misses += 1 if row.raw_missed_contact else 0
		if row.raw_safe_fraction_error_m != null:
			late_error = maxf(late_error, row.raw_safe_fraction_error_m)
			early_error = maxf(early_error, -row.raw_safe_fraction_error_m)
	print("CAST_SUMMARY " + JSON.stringify({"rows": _rows.size(), "raw_missed_contacts": misses,
		"max_raw_late_distance_m": late_error, "max_raw_early_distance_m": early_error,
		"backend_clearance_gate": "blocked_unfrozen_contact_precision", "motion_authorized": false}))
	print("TESTS checks=%d failures=%d" % [_checks, _failures.size()])
	for failure in _failures:
		print("FAILURE: " + failure)
	print("RESULT PASS" if _failures.is_empty() else "RESULT FAIL")
	quit(0 if _failures.is_empty() else 1)

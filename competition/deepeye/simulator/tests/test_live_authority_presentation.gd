extends SceneTree
## Focused real viewer scene integration, not a full live chain or UI acceptance.
var checks := 0
var failures: Array = []
var rows: Array = []
var asset_observation: Dictionary = {}

func _initialize() -> void:
	_run.call_deferred()

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _run_gate_stays_closed(scene) -> void:
	check(scene.shell._run_button.disabled, "renderer never enables Run")
	check(scene.shell._continue_button.disabled, "renderer never enables continue")
	check(scene.shell._pause_button.disabled, "renderer never enables pause")
	check(not scene.document.control_bridge_connected, "renderer grants no control connection")
	check(not scene.document.is_motion_active(), "renderer grants no motion activity")

func _run() -> void:
	var packed = load("res://viewer/main.tscn")
	if packed == null:
		check(false, "actual viewer scene loads")
		_finish()
		return
	var scene = packed.instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var target: Node3D = scene.get("_drill_root")
	check(is_instance_valid(target), "actual viewer builds its original drill anchor")
	if not is_instance_valid(target):
		scene.free()
		_finish()
		return
	var asset: Node3D = target.get_node_or_null("DrillPDC")
	asset_observation = {"presenter": scene._asset_presenter.report(), "target_name": str(target.name),
		"target_path": str(target.get_path()), "asset_id": "" if asset == null else asset.get_meta("asset_id", ""),
		"mesh_count": target.find_children("*", "MeshInstance3D", true, false).size()}
	check(target.name == &"DrillPresentation", "original named DrillPresentation present without greybox")
	check(asset != null and asset_observation.asset_id == "drill_pdc_v1", "real drill asset remains attached")
	check(asset_observation.presenter.state == "ready", "report any asset fallback or degradation")
	_run_gate_stays_closed(scene)
	for method in ["bind_authority_renderer", "present_authority_frame", "read_authority_presentation"]:
		check(scene.has_method(method), "viewer implements " + method)
	if not scene.has_method("present_authority_frame") or not scene.has_method("bind_authority_renderer") or not scene.has_method("read_authority_presentation"):
		scene.free()
		_finish()
		return
	var fixture = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/authority-owner-frames.json"))
	var original_id := target.get_instance_id()
	var original_asset_id := 0 if asset == null else asset.get_instance_id()
	var original_world_children: int = scene._world.get_child_count()
	var original_camera: Transform3D = scene._camera.global_transform
	var original_gate_ids: Array = []
	for gate in scene._gate_root.get_children():
		original_gate_ids.append(gate.get_instance_id())
	var before: Transform3D = target.global_transform
	var metadata_before: Array = target.get_meta_list()
	check(not scene.present_authority_frame(fixture[0]).get("accepted", true), "unbound first frame cannot claim run or target")
	check(target.global_transform == before and target.get_meta_list() == metadata_before, "unbound frame cannot mutate original drill")
	check(scene.read_authority_presentation().is_empty(), "unbound readback empty")
	check(not scene.bind_authority_renderer(""), "invalid explicit run refused without occupying target")
	check(scene.bind_authority_renderer("run-1"), "trusted Root explicitly binds current drill")
	check(not scene.bind_authority_renderer("other-run"), "successful bind cannot be replaced")
	check(target.global_transform == before and target.get_meta_list() == metadata_before, "binding itself does not move drill")
	_run_gate_stays_closed(scene)
	for frame in fixture:
		var reply: Dictionary = scene.present_authority_frame(frame)
		check(reply.get("accepted", false), "actual scene accepts owner snapshot")
		var readback: Dictionary = scene.read_authority_presentation()
		var p = frame.position_m
		check(target.global_position.distance_to(Vector3(p[0], p[1], p[2])) < 0.00001, "actual scene drill origin follows committed pose")
		check(abs(target.global_basis.z.z + 1.0) < 0.00001, "actual scene drill rotation follows committed quaternion")
		check(readback.position_m == [target.global_position.x, target.global_position.y, target.global_position.z], "readback uses original native drill transform")
		check(readback.authority_revision == frame.authority_revision and readback.pose_revision == frame.pose_revision, "native revisions track actual Root and pose revisions")
		check(readback.stopped == frame.stopped and target.get_meta(&"deepeye_authority_stopped") == frame.stopped, "real higher-state same-pose STOP displayed")
		check(scene._drill_root.get_instance_id() == original_id, "no replacement drill anchor")
		rows.append(readback)
		_run_gate_stays_closed(scene)
	check(rows[0].position_m != rows[1].position_m, "two owner revisions produce distinct actual native poses")
	check(rows[1].position_m == rows[2].position_m and not rows[1].stopped and rows[2].stopped, "STOP changes native status without new geometry")
	before = target.global_transform
	var read_before: Dictionary = scene.read_authority_presentation()
	for mutation in [{"run_id": "wrong-run"}, {"authority_revision": 4}, {"seed": 1}, {"scene": {}}, {"obstacles": []}]:
		var bad: Dictionary = fixture[2].duplicate(true)
		bad.authority_revision = 6
		bad.merge(mutation, true)
		check(not scene.present_authority_frame(bad).get("accepted", true), "actual viewer rejects bad run stale or truth field")
		check(target.global_transform == before, "rejected frame leaves original native drill pose unchanged")
		check(scene.read_authority_presentation() == read_before, "rejected frame leaves original native metadata unchanged")
	check(scene._world.get_child_count() == original_world_children, "no extra presentation or world node")
	check(asset != null and asset.get_instance_id() == original_asset_id, "same original body asset retained")
	check(scene._camera.global_transform == original_camera, "renderer does not move camera")
	var gate_ids: Array = []
	for gate in scene._gate_root.get_children():
		gate_ids.append(gate.get_instance_id())
	check(gate_ids == original_gate_ids, "renderer does not replace gates")
	_run_gate_stays_closed(scene)
	scene.free()
	_finish()

func _finish() -> void:
	print(JSON.stringify({"checks": checks, "failures": failures, "asset_observation": asset_observation, "native_rows": rows}))
	quit(0 if failures.is_empty() else 1)

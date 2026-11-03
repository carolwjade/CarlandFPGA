extends SceneTree
const Doc = preload("res://editor/scene_document.gd")
const ScopeSHA = "2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d"
var failures: Array[String] = []
func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void:
	run.call_deferred()
func run() -> void:
	var doc = Doc.new()
	check(doc.set_gate("entry","top",14.75,0.0).ok,"edge .25 accepted")
	check(not doc.set_gate("entry","top",14.76,0.0).ok,"edge crossing refused")
	doc.set_gate("entry","top",0.0,0.0)
	check(not doc.set_gate("exit","top",0.49,0.0).ok,".5m circles overlap at .49")
	check(doc.set_gate("exit","top",0.5,0.0).ok,".5m circles tangent accepted")
	var exported: Dictionary = doc.export_layout_text()
	check(exported.ok,"new geometry exports")
	if exported.ok:
		var packed: Dictionary = JSON.parse_string(exported.text)
		check(packed.contract=="DEEPEYE-HUMAN-LOCK-20261014/revision2" and packed.requirements_sha256==ScopeSHA,"export binds human revision2")
	var scene: PackedScene = load("res://viewer/main.tscn")
	var viewer = scene.instantiate()
	root.add_child(viewer)
	await process_frame
	for which in ["entry","exit"]:
		var visual = viewer._gate_root.get_node("Gate_"+which)
		var disc: MeshInstance3D = visual.get_node("Disc")
		check(disc.mesh.top_radius==0.25 and disc.mesh.bottom_radius==0.25,"actual native "+which+" aperture .5m")
	viewer.queue_free()
	await process_frame
	print(JSON.stringify({"scope":"revision2 native geometry/editor/export only","passed":failures.is_empty(),"failures":failures,"board":"not_run","all29":"not_run"}))
	quit(0 if failures.is_empty() else 1)

extends Node3D
## Visual channel follows accepted native poses only; never a sensor/collision input.
const SEGMENTS_PER_BATCH := 256
const VISUAL_SPACING_M := 0.02
var _radius := 0.12
var _tail_clearance := 0.52
var _travelled := 0.0
var _points: Array[Vector3] = []
var _distances: Array[float] = []
var _cursor := 0
var _sealed_distance := 0.0
var _sealed_center := Vector3.ZERO
var _rendered_center := Vector3.ZERO
var _has_sealed := false
var _cylinders: MultiMeshInstance3D
var _joins: MultiMeshInstance3D
var _used := 0
var _live_cylinder: MeshInstance3D
var _live_join: MeshInstance3D
var _cylinder_mesh: CylinderMesh
var _join_mesh: SphereMesh
var _material: StandardMaterial3D

func reset_channel(_epoch: String, radius_m: float, half_length_m: float) -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	_radius=radius_m
	_tail_clearance=half_length_m+radius_m
	_travelled=0.0;_points.clear();_distances.clear();_cursor=0
	_sealed_distance=0.0;_has_sealed=false;_used=0
	_sealed_center=Vector3.ZERO;_rendered_center=Vector3.ZERO
	_cylinders=null;_joins=null;_live_cylinder=null;_live_join=null
	_material=StandardMaterial3D.new()
	_material.albedo_color=Color(0.08,0.88,0.27,0.76)
	_material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	_material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	_material.cull_mode=BaseMaterial3D.CULL_DISABLED
	_cylinder_mesh=CylinderMesh.new()
	_cylinder_mesh.top_radius=_radius;_cylinder_mesh.bottom_radius=_radius
	_cylinder_mesh.height=1.0;_cylinder_mesh.radial_segments=12
	_cylinder_mesh.material=_material
	_join_mesh=SphereMesh.new()
	_join_mesh.radius=_radius;_join_mesh.height=2.0*_radius
	_join_mesh.radial_segments=12;_join_mesh.rings=8;_join_mesh.material=_material

func record_accepted_center(center: Vector3) -> void:
	if not center.is_finite():return
	if not _points.is_empty():
		var travelled_now := center.distance_to(_points[-1])
		if travelled_now<0.0000001:return
		_travelled+=travelled_now
	_points.append(center);_distances.append(_travelled)

func _process(_seconds: float) -> void:
	render_pending()

func render_pending() -> void:
	var end_distance := maxf(0.0,_travelled-_tail_clearance)
	if _points.size()<2 or end_distance<=0.0:return
	if not _has_sealed:
		_sealed_center=_points[0];_has_sealed=true
	while _cursor+1<_points.size() and _distances[_cursor+1]<=end_distance:
		_cursor+=1
		if _distances[_cursor]-_sealed_distance>=VISUAL_SPACING_M:
			seal_segment(_points[_cursor],_distances[_cursor])
	var a := _points[_cursor]
	var endpoint := a
	if _cursor+1<_points.size():
		var t := (end_distance-_distances[_cursor])/(_distances[_cursor+1]-_distances[_cursor])
		endpoint=a.lerp(_points[_cursor+1],t)
	_rendered_center=endpoint
	if _live_cylinder==null:
		_live_cylinder=MeshInstance3D.new();_live_cylinder.mesh=_cylinder_mesh;add_child(_live_cylinder)
		_live_join=MeshInstance3D.new();_live_join.mesh=_join_mesh;add_child(_live_join)
	var gap := endpoint.distance_to(_sealed_center)
	_live_cylinder.visible=gap>0.000001
	if _live_cylinder.visible:_live_cylinder.transform=segment_transform(_sealed_center,endpoint)
	_live_join.position=endpoint
	# Retain only the unresolved tail, independent of mission duration.
	if _cursor>256:
		_points=_points.slice(_cursor);_distances=_distances.slice(_cursor);_cursor=0

func seal_segment(endpoint: Vector3, distance_m: float) -> void:
	if _cylinders==null or _used==SEGMENTS_PER_BATCH:
		_cylinders=new_batch(_cylinder_mesh);_joins=new_batch(_join_mesh);_used=0
	_cylinders.multimesh.set_instance_transform(_used,segment_transform(_sealed_center,endpoint))
	_joins.multimesh.set_instance_transform(_used,Transform3D(Basis.IDENTITY,_sealed_center))
	_used+=1
	_cylinders.multimesh.visible_instance_count=_used;_joins.multimesh.visible_instance_count=_used
	_sealed_center=endpoint;_sealed_distance=distance_m

func new_batch(mesh: Mesh) -> MultiMeshInstance3D:
	var node := MultiMeshInstance3D.new()
	var batch := MultiMesh.new()
	batch.transform_format=MultiMesh.TRANSFORM_3D
	batch.mesh=mesh;batch.instance_count=SEGMENTS_PER_BATCH;batch.visible_instance_count=0
	node.multimesh=batch;add_child(node)
	return node

func segment_transform(a: Vector3,b: Vector3) -> Transform3D:
	var direction := b-a
	var y := direction.normalized()
	var helper := Vector3.FORWARD if absf(y.dot(Vector3.FORWARD))<0.9 else Vector3.RIGHT
	var x := y.cross(helper).normalized()
	var z := x.cross(y).normalized()
	return Transform3D(Basis(x,y*direction.length(),z),(a+b)*0.5)

func metrics() -> Dictionary:
	return {"travelled_m":_travelled,"channel_length_m":maxf(0.0,_travelled-_tail_clearance),"channel_diameter_m":2.0*_radius}

func last_rendered_center() -> Vector3:
	return _rendered_center

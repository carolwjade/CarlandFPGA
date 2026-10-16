extends SceneTree
var world: Node3D
func _initialize():
	run.call_deferred()
func vec(a):
	return Vector3(a[0],a[1],a[2])
func arr(v):
	return [v.x,v.y,v.z]
func run():
	world=Node3D.new();root.add_child(world)
	var cases=JSON.parse_string(FileAccess.get_file_as_string("res://independent-cases.json"))
	for c in cases:
		var box=BoxShape3D.new();box.size=vec(c.size);box.margin=0.0
		var body=StaticBody3D.new();body.collision_layer=1;body.collision_mask=0;body.position=vec(c.position)
		var node=CollisionShape3D.new();node.shape=box;body.add_child(node);world.add_child(body)
		var capsule=CapsuleShape3D.new();capsule.radius=c.radius;capsule.height=c.height;capsule.margin=0.0
		var q=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.margin=0.0;q.collision_mask=1;q.collide_with_areas=false;q.collide_with_bodies=true
		# Explicit independent basis, no product adapter call.
		q.transform=Transform3D(Basis(Vector3(1,0,0),Vector3(0,0,1),Vector3(0,-1,0)),Vector3.ZERO)
		await physics_frame;await physics_frame;await process_frame
		var space=world.get_world_3d().direct_space_state
		var initial=space.intersect_shape(q,32).size()
		q.motion=Vector3(0,0,2);var full=Array(space.cast_motion(q))
		# Ten additional syncs eliminate a one-frame registration hypothesis.
		for i in 10:await physics_frame
		q.motion=Vector3(0,0,2);var late_sync=Array(space.cast_motion(q))
		var samples=[]
		for f in [0.0,0.299,0.3,0.31,0.4,0.4453125,0.5,0.7,1.0]:
			q.motion=Vector3.ZERO;q.transform.origin=Vector3(0,0,2*f)
			samples.append({"fraction":f,"origin":arr(q.transform.origin),"hits":space.intersect_shape(q,32).size()})
		# Axial translation union is precisely a longer capsule, same radius.
		var sweep=CapsuleShape3D.new();sweep.radius=capsule.radius;sweep.height=capsule.height+2.0;sweep.margin=0.0
		q.shape=sweep;q.motion=Vector3.ZERO;q.transform.origin=Vector3(0,0,1)
		var swept_hits=space.intersect_shape(q,32).size()
		q.shape=capsule;q.transform.origin=Vector3.ZERO;q.motion=Vector3(0,0,2);q.collision_mask=2
		var masked=Array(space.cast_motion(q));q.collision_mask=1;q.exclude=[body.get_rid()]
		var excluded=Array(space.cast_motion(q));q.exclude=[]
		var subdiv=[]
		for n in [2,4,16,64]:
			var first=-1.0
			for i in n:
				q.transform.origin=Vector3(0,0,2.0*i/n);q.motion=Vector3(0,0,2.0/n)
				var v=space.cast_motion(q)
				if v[0]<1.0:first=(i+v[0])/n;break
			subdiv.append({"n":n,"first_cast_hit":first})
		print("INDEPENDENT "+JSON.stringify({"label":c.label,"box_position":arr(body.position),"box_size":arr(box.size),"capsule_data":PhysicsServer3D.shape_get_data(capsule.get_rid()),"radius":capsule.radius,"height":capsule.height,"initial":initial,"cast":full,"after_10_frames":late_sync,"samples":samples,"swept_capsule_hits":swept_hits,"sweep_height":sweep.height,"masked":masked,"excluded":excluded,"subdiv":subdiv}))
		body.free()
	quit(0)

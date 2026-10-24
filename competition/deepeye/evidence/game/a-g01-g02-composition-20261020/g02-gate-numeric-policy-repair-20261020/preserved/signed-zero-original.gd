extends SceneTree
const Doc = preload("res://editor/scene_document.gd")
const Numeric = preload("res://editor/gate_numeric.gd")
var failures := 0
var checks := 0
func check(value: bool,label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		print("FAIL ",label)
func _initialize() -> void:
	for face in Doc.FACES:
		var zeros := Doc.new()
		zeros.gates.entry = {"face":face,"u":-0.0,"v":0.0}
		zeros.gates.exit.face = "top" if face != "top" else "bottom"
		var reopened := Doc.new()
		check(reopened.apply_layout_text(zeros.export_layout_text().text).ok,"signed zero save/open")
		var zero_bits := PackedByteArray(); zero_bits.resize(16)
		zero_bits.encode_double(0,float(reopened.gates.entry.u));zero_bits.encode_double(8,float(reopened.gates.entry.v))
		check(zero_bits.hex_encode()=="00000000000000800000000000000000","signed zero roundtrip bits")
		for value in [NAN,INF,-INF]:
			for axis in ["u","v"]:
				var doc := Doc.new()
				doc.gates.entry.face = face
				doc.gates.exit.face = "top" if face != "top" else "bottom"
				var old: String = doc.commitment_hash()
				var u: float = value if axis=="u" else 0.0
				var v: float = value if axis=="v" else 0.0
				check(not doc.set_gate("entry",face,u,v).ok,"nonfinite setter")
				check(doc.commitment_hash()==old and doc.undo_depth()==0,"nonfinite no geometry/history mutation")
				doc.gates.entry[axis] = value
				check(not doc.validate_gates().valid,"nonfinite document")
				check(not doc.export_layout_text().ok,"nonfinite encode")
				check(not Numeric.valid_coordinate(value),"nonfinite helper")
	check(Numeric.valid_coordinate(-0.0) and Numeric.valid_coordinate(0.0),"signed zero legal")
	check(not Numeric.circles_overlap(-0.0,0.0,0.3,-0.0),"signed zero tangent")
	check(Numeric.circles_overlap(-0.0,0.0,0.0,-0.0),"signed zero coincidence")
	var limbs: Array = []
	for hex in ["0000000000000000","0000000000000080","0100000000000000","0000000000001000","333333333333c33f","cdccccccccccdc3f","3333333333b32d40","3333333333b32dc0"]:
		var bits: PackedByteArray = String(hex).hex_decode()
		var value: float = bits.decode_double(0)
		limbs.append({"hex":hex,"magnitude":Numeric._magnitude(value)})
	var f := FileAccess.open("res://tests/limb_observations.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(limbs));f.close()
	print("FINITE checks=%d failures=%d" % [checks,failures])
	quit(0 if failures==0 else 1)

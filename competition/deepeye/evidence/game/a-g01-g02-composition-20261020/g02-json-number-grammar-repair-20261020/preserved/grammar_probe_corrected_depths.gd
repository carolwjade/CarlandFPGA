extends SceneTree
const C=preload("res://editor/layout_codec.gd")
const R=preload("res://editor/gate_json_numbers.gd")
const D=preload("res://editor/scene_document.gd")
var checks:=0
var failures:=0
var observations:Array=[]
func check(ok:bool,label:String)->void:
	checks+=1
	if not ok:
		failures+=1
		if failures<18:print("FAIL ",label)
func snapshot(doc)->String:
	return var_to_str([doc.gates,doc.obstacles,doc.commitment_hash(),doc.undo_depth(),doc.redo_depth()])
func reject_preserves(text:String,label:String)->void:
	var doc=D.new()
	check(doc.add_obstacle("water",Vector3(1,0,0),Vector3.ZERO,Vector3(3,2,1)).ok,"seed obstacle "+label)
	check(doc.set_gate("entry","top",1.0,1.0).ok,"seed undo "+label)
	check(doc.set_gate("exit","bottom",2.0,2.0).ok,"seed redo "+label)
	doc.undo()
	check(doc.undo_depth()>0 and doc.redo_depth()>0,"both histories "+label)
	var before:String=snapshot(doc)
	var result:Dictionary=doc.apply_layout_text(text)
	check(not result.ok,"reject "+label)
	check(snapshot(doc)==before,"preserve "+label)
func _initialize()->void:
	for name in ["leading-zero","missing-fraction","missing-fraction-with-exponent","valid-exponent"]:
		var text:String=FileAccess.get_file_as_string("res://grammar-fixtures/"+name+".json")
		var result:Dictionary=C.decode(text)
		var want:bool=name=="valid-exponent"
		check(result.ok==want,"original exact fixture "+name)
		observations.append({"kind":"original","name":name,"accepted":result.ok,"want":want})
		if not want:reject_preserves(text,name)
	var rows:Array=JSON.parse_string(FileAccess.get_file_as_string("res://tests/grammar_cases.json"))
	for row in rows:
		var parser:=JSON.new()
		var parse_error:int=parser.parse(row.text)
		var parsed=parser.data
		var data:Dictionary=parsed if parsed is Dictionary else {}
		var before:PackedByteArray=var_to_bytes(data)
		var result:Dictionary=R.restore(row.text,data)
		check(result.ok==row.want,row.label)
		if row.want and row.preserve:check(var_to_bytes(data)==before,"non-gate values unchanged "+row.label)
		observations.append({"kind":"reader","label":row.label,"engine_parse_error":parse_error,"accepted":result.ok,"want":row.want})
	# Full codec obstacle cases use one encoded legal layout, then vary equivalent
	# numeric spellings. The independent CPython oracle checks each saved text.
	var doc=D.new()
	check(doc.add_obstacle("water",Vector3(1,0,0),Vector3.ZERO,Vector3(3,2,1)).ok,"seed legal obstacle")
	var encoded:Dictionary=doc.export_layout_text()
	check(encoded.ok,"obstacle legal control exports")
	if encoded.ok:
		for token in ["01","1.","1.e0","1e+0","1.00","1E-0"]:
			var changed:String=String(encoded.text).replace('"x": 1.0','"x": '+token)
			check(changed!=encoded.text,"obstacle fixture changes "+token)
			var result:Dictionary=C.decode(changed)
			var want:bool=token in ["1e+0","1.00","1E-0"]
			check(result.ok==want,"obstacle full codec "+token)
			observations.append({"kind":"obstacle","token":token,"accepted":result.ok,"want":want,"text":changed})
			if not want:reject_preserves(changed,"obstacle "+token)
	var out=FileAccess.open("res://tests/grammar_observations.json",FileAccess.WRITE)
	out.store_string(JSON.stringify({"checks":checks,"failures":failures,"observations":observations},"",true,true));out.close()
	print("GRAMMAR checks=%d failures=%d rows=%d"%[checks,failures,rows.size()])
	quit(0 if failures==0 else 1)

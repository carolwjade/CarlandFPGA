extends SceneTree
const N = preload("res://editor/gate_numeric.gd")
const R = preload("res://editor/gate_json_numbers.gd")
const D = preload("res://editor/scene_document.gd")
const C = preload("res://editor/layout_codec.gd")
var failures: Array = []
var observations: Array = []
var checks := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); print("FAIL ", label)
func bits(x: float) -> String:
	var b := PackedByteArray(); b.resize(8); b.encode_double(0,x); return b.hex_encode()
func snapshot(doc) -> String:
	return var_to_str([doc.gates,doc.obstacles,doc.undo_depth(),doc.redo_depth(),doc.commitment_hash()])
func _initialize() -> void:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://tests/independent_geometry.json"))
	for i in rows.size():
		var row: Dictionary = rows[i]; var b: PackedByteArray = String(row.hex).hex_decode()
		var doc = D.new(); doc.gates={"entry":{"face":row.entry_face,"u":b.decode_double(0),"v":b.decode_double(8)},"exit":{"face":row.exit_face,"u":b.decode_double(16),"v":b.decode_double(24)}}
		check(doc.validate_gates().valid==row.want,"geometry %d"%i)
		var wire: Dictionary=doc.export_layout_text(); check(wire.ok==row.want,"export %d"%i)
		if wire.ok:
			var target = D.new(); check(target.apply_layout_text(wire.text).ok,"reopen %d"%i)
			for j in 4:
				var actual: float=target.gates["entry" if j<2 else "exit"]["u" if j%2==0 else "v"]
				check(actual==b.decode_double(j*8) and (actual==0.0 or bits(actual)==bits(b.decode_double(j*8))),"nonzero roundtrip %d/%d"%[i,j])
	var decimals: Array=JSON.parse_string(FileAccess.get_file_as_string("res://tests/independent_decimal.json"))
	var longest := ""
	for i in decimals.size():
		var row: Dictionary=decimals[i]; var t: int=Time.get_ticks_usec();var read: Dictionary=N.read_decimal(row.token)
		observations.append({"kind":"decimal","index":i,"label":row.label,"length":String(row.token).length(),"microseconds":Time.get_ticks_usec()-t,"ok":read.ok,"hex":bits(read.value) if read.ok else ""})
		check(read.ok==row.want,"decimal accepted %d"%i)
		if read.ok:check(bits(read.value)==row.hex,"decimal bits %d"%i)
		if row.label=="maximum-near-midpoint":longest=row.token
	for token in ["01","-01","1.","1.e0","1e","1e+","+0",".1","--1","0x1","1_0"," 1","1\n"]:
		check(not N.read_decimal(token).ok,"numeric grammar "+token)
	var doc=D.new();var good: String=doc.export_layout_text().text
	var valid_escape: String=good.replace('"layout":','"\\u006cayout":').replace('"entry":','"entr\\u0079":').replace('"u":','"\\u0075":')
	check(C.decode(valid_escape).ok,"escaped genuine paths")
	var variants: Array=[
		good.replace('"u": 0.0','"u": 0.0,"\\u0075":0'),
		good.replace('"layout": {','"layout":{},"\\u006cayout":{'),
		good.replace('"entry": {','"entry":{"u":1},"entry":{'),
		good.replace('"u": 0.0','"u":01'),good.replace('"u": 0.0','"u":1.'),
		good.replace('"u": 0.0','"u":14.850000000000001'),
		good.replace('"u": 0.0','"u":'+"[".repeat(33)+"0"+"]".repeat(33)),
		good.replace('"u": 0.0','"u":'+"0."+"0".repeat(2046)+"1")]
	for i in variants.size():
		var text: String=variants[i];check(text!=good,"fixture changes %d"%i)
		var target=D.new();target.set_gate("entry","front",1.0,1.0);target.undo()
		var before: String=snapshot(target);var result: Dictionary=target.apply_layout_text(text)
		check(not result.ok,"rejected import %d"%i);check(snapshot(target)==before,"transaction full state %d"%i)
	# Direct reader isolates extraction from later strict schema rejection.
	var traps: Array=[
		'{"layout":{"gates":{"entry":{"u":14.850000000000001,"v":-0.0},"exit":{"u":0,"v":0}}},"decoy":[{"layout":{"gates":{"entry":{"u":0}}}}],"s":"\\\"u\\\":0"}',
		'{"layout":[{"gates":{"entry":{"u":14.850000000000001}}}]}',
		'{"layout":{"gates":[{"entry":{"u":14.850000000000001}}]}}',
		'{"layout":{"gates":{"entry":[{"u":14.850000000000001}]}}}'
	]
	for i in traps.size():
		var parsed: Dictionary=JSON.parse_string(traps[i]);var result: Dictionary=R.restore(traps[i],parsed)
		check(result.ok,"structural trap %d"%i)
		if i==0:check(bits(parsed.layout.gates.entry.u)=="3433333333b32d40" and bits(parsed.layout.gates.entry.v)=="0000000000000080","real tokens beat decoys")
	# Characterize permissive engine grammar at non-gate numeric locations.
	for token in ["01","1.","1.e0","1e+0"]:
		var text: String=good.replace('"schema": 1','"schema": '+token)
		var result: Dictionary=C.decode(text)
		observations.append({"kind":"schema_grammar","token":token,"ok":result.ok,"text":text})
	# Repeated maximum-length legal gate tokens (four conversions per import).
	var long_wire: String=good.replace('"u": 0.0','"u":'+longest).replace('"v": 0.0','"v":'+longest)
	var parsed: Dictionary=JSON.parse_string(long_wire);var restore_result: Dictionary=R.restore(long_wire,parsed)
	check(restore_result.ok,"long gate restore")
	parsed.layout_hash=C._canon(parsed.layout).sha256_text()
	# All four .3 tokens have a commitment different from the initial zero layout.
	long_wire=long_wire.replace(String(JSON.parse_string(good).layout_hash),String(parsed.layout_hash))
	for i in 3:
		var start: int=Time.get_ticks_usec();var result: Dictionary=C.decode(long_wire)
		observations.append({"kind":"four_max_tokens","iteration":i,"microseconds":Time.get_ticks_usec()-start,"ok":result.ok,"bytes":long_wire.to_utf8_buffer().size()})
		check(result.ok,"four maximum tokens %d"%i)
	var wide: String='{"decoy":{'
	for i in 18000:wide+=('"x%d":0,'%i)
	wide+='"last":0},"layout":{"gates":{"entry":{"u":14.850000000000001}}}}'
	var parsed_wide: Dictionary=JSON.parse_string(wide);var start: int=Time.get_ticks_usec()
	check(R.restore(wide,parsed_wide).ok and bits(parsed_wide.layout.gates.entry.u)=="3433333333b32d40","wide object")
	observations.append({"kind":"wide","microseconds":Time.get_ticks_usec()-start,"bytes":wide.length()})
	var out=FileAccess.open("res://independent-observations.json",FileAccess.WRITE)
	out.store_string(JSON.stringify({"checks":checks,"failures":failures,"observations":observations},"",true,true));out.close()
	print("INDEPENDENT checks=%d failures=%d geometry=%d decimal=%d"%[checks,failures.size(),rows.size(),decimals.size()])
	quit(0 if failures.is_empty() else 1)

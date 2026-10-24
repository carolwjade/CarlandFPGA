extends SceneTree
const Numeric = preload("res://editor/gate_numeric.gd")
const Reader = preload("res://editor/gate_json_numbers.gd")
const Doc = preload("res://editor/scene_document.gd")
const Codec = preload("res://editor/layout_codec.gd")
var checks := 0
var failures := 0
func check(value: bool,label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		if failures<16: print("FAIL ",label)
func bits(value: float) -> String:
	var p := PackedByteArray(); p.resize(8); p.encode_double(0,value); return p.hex_encode()
func reject(text: String,label: String) -> void:
	var doc := Doc.new()
	var hash_before: String = doc.commitment_hash()
	var result: Dictionary = doc.apply_layout_text(text)
	check(not result.ok,label)
	check(hash_before==doc.commitment_hash() and doc.undo_depth()==0 and doc.redo_depth()==0,label+" preserved")
func _initialize() -> void:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://tests/reader_cases.json"))
	for i in rows.size():
		var row: Dictionary = rows[i]
		var read: Dictionary = Numeric.read_decimal(row.token)
		check(bool(read.ok)==bool(row.want),"decimal %d accepted" % i)
		if read.ok: check(bits(read.value)==String(row.hex),"decimal %d exact nearest-even" % i)
	for token in ["01","1.","+1",".3","--1","1e","1e+","NaN","Infinity","abc"]:
		check(not Numeric.read_decimal(token).ok,"non-JSON numeral "+token)
	var doc := Doc.new()
	var good: String = doc.export_layout_text().text
	var data: Dictionary = JSON.parse_string(good)
	# Real codec rejects duplicate decoded keys, including Unicode escape aliases.
	for changed in [good.replace('"u": 0.0','"u": 14.850000000000001, "u": 0.0'),good.replace('"u": 0.0','"u": 14.850000000000001, "\\u0075": 0.0'),good.replace('"schema": 1','"schema": 1, "schema": 1'),good.replace('"entry": {','"entry": {}, "entry": {')]:
		check(changed!=good,"duplicate fixture changed")
		reject(changed,"duplicate rejected")
	# Escaped supported keys remain legitimate; schema stays unchanged.
	var escaped: String = good.replace('"layout":','"\\u006cayout":').replace('"u":','"\\u0075":')
	check(Codec.decode(escaped).ok,"escaped supported keys")
	# Scanner must ignore decoy keys inside strings and nested array/object paths.
	var fake: String = '{"layout":{"gates":{"entry":{"u":14.850000000000001,"v":-0.0},"exit":{"u":0,"v":0}}},"decoy":"\\\"layout\\\":{\\\"gates\\\":{\\\"entry\\\":{\\\"u\\\":0}}}","nested":[{"layout":{"gates":{"entry":{"u":0}}}}]}'
	var fake_data: Dictionary = JSON.parse_string(fake)
	var restored: Dictionary = Reader.restore(fake,fake_data)
	check(restored.ok,"structural extraction accepted")
	check(bits(fake_data.layout.gates.entry.u)=="3433333333b32d40","decoy cannot change gate coordinate")
	check(bits(fake_data.layout.gates.entry.v)=="0000000000000080","signed zero preserved")
	check(fake_data.nested[0].layout.gates.entry.u==0,"unrelated nested values unchanged")
	# Invalid shape, strings, booleans, JSON non-finite and nesting are rejected.
	for token in ['"14.85"','true','null','[]','{}','NaN','Infinity','1e999999999','14.850000000000001','-14.850000000000001']:
		var text: String = good.replace('"u": 0.0','"u": '+token)
		check(text!=good,"invalid token fixture changed")
		reject(text,"invalid gate token "+token)
	for suffix in [",}",",]",' garbage']:
		reject(good.substr(0,good.rfind("}"))+suffix,"trailing malformed")
	var nesting: String = good.replace('"u": 0.0','"u": '+"[".repeat(33)+"0"+"]".repeat(33))
	reject(nesting,"nested gate rejected")
	print("READER checks=%d failures=%d cases=%d" % [checks,failures,rows.size()])
	quit(0 if failures==0 else 1)

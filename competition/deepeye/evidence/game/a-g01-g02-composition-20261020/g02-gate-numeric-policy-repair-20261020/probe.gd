extends SceneTree
const Doc = preload("res://editor/scene_document.gd")
const Codec = preload("res://editor/layout_codec.gd")
var checks := 0
var failures := 0
func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		if failures < 15: print("FAIL ", label)
func _initialize() -> void:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://tests/numeric_cases.json"))
	var observations: Array = []
	for i in rows.size():
		var row: Dictionary = rows[i]
		var bits: PackedByteArray = String(row.hex).hex_decode()
		var entry := {"face":row.entry_face,"u":bits.decode_double(0),"v":bits.decode_double(8)}
		var exit_gate := {"face":row.exit_face,"u":bits.decode_double(16),"v":bits.decode_double(24)}
		var doc := Doc.new()
		doc.gates = {"entry":entry,"exit":exit_gate}
		var valid: bool = doc.validate_gates().valid
		check(valid == bool(row.want), "%d %s document expected=%s got=%s" % [i,row.name,row.want,valid])
		var exported: Dictionary = doc.export_layout_text()
		check(bool(exported.ok) == bool(row.want), "%d encode expected=%s" % [i,row.want])
		# Construct an independent valid envelope, replace its gates and hash.
		var clean := Doc.new()
		var envelope: Dictionary = JSON.parse_string(clean.export_layout_text().text)
		envelope.layout.gates = doc.gates.duplicate(true)
		envelope.layout_hash = Codec._canon(envelope.layout).sha256_text()
		var text := JSON.stringify(envelope,"",true,true)
		var decoded: Dictionary = Codec.decode(text)
		check(bool(decoded.ok) == bool(row.want), "%d decode expected=%s" % [i,row.want])
		var old_hash: String = clean.commitment_hash()
		var old_history: int = clean.undo_depth()
		var applied: Dictionary = clean.apply_layout_text(text)
		check(bool(applied.ok) == bool(row.want), "%d apply expected=%s" % [i,row.want])
		if not bool(row.want):
			check(clean.commitment_hash() == old_hash and clean.undo_depth() == old_history, "%d rejected import preserved geometry/history" % i)
		# Real setter starting with separated faces; invalid entry tested too.
		var setter := Doc.new()
		var other_face: String = "bottom" if row.entry_face == "top" else "top"
		setter.gates = {"entry":entry.duplicate(true),"exit":{"face":other_face,"u":0.0,"v":0.0}}
		if setter.validate_gates().valid:
			var prior: String = setter.commitment_hash()
			var edited: Dictionary = setter.set_gate("exit",row.exit_face,exit_gate.u,exit_gate.v)
			check(bool(edited.ok) == bool(row.want), "%d setter expected=%s" % [i,row.want])
			if not bool(row.want): check(setter.commitment_hash() == prior and setter.undo_depth()==0,"%d rejected setter preserved geometry/history" % i)
		else:
			setter = Doc.new()
			setter.gates.exit.face = other_face
			var prior: String = setter.commitment_hash()
			var edited: Dictionary = setter.set_gate("entry",row.entry_face,entry.u,entry.v)
			check(not edited.ok and setter.commitment_hash()==prior and setter.undo_depth()==0,"%d rejected edge setter preserved geometry/history" % i)
		var wire := ""
		var reopened_hex := ""
		if exported.ok:
			wire = exported.text
			var reopened := Doc.new()
			check(reopened.apply_layout_text(wire).ok,"%d own save reopens" % i)
			var reopened_bits := PackedByteArray(); reopened_bits.resize(32)
			reopened_bits.encode_double(0,float(reopened.gates.entry.u))
			reopened_bits.encode_double(8,float(reopened.gates.entry.v))
			reopened_bits.encode_double(16,float(reopened.gates.exit.u))
			reopened_bits.encode_double(24,float(reopened.gates.exit.v))
			reopened_hex = reopened_bits.hex_encode()
			check(reopened_hex == String(row.hex),"%d own save preserves exact binary64 coordinates" % i)
		var parsed: Dictionary = JSON.parse_string(text)
		var parsed_bits := PackedByteArray()
		parsed_bits.resize(32)
		parsed_bits.encode_double(0,float(parsed.layout.gates.entry.u))
		parsed_bits.encode_double(8,float(parsed.layout.gates.entry.v))
		parsed_bits.encode_double(16,float(parsed.layout.gates.exit.u))
		parsed_bits.encode_double(24,float(parsed.layout.gates.exit.v))
		observations.append({"index":i,"valid":valid,"encoded":exported.ok,"decoded":decoded.ok,"wire":wire,"envelope":text,"parsed_hex":parsed_bits.hex_encode(),"reopened_hex":reopened_hex})
	var f := FileAccess.open("res://tests/numeric_observations.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(observations,"",true,true));f.close()
	print("NUMERIC checks=%d failures=%d rows=%d" % [checks,failures,rows.size()])
	quit(0 if failures==0 else 1)

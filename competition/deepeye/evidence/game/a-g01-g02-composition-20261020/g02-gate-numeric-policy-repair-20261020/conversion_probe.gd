extends SceneTree
func bits(value: float) -> String:
	var p := PackedByteArray();p.resize(8);p.encode_double(0,value);return p.hex_encode()
func _initialize() -> void:
	var rows: Array = []
	for text in ["14.850000000000001","14.85","0.29999999999999999","0.29999999999999993","0.30000000000000004","-0.0","4.9406564584124654e-324","2.2250738585072014e-308","1.4850000000000001e1","0.14999999999999999","-14.850000000000001"]:
		rows.append({"text":text,"json":bits(float(JSON.parse_string(text))),"to_float":bits(text.to_float()),"float_string":bits(float(text))})
	print("CONVERSION ",JSON.stringify(rows))
	quit()

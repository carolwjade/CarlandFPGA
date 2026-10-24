extends SceneTree
const C=preload("res://editor/layout_codec.gd")
func _initialize() -> void:
	var base: String=FileAccess.get_file_as_string("res://good.json")
	var failures := 0
	for token in ["01","1.","1.e0","1e+0"]:
		var text: String=base.replace('"schema": 1','"schema": '+token)
		var result: Dictionary=C.decode(text)
		var expected: bool=token=="1e+0"
		print("GRAMMAR token=",token," accepted=",result.ok," expected_strict_json=",expected)
		if result.ok!=expected:failures+=1
	print("STRICT_JSON failures=",failures)
	quit(0 if failures==0 else 1)

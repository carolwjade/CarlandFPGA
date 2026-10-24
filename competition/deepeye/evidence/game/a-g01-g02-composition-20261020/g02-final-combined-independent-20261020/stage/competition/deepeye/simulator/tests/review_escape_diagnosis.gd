extends SceneTree
func _initialize():
	run.call_deferred()
func run():
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var cases := ["plain", "line\nbreak", "literal\\n", "C:\\new\\test", "literal\\t", "literal\\\\", "文\\n\n\t\\末".repeat(100).substr(0,512)]
	var count := 0
	for reason in cases:
		scene.shell._set_file_failure("escape_diagnosis",reason)
		var expected := "布局文件操作失败：" + reason
		var tooltip: String = scene.shell._action_status_label.get_tooltip()
		var decoded := tooltip.replace("\n", "").c_unescape()
		var first := -1
		for i in range(mini(expected.length(),decoded.length())):
			if expected.unicode_at(i)!=decoded.unicode_at(i):
				first=i
				break
		if first==-1 and expected.length()!=decoded.length():
			first=mini(expected.length(),decoded.length())
		print("EXTRA_ESCAPE_ROW " + JSON.stringify({"reason":reason,"raw_exact":String(scene.shell._action_status_label.text)==expected,"escaped":expected.c_escape(),"tooltip":tooltip,"decoded":decoded,"roundtrip":decoded==expected,"first_difference":first,"expected_length":expected.length(),"decoded_length":decoded.length()}))
		count+=1
	print("EXTRA_DIAGNOSIS cases=%d" % count)
	scene.queue_free()
	await process_frame
	quit(0)

extends RefCounted
## Structural gate-number extraction after the engine validates JSON grammar.
## Does not rewrite JSON or change schema. Duplicate decoded object keys reject.
const Numeric = preload("res://editor/gate_numeric.gd")
const PATHS := [["layout","gates","entry","u"],["layout","gates","entry","v"],
	["layout","gates","exit","u"],["layout","gates","exit","v"]]

static func restore(text: String, data: Dictionary) -> Dictionary:
	var state := {"at":0,"error":"","tokens":{}}
	_walk(text, state, [], 0)
	if state.error != "": return {"ok":false,"reason":state.error}
	_space(text, state)
	if state.at != text.length(): return {"ok":false,"reason":"布局文件 JSON 尾部含多余数据"}
	# Only overwrite numeric scalar gates. The existing codec checks types,
	# supported fields, contract, dimensions, hash and geometry afterwards.
	for index in PATHS.size():
		if not state.tokens.has(index): continue
		var converted: Dictionary = Numeric.read_decimal(state.tokens[index])
		if not converted.ok: return converted
		var path: Array = PATHS[index]
		if data.get("layout") is Dictionary and data.layout.get("gates") is Dictionary:
			var gate = data.layout.gates.get(path[2])
			if gate is Dictionary: gate[path[3]] = converted.value
	return {"ok":true}

static func _space(text: String, state: Dictionary) -> void:
	while state.at < text.length() and text[state.at] in [" ","\t","\r","\n"]: state.at += 1

static func _string_end(text: String, state: Dictionary) -> String:
	var start: int = state.at
	if start >= text.length() or text[start] != "\"":
		state.error = "布局文件 JSON 字符串边界无效"; return ""
	state.at += 1
	while state.at < text.length():
		var ch: String = text[state.at]
		state.at += 1
		if ch == "\\": state.at += 1
		elif ch == "\"": return text.substr(start, state.at - start)
	state.error = "门坐标词元读取失败"
	return ""

static func _walk(text: String, state: Dictionary, path: Array, depth: int) -> void:
	if state.error != "": return
	if depth > 32:
		state.error = "门坐标 JSON 嵌套超限"; return
	_space(text, state)
	if state.at >= text.length():
		state.error = "门坐标词元读取失败"; return
	var ch: String = text[state.at]
	if ch == "{":
		state.at += 1; _space(text, state)
		var keys: Dictionary = {}
		if state.at >= text.length(): state.error = "布局文件 JSON 对象未结束"; return
		if text[state.at] == "}": state.at += 1; return
		while state.error == "":
			var raw_key: String = _string_end(text, state)
			if state.error != "": return
			var key = JSON.parse_string(raw_key)
			if not key is String:
				state.error = "JSON 对象键无效"; return
			if keys.has(key):
				state.error = "布局文件含重复 JSON 键"; return
			keys[key] = true
			_space(text, state)
			if state.at >= text.length() or text[state.at] != ":": state.error = "布局文件 JSON 缺少冒号"; return
			state.at += 1
			_walk(text, state, path + [key], depth + 1)
			if state.error != "": return
			_space(text, state)
			if state.at >= text.length(): state.error = "布局文件 JSON 对象未结束"; return
			if text[state.at] == "}": state.at += 1; return
			if text[state.at] != ",": state.error = "布局文件 JSON 对象分隔无效"; return
			state.at += 1; _space(text, state)
	elif ch == "[":
		state.at += 1; _space(text, state)
		if state.at >= text.length(): state.error = "布局文件 JSON 数组未结束"; return
		if text[state.at] == "]": state.at += 1; return
		var index: int = 0
		while state.error == "":
			_walk(text, state, path + [index], depth + 1)
			if state.error != "": return
			_space(text, state)
			if state.at >= text.length(): state.error = "布局文件 JSON 数组未结束"; return
			if text[state.at] == "]": state.at += 1; return
			if text[state.at] != ",": state.error = "布局文件 JSON 数组分隔无效"; return
			state.at += 1; index += 1
	elif ch == "\"":
		_string_end(text, state)
	elif ch in ["t","f","n"]:
		state.at += 4 if ch != "f" else 5
	else:
		var start: int = state.at
		while state.at < text.length() and text[state.at] in ["0","1","2","3","4","5","6","7","8","9","-","+",".","e","E"]:
			state.at += 1
		if state.at == start: state.error = "布局文件 JSON 数值词元无效"; return
		for index in PATHS.size():
			if path == PATHS[index]: state.tokens[index] = text.substr(start, state.at-start)

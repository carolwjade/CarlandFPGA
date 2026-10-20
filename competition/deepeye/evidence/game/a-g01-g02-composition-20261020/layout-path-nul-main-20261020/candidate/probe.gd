extends SceneTree
const Store = preload("res://layout_store.gd")
var checks := 0
var failures := 0
func check(value: bool, label: String) -> void:
    checks += 1
    if not value:
        failures += 1
        print("FAIL ", label)
func _initialize() -> void:
    var store = Store.new()
    var ordinary: String = OS.get_user_data_dir().path_join("ordinary.json")
    var replacement: String = OS.get_user_data_dir().path_join("valid-" + String.chr(65533) + ".json")
    check(store._absolute_path(ordinary).ok, "ordinary absolute path accepts")
    check(store._absolute_path(replacement).ok, "valid replacement-codepoint path accepts")
    check(not store._absolute_path("").ok, "empty path rejects")
    check(not store._absolute_path("relative.json").ok, "relative path rejects")
    var zero: String = String.chr(0)
    print("ZERO_REPRESENTATION length=", zero.length(), " utf8=", zero.to_utf8_buffer())
    if zero.length() == 1 and zero.unicode_at(0) == 0:
        check(not store._absolute_path(ordinary + zero + "suffix").ok, "actual zero codepoint rejects")
    else:
        print("ZERO_STRING_UNREPRESENTABLE on this engine; no rejection assertion inferred")
    var saved: Dictionary = store.save_new(replacement, "{}")
    check(saved.ok, "save new valid Unicode path succeeds")
    var loaded: Dictionary = store.read_text(replacement)
    check(loaded.ok and loaded.get("text", "") == "{}", "read back valid Unicode path succeeds")
    print("PATH_PROBE checks=", checks, " failures=", failures)
    quit(1 if failures else 0)

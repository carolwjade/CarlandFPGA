extends SceneTree
## Real bounded file I/O on a legal Unicode path. Headless only.
const Store = preload("res://editor/layout_store.gd")
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
    var replacement: String = OS.get_user_data_dir().path_join("valid-" + String.chr(65533) + "-%d.json" % Time.get_ticks_usec())
    check(store._absolute_path(ordinary).ok, "ordinary absolute path accepts")
    check(store._absolute_path(replacement).ok, "valid replacement-codepoint path accepts")
    check(not store._absolute_path("").ok, "empty path rejects")
    check(not store._absolute_path("relative.json").ok, "relative path rejects")
    var saved: Dictionary = store.save_new(replacement, "{}")
    check(saved.ok, "save new valid Unicode path succeeds")
    var loaded: Dictionary = store.read_text(replacement)
    check(loaded.ok and loaded.get("text", "") == "{}", "read back valid Unicode path succeeds")
    print("UNICODE_PATH checks=", checks, " failures=", failures)
    quit(1 if failures else 0)

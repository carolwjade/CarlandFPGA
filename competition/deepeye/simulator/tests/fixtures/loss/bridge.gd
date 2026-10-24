extends "res://editor/layout_commit_bridge.gd"

# Explicit test-only pinned adapter.
func _bundle_spec() -> Dictionary:
	return {"path": "res://tests/fixtures/loss/layout_commit_bundle.json", "sha256": "cb4c32fc617868a564c22eaa92b947f20ca5d4a70526fe3f385a2ef0c6107ba6"}

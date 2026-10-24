extends "res://editor/layout_commit_bridge.gd"

# Explicit test-only pinned adapter.
func _bundle_spec() -> Dictionary:
	return {"path": "res://tests/fixtures/split/layout_commit_bundle.json", "sha256": "5b0b1b74147636143a5369241b11b12d3f64f6d01230df531176ec3de7f09210"}

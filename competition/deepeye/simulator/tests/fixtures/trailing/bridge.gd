extends "res://editor/layout_commit_bridge.gd"

# Explicit test-only pinned adapter.
func _bundle_spec() -> Dictionary:
	return {"path": "res://tests/fixtures/trailing/layout_commit_bundle.json", "sha256": "185aee00fef2b0d6bbb3d3568fb19a9fd3563c98dcaf2858a464474a6ee9eac2"}

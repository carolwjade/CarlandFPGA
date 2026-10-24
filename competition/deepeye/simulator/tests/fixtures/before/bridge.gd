extends "res://editor/layout_commit_bridge.gd"

# Explicit test-only pinned adapter.
func _bundle_spec() -> Dictionary:
	return {"path": "res://tests/fixtures/before/layout_commit_bundle.json", "sha256": "473a7a912a67706d7443cb22e53823b5959d8f2c3a856a4131aebce8073cb6e8"}

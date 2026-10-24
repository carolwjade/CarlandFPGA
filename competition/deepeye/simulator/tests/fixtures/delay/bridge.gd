extends "res://editor/layout_commit_bridge.gd"

# Explicit test-only pinned adapter.
func _bundle_spec() -> Dictionary:
	return {"path": "res://tests/fixtures/delay/layout_commit_bundle.json", "sha256": "62f2c7be36ed01dd0fcd5f200c74108cc66bf5e82d60754b87591aa7438e45c8"}

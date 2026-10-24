extends SceneTree
func _initialize():
	run.call_deferred()
func inspect(node: Node):
	if node.name.contains("Tooltip") or node is PopupPanel:
		print("TOOLTIP_NODE class=%s name=%s" % [node.get_class(), node.name])
		if node is Control:
			print("TOOLTIP_RECT ", node.get_global_rect())
		if node is Window:
			print("TOOLTIP_WINDOW position=%s size=%s" % [node.position, node.size])
	if node is Label and node.name.contains("Tooltip"):
		print("TOOLTIP_LABEL chars=%d lines=%d rect=%s" % [node.text.length(), node.get_line_count(), node.get_global_rect()])
	for child in node.get_children(true):
		inspect(child)
func run():
	var scene = load("res://viewer/main.tscn").instantiate()
	root.add_child(scene)
	for i in range(8):
		await process_frame
	root.size = Vector2i(1920,1080)
	root.content_scale_size = Vector2i(1920,1080)
	root.content_scale_factor = 1.0
	for i in range(8):
		await process_frame
	scene.shell._set_file_failure("tooltip_probe", "边".repeat(512))
	for i in range(8):
		await process_frame
	var motion := InputEventMouseMotion.new()
	motion.position = root.get_final_transform() * scene.shell._action_status_label.get_global_rect().get_center()
	root.push_input(motion)
	await create_timer(1.0).timeout
	print("TOOLTIP_HOVER ", root.gui_get_hovered_control())
	inspect(root)
	scene.queue_free()
	await process_frame
	quit(0)

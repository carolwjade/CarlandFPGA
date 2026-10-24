import importlib.util, json, pathlib, shutil
spec = importlib.util.spec_from_file_location('evidence', pathlib.Path(__file__).with_name('evidence_runner.py'))
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
for mode in ('missing-file','null-factory','enabled-collider'):
    target = evidence.snapshot('fixture-'+mode)
    shutil.copyfile(evidence.EVIDENCE/'test_asset_failure.gd', target/'tests/test_asset_failure.gd')
    (target/'failure-mode.txt').write_text(mode, encoding='utf-8')
    factory = target/'world/asset_library.gd'
    if mode == 'missing-file':
        dependency = target/'world/drill_geometry.gd'
        assert dependency.is_relative_to(evidence.EVIDENCE)
        dependency.unlink()
    else:
        original = factory.read_text(encoding='utf-8')
        needle = 'static func create_obstacle(kind: String) -> Node3D:\n'
        assert original.count(needle) == 1
        if mode == 'null-factory':
            updated = original.replace(needle, needle+'    if kind == "water":\n        return null\n')
        else:
            needle = '    _finalize_asset(root, "obstacle_" + kind + "_v1", "res://world/obstacle_geometry.gd")\n'
            assert original.count(needle) == 1
            updated = original.replace(needle, needle+'    if kind == "water":\n        root.get_node("Collision").get_child(0).disabled = false\n')
        factory.write_text(updated, encoding='utf-8', newline='\n')
    evidence.write('fixture-'+mode+'-manifest.json', evidence.manifest(target))
print('Created 3 isolated negative fixtures; product/B inputs unchanged.')

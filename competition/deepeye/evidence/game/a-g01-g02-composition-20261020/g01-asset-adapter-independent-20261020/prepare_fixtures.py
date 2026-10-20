import pathlib,shutil,json
from review_runner import E, SOURCE, manifest, dump
for mode in ['missing','parser','null','collider','empty-visual','bad-license','signature']:
    p=E/('fixture-'+mode)
    assert not p.exists()
    shutil.copytree(SOURCE,p,ignore=shutil.ignore_patterns('.godot'))
    shutil.copyfile(E/'test_failure_review.gd',p/'tests/test_failure_review.gd')
    (p/'review-mode.txt').write_text(mode,encoding='utf-8')
    factory=p/'world/asset_library.gd'
    text=factory.read_text(encoding='utf-8')
    if mode=='missing': (p/'world/drill_geometry.gd').unlink()
    elif mode=='parser': text='extends RefCounted\nthis is invalid gdscript\n'
    elif mode=='signature': text=text.replace('create_obstacle(kind: String) -> Node3D:', 'create_obstacle(kind: String, required_argument: int) -> Node3D:')
    else:
        insertion={'null':'        root.free()\n        return null','collider':'        root.find_children("*", "CollisionShape3D", true, false)[0].disabled = false','empty-visual':'        for child in root.get_node("Visual").get_children():\n            child.free()','bad-license':'        root.set_meta("source_license", {})'}[mode]
        needle='    _finalize_asset(root, "obstacle_" + kind + "_v1", "res://world/obstacle_geometry.gd")\n'
        assert needle in text
        text=text.replace(needle,needle+'    if kind == "water":\n'+insertion+'\n')
    if mode!='missing': factory.write_text(text,encoding='utf-8')
    dump('fixture-'+mode+'-manifest.json',manifest(p))
print('Created 7 isolated fixtures; product source untouched')

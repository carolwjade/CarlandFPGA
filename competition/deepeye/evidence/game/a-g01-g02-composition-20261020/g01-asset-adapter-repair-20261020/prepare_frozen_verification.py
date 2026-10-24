import shutil
from repair_runner import E,REVIEW,SOURCE,OWNED,dump,manifest,sha
for mode in ['bad-license','signature','empty-visual','null']:
    dest=E/('frozen-fixture-'+mode); assert not dest.exists()
    shutil.copytree(REVIEW/('fixture-'+mode),dest,ignore=shutil.ignore_patterns('.godot'))
    for f in OWNED: shutil.copyfile(SOURCE/f,dest/f)
    assert sha(dest/'tests/test_failure_review.gd')==sha(E/'test_failure_review.gd')
    dump('frozen-fixture-'+mode+'-manifest.json',manifest(dest))
# Exercise the added regression harness against original product bytes. This
# keeps the original source snapshot and every earlier RED receipt untouched.
dest=E/'frozen-harness-red-stage'; assert not dest.exists()
shutil.copytree(E/'original-stage',dest,ignore=shutil.ignore_patterns('.godot'))
shutil.copyfile(SOURCE/'tests/test_viewer_asset_integration.gd',dest/'tests/test_viewer_asset_integration.gd')
dump('frozen-harness-red-stage-manifest.json',manifest(dest))

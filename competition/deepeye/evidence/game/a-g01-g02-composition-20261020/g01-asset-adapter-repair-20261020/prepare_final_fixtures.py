import shutil
from repair_runner import E, REVIEW, SOURCE, OWNED, dump, manifest, sha
for mode in ['bad-license','signature','empty-visual','null']:
    dest=E/('final-fixture-'+mode); assert not dest.exists()
    shutil.copytree(REVIEW/('fixture-'+mode),dest,ignore=shutil.ignore_patterns('.godot'))
    for f in OWNED: shutil.copyfile(SOURCE/f,dest/f)
    assert sha(dest/'tests/test_failure_review.gd')==sha(E/'test_failure_review.gd')
    dump('final-fixture-'+mode+'-manifest.json',manifest(dest))

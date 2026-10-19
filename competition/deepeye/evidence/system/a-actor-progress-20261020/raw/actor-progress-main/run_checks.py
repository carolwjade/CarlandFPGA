"""Bounded offline regression; immutable per-run logs and imported source hashes."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

DEST = Path(__file__).resolve().parent
ROOT = DEST.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
REL = 'competition/deepeye/tests/simulation/test_actor_composition.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tests(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ActorCompositionTests')
    return {node.name: ast.dump(node, include_attributes=False) for node in cls.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}

mode = sys.argv[1]
if mode == 'payload':
    mode = sys.argv[2]
    sys.path[:0] = [str(PRODUCT), str(PRODUCT / 'competition/deepeye'),
                   str(ROOT / '.local/deepeye-host-deps')]
    names = ['competition.deepeye.tests.simulation.test_actor_composition.ActorCompositionTests']
    if mode.startswith('regression'):
        names += ['competition.deepeye.tests.simulation.' + name for name in
                  ('test_actor_owner', 'test_actor_lifetime', 'test_pc_direct_runtime', 'test_motion_executor')]
    old, new = tests(DEST / 'baseline' / REL), tests(PRODUCT / REL)
    changes = [name for name, value in old.items() if new.get(name) != value]
    assert len(old) == 24 and not changes, changes
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    origins = {}
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and Path(path).is_file() and Path(path).resolve().is_relative_to(PRODUCT):
            path = Path(path).resolve()
            origins[name] = {'path': str(path), 'sha256': sha(path)}
    data = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                skipped=len(result.skipped), successful=result.wasSuccessful(),
                original_24_test_methods_ast_unchanged=True, module_origins=origins)
    with (DEST / (mode + '-result.json')).open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2); f.write('\n')
    sys.exit(0 if result.wasSuccessful() else 1)

assert mode.startswith(('focused', 'regression'))
env = os.environ.copy()
temp = DEST / (mode + '-temp'); temp.mkdir(exist_ok=False)
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', TEMP=str(temp), TMP=str(temp))
cmd = [sys.executable, '-B', str(Path(__file__).resolve()), 'payload', mode]
before = {rel: sha(PRODUCT / rel) for rel in (REL, 'competition/deepeye/simulation/authority/actor_composition.py')}
with (DEST / (mode + '.stdout.log')).open('xb') as out, (DEST / (mode + '.stderr.log')).open('xb') as err:
    completed = subprocess.run(cmd, cwd=PRODUCT, env=env, stdout=out, stderr=err, timeout=180)
after = {rel: sha(PRODUCT / rel) for rel in before}
with (DEST / (mode + '-command.json')).open('x', encoding='utf-8') as f:
    json.dump(dict(command=cmd, cwd=str(PRODUCT), returncode=completed.returncode,
                   before=before, after=after, sources_unchanged=before == after), f, indent=2); f.write('\n')
print(json.dumps(dict(mode=mode, returncode=completed.returncode, sources_unchanged=before == after)))
sys.exit(completed.returncode)

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
BASE = PRODUCT / 'competition/deepeye'
OWNED = ['simulation/authority/actor_composition.py', 'tests/simulation/test_actor_composition.py', 'docs/actor_composition.md']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def source_files():
    paths = []
    for directory in ('simulation', 'integration', 'tests/simulation'):
        paths.extend(p for p in (BASE / directory).rglob('*.py') if '__pycache__' not in p.parts)
    paths.extend(BASE / 'docs' / p for p in ('interface.json', 'enums.json', 'host_contract.json', 'host_timing_contract.md'))
    return sorted(paths)

def check_baseline():
    scope = json.loads((ROOT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    pin = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert pin == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    actor = json.loads((HERE.parent / 'actor-binding-repair/source-manifest.json').read_bytes())
    for item in actor['files']: assert sha(PRODUCT / item['path']) == item['sha256'], item['path']
    bridge = json.loads((HERE.parent / 'entry-bridge-implementation/source-manifest.json').read_bytes())
    for rel, item in bridge['candidate'].items(): assert sha(PRODUCT / rel) == item['sha256'], rel
    current = {str(p.relative_to(BASE)).replace('\\', '/'): sha(p) for p in source_files()
               if str(p.relative_to(BASE)).replace('\\', '/') not in OWNED}
    target = HERE / 'baseline.json'
    if target.exists(): assert json.loads(target.read_bytes())['source_hashes'] == current, 'unowned dependencies changed'
    else:
        write(target, dict(requirements_sha256=pin, source_hashes=current,
            selection_sha256=sha(HERE.parent / 'actor-bridge-main-selection.json'),
            actor_manifest_sha256=sha(HERE.parent / 'actor-binding-repair/source-manifest.json'),
            bridge_manifest_sha256=sha(HERE.parent / 'entry-bridge-implementation/source-manifest.json')))
    return current

def main():
    label = sys.argv[1]
    assert label.replace('-', '').isalnum()
    hashes = check_baseline()
    stage = HERE / (label + '-source')
    assert not stage.exists(), 'evidence source is immutable; choose a new label'
    stage.mkdir()
    for p in source_files():
        rel = Path('competition/deepeye') / p.relative_to(BASE)
        dest = stage / rel; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, dest)
    temporary = HERE / (label + '-temp'); temporary.mkdir()
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=os.pathsep.join((str(stage), str(ROOT / '.local/deepeye-host-deps'))),
               TEMP=str(temporary), TMP=str(temporary))
    modules = ['competition.deepeye.tests.simulation.test_actor_composition']
    if label.startswith('green'):
        modules += ['competition.deepeye.tests.simulation.' + n for n in
                    ['test_actor_owner', 'test_actor_lifetime', 'test_pc_direct_runtime', 'test_motion_executor']]
    runner = r'''
import importlib,json,sys,unittest
from pathlib import Path
modules=json.loads(sys.argv[1]); stage=Path.cwd().resolve()
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in modules)
result=unittest.TextTestRunner(verbosity=2).run(suite)
origins={n:getattr(m,'__file__',None) for n,m in list(sys.modules.items()) if n.startswith('competition.deepeye.') and getattr(m,'__file__',None)}
assert all(Path(p).resolve().is_relative_to(stage) for p in origins.values()),origins
Path(sys.argv[2]).write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),successful=result.wasSuccessful(),module_origins=origins),indent=2)+'\n',encoding='utf-8',newline='\n')
sys.exit(0 if result.wasSuccessful() else 1)
'''
    proc = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', runner, json.dumps(modules), str(HERE / (label + '.result.json'))],
                          cwd=stage, env=env, capture_output=True)
    (HERE / (label + '.stdout.txt')).write_bytes(proc.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(proc.stderr)
    result = json.loads((HERE / (label + '.result.json')).read_bytes())
    result.update(exit_code=proc.returncode, source_files=len(hashes), isolated_source=str(stage))
    write(HERE / (label + '.result.json'), result)
    check_baseline()
    print(json.dumps({k: result[k] for k in ['tests','failures','errors','skipped','successful','exit_code']}))
    sys.exit(proc.returncode)

main()

"""Assert actual imported project modules are within the isolated source tree."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
TREE = HERE / 'pinned-source'
label, modules = sys.argv[1], sys.argv[2:]
suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
result = unittest.TextTestRunner(verbosity=2).run(suite)
origins = {}
for name, module in tuple(sys.modules.items()):
    if name.startswith(('competition.deepeye.', 'simulation.isolation.')) or name in (
            'test_windows_cleanup', 'test_host_envelope', 'test_pc_direct_watchdog', 'independent_actor_tests'):
        filename = getattr(module, '__file__', None)
        if filename is None: continue
        path = Path(filename).resolve()
        if name == 'independent_actor_tests':
            assert path.parent == HERE / 'runs' / label
            assert hashlib.sha256(path.read_bytes()).hexdigest() == 'de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f'
        else: assert path.is_relative_to(TREE.resolve()), 'non-pinned project import: ' + str(path)
        origins[name] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
(HERE / (label + '.module-origins.json')).write_text(json.dumps(origins, indent=2) + '\n', encoding='utf-8', newline='\n')
raise SystemExit(0 if result.wasSuccessful() else 1)

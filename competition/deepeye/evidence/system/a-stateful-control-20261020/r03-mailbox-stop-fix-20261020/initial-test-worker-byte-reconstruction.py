"""Run only the proposed mailbox tests from an owned pinned mirror."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
LABEL = sys.argv[1]
assert LABEL in ('red-01', 'green-01')
OUT = D / LABEL
MIRROR = D / 'mirror'
ATTEMPTS = []

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def audit(event, args):
    denied = event.startswith(('socket.', 'subprocess.')) or event in {'os.system', 'os.startfile', 'os.startfile/2', 'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink', 'os.chdir'}
    if event == 'open' and not isinstance(args[0], int):
        path, mode, flags = args
        denied |= 'lease.private' in str(path).lower()
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        denied |= bool(writing) and not Path(path).resolve().is_relative_to(OUT)
    if event == 'os.mkdir':
        denied |= not Path(args[0]).resolve().is_relative_to(OUT)
    if denied:
        ATTEMPTS.append(event)
        raise RuntimeError('prohibited test effect: ' + event)

sys.addaudithook(audit)
snapshots = {}
for name in ('candidate_mailbox.py', 'test_candidate_mailbox.py'):
    p = MIRROR / 'integration' / name
    content = p.read_bytes()
    snapshots[name] = digest(p)
    with (OUT / name).open('xb') as f:
        f.write(content)
sys.path[:0] = [str(MIRROR / 'integration'), str(ROOT / '.local/deepeye-host-deps')]
spec = importlib.util.spec_from_file_location('pinned_mailbox_tests', MIRROR / 'integration/test_candidate_mailbox.py')
tests = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tests
spec.loader.exec_module(tests)
assert Path(tests.mailbox.__file__).resolve() == MIRROR / 'integration/candidate_mailbox.py'
suite = unittest.defaultTestLoader.loadTestsFromTestCase(tests.MailboxTests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
imports = {}
for module in list(sys.modules.values()):
    filename = getattr(module, '__file__', None)
    if filename:
        p = Path(filename)
        if p.is_file():
            imports[str(p.resolve())] = digest(p)
for name, expected in snapshots.items():
    assert digest(MIRROR / 'integration' / name) == expected
checks = {'tests_run': result.testsRun, 'failures': [{'test': str(t), 'traceback': text} for t, text in result.failures], 'errors': [{'test': str(t), 'traceback': text} for t, text in result.errors], 'skipped': result.skipped, 'stop_binding_traces': tests.STOP_BINDING_TRACES, 'prohibited_attempts': ATTEMPTS, 'source_snapshots': snapshots, 'module_file_hashes': imports, 'product_imported_as_mailbox': False, 'R03': 'not_run', 'all29': 'not_run'}
save('checks.json', checks)
print(json.dumps({'tests_run': result.testsRun, 'failure_subcases': len(result.failures), 'errors': len(result.errors), 'stop_traces': len(tests.STOP_BINDING_TRACES), 'source_snapshots': snapshots, 'prohibited_attempts': ATTEMPTS}))
raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)

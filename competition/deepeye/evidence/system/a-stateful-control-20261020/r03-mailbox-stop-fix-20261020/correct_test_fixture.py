"""Retain first GREEN harness failure; ensure each replacement session is new."""
import difflib
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a/competition/deepeye'
stage = __import__('sys').argv[1]
assert stage in ('red-02', 'green-02')
if stage == 'red-02':
    checks = json.loads((D / 'green-01/checks.json').read_bytes())
    assert not checks['failures'] and len(checks['errors']) == 3
    assert all(v['snapshot_after_call']['stopped'] and v['candidate_consumed_after_call'] is None for v in checks['stop_binding_traces'])
    before = (D / 'proposed/test_candidate_mailbox.py').read_bytes()
    assert before == (D / 'red-01/test_candidate_mailbox.py').read_bytes()
    old = b'                fresh = dict(self.ctx, session=8)\n'
    assert before.count(old) == 1
    after = before.replace(old, b"                fresh = dict(self.ctx, session=self.ctx['session']+1)\n")
    (D / 'proposed/test_candidate_mailbox.py').write_bytes(after)
    (D / 'mirror/integration/test_candidate_mailbox.py').write_bytes(after)
    with (D / 'initial-test-proposal.diff').open('xb') as f:
        f.write((D / 'test_candidate_mailbox.py.diff').read_bytes())
    original = (PRODUCT / 'integration/test_candidate_mailbox.py').read_text(encoding='utf-8')
    (D / 'test_candidate_mailbox.py.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), after.decode().splitlines(True), fromfile='original/test_candidate_mailbox.py', tofile='proposed/test_candidate_mailbox.py')), encoding='utf-8')
    record = {'cause': 'Test helper carries self.ctx between mode subcases; fixed session8 is reused in mode2', 'correction': 'Derive strictly new test session from current session+1; no product change', 'old_test_sha256': hashlib.sha256(before).hexdigest(), 'new_test_sha256': hashlib.sha256(after).hexdigest(), 'retained_failed_run': 'green-01', 'no_tolerance_or_policy_change': True}
    with (D / 'test-fixture-correction.json').open('x', encoding='utf-8') as f:
        json.dump(record, f, indent=2)
    original_module = (PRODUCT / 'integration/candidate_mailbox.py').read_bytes()
    assert hashlib.sha256(original_module).hexdigest() == 'c30a52d58a6dde7569ea7f55e751ba766d6887e5858e6b84a1229d8de5cbfca0'
    (D / 'mirror/integration/candidate_mailbox.py').write_bytes(original_module)
else:
    red = json.loads((D / 'red-02/checks.json').read_bytes())
    assert red['tests_run'] == 30 and len(red['failures']) == 6 and not red['errors']
    terminal = json.loads((D / 'red-02/terminal.json').read_bytes())
    assert terminal['exit_code'] == 1 and terminal['all_processes_terminated']
    assert all(v['signaled'] for v in terminal['held_members'])
    assert (D / 'red-02/test_candidate_mailbox.py').read_bytes() == (D / 'proposed/test_candidate_mailbox.py').read_bytes()
    module = (D / 'proposed/candidate_mailbox.py').read_bytes()
    assert hashlib.sha256(module).hexdigest() == '5ca4aafb97f88b3080cc918e38f6c27a462f4caa7af5fa436eeb663f91d3f1d5'
    (D / 'mirror/integration/candidate_mailbox.py').write_bytes(module)
print(json.dumps({'prepared': stage, 'module_sha256': hashlib.sha256((D / 'mirror/integration/candidate_mailbox.py').read_bytes()).hexdigest(), 'test_sha256': hashlib.sha256((D / 'mirror/integration/test_candidate_mailbox.py').read_bytes()).hexdigest()}))

"""Only after verified RED, add the selected single entry decorator."""
import difflib
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a/competition/deepeye'
red = json.loads((D / 'red-01/checks.json').read_bytes())
terminal = json.loads((D / 'red-01/terminal.json').read_bytes())
assert red['tests_run'] == 30 and len(red['failures']) == 6 and not red['errors'] and not red['skipped']
assert terminal['exit_code'] == 1 and terminal['all_processes_terminated']
assert all(v['signaled'] for v in terminal['held_members'])
assert len(red['stop_binding_traces']) == 6
assert all(not v['snapshot_after_call']['stopped'] and v['candidate_consumed_after_call'] == 1 for v in red['stop_binding_traces'])
raw = (PRODUCT / 'integration/candidate_mailbox.py').read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'c30a52d58a6dde7569ea7f55e751ba766d6887e5858e6b84a1229d8de5cbfca0'
assert (D / 'red-01/candidate_mailbox.py').read_bytes() == raw
old = b"    def stop(self, reason='stop'):\n"
assert raw.count(old) == 1
new = raw.replace(old, b'    @_entry\n' + old)
with (D / 'proposed/candidate_mailbox.py').open('xb') as f:
    f.write(new)
(D / 'mirror/integration/candidate_mailbox.py').write_bytes(new)
for name in ('candidate_mailbox.py', 'test_candidate_mailbox.py'):
    before = (PRODUCT / 'integration' / name).read_text(encoding='utf-8')
    after = (D / 'proposed' / name).read_text(encoding='utf-8')
    with (D / (name + '.diff')).open('x', encoding='utf-8') as f:
        f.write(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='original/' + name, tofile='proposed/' + name)))
print(json.dumps({'implementation_change': 'single @_entry decorator above stop', 'new_sha256': hashlib.sha256(new).hexdigest(), 'test_source_unchanged_from_red': (D / 'proposed/test_candidate_mailbox.py').read_bytes() == (D / 'red-01/test_candidate_mailbox.py').read_bytes()}))

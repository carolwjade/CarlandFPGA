"""Independent saved-evidence audit; no live inventory or target-package imports."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
AUTHOR = OUT.parent / 'r02-preflight-implementation-20261020'
PLAN = PRODUCT / '.superpowers/sdd/2026-10-20-r02-readonly-preflight'
EXPECTED = {
    'competition/deepeye/tools/preflight.py': '5052890bc30b9b7a3170a771b1f2e247210d81c11c98c221e07d011db870037d',
    'competition/deepeye/tools/preflight_windows.ps1': '75a0454a82e1f9a27e4ba2fbd2870643121521a0413cbb568909c168477d5cc2',
    'competition/deepeye/tests/test_preflight.py': 'b554eb98c5fe587f6f91fc9fab6b82e0a6155243aafe0ef882c948b0b78b1ebc',
    'competition/deepeye/hardware/preflight.md': '16503a3383843dbdc1554d17ad760bfe92eb831ccc89b04f95560aea7e2beab3',
}
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def read_json(path):
    return json.loads(path.read_bytes())

audit = {'at_utc': datetime.now(timezone.utc).isoformat(),
         'scope': 'saved receipts and focused synthetic checks only; no full-suite or CIM execution',
         'candidate': {}, 'receipts': {}, 'contracts': {}}
package = (PLAN / 'task-1-review-package.md').read_text(encoding='utf-8')
for name, expected in EXPECTED.items():
    raw = (PRODUCT / name).read_bytes()
    assert sha(raw) == expected
    marker = '## ' + name + '\n'
    section = package.split(marker, 1)[1].split('\n## ', 1)[0]
    assert 'SHA256 ' + expected in section
    diff = section.split('```diff\n', 1)[1].split('\n```', 1)[0]
    reconstructed = '\n'.join(line[1:] for line in diff.splitlines()
                              if line.startswith('+') and not line.startswith('+++')) + '\n'
    assert reconstructed == raw.decode('utf-8').replace('\r\n', '\n')
    audit['candidate'][name] = {'sha256': expected, 'bytes': len(raw), 'diff_matches': True}
for label in ('green-final', 'live'):
    receipt_path = AUTHOR / (label + '.receipt.json')
    receipt = read_json(receipt_path)
    for name, expected in EXPECTED.items():
        assert receipt['source_hashes_before'][name] == expected
        assert receipt['source_hashes_after'][name] == expected
    logs = {}
    for channel in ('stdout', 'stderr'):
        raw = (AUTHOR / (label + '.' + channel + '.txt')).read_bytes()
        actual = sha(raw)
        assert actual == receipt[channel + '.txt_sha256']
        logs[channel] = {'sha256': actual, 'bytes': len(raw)}
    audit['receipts'][label] = {'receipt_sha256': sha(receipt_path.read_bytes()),
                              'exit_code': receipt['exit_code'],
                              'timed_out': receipt['timed_out'], 'logs': logs,
                              'candidate_before_after_match': True}
    assert receipt['creationflags'] & 0x08004000 == 0x08004000
assert audit['receipts']['green-final']['exit_code'] == 0
assert audit['receipts']['live']['exit_code'] == 2
assert b'Ran 14 tests in 0.055s' in (AUTHOR / 'green-final.stderr.txt').read_bytes()
stdout = (AUTHOR / 'live.stdout.txt').read_bytes()
filebytes = (AUTHOR / 'host-inventory.json').read_bytes()
live = json.loads(stdout)
assert json.loads(filebytes) == live
assert stdout != filebytes and stdout.replace(b'\r\n', b'\n') == filebytes
assert live['observations'] is None and live['inventory_complete'] is False
assert live['R02'] == 'not_run' and live['formal_acceptance'] is False
assert live['errors'][0]['code'] == 'collector_exit'
assert 'UnauthorizedAccess' in live['errors'][0]['stderr']
audit['live'] = {'stdout_file_json_equal': True, 'stdout_file_bytes_equal': False,
                 'stdout_crlf_count': stdout.count(b'\r\n'),
                 'file_crlf_count': filebytes.count(b'\r\n'),
                 'file_sha256': sha(filebytes),
                 'no_inventory_obtained': True,
                 'launch_error': 'collector_exit/UnauthorizedAccess',
                 'diagnostic_replacement_characters': live['errors'][0]['stderr'].count('\ufffd')}
for label, base in (('root', ROOT), ('product', PRODUCT)):
    contract = read_json(base / 'docs/competition/deepeye-2026/immutable_scope.json')
    digest = sha(json.dumps(contract['requirements'], ensure_ascii=False, sort_keys=True,
                            separators=(',', ':')).encode('utf-8'))
    assert digest == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    assert contract['contract_id'] == 'DEEPEYE-HUMAN-LOCK-20261014'
    assert type(contract['revision']) is int and contract['revision'] == 1
    assert len(contract['requirements']) == 15
    assert {item['id'] for item in contract['requirements']} == {f'H{i:02}' for i in range(1, 16)}
    audit['contracts'][label] = {'requirements_sha256': digest, 'exact_H01_H15': True}
transfer = read_json(ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json')
assert transfer['status'] == 'active'
assert transfer['new_director_thread_id'] == '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
assert transfer['director_generation'] == 2
audit['director'] = {'thread': transfer['new_director_thread_id'], 'active': True, 'generation': 2}
author_audit = read_json(AUTHOR / 'final-audit.json')
protected = {}
for name, expected in author_audit['source_hashes'].items():
    if name in EXPECTED:
        continue
    assert sha((PRODUCT / name).read_bytes()) == expected
    protected[name] = expected
audit['protected_saved_hashes_match_current'] = protected
audit['base'] = {'expected': 'f1d8c6d37bf6e17b3b0b92dc4998a4c7f8959bbe',
                 'saved_author_head': author_audit['git']['head']['stdout'].strip(),
                 'fresh_git_not_executed': True}
assert audit['base']['saved_author_head'] == audit['base']['expected']
spec = importlib.util.spec_from_file_location('independent_preflight_review', PRODUCT / 'competition/deepeye/tools/preflight.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.is_npu_candidate('Unknown device', r'PCI\VEN_1022&DEV_17F0&SUBSYS_0000') is True
assert module.is_npu_candidate('USB Input Device', r'USB\INPUT') is False
# One fake child checks the exact non-UTF8 failure boundary without launching PowerShell.
class Process:
    stdout = io.BytesIO(b'')
    stderr = io.BytesIO(b'path-\xff')
    returncode = 1
    def wait(self, timeout=None):
        return 1
with patch.object(module.subprocess, 'Popen', return_value=Process()) as spawn:
    try:
        module.collect_windows()
    except module.CollectionError as exc:
        assert exc.code == 'collector_exit'
        assert exc.details['stderr'] == 'path-\ufffd'
        command = spawn.call_args.args[0]
        assert '-File' in command and '-Command' not in command
        audit['synthetic'] = {'unknown_DEV_17F0_is_candidate': True,
                              'Input_false_positive_rejected': True,
                              'non_utf8_diagnostic_raw_bytes_discarded': True,
                              'one_fake_launch_only': spawn.call_count == 1,
                              'current_launch_mode': '-File'}
    else:
        raise AssertionError('Expected collector_exit')
for name, expected in EXPECTED.items():
    assert sha((PRODUCT / name).read_bytes()) == expected
with (OUT / 'verification.json').open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(audit, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({'verified_candidates': len(EXPECTED), 'verified_receipts': 2,
                  'saved_tests': 14, 'actual_host_inventory': False,
                  'raw_stdout_equals_output': False, 'synthetic_only': True,
                  'audit_sha256': sha((OUT / 'verification.json').read_bytes())}))

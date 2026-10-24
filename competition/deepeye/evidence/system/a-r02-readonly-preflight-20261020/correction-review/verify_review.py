"""Read saved correction evidence; no collection, suite, or synthetic execution."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
AUTHOR = OUT.parent / 'r02-preflight-fix1-20261020'
OLD = OUT.parent / 'r02-preflight-independent-20261020'
FROZEN = OUT.parent / 'r02-preflight-main-20261020/candidate-v1'
PLAN = PRODUCT / '.superpowers/sdd/2026-10-20-r02-readonly-preflight'
EXPECTED = {
 'competition/deepeye/tools/preflight.py': '94d574a5e6c742fb4948df65e3e9fdfb1137f950ab1b8798317aed1423a7786b',
 'competition/deepeye/tools/preflight_windows.ps1': 'f1af74889d292b1bacfdc1542e81a14fd0b9cfc01bfb8d02d890d3f75a5599ca',
 'competition/deepeye/tests/test_preflight.py': 'a0b4e8b02452647d474e135773cd60b2220e963517dc2f43deb20521347bffc2',
 'competition/deepeye/hardware/preflight.md': '766283e8bcf090c010c80323526ed3a27a91e7b35fa5114469fa56981db5925f',
}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def js(path):
    return json.loads(path.read_bytes())

audit = {'at_utc': datetime.now(timezone.utc).isoformat(), 'candidate': {},
         'scope': 'complete original diff plus exact correction delta; saved evidence only',
         'suite_rerun': False, 'CIM_rerun': False, 'synthetic_checks': 0}
old_audit = js(OLD / 'verification.json')
original_package = (PLAN / 'task-1-review-package.md').read_text(encoding='utf-8')
delta_package = (PLAN / 'task-1-fix1-review-package.md').read_text(encoding='utf-8')
blocks = re.findall(r'```diff\n(.*?)\n```', delta_package, re.S)
assert len(blocks) == 4
for name, expected in EXPECTED.items():
    assert sha(PRODUCT / name) == expected
    frozen = (FROZEN / name).read_text(encoding='utf-8')
    assert sha(FROZEN / name) == old_audit['candidate'][name]['sha256']
    section = original_package.split('## ' + name + '\n', 1)[1].split('\n## ', 1)[0]
    initial = section.split('```diff\n', 1)[1].split('\n```', 1)[0]
    reconstructed = '\n'.join(line[1:] for line in initial.splitlines()
                              if line.startswith('+') and not line.startswith('+++')) + '\n'
    assert reconstructed == frozen
    block = next(b for b in blocks if b.startswith('--- frozen-v1/' + name + '\n'))
    before = frozen.splitlines()
    patched = []
    cursor = 0
    hunks = block.splitlines()[2:]
    index = 0
    hunk_count = 0
    while index < len(hunks):
        match = re.fullmatch(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@.*', hunks[index])
        assert match, hunks[index]
        old_start, old_count, new_start, new_count = map(int, match.groups())
        assert old_start - 1 >= cursor
        patched.extend(before[cursor:old_start-1])
        cursor = old_start-1
        assert len(patched) == new_start-1
        consumed = produced = 0
        index += 1
        while index < len(hunks) and not hunks[index].startswith('@@ '):
            line = hunks[index]
            assert line and line[0] in ' +-'
            if line[0] in ' -':
                assert before[cursor] == line[1:]
                cursor += 1
                consumed += 1
            if line[0] in ' +':
                patched.append(line[1:])
                produced += 1
            index += 1
        assert (consumed, produced) == (old_count, new_count)
        hunk_count += 1
    patched.extend(before[cursor:])
    assert '\n'.join(patched) + '\n' == (PRODUCT / name).read_text(encoding='utf-8')
    audit['candidate'][name] = {'sha256': expected, 'initial_diff_matches_frozen': True,
                               'exact_delta_reconstructs_current': True, 'hunks': hunk_count}
audit['receipts'] = {}
for label in ('red', 'green', 'live'):
    path = AUTHOR / (label + '.receipt.json')
    receipt = js(path)
    logs = {}
    for channel in ('stdout', 'stderr'):
        p = AUTHOR / (label + '.' + channel + '.txt')
        assert sha(p) == receipt[channel + '.txt_sha256']
        logs[channel] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    if label != 'red':
        for name, expected in EXPECTED.items():
            assert receipt['source_hashes_before'][name] == expected
            assert receipt['source_hashes_after'][name] == expected
        assert receipt['exit_code'] == 0 and not receipt['timed_out']
    else:
        assert receipt['exit_code'] == 1
    assert receipt['creationflags'] == 0x08004000
    audit['receipts'][label] = {'sha256': sha(path), 'exit_code': receipt['exit_code'],
                                'logs': logs, 'started_at_utc': receipt['started_at_utc'],
                                'ended_at_utc': receipt['ended_at_utc']}
assert 'Ran 16 tests in 0.050s' in (AUTHOR / 'green.stderr.txt').read_text(encoding='utf-8')
assert 'FAILED (failures=4, errors=2)' in (AUTHOR / 'red.stderr.txt').read_text(encoding='utf-8')
spec = importlib.util.spec_from_file_location('independent_fix1_review', PRODUCT / 'competition/deepeye/tools/preflight.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
stdout = (AUTHOR / 'live.stdout.txt').read_bytes()
filebytes = (AUTHOR / 'host-inventory.json').read_bytes()
live = module.decode_json(stdout)
assert live == module.decode_json(filebytes)
assert stdout != filebytes and stdout.replace(b'\r\n', b'\n') == filebytes
assert live['inventory_complete'] is True and live['errors'] == []
assert live['R02'] == 'not_run' and live['formal_acceptance'] is False
assert not module.validate_inventory(live['observations'])
assert set(live['gates'].values()) <= {'not_run', 'unknown'}
assert live['collector_source_sha256'] == EXPECTED['competition/deepeye/tools/preflight_windows.ps1']
groups = live['observations']['groups']
counts = {key: len(value['rows']) for key, value in groups.items()}
assert counts == {'cpu': 1, 'os': 1, 'gpu': 2, 'npu_candidates': 1, 'drivers': 3, 'disks': 2}
device_ids = {row['device_id'] for key in ('gpu', 'npu_candidates') for row in groups[key]['rows']}
assert {row['device_id'] for row in groups['drivers']['rows']} == device_ids
assert live['package_metadata']['complete'] is True
assert set(live['package_metadata']['packages']) == set(module.PACKAGES)
audit['live'] = {'output_json_equal': True, 'raw_bytes_equal': False,
                 'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
                 'file_sha256': hashlib.sha256(filebytes).hexdigest(),
                 'observed_at_utc': live['observations']['observed_at_utc'],
                 'group_counts': counts, 'typed_groups_valid': True,
                 'driver_correspondence': True, 'collector_digest_matches_current': True,
                 'inventory_collection_only': True}
audit['contracts'] = {}
for label, base in (('root', ROOT), ('product', PRODUCT)):
    contract = js(base / 'docs/competition/deepeye-2026/immutable_scope.json')
    canonical = json.dumps(contract['requirements'], ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')).encode('utf-8')
    digest = hashlib.sha256(canonical).hexdigest()
    assert digest == module.PINNED_REQUIREMENTS_SHA256
    assert contract['contract_id'] == 'DEEPEYE-HUMAN-LOCK-20261014'
    assert type(contract['revision']) is int and contract['revision'] == 1
    assert len(contract['requirements']) == 15
    assert {r['id'] for r in contract['requirements']} == {f'H{i:02}' for i in range(1,16)}
    audit['contracts'][label] = digest
transfer = js(ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json')
assert transfer['status'] == 'active' and transfer['director_generation'] == 2
assert transfer['new_director_thread_id'] == '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
audit['director_unchanged'] = True
author_audit = js(AUTHOR / 'final-audit.json')
protected = {name: expected for name, expected in author_audit['source_hashes'].items() if name not in EXPECTED}
assert all(sha(PRODUCT / name) == expected for name, expected in protected.items())
audit['protected_hashes_match'] = protected
frozen_receipt = js(AUTHOR / 'live.receipt.json')
preserved = {}
for name, expected in frozen_receipt['frozen_hashes_before'].items():
    assert frozen_receipt['frozen_hashes_after'][name] == expected
    if name.endswith('lease.private.json') or name.endswith('reserve-request.json'):
        continue
    assert sha(ROOT / name) == expected
    preserved[name] = expected
audit['preserved_public_evidence_count'] = len(preserved)
audit['original_review_hashes_match'] = all(sha(OLD / name) == expected
                                            for name, expected in js(OLD / 'review-hashes.json').items())
assert audit['original_review_hashes_match']
terminal = js(AUTHOR / 'native-complete-response.json')
assert terminal['status'] == 'completed' and terminal['terminal'] is True
assert terminal['result']['text'] == (AUTHOR / 'final-result.txt').read_text(encoding='utf-8')
audit['author_original_terminal_exact'] = True
source = (PRODUCT / 'competition/deepeye/tools/preflight.py').read_text(encoding='utf-8')
tree = ast.parse(source)
calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
popen_calls = [n for n in calls if isinstance(n.func, ast.Attribute)
               and isinstance(n.func.value, ast.Name) and n.func.value.id == 'subprocess'
               and n.func.attr == 'Popen']
assert len(popen_calls) == 1
assert '"-Command", collector_text]' in source and '"-File"' not in source
assert '"-ExecutionPolicy"' not in source
assert 'collector.read(MAX_JSON_BYTES + 1)' in source
assert 'collector_bytes.decode("utf-8")' in source
assert 'hashlib.sha256(collector_bytes)' in source
ps = (PRODUCT / 'competition/deepeye/tools/preflight_windows.ps1').read_text(encoding='utf-8')
assert '17F0' not in source and '17F0' not in ps
docs = (PRODUCT / 'competition/deepeye/hardware/preflight.md').read_text(encoding='utf-8')
assert 'same JSON object' in docs and 'replacement-decoded' in docs
audit['static_corrections'] = {'F1': 'resolved', 'F2': 'resolved', 'F3': 'resolved',
                               'decoded_diagnostics_limit_documented': True,
                               'Popen_call_sites': 1}
audit['base'] = {'expected': 'f1d8c6d37bf6e17b3b0b92dc4998a4c7f8959bbe',
                 'saved_author_head': author_audit['git']['head']['stdout'].strip(),
                 'fresh_git_executed': False}
assert audit['base']['saved_author_head'] == audit['base']['expected']
for name, expected in EXPECTED.items():
    assert sha(PRODUCT / name) == expected
with (OUT / 'verification.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(audit, f, indent=2)
    f.write('\n')
print(json.dumps({'verified_candidates': 4, 'exact_delta_matches': True,
                  'saved_tests': 16, 'saved_live_exit': 0, 'typed_groups': counts,
                  'original_failure_preserved': True, 'CIM_rerun': False,
                  'synthetic_checks': 0, 'verification_sha256': sha(OUT / 'verification.json')}))

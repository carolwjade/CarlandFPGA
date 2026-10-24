"""Main decision after completed independent source, harness and byte reviews."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
BASE = HERE.parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked(path, expected):
    assert digest(path) == expected, path
    return json.loads(path.read_bytes())

pin = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
for root in (ROOT, PRODUCT):
    scope = json.loads((root / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    assert scope['requirements_sha256'] == pin
    canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(canonical).hexdigest() == pin
transfer = json.loads((ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
assert transfer['status'] == 'active' and transfer['director_generation'] == 2
assert transfer['new_director_thread_id'] == '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
review = checked(BASE / 'isolation-final-review/receipt.json', '2c1d20a53f5b07ffef105c1e706e9e5a3bceefcd9bb96968ebce9e3a249cc59c')
bridge = checked(BASE / 'isolation-publication-review/receipt.json', 'c20703ba5df5c06d3c4ef89ba9d8cd48e57c772a63e17aff3c833cc6e5f373f3')
completion = json.loads((BASE / 'isolation-publication-review/native_complete.json').read_bytes())
completion = json.loads(next(x['text'] for x in completion['content'] if x['type'] == 'text'))
assert completion['status'] == 'completed' and completion['terminal'] is True
assert review['IL-R1'] == review['IL-H1'] == 'closed'
assert bridge['exact_old_replace_crlf_lf'] and bridge['ast_equal'] and bridge['all_raw_equal_git_clean']
manifest_path = BASE / 'isolation-publication-bytes/source-manifest.json'
manifest_pin = '21c42710a33a2c1be2355129cfb113e5f23e261571dd8d8a35a2845f38fe7e63'
manifest = checked(manifest_path, manifest_pin)
for name, expected in manifest.items():
    assert digest(PRODUCT / name) == expected['sha256'], name
assert digest(HERE / 'run_native.py') == '2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613'
preflight = json.loads((HERE / 'runtime-preflight.json').read_bytes())
verified = []
for item in preflight['runtime_files'] + preflight['isolation_module_files']:
    path = Path(item['path'])
    expected = item['sha256']
    if path.name == 'prototype.py':
        assert expected == bridge['prototype_old_sha256']
        expected = bridge['prototype_new_sha256']
    assert digest(path) == expected, path
    verified.append({'path': str(path), 'sha256': expected})
gate = {
    'work_id': 'A-isolation-native-three-case-20261019-v1',
    'main': transfer['new_director_thread_id'], 'generation': 2,
    'accepted_at_utc': datetime.now(timezone.utc).isoformat(),
    'main_accepted_independent_review': True,
    'source_manifest': manifest_path.relative_to(ROOT).as_posix(),
    'source_manifest_sha256': manifest_pin,
    'source_review_sha256': digest(BASE / 'isolation-final-review/receipt.json'),
    'byte_bridge_review_sha256': digest(BASE / 'isolation-publication-review/receipt.json'),
    'harness_sha256': digest(HERE / 'run_native.py'),
    'runtime_and_supporting_sources_verified': verified,
    'requirements_sha256': pin,
    'scope': 'Exactly three fresh CPU AppContainer fixture cases: normal, timeout, persistent receipt failure after CreateProcess.',
    'unresolved_ownership': 'Retain original live owners and runner; do not retry close, reopen PID or kill runner.',
    'original_services_credentials_queues_or_board_selected': False,
    'formal_acceptance': 'not_run',
}
with (HERE / 'native-execution-gate.json').open('x', encoding='utf-8') as stream:
    json.dump(gate, stream, ensure_ascii=False, indent=2)
    stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
print(json.dumps({'gate_created': True, 'source_files': len(manifest), 'runtime_and_supporting_sources': len(verified), 'gate_sha256': digest(HERE / 'native-execution-gate.json')}))

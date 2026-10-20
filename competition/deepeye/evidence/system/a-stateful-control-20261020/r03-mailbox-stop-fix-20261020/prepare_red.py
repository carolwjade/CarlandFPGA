"""Pin read-only inputs and prepare unchanged implementation plus new tests."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a/competition/deepeye'
REVIEW = D.parent / 'r03-mailbox-independent-20261020'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')

manifest = REVIEW / 'artifact-manifest.json'
assert sha(manifest) == 'f9341aa1e1387d06f6301cc9764d57acaff9b3ae60c6535fb9235c79bdfc9ef1'
entries = json.loads(manifest.read_bytes())['files']
assert len(entries) == 26
for name, record in entries.items():
    p = REVIEW / name
    assert p.stat().st_size == record['bytes'] and sha(p) == record['sha256']
scope = json.loads((ROOT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
digest = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert digest == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
transfer = json.loads((ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
assert transfer['status'] == 'active' and transfer['director_generation'] == 2
assert sha(PRODUCT / 'integration/candidate_mailbox.py') == 'c30a52d58a6dde7569ea7f55e751ba766d6887e5858e6b84a1229d8de5cbfca0'
for name, expected in {'win_job.py': '127daf70b2aa6cf3e7a299978596766fc310d191d13f6a2165626f719889052d', 'boundary.py': 'dc27aea6104424fbb2ee9109bb5e2adaf90684161e9d43bd2636b5ea4d6f2908'}.items():
    assert sha(REVIEW / name) == expected
    with (D / name).open('xb') as f:
        f.write((REVIEW / name).read_bytes())
files = ['integration/candidate_mailbox.py', 'integration/test_candidate_mailbox.py', 'integration/boot_profile.py', 'integration/host_envelope.py', 'integration/test_host_envelope.py', 'integration/wire.py', 'integration/motion.py', 'docs/boot_profiles.json', 'docs/host_contract.json', 'docs/host_timing_contract.md', 'docs/interface.json', 'docs/enums.json', 'tests/vectors/r03_mailbox_lifecycle.json']
pins = {}
for name in files:
    p = PRODUCT / name
    pins[str(p)] = {'bytes': p.stat().st_size, 'sha256': sha(p)}
    target = D / 'mirror' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as f:
        f.write(p.read_bytes())
proposed = D / 'proposed'
proposed.mkdir()
raw = (PRODUCT / 'integration/test_candidate_mailbox.py').read_bytes()
marker = b"\n\nif __name__=='__main__':unittest.main(verbosity=2)"
assert raw.count(marker) == 1
addition = b'\n\n' + (D / 'new-test-methods.txt').read_bytes()
updated = raw.replace(marker, addition + b'\nSTOP_BINDING_TRACES = []\n' + marker)
with (proposed / 'test_candidate_mailbox.py').open('xb') as f:
    f.write(updated)
(D / 'mirror/integration/test_candidate_mailbox.py').write_bytes(updated)
save(D / 'input-pins.json', {'files': pins, 'requirements_sha256': digest, 'review_manifest_sha256': sha(manifest), 'review_file_count': len(entries), 'replacement_test_sha256': sha(proposed / 'test_candidate_mailbox.py'), 'original_module_sha256': sha(PRODUCT / 'integration/candidate_mailbox.py'), 'original_test_sha256': sha(PRODUCT / 'integration/test_candidate_mailbox.py'), 'vector_sha256': sha(PRODUCT / 'tests/vectors/r03_mailbox_lifecycle.json')})
print(json.dumps({'prepared': 'RED', 'input_files': len(pins), 'review_files_verified': 26, 'implementation_unchanged': True}))

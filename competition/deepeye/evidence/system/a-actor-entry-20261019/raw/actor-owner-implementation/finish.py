"""Verify frozen bytes and complete only the assigned original native job."""
import asyncio
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
sys.path.insert(0, str(ROOT))
from fpga_mesh.child_control import LocalControlFileClient

JOB = 'child-2c9f9b14e5c94153a6d9fb2f1695b183'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

manifest = json.loads((HERE / 'source-manifest.json').read_bytes())
for row in manifest['files']:
    assert sha(PRODUCT / row['path']) == row['sha256']
    assert sha(HERE / 'candidate' / row['path']) == row['sha256']
for name, expected in manifest['dependencies'].items():
    if name != 'requirements': assert sha(PRODUCT / 'competition/deepeye' / name) == expected
scope = json.loads((PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert hashlib.sha256(canonical).hexdigest() == manifest['dependencies']['requirements']
result = json.loads((HERE / 'final-software-evidence.json').read_bytes())
assert result['exit_code'] == 0
assert sha(HERE / 'final-software-evidence.stderr.txt') == result['stderr_sha256']
assert re.search(r'Ran 116 tests.*\n\s*\nOK\s*$', (HERE / 'final-software-evidence.stderr.txt').read_text(encoding='utf-8'), re.S)
receipt = dict(job_id=JOB, agent_id='/root/worker_results_review_20261018',
    source_manifest_sha256=sha(HERE / 'source-manifest.json'), report_sha256=sha(HERE / 'report.md'),
    tests=dict(discovered=116, passed=116, skipped=0, new_component=52, existing_runtime=64,
               command_result_sha256=sha(HERE / 'final-software-evidence.json'),
               raw_stderr_sha256=result['stderr_sha256']),
    owned_files=5, dependency_hashes_unchanged=True, raw_equals_git_clean=True,
    requirements_sha256=manifest['dependencies']['requirements'], native='not_run', product_run='not_run',
    actual_ai='not_run', full_H12='not_run', all29='not_run', independent_review='pending')
assert not (HERE / 'native_completion_text.txt').exists(), 'Earlier completion may be uncertain; do not replay'
assert not (HERE / 'native_completion.json').exists(), 'Reuse terminal receipt; do not replay'
save('receipt.json', receipt)
lease = json.loads((HERE.parent / 'actor-owner-implementation-lease.private.json').read_text(encoding='utf-8-sig'))
assert lease['job_id'] == JOB
text = ('Retained actor owner author candidate frozen: five new files; actual acquisition orchestration and '
        'original HANDLE zero-time observations; strong registry retention, consumed BOOT/instance binding, '
        'failure-safe same-thread STOP/executor revoke, one-attempt cleanup/quarantine and private failure provenance. '
        '116 offline software tests passed (52 new +64 runtime), zero skips. No native launch/product Run or source edits '
        'outside owned paths; independent review pending. Old dependencies unchanged; raw UTF8 LF equals Git clean. '
        'Post-sample death, creation-to-job-assignment and owner-hang limits retained; real AI/readiness/IPC and all29/H12 '
        'acceptance not_run. Evidence .planning/deepeye-resume-20261018/actor-owner-implementation/. '
        'source-manifest SHA256=' + receipt['source_manifest_sha256'] + '; report SHA256=' + receipt['report_sha256'] +
        '; receipt SHA256=' + sha(HERE / 'receipt.json') + '.')

async def main():
    client = LocalControlFileClient(Path(lease['original_control_file']))
    validation = await client.call('native_validate', dict(job_id=JOB, lease_token=lease['lease_token'],
                                agent_id='/root/worker_results_review_20261018'))
    public_validation = {k: validation.get(k) for k in ('job_id', 'execution_allowed', 'status', 'reason')}
    print(json.dumps(public_validation))
    if validation.get('execution_allowed') is not True: raise RuntimeError('Original job not executable')
    save('final-validation.json', public_validation)
    (HERE / 'native_completion_text.txt').write_text(text + '\n', encoding='utf-8', newline='\n')
    completed = await client.call('native_complete', dict(job_id=JOB, lease_token=lease['lease_token'], text=text))
    public = {k: completed.get(k) for k in ('job_id', 'status', 'terminal', 'result', 'error', 'duplicate')}
    save('native_completion.json', public)
    print(json.dumps(public, ensure_ascii=False))

asyncio.run(main())

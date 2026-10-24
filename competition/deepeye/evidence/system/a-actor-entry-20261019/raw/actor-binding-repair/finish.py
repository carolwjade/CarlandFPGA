"""Check immutable freeze, persist receipt and finish the original repair once."""
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

JOB = 'child-bc96ffdb98124a4682293803674ac807'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
assert not (HERE / 'native_completion_text.txt').exists(), 'Earlier completion uncertain; do not replay'
assert not (HERE / 'native_completion.json').exists(), 'Reuse recorded terminal receipt'
manifest = json.loads((HERE / 'source-manifest.json').read_bytes())
assert sha(HERE / 'source-manifest.json') == '98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670'
for row in manifest['files']:
    for path in (PRODUCT / row['path'], HERE / 'pinned-source' / row['path'], HERE / 'candidate' / row['path']):
        assert sha(path) == row['sha256']
for path, expected in manifest['unchanged_live_nonmoving_dependencies'].items(): assert sha(PRODUCT / path) == expected
logs = {}
for label, expected_count in [('green-repair', 148), ('final-independent8', 8)]:
    result = json.loads((HERE / (label + '.result.json')).read_bytes())
    assert result['exit_code'] == 0 and sha(HERE / (label + '.stderr.txt')) == result['stderr_sha256']
    raw = (HERE / (label + '.stderr.txt')).read_text(encoding='utf-8')
    assert re.search(r'Ran ' + str(expected_count) + r' tests.*\n\s*\nOK\s*$', raw, re.S)
    logs[label] = dict(methods=expected_count, exit_code=0, skipped=0,
        result_sha256=sha(HERE / (label + '.result.json')), raw_stderr_sha256=result['stderr_sha256'])
scope = json.loads((PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert hashlib.sha256(canonical).hexdigest() == manifest['requirements_sha256']
receipt = dict(job_id=JOB, agent_id='/root/worker_results_review_20261018',
    outcome='repair_author_candidate_frozen_pending_independent_review',
    repaired_findings=['AOR-R1', 'AOR-R2', 'AOR-R3'], modified_product_files=6, combined_candidate_files=7,
    actor_lifetime_unchanged=True, base=manifest['base'], source_manifest_sha256=sha(HERE / 'source-manifest.json'),
    report_sha256=sha(HERE / 'report.md'), tests=logs, original_assertions_preserved=manifest['original_test_assertions'],
    independent_script_sha256=manifest['independent_source_sha256'],
    module_origins_sha256=sha(HERE / 'final-independent8.module-origins.json'),
    original_review_manifest_verified=True, raw_equals_git_clean=True,
    requirements_sha256=manifest['requirements_sha256'], new_G06_joint_regression='not_run',
    actual_native_actor='not_run', actual_AI_H12_game_board_Run='not_run', all29='not_run')
save('receipt.json', receipt)
text = ('Actor binding repair author candidate frozen: AOR-R1 per-target original activation callback fences cover '
        'all stale old-owner entry paths and mixed/partial activations; AOR-R2 exact-int Wait classification and '
        'AOR-R3 all-four exact-int inheritance readback defenses. Six modified product files plus unchanged '
        'actor_lifetime.py in seven-file bundle. Fixed3f702903 isolated tree:148 methods passed, exact original8 '
        'independent methods separately passed; original52 actor/16 cleanup assertions preserved, original64 runtime '
        'regressions included. Initial import scaffolding failure accurately retained; final module origins pinned. '
        'No moving live G06 dependency copied/tested, no actual native fixture, network/package/service/board effect. '
        'NewG06 joint regression and independent review remain main-owned/pending. H01-H15 unchanged, all29not_run. '
        'Evidence .planning/deepeye-resume-20261018/actor-binding-repair/. manifestSHA256=' +
        receipt['source_manifest_sha256'] + '; reportSHA256=' + receipt['report_sha256'] +
        '; receiptSHA256=' + sha(HERE / 'receipt.json') + '.')
lease = json.loads((HERE.parent / 'actor-binding-repair-lease.private.json').read_text(encoding='utf-8-sig'))
assert lease['job_id'] == JOB

async def main():
    client = LocalControlFileClient(Path(lease['original_control_file']))
    validation = await client.call('native_validate', dict(job_id=JOB, lease_token=lease['lease_token'],
        agent_id='/root/worker_results_review_20261018'))
    public_validation = {k: validation.get(k) for k in ('job_id', 'execution_allowed', 'status', 'reason')}
    save('final-validation.json', public_validation)
    assert validation.get('execution_allowed') is True
    (HERE / 'native_completion_text.txt').write_text(text + '\n', encoding='utf-8', newline='\n')
    result = await client.call('native_complete', dict(job_id=JOB, lease_token=lease['lease_token'], text=text))
    public = {k: result.get(k) for k in ('job_id', 'status', 'terminal', 'result', 'error', 'duplicate')}
    save('native_completion.json', public)
    print(json.dumps(public, ensure_ascii=False))

asyncio.run(main())

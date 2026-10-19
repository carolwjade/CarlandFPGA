import asyncio
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
sys.path.insert(0, str(ROOT))
from fpga_mesh.child_control import LocalControlFileClient

JOB = 'child-31468257c4304dcab47f85ea86fd6659'
AGENT = '/root/worker_results_review_20261018'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name, data): (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

async def main():
    assert not (HERE / 'native_completion_attempt.json').exists(), 'never replay uncertain completion'
    lease = json.loads((HERE.parent / 'actor-composition-implementation-lease.private.json').read_text(encoding='utf-8-sig'))
    assert lease['job_id'] == JOB
    client = LocalControlFileClient(Path(lease['original_control_file']))
    validation = await client.call('native_validate', dict(job_id=JOB, lease_token=lease['lease_token'], agent_id=AGENT))
    assert validation.get('execution_allowed') is True
    write('validation.json', {k: validation.get(k) for k in ['job_id', 'status', 'execution_allowed', 'reason']})
    manifest = json.loads((HERE / 'source-manifest.json').read_bytes())
    assert sha(HERE / 'source-manifest.json') == '11663f50a276bee91cb77e27693d33e101d72a47c64cba23e269d10589ea034e'
    for item in manifest['files']:
        assert sha(PRODUCT / item['path']) == item['sha256']
        assert sha(HERE / 'candidate' / item['path']) == item['sha256']
    baseline = json.loads((HERE / 'baseline.json').read_bytes())
    for rel, expected in baseline['source_hashes'].items():
        assert sha(PRODUCT / 'competition/deepeye' / rel) == expected
    scope = json.loads((ROOT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(canonical).hexdigest() == baseline['requirements_sha256']
    transfer = json.loads((ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
    assert transfer['status'] == 'active' and transfer['director_generation'] == 2
    assert transfer['new_director_thread_id'] == '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
    tests = {}
    for name in ['red-missing', 'green-first', 'green-second', 'red-postcommit', 'green-final']:
        result = json.loads((HERE / (name + '.result.json')).read_bytes())
        tests[name] = {k: result[k] for k in ['tests','failures','errors','skipped','exit_code']}
        tests[name].update(result_sha256=sha(HERE / (name + '.result.json')),
            stderr_sha256=sha(HERE / (name + '.stderr.txt')))
    write('evidence-manifest.json', dict(job_id=JOB, tests=tests,
        report_sha256=sha(HERE / 'report.md'), source_manifest_sha256=sha(HERE / 'source-manifest.json'),
        baseline_sha256=sha(HERE / 'baseline.json'), run_checks_sha256=sha(HERE / 'run_checks.py'),
        freeze_script_sha256=sha(HERE / 'freeze.py'), complete_script_sha256=sha(Path(__file__)),
        selected_assignment_sha256=sha(HERE.parent / 'actor-composition-implementation-assignment.md'),
        transfer_sha256=sha(ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json')))
    receipt = dict(job_id=JOB, agent_id=AGENT, outcome='three_file_author_candidate_frozen_pending_independent_review',
        product_files=3, source_manifest_sha256=sha(HERE / 'source-manifest.json'),
        evidence_manifest_sha256=sha(HERE / 'evidence-manifest.json'), report_sha256=sha(HERE / 'report.md'),
        tests=tests['green-final'], new_methods=24, existing_methods=148,
        original_dependency_files_unchanged=55, raw_equals_git_clean=True,
        requirements_sha256=baseline['requirements_sha256'],
        production_verifier='unavailable: rejects before ActorRegistry construction/launch',
        native_fixture='not_run', real_AI_H12_Run_game_board='not_run', all29='not_run')
    write('receipt.json', receipt)
    summary = (f'Actor composition three-file candidate frozen pending independent main review. '
        f'source_manifest_sha256={receipt["source_manifest_sha256"]}; report_sha256={receipt["report_sha256"]}; '
        f'receipt_sha256={sha(HERE / "receipt.json")}. '
        '172 isolated offline methods pass,0skip (24new+148existing); 55 accepted source/schema dependencies unchanged. '
        'Original missing-feature RED22, first GREEN-attempt3errors and post-CAS RED1 preserved. '
        'Production unavailable verifier rejects before registry construction/launch; original-actor lifetime fixed, captured-activation dual revocation and retained recovery. '
        'No native fixture/stage/model/board/service/external network/Git effects. H01-H15 pinned c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804; realAI/full H12/Run/all29 not_run.')
    (HERE / 'native_completion_text.txt').write_text(summary + '\n', encoding='utf-8', newline='\n')
    with (HERE / 'native_completion_attempt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(dict(job_id=JOB, text_sha256=hashlib.sha256(summary.encode()).hexdigest())) + '\n')
    result = await client.call('native_complete', dict(job_id=JOB, lease_token=lease['lease_token'], text=summary))
    public = {k: result.get(k) for k in ['job_id','status','terminal','result','error','duplicate']}
    write('native_completion.json', public)
    print(json.dumps(dict(receipt_sha256=sha(HERE / 'receipt.json'), report_sha256=receipt['report_sha256'],
        evidence_manifest_sha256=receipt['evidence_manifest_sha256'], native=public), ensure_ascii=False))

asyncio.run(main())

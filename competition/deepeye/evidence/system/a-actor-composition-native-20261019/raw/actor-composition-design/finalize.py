import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from fpga_mesh.child_control import LocalControlFileClient

JOB = 'child-37334357eaea4e4a91639bad35a47e67'
AGENT = '/root/worker_results_review_20261018'

def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                            encoding='utf-8', newline='\n')

def digest(path):
    raw = path.read_bytes()
    return dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

async def main():
    assert not (HERE / 'native_completion_attempt.json').exists(), 'never replay unknown completion'
    lease = json.loads((HERE.parent / 'actor-composition-design-lease.private.json').read_text(encoding='utf-8-sig'))
    assert lease['job_id'] == JOB
    client = LocalControlFileClient(Path(lease['original_control_file']))
    validation = await client.call('native_validate', dict(job_id=JOB, lease_token=lease['lease_token'], agent_id=AGENT))
    allowed = {k: validation.get(k) for k in ['job_id', 'execution_allowed', 'status', 'reason']}
    assert validation.get('execution_allowed') is True, allowed
    write('validation.json', allowed)
    subprocess.run([sys.executable, '-B', '-X', 'utf8', str(HERE / 'snapshot.py')], check=True)
    manifest = json.loads((HERE / 'input-manifest.json').read_bytes())
    repaired = json.loads((HERE.parent / 'actor-binding-repair/source-manifest.json').read_bytes())
    repair_matches = []
    product = ROOT / '.local/deepeye-implementation-a'
    for item in repaired['files']:
        assert digest(product / item['path'])['sha256'] == item['sha256'], item['path']
        repair_matches.append(item['path'])
    document = (HERE / 'design.md').read_bytes()
    assert b'\r' not in document and document.decode('utf-8')
    assert b'TODO' not in document and b'TBD' not in document
    verification = dict(inputs_unchanged=True, inputs=len(manifest['inputs']),
        original_repair_candidate_matching_files=repair_matches,
        requirements_sha256=manifest['requirements_sha256'],
        design_utf8_lf=True, no_placeholders=True,
        product_imports=False, product_tests='not_run: design-only',
        native_fixture='not_run', real_AI_readiness='not_run', product_Run='not_run',
        all29='not_run', scope='read-only inspection and evidence hashing; not independent product acceptance')
    write('verification.json', verification)
    deliverables = ['design.md', 'input-manifest.json', 'input-recheck.json', 'snapshot.py',
                    'finalize.py', 'validation.json', 'verification.json']
    frozen = dict(schema=1, job_id=JOB, files=[dict(path=n, **digest(HERE / n)) for n in deliverables],
                  product_changes='none by this job', format='UTF-8 LF evidence',
                  source_identity='raw checkout bytes recorded separately from product HEAD')
    write('source-manifest.json', frozen)
    receipt = dict(job_id=JOB, agent_id=AGENT, outcome='design_frozen_pending_main_selection',
        design_sha256=digest(HERE / 'design.md')['sha256'],
        source_manifest_sha256=digest(HERE / 'source-manifest.json')['sha256'],
        input_manifest_sha256=digest(HERE / 'input-manifest.json')['sha256'],
        requirements_sha256=manifest['requirements_sha256'], inputs_verified_unchanged=len(manifest['inputs']),
        recommended_next_slice=['simulation/authority/actor_composition.py',
            'tests/simulation/test_actor_composition.py', 'docs/actor_composition.md'],
        real_producer_gap='No enabled production authority composition or actual model entry in inspected checkout; production channel gate must reject before launch until real verifier exists.',
        real_AI_H12_Run_game_board='not_run', all29='not_run', product_writes=False,
        native_or_network_execution=False)
    write('receipt.json', receipt)
    summary = (f'Actor composition design frozen for main selection. design_sha256={receipt["design_sha256"]}; '
        f'manifest_sha256={receipt["source_manifest_sha256"]}; receipt_sha256={digest(HERE / "receipt.json")["sha256"]}. '
        '47 input hashes unchanged; repaired seven-file candidate matches. Recommend three new files for fixed original-actor lifetime routing, '
        'paired failure/recovery and unavailable-channel gate before native acquisition. Actual AI producer/BOOT/channel/measurement authentication '
        'remain explicit dependencies. Design only; no product writes/imports/tests/native fixture/network. H01-H15 canonical c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 preserved; all29/product Run/both H12 chains not_run.')
    (HERE / 'native_completion_text.txt').write_text(summary + '\n', encoding='utf-8', newline='\n')
    with (HERE / 'native_completion_attempt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(dict(job_id=JOB, text_sha256=hashlib.sha256(summary.encode()).hexdigest())) + '\n')
    response = await client.call('native_complete', dict(job_id=JOB, lease_token=lease['lease_token'], text=summary))
    public = {k: response.get(k) for k in ['job_id', 'status', 'terminal', 'result', 'error', 'duplicate']}
    write('native_completion.json', public)
    print(json.dumps(dict(design_sha256=receipt['design_sha256'], manifest_sha256=receipt['source_manifest_sha256'],
        receipt_sha256=digest(HERE / 'receipt.json')['sha256'], native=public), ensure_ascii=False))

asyncio.run(main())

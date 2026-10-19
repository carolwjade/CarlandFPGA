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

JOB = 'child-9b77838d22574ae49550293f0b1d61c3'
AGENT = '/root/worker_results_review_20261018'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name, data): (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

async def main():
    assert not (HERE / 'native_completion_attempt.json').exists(), 'no uncertain completion replay'
    lease = json.loads((HERE.parent / 'actor-progress-design-lease.private.json').read_text(encoding='utf-8-sig'))
    assert lease['job_id'] == JOB
    client = LocalControlFileClient(Path(lease['original_control_file']))
    validation = await client.call('native_validate', dict(job_id=JOB, lease_token=lease['lease_token'], agent_id=AGENT))
    assert validation.get('execution_allowed') is True
    write('validation.json', {k: validation.get(k) for k in ['job_id','status','execution_allowed','reason']})
    subprocess.run([sys.executable, '-B', '-X', 'utf8', str(HERE / 'snapshot.py')], check=True)
    inputs = json.loads((HERE / 'input-manifest.json').read_bytes())
    design = (HERE / 'design.md').read_bytes()
    assert b'\r' not in design and design.decode('utf-8')
    assert b'TODO' not in design and b'TBD' not in design
    write('verification.json', dict(inputs_unchanged=len(inputs['inputs']), design_utf8_lf=True,
        immutable_requirements_verified=True, accepted_composition_sources_verified=True,
        selected_main_record_sha256='68d826276c8eb4ebdb8ddcb61f8158619b5aa179c57fe904119807e110ade67f',
        independent_findings_read_in_full=True, original_negative_witness_retained=True,
        code_implementation=False, tests='not_run: design-only; existing independent evidence read',
        product_imports=False, native_IPC_network_service_board=False,
        original_interpreter_48521='not inspected or operated', source38_snapshots='unchanged/not operated'))
    files = ['design.md','input-manifest.json','input-recheck.json','snapshot.py','complete.py','validation.json','verification.json']
    write('source-manifest.json', dict(job_id=JOB, files=[dict(path=name,sha256=sha(HERE/name),bytes=(HERE/name).stat().st_size) for name in files],
        source_identity='raw source bytes listed in input-manifest; no Git normalization claim',
        product_changes='none', requirements_sha256=inputs['requirements_sha256']))
    receipt = dict(job_id=JOB, agent_id=AGENT, outcome='progress_final_fence_design_frozen_pending_main_selection',
        design_sha256=sha(HERE / 'design.md'), source_manifest_sha256=sha(HERE / 'source-manifest.json'),
        input_manifest_sha256=sha(HERE / 'input-manifest.json'), inputs_unchanged=44,
        requirements_sha256=inputs['requirements_sha256'],
        recommendation='private per-activation command-bound progress gate in existing composition; combine original actor AiLease deadline with immutable verified completion deadline',
        proposed_owned_paths=['competition/deepeye/simulation/authority/actor_composition.py',
            'competition/deepeye/tests/simulation/test_actor_composition.py','competition/deepeye/docs/actor_composition.md'],
        genuine_progress_source='cannot establish without real trusted model/backend completion producer; keep production gate unavailable',
        planned_RED='expire progress deadline during actual geometry and inside commit before final fence; current life/heartbeat/TTL stay fresh',
        new_tests_or_implementation='not_run: design-only',
        native_AI_full_H12_Run_game_board_all29='not_run', original_interpreter_48521='untouched')
    write('receipt.json', receipt)
    summary = (f'Progress/final-fence design frozen for main selection. design_sha256={receipt["design_sha256"]}; '
        f'manifest_sha256={receipt["source_manifest_sha256"]}; receipt_sha256={sha(HERE/"receipt.json")}. '
        '44 input hashes unchanged; full independent negative witness retained. Recommend three existing composition/test/doc paths: '
        'private activation/command-bound original-completion gate combined through min(original actor AiLease deadline, progress deadline), '
        'so existing actual final fence bounds whole dt without channel callback/I/O after fence. Genuine model/backend completion producer is absent; '
        'no receipt/duplicate/alive renewal and production gate stays unavailable. Design only; no source edits/tests/product imports/native/IPC/network; '
        'interpreter48521/source38 untouched. H01-H15 canonical c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804; realAI/full H12/Run/all29 not_run.')
    (HERE / 'native_completion_text.txt').write_text(summary+'\n', encoding='utf-8', newline='\n')
    with (HERE / 'native_completion_attempt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(dict(job_id=JOB,text_sha256=hashlib.sha256(summary.encode()).hexdigest()))+'\n')
    response = await client.call('native_complete', dict(job_id=JOB, lease_token=lease['lease_token'], text=summary))
    public = {k: response.get(k) for k in ['job_id','status','terminal','result','error','duplicate']}
    write('native_completion.json', public)
    print(json.dumps(dict(design_sha256=receipt['design_sha256'],manifest_sha256=receipt['source_manifest_sha256'],
        receipt_sha256=sha(HERE / 'receipt.json'), native=public),ensure_ascii=False))

asyncio.run(main())

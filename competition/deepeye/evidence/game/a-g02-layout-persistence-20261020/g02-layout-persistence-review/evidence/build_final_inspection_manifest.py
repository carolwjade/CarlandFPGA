import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd()
REVIEW = ROOT / '.planning/deepeye-resume-20261018/g02-layout-persistence-review'
OUT = REVIEW / 'inspection_manifest.json'

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def rec(rel_or_path):
    p = Path(rel_or_path)
    if not p.is_absolute():
        p = ROOT / p
    data = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix(), 'exists': True, 'bytes': len(data), 'sha256': sha_bytes(data)}

def rel_rec(path):
    data = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': sha_bytes(data)}

def load_json(path):
    data = path.read_bytes()
    if data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
        return json.loads(data.decode('utf-16'))
    return json.loads(data.decode('utf-8-sig'))
findings = REVIEW / 'findings.md'
base = load_json(OUT)
strict = REVIEW / 'evidence/pins-final-strict-02.stdout.json'
scope_audit_path = REVIEW / 'evidence/final-scope-audit-03/stdout.json'
scope_audit = load_json(scope_audit_path)
strict_json = load_json(strict)
before = REVIEW / 'evidence/pins-before.stdout.json'
after = REVIEW / 'evidence/pins-after.stdout.json'
json_validation = REVIEW / 'evidence/json-validation-01'
tooling = REVIEW / 'evidence/reviewer-tooling-failures.md'

scope_input_current=[]
for item in base.get('scope_inputs',[]):
    p=ROOT/item['path']
    if p.is_file():
        b=p.read_bytes(); current={'path':item['path'],'bytes':len(b),'sha256':sha_bytes(b)}
        item['current_bytes']=current['bytes']; item['current_sha256']=current['sha256']
        item['drifted_since_inspection']=current['bytes']!=item.get('bytes') or current['sha256']!=item.get('sha256')
        if item['drifted_since_inspection']:
            scope_input_current.append({'path':item['path'],'inspected_bytes':item.get('bytes'),'inspected_sha256':item.get('sha256'),'current_bytes':current['bytes'],'current_sha256':current['sha256'],'classification':'external non-owned input drift; original inspected bytes remain pinned'})
base['scope_input_external_drift']=scope_input_current
base['generated_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
head_meta = scope_audit['head_commit_metadata']['stdout'].splitlines()
base['product'] = {
    'root': '.local/deepeye-implementation-a',
    'head_at_task_start_and_initial_pin_audits': '678e01dd097f326e5bf724dc9db9e6b3e388384d',
    'initial_product_head_from_author': '889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1',
    'head_at_final_read_only_audit': scope_audit['final_head'],
    'head_advanced_during_review_by_external_main_commit': scope_audit['head_advanced_during_review'],
    'final_head_commit': {
        'hash': head_meta[0] if len(head_meta)>0 else None,
        'parents': head_meta[1] if len(head_meta)>1 else None,
        'committed_at': head_meta[2] if len(head_meta)>2 else None,
        'subject': head_meta[3] if len(head_meta)>3 else None,
    },
    'reviewed_scope_changed_path_count': len(scope_audit['reviewed_scope_changed_paths']),
    'reviewed_scope_changed_paths': scope_audit['reviewed_scope_changed_paths'],
    'scoped_status': scope_audit['candidate_status'],
    'scoped_status_classification': 'exactly two modified and four untracked candidate files',
    'scoped_diff_check_exit': next(x['exit_code'] for x in scope_audit['git_commands'] if x['argv'][-1]=='--check' or '--check' in x['argv']),
    'product_writes_by_review': False,
    'godot_directory': scope_audit['godot_directory'],
    'git': scope_audit['git'],
}

candidate=[]
for item in base['candidate_sources']:
    actual=rec(item['product_path'])
    if actual['sha256'] != item['sha256'] or actual['bytes'] != item['bytes']:
        raise SystemExit('candidate identity changed: '+item['product_path'])
    candidate.append(item)
base['candidate_sources']=candidate

deps=[]
for item in base['dependencies']:
    actual=rec(item['product_path'])
    if actual['sha256'] != item['after_sha256'] or item['before_sha256'] != item['after_sha256']:
        raise SystemExit('dependency identity changed: '+item['path'])
    deps.append(item)
base['dependencies']=deps

base['pin_audit'] = {
    'before': {'path': rel_rec(before)['path'], **{k:v for k,v in rel_rec(before).items() if k!='path'}, 'status':load_json(before).get('status'), 'checks':len(load_json(before).get('checks',[])), 'failures':len(load_json(before).get('failures',[]))},
    'after': {'path': rel_rec(after)['path'], **{k:v for k,v in rel_rec(after).items() if k!='path'}, 'status':load_json(after).get('status'), 'checks':len(load_json(after).get('checks',[])), 'failures':len(load_json(after).get('failures',[]))},
    'strict_final': {'path': rel_rec(strict)['path'], **{k:v for k,v in rel_rec(strict).items() if k!='path'}, 'status':strict_json.get('status'), 'checks':len(strict_json.get('checks',[])), 'failures':strict_json.get('failures')},
    'reviewed_scope_audit': {'path': rel_rec(scope_audit_path)['path'], **{k:v for k,v in rel_rec(scope_audit_path).items() if k!='path'}, 'status':scope_audit['status'], 'checks':len(scope_audit['checks']), 'failures':len(scope_audit['failures']), 'nonhead_checks_pass':scope_audit['strict_final_summary']['nonhead_checks_pass']},
    'six_dependencies_evidence_sections_identical': True,
    'strict_final_explanation': 'Sole strict failure is exact product_head drift from an external main commit after the independent runs; the other 73 checks and all reviewed source bytes remain valid.',
}

base['json_validation'] = {
    'script': rel_rec(REVIEW/'evidence/validate_json.py'),
    'command_record': rel_rec(json_validation/'command.json'),
    'stdout': rel_rec(json_validation/'stdout.log'),
    'stderr': rel_rec(json_validation/'stderr.log'),
    'exit': rel_rec(json_validation/'exit.txt'),
    'result': 'PASS',
    'files_checked': 45,
    'bad_files': 0,
    'scope': 'review-root *.json + evidence/**/*.json + runs/**/*.json; UTF-8/UTF-8-BOM/UTF-16 BOM aware; intentional env fixtures excluded',
}

doc = next(x for x in strict_json['six_files'] if x['path'].endswith('layout_persistence.md'))
base['documentation_byte_identity'] = {
    'path': '.local/deepeye-implementation-a/'+doc['path'],
    'actual_bytes': doc['bytes'],
    'actual_sha256': doc['sha256_actual'],
    'actual_raw_git_blob_sha1': doc['raw_git_blob_sha1'],
    'clean_lf_git_blob_sha1': doc['lf_git_blob_sha1'],
    'manifest_git_blob_sha1': doc['git_blob_sha1_manifest'],
    'crlf_count': doc['crlf_count'],
    'classification': doc['classification'],
    'author_manifest_edited_by_reviewer': False,
}

evfiles=sorted([p for p in (REVIEW/'evidence').rglob('*') if p.is_file()], key=lambda p:p.as_posix().lower())
runfiles=sorted([p for p in (REVIEW/'runs').rglob('*') if p.is_file()], key=lambda p:p.as_posix().lower())
base['review_evidence']=[rel_rec(p) for p in evfiles]
base['review_evidence_count']=len(evfiles)
base['review_run_files']=[rel_rec(p) for p in runfiles]
base['review_run_file_count']=len(runfiles)
base['review_inputs']=[rec(REVIEW/'assignment.md'), rec(REVIEW/'dispatch-started.json'), rec(REVIEW/'dispatch-result.json'), rec(findings)]
base['findings_file']={'path':rel_rec(findings)['path'], 'bytes':rel_rec(findings)['bytes'], 'sha256':rel_rec(findings)['sha256']}
base['tooling_failures']={'path':rel_rec(tooling)['path'], 'bytes':rel_rec(tooling)['bytes'], 'sha256':rel_rec(tooling)['sha256'], 'note':'All review tooling failures are preserved; none is classified as a candidate failure.'}
base['scope_status'] = {
    'bounded_headless_software_review':'PASS',
    'blocking_implementation_defects':0,
    'low_findings':1,
    'info_findings':3,
    'product_accepted':False,
    'all_29_taskbook_cards':'not_run',
    'formal29':'not_run',
    'g02':'not_run',
    'h01_h15':'not_run',
    'native_ui':'not_run',
    'physical_collision':'not_run',
    'os_isolation':'not_run',
    'ai_access':'not_run',
    'board_run':'not_run',
    'dual_h12':'not_run',
}
base['prohibited_actions_not_performed']=['source_edit','product_write','author_evidence_write','git_commit','git_push','new_thread','peer_or_group_message','board_operation','service_or_driver_change','dependency_install','native_ui_run','product_cache_write']
base['independent_execution_environment']={'python':'.local/venv/Scripts/python.exe -B','PYTHONPATH':'.local/deepeye-host-deps','PYTHONDONTWRITEBYTECODE':'1','all_engine_runs_staged':True,'all_engine_processes_confirmed_exited':True}
base['implementation_review'] = {
    'codec_and_boundaries':'inspected strict schema/version/type/finite/depth/size/unknown-field paths',
    'filesystem_publish':'inspected bounded read, temp write/reread, rename, sequential target preservation and documented concurrent limitation',
    'document_semantics':'inspected validate-before-mutation, undo/redo/selection/history reset, seed unknown/origin and run/link preservation',
    'viewer_and_ui_path':'inspected original viewer signals, toolbar/FileDialog wiring, callback consumption, state recheck and cancellation',
    'dynamic_loading_and_authority':'no ResourceLoader/eval/dynamic-load network/process path found in final seam; Run/link authority unchanged',
    'native_ui_and_engine_interaction':'not_run',
}

base['review_evidence_files_pinned']=len(evfiles)
base['review_run_files_pinned']=len(runfiles)
base['review_status_note']='Bounded headless software candidate review only; main owns adoption and all later native/formal acceptance.'
OUT.write_text(json.dumps(base, indent=2, ensure_ascii=False)+"\n", encoding='utf-8')
print('WROTE='+OUT.as_posix())
print('REVIEW_EVIDENCE='+str(len(evfiles)))
print('RUN_FILES='+str(len(runfiles)))
print('FINDINGS_SHA256='+rel_rec(findings)['sha256'])
print('STRICT_FINAL_FAILURES='+str(len(strict_json.get('failures',[]))))
print('SCOPE_AUDIT_STATUS='+scope_audit['status'])

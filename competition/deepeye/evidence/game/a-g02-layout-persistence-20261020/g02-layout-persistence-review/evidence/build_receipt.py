import datetime
import hashlib
import json
import re
from pathlib import Path

ROOT = Path.cwd()
REVIEW = ROOT / '.planning/deepeye-resume-20261018/g02-layout-persistence-review'
OUT = REVIEW / 'receipt.json'
MANIFEST = REVIEW / 'inspection_manifest.json'

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def rec(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    data = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': sha_bytes(data)}

def load_json(path):
    p=Path(path)
    if not p.is_absolute(): p=ROOT/p
    data=p.read_bytes()
    if data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
        return json.loads(data.decode('utf-16'))
    if data.startswith(b'\xef\xbb\xbf'):
        return json.loads(data.decode('utf-8-sig'))
    return json.loads(data.decode('utf-8'))

manifest = load_json(MANIFEST)
audit = load_json(ROOT/'.planning/deepeye-resume-20261018/g02-layout-author-handoff-audit.json')
scope_audit = load_json(REVIEW/'evidence/final-scope-audit-03/stdout.json')
strict = load_json(REVIEW/'evidence/pins-final-strict-02.stdout.json')

run_root = REVIEW/'runs'
run_specs = {
    'engine-version-02':'preserved PowerShell Start-Process probe with unavailable ExitCode after confirmed exit',
    'engine-version-03':'preserved first .NET version probe with unavailable ExitCode after confirmed exit',
    'engine-version-04':'independent pinned-engine version probe',
    'persistence-01':'independent fresh-staged 618-check layout persistence suite',
    'editor-01':'independent fresh-staged untouched 696-check editor suite',
    'smoke-01':'independent fresh-staged headless scene smoke',
    'rename-probe-01':'independent disposable rename destination-exists probe',
    'flow-counterexample-01':'independent dialog state/cancellation/duplicate-callback counterexample',
    'import-origin-01':'independent source/resource import-origin probe',
}
runs=[]
for label in sorted(run_specs):
    rd=run_root/label
    cmd=load_json(rd/'command.json')
    result=load_json(rd/'result.json')
    stdout=(rd/'stdout.log').read_bytes()
    stderr=(rd/'stderr.log').read_bytes()
    stdout_text=stdout.decode('utf-8','replace')
    stderr_text=stderr.decode('utf-8','replace')
    files=sorted([p for p in rd.iterdir() if p.is_file()], key=lambda p:p.name.lower())
    exit_file=(rd/'exit_code.txt')
    process_file=(rd/'process_exited.txt')
    checks=None; failures=None
    tests_matches=re.findall(r'(?:TESTS|COUNTEREXAMPLE_FLOW) checks=(\d+) failures=(\d+)', stdout_text)
    if tests_matches:
        checks=int(tests_matches[-1][0]); failures=int(tests_matches[-1][1])
    markers=[line for line in stdout_text.splitlines() if line.startswith(('RESULT ','SCENE_SMOKE_PASS','COUNTEREXAMPLE_FLOW_RESULT','RENAME_EXISTING_','TARGET_AFTER_HEX','ORIGIN ' ,'ORIGIN_SCENE='))]
    runs.append({
        'label':label,
        'purpose':run_specs[label],
        'command':cmd,
        'command_file':rec(rd/'command.json'),
        'result':result,
        'result_file':rec(rd/'result.json'),
        'exit_code':result.get('exit_code'),
        'exit_code_file_value':exit_file.read_text(encoding='ascii').strip() if exit_file.exists() else None,
        'process_exited_file_value':process_file.read_text(encoding='ascii').strip() if process_file.exists() else None,
        'timed_out':result.get('timed_out'),
        'process_started':result.get('process_started'),
        'stdout':rec(rd/'stdout.log'),
        'stderr':rec(rd/'stderr.log'),
        'checks':checks,
        'failures':failures,
        'markers':markers,
        'raw_files':[rec(p) for p in files],
    })
run_by_label={x['label']:x for x in runs}

def require(cond,msg):
    if not cond:
        raise SystemExit(msg)

require(run_by_label['persistence-01']['exit_code']==0 and run_by_label['persistence-01']['checks']==618 and run_by_label['persistence-01']['failures']==0, 'persistence independent count mismatch')
require(run_by_label['editor-01']['exit_code']==0 and run_by_label['editor-01']['checks']==696 and run_by_label['editor-01']['failures']==0, 'editor independent count mismatch')
require(run_by_label['flow-counterexample-01']['exit_code']==0 and run_by_label['flow-counterexample-01']['checks']==11 and run_by_label['flow-counterexample-01']['failures']==0, 'flow counterexample mismatch')
require(any(x=='SCENE_SMOKE_PASS document=1 shell=1 file_dialog=1' for x in run_by_label['smoke-01']['markers']), 'smoke marker missing')
require(run_by_label['rename-probe-01']['exit_code']==0 and any(x.startswith('RENAME_EXISTING_NAME=') for x in run_by_label['rename-probe-01']['markers']), 'rename probe marker missing')
require(run_by_label['import-origin-01']['exit_code']==0, 'import origin run failed')
require(run_by_label['engine-version-04']['exit_code']==0, 'engine version probe failed')

import_text=run_by_label['import-origin-01']['stdout']['path']
import_stdout=(ROOT/import_text).read_text(encoding='utf-8',errors='replace')
origin_lines=[line for line in import_stdout.splitlines() if line.startswith(('ORIGIN ','ORIGIN_SCENE='))]
require(len(origin_lines)==6, 'expected six import/scene origins')
stage_prefix='g02-layout-persistence-review/stage/counterexample-import-origin-01/'
require(all(stage_prefix in line.replace('\\','/') for line in origin_lines), 'origin outside review stage')

engine = manifest['engine']
findings=rec(REVIEW/'findings.md')
inspection=rec(MANIFEST)
tooling=rec(REVIEW/'evidence/reviewer-tooling-failures.md')
json_val=REVIEW/'evidence/json-validation-01'

review_assertions = {
    'toolbar_and_filedialog_source_path_present': {'status':'verified_static_and_headless_only','shell_lines':'224-235, 345-354, 517-520, 575-590, 611-674','native_ui':'not_run'},
    'strict_versioned_geometry_only_format':'verified_by_source_inspection_and_618_check_staged_suite',
    'finite_type_depth_size_unknown_field_limits':'verified_by_source_inspection_and_618_check_staged_suite',
    'transaction_undo_selection_history_seed_semantics':'verified_by_source_inspection_and_staged_suite',
    'whole_document_viewer_and_gate_updates':'verified_headless_only',
    'dialog_state_change_duplicate_and_cancel':'verified_by_11_check_independent_counterexample',
    'write_read_error_paths_and_sequential_target_preservation':'verified_by_staged_suite_and_source_inspection',
    'rename_destination_exists_behavior':'observed_OK_and_target_replaced_in_disposable_stage; documented concurrent no-overwrite limitation',
    'private_default_storage_geometry_only':'verified_source_representation_excludes_run_link_control_seed_truth_fields',
    'ai_os_confidentiality':'not_run',
    'run_link_authority_changed_by_review':'false',
    'production_run_gate':'unavailable_unchanged_not_enabled',
    'resourceloader_eval_or_dynamic_load_in_final_seam':'not_found_in_static_inspection',
}

out={
    'schema':1,
    'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'task_id':'DEEPEYE-IMPLEMENTATION-20261014',
    'task_version':1,
    'work_id':'A-G02-LAYOUT-PERSISTENCE-REVIEW-20261020-v1',
    'review_identity':{
        'review_child_job_id':'child-ffab680842604466bbb1ead6549b1c11',
        'instance_id':'deepseek-a-29',
        'responsible_main':'Desktop01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2',
        'route':'existing authenticated DeepSeek execution',
        'author_original_child_job_id':'child-9d0281a0ffd54a8c99db1ad653d1d39c',
        'author_terminal':audit.get('terminal'),
        'authority':'independent read-only review; main owns adoption and final acceptance',
    },
    'status':'bounded_headless_software_review_pass_awaiting_main_adoption',
    'verdict':{
        'bounded_headless_software_review':'PASS',
        'blocking_implementation_defect_found':False,
        'product_accepted':False,
        'g02_accepted':False,
        'formal29_accepted':False,
        'native_ui_accepted':False,
    },
    'immutable_contract':manifest['immutable_contract'],
    'product':manifest['product'],
    'candidate_sources':manifest['candidate_sources'],
    'dependencies':manifest['dependencies'],
    'author_inputs':{
        'metadata':manifest['author_metadata'],
        'evidence_count':manifest['author_evidence_count'],
        'evidence_failures':manifest['author_evidence_failures'],
        'evidence':manifest['author_evidence'],
        'prior_red':manifest['prior_red'],
        'handoff_audit':audit,
    },
    'pin_audit':manifest['pin_audit'],
    'engine':engine,
    'runs':runs,
    'independent_test_conclusion':{
        'persistence':{'checks':run_by_label['persistence-01']['checks'],'failures':run_by_label['persistence-01']['failures'],'exit_code':run_by_label['persistence-01']['exit_code']},
        'editor':{'checks':run_by_label['editor-01']['checks'],'failures':run_by_label['editor-01']['failures'],'exit_code':run_by_label['editor-01']['exit_code']},
        'scene_smoke':{'marker':'SCENE_SMOKE_PASS document=1 shell=1 file_dialog=1','exit_code':run_by_label['smoke-01']['exit_code']},
        'flow_counterexample':{'checks':run_by_label['flow-counterexample-01']['checks'],'failures':run_by_label['flow-counterexample-01']['failures'],'exit_code':run_by_label['flow-counterexample-01']['exit_code']},
        'author_reported_counts_used_as_evidence':False,
    },
    'import_origins':{'source_run':'runs/import-origin-01/stdout.log','lines':origin_lines,'all_inside_review_stage':True},
    'stage':{
        'identity':manifest['stage_ledger'],
        'source_and_import_check':manifest['stage_source_check'],
        'fresh_review_copies_only':True,
        'product_godot_cache_created':False,
    },
    'documentation_byte_handling':manifest['documentation_byte_identity'],
    'json_validation':manifest['json_validation'],
    'review_assertions':review_assertions,
    'findings':findings,
    'inspection_manifest':inspection,
    'tooling_failures':tooling,
    'preserved_failures':[
        {'path':'evidence/pins-before.failed.stdout.json','reason':'wrong manifest field assumption; preserved failed pin attempt'},
        {'path':'evidence/stage-source-check-v1.incorrect-path-scope.json','reason':'incorrect stage-relative path scope'},
        {'path':'evidence/stage-source-check-v2.docs-and-origin-count-mis-scoped.json','reason':'incorrect docs and origin-count expectations'},
        {'path':'evidence/test-summary-v1.incorrect-exit-readback.json','reason':'incorrect exit readback in summary'},
        {'path':'runs/engine-version-02/result.json','reason':'preserved null ExitCode from PowerShell runner'},
        {'path':'runs/engine-version-03/result.json','reason':'preserved null ExitCode from disposed Process'},
        {'path':'evidence/final-scope-audit-01/stdout.json','reason':'helper expected strict pin audit to pass despite deliberately preserved unrelated head drift; corrected in 02'},
    ],
    'review_evidence':manifest['review_evidence'],
    'review_run_files':manifest['review_run_files'],
    'remaining_not_run':{
        'all_29_taskbook_cards':'not_run',
        'formal29':'not_run',
        'h01_h15':'not_run',
        'g02':'not_run',
        'native_ui_mouse_keyboard_visual_scaling_accessibility':'not_run',
        'physical_collision':'not_run',
        'full_crossing_route_control':'not_run',
        'os_isolation':'not_run',
        'ai_access_or_confidentiality':'not_run',
        'board_run':'not_run',
        'services_drivers':'not_run',
        'dual_h12':'not_run',
        'concurrent_atomic_no_overwrite_proof':'not_run',
    },
    'actions_not_performed':[
        'source_edit','product_write','author_evidence_write','git_commit','git_push','new_thread','peer_or_group_message','board_operation','service_or_driver_change','dependency_install','native_ui_run','product_cache_write'
    ],
    'genuine_limits':[
        'Headless FileDialog behavior is source/script exercised, not native or visual UI acceptance.',
        'Windows rename replaces an existing file if the destination appears after the final target check; no concurrent no-overwrite/atomic primitive is proven.',
        'Private default storage does not establish AI whitelist, OS isolation or filesystem confidentiality.',
        'A concurrent external main commit advanced PRODUCT HEAD after independent runs; strict final pin reports only that exact-head mismatch, while all reviewed bytes and the other 73 checks remain valid.',
        'No product, board, native, formal29, G02, AI, physical-collision, OS-isolation or dual-H12 acceptance is claimed.',
    ],
    'main_decision_required':True,
}
OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding='utf-8')
print('WROTE='+OUT.as_posix())
print('PERSISTENCE='+json.dumps(out['independent_test_conclusion']['persistence'],sort_keys=True))
print('EDITOR='+json.dumps(out['independent_test_conclusion']['editor'],sort_keys=True))
print('SMOKE='+json.dumps(out['independent_test_conclusion']['scene_smoke'],sort_keys=True))
print('FLOW='+json.dumps(out['independent_test_conclusion']['flow_counterexample'],sort_keys=True))
print('IMPORTS='+str(len(origin_lines)))
print('INSPECTION_MANIFEST_SHA256='+inspection['sha256'])
print('FINDINGS_SHA256='+findings['sha256'])
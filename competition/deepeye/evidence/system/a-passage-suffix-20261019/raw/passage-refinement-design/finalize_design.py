import hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a'
def identity(path):
 data=path.read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=json.loads((O/'source_hashes.json').read_text(encoding='utf-8'))
for path,expected in before['files'].items():assert identity(P/path)==expected,path
motion=json.loads((O.parent/'trusted-motion-rereview/before.json').read_text(encoding='utf-8'))['files']
for path,expected in motion.items():
 observed=identity(P/path);assert observed=={'bytes':expected['size'],'sha256':expected['sha256']},path
save('after.json',{'inspected_files':before['files'],'unchanged_from_diagnostic':True,'reviewed_motion_input_closure':motion,'closure_files_unchanged':35,'scope':'planning-only numerical diagnosis; product read-only'})
command=json.loads((O/'command.json').read_text(encoding='utf-8'));assert command['exit_code']==0
observed=json.loads((O/'observations.json').read_text(encoding='utf-8'));assert len(observed['cases'])==6
save('execution-summary.json',{'python':sys.version,'outer_cwd':str(R),'outer_argv_prefix':[str(R/'.local/venv/Scripts/python.exe'),'-B','-X','utf8'],'outer_invocations':[{'script':'run_inspection.py','exit_code':0},{'script':'finalize_design.py','exit_code':0}],
 'diagnostic_cases':6,'scope':'observations on current original source, no new implementation or test acceptance','preview_SAFE':2,'preview_UNKNOWN':4,'motion_commits':0})
manifest={str(path.relative_to(O)).replace('\\','/'):identity(path) for path in sorted(O.rglob('*')) if path.is_file() and path.name not in ('evidence_manifest.json','receipt.json','completion-text.txt','native_complete.json')}
save('evidence_manifest.json',manifest)
save('receipt.json',{'task':'DEEPEYE-IMPLEMENTATION-20261014/v1','work_id':'A-passage-refinement-design-20261019-v1','job_id':'child-160b966d82644c4cac5643d237a2a07c','owner':'/root/pc_direct_review_20261018',
 'result':'design_delivered_pending_main_selection','recommendation':'whole-original-dt strict-red-outside terminal suffix using existing six-face certificates','alternatives':['bounded canonical event-window subinterval refinement','new robust full-body support monotonicity proof'],
 'observed_current_causes':['early ARRIVED reducer guard before checking suffix','distinct entry-role-to-exit margin failure'],
 'diagnostics':{'cases':6,'exit_code':0,'commits':0,'formal_test_acceptance':False},'owned_product_paths_proposed':[
 'competition/deepeye/simulation/authority/motion/passage_phase.py','competition/deepeye/tests/simulation/test_passage_phase.py','competition/deepeye/tests/simulation/test_motion_executor.py','competition/deepeye/docs/workspace_passage.md'],
 'design':identity(O/'design.md'),'source_hashes':identity(O/'source_hashes.json'),'evidence_manifest':identity(O/'evidence_manifest.json'),
 'contract':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':before['requirements_sha256'],'H01_H15':'unchanged','product_code_modified':False,'authority_freshness_or_margin_change':False,'full_control_topologies':'preserved','all_29_formal_cards':'not_run'})
text=('A-passage-refinement-design-20261019-v1 completed planning-only. Current repaired executor manifest1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533 and35-input closure unchanged. '
 '6 current-source numerical diagnostics/exit0/no commits identify early multi-slice ARRIVED guard and separate blue-entry role-switch margin UNKNOWN. '
 'Recommend minimal whole-dt strict-red-outside suffix validation with existing six-face certificates; keep APERTURE-only tails/entry margin gaps UNKNOWN; no safe prefix, tolerance relaxation, source authority or TTL change. '
 'Design compares3 alternatives, conservative proof obligations,4 proposed product paths and meaningful positive/negative tests. Pending main selection, no product implementation/OS/service/board/external send. H01-H15 and both live control topologies preserved, all29 formal cards not_run. '
 'Design .planning/deepeye-resume-20261018/passage-refinement-design/design.md SHA256 '+identity(O/'design.md')['sha256']+'; receipt SHA256 '+identity(O/'receipt.json')['sha256']+'.')
(O/'completion-text.txt').write_text(text,encoding='utf-8')
print(json.dumps({'result':'design_ready_for_main_selection','design':identity(O/'design.md'),'receipt':identity(O/'receipt.json'),'evidence_entries':len(manifest)}))

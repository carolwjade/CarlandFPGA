"""Write the new review's evidence manifest and receipt, excluding private lease."""
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
own=Path(__file__).resolve().parent
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def ident(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(name,value):
    p=own/name
    assert not p.exists(), 'refuse overwrite '+name
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=load(own/'reconciliation.json'); c=load(own/'cleanup-current.json'); v=load(own/'lease-validation.json')
assert r['status']=='evidence_reconciled' and c['cleanup_observed'] and v['execution_allowed']
assert load(own/'audit-attempt-02/command.json')['exit_code']==0
excluded=['lease.private.json','manifest.json','receipt.json','final-result.txt','native-complete.json','final-check.json']
files={p.relative_to(own).as_posix():ident(p) for p in sorted(own.rglob('*')) if p.is_file() and p.relative_to(own).as_posix() not in excluded}
write('manifest.json',{'schema':1,'kind':'new_review_evidence_manifest','work_id':v['work_id'],'job_id':v['job_id'],'files':files,'exclusions':excluded,'exclusion_reason':'Private lease never included; manifest, dependent receipt and terminal administration are outside this acyclic evidence index. Preserved originals are bound by preserved-input-index.json.'})
receipt={'schema':1,'status':'completed_evidence_reconciliation','at_utc':datetime.now(timezone.utc).isoformat(),'job_id':v['job_id'],'native_agent_id':v['native_agent_id'],'work_id':v['work_id'],'task_id':v['task_id'],'task_version':1,'tested_head':r['tested_head'],'source_commit':r['source_commit'],'operation_id':'B-DEEPEYE-PWM-ATOMIC-20261020-12','request_sha256':'9951beb894c52fa1e9ec6ae6f487856125a9a91e7e91b8aae75c297b04420e56','source_handoff_manifest_sha256':'6d6de98ec58741efdd20110dba91ea3cff644ae59901413910fc654376b7cd04','contract_id':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':r['requirements_sha256'],'original_job':r['original_job_terminal'],'evidence_reuse':True,'simulation_rerun':False,'samples':46190,'full_frame_intervals':2000000,'following_complete_period37_frames':2,'exact_dut_guards':4,'real_mutants':2,'author_entries_verified':40,'author_unavailable_work_entries':45,'source_and_original_review_unchanged':True,'cleanup_observed':True,'product_acceptance':'not_granted; quality main owns adoption','formal_cards':'all 29 not_run','other_not_run':r['not_run'],'findings':ident(own/'findings.md'),'reconciliation':ident(own/'reconciliation.json'),'manifest':ident(own/'manifest.json'),'new_audit_command':load(own/'audit-attempt-02/command.json')}
write('receipt.json',receipt)
print(json.dumps({name:ident(own/name) for name in ['findings.md','reconciliation.json','manifest.json','receipt.json']},indent=2))

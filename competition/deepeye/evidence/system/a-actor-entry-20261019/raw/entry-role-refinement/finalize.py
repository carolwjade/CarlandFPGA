from pathlib import Path
import hashlib,json,subprocess

O=Path(__file__).resolve().parent
ROOT=O.parents[2]
P=ROOT/'.local/deepeye-implementation-a'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args,input=None):
    r=subprocess.run(['git',*args],cwd=P,input=input,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8'))
    return r.stdout.decode('utf-8').strip()
baseline=json.loads((O/'before.json').read_text('utf-8'))
assert baseline==json.loads((O/'after.json').read_text('utf-8'))
assert git('rev-parse','HEAD')==baseline['head']
deps={}
for name in [*baseline['files'],'competition/deepeye/integration/motion.py']:
    raw=(P/name).read_bytes()
    if name in baseline['files']:assert sha(raw)==baseline['files'][name]['sha256'],name
    clean=git('hash-object','--path='+name,'--stdin',input=raw)
    pinned=git('rev-parse',baseline['head']+':'+name)
    assert clean==pinned,(name,clean,pinned)
    deps[name]={'raw_sha256':sha(raw),'bytes':len(raw),'git_clean_blob':clean,'pinned_blob':pinned}
(O/'dependencies-final.json').write_text(json.dumps({'head':baseline['head'],'files':deps},indent=2)+'\n',encoding='utf-8')
command=json.loads((O/'diagnostics-r3.command.json').read_text('utf-8'))
assert command['exit_code']==0
log=(O/'diagnostics-r3.stderr.log').read_text('utf-8')
assert 'Ran 4 tests' in log and log.rstrip().endswith('OK')
obs=json.loads((O/'observations.json').read_text('utf-8'))
assert len(obs)==10
assert [(r['name'],r['preview_status']) for r in obs[:2]]==[('14.481','SAFE'),('14.4815','UNKNOWN')]
inventory={f.name:{'sha256':sha(f.read_bytes()),'bytes':f.stat().st_size} for f in sorted(O.iterdir()) if f.is_file() and f.name not in ('receipt.json','native_complete.json','completion_payload.txt')}
receipt={'work_id':'A-G06-entry-role-refinement-design-20261019-v1','job_id':'child-cf373a04748847349b2b82930e4ebaa8',
 'owner':'/root/r03_review_20261018','kind':'design_and_read_only_numerical_diagnostics',
 'head':baseline['head'],'requirements_sha256':baseline['requirements_sha256'],'all_H01_H15_preserved':True,
 'product_writes':False,'design_implemented':False,'new_lemma_verified_in_product':False,
 'diagnostic_exit_code':0,'diagnostic_methods':4,'numerical_seed_cases':10,
 'exact_dependencies_stable_and_git_clean_equivalent':True,'dependency_count':len(deps),
 'recommended_next_dependency':'typed uniform-error inward-support non-exit lemma plus same-plan entry-handoff bridge; main decision and separate implementation/review required',
 'current_gap_remains':'14.4815 current source UNKNOWN; no accepted prefix or event history',
 'formal_cards':'all29 not_run; G06/G07 and both actual H12 chains not_run',
 'not_executed':['model','native OS probe','UI','service','board','1000-case campaign','network publish','product/index mutation'],
 'artifacts':inventory}
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'design_sha256':inventory['design.md']['sha256'],'receipt_sha256':sha((O/'receipt.json').read_bytes()),'dependencies':len(deps),'methods':4,'cases':10}))

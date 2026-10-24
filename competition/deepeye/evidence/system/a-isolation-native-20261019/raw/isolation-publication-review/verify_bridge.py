"""Read-only byte/AST/Git-clean bridge. No behavioral/native tests."""
from pathlib import Path
import ast,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a'
A=O.parent/'isolation-publication-bytes';V=O.parent/'isolation-final-review'
PIN='21c42710a33a2c1be2355129cfb113e5f23e261571dd8d8a35a2845f38fe7e63'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
raw_manifest=(A/'source-manifest.json').read_bytes();assert sha(raw_manifest)==PIN
manifest=json.loads(raw_manifest);previous=json.loads((V/'receipt.json').read_bytes())
assert len(manifest)==12
assert sha((V/'receipt.json').read_bytes())=='2c1d20a53f5b07ffef105c1e706e9e5a3bceefcd9bb96968ebce9e3a249cc59c'
assert sha((V/'findings.md').read_bytes())=='45530fd227ad583a5b7b926b0afc90d81d345eca49cf4bb1187acfedfe73a58b'
prototype='competition/deepeye/simulation/isolation/prototype.py'
old=(A/'prototype.before.py').read_bytes();new=(P/prototype).read_bytes()
assert sha(old)=='af54c6a5240be4e585f1c621034f5b687f79199595b82d54b2278253ceb4e452'
assert old==(V/'frozen'/prototype).read_bytes()
assert old.count(b'\r\n')==307 and old.replace(b'\r\n',b'\n')==new
assert len(old)-len(new)==307 and b'\r' not in new
assert ast.dump(ast.parse(old),include_attributes=False)==ast.dump(ast.parse(new),include_attributes=False)
commands=[];sources={};env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(args,data):
    command=['git','-C',str(P),*args]
    run=subprocess.run(command,input=data,capture_output=True,env=env)
    commands.append({'command':command,'exit_code':run.returncode,'stdout':run.stdout.decode().strip(),'stderr':run.stderr.decode('utf8','replace')})
    assert run.returncode==0
    return run.stdout.decode().strip()
changed=[]
for name,want in manifest.items():
    data=(P/name).read_bytes();assert {'size':len(data),'sha256':sha(data)}==want
    assert data==(A/'frozen'/name).read_bytes()
    same_before=want==previous['source_files'][name]
    if not same_before:changed.append(name)
    raw_blob=git(['hash-object','--stdin'],data)
    clean_blob=git(['hash-object','--path='+name,'--stdin'],data)
    assert raw_blob==clean_blob,name
    sources[name]={**want,'unchanged_from_final_review':same_before,'raw_git_blob':raw_blob,'clean_git_blob':clean_blob,'raw_equals_clean':True}
assert changed==[prototype]
harness=O.parent/'isolation-launcher-native/run_native.py'
assert sha(harness.read_bytes())=='2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613'
assert not (harness.parent/'native-execution-gate.json').exists()
req=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())['requirements']
reqhash=sha(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
assert reqhash=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
evidence=json.loads((V/'final-evidence-manifest.json').read_bytes())
for name,want in evidence.items():
    data=(V/name).read_bytes();assert {'size':len(data),'sha256':sha(data)}==want,name
completion_outer=json.loads((V/'native_complete.json').read_bytes())
completion=json.loads(next(c['text'] for c in completion_outer['content'] if c['type']=='text'))
assert completion['status']=='completed' and completion['terminal'] is True and completion['duplicate'] is False
save('git-commands.json',commands)
save('verified-source-manifest.json',sources)
save('receipt.json',{
    'work_id':'A-isolation-publication-review-20261019-v1','job_id':'child-4debee817c124124b4a7f5438cbbbc76',
    'reviewer':'/root/r03_review_20261018','result':'byte bridge verified',
    'publication_manifest_sha256':PIN,'files_verified':12,'other_files_unchanged':11,
    'prototype_old_sha256':sha(old),'prototype_new_sha256':sha(new),'crlf_replacements':307,
    'exact_old_replace_crlf_lf':True,'ast_equal':True,'all_raw_equal_git_clean':True,
    'harness_sha256':sha(harness.read_bytes()),'prior_evidence_files_verified':len(evidence),
    'prior_findings_sha256':sha((V/'findings.md').read_bytes()),'prior_receipt_sha256':sha((V/'receipt.json').read_bytes()),
    'prior_completion_file_sha256':sha((V/'native_complete.json').read_bytes()),'prior_job_terminal':True,
    'requirements_sha256':reqhash,'suites_rerun':False,'native_executed':False,'gate_created':False,'formal_acceptance':'not_run',
    'command':[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve())],
    'source_write':False,'git_mutation':False,
})
print(json.dumps({'result':'PASS','files':12,'other_unchanged':11,'exact_replacements':307,'AST_equal':True,
    'prior_evidence_files':len(evidence),'receipt_sha256':sha((O/'receipt.json').read_bytes())},indent=2))

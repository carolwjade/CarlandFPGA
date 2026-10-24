import datetime,hashlib,json,pathlib,subprocess
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[2];S=D/'snapshot';R=S/'repo';R.mkdir(exist_ok=True);G=pathlib.Path('C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe');H='f7736ac737d1c7b256974beb1574b94096819270';m=json.loads((S/'manifest.json').read_bytes());receipts=[]
def check(c,s):
 if not c:raise AssertionError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
request_sha=sha(json.dumps(m['request'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode());check(request_sha==m['request_hash']=='427a2e0ab4117bbafac87ea7156175e9df8714801ed9d2249ecd636bf5950d8d','canonical request hash')
check(len(m['artifacts'])==len(set(m['artifacts']))==len(m['files'])==211 and set(m['artifacts'])==set(m['files']),'211 unique mapped paths');check(sum(v['size'] for v in m['files'].values())<=134217728 and max(v['size'] for v in m['files'].values())<=16777216,'bounded extraction')
paths=list(m['artifacts'])
testpath=json.loads((D/'initial-provenance.json').read_bytes())['test_repo_path'];runnerpath='competition/deepeye/tools/control3d/run_pwm_applied_capture.py'
for p in [runnerpath,testpath]:
 if p not in paths:paths.append(p)
for path in paths:
 rel=pathlib.PurePosixPath(path);check(not rel.is_absolute() and '..' not in rel.parts and '\\' not in path,'safe repository-relative artifact');cmd=[str(G),'-C',str(ROOT),'cat-file','blob',H+':'+path];start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(cmd,capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);check(p.returncode==0,'local artifact blob '+path);check(len(p.stdout)<=16777216,'blob limit');digest=sha(p.stdout)
 if path in m['files']:check(len(p.stdout)==m['files'][path]['size'] and digest==m['files'][path]['sha256'],'artifact exact bytes '+path)
 dest=R/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.stdout);receipts.append({'path':path,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':cmd,'exit':p.returncode,'bytes':len(p.stdout),'sha256':digest,'stderr':p.stderr.decode('utf-8')})
for dirname,source in [('tools/control3d/run_pwm_applied_capture.py',runnerpath),('tests/control/test_pwm_applied_capture_runner.py',testpath)]:
 dest=D/'minimal/competition/deepeye'/dirname;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((R/source).read_bytes())
rtl=[]
for file in ['deepeye_atomic_pwm.sv','deepeye_pwm_coherent_capture.sv','deepeye_pwm_applied_capture.sv']:
 path='competition/deepeye/fpga/control3d/'+file;values=[]
 for ref in ['df82af1bc91d01aeb9adee19f48c0890dfc1ac5b',H]:
  cmd=[str(G),'-C',str(ROOT),'cat-file','blob',ref+':'+path];p=subprocess.run(cmd,capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);check(p.returncode==0,'RTL blob');values.append({'ref':ref,'sha256':sha(p.stdout),'git_blob':hashlib.sha1(b'blob '+str(len(p.stdout)).encode()+b'\0'+p.stdout).hexdigest(),'bytes':len(p.stdout)})
 check(values[0]['sha256']==values[1]['sha256'] and values[0]['git_blob']==values[1]['git_blob'],'same prior-synthesized RTL');rtl.append({'path':path,'versions':values})
scopepath='docs/competition/deepeye-2026/immutable_scope.json';cmd=[str(G),'-C',str(ROOT),'cat-file','blob','f5989cd5defce561f9ba98e6b18fc2682945f0a2:'+scopepath];p=subprocess.run(cmd,capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);check(p.returncode==0,'contract pinned commit');scope=json.loads(p.stdout);check(sha(json.dumps(scope['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','H01-H15 canonical pin');check([r['id'] for r in scope['requirements']]==[f'H{i:02}' for i in range(1,16)],'exact H01-H15 membership')
summary={'status':'211_artifacts_exact_and_scoped_sources_extracted','request_sha256':request_sha,'artifact_count':211,'declared_total_bytes':sum(v['size'] for v in m['files'].values()),'maximum_artifact_bytes':max(v['size'] for v in m['files'].values()),'git_blob_commands':receipts,'RTL_same_bytes_and_objects':rtl,'pinned_contract_verified':True,'test_repo_path':testpath};(D/'artifact-verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k not in ['git_blob_commands','RTL_same_bytes_and_objects']}))

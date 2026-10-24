import datetime,hashlib,json,pathlib,subprocess
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[2];G=pathlib.Path('C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe');HEAD='f7736ac737d1c7b256974beb1574b94096819270';BASE='df82af1bc91d01aeb9adee19f48c0890dfc1ac5b';PARENT='45fe6cd9c19d6056bf1867cc4255ac6a47ddddd5';manifestpath='handoffs/b/B-DEEPEYE-PWM-RUNNER-QUALIFICATION-20261020-16/manifest.json';snap=D/'snapshot';snap.mkdir();receipts=[]
def check(c,s):
 if not c:raise AssertionError(s)
def digest(b):return hashlib.sha256(b).hexdigest()
def git(*args,cap=16777216):
 cmd=[str(G),'-C',str(ROOT),*args];start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(cmd,capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);check(p.returncode==0,'local Git '+repr(args));check(len(p.stdout)<=cap,'bounded local blob');receipts.append({'command':cmd,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':digest(p.stdout),'stderr':p.stderr.decode('utf-8')});return p.stdout
raw=git('cat-file','blob',HEAD+':'+manifestpath);check(len(raw)==88085 and digest(raw)=='990a3ca2ce4eda78d92be3ad483ca09871ef06626e4904c4e992c8ef2b196f6d','manifest identity');check(raw==(D.parent/'b-op16-review-main-20261020/original-manifest.json').read_bytes(),'Git/API raw manifest equality');m=json.loads(raw);(snap/'manifest.json').write_bytes(raw)
print('MANIFEST_KEYS',list(m));print('MANIFEST_METADATA',json.dumps({k:v for k,v in m.items() if k not in ['artifacts','files']},indent=2)[:18000]);print('FILES_SHAPE',repr(next(iter(m['files'].items()))));print('ARTIFACT_COUNT',len(m['artifacts']))
def tree(ref):
 result={}
 for record in git('ls-tree','-r','--full-tree','-z',ref).split(b'\0'):
  if not record:continue
  info,path=record.split(b'\t',1);mode,kind,oid=info.decode().split();result[path.decode()]={'mode':mode,'type':kind,'oid':oid}
 return result
old=tree(BASE);new=tree(HEAD);parent=tree(PARENT);modified=[p for p in old if p in new and old[p]!=new[p]];removed=[p for p in old if p not in new];added=[p for p in new if p not in old];check(not removed and modified==['competition/deepeye/tools/control3d/run_pwm_applied_capture.py'],'bounded modified scope');check(len(modified)+len(added)==213,'213 diff names')
commit=git('cat-file','-p',HEAD).decode();check(('parent '+PARENT+'\n') in commit,'exact candidate parent');ancestry=git('merge-base',BASE,HEAD).decode().strip();check(ancestry==BASE,'candidate ancestry')
runner='competition/deepeye/tools/control3d/run_pwm_applied_capture.py';tests=[p for p in added if '/tools/' in p and p.endswith('.py')];check(len(tests)==1,'one added runner test')
for name,path,ref in [('runner.py',runner,HEAD),('previous-runner.py',runner,BASE),('new_tests.py',tests[0],HEAD)]:
 b=git('cat-file','blob',ref+':'+path);(snap/name).write_bytes(b);print('SOURCE',name,path,len(b),digest(b))
(D/'initial-provenance.json').write_text(json.dumps({'head':HEAD,'base':BASE,'parent':PARENT,'manifest_repo_path':manifestpath,'manifest_sha256':digest(raw),'tree_counts':{'base':len(old),'parent':len(parent),'head':len(new)},'modified':modified,'removed':removed,'added':added,'test_repo_path':tests[0],'tracked_base_paths_preserved':len(old),'unchanged_base_bytes':sum(old[p]==new[p] for p in old),'git_receipts':receipts},indent=2),encoding='utf-8')

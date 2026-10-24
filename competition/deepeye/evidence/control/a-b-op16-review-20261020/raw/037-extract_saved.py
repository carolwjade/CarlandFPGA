import datetime,hashlib,json,pathlib,subprocess
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[2];R=D/'snapshot/repo';H='f7736ac737d1c7b256974beb1574b94096819270';G='C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe';E=R/'competition/deepeye/evidence/control3d/pwm-runner-qualification-20261020-16';receipts=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def get(ref,path):
 cmd=[G,'-C',str(ROOT),'cat-file','blob',ref+':'+path];start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);out,err=p.communicate(timeout=10);assert p.returncode==0,(path,err);assert len(out)<=16777216
 receipts.append(dict(argv=cmd,pid=p.pid,exit=p.returncode,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=len(out),sha256=sha(out),stderr=err.decode('utf-8')));return out
f=json.loads((E/'a-original/FETCHED.json').read_bytes());original=[]
for x in f['files']:
 b=get(f['commit'],f['prefix']+x['path']);a=(E/'a-original'/x['path']).read_bytes();assert b==a and len(b)==x['bytes'] and sha(b)==x['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['git_blob'];original.append(x)
old='competition/deepeye/evidence/control3d/pwm-applied-capture-20261020-15/author/run-main-repaired-20261020-15-a';s=get(H,old+'/RUN_SUMMARY.json');assert sha(s)=='1bc4a0db74686b8c6d5033052f4a626f9ba9d59cd5f954d43965a99754f4bf31';S=D/'snapshot/saved';S.mkdir(exist_ok=True);(S/'RUN_SUMMARY.json').write_bytes(s);summary=json.loads(s);assert len(summary['commands'])==47
for rec in summary['commands']:
 for stream in ('stdout','stderr'):
  name=pathlib.PureWindowsPath(rec[stream]).name;b=get(H,old+'/logs/'+name);assert sha(b)==rec[stream+'_sha256'];(S/name).write_bytes(b)
for path in ['competition/deepeye/tests/rtl/control3d/tb_pwm_applied_capture.sv']:
 b=get(H,path);p=D/'snapshot'/pathlib.PurePosixPath(path).name;p.write_bytes(b)
result={'original_A_archive_verified':len(original),'original_A_files':original,'saved_commands':47,'saved_streams':94,'git_receipts':receipts,'no_new_simulator_execution':True};(D/'saved-provenance.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['original_A_files','git_receipts']}))

from pathlib import Path
import sys,os,hashlib,json,subprocess,time,datetime
H=Path(__file__).resolve().parent;ROOT=H.parents[2];S=H/'stage'
P=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):return {q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and '.godot' not in q.parts and '__pycache__' not in q.parts and not q.name.endswith('_observations.json')}
label=sys.argv[1];out=H/'raw'/label;out.mkdir(parents=True,exist_ok=False)
if label=='grammar-red-corrected':S=H/'baseline-stage'
if label=='prepare' or label.startswith('analyze'):
 argv=[sys.executable,'-B','-X','utf8',str(H/('prepare.py' if label=='prepare' else 'analyze.py'))];cwd=H
else:argv=[str(ENGINE),'--headless','--path',str(S),'--script',sys.argv[2]];cwd=S
assert sha(ENGINE)=='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
env=os.environ.copy();overrides={'PYTHONDONTWRITEBYTECODE':'1'}
for key in ['APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']:
 d=H/'private-env'/label/key;d.mkdir(parents=True,exist_ok=True);overrides[key]=str(d)
env.update(overrides)
rec=dict(argv=argv,cwd=str(cwd),environment_overrides=overrides,executable_sha256=sha(Path(argv[0])),timeout_seconds=55,source_before=files(S) if S.exists() else {},product_before=files(P),harness_sha256=sha(Path(__file__)),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
def save():(out/'result.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
save();start=time.monotonic()
with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
 p=subprocess.Popen(argv,cwd=cwd,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);rec['pid']=p.pid;save()
 try:rec.update(exit_code=p.wait(timeout=55),timed_out=False)
 except subprocess.TimeoutExpired:p.kill();rec.update(exit_code=p.wait(timeout=5),timed_out=True)
rec.update(terminal=p.poll() is not None,elapsed_seconds=time.monotonic()-start,source_after=files(S) if S.exists() else {},product_after=files(P),stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'))
rec['changed_product_files']=[k for k in set(rec['product_before'])|set(rec['product_after']) if rec['product_before'].get(k)!=rec['product_after'].get(k)]
rec['source_unchanged']=rec['source_before']==rec['source_after']
output=(out/'stdout.txt').read_text(encoding='utf8',errors='replace');errors=(out/'stderr.txt').read_text(encoding='utf8',errors='replace')
rec['script_errors']=any(t in output+errors for t in ['SCRIPT ERROR','Parse Error','Compile Error']);save()
for name in ['grammar_observations.json','numeric_observations.json']:
 q=S/'tests'/name
 if q.exists() and ((label.startswith('grammar') and name.startswith('grammar')) or (label=='numeric-final' and name.startswith('numeric'))):(out/name).write_bytes(q.read_bytes())
print(json.dumps({k:rec[k] for k in ['pid','terminal','exit_code','timed_out','elapsed_seconds','source_unchanged','changed_product_files','script_errors']}));print(output[-2500:]);print(errors[-1200:])
assert rec['terminal'] and not rec['timed_out'] and not rec['script_errors']
assert not rec['changed_product_files']
sys.exit(rec['exit_code'])

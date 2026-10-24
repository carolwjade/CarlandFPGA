from pathlib import Path
import os,subprocess,sys,json,hashlib,time,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SIM=HERE/'stage/competition/deepeye/simulator';PROD=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sources(base):return {p.relative_to(base).as_posix():sha(p) for p in base.rglob('*') if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts and p.name not in ['numeric_observations.json','limb_observations.json']}
label=sys.argv[1];out=HERE/'raw'/label;out.mkdir(parents=True,exist_ok=False)
assert sha(ENGINE)=='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
argv=[str(ENGINE),'--headless','--path',str(SIM)]+sys.argv[2:]
env=os.environ.copy();overrides={'PYTHONDONTWRITEBYTECODE':'1'}
for k in ['APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']:
 d=HERE/'tmp'/label/k;d.mkdir(parents=True,exist_ok=True);overrides[k]=str(d)
env.update(overrides)
rec=dict(argv=argv,cwd=str(SIM),environment_overrides=overrides,executable_sha256=sha(ENGINE),source_before=sources(SIM),product_before=sources(PROD),timeout_seconds=55,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
dump(out/'command.json',rec);start=time.monotonic()
with (out/'stdout.bin').open('wb') as so,(out/'stderr.bin').open('wb') as se:
 p=subprocess.Popen(argv,cwd=SIM,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);rec['pid']=p.pid
 try:rec.update(exit_code=p.wait(timeout=55),timed_out=False)
 except subprocess.TimeoutExpired:p.kill();rec.update(exit_code=p.wait(timeout=5),timed_out=True)
rec.update(terminal=p.poll() is not None,elapsed_seconds=time.monotonic()-start,source_after=sources(SIM),product_after=sources(PROD),stdout_sha256=sha(out/'stdout.bin'),stderr_sha256=sha(out/'stderr.bin'))
rec['product_unchanged']=rec['product_before']==rec['product_after'];rec['source_unchanged']=rec['source_before']==rec['source_after'];dump(out/'result.json',rec)
ob=SIM/'tests/numeric_observations.json'
if ob.exists(): (out/'observations.json').write_bytes(ob.read_bytes())
so=(out/'stdout.bin').read_text(encoding='utf-8',errors='replace');se=(out/'stderr.bin').read_text(encoding='utf-8',errors='replace')
print(json.dumps({k:rec[k] for k in ['pid','exit_code','terminal','timed_out','elapsed_seconds','product_unchanged','source_unchanged']}));print(so[-3500:]);print(se[-3500:])
rec['changed_product_files']=[k for k in set(rec['product_before'])|set(rec['product_after']) if rec['product_before'].get(k)!=rec['product_after'].get(k)]
rec['script_errors']=any(x in so+'\n'+se for x in ['SCRIPT ERROR','Parse Error','Compile Error'])
dump(out/'result.json',rec)
assert rec['terminal'] and not rec['timed_out']
# Other owned viewers may change concurrently; bind inputs and require our two
# PRODUCT editor inputs remain untouched. Report full external deltas explicitly.
assert all(not p.startswith('editor/') for p in rec['changed_product_files'])
assert not rec['script_errors']
sys.exit(rec['exit_code'])

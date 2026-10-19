import ast,difflib,hashlib,json,os,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';A=O.parent/'trusted-motion-repair';OLD=O.parent/'trusted-motion-review'
def sha(data):return hashlib.sha256(data).hexdigest()
def identity(path):
 data=path.read_bytes();return {'size':len(data),'sha256':sha(data)}
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha((A/'source-manifest.json').read_bytes())=='1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533'
candidate=json.loads((A/'source-manifest.json').read_text(encoding='utf-8'))
previous=json.loads((OLD/'before.json').read_text(encoding='utf-8'))['files'];diff=[];changed=[]
for path,digest in previous.items():
 current=(P/path).read_bytes()
 if path in candidate:assert identity(P/path)==identity(A/'frozen'/path)==candidate[path]
 if sha(current)!=digest:
  changed.append(path)
  before=(A/'before'/path).read_bytes();assert sha(before)==digest
  diff.extend(difflib.unified_diff(before.decode('utf-8').splitlines(True),current.decode('utf-8').splitlines(True),fromfile='before/'+path,tofile='repaired/'+path))
 else:assert sha(current)==digest
 target=O/'frozen'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(current)
assert set(changed)==set(json.loads((A/'receipt.json').read_text(encoding='utf-8'))['changed_product_files'])
assert len(previous)==35 and len(changed)==3
for root in (R,P):
 root.joinpath('docs/competition/deepeye-2026/immutable_scope.md').read_text(encoding='utf-8')
 d=json.loads(root.joinpath('docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
 pin=sha(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
 assert pin=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 assert [x['id'] for x in d['requirements']]==['H%02d'%i for i in range(1,16)]
old=(OLD.parent/'trusted-motion-implementation/passage_phase.before.py').read_bytes()
new=(P/'competition/deepeye/simulation/authority/motion/passage_phase.py').read_bytes()
assert all(ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False) for x,y in zip(ast.parse(old).body,ast.parse(new).body))
(O/'repair.diff').write_text(''.join(diff),encoding='utf-8')
original=(OLD/'test_independent_motion.py').read_bytes();assert original==(A/'test_independent_motion.py').read_bytes()
(O/'original_independent_eight.py').write_bytes(original)
before={path:identity(P/path) for path in previous}
save('before.json',{'files':before,'changed_paths':changed,'unchanged_from_previous':32,'candidate':candidate,'requirements_sha256':pin,'original_independent_script_sha256':sha(original),'passage_prefix_ast_unchanged':True})
env=dict(os.environ);env['PYTHONPATH']=str(P)+os.pathsep+str(R/'.local/deepeye-host-deps');env['TEMP']=env['TMP']=str(O/'temp');env['PYTHONDONTWRITEBYTECODE']='1';Path(env['TEMP']).mkdir(exist_ok=True)
full=json.loads((A/'green-complete.command.json').read_text(encoding='utf-8'))['command'];full[0]=sys.executable
commands=[('full-137',full),('original-eight',[sys.executable,'-B','-X','utf8',str(O/'original_independent_eight.py')]),('safe-continuation',[sys.executable,'-B','-X','utf8',str(O/'test_safe_continuation.py')])]
rows=[]
for label,argv in commands:
 r=subprocess.run(argv,cwd=P,env=env,capture_output=True,timeout=60)
 (O/(label+'.stdout.log')).write_bytes(r.stdout);(O/(label+'.stderr.log')).write_bytes(r.stderr)
 rows.append({'label':label,'argv':argv,'cwd':str(P),'exit_code':r.returncode});print(label,r.returncode,flush=True)
 if r.returncode:print(r.stderr.decode('utf-8','replace'))
save('commands.json',{'runs':rows,'environment':{'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONDONTWRITEBYTECODE':'1'}})
after={path:identity(P/path) for path in previous};assert before==after
save('after.json',{'files':after,'candidate_and_inputs_unchanged':35})
sys.exit(0 if all(row['exit_code']==0 for row in rows) else 1)

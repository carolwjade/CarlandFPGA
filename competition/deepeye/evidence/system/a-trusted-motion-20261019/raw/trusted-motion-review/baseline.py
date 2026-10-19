import ast,hashlib,json,os,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';A=O.parent/'trusted-motion-implementation'
def sha(data):return hashlib.sha256(data).hexdigest()
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha((A/'report.md').read_bytes())=='a8e18ad0fb4c880b1c659c8731734378e1feb4c97965b367d9e0cab7b0e7b6db'
assert sha((A/'receipt.json').read_bytes())=='1deafc745e2041f811bb7c962395358e90b8972fb11d057ffb39407f4fc6a92b'
sources=json.loads((A/'source_final.json').read_text(encoding='utf-8'));receipt=json.loads((A/'receipt.json').read_text(encoding='utf-8'))
assert len(sources)==35
for relative,expected in sources.items():
 data=(P/relative).read_bytes();assert sha(data)==expected,relative
 target=O/'frozen'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
assert all(sources[name]==digest for name,digest in receipt['owned_files'].items())
old=(A/'passage_phase.before.py').read_bytes();assert sha(old)=='28c948f63ba9010bc48a89f5472faa70a18887733284b1f5b0fcb03c65bc07cc'
previous=ast.parse(old);current=ast.parse((P/'competition/deepeye/simulation/authority/motion/passage_phase.py').read_bytes())
assert len(current.body)>len(previous.body)
assert all(ast.dump(left,include_attributes=False)==ast.dump(right,include_attributes=False) for left,right in zip(previous.body,current.body))
for root in (R,P):
 root.joinpath('docs/competition/deepeye-2026/immutable_scope.md').read_text(encoding='utf-8')
 d=json.loads(root.joinpath('docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
 pin=sha(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
 assert pin=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 assert [q['id'] for q in d['requirements']]==['H%02d'%i for i in range(1,16)]
save('before.json',{'files':sources,'owned_files':receipt['owned_files'],'preexisting_passage_ast_unchanged':True,'requirements_sha256':pin,'python':sys.version})
env=dict(os.environ);env['PYTHONPATH']=str(P)+os.pathsep+str(R/'.local/deepeye-host-deps');env['TEMP']=env['TMP']=str(O/'temp');env['PYTHONDONTWRITEBYTECODE']='1';Path(env['TEMP']).mkdir(exist_ok=True)
cmd=json.loads((A/'final-suite-frozen.command.json').read_text(encoding='utf-8'))['command'];cmd[0]=sys.executable
run=subprocess.run(cmd,cwd=P,env=env,capture_output=True,timeout=60)
(O/'author-135.stdout.log').write_bytes(run.stdout);(O/'author-135.stderr.log').write_bytes(run.stderr)
save('author-command.json',{'argv':cmd,'cwd':str(P),'exit_code':run.returncode,'environment':{'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONDONTWRITEBYTECODE':'1'}})
print(json.dumps({'files_verified':35,'owned':4,'passage_ast_unchanged':True,'author_exit_code':run.returncode}));sys.exit(run.returncode)

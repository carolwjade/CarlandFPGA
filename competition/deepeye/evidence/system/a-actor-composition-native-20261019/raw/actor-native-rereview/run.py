from pathlib import Path
import hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'.local/deepeye-implementation-a'
def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot():
    source=O.parent/'actor-native-repair/source-manifest.json'
    assert sha(source.read_bytes())=='415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3'
    rows=json.loads(source.read_text('utf-8'))['files']
    actor=O.parent/'actor-binding-repair/source-manifest.json'
    assert sha(actor.read_bytes())=='98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670'
    accepted=json.loads(actor.read_text('utf-8'));rows+=accepted['files']
    expected={r['path']:r['sha256'] for r in rows};expected.update(accepted['unchanged_live_nonmoving_dependencies'])
    files={}
    for n,d in expected.items():
        raw=(P/n).read_bytes();assert sha(raw)==d,n
        files[n]={'sha256':sha(raw),'bytes':len(raw)}
    original=O.parent/'actor-native-review/review_cases.py'
    assert original.read_bytes()==(O/'review_cases.py').read_bytes()
    prior=json.loads((O.parent/'actor-native-review/receipt.json').read_text('utf-8'))
    for n,d in prior['artifacts'].items():assert sha((O.parent/'actor-native-review'/n).read_bytes())==d,n
    scope=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text('utf-8'))
    assert sha(json.dumps(scope['requirements'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    return {'files':files,'original9_sha256':sha(original.read_bytes()),'old_evidence_unchanged':True}
label=sys.argv[1];assert not (O/(label+'.command.json')).exists()
if label=='offline':cmd=[sys.executable,'-B','-X','utf8','-m','unittest','-v','competition.deepeye.tests.isolation.test_actor_windows_live']
elif label=='original9':cmd=[sys.executable,'-B','-X','utf8',str(O/'review_cases.py')]
else:cmd=[sys.executable,'-B','-X','utf8',str(O/'closure_cases.py')]
env=os.environ.copy();env['PYTHONPATH']=str(P)+';'+str(ROOT/'.local/deepeye-host-deps')
temp=O/'temporary';temp.mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(temp)
before=snapshot();r=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(O/(label+'.stdout.log')).write_bytes(r.stdout);(O/(label+'.stderr.log')).write_bytes(r.stderr)
(O/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'exit_code':r.returncode,'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'before':before,'after':snapshot()},indent=2)+'\n',encoding='utf-8')
print(r.stderr.decode('utf-8'));raise SystemExit(r.returncode)

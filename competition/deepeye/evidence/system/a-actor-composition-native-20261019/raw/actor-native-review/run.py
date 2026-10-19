from pathlib import Path
import hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'.local/deepeye-implementation-a'
SHA='6474920de9d6ddd99eab6a7aa9ff66010fbcf40ba05a3b29954c4ebe3afdf9fa'
def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot():
    manifest=O.parent/'actor-native-preparation/source-manifest.json';assert sha(manifest.read_bytes())==SHA
    source=json.loads(manifest.read_text('utf-8'));result={}
    for row in source['files']:
        n=row['path'];raw=(P/n).read_bytes();assert sha(raw)==row['sha256'],n
        frozen=O.parent/'actor-native-preparation/frozen'/n
        assert raw==frozen.read_bytes(),n
        result[n]={'sha256':sha(raw),'bytes':len(raw)}
    scope=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text('utf-8'))
    assert sha(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==source['requirements_sha256']
    return result
label=sys.argv[1];assert not (O/(label+'.command.json')).exists()
env=os.environ.copy();env['PYTHONPATH']=str(P)+';'+str(ROOT/'.local/deepeye-host-deps')
temp=O/'temporary';temp.mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(temp)
if label=='offline':cmd=[sys.executable,'-B','-X','utf8','-m','unittest','-v','competition.deepeye.tests.isolation.test_actor_windows_live']
else:cmd=[sys.executable,'-B','-X','utf8',str(O/'review_cases.py')]
before=snapshot();r=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(O/(label+'.stdout.log')).write_bytes(r.stdout);(O/(label+'.stderr.log')).write_bytes(r.stderr)
(O/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'exit_code':r.returncode,'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'before':before,'after':snapshot()},indent=2)+'\n',encoding='utf-8')
print(r.stderr.decode('utf-8'));raise SystemExit(r.returncode)

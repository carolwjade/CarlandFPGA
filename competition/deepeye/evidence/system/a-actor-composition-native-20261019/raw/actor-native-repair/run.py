import pathlib,hashlib,json,sys,subprocess,os,datetime
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a'
OWN=['competition/deepeye/tests/isolation/test_actor_windows_live.py','competition/deepeye/docs/actor_native_probe.md']
FIXTURE='competition/deepeye/simulation/isolation/actor_fixture.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 names=set(OWN+[FIXTURE]);actor=json.loads((H.parent/'actor-binding-repair/source-manifest.json').read_text());names.update(x['path'] for x in actor['files']);names.update(actor['unchanged_live_nonmoving_dependencies'])
 bridge=json.loads((H.parent/'entry-bridge-implementation/source-manifest.json').read_text());names.update(bridge['candidate']);names.update(bridge['unaffected']);return {n:sha(P/n) for n in sorted(names)}
label=sys.argv[1]
if label=='baseline':
 review=H.parent/'actor-native-review';assert sha(review/'findings.md')=='c623ffd38b9a8ec941c12110bc25852235ee007e8210b13edf3337529d6d068e'
 for rel in OWN+[FIXTURE]:
  target=H/'before-source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((P/rel).read_bytes())
 (H/'review_cases.py').write_bytes((review/'review_cases.py').read_bytes())
 lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text());req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert req=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 (H/'before.json').write_text(json.dumps({'files':snapshot(),'requirements_sha256':req,'review_source_sha256':sha(review/'review_cases.py'),'main_selection_sha256':sha(H.parent/'actor-bridge-main-selection.json')},indent=2),encoding='utf-8');print('before bytes and unchanged9 reviewer source retained');raise SystemExit()
assert not (H/(label+'.command.json')).exists()
env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(P),str(ROOT/'.local/deepeye-host-deps'),str(H)]);env['PYTHONDONTWRITEBYTECODE']='1';(H/'temporary').mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(H/'temporary')
if label.startswith('review'):cmd=[sys.executable,'-B','-X','utf8',str(H/'review_cases.py')]
elif label.startswith('offline'):cmd=[sys.executable,'-B','-X','utf8','-m','unittest','competition.deepeye.tests.isolation.test_actor_windows_live','-v']
else:cmd=[sys.executable,'-B','-X','utf8',str(H/'boundary_payload.py'),label]
before=snapshot();start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(H/(label+'.stdout.log')).write_bytes(r.stdout);(H/(label+'.stderr.log')).write_bytes(r.stderr)
(H/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'environment_overrides':{k:env[k] for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','TEMP','TMP']},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'before':before,'after':snapshot()},ensure_ascii=False,indent=2),encoding='utf-8');print(r.stderr.decode());raise SystemExit(r.returncode)

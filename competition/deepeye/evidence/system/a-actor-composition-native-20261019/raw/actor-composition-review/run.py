import pathlib,hashlib,json,sys,os,subprocess,datetime,shutil
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';B=P/'competition/deepeye';A=H.parent/'actor-composition-implementation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 source=json.loads((A/'baseline.json').read_text())['source_hashes'];r={('competition/deepeye/'+n):sha(B/n) for n in source}
 m=json.loads((A/'source-manifest.json').read_text());r.update({x['path']:sha(P/x['path']) for x in m['files']});return r
label=sys.argv[1]
if label=='baseline':
 assert sha(A/'source-manifest.json')=='11663f50a276bee91cb77e27693d33e101d72a47c64cba23e269d10589ea034e'
 assert sha(A/'report.md')=='e06103253055b644a511706d07419ff4c2e77f574852f7e58ec454d2d221dee1'
 assert sha(A/'receipt.json')=='f40a4e5ccdbffdbde0a023debe66ee91b2134e6eb62c34667c557fcec06f82d1'
 terminal=json.loads((A/'native_completion.json').read_text());assert terminal['status']=='completed' and terminal['terminal'] is True
 m=json.loads((A/'source-manifest.json').read_text());old=json.loads((A/'baseline.json').read_text());assert len(old['source_hashes'])==55
 for n,digest in old['source_hashes'].items():assert sha(B/n)==digest,n
 git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
 for entry in m['files']:
  rel=entry['path'];assert sha(P/rel)==sha(A/'candidate'/rel)==entry['sha256']
  for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
   r=subprocess.run([git,'hash-object',*args],cwd=P,input=(P/rel).read_bytes(),capture_output=True);assert r.returncode==0 and r.stdout.decode().strip()==entry[key]
  t=H/'frozen'/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes((P/rel).read_bytes())
 lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text());req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert req==m['requirements_sha256']
 (H/'before.json').write_text(json.dumps({'files':snapshot(),'requirements_sha256':req,'manifest_sha256':sha(A/'source-manifest.json'),'baseline_sha256':sha(A/'baseline.json'),'selection_sha256':sha(H.parent/'actor-bridge-main-selection.json')},indent=2),encoding='utf-8');print('3 candidate exact/frozen/raw-clean +55 dependencies matched');raise SystemExit()
assert not (H/(label+'.command.json')).exists()
modules=['competition.deepeye.tests.simulation.'+n for n in ['test_actor_composition','test_actor_owner','test_actor_lifetime','test_pc_direct_runtime','test_motion_executor']] if label=='regression172' else ['composition_counterexamples.CompositionCounterexamples.test_progress_loss_after_prepare_is_documented_remaining_fence_dependency'] if label=='progress-gap' else ['composition_counterexamples']
env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(P),str(ROOT/'.local/deepeye-host-deps'),str(H)]);env['PYTHONDONTWRITEBYTECODE']='1';(H/'temporary').mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(H/'temporary')
cmd=[sys.executable,'-B','-X','utf8',str(H/'payload.py'),label,*modules];before=snapshot();started=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(H/(label+'.stdout.log')).write_bytes(r.stdout);(H/(label+'.stderr.log')).write_bytes(r.stderr)
(H/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'environment_overrides':{k:env[k] for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','TEMP','TMP']},'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'before':before,'after':snapshot()},ensure_ascii=False,indent=2),encoding='utf-8');print(r.stderr.decode());raise SystemExit(r.returncode)

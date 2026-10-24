import pathlib,hashlib,json,sys,subprocess,os,datetime,shutil
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';A=H.parent/'actor-binding-repair'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files():
 m=json.loads((A/'source-manifest.json').read_text());r={x['path']:sha(P/x['path']) for x in m['files']}
 r.update({n:sha(P/n) for n in m['unchanged_live_nonmoving_dependencies']})
 g=json.loads((H.parent/'entry-bridge-implementation/source-manifest.json').read_text());r.update({n:sha(P/n) for n in list(g['candidate'])+list(g['unaffected'])});return r
label=sys.argv[1]
if label=='baseline':
 assert sha(A/'source-manifest.json')=='98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670'
 assert sha(A/'report.md')=='0f806762c803d963dd93b5ee367105eac1708836a7b9b265dd6ff28a11ba908f'
 assert sha(A/'receipt.json')=='d582340e7498d0830f0a3b327470e4143f8c66214eafae171ee2eb93af0e72a6'
 native=json.loads((A/'native_completion.json').read_text());assert native['status']=='completed' and native['terminal'] is True
 original=H.parent/'actor-owner-review/independent_actor_tests.py';assert sha(original)=='de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f'
 (H/'independent_actor_tests.py').write_bytes(original.read_bytes())
 m=json.loads((A/'source-manifest.json').read_text());git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
 for entry in m['files']:
  rel=entry['path'];assert sha(P/rel)==sha(A/'candidate'/rel)==entry['sha256']
  for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
   r=subprocess.run([git,'hash-object',*args],cwd=P,input=(P/rel).read_bytes(),capture_output=True);assert r.returncode==0 and r.stdout.decode().strip()==entry[key]
  t=H/'frozen'/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes((P/rel).read_bytes())
 for rel,digest in m['unchanged_live_nonmoving_dependencies'].items():assert sha(P/rel)==digest
 lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text());req=hashlib.sha256(json.dumps(lock['requirements'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert req==m['requirements_sha256']
 (H/'before.json').write_text(json.dumps({'files':files(),'requirements_sha256':req,'old_review_findings_sha256':sha(H.parent/'actor-owner-review/findings.md'),'actor_candidate_manifest':sha(A/'source-manifest.json'),'g06_candidate_manifest':sha(H.parent/'entry-bridge-implementation/source-manifest.json')},indent=2),encoding='utf-8');print('seven candidate live/frozen/raw-clean; stable dependencies; immutable verified');raise SystemExit()
if label=='original8':module='independent_actor_tests'
else:module='new_actor_boundaries'
assert not (H/(label+'.command.json')).exists()
env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(P),str(ROOT/'.local/deepeye-host-deps'),str(H)]);env['PYTHONDONTWRITEBYTECODE']='1';(H/'temporary').mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(H/'temporary')
cmd=[sys.executable,'-B','-X','utf8',str(H/'payload.py'),module,label];before=files();start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(H/(label+'.stdout.log')).write_bytes(r.stdout);(H/(label+'.stderr.log')).write_bytes(r.stderr)
(H/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'environment_overrides':{k:env[k] for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','TEMP','TMP']},'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'before':before,'after':files()},ensure_ascii=False,indent=2),encoding='utf-8');print(r.stderr.decode());raise SystemExit(r.returncode)

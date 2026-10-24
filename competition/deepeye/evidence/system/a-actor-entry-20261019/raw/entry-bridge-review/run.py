import hashlib,json,pathlib,os,subprocess,sys,datetime,shutil
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';A=H.parent/'entry-bridge-implementation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 m=json.loads((A/'source-manifest.json').read_text());return {r:sha(P/r) for r in list(m['candidate'])+list(m['unaffected'])}
label=sys.argv[1]
if label=='baseline':
 assert sha(A/'source-manifest.json')=='cb904c57a2f985ff02ddb67e5b426968ecf4a22a1b03ecca2d382f99901ece19'
 assert sha(A/'report.md')=='7a558d3ac673ed5d6e8d9af659c5157af9d675daa0dcdc177920ddf1e53840b3'
 native=json.loads((A/'native_complete.json').read_text());native=json.loads(native['content'][0]['text']);assert native['status']=='completed' and native['terminal'] is True
 m=json.loads((A/'source-manifest.json').read_text());git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe';files=snapshot()
 for rel,entry in (m['candidate']|m['unaffected']).items():assert files[rel]==entry['sha256']
 for rel,entry in m['candidate'].items():
  assert sha(A/'candidate'/rel)==sha(P/rel)
  for args,key in [(['--stdin'],'raw_git_blob'),(['--path='+rel,'--stdin'],'git_clean_blob')]:
   r=subprocess.run([git,'hash-object',*args],cwd=P,input=(P/rel).read_bytes(),capture_output=True);assert r.returncode==0 and r.stdout.decode().strip()==entry[key]
  target=H/'frozen'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((P/rel).read_bytes())
 lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
 req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert req==m['requirements_sha256']
 (H/'before.json').write_text(json.dumps({'files':files,'requirements_sha256':req,'candidate_files':5,'unaffected':18,'actor':'excluded concurrent owner','author_terminal':'completed/true'},indent=2),encoding='utf-8');print('5 exact candidate/raw/clean/frozen +18 dependency bytes verified');raise SystemExit()
assert not (H/(label+'.command.json')).exists()
if label=='regression265':modules=json.loads((A/'regression1.command.json').read_text())['argv'][9:]  # Original saved239 run retained; corrected coverage below.
elif label=='missing26':modules=['competition.deepeye.tests.simulation.test_passage_phase']
elif label=='zero_speed_fixed':modules=['independent_entry_tests.IndependentEntryTests.test_zero_speed_holds_and_full_step_speed_carry_is_not_reset']
else:modules=['independent_entry_tests']
env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(P),str(ROOT/'.local/deepeye-host-deps'),str(H)]);env['PYTHONDONTWRITEBYTECODE']='1';(H/'temporary').mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(H/'temporary')
cmd=[sys.executable,'-B','-X','utf8','-m','unittest','-v',*modules];before=snapshot();start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(H/(label+'.stdout.log')).write_bytes(r.stdout);(H/(label+'.stderr.log')).write_bytes(r.stderr)
(H/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'environment_overrides':{k:env[k] for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','TEMP','TMP']},'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'before':before,'after':snapshot()},ensure_ascii=False,indent=2),encoding='utf-8')
print(r.stderr.decode('utf-8'));raise SystemExit(r.returncode)

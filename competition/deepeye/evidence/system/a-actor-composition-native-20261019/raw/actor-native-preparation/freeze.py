import ast,hashlib,json,pathlib,shutil,subprocess,sys,datetime
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((H/'before.json').read_text(encoding='utf-8'))
after={p:sha(pathlib.Path(p)) for p in b['reference_hashes']}
assert after==b['reference_hashes'],'stable read-only reference changed'
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert req==b['requirements_sha256']
cards=json.loads((P/'docs/competition/deepeye-2026/execution_plan_final.json').read_text(encoding='utf-8-sig'))['tasks']
assert len(cards)==29 and all(v['status']=='not_run' for v in cards.values())
git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
files=[]
for rel in b['new_paths_absent']:
 p=P/rel;raw=p.read_bytes()
 if p.suffix=='.py':ast.parse(raw);compile(raw,str(p),'exec')
 entry={'path':rel,'bytes':len(raw),'sha256':sha(p)}
 for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
  r=subprocess.run([git,'hash-object',*args],cwd=P,input=raw,capture_output=True);assert r.returncode==0;entry[key]=r.stdout.decode().strip()
 assert entry['raw_git_object']==entry['clean_git_object']
 target=H/'frozen'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);files.append(entry)
test=(P/b['new_paths_absent'][1]).read_text(encoding='utf-8');tree=ast.parse(test)
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('WriteFile','TerminateProcess','OpenProcess') for f in tree.body if isinstance(f,ast.FunctionDef) and f.name in ('run_case','_fixture_reader') for n in ast.walk(f))
assert 'Ran 13 tests' in (H/'green-final.stderr.txt').read_text() and 'OK (skipped=3)' in (H/'green-final.stderr.txt').read_text()
assert json.loads((H/'green-final.json').read_text())['exit_code']==0
assert json.loads((H/'red-initial.json').read_text())['exit_code']==1
write('source-manifest.json',{'files':files,'requirements_sha256':req,'execution_candidate_dependencies':'not bound; concurrent actor repair must finish and be independently reviewed','native':'not_run'})
write('after.json',{'stable_reference_hashes':after,'unchanged':True,'formal_cards':{k:v['status'] for k,v in cards.items()},'scope':'only declared3 NEW product files plus actor-native-preparation evidence; concurrent repair/G06 not edited or asserted frozen','limitations':'reference hashes are not a global filesystem write audit'})
write('receipt.json',{'work_id':'A-actor-native-fixture-preparation-20261019-v1','job_id':'child-ccfb46268a8e450da682eac66cffe460','status':'ready-for-independent-review','report_sha256':sha(H/'report.md'),'source_manifest_sha256':sha(H/'source-manifest.json'),'requirements_sha256':req,'tests':{'discovered':13,'offline_passed':10,'native_skipped':3,'exit_code':0,'red_failed':6,'red_native_skipped':3},'native':'not_run','runtime_staging':'not_run','actual_exit_write':'not_run: synchronous write has no deadline contract','normal_alternative':'fixed natural exit, prepared only','expiry':'readiness=lifetime simultaneous unbound cap only','raw_wait_capture':'not_run; evidence explicitly source-derived','repaired_actor_manifest':'not bound by this preparation','final_allow_record':'not produced; main owns it','all29':'not_run','H12_AI_Run_board_geometry':'not_run','owned_product_files':3})
write('freeze.result.json',{'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(pathlib.Path.cwd()),'exit_code':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'syntax_files':2,'raw_clean_parity':3,'stable_reference_files':len(after)})
evidence=[{'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ('evidence-manifest.json','native_completion.json')]
write('evidence-manifest.json',{'files':evidence,'excluded':['evidence-manifest.json','native_completion.json'],'terminal_policy':'native_completion.json appended once after original native_complete, then stop writes'})
print(json.dumps({'source_manifest_sha256':sha(H/'source-manifest.json'),'report_sha256':sha(H/'report.md'),'receipt_sha256':sha(H/'receipt.json'),'evidence_manifest_sha256':sha(H/'evidence-manifest.json'),'status':'ready-for-independent-review/native not_run'},indent=2))

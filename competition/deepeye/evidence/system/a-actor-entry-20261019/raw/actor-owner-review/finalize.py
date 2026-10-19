"""Freeze read-only review evidence; no native imports or source mutations."""
import ast, datetime, hashlib, json, pathlib, shutil, subprocess, sys
H=pathlib.Path(__file__).resolve().parent
ROOT=H.parents[2]; P=ROOT/'.local/deepeye-implementation-a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(H/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=json.loads((H/'before.json').read_text(encoding='utf-8'))
after={p:sha(pathlib.Path(p)) for p in before['files']}
assert after==before['files'],'read-only source/dependency/rule bytes changed'
git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
r=subprocess.run([git,'rev-parse','HEAD'],cwd=P,capture_output=True)
assert r.returncode==0
head=r.stdout.decode().strip()
assert head==before['head']
for entry in before['candidate']:
    rel=entry['path'];p=P/rel
    assert sha(p)==sha(H/'frozen'/rel)==entry['sha256']
    for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
        obj=subprocess.run([git,'hash-object',*args],input=p.read_bytes(),cwd=P,capture_output=True)
        assert obj.returncode==0 and obj.stdout.decode().strip()==entry[key]
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert req==before['requirements_sha256']=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
cards=json.loads((P/'docs/competition/deepeye-2026/execution_plan_final.json').read_text(encoding='utf-8-sig'))['tasks']
assert len(cards)==29 and all(t['status']=='not_run' for t in cards.values())
tree=ast.parse((H/'independent_actor_tests.py').read_text(encoding='utf-8'))
methods=[n.name for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='OwnerIndependent' for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
assert len(methods)==8
author=json.loads((H/'author116.result.json').read_text())
independent=json.loads((H/'independent8_binding4.result.json').read_text())
assert author['exit_code']==0 and independent['exit_code']==1
assert 'Ran 116 tests' in (H/'author116.stderr.txt').read_text() and (H/'author116.stderr.txt').read_text().rstrip().endswith('OK')
assert 'Ran 8 tests' in (H/'independent8_binding4.stderr.txt').read_text() and 'FAILED (failures=6)' in (H/'independent8_binding4.stderr.txt').read_text()
for action in ('close','poll','ai_lease','malformed_ai_lease'):
    w=json.loads((H/('old_binding_'+action+'.witness.json')).read_text())
    assert w['new_executor_stopped'] and w['new_runtime_latched'] and not w['native_effects_replayed'] and w['generation']==2
assert json.loads((H/'boolean_wait_cleanup.witness.json').read_text())['fake_process_still_live']
write('after.json',{'head':head,'files':after,'all_before_bytes_unchanged':True,'candidate_live_frozen_raw_clean_parity':True,'requirements_sha256':req,'formal_cards':{k:v['status'] for k,v in cards.items()},'scope_verification':{'write_root':str(H),'product_and_previous_evidence':'read only throughout this review','native_execution':False,'services_board_external_sends':False,'hash_scope_files':len(after),'limitation':'Hashes cover the declared 34-file review boundary; not a global filesystem audit.'}})
write('receipt.json',{'schema':1,'work_id':'A-actor-owner-independent-review-20261019-v1','job_id':'child-ed80d3358dba43b4b83dafef40a52b9b','agent_id':'/root/pc_direct_review_20261018','result':'review_completed_with_findings','head':head,'requirements_sha256':req,'candidate_manifest_sha256':'2bace7921cd89ff2cf7e9d1dd8b87dbd1be6f4d34abd1ac3cc3d37026dc39630','findings_sha256':sha(H/'findings.md'),'after_sha256':sha(H/'after.json'),'author_tests':{'methods':116,'exit_code':0,'skipped':0},'independent_tests':{'methods':8,'passing_methods':5,'failing_methods':3,'failed_assertions_or_subtests':6,'exit_code':1,'source_sha256':sha(H/'independent_actor_tests.py'),'original_40_method_discovery_logs_retained':True,'original_exact8_version_preserved':'independent_actor_tests.initial8.py.txt'},'findings':[{'id':'AOR-R1','class':'reachable old-binding public API revocation of new activation','public_actions':['close','poll','ai_lease','malformed_ai_lease'],'priority_suggestion':'P2 availability'},{'id':'AOR-R2','class':'injected dependency shape boundary; no real Win32 malformed return observed'},{'id':'AOR-R3','class':'injected dependency shape boundary; no real Win32 malformed return observed'}],'known_provider_detached_witness':'documented trusted composition obligation, not safe-operation evidence','static_helper_call_signatures':20,'native_compatibility':'not_run','formal_cards':'29 not_run','actual_AI_full_H12_game_board_Run':'not_run','source_files_unchanged':len(after),'next_ownership_proposal':['competition/deepeye/simulation/isolation/actor_owner.py','competition/deepeye/tests/simulation/test_actor_lifetime.py','competition/deepeye/docs/actor_lifetime.md'],'next_step':'Main assigns a new exclusive repair job: fence revocation callbacks to their original binding across every public error/retirement entry; preserve primary exceptions, partial-activation revocation, one cleanup, and quarantine. Shared windows_cleanup changes require separate explicit ownership.','acceptance_owner':'sole generation2 director; review completion is not candidate acceptance'})
write('finalize.result.json',{'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(pathlib.Path.cwd()),'exit_code':0,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'static hashes and evidence consistency; no test rerun'})
files=[{'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ('manifest.json','native_complete.json')]
write('manifest.json',{'schema':1,'files':files,'excluded_terminal_append':'native_complete.json is written once after immutable completion; manifest excludes itself'})
print(json.dumps({'findings_sha256':sha(H/'findings.md'),'receipt_sha256':sha(H/'receipt.json'),'manifest_sha256':sha(H/'manifest.json'),'files_unchanged':len(after),'author_tests':116,'independent_methods':8,'independent_failed_assertions_or_subtests':6,'formal_cards_not_run':29},indent=2))

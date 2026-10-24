import ast,hashlib,json,pathlib,subprocess,shutil,sys,datetime
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';A=H.parent/'actor-binding-repair'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((H/'before.json').read_text());after={n:sha(P/n) for n in b['files']};assert after==b['files']
m=json.loads((A/'source-manifest.json').read_text());assert sha(A/'source-manifest.json')==b['actor_candidate_manifest']
assert sha(A/'report.md')=='0f806762c803d963dd93b5ee367105eac1708836a7b9b265dd6ff28a11ba908f'
assert sha(A/'receipt.json')=='d582340e7498d0830f0a3b327470e4143f8c66214eafae171ee2eb93af0e72a6'
assert sha(H.parent/'actor-owner-review/findings.md')==b['old_review_findings_sha256']=='85c01193a3878a41cbd69fd516e649efb67e7a82a1de45fac01534ab2a6bdeca'
assert sha(H/'independent_actor_tests.py')==sha(H.parent/'actor-owner-review/independent_actor_tests.py')==m['independent_source_sha256']
git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
for entry in m['files']:
 rel=entry['path'];assert sha(P/rel)==sha(H/'frozen'/rel)==sha(A/'candidate'/rel)==entry['sha256']
 for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
  r=subprocess.run([git,'hash-object',*args],cwd=P,input=(P/rel).read_bytes(),capture_output=True);assert r.returncode==0 and r.stdout.decode().strip()==entry[key]
def nodes(path):
 t=ast.parse(path.read_text(encoding='utf-8'));out={}
 for i,n in enumerate(t.body):
  if isinstance(n,ast.ClassDef):
   for j,part in enumerate(n.body):out[(n.name,getattr(part,'name',str(j)))]=ast.dump(part,include_attributes=False)
  else:out[('module',getattr(n,'name',str(i)))]=ast.dump(n,include_attributes=False)
 return out
preserved={}
for tail in ['tests/simulation/test_actor_owner.py','tests/simulation/test_actor_lifetime.py','tests/isolation/test_windows_cleanup.py']:
 rel='competition/deepeye/'+tail;old=A/'before-source'/rel;current=P/rel;old_nodes=nodes(old);new_nodes=nodes(current)
 differences=[k for k,v in old_nodes.items() if new_nodes.get(k)!=v]
 additive_import=False
 if differences:
  assert tail=='tests/isolation/test_windows_cleanup.py' and differences==[('module','6')]
  expected_old=ast.dump(ast.parse('from simulation.isolation.resource_cleanup import Outcome, Provenance').body[0],include_attributes=False)
  expected_new=ast.dump(ast.parse('from simulation.isolation.resource_cleanup import Outcome, Provenance, Resource').body[0],include_attributes=False)
  assert old_nodes[differences[0]]==expected_old and new_nodes[differences[0]]==expected_new
  additive_import=True
 if 'actor_' in tail:assert sha(old)==sha(H.parent/'actor-owner-implementation/candidate'/rel)
 else:assert sha(old)==json.loads((A/'baseline.json').read_text())['exported_git_blobs'][rel]['sha256']
 preserved[rel]={'all_original_helper_test_AST_identical':True,'original_module_AST_except_additive_Resource_import_identical':True,'additive_Resource_import':additive_import,'old_test_methods':sum(k[1].startswith('test_') for k in old_nodes),'current_test_methods':sum(k[1].startswith('test_') for k in new_nodes)}
origins={}
for label,count in [('original8',8),('additional4',4)]:
 cmd=json.loads((H/(label+'.command.json')).read_text());log=(H/(label+'.stderr.log')).read_text()
 assert cmd['exit_code']==0 and f'Ran {count} tests' in log and log.rstrip().endswith('OK') and '... skipped ' not in log
 assert cmd['before']==cmd['after']==b['files']
 imported=json.loads((H/(label+'.module-origins.json')).read_text());assert not any(n.endswith('.isolation.win32') for n in imported)
 for name,entry in imported.items():assert sha(pathlib.Path(entry['path']))==entry['sha256'];origins[name]=entry
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text());req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert req==b['requirements_sha256']
cards=json.loads((P/'docs/competition/deepeye-2026/execution_plan_final.json').read_text())['tasks'];assert len(cards)==29 and all(v['status']=='not_run' for v in cards.values())
write('after.json',{'files':after,'unchanged':True,'original_AST_verification':preserved,'imported_project_modules':origins,'requirements_sha256':req,'formal_cards':{k:v['status'] for k,v in cards.items()},'scope':'only actor-binding-review evidence written; product/old evidence read-only; hashes cover declared boundary, not global filesystem'})
write('receipt.json',{'work_id':'A-actor-binding-independent-review-20261019-v1','job_id':'child-f51ad639fe7a4aed9c4f5aff827ccea6','status':'review_completed_no_new_blocking_finding','findings_sha256':sha(H/'findings.md'),'after_sha256':sha(H/'after.json'),'candidate_manifest_sha256':sha(A/'source-manifest.json'),'current_G06_manifest_sha256':b['g06_candidate_manifest'],'requirements_sha256':req,'exact_original8':{'source_sha256':sha(H/'independent_actor_tests.py'),'pass':8,'skip':0,'exit_code':0},'different_boundaries':{'pass':4,'skip':0,'exit_code':0},'original_assertions_and_helpers_preserved':preserved,'software_findings':{'AOR-R1':'addressed per-target exact activation at callback dispatch','AOR-R2':'addressed exact int Wait at both phases; injected shape boundary only','AOR-R3':'addressed all4 exact int masks; injected shape boundary only'},'unwired_provider':'remaining deliberate integration gap; fake actor dead and numerical motion commits, not safety evidence','source_boundary_files_unchanged':len(after),'native':'not_run','main_current_G06_148_joint_regression':'separate main-owned evidence; not rerun/claimed here','historical_native':'predates repair; not transferred','formal29_AI_H12_Run_game_board':'not_run','acceptance_owner':'Desktop generation2 sole main'})
write('freeze.result.json',{'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(pathlib.Path.cwd()),'exit_code':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
files=[{'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ('manifest.json','native_complete.json')]
write('manifest.json',{'files':files,'excluded':['manifest.json','native_complete.json'],'terminal_policy':'native_complete appended once then stop writes'})
print(json.dumps({'findings_sha256':sha(H/'findings.md'),'receipt_sha256':sha(H/'receipt.json'),'manifest_sha256':sha(H/'manifest.json'),'before_after_files':len(after),'original8_pass':8,'additional_pass':4,'original_AST':preserved},indent=2))

import ast,hashlib,json,pathlib,subprocess,shutil,datetime,sys,re
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';A=H.parent/'entry-bridge-implementation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((H/'before.json').read_text());m=json.loads((A/'source-manifest.json').read_text())
after={r:sha(P/r) for r in b['files']};assert after==b['files']
assert sha(H.parent/'entry-role-refinement/design.md')=='ba78ae582dd693f837ce69abd1016582c00a35dd1bd27702c3a3ca253bf52096'
assert sha(H.parent/'bridge-and-actor-main-selection.json')==m['design_selection_sha256']
assert sha(A/'source-manifest.json')=='cb904c57a2f985ff02ddb67e5b426968ecf4a22a1b03ecca2d382f99901ece19'
assert sha(A/'report.md')=='7a558d3ac673ed5d6e8d9af659c5157af9d675daa0dcdc177920ddf1e53840b3'
git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
head=subprocess.run([git,'rev-parse','HEAD'],cwd=P,capture_output=True);assert head.returncode==0
for rel,entry in m['candidate'].items():
 assert sha(H/'frozen'/rel)==sha(A/'candidate'/rel)==after[rel]==entry['sha256']
 for args,key in [(['--stdin'],'raw_git_blob'),(['--path='+rel,'--stdin'],'git_clean_blob')]:
  r=subprocess.run([git,'hash-object',*args],cwd=P,input=(P/rel).read_bytes(),capture_output=True);assert r.returncode==0 and r.stdout.decode().strip()==entry[key]
labels={'regression265':(239,0),'missing26':(26,0),'independent1':(5,1),'zero_speed_fixed':(1,0)}
commands={}
for label,(count,code) in labels.items():
 command=json.loads((H/(label+'.command.json')).read_text());log=(H/(label+'.stderr.log')).read_text()
 assert command['exit_code']==code and f'Ran {count} test' in log and '... skipped ' not in log
 assert command['before']==command['after']==b['files'];commands[label]=command
 if code==0:assert log.rstrip().endswith('OK')
expected=json.loads((A/'regression1.command.json').read_text())['argv'][8:]
actual=commands['regression265']['argv'][7:]+commands['missing26']['argv'][7:]
assert len(actual)==len(set(actual)) and set(expected)==set(actual)
def methods(path):
 t=ast.parse(path.read_text());return {n.name:ast.dump(n,include_attributes=False) for c in t.body if isinstance(c,ast.ClassDef) and c.name=='IndependentEntryTests' for n in c.body if isinstance(n,ast.FunctionDef)}
original=methods(H/'independent_entry_tests.first.py.txt');final=methods(H/'independent_entry_tests.py')
changed=[k for k in final if original[k]!=final[k]];assert changed==['test_zero_speed_holds_and_full_step_speed_carry_is_not_reset']
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert req==b['requirements_sha256']
cards=json.loads((P/'docs/competition/deepeye-2026/execution_plan_final.json').read_text())['tasks'];assert len(cards)==29 and all(x['status']=='not_run' for x in cards.values())
write('after.json',{'files':after,'unchanged':True,'observed_head':head.stdout.decode().strip(),'candidate_raw_clean_frozen_parity':5,'unaffected_dependencies':18,'requirements_sha256':req,'formal_cards':{k:v['status'] for k,v in cards.items()},'scope':'only entry-bridge-review evidence written; no source/Git/native effects; concurrent actor excluded','limitation':'23-file pinned boundary verification, not a global filesystem audit'})
write('receipt.json',{'work_id':'A-entry-bridge-independent-review-20261019-v1','job_id':'child-f337f8c19052446ab2e5fbec9f7cd26b','status':'review_completed_no_new_blocking_finding','candidate_manifest_sha256':sha(A/'source-manifest.json'),'findings_sha256':sha(H/'findings.md'),'after_sha256':sha(H/'after.json'),'independent_source_sha256':sha(H/'independent_entry_tests.py'),'requirements_sha256':req,'regression':{'unique_methods':265,'runs':[{'label':'regression265','actual_methods':239,'exit_code':0},{'label':'missing26','actual_methods':26,'exit_code':0}],'skipped':0,'module_union_verified':True},'independent':{'unique_methods_with_success':5,'initial_methods':5,'initial_pass':4,'initial_error':1,'corrected_method_run':1,'corrected_exit_code':0,'unchanged_four_pass_methods_AST_verified':True,'error_cause':'reviewer requested zero-speed with invalid yaw7000; fixed review request to yaw0, no candidate change'},'numerical_witnesses':['six-normal-enclosures.json','uniform-error-negatives.json','late-real-face-failure.json','ramp-bounded-calls.json'],'scope_acceptance':'main decides exact numerical candidate only','source_files_unchanged':23,'product_native_AI_H12_Run_board_G06_G07_all29':'not_run'})
write('freeze.result.json',{'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(pathlib.Path.cwd()),'exit_code':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
files=[{'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ('manifest.json','native_complete.json')]
write('manifest.json',{'files':files,'excluded':['manifest.json','native_complete.json'],'terminal_policy':'append original native_complete.json once, then stop writes'})
print(json.dumps({'findings_sha256':sha(H/'findings.md'),'receipt_sha256':sha(H/'receipt.json'),'manifest_sha256':sha(H/'manifest.json'),'source_unchanged':23,'regression_pass':265,'independent_pass':5},indent=2))

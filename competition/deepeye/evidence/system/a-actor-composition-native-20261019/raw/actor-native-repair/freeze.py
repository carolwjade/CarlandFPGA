import ast,hashlib,json,pathlib,shutil,subprocess,datetime,sys
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a'
OWN=['competition/deepeye/tests/isolation/test_actor_windows_live.py','competition/deepeye/docs/actor_native_probe.md'];FIXTURE='competition/deepeye/simulation/isolation/actor_fixture.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((H/'before.json').read_text());after={r:sha(P/r) for r in b['files']}
changed=[r for r in after if after[r]!=b['files'][r]];assert set(changed)==set(OWN)
assert sha(H/'review_cases.py')==b['review_source_sha256']==sha(H.parent/'actor-native-review/review_cases.py')
assert sha(H.parent/'actor-bridge-main-selection.json')==b['main_selection_sha256']
for label,count,code,skips in [('review-red',9,1,0),('boundary-red',3,1,0),('review-final',9,0,0),('boundary-final',3,0,0),('offline-final',13,0,3)]:
 cmd=json.loads((H/(label+'.command.json')).read_text());log=(H/(label+'.stderr.log')).read_text();assert cmd['exit_code']==code and f'Ran {count} tests' in log
 assert cmd['before']==cmd['after']
 if code==0:assert log.rstrip().endswith('OK' if not skips else 'OK (skipped=3)');assert cmd['after']==after
 else:assert cmd['after']==b['files']
old=ast.parse((H/'before-source'/OWN[0]).read_text());new=ast.parse((P/OWN[0]).read_text())
def classes(tree):return {c.name:{n.name:ast.dump(n,include_attributes=False) for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))} for c in tree.body if isinstance(c,ast.ClassDef)}
o,n=classes(old),classes(new)
for name in ['OfflinePreparationTests','ActorWindowsLiveTests']:assert o[name]==n[name]
origins=json.loads((H/'boundary-final.module-origins.json').read_text());assert not any(x.endswith('.isolation.win32') or x.endswith('.isolation.prototype') for x in origins)
for name,entry in origins.items():assert sha(pathlib.Path(entry['path']))==entry['sha256']
expected_harness=str((P/OWN[0]).resolve());assert origins['competition.deepeye.tests.isolation.test_actor_windows_live']['path']==expected_harness
git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe';bundle=[]
for rel in OWN+[FIXTURE]:
 p=P/rel;raw=p.read_bytes();entry={'path':rel,'sha256':sha(p),'bytes':len(raw),'ownership':'modified' if rel in OWN else 'unchanged fixture'}
 if p.suffix=='.py':ast.parse(raw);compile(raw,str(p),'exec')
 for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
  r=subprocess.run([git,'hash-object',*args],cwd=P,input=raw,capture_output=True);assert r.returncode==0;entry[key]=r.stdout.decode().strip()
 assert entry['raw_git_object']==entry['clean_git_object'];bundle.append(entry)
 t=H/'frozen'/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(raw)
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text());req=hashlib.sha256(json.dumps(lock['requirements'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert req==b['requirements_sha256']
cards=json.loads((P/'docs/competition/deepeye-2026/execution_plan_final.json').read_text())['tasks'];assert len(cards)==29 and all(v['status']=='not_run' for v in cards.values())
write('source-manifest.json',{'work_id':'A-actor-native-classification-repair-20261019-v1','files':bundle,'requirements_sha256':req,'actor_bridge_dependencies':'unchanged from before; main software acceptance separate','native_stage':'not_run'})
write('after.json',{'files':after,'only_modified':changed,'unchanged_dependency_files':len(after)-2,'reviewer9_byte_identical':True,'original_offline_and_native_test_AST_identical':True,'actual_module_origins':origins,'requirements_sha256':req,'formal_cards':{k:v['status'] for k,v in cards.items()},'scope':'only two authorized product files plus actor-native-repair evidence; no global filesystem audit'})
write('receipt.json',{'work_id':'A-actor-native-classification-repair-20261019-v1','job_id':'child-bc0ea14b25eb4fbfbcbf1e2e3606266e','status':'frozen_for_independent_review','source_manifest_sha256':sha(H/'source-manifest.json'),'report_sha256':sha(H/'report.md'),'after_sha256':sha(H/'after.json'),'requirements_sha256':req,'reviewer9':{'unchanged_source_sha256':sha(H/'review_cases.py'),'red_failures':1,'green_pass':9,'skipped':0},'added_boundaries':{'methods':3,'matrix_entries':10,'red_failed_assertions_subtests':13,'green_pass':3},'existing_offline':{'discovered':13,'pass':10,'native_skipped':3,'exit_code':0},'original_tests_AST_unchanged':True,'modified_product_files':2,'unchanged_product_dependency_files':len(after)-2,'original_process_exit':'exact retained resource_id; strict builtin int0; backend.terminated is False; separate provenance','expected_negative_receipts':'fixture expectation may match, normal_exit_success/evidence_success remain False','actual_native_stage_registry_AI_H12_Run_board_all29':'not_run','acceptance_owner':'sole generation2 main after independent review'})
write('freeze.result.json',{'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(pathlib.Path.cwd()),'exit_code':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
files=[{'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ('manifest.json','native_complete.json')]
write('manifest.json',{'files':files,'excluded':['manifest.json','native_complete.json'],'terminal_policy':'append original native_complete.json once then stop writes'})
print(json.dumps({'source_manifest_sha256':sha(H/'source-manifest.json'),'report_sha256':sha(H/'report.md'),'receipt_sha256':sha(H/'receipt.json'),'manifest_sha256':sha(H/'manifest.json'),'unchanged_dependencies':len(after)-2},indent=2))

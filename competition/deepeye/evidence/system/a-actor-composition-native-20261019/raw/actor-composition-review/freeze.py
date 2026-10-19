import pathlib,hashlib,json,subprocess,shutil,sys,datetime,ast
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';A=H.parent/'actor-composition-implementation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((H/'before.json').read_text());after={r:sha(P/r) for r in b['files']};assert after==b['files'] and len(after)==58
m=json.loads((A/'source-manifest.json').read_text());assert sha(A/'source-manifest.json')==b['manifest_sha256']=='11663f50a276bee91cb77e27693d33e101d72a47c64cba23e269d10589ea034e'
assert sha(A/'baseline.json')==b['baseline_sha256']==m['dependency_baseline_sha256']
assert sha(A/'report.md')=='e06103253055b644a511706d07419ff4c2e77f574852f7e58ec454d2d221dee1'
assert sha(A/'receipt.json')=='f40a4e5ccdbffdbde0a023debe66ee91b2134e6eb62c34667c557fcec06f82d1'
assert sha(H.parent/'actor-composition-design/design.md')==m['selected_design_sha256']
assert sha(H.parent/'actor-bridge-main-selection.json')==b['selection_sha256']==m['selected_main_record_sha256']
git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
for row in m['files']:
 rel=row['path'];assert sha(P/rel)==sha(H/'frozen'/rel)==sha(A/'candidate'/rel)==row['sha256']
 for args,key in [(['--stdin'],'raw_git_object'),(['--path='+rel,'--stdin'],'clean_git_object')]:
  r=subprocess.run([git,'hash-object',*args],cwd=P,input=(P/rel).read_bytes(),capture_output=True);assert r.returncode==0 and r.stdout.decode().strip()==row[key]
origin_union={}
for label,count in [('regression172',172),('independent5',5),('progress-gap',1)]:
 cmd=json.loads((H/(label+'.command.json')).read_text());r=json.loads((H/(label+'.result.json')).read_text());log=(H/(label+'.stderr.log')).read_text()
 assert cmd['exit_code']==0 and r['tests']==count and r['failures']==r['errors']==r['skipped']==0 and r['successful'] and log.rstrip().endswith('OK')
 assert cmd['before']==cmd['after']==b['files']
 for name,entry in r['module_origins'].items():assert sha(pathlib.Path(entry['path']))==entry['sha256'];origin_union[name]=entry
 assert not any(x.endswith('.isolation.win32') or x.endswith('.isolation.prototype') or x.endswith('.test_actor_windows_live') for x in r['module_origins'])
gap=json.loads((H/'progress-final-fence-gap.json').read_text());assert gap['committed_after_synthetic_progress_loss'] and gap['actual_revision']==1
cas=json.loads((H/'commit-plus-quarantine.json').read_text());assert cas['reported_committed'] and cas['reported_revision']==cas['actual_revision']==1 and cas['state']=='QUARANTINED' and cas['unresolved']
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text());req=hashlib.sha256(json.dumps(lock['requirements'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert req==b['requirements_sha256']
cards=json.loads((P/'docs/competition/deepeye-2026/execution_plan_final.json').read_text())['tasks'];assert len(cards)==29 and all(v['status']=='not_run' for v in cards.values())
write('after.json',{'files':after,'all_58_unchanged':True,'candidate_raw_clean_frozen_parity':3,'unaffected_dependencies':55,'module_origins':origin_union,'requirements_sha256':req,'formal_cards':{k:v['status'] for k,v in cards.items()},'scope':'review directory only; main native process/stage/source/evidence untouched; declared hash boundary, not global filesystem audit','old_detached_provider_witness_sha256':sha(H.parent/'actor-owner-review/provider_detached_integration_gap.witness.json')})
write('receipt.json',{'work_id':'A-actor-composition-independent-review-20261019-v1','job_id':'child-f77104b71ea14097ba5a69ae79badaca','status':'review_completed_no_new_blocking_software_finding','candidate_manifest_sha256':sha(A/'source-manifest.json'),'findings_sha256':sha(H/'findings.md'),'after_sha256':sha(H/'after.json'),'requirements_sha256':req,'regression':{'tests':172,'pass':172,'skip':0,'exit_code':0,'split':'24new+21actor_owner+36actor_lifetime+64runtime+27executor; different from earlier main148'},'additional':{'protective_methods_pass':5,'documented_negative_integration_method_pass':1,'negative_method_fact':'progress lost after preparation can still commit revision1 before next poll','skip':0},'source_unchanged':58,'production_verifier':'unavailable before registry; no public fallback','final_progress_deadline_integration':'missing documented producer/fence dependency; cannot enable by accepting verifier alone','post_CAS_late_veto_cleanup':'commit1 fact preserved plus QUARANTINED strong unresolved context','native_harness_and_main_interpreter':'not imported/touched','real_AI_BOOT_H12_Run_game_board_formal29':'not_run','acceptance_owner':'sole generation2 main; bounded unavailable-production library only'})
write('freeze.result.json',{'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(pathlib.Path.cwd()),'exit_code':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
files=[{'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ('manifest.json','native_complete.json')]
write('manifest.json',{'files':files,'excluded':['manifest.json','native_complete.json'],'terminal_policy':'append original native_complete.json once then stop writes'})
print(json.dumps({'findings_sha256':sha(H/'findings.md'),'receipt_sha256':sha(H/'receipt.json'),'manifest_sha256':sha(H/'manifest.json'),'regression':172,'protective_counterexample_methods':5,'negative_integration_witness_methods':1,'source_unchanged':58},indent=2))

import hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads((D/p).read_bytes())
m=j('snapshot/manifest.json');verified=0
for p,x in m['files'].items():
 b=(D/'snapshot/repo'/p).read_bytes();assert len(b)==x['size'] and sha(b)==x['sha256'];verified+=1
assert verified==211
for label in ['unit-pid','portable-pid','classification2','preservation','saved-extract2']:
 r=j(label+'-execution.json');assert r['exit_code']==0 and r['inputs_unchanged'] and r['pid']>0 and r['elapsed_seconds']<50
 for stream in ['stdout','stderr']:assert sha((D/(label+'-'+stream+'.txt')).read_bytes())==r[stream+'_sha256']
for mode in ['unit','portable']:
 r=j(mode+'-result.json');assert r['tests']==23 and r['failures']==r['errors']==0 and r['prohibited_process_network_attempts']==[]
c=j('counterexamples.json');assert len(c['cases'])==5 and sum(not x['expectation_met'] for x in c['cases'])==3 and c['process_network_attempts']==[]
s=j('saved-reclassification.json');assert s['saved_commands']==47 and s['saved_stdout_stderr_verified']==94 and len(s['observations'])==33 and s['failed_count']==0 and s['positive_samples']==208667
status={'work_id':'A-B-OP16-INDEPENDENT-20261020-v1','job_id':'child-c91b70f500b84f5f8ab65b13dc5690c5','agent_id':'/root/r02_static_dependency_review_20261020','candidate':'f7736ac737d1c7b256974beb1574b94096819270','review_status':'evidence_reproduced_with_two_residual_P2_findings','final_acceptance_owner':'A quality main','artifact_count_verified':211,'old_tracked_unchanged':4732,'old_A_archive_files_verified':40,'prior_B_files_verified':102,'unit_tests_passed':23,'portable_tests_passed':23,'original_A_negative_rejections':2,'saved_commands':47,'saved_streams':94,'saved_scenarios':33,'saved_positive_samples':208667,'new_simulator_runs':0,'new_Vivado_runs':0,'board_runs':0,'independent_controls_passed':2,'independent_counterexamples_false_accepted':3,'findings':[{'id':'P2-01','topic':'invalid guard substring and unrelated fatal acceptance','preexisting':True},{'id':'P2-02','topic':'code7 observation accepted in ordinary group','preexisting':True}],'formal_gates':{k:'not_run' for k in ['all29','G05','B06','R03','board','system']},'H01_H15':'unchanged','requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','scope':'independent artifact/source verification, Python-only tests and saved-log classification; no product acceptance'}
(D/'review-status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
text='A-B-OP16-INDEPENDENT-20261020-v1 completed: candidate f7736ac737d1c7b256974beb1574b94096819270; all 211 artifacts, 4732 unchanged baseline files, 40 original A and 102 prior-B archive files verified. Original A negatives repaired; 23 unit + 23 portable tests pass. Saved 47 commands/94 streams reproduce 33 scenarios and 208667 reported positive samples, with zero new RTL/ModelSim/Vivado/board execution. Two preexisting residual P2 findings: guard substring/unrelated-fatal acceptance and ordinary-group code7 acceptance; three exact counterexamples retained. Scoped repair evidence and residual gaps are separate; final adoption belongs to A quality main. H01-H15 unchanged; all29/G05/B06/R03/board/system not_run. Public artifact credential scan clean. See findings.md, review-status.json, artifact-manifest.json.\n'
(D/'final-result.txt').write_text(text,encoding='utf-8')
token=j('lease.private.json')['lease_token'].encode();matches=[];files=[p for p in D.rglob('*') if p.is_file() and 'private' not in p.name]
for p in files:
 if token in p.read_bytes():matches.append(p.relative_to(D).as_posix())
assert not matches
(D/'credential-scan.json').write_text(json.dumps({'scanned_files':len(files),'matching_files':matches,'match_count':len(matches),'values_printed':False},indent=2)+'\n',encoding='utf-8')
inventory={p.relative_to(D).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file() and 'private' not in p.name and p.name not in ['artifact-manifest.json','native-complete-response.json']}
(D/'artifact-manifest.json').write_text(json.dumps({'files':inventory,'file_count':len(inventory),'excluded':['private lease','this inventory','future native completion closure receipt'],'closure_policy':'native-complete-response.json is separately persisted and exact-readback verified; no review writes after completion'},indent=2)+'\n',encoding='utf-8')
assert token not in (D/'artifact-manifest.json').read_bytes()
print(json.dumps({'public_manifest_files':len(inventory),'manifest_sha256':sha((D/'artifact-manifest.json').read_bytes()),'credential_matches':0,'all_211_reverified':True,'review_status':status['review_status']}))

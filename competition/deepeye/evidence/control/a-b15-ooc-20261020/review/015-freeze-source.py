import datetime,hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent;OUT=D.parent
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(c,s):
 if not c:raise AssertionError(s)
status=load(D/'review-status.json');check(status['job_id']==load(D/'native-validate-response.json')['job_id'],'original reviewer job')
for label,source in [('static','audit_static.py'),('after','audit_readback.py')]:
 r=load(D/(label+'-execution.json'));check(r['exit_code']==0 and sha(D/source)==r['source_sha256']==sha(D/(label+'-source.py')),'exact offline source/exit '+label);check(sha(D/(label+'-stdout.txt'))==r['stdout_sha256'] and sha(D/(label+'-stderr.txt'))==r['stderr_sha256'],'actual offline output '+label)
for base in ['static','native']:
 before=load(D/(base+'-inputs-before.json'));after=load(D/(base+'-inputs-after.json'));check(before==after,'unchanged '+base+' snapshots')
 for p,h in before.items():check(sha(pathlib.Path(p))==h,'still pinned '+p)
readback=load(D/'native-readback-result.json');audit=load(D/'readback-report-audit.json');check(readback['batch_exit_code']==1 and readback['status']=='failed' and not audit['native_end_to_end_harness_pass'] and audit['native_ports_all_match'] and audit['native_open_checkpoint_completed'],'raw failed harness and successful report layers')
for f in load(OUT/'background-synthesis-main-20261020/synthesis-public-inputs.json')['artifacts']:check(sha(OUT/f['path'])==f['sha256'],'47 frozen public inputs')
token=load(D/'lease.private.json')['lease_token'].encode();matches=[]
for p in D.rglob('*'):
 if p.is_file() and p.name!='lease.private.json' and token in p.read_bytes():matches.append(str(p.relative_to(D)))
(D/'credential-scan.json').write_text(json.dumps({'nonprivate_matching_file_count':len(matches),'matching_filenames':matches,'private_source_excluded':'lease.private.json','license_content_not_copied':True},indent=2),encoding='utf-8');check(not matches,'contaminated artifact filenames '+repr(matches))
(D/'closeout-verification.json').write_text(json.dumps({'status':'independent_audit_closeout_verified','public_inputs':47,'original_batch_exits':[1,1,0],'independent_native_batch_exit':1,'independent_checkpoint_open_and_reports_verified':True,'independent_end_to_end_native_harness_pass':False,'new_native_checkpoint_runs':1,'new_synthesis_runs':0,'token_nonprivate_matches':0,'all29':'not_run','main_acceptance':'not_granted_by_child'},indent=2),encoding='utf-8')
exclude={'lease.private.json','nonsecret-artifact-manifest.json','native-complete-response.json','freeze-started.json','freeze-stdout.txt','freeze-stderr.txt','freeze-execution.json'};excluded_dirs={'native-temp','.Xil'};items=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name not in exclude and not excluded_dirs.intersection(p.relative_to(D).parts):items.append({'path':str(p.relative_to(D)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)})
m={'schema':1,'work_id':status['work_id'],'job_id':status['job_id'],'agent':status['agent'],'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_count':len(items),'files':items,'excluded_files':sorted(exclude),'excluded_directories':sorted(excluded_dirs),'final_result_sha256':sha(D/'final-result.txt'),'all29':'not_run','main_acceptance':'not_granted_by_child'}
(D/'nonsecret-artifact-manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8');print(json.dumps({'status':'independent_audit_closeout_verified','artifacts':len(items),'manifest_sha256':sha(D/'nonsecret-artifact-manifest.json'),'final_result_sha256':sha(D/'final-result.txt'),'token_nonprivate_matches':0}))

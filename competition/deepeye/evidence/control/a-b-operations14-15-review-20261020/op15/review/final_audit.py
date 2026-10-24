import hashlib,json,re,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent
BASE=D.parent/'b-pr30-operations14-15-20261020/15';SRC=BASE/'source';B=SRC/'competition/deepeye';EV=B/'evidence/control3d/pwm-applied-capture-20261020-15'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
meta=load(BASE/'artifact-integrity.json');bad=[]
for name,r in meta['files'].items():
    data=(SRC/name).read_bytes();actual={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}
    if actual!=r:bad.append(name)
assert not bad
handoff=load(SRC/'handoffs/b/B-DEEPEYE-PWM-APPLIED-CAPTURE-20261020-15/manifest.json')
for name,r in handoff['files'].items():assert sha(SRC/name)==r['sha256']and(SRC/name).stat().st_size==r['size']
assert len(handoff['files'])==1773
request_hash=hashlib.sha256(json.dumps(handoff['request'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();assert request_hash==meta['request_hash']==handoff['request_hash']
repaired=EV/'author/run-main-repaired-20261020-15-a';s=load(repaired/'RUN_SUMMARY.json');log=repaired/'logs'
def local(p):return log/Path(p.replace('\\','/')).name
strict=[]
for e in s['positive']:
    tx=local(e['stdout']).read_text(encoding='utf8');err=local(e['stderr']).read_text(encoding='utf8')
    markers=re.findall(r'^# TB_PASS group=\d+ loopback=[01]\s*$',tx,re.M);stats=re.findall(r'^# TB_STATS [^\r\n]+$',tx,re.M)
    assert len(markers)==len(stats)==1 and e['exit']==0 and not re.search(r'\*\*\s+(?:Error|Fatal):',tx+err)and re.search(r'^# Errors: 0, Warnings: 0\s*$',tx,re.M)
    assert 'mismatches=0'in stats[0]and e['stats']['mismatches']==0
    strict.append({'id':e['id'],'pass_marker':markers[0].strip(),'stats':stats[0],'exit':e['exit']})
negative=[]
for mu in s['mutants']:
    assert mu['compile']['compiled']and mu['compile']['vlog_exit']==0
    for run in mu['runs']:
        tx=local(run['stdout']).read_text(encoding='utf8');diags=re.findall(r'\*\*\s+(?:Error|Fatal):[^\r\n]+',tx)
        assert run['exit']==0 and len(re.findall(r'^# TB_STATS [^\r\n]+$',tx,re.M))==1
        if run['expect']=='fail':
            assert run['stats']['mismatches']>0 and run['mismatch_labels']and'** Fatal: TB_FAIL public-port self-check'in tx and not re.search(r'^# TB_PASS\b',tx,re.M)
        else:assert run['expect']=='pass_code7'and run['stats']['mismatches']==0 and'CODE7_OBSERVED'in tx and re.search(r'^# TB_PASS group=30 loopback=0\s*$',tx,re.M)and not diags
        negative.append({'id':mu['id'],'group':run['group'],'expect':run['expect'],'exit':run['exit'],'mismatches':run['stats']['mismatches'],'mismatch_labels':run['mismatch_labels'],'diagnostics':diags})
for e in s['invalid_parameters']:
    tx=local(e['record']['stdout']).read_text(encoding='utf8')
    assert e['record']['exit']==0 and e['diagnostic']==e['expected']and'Time: 0 ps'in tx and '** Fatal: DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM unsupported widths'in tx and not re.search(r'\*\*\s+Error:',tx)
for cmd in s['commands']:
    for stream in ['stdout','stderr']:assert sha(local(cmd[stream]))==cmd[stream+'_sha256']
for key,item in s['source_snapshot']['files'].items():
    f=repaired/'source_snapshot'/item['snapshot_name'];assert sha(f)==item['sha256']
snap=s['source_snapshot']['runner'];assert sha(repaired/'source_snapshot'/snap['snapshot_name'])==snap['sha256']==sha(B/'tools/control3d/run_pwm_applied_capture.py')
main=EV/'main/run-01';ms=load(main/'result.json');commands=[]
for cmd in ms['commands']:
    for stream in ['stdout','stderr']:
        f=main/(cmd['name']+'.'+stream+'.txt');assert sha(f)==cmd[stream+'_sha256']
    commands.append({'name':cmd['name'],'exit_code':cmd['exit_code']})
runs=[]
for run in ms['runs']:
    name=f"c{run['count_w']}_w{run['witness_w']}_t{run['tag_w']}";f=main/(name+'.vectors.txt');lines=f.read_text(encoding='ascii').splitlines();edges=sum(int(line.split()[0],16)for line in lines[1:]);assert int(lines[0])==len(lines)-1==run['rle_rows']and edges==run['sampled_edges']
    tx=(main/(name+'.stdout.txt')).read_text(encoding='utf8');assert re.search(r'^# MAIN_APPLIED_CAPTURE_PASS edges='+str(edges)+r' rows='+str(run['rle_rows'])+r'\s*$',tx,re.M)and not re.search(r'\*\*\s+(?:Error|Fatal):',tx)
    runs.append({'config':[run['count_w'],run['witness_w'],run['tag_w']],'edges':edges,'rle_rows':run['rle_rows'],'vectors_sha256':sha(f)})
assert sum(x['edges']for x in runs)==492440 and sum(x['rle_rows']for x in runs)==83462
fresh=load(D/'attempt03/receipt.json');mutants=load(D/'mutant-runs/receipt.json')
assert all(r['error_count']==0 for r in fresh['runs'])and all(r['error_count']>0 and r['compiled']for r in mutants['mutants'])and all(g['exact_guard_diagnostic']for g in fresh['guards'])
assert fresh['mapping_removed']and mutants['mapping_removed']
all_cmd=[]
for root in [D,D/'attempt02',D/'attempt03',D/'mutant-runs',D/'same-tag-probe']:
    for f in (root/'commands').glob('*/record.json'):
        rec=load(f);assert rec['process_exited']and not rec['timeout']
        for stream in ['stdout','stderr']:assert sha(f.parent/(stream+'.txt'))==rec[stream+'_sha256']
        all_cmd.append({'path':str(f.relative_to(D)),'pid':rec['pid'],'exit':rec['exit']})
out={'selected_files':len(meta['files']),'handoff_entries':len(handoff['files']),'all_bytes_and_git_blobs_match':not bad,'request_hash':request_hash,'repaired_commands_verified':len(s['commands']),'repaired_positive_totals':s['positive_totals'],'strict_positive_markers_and_stats':strict,'mutants_actual_behaviors':negative,'guards_exact_own_diagnostic':len(s['invalid_parameters']),'main_preserved_log_reconciliation':{'result_sha256':sha(main/'result.json'),'commands':commands,'runs':runs,'claim_boundary':'raw record reconciliation only; no B oracle imported or broad simulation rerun'},'fresh_total_edges':sum(r['edges']for r in fresh['runs']),'fresh_total_handshakes':sum(r['handshakes']for r in fresh['runs']),'fresh_trace_valid_observations':sum(r['valid_observations']for r in fresh['runs']),'fresh_checker_errors':sum(r['error_count']for r in fresh['runs']),'fresh_guard_count':len(fresh['guards']),'fresh_mutant_errors':{r['name']:r['error_count']for r in mutants['mutants']},'own_command_records':len(all_cmd),'own_all_commands_exited_without_timeout':True,'own_commands':all_cmd,'source_unchanged_after_runs':True,'all29_formal':'not_run'}
same=load(D/'same-tag-probe/receipt.json');assert same['behaviorally_rejected']and same['compiled']and same['simulator_completed']and same['mapping_removed'];out['additional_same_tag_state_retention_probe']={'error_count':same['error_count'],'counterexample_old_handshake_edges':[e['edge']for e in same['errors']if e['label']=='preedge_control_suppresses_old_handshake']}
save(D/'final-audit.json',out)
print(json.dumps({k:v for k,v in out.items()if k not in ['strict_positive_markers_and_stats','mutants_actual_behaviors','main_preserved_log_reconciliation','own_commands']}))

"""Read-only post-run evidence audit; only audit-result.json is written."""
import hashlib,json,pathlib,re
H=pathlib.Path(__file__).absolute().parent
ROOT=H.parents[2];I=ROOT/'.planning/deepeye-resume-20261018/b-pr30-operations14-15-20261020/14';S=I/'source'
B=S/'competition/deepeye/evidence/control3d/pwm-coherent-capture-20261020-14/main'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
r=read(H/'receipt.json');assert r['status']=='bounded_independent_simulation_passed'
m=read(S/'handoffs/b/B-DEEPEYE-PWM-COHERENT-CAPTURE-20261020-14/manifest.json')
for rel,item in m['files'].items():
    p=S/rel;assert p.stat().st_size==item['size'] and sha(p)==item['sha256'],rel
assert len(m['files'])==293
before=read(H/'source-inventory-before.json');after=read(H/'source-inventory-after.json')
assert before==after and len(before)==309
for rel,item in after.items():assert sha(S/rel)==item['sha256']
assert sha(H/'review.py')==r['source_hashes']['own_oracle_runner']
assert read(H/'outer-launch.json')['actual_exit']==0
clean=read(H/'cleanup-current.json');assert not clean['matching_processes'] and not clean['q_exists'] and clean['all_recorded_direct_processes_exited']
assert all(x['exit_code']==0 and x['actual_process_exited'] and not x['timed_out'] for x in r['commands'])
for cmd in r['commands']:
    d=H/'commands'/cmd['label'];assert sha(d/'stdout.txt')==cmd['stdout_sha256'] and sha(d/'stderr.txt')==cmd['stderr_sha256']
assert sum(x['edges'] for x in r['cases'])==800870 and sum(x['rle_rows'] for x in r['cases'])==65156
assert all(x['simulation_passed'] and x['trace_equals_B'] for x in r['cases'])
assert len(r['guards'])==11 and len(r['mutants'])==2
bguards=[]
for p in sorted((B/'run-02').glob('invalid_*.stdout.txt')):
    raw=p.read_bytes();fatal=b'** Fatal: DEEPEYE_COHERENT_INVALID_PARAM unsupported widths'
    assert raw.count(fatal)==1 and b'Time: 0 ps' in raw and b'main_tb_pwm_coherent_capture.dut' in raw
    assert b'MAIN_COHERENT_CAPTURE_PASS' not in raw
    bguards.append({'log':p.name,'errors_warnings':re.search(rb'Errors:\s*\d+,\s*Warnings:\s*\d+',raw).group().decode(),
                    'width_warnings':len(re.findall(rb'\*\* Warning:.*Connection width',raw)),'sha256':sha(p)})
assert len(bguards)==11
failed=read(B/'run-01/result.json');assert failed['status']=='failed'
assert 'explicit DUT diagnostic' in failed['error']
contexts=[]
for mutant in r['mutants']:
    match=re.search(r'row=(\d+).*edge=(\d+) field=(\d+)',mutant['public_counterexample']);row=int(match[1]);edge=int(match[2]);field=int(match[3])
    lines=(H/'run/c3_w6_t64.vectors.txt').read_text().splitlines()[1:];rows=[[int(x,16) for x in l.split()] for l in lines]
    contexts.append({'mutant':mutant['label'],'row':row,'one_based_sample':edge,'field':field,'expected_port_value':rows[row][7+field],
                     'nearby_rows':[{'row':i,'repeat_rst_stop_rearm_levels_tag_ready':rows[i][:7],'expected_ports':rows[i][7:]} for i in range(max(0,row-4),row+1)]})
tree=read(I/'head-tree.raw.json');commit=read(I/'commit.raw.json')
# Fetch records are immutable evidence inputs; support the unwrapped GitHub form.
assert commit['sha']==r['authority']['tested_head']
assert not tree.get('truncated',False)
treefiles={x['path']:x for x in tree['tree'] if x['type']=='blob'}
for rel,item in after.items():assert treefiles[rel]['sha']==item['git_blob'] and treefiles[rel]['size']==item['bytes']
summary={'status':'audit_passed','manifest_entries_verified':293,'selected_files_verified_against_head_tree':309,
         'source_unchanged':True,'commands':len(r['commands']),'actual_exits_all_zero':True,'positive_runs':6,
         'sampled_edges':800870,'rle_rows':65156,'independent_triples_w2':len(r['cases'][0]['observed_triples']),
         'independent_triples_w3':len(r['cases'][1]['observed_triples']),'B_guard_diagnostics':bguards,
         'B_preserved_initial_failure':failed['error'],'mutant_counterexample_context':contexts,
         'cleanup_verified':True,'receipt_sha256':sha(H/'receipt.json'),'oracle_freeze_sha256':sha(H/'independent-oracle-before-simulation.json')}
(H/'audit-result.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['status','manifest_entries_verified','selected_files_verified_against_head_tree','commands','sampled_edges','rle_rows','cleanup_verified']}))

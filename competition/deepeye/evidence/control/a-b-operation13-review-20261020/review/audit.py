"""Read-only reconciliation of fresh op13 commands and source provenance."""
import hashlib, json, pathlib, re
P=pathlib.Path(__file__).absolute().parent
ROOT=P.parents[2]
B=ROOT/'.planning/deepeye-resume-20261018/b-pr30-operation13-20261020/source'
E=B/'competition/deepeye/evidence/control3d/pwm-edge-measure-20261020-13/main'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,d): (P/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=json.loads((P/'receipt.json').read_bytes())
assert r['status']=='bounded_independent_simulation_passed' and r['sampled_edges']==1253606 and r['rle_rows']==79247
assert r['source_unchanged'] and r['mapping_removed'] and len(r['commands'])==25
assert json.loads((P/'source-inventory-before.json').read_bytes())==json.loads((P/'source-inventory-after.json').read_bytes())
assert sha(P/'review.py')==r['source_hashes']['own_oracle_runner']
assert sha(P/'run/dut.sv')==r['source_hashes']['rtl'] and sha(P/'run/tb.sv')==r['source_hashes']['public_tb']
for c in r['commands']:
    d=P/'commands'/c['label']; assert sha(d/'stdout.txt')==c['stdout_sha256'] and sha(d/'stderr.txt')==c['stderr_sha256']
    assert json.loads((d/'command.json').read_bytes())=={k:v for k,v in c.items() if k!='label'}
    assert c['exit_code']==0 and c['actual_process_exited'] and not c['timed_out']
tool=pathlib.Path('C:/modeltech64_2020.4/win64')
assert all(sha(tool/(n+'.exe'))==h for n,h in r['tool_hashes'].items())
guard=[]
for g in r['guards']:
    label='guard_w%d_t%d'%(g['count_w'],g['tag_w']); o=(P/'commands'/label/'stdout.txt').read_text()
    pat=r'Time:\s*(0 ps)\s+Scope:\s*(main_tb_pwm_edge_measure\.dut\.g_param_guard)\s+File:\s*(dut\.sv)\s+Line:\s*(202)'
    m=re.search(pat,o); assert m and o.count('** Fatal:')==1
    assert g['exact_fatal'] in o and 'Errors: 1, Warnings: 0' in o
    guard.append({'count_w':g['count_w'],'tag_w':g['tag_w'],'time':m[1],'scope':m[2],'file':m[3],'line':int(m[4]),'outer_exit':g['actual_exit']})
for case in r['cases']:
    label='w%d_t%d'%(case['count_w'],case['tag_w'])
    assert case['simulation_passed']
    assert sha(P/'run'/(label+'.vectors.txt'))==sha(E/'frozen-harness-03'/(label+'.vectors.txt'))==case['vectors_sha256']
    assert sha(P/'run'/(label+'.ports.txt'))==sha(E/'run-02'/(label+'.ports.txt'))==case['ports_sha256']
mut=[]
for m in r['mutants']:
    assert sha(P/'run'/(m['label']+'.sv'))==m['rtl_sha256']
    o=(P/'commands'/m['label']/'stdout.txt').read_text()
    assert m['public_counterexample'] in o
    assert 'Errors: 1, Warnings: 0' in o and '** Fatal: PUBLIC_PORT_MISMATCH' in o
    exact=re.search(r'Time:\s*([^\r\n]+Scope:[^\r\n]+)',o)
    mut.append({'label':m['label'],'counterexample':m['public_counterexample'],'diagnostic_location':exact[1],'outer_exit':m['actual_exit']})
cleanup=json.loads((P/'cleanup-current.json').read_text(encoding='utf-8-sig'))
assert cleanup['matching_processes']==[] and cleanup['subst_output']==[] and not cleanup['q_drive_exists']
req=json.loads((B/'handoffs/b/B-DEEPEYE-PWM-EDGE-MEASURE-20261020-13/input.json').read_bytes())['request']
assert hashlib.sha256(json.dumps(req,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==r['authority']['request_hash']
# No private token may appear in authored artifacts. Never print its value.
secret=json.loads((P/'lease.private.json').read_bytes())['lease_token'].encode()
for f in P.rglob('*'):
    if f.is_file() and f.name!='lease.private.json': assert secret not in f.read_bytes(), f.name
result={'status':'reconciled','simulator_rerun':False,'commands_verified':len(r['commands']), 'tool_hashes_unchanged':True,
        'source_entries_verified':len(json.loads((P/'source-inventory-after.json').read_bytes())), 'exact_guards':guard,'mutant_diagnostics':mut,
        'five_frozen_vector_and_public_trace_hashes_equal_B':True,'private_token_absent_from_authored_artifacts':True,
        'process_cleanup_checked':True,'formal_cards':'29 not_run','acceptance':'main only'}
write('audit-result.json',result)
print(json.dumps(result,ensure_ascii=False))

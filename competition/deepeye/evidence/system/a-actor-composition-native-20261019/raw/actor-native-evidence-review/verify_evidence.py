"""Pure file reconciliation of already completed native cases. No imports
from product, process/registry/native calls, interpreter input or mutations.
"""
from pathlib import Path
import ast,hashlib,json,zipfile
O=Path(__file__).resolve().parent;BASE=O.parent;ROOT=BASE.parents[1];P=ROOT/'.local/deepeye-implementation-a';M=BASE/'actor-native-main'
CASE_IDS={'retained-natural-exit':'afabf8e730984984ad6e3e3e54cd62eb','fixed-unbound-expiry':'fe2055ceae4c4f9c808c645af05c8de5','persistence-after-acquisition':'9db110fa0af943e1ac31740bad9d3e6a'}
CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
DIRECTOR='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
FILES={};SUMMARY=[]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
    path=Path(path);raw=path.read_bytes();FILES[str(path.resolve())]={'sha256':sha(raw),'bytes':len(raw)};return raw
def load(path):return json.loads(read(path))
readback=load(M/'retained-main-readback.json')
observed_readback_sha256=sha(read(M/'retained-main-readback.json'))
correction=load(BASE/'actor-native-evidence-review-pin-correction.json')
assert len(correction['original_assignment_pin'])==65 and correction['native_repeated'] is False
assert observed_readback_sha256==correction['correct_sha256']=='a360b90f7a89f11da67e63b4050fef0cf10318a83a34af32d50546281816030d'
assert readback['interpreter_session_id']==48521 and readback['retained_contexts']==readback['retained_case_count']==3
assert {r['case'] for r in readback['cases']}==set(CASE_IDS)
scope=load(P/'docs/competition/deepeye-2026/immutable_scope.json')
assert sha(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==CONTRACT
read(P/'docs/competition/deepeye-2026/immutable_scope.md')
manifest=load(BASE/'actor-native-repair/source-manifest.json')
assert sha(read(BASE/'actor-native-repair/source-manifest.json'))=='415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3'
for row in manifest['files']:assert sha(read(P/row['path']))==row['sha256']
for path in ['actor-native-review/findings.md','actor-native-review/receipt.json','actor-native-rereview/findings.md','actor-native-rereview/receipt.json','actor-native-rereview/source-manifest.json','actor-native-rereview/native_complete.json']:
    read(BASE/path)
for path in ['actor-native-evidence-review-assignment.md','actor-bridge-main-selection.json']:
    read(BASE/path)
for path in ['.agents/skills/fpga-multi-node/SKILL.md','.agents/skills/fpga-multi-node/skill-role.json','.agents/skills/fpga-multi-node/references/protocol.md','.planning/deepeye-desktop-handoff-20261015/transfer.json']:
    read(ROOT/path)
assert sha(read(BASE/'actor-native-rereview/receipt.json'))=='4d8cde10a943948d82b70daf0a67b3f9eec793315e91f09b1163d182c7a8400d'
for n in ['actor_native_interactive.py','actor_native_retained_readback.py','prepare_actor_native_main.py','approve_actor_native_case.py','audit_actor_native_stage.py']:
    ast.parse(read(BASE/n).decode('utf-8'))
ast.parse(read(M/'audit-stage-before-crlf-fix.py').decode('utf-8'))
initial=load(M/'stage-audit-initial-failure.json');assert initial['exit_code']==1 and initial['native_execution'] is False and initial['stage_unchanged'] is True
assert initial['observed_pth_repr']=="b'python312.zip\\r\\nDLLs\\r\\n.\\r\\n'"
source_sets=[];zip_member_sets=[];previous_return=None
for ordinal,(case,uid) in enumerate(CASE_IDS.items(),1):
    d=M/uid;index=load(M/(case+'.stage.json'));proposal=load(d/'allow-proposal.json');allow=load(d/'allow.json')
    assert Path(index['attempt_directory'])==d and index['native_execution'] is False
    assert sha(read(d/'allow-proposal.json'))==index['proposal_sha256']
    assert proposal['native_execution'] is False and proposal['approved_by'] is None and proposal['case'] is None
    assert allow==dict(proposal,approved_by=DIRECTOR,native_execution=True,case=case)
    assert allow['requirements_sha256']==CONTRACT and Path(allow['attempt_directory'])==d
    approval=load(d/'main-approval.json');invocation=load(d/'main-invocation.json');claim=load(d/'execution-claimed.json')
    returned=load(d/'main-return.json');memory=load(d/'fixture-memory-result.json');audit=load(d/'stage-main-audit.json')
    assert approval['case']==invocation['case']==claim['case']==returned['case']==memory['case']==case
    assert approval['main']==DIRECTOR and approval['generation']==2 and approval['no_retry'] is True and approval['harness_independent_review_accepted'] is True
    assert approval['candidate_manifest_sha256']==index['candidate_manifest_sha256']=='415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3'
    assert approval['allow_sha256']==invocation['allow_sha256']==claim['allow_sha256']==sha(read(d/'allow.json'))
    assert approval['review_receipt_sha256']==sha(read(BASE/'actor-native-rereview/receipt.json'))
    assert approval['stage_audit_sha256']==sha(read(d/'stage-main-audit.json'))
    assert approval['approved_at_utc']<invocation['at_utc']<returned['at_utc']
    if previous_return:assert previous_return<approval['approved_at_utc']
    previous_return=returned['at_utc']
    assert invocation['interpreter_flags_interactive']==1 and invocation['python'].startswith('3.12.14')
    assert invocation['source_hashes']==returned['source_hashes_after']==allow['sources'] and returned['source_hashes_unchanged'] is True
    source_sets.append(allow['sources'])
    for name,digest in allow['sources'].items():assert sha(read(P/name))==digest,name
    assert audit['zip_crc']=='passed' and audit['native_execution'] is False and audit['enabled_allow_written'] is False
    assert audit['source_files_verified']==len(allow['sources'])==38
    stage=d/'source-stage';actual_names={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    assert actual_names==set(allow['staged_files']) and len(actual_names)==audit['final_stage_files_verified']==10
    for name,digest in allow['staged_files'].items():assert sha(read(stage/name))==digest
    origin=load(d/'origin-stage-manifest.json');assert 'superseded' in origin['meaning'];members={}
    for row in origin['entries']:
        if 'source' in row:
            raw=read(row['source']);assert sha(raw)==row['sha256'] and len(raw)==row['size']
            if 'zip_member' in row:members[row['zip_member']]={'sha256':row['sha256'],'bytes':row['size']}
            elif row['stage']!='fixture.py':assert read(stage/row['stage'])==raw
        elif row['stage'] in ('python312.zip','python312._pth'):
            raw=read(stage/row['stage']);assert sha(raw)==row['sha256'] and len(raw)==row['size']
    with zipfile.ZipFile(stage/'python312.zip') as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(members) and set(archive.namelist())==set(members)
        for name,row in members.items():
            raw=archive.read(name);assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
    zip_member_sets.append(members)
    assert len(members)==audit['zip_members_verified']
    assert read(stage/'python312._pth')==b'python312.zip\r\nDLLs\r\n.\r\n'
    assert sha(read(stage/'fixture.py'))==allow['sources']['competition/deepeye/simulation/isolation/actor_fixture.py']
    rb=next(r for r in readback['cases'] if r['case']==case);snapshot=memory['cleanup']
    assert snapshot==returned['cleanup']==rb['snapshot'] and rb['snapshot_unchanged'] is True
    for key in ('context_retained_by_attempts','registry_retains_exact_actor','profile_absence_observed_by_original_backend','original_profile_path_currently_absent','copied_runtime_equals_approved_stage','source_hashes_unchanged','original_primary_retained','resources_all_confirmed'):assert rb[key] is True,(case,key)
    assert rb['profile_delete_hresult']==0 and rb['registry_owner_count']==1 and rb['unresolved'] is False and rb['owner_errors']==[]
    runtime=Path(rb['copied_runtime_directory']);assert runtime.is_relative_to(d)
    runtime_names={p.relative_to(runtime).as_posix() for p in runtime.rglob('*') if p.is_file()}
    assert runtime_names==set(allow['staged_files'])
    for name,digest in allow['staged_files'].items():assert sha(read(runtime/name))==digest==rb['copied_runtime_hashes'][name]
    assert memory['passed'] is True and returned['passed_fixture_expectation'] is True and memory['unresolved'] is returned['unresolved'] is False
    assert returned['registry_retains_exact_actor'] is True and returned['retained_contexts']==ordinal
    assert returned['fixture_result_sha256']==sha(read(d/'fixture-memory-result.json'))
    assert snapshot['resources_complete'] is True and snapshot['terminal_confirmed'] is True and snapshot['profile_outcome']=='confirmed' and snapshot['unresolved_resources']==[]
    resources=snapshot['resources'];assert len(resources)==18 and len({r['resource_id'] for r in resources})==18
    assert all(r['attempted'] is True and r['outcome']=='confirmed' and r['ambiguous'] is False for r in resources)
    process=next(r for r in resources if r['label']=='process');exit_=snapshot['original_process_exit']
    assert process['terminal_confirmed'] is True and exit_['resource_id']==process['resource_id']=='process:15'
    assert exit_['identity_continuous'] is True and exit_['exit_code_recorded'] is True and exit_['exit_code_type']=='int' and exit_['owner_terminated_type']=='bool'
    raw=read(d/'fixture-stdout.bin');assert raw.hex()==returned['raw_stdout_hex']
    assert memory['runtime_ready_boot_ai_h12_formal']=='not_run'
    receipt_rows=memory['actor_receipt_snapshots'];assert len(receipt_rows)==1
    receipt_path=Path(receipt_rows[0]['path']);assert receipt_path.is_relative_to(d)
    receipt=load(receipt_path);assert sha(read(receipt_path))==receipt_rows[0]['sha256']
    assert 'snapshot' in receipt_rows[0]['meaning'] and receipt['instance_id']==snapshot['instance_id']
    assert receipt['requirements_sha256']==CONTRACT
    provenance=receipt['provenance'];assert provenance['task_id']=='DEEPEYE-IMPLEMENTATION-20261014/v1'
    assert provenance['owner_id']==provenance['work_id']==snapshot['instance_id']
    assert dict(provenance['source_hashes'])=={'requirements':CONTRACT,**{'stage:'+n:h for n,h in allow['staged_files'].items()}}
    if case=='retained-natural-exit':
        assert raw==b'DEEPEYE-ACTOR/1 READY\n' and snapshot['state']=='CLOSED' and exit_['exit_code']==0 and exit_['owner_terminated'] is False
        assert memory['normal_exit_success'] is True and memory['evidence_success'] is True and memory['result_semantics']=='normal_exit_fixture'
        assert returned['primary_error'] is memory['primary_error'] is None and snapshot['evidence_errors']==[]
    elif case=='fixed-unbound-expiry':
        assert raw==b'DEEPEYE-ACTOR/1 READY\n' and snapshot['state']=='CLOSED' and exit_['exit_code']==0xdead and exit_['owner_terminated'] is True
        assert memory['normal_exit_success'] is False and memory['evidence_success'] is False and memory['result_semantics']=='expected_negative_fixture'
        assert snapshot['primary_error']['message']=='fixed actor/readiness/sample deadline expired'
        assert returned['primary_error'] is memory['primary_error'] is None and snapshot['evidence_errors']==[]
    else:
        assert raw==b'' and snapshot['state']=='QUARANTINED' and exit_['exit_code']==0xdead and exit_['owner_terminated'] is True
        assert memory['normal_exit_success'] is False and memory['evidence_success'] is False and memory['result_semantics']=='expected_negative_fixture'
        assert returned['primary_error']==memory['primary_error']==snapshot['primary_error']==rb['original_primary']
        assert memory['primary_error']=={'type':'OSError','message':'intentional actor persistence failure after acquisition'}
        assert len(snapshot['evidence_errors'])==44 and all(e==memory['primary_error'] for e in snapshot['evidence_errors'])
        assert receipt['state']=='ALLOCATING' and receipt['cleanup'] is None and len(receipt['resources'])==3 and receipt['primary_error'] is None
        assert snapshot['evidence_complete'] is rb['evidence_complete'] is False
    if case!='persistence-after-acquisition':
        assert receipt['state']=='CLOSED' and receipt['resources']==resources and receipt['cleanup']['resources_complete'] is True and receipt['cleanup']['success'] is False
    events=memory['events'];assert all(a['elapsed_ns']<=b['elapsed_ns'] for a,b in zip(events,events[1:])) if events else True
    if events:
        assert events[-1]['operation']=='poll/read retired' and events[-1]['error']==snapshot['primary_error']['message']
        assert all(e['operation']=='public_poll' and 'implied' in e['wait_result_source'] for e in events[:-1])
    terminal_tool=load(M/({'retained-natural-exit':'natural','fixed-unbound-expiry':'expiry','persistence-after-acquisition':'persistence'}[case]+'-terminal-tool-result.json'))
    # Persistence terminal output includes cursor ANSI after >>>, not a plain
    # space. Preserve raw bytes; structured case evidence is reconciled above.
    assert terminal_tool['session_id']==48521 and '>>>' in terminal_tool['output'] and ('execute_case(\''+case+'\')') in terminal_tool['output']
    SUMMARY.append({'case':case,'attempt':uid,'state':snapshot['state'],'instance_id':snapshot['instance_id'],'original_process_resource_id':process['resource_id'],'original_process_native':process['native'],
      'exit_code':exit_['exit_code'],'owner_terminated':exit_['owner_terminated'],'resources_confirmed':len(resources),
      'passed_fixture_expectation':memory['passed'],'normal_exit_success':memory['normal_exit_success'],'evidence_success':memory['evidence_success'],
      'stdout_bytes':len(raw),'elapsed_ns':memory['elapsed_ns'],'event_count':len(events),'evidence_errors':len(snapshot['evidence_errors']),
      'owner_primary':snapshot['primary_error'],'context_primary':memory['primary_error'],'receipt_state':receipt['state'],'receipt_resource_count':len(receipt['resources']),
      'receipt_cleanup_success':receipt['cleanup']['success'] if receipt['cleanup'] else None,'profile_absence_source':'original backend plus retained-main filesystem readback, not a new reviewer OS probe',
      'stage_files':len(actual_names),'source_files':len(allow['sources']),'stdlib_members':len(members)})
assert all(s==source_sets[0] for s in source_sets)
assert all(s==zip_member_sets[0] for s in zip_member_sets)
for name,row in readback['imported_modules'].items():
    assert name.startswith('competition.deepeye.') and Path(row['path']).is_relative_to(P)
    assert sha(read(row['path']))==row['sha256']
assert not any('actor_composition' in name for name in readback['imported_modules'])
(O/'reconciliation.json').write_text(json.dumps({'cases':SUMMARY,'retained_readback_sha256':sha(read(M/'retained-main-readback.json')),'same38_source_pins':True,'same_stdlib_member_bytes':True,'native_rerun':False,'main_interpreter_contacted':False,'formal29':'not_run'},indent=2)+'\n',encoding='utf-8')
(O/'inspected-manifest.json').write_text(json.dumps({'files':FILES,'file_count':len(FILES),'source_stage_and_original_artifacts_read_only':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':SUMMARY,'inspected_files':len(FILES)},ensure_ascii=False,indent=2))

"""Read-only saved native-evidence audit. No Win32 imports, reruns or canary reads."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a'
N=O.parent/'isolation-launcher-native';A=N/'attempt-01'
PIN='21c42710a33a2c1be2355129cfb113e5f23e261571dd8d8a35a2845f38fe7e63'
H='2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613'
hashes={}
def sha(data):return hashlib.sha256(data).hexdigest()
def raw(path):
    path=Path(path)
    assert path.name!='truth.canary' and path.suffix.lower() not in ('.exe','.dll','.pyd','.zip')
    data=path.read_bytes();hashes[str(path)]={'size':len(data),'sha256':sha(data)};return data
def read(path):return json.loads(raw(path))
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
gate=read(N/'native-execution-gate.json');preflight=read(A/'preflight.json');campaign=read(A/'campaign-result.json')
assert preflight['gate']==gate
assert gate['main']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d' and gate['generation']==2
assert gate['main_accepted_independent_review'] is True
assert gate['source_manifest_sha256']==PIN and gate['harness_sha256']==H
assert sha(raw(N/'run_native.py'))==H
assert sha(raw(R/gate['source_manifest']))==PIN
manifest=json.loads((R/gate['source_manifest']).read_bytes());assert manifest==preflight['sources']
for name,want in manifest.items():
    data=raw(P/name);assert {'size':len(data),'sha256':sha(data)}==want,name
for name,key in (('isolation-final-review','source_review_sha256'),('isolation-publication-review','byte_bridge_review_sha256')):
    assert sha(raw(O.parent/name/'receipt.json'))==gate[key]
support=[]
for item in gate['runtime_and_supporting_sources_verified']:
    # Hash original runtime inputs without copying, parsing or executing binaries.
    path=Path(item['path']);data=path.read_bytes();assert sha(data)==item['sha256']
    support.append({'path':str(path),'size':len(data),'sha256':sha(data)})
req=read(P/'docs/competition/deepeye-2026/immutable_scope.json')['requirements']
reqhash=sha(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
assert reqhash==gate['requirements_sha256']=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
assert campaign['passed'] is True and campaign['formal_acceptance']=='not_run'
names=['test_real_boundary_and_profile_cleanup','test_timeout_is_failed_and_own_process_profile_are_cleaned',
       'test_persistence_failure_after_process_creation_still_cleans_owned_objects']
assert [c['test'] for c in campaign['cases']]==names
policy={'appcontainer':True,'capabilities':[],'win32k_disabled':True,'child_process_restricted':True,'suspended':True,
        'job_kill_on_close':True,'job_active_process_limit':1,'job_process_memory_limit':268435456,'job_ui_restrictions':255}
summary=[];run_ids=[];profiles=[]
for index,case in enumerate(campaign['cases']):
    folder=Path(case['run_directory']);assert folder.parent.resolve()==A.resolve()
    run_ids.append(folder.name)
    memory=read(folder/'main-returned-memory.json');observation=read(folder/'main-observation.json')
    stale=read(folder/'receipt.json');runtime=read(folder/'runtime_manifest.json')
    assert sha((folder/'main-returned-memory.json').read_bytes())==case['memory_sha256']
    assert sha((folder/'main-observation.json').read_bytes())==case['observation_sha256']
    assert sha((folder/'runtime_manifest.json').read_bytes())==memory['runtime_manifest_sha256']
    for record in runtime:
        source=record.get('source')
        if source and any(source==s['path'] for s in support):
            assert record['sha256']==next(s['sha256'] for s in support if s['path']==source)
    for name,digest in memory['launcher_source_hashes'].items():assert sha(raw(P/'competition/deepeye/simulation/isolation'/name))==digest
    assert case['test_passed'] is True and case['tests_run']==1 and case['skipped']==0
    assert memory['verdict']==case['case_verdict'] and memory['verdict']['G03_formal_acceptance']=='not_run'
    assert memory['requested_policy']==policy
    assert memory['environment_keys']==['LOCALAPPDATA','SystemRoot','TEMP','TMP','WINDIR']
    inheritance=memory['inheritance'];assert inheritance['verified'] is True
    assert inheritance['allowed_flags']==[1,1] and inheritance['parent_endpoint_flags']==[0,0]
    assert inheritance['excluded_canary_inheritable'] is True and len(inheritance['allowed'])==2
    assert all(v is True for v in memory['parent_controls'].values())
    cleanup=memory['cleanup'];life=memory['lifecycle'];events=observation['events']
    assert cleanup['resources_complete'] is True and not cleanup['unresolved'] and not observation['unresolved']
    assert not cleanup['cleanup_errors'] and not cleanup['owner_errors']
    assert all(r['outcome']=='confirmed' and r['attempted'] is True and r['ambiguous'] is False for r in cleanup['resources'])
    assert life['terminal'] is True and life['profile_deleted'] is True and life['profile_directory_absent'] is True
    assert life['profile_delete_hresult']==0 and observation['profile_absence_after_return'] is True
    created=[(i,e) for i,e in enumerate(events) if e['action']=='actual_create_suspended_return'];assert len(created)==1
    created_index,created=created[0];handle=created['process_handle']
    process=[r for r in cleanup['resources'] if r['label']=='process'];assert len(process)==1
    process=process[0];assert process['native']==handle and process['terminal_confirmed'] is True and memory['pid']==created['pid']
    terminal=[(i,e) for i,e in enumerate(events) if e['action']=='independent_terminal_before_close'];assert len(terminal)==1
    terminal_index,terminal=terminal[0]
    assert terminal['resource_id']==process['resource_id'] and terminal['handle']==handle
    assert terminal['wait_result']==0 and terminal['error'] is None and terminal['exit_code']==life['exit_code']
    closed=[(i,e) for i,e in enumerate(events) if i>created_index and e['action']=='actual_close' and e['handle']==handle]
    assert len(closed)==1 and created_index<terminal_index<closed[0][0] and closed[0][1]['result'] is True
    waits=[e for e in events if e['action']=='actual_wait'];assert all(e['handle']==handle for e in waits)
    deletes=[e for e in events if e['action']=='actual_delete_profile'];assert len(deletes)==1
    assert deletes[0]['hresult']==0 and deletes[0]['profile_name']==memory['profile_name']
    profiles.append(memory['profile_name']);assert profiles[-1].startswith('DeepEye.P1a.')
    log=raw(A/(case['test']+'.unittest.log')).decode('utf8').replace('\r\n','\n')
    assert 'Ran 1 test' in log and '\nOK\n' in log and 'skipped' not in log.lower() and '... ok' in log
    stdout=raw(folder/'fixture_stdout.bin');assert len(stdout)<=4096
    stage_fixture=raw(folder/'r/fixture.py')
    expected_fixture=raw(P/'competition/deepeye/simulation/isolation/fixture.py')
    if index<2:
        trusted=memory['trusted']
        assert all(trusted[k] is True for k in ('is_appcontainer','sid_matches','win32k_disabled','child_process_restricted','in_job','job_limits_match','resumed_after_verification'))
        assert trusted['capability_count']==0
        assert trusted['job_limits']=={'limit_flags':0x2108,'active_process_limit':1,'process_memory_limit':268435456,'ui_restrictions':255}
        assert memory==stale and cleanup['evidence_complete'] is True and not memory['evidence_errors']
    if index==0:
        assert stage_fixture==expected_fixture
        assert memory['verdict']['passed'] is True and not memory['verdict']['failures'] and not memory.get('error')
        assert life['exit_code']==0xc0000008 and life['terminated_by_launcher'] is False
        frames=[json.loads(line) for line in stdout.decode('utf8').splitlines()]
        assert [f['phase'] for f in frames]==['positive_controls','boundaries','excluded_handle_attempt']
        assert frames[-1]['handle']==inheritance['deliberately_excluded_inheritable_canary']
        assert frames[0]['result']['model_ok'] is True and frames[0]['result']['pipe_ok'] is True and frames[0]['result']['cpu_output']==23
        boundary=frames[1]['result'];assert boundary['truth_open_error']==5
        assert boundary['process_access_errors']=={'8':5,'16':5,'32':5,'64':5,'128':5}
        assert trusted['mitigation_raw']['strict_handle']&1 and memory['fixture']['fatal_handle_denial_attested'] is True
        assert [(e['timeout_ms'],e['result']) for e in waits]==[(15000,0),(0,0),(5000,0)]
        assert not any(e['action']=='actual_terminate' for e in events)
    else:
        assert memory['verdict']['passed'] is False and life['terminated_by_launcher'] is True and life['exit_code']==0xdead
        terminate=[e for e in events if e['action']=='actual_terminate'];assert len(terminate)==1
        assert terminate[0]['handle']==handle and terminate[0]['code']==0xdead and terminate[0]['result'] is True
        assert stdout==b''
        raw(folder/'failure.txt')
        if index==1:
            assert stage_fixture==b'import time; time.sleep(10)\n'
            assert memory['error']['type']=='TimeoutError' and '0x00000102' in memory['error']['message']
            assert [(e['timeout_ms'],e['result']) for e in waits]==[(100,258),(0,258),(5000,0)]
            assert any(x.get('timeout_test_replacement')=='fixture.py' and x['sha256']==sha(stage_fixture) for x in runtime)
        else:
            assert stage_fixture==expected_fixture
            assert memory['error']['type']=='OSError' and memory['error']['message']=='intentional persistence failure after process creation'
            assert cleanup['evidence_complete'] is False and len(cleanup['audit_errors'])==50 and len(memory['evidence_errors'])==52
            assert [(e['timeout_ms'],e['result']) for e in waits]==[(0,258),(5000,0)]
            assert 'pid' not in stale and 'verdict' not in stale and stale['lifecycle']=={} and 'finished_utc' not in stale
            assert 'trusted' not in memory and 'fixture' not in memory
            recovered=read(folder/'expected-persistence-failure-memory.json');assert recovered==memory
    summary.append({'test':case['test'],'run_id':folder.name,'pid':created['pid'],'process_handle':handle,
        'terminal_before_close':terminal,'close_event_index':closed[0][0],
        'resource_count':len(cleanup['resources']),'all_resources_confirmed':True,'profile_absence_observed':True,
        'product_passed':memory['verdict']['passed'],'fixture_test_passed':True,'error_type':memory.get('error',{}).get('type'),
        'exit_code':life['exit_code'],'evidence_complete':cleanup['evidence_complete'],
        'stale_receipt':index==2,'observation_sha256':case['observation_sha256'],'memory_sha256':case['memory_sha256']})
assert len(set(run_ids))==3 and len(set(profiles))==3
for path,want in list(hashes.items()):
    data=Path(path).read_bytes();assert {'size':len(data),'sha256':sha(data)}==want,path
save('evidence-hashes.json',hashes)
save('supporting-source-hashes.json',support)
save('verified-cases.json',summary)
save('receipt.json',{'work_id':'A-isolation-native-evidence-review-20261019-v1','job_id':'child-a17dc889e3c346bc9306dfe3d17f3f2f',
    'reviewer':'/root/r03_review_20261018','result':'saved native evidence reconciled for exactly3 CPU fixtures',
    'cases':summary,'attempt':'attempt-01','source_manifest_sha256':PIN,'harness_sha256':H,
    'evidence_files_verified':len(hashes),'supporting_source_files_verified':len(support),'source_unchanged':True,
    'formal_acceptance':'not_run','reviewer_native_execution':False,'truth_canary_contents_read':False,
    'runtime_binaries_copied':False,'requirements_sha256':reqhash,
    'official_exec_exit':{'session_id':87134,'exit_code':0,'provenance':'provided by main official tool result; not rerun or queried by this reviewer'},
    'limitations':['saved same-run native readbacks reviewed; no current OS identity/profile probe',
                   'persistent-save case ended before trusted token/Job readback and resume; proves cleanup only',
                   'no four-process/G03/ROCm/AI/game/R03/board or formal acceptance']})
print(json.dumps({'result':'PASS','cases':len(summary),'evidence_files':len(hashes),'supporting_sources':len(support),
    'source_unchanged':True,'receipt_sha256':sha((O/'receipt.json').read_bytes())},indent=2))

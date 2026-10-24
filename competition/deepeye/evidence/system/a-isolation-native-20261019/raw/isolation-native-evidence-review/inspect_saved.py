"""Only saved JSON/log metadata; never open truth canaries or runtime binaries."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;N=O.parent/'isolation-launcher-native';A=N/'attempt-01'
campaign=json.loads((A/'campaign-result.json').read_bytes())
for case in campaign['cases']:
    folder=Path(case['run_directory']);assert folder.parent.resolve()==A.resolve()
    memory=json.loads((folder/'main-returned-memory.json').read_bytes())
    observed=json.loads((folder/'main-observation.json').read_bytes())
    stale=json.loads((folder/'receipt.json').read_bytes())
    summary={'test':case['test'],'run_id':folder.name,'saved_files':[p.name for p in folder.iterdir() if p.is_file()],
        'memory':{key:memory.get(key) for key in ('verdict','error','parent_controls','trusted','requested_policy','inheritance','environment_keys','lifecycle','fixture')},
        'cleanup':{key:memory['cleanup'].get(key) for key in ('resources_complete','evidence_complete','coordinator_success','unresolved','cleanup_errors')},
        'error_counts':{'evidence':len(memory.get('evidence_errors',[])),'audit':len(memory['cleanup'].get('audit_errors',[])),
                        'resources':len(memory['cleanup'].get('resources',[]))},
        'observation':{key:observed.get(key) for key in ('unresolved','profile_absence_after_return')},
        'process_events':[event for event in observed['events'] if event['action'] in ('actual_create_suspended_return','actual_wait','actual_terminate','independent_terminal_before_close','actual_delete_profile')],
        'receipt':{key:stale.get(key) for key in ('pid','verdict','error','trusted','lifecycle','finished_utc')},
        'log':(A/(case['test']+'.unittest.log')).read_text(encoding='utf8')}
    print(json.dumps(summary,ensure_ascii=False,indent=2))

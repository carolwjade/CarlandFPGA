"""Main's retained interpreter. No case runs merely by loading this script."""
import datetime,hashlib,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a';HERE=OUT/'actor-native-main'
assert sys.flags.interactive and sys.version_info[:2]==(3,12)
sys.path[:0]=[str(PRODUCT),str(PRODUCT/'competition/deepeye'),str(ROOT/'.local/deepeye-host-deps')]
from competition.deepeye.tests.isolation import test_actor_windows_live as probe
case_results={};case_errors=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute_case(case):
    """One explicit main invocation, no campaign loop and no retry."""
    assert case in probe.CASES and case not in case_results
    assert not case_errors and not any(r.unresolved or not r.passed for r in case_results.values())
    index=json.loads((HERE/(case+'.stage.json')).read_bytes());attempt=Path(index['attempt_directory'])
    allow=attempt/'allow.json';record=json.loads(allow.read_bytes())
    assert record['approved_by']==probe.DIRECTOR and record['native_execution'] is True and record['case']==case
    approval=json.loads((attempt/'main-approval.json').read_bytes());assert approval['allow_sha256']==digest(allow)
    assert approval['harness_independent_review_accepted'] is True
    before={n:digest(PRODUCT/n) for n in record['sources']};assert before==record['sources']
    invocation={'case':case,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'allow_sha256':digest(allow),'source_hashes':before,'interpreter_flags_interactive':sys.flags.interactive,'python':sys.version,'native_modules_before':[n for n in sys.modules if n.endswith('.isolation.win32')]}
    with (attempt/'main-invocation.json').open('x',encoding='utf-8') as f:json.dump(invocation,f,indent=2);f.write('\n')
    try:
        context=probe.run_case(HERE,allow,case)
        case_results[case]=context  # Strong original recovery roots, including quarantine.
    except BaseException as error:
        case_errors.append(error)
        with (attempt/'main-invocation-error.json').open('x',encoding='utf-8') as f:json.dump({'type':type(error).__name__,'message':str(error),'retained_contexts':len(probe._ATTEMPTS),'unresolved':[c.unresolved for c in probe._ATTEMPTS]},f,indent=2)
        raise
    after={n:digest(PRODUCT/n) for n in record['sources']}
    document={'case':case,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed_fixture_expectation':context.passed,'unresolved':context.unresolved,'cleanup':context.cleanup,'primary_error':None if context.primary is None else {'type':type(context.primary).__name__,'message':str(context.primary)},'raw_stdout_hex':context.raw.hex(),'source_hashes_unchanged':before==after,'source_hashes_after':after,'retained_contexts':len(probe._ATTEMPTS),'registry_retains_exact_actor':context.registry is not None and context.actor is not None and any(o is context.actor for o in context.registry._owners),'fixture_result_sha256':digest(attempt/'fixture-memory-result.json') if (attempt/'fixture-memory-result.json').exists() else None,'all29':'not_run'}
    with (attempt/'main-return.json').open('x',encoding='utf-8') as f:json.dump(document,f,indent=2);f.write('\n')
    assert before==after
    print(json.dumps({k:document[k] for k in ('case','passed_fixture_expectation','unresolved','source_hashes_unchanged','registry_retains_exact_actor')}))
    print(json.dumps({'state':context.cleanup.get('state'),'resources_complete':context.cleanup.get('resources_complete'),'profile_outcome':context.cleanup.get('profile_outcome'),'original_process_exit':context.cleanup.get('original_process_exit'),'primary':document['primary_error']}))
    return context
print('RETAINED_INTERPRETER_READY; no native case has run; execute exactly one approved case at a time')

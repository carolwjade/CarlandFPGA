import hashlib,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRODUCT=HERE.parents[2]/'.local/deepeye-implementation-a'
MODULES=[
 'competition.deepeye.tests.simulation.test_actor_owner',
 'competition.deepeye.tests.simulation.test_actor_lifetime',
 'competition.deepeye.tests.simulation.test_pc_direct_runtime',
 'independent_actor_tests','test_windows_cleanup']
suite=unittest.defaultTestLoader.loadTestsFromNames(MODULES)
assert suite.countTestCases()==148,suite.countTestCases()
result=unittest.TextTestRunner(verbosity=2).run(suite)
origins={}
for name,module in tuple(sys.modules.items()):
    if name.startswith(('competition.deepeye.','simulation.','integration.')) or name in ('test_windows_cleanup','test_host_envelope','test_pc_direct_watchdog','independent_actor_tests'):
        file=getattr(module,'__file__',None)
        if not file:continue
        path=Path(file).resolve()
        if name=='independent_actor_tests':
            assert path==HERE/'independent_actor_tests.py'
            assert hashlib.sha256(path.read_bytes()).hexdigest()=='de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f'
        else:assert path.is_relative_to(PRODUCT.resolve()),(name,str(path))
        origins[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
for needed in ('competition.deepeye.simulation.isolation.actor_owner','competition.deepeye.simulation.authority.motion.passage_phase','competition.deepeye.simulation.authority.motion.workspace_boundaries'):
    assert needed in origins,needed
for name,doc in [('module-origins.json',origins),('unittest-result.json',dict(modules=MODULES,tests=result.testsRun,skipped=len(result.skipped),failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful()))]:
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(doc,f,indent=2);f.write('\n')
raise SystemExit(0 if result.wasSuccessful() else 1)

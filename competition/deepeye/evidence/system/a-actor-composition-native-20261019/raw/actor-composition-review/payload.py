import unittest,pathlib,hashlib,json,sys
H=pathlib.Path(__file__).resolve().parent;P=H.parents[2]/'.local/deepeye-implementation-a';label,*modules=sys.argv[1:]
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in modules);result=unittest.TextTestRunner(verbosity=2).run(suite)
origins={}
for name,mod in list(sys.modules.items()):
 raw=getattr(mod,'__file__',None)
 if raw:
  p=pathlib.Path(raw).resolve()
  if p.is_relative_to(P) and p.is_file():origins[name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert not any(n.endswith('.isolation.win32') or n.endswith('.isolation.prototype') or n.endswith('.test_actor_windows_live') for n in sys.modules)
assert origins['competition.deepeye.simulation.authority.actor_composition']['path']==str((P/'competition/deepeye/simulation/authority/actor_composition.py').resolve())
(H/(label+'.result.json')).write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'module_origins':origins},ensure_ascii=False,indent=2),encoding='utf-8')
sys.exit(not result.wasSuccessful())

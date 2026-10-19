import unittest,sys,pathlib,json,hashlib
H=pathlib.Path(__file__).resolve().parent;P=H.parents[2]/'.local/deepeye-implementation-a'
module,label=sys.argv[1:];suite=unittest.defaultTestLoader.loadTestsFromName(module)
result=unittest.TextTestRunner(verbosity=2).run(suite)
origins={}
for name,mod in list(sys.modules.items()):
 f=getattr(mod,'__file__',None)
 if f:
  path=pathlib.Path(f).resolve()
  if path.is_relative_to(P) and path.is_file():origins[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
assert not any(n.endswith('.isolation.win32') for n in origins),'no real ctypes/native module expected'
assert origins['competition.deepeye.simulation.isolation.actor_owner']['path']==str((P/'competition/deepeye/simulation/isolation/actor_owner.py').resolve())
(H/(label+'.module-origins.json')).write_text(json.dumps(origins,ensure_ascii=False,indent=2),encoding='utf-8')
sys.exit(not result.wasSuccessful())

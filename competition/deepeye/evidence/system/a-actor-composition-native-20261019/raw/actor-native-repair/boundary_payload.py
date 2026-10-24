import unittest,pathlib,sys,json,hashlib
import exit_boundaries as cases
H=pathlib.Path(__file__).resolve().parent;P=H.parents[2]/'.local/deepeye-implementation-a';label=sys.argv[1]
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cases.ExitBoundaries))
(H/(label+'.witnesses.json')).write_text(json.dumps(cases.WITNESSES,indent=2),encoding='utf-8')
origins={}
for name,module in list(sys.modules.items()):
 path=getattr(module,'__file__',None)
 if path and pathlib.Path(path).resolve().is_relative_to(P):
  p=pathlib.Path(path).resolve();origins[name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert not any(n.endswith('.isolation.win32') or n.endswith('.isolation.prototype') for n in sys.modules)
(H/(label+'.module-origins.json')).write_text(json.dumps(origins,ensure_ascii=False,indent=2),encoding='utf-8')
sys.exit(not result.wasSuccessful())

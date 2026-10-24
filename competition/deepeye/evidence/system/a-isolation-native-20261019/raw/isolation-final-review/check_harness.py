"""Fake-only review. Never invoke main or real Win32 APIs."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,sys,unittest
from types import SimpleNamespace
from unittest.mock import patch
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
SOURCE=OUT.parent/'isolation-launcher-native/run_native.py'
PIN='d3990462ec2acf77b4b06212cad39eece16e3cb36efc82ea7ce6dcfa15cc8060'
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
ast.parse(raw)
(OUT/'run_native.reviewed.py').write_bytes(raw)
(OUT/'plan.reviewed.md').write_bytes((SOURCE.parent/'plan.md').read_bytes())
req=json.loads((ROOT/'.local/deepeye-implementation-a/docs/competition/deepeye-2026/immutable_scope.json').read_bytes())['requirements']
reqhash=hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert reqhash=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
spec=importlib.util.spec_from_file_location('reviewed_main_harness',OUT/'run_native.reviewed.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
assert not (SOURCE.parent/'native-execution-gate.json').exists()

class Held(BaseException):pass

class HoldBoundaryTests(unittest.TestCase):
    def exercise(self,*,output_error=False,input_error=False):
        owner=SimpleNamespace(unresolved=(SimpleNamespace(resource_id='held-fixture-handle'),),provenance=SimpleNamespace(owner_id='fake-owner'))
        h.LIVE_OWNERS[:]=[owner];waited=[]
        class Event:
            def wait(self):waited.append('retention wait reached');raise Held()
        def print_fake(*args,**kwargs):
            if output_error:raise OSError('fake output persistence unavailable')
        def read_fake():
            if input_error:raise OSError('fake status input unavailable')
            return ''
        error=None
        with patch.object(h,'print',print_fake,create=True),patch.object(h.threading,'Event',Event),patch.object(h.sys,'stdin',SimpleNamespace(readline=read_fake)):
            try:h.hold_unresolved()
            except BaseException as exc:error=exc
        self.assertTrue(waited,'unresolved owner was abandoned before the retention wait')
        self.assertIsInstance(error,Held)
        self.assertIs(owner,h.LIVE_OWNERS[0])

    def test_output_failure_cannot_bypass_unresolved_owner_retention(self):self.exercise(output_error=True)
    def test_input_failure_cannot_bypass_unresolved_owner_retention(self):self.exercise(input_error=True)

if __name__=='__main__':
    os.environ.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT',None)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HoldBoundaryTests))
    (OUT/'harness-review-metadata.json').write_text(json.dumps({'harness_sha256':PIN,'requirements_sha256':reqhash,
        'gate_present':False,'native_api_calls':0,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)},indent=2)+'\n',encoding='utf8')
    sys.exit(0 if result.wasSuccessful() else 1)

"""Closure matrix, original author assertions plus distinct provenance guards.
All registry/actor/native seams are replaced by the unchanged reviewer fake.
"""
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
import hashlib,json,sys,unittest
import review_cases as review
import exit_boundaries as author
O=Path(__file__).resolve().parent
OBS=[]

class Provenance(unittest.TestCase):
    def test_original_reference_id_native_membership_and_map_shape_cannot_substitute(self):
        for fault in ('reference','resource_id','native','membership','dict_subclass'):
            fixture=review.Cases();fixture.setUp();original=review.FakeOwner.close
            def close(owner,reason):
                original(owner,reason)
                if fault=='reference':owner._process=N(resource_id='original-process',native=42,terminal_confirmed=True)
                elif fault=='resource_id':owner._process.resource_id='different-process'
                elif fault=='native':owner._process.native=43
                elif fault=='membership':owner._resources.references=[]
                else:
                    class Codes(dict):pass
                    owner._backend.exit_codes=Codes(owner._backend.exit_codes)
            try:
                with patch.object(review.FakeOwner,'close',close):result=fixture.fake_run('natural')
                saved=review.WITNESSES[-1]['persisted_result']
                OBS.append({'fault':fault,'passed':result.passed,'cleanup':result.cleanup,'saved':saved})
                self.assertFalse(result.passed);self.assertFalse(saved['normal_exit_success']);self.assertFalse(saved['evidence_success'])
                self.assertEqual('original-process',result.original_process_resource_id)
                self.assertIs(result.original_process_reference,result.actor._original_process)
            finally:fixture.tearDown()

if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(author.ExitBoundaries),unittest.defaultTestLoader.loadTestsFromTestCase(Provenance)])
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    (O/'closure-witnesses.json').write_text(json.dumps({'author_matrix':author.WITNESSES,'new_provenance':OBS},indent=2)+'\n',encoding='utf-8')
    origins={name:{'path':str(Path(module.__file__).resolve()),'sha256':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()} for name,module in sys.modules.items() if name in ('competition.deepeye.tests.isolation.test_actor_windows_live','competition.deepeye.simulation.isolation.actor_fixture')}
    (O/'module-origins.json').write_text(json.dumps(origins,indent=2)+'\n',encoding='utf-8')
    assert not any(name.endswith('.isolation.win32') or name.endswith('.isolation.actor_composition') or name.endswith('.isolation.actor_owner') for name in sys.modules)
    raise SystemExit(0 if r.wasSuccessful() else 1)

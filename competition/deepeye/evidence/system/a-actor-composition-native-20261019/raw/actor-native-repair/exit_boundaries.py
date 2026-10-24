"""Offline classification matrices. Every registry/owner/native seam is fake."""
import enum,json,pathlib,unittest
from unittest.mock import patch
import review_cases as review
H=pathlib.Path(__file__).resolve().parent
WITNESSES=[]
class Number(int):pass
class Exit(enum.IntEnum):ZERO=0


class ExitBoundaries(unittest.TestCase):
 def test_complete_pipeline_normal_exit_matrix(self):
  cases=[('valid-zero',0,False,True),('exit17',17,False,False),('missing','missing',False,False),
   ('bool',False,False,False),('float',0.0,False,False),('int-subclass',Number(0),False,False),
   ('enum',Exit.ZERO,False,False),('forced',0,True,False),('malformed-terminated',0,0,False),('missing-terminated',0,'missing',False)]
  for name,code,terminated,expected in cases:
   with self.subTest(case=name):
    f=review.Cases();f.setUp();original=review.FakeOwner.close
    def close(owner,reason):
     original(owner,reason)
     if code=='missing':owner._backend.exit_codes.clear()
     else:owner._backend.exit_codes['original-process']=code
     if terminated=='missing':del owner._backend.terminated
     else:owner._backend.terminated=terminated
    try:
     with patch.object(review.FakeOwner,'close',close):result=f.fake_run('natural')
     persisted=review.WITNESSES[-1]['persisted_result']
     WITNESSES.append({'name':name,'code_type':type(code).__name__,'terminated_type':type(terminated).__name__,'passed':result.passed,'persisted_passed':persisted['passed'],'cleanup':result.cleanup})
     self.assertEqual(expected,result.passed,'READY + terminal/resource cleanup must not substitute normal exit')
     self.assertEqual(expected,persisted['passed'])
     observed=result.cleanup.get('original_process_exit')
     self.assertIsNotNone(observed,'exit provenance absent')
     self.assertEqual('original-process',observed['resource_id'])
     self.assertEqual(code!='missing',observed['exit_code_recorded'])
     self.assertEqual(expected,persisted['normal_exit_success'])
    finally:f.tearDown()

 def test_other_process_zero_cannot_replace_original_exit(self):
  f=review.Cases();f.setUp();original=review.FakeOwner.close
  def close(owner,reason):original(owner,reason);owner._backend.exit_codes={'different-process':0}
  try:
   with patch.object(review.FakeOwner,'close',close):result=f.fake_run('natural')
   self.assertFalse(result.passed);self.assertEqual('original-process',result.original_process_resource_id)
   self.assertFalse(result.cleanup['original_process_exit']['exit_code_recorded'])
  finally:f.tearDown()

 def test_expected_negative_cases_are_not_normal_evidence_success(self):
  for mode,case in [('expiry','fixed-unbound-expiry'),('persistence','persistence-after-acquisition')]:
   with self.subTest(case=case):
    f=review.Cases();f.setUp()
    try:
     result=f.fake_run(mode,case);persisted=review.WITNESSES[-1]['persisted_result']
     self.assertTrue(result.passed)
     self.assertFalse(persisted.get('normal_exit_success',True))
     self.assertFalse(persisted.get('evidence_success',True))
     self.assertEqual('expected_negative_fixture',persisted['result_semantics'])
    finally:f.tearDown()

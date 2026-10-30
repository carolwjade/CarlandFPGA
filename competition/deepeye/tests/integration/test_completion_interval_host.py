import json,unittest
from competition.deepeye.integration import host_envelope as host
CTX=dict(session=7,config_epoch=2,boot_sha256='a'*64,transport_profile_id=1,source_id=3,topology_id=1,acquisition_profile_id=1)
NOW=5000000000
def candidate():
 return dict(schema_version=2,kind='model_candidate',context=CTX,candidate_id=1,model_sha256='b'*64,observation={'context':CTX,'observed_seq':9},target=dict(action=1,yaw_q=0,pitch_q=0,speed_code=5,duration_ms=1),completion_observed_interval_ns={'lower_ns':NOW-1000,'upper_ns':NOW-100},basis='host_dispatch_to_complete_result_observed_v1')
def encode(v):return json.dumps(v,separators=(',',':')).encode()
def bounds():return dict(max_age_ns=100000000,source_deadline_ns=NOW+90000000,dispatch_deadline_ns=NOW+80000000,previous_deadline_ns=None)
class Controls(unittest.TestCase):
 def test_explicit_opt_in_interval(self):
  c=host.validate_message(encode(candidate()),producer='ai_controller',context=CTX,now_ns=NOW,enable_completion_interval=True,completion_bounds=bounds())
  self.assertEqual(NOW+80000000,c.valid_until_ns)

 def test_default_scalar_and_non_optin_reject(self):
  d=candidate();d['schema_version']=1;d['completed_monotonic_ns']=NOW-1;del d['completion_observed_interval_ns'];del d['basis']
  result=host.validate_message(encode(d),producer='ai_controller',context=CTX,now_ns=NOW)
  self.assertEqual('model_candidate',result.kind)
  with self.assertRaises(ValueError):host.validate_message(encode(d),producer='ai_controller',context=CTX,now_ns=NOW,completion_bounds=bounds())
 def test_original_bounds_and_strict_time(self):
  for changed in ({'max_age_ns':True},{'max_age_ns':0},{'source_deadline_ns':None},{'dispatch_deadline_ns':None},{'previous_deadline_ns':NOW}):
   b=bounds();b.update(changed)
   with self.assertRaises(ValueError):host.validate_message(encode(candidate()),producer='ai_controller',context=CTX,now_ns=NOW,enable_completion_interval=True,completion_bounds=b)
  d=candidate();d['completion_observed_interval_ns']['upper_ns']=NOW+1
  with self.assertRaises(ValueError):host.validate_message(encode(d),producer='ai_controller',context=CTX,now_ns=NOW,enable_completion_interval=True,completion_bounds=bounds())
 def test_immutable_and_duration_deadline(self):
  c=host.validate_message(encode(candidate()),producer='ai_controller',context=CTX,now_ns=NOW,enable_completion_interval=True,completion_bounds=bounds())
  with self.assertRaises(TypeError):c.document['target']['speed_code']=1
  mod=__import__('sys').modules['deepeye_completion_interval']
  ok=mod.adapt_action_candidate(c,host_issue_ns=NOW,now_ns=NOW,previous_deadline_ns=NOW+2000000)
  self.assertEqual(NOW+1000000,ok.deadline_ns);self.assertEqual('none',ok.authority)
  with self.assertRaises(ValueError):mod.adapt_action_candidate(c,host_issue_ns=NOW,now_ns=NOW,previous_deadline_ns=NOW+999999)
 def test_stop_has_no_lease(self):
  d=candidate();d['target']=dict(action=0,yaw_q=0,pitch_q=0,speed_code=0,duration_ms=0);d['observation']=None
  c=host.validate_message(encode(d),producer='ai_controller',context=CTX,now_ns=NOW,enable_completion_interval=True,completion_bounds=bounds())
  mod=__import__('sys').modules['deepeye_completion_interval'];self.assertIsNone(mod.adapt_action_candidate(c,host_issue_ns=NOW,now_ns=NOW,previous_deadline_ns=None).deadline_ns)

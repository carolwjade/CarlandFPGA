import sys
sys.path.insert(0,"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps")
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/"python-source"))
"""Pure CPU controls for an explicitly provisional fixed-C0 demo profile."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import unittest
from competition.deepeye.simulation.authority import demo30h_ai_em3_profile_v2 as profiles

class EntryC0Controls(unittest.TestCase):
 def selected(self):
  self.assertTrue(hasattr(profiles,'NAV_ENTRY_C0_V1'),'explicit fixed-C0 selector missing')
  return profiles.selected_profile(8_000_000_000,navigation_profile=profiles.NAV_ENTRY_C0_V1)
 def package(self,selected):
  path=Path(selected.package_root)/'c37_package.py';spec=importlib.util.spec_from_file_location('_synthetic_entry490',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def public(self,selected,counts=None):
  pose=dict(position_m=[0,0,0],orientation_xyzw=[0,0,0,1]);now=10_000_000_000
  obs=dict(sample_id='a'*64,counts=[3099,2006,2084,None] if counts is None else counts,quality=7,missing_feature_mask=8,adc_qpc_ns=now,em_qpc_ns=now,adc_pose=pose,em_pose=pose)
  return dict(schema_version=1,projection_id='g05_csr_em3_demo_view_v2',engineering_profile=dict(selected.engineering_profile),enabled=True,now_qpc_ns=now,pose=pose,goal_m=[0,0,1],observation=obs,history=[],executed_actions=[])
 def infer(self,selected,public):
  package=self.package(selected);ids=dict(operation_id='synthetic490',run_id='synthetic490',actor_instance_id='synthetic490',invocation_id=1,tested_commit='a'*40,package_manifest_sha256=selected.manifest_sha256)
  req=package.make_request(ids,public,enabled=True);out=package.process_wire(req);pair=selected.verifier.verify_pair(req,out,expected_ids=ids)
  self.assertEqual(pair.result['status'],'RESULT');return pair.result['result']
 def test_old_packages_and_selectors_keep_fixed_bytes_and_stop_sample(self):
  old=profiles.selected_profile(5_000_000_000,navigation_profile=profiles.NAV_FAST_V1)
  self.assertEqual(old.model_sha256,'9068a7699fd11765d04245460989105fced3983b03e0c0876c54df89f958505d')
  self.assertEqual(old.manifest_sha256,'ffb1e4d333405462285c31ca4f6de7369ddfe492d67fd59b3d0045f6b3135b81')
  self.assertEqual(self.infer(old,self.public(old))['status'],'STOP')
 def test_new_profile_advises_from_exact_counts_and_retains_missing_C3_penalties(self):
  s=self.selected();public=self.public(s);advice=self.infer(s,public)
  self.assertEqual(advice['status'],'ADVISE');self.assertEqual(list(advice['observation']['counts']),[3099,2006,2084,None])
  self.assertFalse(advice['c3_observed']);self.assertEqual(advice['missing_feature_mask'],8)
  self.assertGreaterEqual(advice['risk'],.25);self.assertGreaterEqual(advice['uncertainty'],.7)
  self.assertGreater(advice['speed_limit_m_s'],0);self.assertLessEqual(advice['speed_limit_m_s'],.25)
  expected=min(1,abs((-.6989700043360187+4*3099/4095)-2.3)/2+.25)
  self.assertAlmostEqual(advice['map_cells'][0]['risk'],expected)
  self.assertEqual(s.prospective_command_max_ns,3_000_000_000)
 def test_gradient_sign_changes_candidate_direction(self):
  s=self.selected();left=self.infer(s,self.public(s,[3684,1229,2048,None]));right=self.infer(s,self.public(s,[3684,2866,2048,None]))
  self.assertEqual((left['status'],right['status']),('ADVISE','ADVISE'))
  self.assertGreater(left['direction_world'][0],0);self.assertLess(right['direction_world'][0],0)
 def test_fault_expiry_contact_and_profile_tampering_remain_rejected_or_stop(self):
  s=self.selected()
  for case in ('fault','expired','contact'):
   p=self.public(s)
   if case=='fault':p['observation'].update(counts=[None]*4,quality=4096,missing_feature_mask=15,em_qpc_ns=None,em_pose=None)
   elif case=='expired':p['now_qpc_ns']+=8_000_000_001
   else:p['observation'].update(counts=[3099,2006,2084,2000],quality=15,missing_feature_mask=0)
   self.assertEqual(self.infer(s,p)['status'],'STOP')
  p=self.public(s);p['engineering_profile']['sha256']='0'*64
  with self.assertRaises(ValueError):s.verifier.validate_public(p)
 def test_new_verifier_rejects_old_package_pair(self):
  new=self.selected();old=profiles.selected_profile(5_000_000_000,navigation_profile=profiles.NAV_FAST_V1)
  p=self.public(old);pkg=self.package(old);ids=dict(operation_id='synthetic490',run_id='synthetic490',actor_instance_id='synthetic490',invocation_id=1,tested_commit='a'*40,package_manifest_sha256=old.manifest_sha256)
  req=pkg.make_request(ids,p,enabled=True)
  with self.assertRaises(ValueError):new.verifier.verify_pair(req,pkg.process_wire(req),expected_ids=ids)
 def test_strict_factory_and_owned_selector_preserve_typed_package_identity(self):
  from dataclasses import replace
  from types import SimpleNamespace as NS
  from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import _selected_ai_profile
  strict=profiles.selected_profile(5_000_000_000)
  self.assertEqual(strict.manifest_sha256,'ffb1e4d333405462285c31ca4f6de7369ddfe492d67fd59b3d0045f6b3135b81')
  self.assertEqual(strict.prospective_command_max_ns,1_000_000_000)
  self.assertIs(type(strict.verifier),profiles.verifier.BoundVerifier)
  new=self.selected();config=NS(g05_csr_v1=NS(demo_ai_profile=new,max_source_age_ns=8_000_000_000))
  self.assertEqual(_selected_ai_profile(config),new)
  config.g05_csr_v1.demo_ai_profile=replace(new,model_sha256='0'*64)
  with self.assertRaises(ValueError):_selected_ai_profile(config)
  with self.assertRaises(ValueError):profiles.selected_profile(8_000_000_001,navigation_profile=profiles.NAV_ENTRY_C0_V1)
 def test_explicit_8s_demo_age_does_not_promote_original_100ms_quality_or_old_caps(self):
  s=self.selected();p=self.public(s);p['now_qpc_ns']+=8_000_000_000
  self.assertEqual(self.infer(s,p)['status'],'ADVISE')
  quality=s.verifier.quality_report(p)
  self.assertTrue(quality['demo_age_accepted']);self.assertFalse(quality['original100ms_quality']);self.assertFalse(quality['target100ms_met'])
  self.assertEqual(quality['source_quality'],7);self.assertFalse(quality['C3_valid'])
  p['now_qpc_ns']+=1
  self.assertEqual(self.infer(s,p)['status'],'STOP')
  for nav in (None,profiles.NAV_FAST_V1):
   with self.assertRaises(ValueError):profiles.selected_profile(5_000_000_001,navigation_profile=nav)
  original_quality=self.public(s);original_quality['observation'].update(counts=[3099,2006,2084,0],quality=15,missing_feature_mask=0)
  original_quality['now_qpc_ns']+=100_000_000
  self.assertTrue(s.verifier.quality_report(original_quality)['original100ms_quality'])
  original_quality['now_qpc_ns']+=1
  quality=s.verifier.quality_report(original_quality)
  self.assertFalse(quality['original100ms_quality']);self.assertTrue(quality['demo_age_accepted'])
  strict_branch=self.public(s);strict_branch['engineering_profile']=dict(profiles.STRICT_ENGINEERING_PROFILE)
  strict_branch['now_qpc_ns']+=5_000_000_001
  self.assertEqual(self.package(s)._infer(strict_branch,{'core_ran':False})['status'],'STOP')



class Entry12Controls(unittest.TestCase):
 def selected(self):
  self.assertTrue(hasattr(profiles,'NAV_ENTRY_C0_12S_V3'),'explicit fixed-C0 selector missing')
  return profiles.selected_profile(12_000_000_000,navigation_profile=profiles.NAV_ENTRY_C0_12S_V3)
 def package(self,selected):
  path=Path(selected.package_root)/'c37_package.py';spec=importlib.util.spec_from_file_location('_synthetic_entry490',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def public(self,selected,counts=None):
  pose=dict(position_m=[0,0,0],orientation_xyzw=[0,0,0,1]);now=10_000_000_000
  obs=dict(sample_id='a'*64,counts=[3099,2006,2084,None] if counts is None else counts,quality=7,missing_feature_mask=8,adc_qpc_ns=now,em_qpc_ns=now,adc_pose=pose,em_pose=pose)
  return dict(schema_version=1,projection_id='g05_csr_em3_demo_view_v2',engineering_profile=dict(selected.engineering_profile),enabled=True,now_qpc_ns=now,pose=pose,goal_m=[0,0,1],observation=obs,history=[],executed_actions=[])
 def infer(self,selected,public):
  package=self.package(selected);ids=dict(operation_id='synthetic490',run_id='synthetic490',actor_instance_id='synthetic490',invocation_id=1,tested_commit='a'*40,package_manifest_sha256=selected.manifest_sha256)
  req=package.make_request(ids,public,enabled=True);out=package.process_wire(req);pair=selected.verifier.verify_pair(req,out,expected_ids=ids)
  self.assertEqual(pair.result['status'],'RESULT');return pair.result['result']
 def test_old_packages_and_selectors_keep_fixed_bytes_and_stop_sample(self):
  old=profiles.selected_profile(5_000_000_000,navigation_profile=profiles.NAV_FAST_V1)
  self.assertEqual(old.model_sha256,'9068a7699fd11765d04245460989105fced3983b03e0c0876c54df89f958505d')
  self.assertEqual(old.manifest_sha256,'ffb1e4d333405462285c31ca4f6de7369ddfe492d67fd59b3d0045f6b3135b81')
  self.assertEqual(self.infer(old,self.public(old))['status'],'STOP')
 def test_new_profile_advises_from_exact_counts_and_retains_missing_C3_penalties(self):
  s=self.selected();public=self.public(s);advice=self.infer(s,public)
  self.assertEqual(advice['status'],'ADVISE');self.assertEqual(list(advice['observation']['counts']),[3099,2006,2084,None])
  self.assertFalse(advice['c3_observed']);self.assertEqual(advice['missing_feature_mask'],8)
  self.assertGreaterEqual(advice['risk'],.25);self.assertGreaterEqual(advice['uncertainty'],.7)
  self.assertGreater(advice['speed_limit_m_s'],0);self.assertLessEqual(advice['speed_limit_m_s'],.25)
  expected=min(1,abs((-.6989700043360187+4*3099/4095)-2.3)/2+.25)
  self.assertAlmostEqual(advice['map_cells'][0]['risk'],expected)
  self.assertEqual(s.prospective_command_max_ns,3_000_000_000)
 def test_gradient_sign_changes_candidate_direction(self):
  s=self.selected();left=self.infer(s,self.public(s,[3684,1229,2048,None]));right=self.infer(s,self.public(s,[3684,2866,2048,None]))
  self.assertEqual((left['status'],right['status']),('ADVISE','ADVISE'))
  self.assertGreater(left['direction_world'][0],0);self.assertLess(right['direction_world'][0],0)
 def test_fault_expiry_contact_and_profile_tampering_remain_rejected_or_stop(self):
  s=self.selected()
  for case in ('fault','expired','contact'):
   p=self.public(s)
   if case=='fault':p['observation'].update(counts=[None]*4,quality=4096,missing_feature_mask=15,em_qpc_ns=None,em_pose=None)
   elif case=='expired':p['now_qpc_ns']+=12_000_000_001
   else:p['observation'].update(counts=[3099,2006,2084,2000],quality=15,missing_feature_mask=0)
   self.assertEqual(self.infer(s,p)['status'],'STOP')
  p=self.public(s);p['engineering_profile']['sha256']='0'*64
  with self.assertRaises(ValueError):s.verifier.validate_public(p)
 def test_new_verifier_rejects_old_package_pair(self):
  new=self.selected();old=profiles.selected_profile(5_000_000_000,navigation_profile=profiles.NAV_FAST_V1)
  p=self.public(old);pkg=self.package(old);ids=dict(operation_id='synthetic490',run_id='synthetic490',actor_instance_id='synthetic490',invocation_id=1,tested_commit='a'*40,package_manifest_sha256=old.manifest_sha256)
  req=pkg.make_request(ids,p,enabled=True)
  with self.assertRaises(ValueError):new.verifier.verify_pair(req,pkg.process_wire(req),expected_ids=ids)
 def test_strict_factory_and_owned_selector_preserve_typed_package_identity(self):
  from dataclasses import replace
  from types import SimpleNamespace as NS
  from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import _selected_ai_profile
  strict=profiles.selected_profile(5_000_000_000)
  self.assertEqual(strict.manifest_sha256,'ffb1e4d333405462285c31ca4f6de7369ddfe492d67fd59b3d0045f6b3135b81')
  self.assertEqual(strict.prospective_command_max_ns,1_000_000_000)
  self.assertIs(type(strict.verifier),profiles.verifier.BoundVerifier)
  new=self.selected();config=NS(g05_csr_v1=NS(demo_ai_profile=new,max_source_age_ns=12_000_000_000))
  self.assertEqual(_selected_ai_profile(config),new)
  config.g05_csr_v1.demo_ai_profile=replace(new,model_sha256='0'*64)
  with self.assertRaises(ValueError):_selected_ai_profile(config)
  with self.assertRaises(ValueError):profiles.selected_profile(12_000_000_001,navigation_profile=profiles.NAV_ENTRY_C0_12S_V3)
 def test_explicit_12s_demo_age_does_not_promote_original_100ms_quality_or_old_caps(self):
  s=self.selected();p=self.public(s);p['now_qpc_ns']+=12_000_000_000
  self.assertEqual(self.infer(s,p)['status'],'ADVISE')
  quality=s.verifier.quality_report(p)
  self.assertTrue(quality['demo_age_accepted']);self.assertFalse(quality['original100ms_quality']);self.assertFalse(quality['target100ms_met'])
  self.assertEqual(quality['source_quality'],7);self.assertFalse(quality['C3_valid'])
  p['now_qpc_ns']+=1
  self.assertEqual(self.infer(s,p)['status'],'STOP')
  for nav in (None,profiles.NAV_FAST_V1):
   with self.assertRaises(ValueError):profiles.selected_profile(5_000_000_001,navigation_profile=nav)
  original_quality=self.public(s);original_quality['observation'].update(counts=[3099,2006,2084,0],quality=15,missing_feature_mask=0)
  original_quality['now_qpc_ns']+=100_000_000
  self.assertTrue(s.verifier.quality_report(original_quality)['original100ms_quality'])
  original_quality['now_qpc_ns']+=1
  quality=s.verifier.quality_report(original_quality)
  self.assertFalse(quality['original100ms_quality']);self.assertTrue(quality['demo_age_accepted'])
  strict_branch=self.public(s);strict_branch['engineering_profile']=dict(profiles.STRICT_ENGINEERING_PROFILE)
  strict_branch['now_qpc_ns']+=5_000_000_001
  self.assertEqual(self.package(s)._infer(strict_branch,{'core_ran':False})['status'],'STOP')




class TypedCaps(unittest.TestCase):
 def test_explicit_new12_old8_strict5_health_caps(self):
  from competition.deepeye.simulation.authority.g05_csr_channels_v1 import G05CsrPolicy
  cases=((None,5_000_000_000),(profiles.NAV_FAST_V1,5_000_000_000),(profiles.NAV_ENTRY_C0_V1,8_000_000_000),(profiles.NAV_ENTRY_C0_12S_V3,12_000_000_000))
  for nav,cap in cases:
   p=profiles.selected_profile(cap,navigation_profile=nav)
   G05CsrPolicy(cap,cap,0,0,p).check()
   with self.assertRaises(ValueError):profiles.selected_profile(cap+1,navigation_profile=nav)
   with self.assertRaises(ValueError):G05CsrPolicy(cap,cap+1,0,0,p).check()
   self.assertEqual(p.age_normalization_ms,5000)
   self.assertEqual(p.original_quality_age_ns,100_000_000)
  old=profiles.selected_profile(8_000_000_000,navigation_profile=profiles.NAV_ENTRY_C0_V1)
  self.assertEqual(old.model_sha256,'8746ef416c2416c9dddd6d932f022846298ddf688aaf20f4f981a3697dee1a27')
  self.assertEqual(old.manifest_sha256,'9069bcd1d1cc42388c8447600711eef22cbedb82e471ec3828f027b7b7b0a1e2')

if __name__=='__main__':unittest.main(verbosity=2)

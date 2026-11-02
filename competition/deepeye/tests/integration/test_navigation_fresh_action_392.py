"""SYNTHETIC_TEST: decision/finite-cap gates after original mapping validation.

No fake object here qualifies a source, channel, actor or board. Full original
mapping/committed-proof validation remains mandatory in the production caller.
"""
from types import SimpleNamespace as NS
import unittest
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
from competition.deepeye.simulation.authority import g05_csr_channels_v1 as g
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ADJACENT_180S
from competition.deepeye.tools.diagnostic.functional50_demo_four_cycle_profile_a import DEMO_FOUR_CYCLE
from competition.deepeye.integration import completion_interval as interval


class FreshActionControls(unittest.TestCase):
    def test_v3_public24_fits_fixed_wire_and_profile_keeps_exact_margin(self):
        path=Path(r'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.planning/deepeye-resume-20261018/gen4-functional-chain-offboard-20261030-07/demo30h-navigation-live-396/wire_size396.py')
        spec=importlib.util.spec_from_file_location('wire_size396_shape_only',path)
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        selected=NAV_ADJACENT_180S;result=helper.measure_size(selected.max_public_items)
        self.assertEqual(selected.max_public_items,24);self.assertIs(type(selected.exit_clearance_margin_m),float)
        self.assertEqual(selected.exit_clearance_margin_m,.05)
        self.assertTrue(result['all_fit']);self.assertLessEqual(result['maximum_payload_bytes'],16380)
        self.assertFalse(helper.measure_size(32)['all_fit'])
        with self.assertRaises(ValueError):replace(selected,max_public_items=32)
        print('NAV_V3_WIRE_SHAPE',json.dumps(result,sort_keys=True))

    def mapping(self,count,tick,phase,*,token=None,em=None):
        channel=getattr(self,'channel',None)
        if channel is None:
            self.channel=channel=object()
        if em is None:em=dict(kind='original_scoped_em_call_v1',source_origin_qpc_ns=1_000_000_000,
            tick_ms=tick,source_count=count)
        draft=dict(status='complete',source_count=count,tick_ms=tick,
            held_em_association=dict(original_em=em,held=False))
        token=token if token is not None else NS(_draft=draft,_ended=True)
        phase_ref=NS(phase_index=phase)
        return g._Mapping(channel,object(),{},dict(token=token,draft=draft,phase_receipt=phase_ref),
            dict(quality=7,source_time=dict(adc_tick_ms=tick,em_tick_ms=tick),
                 observation_identity=dict(capture_sha256='changed-json-id-'+str(phase))),
            b'SYNTHETIC_TEST',1_000_000_000+tick*1_000_000,object())

    def choose(self,previous,current,old,profile=NAV_ADJACENT_180S):
        helper=getattr(g,'_fresh_action_previous',None)
        self.assertIsNotNone(helper,'fresh private action decision is not implemented')
        return helper(previous,current,old,profile=profile,source_origin=1_000_000_000)

    @staticmethod
    def candidate():
        return interval.IntervalCandidate('model_candidate','ai_controller','control_broker',False,
            dict(target=dict(action=1,duration_ms=3000)),6_500_000_000,1_500_000_000,{})

    def test_new_private_sample_and_native_em_get_new_action_cap_without_mutating_old_bound(self):
        previous=NS(deadline_ns=2_000_000_000);old=self.mapping(1,0,2);new=self.mapping(2,1000,5)
        self.assertIsNone(self.choose(previous,new,old))
        finite=interval.adapt_action_candidate(self.candidate(),host_issue_ns=1_500_000_000,
            now_ns=1_500_000_000,previous_deadline_ns=None)
        self.assertEqual(finite.deadline_ns,4_500_000_000)
        self.assertEqual(previous.deadline_ns,2_000_000_000)

    def test_same_sample_renamed_and_held_native_em_cannot_renew(self):
        previous=NS(deadline_ns=2_000_000_000);old=self.mapping(1,0,2)
        same=self.mapping(2,1000,5,token=old.refs['token'])
        held=self.mapping(2,1000,6,em=old.refs['draft']['held_em_association']['original_em'])
        for changed in (same,held):
            self.assertIs(self.choose(previous,changed,old),previous)
            with self.assertRaises(interval.Unavailable):interval.adapt_action_candidate(self.candidate(),
                host_issue_ns=1_500_000_000,now_ns=1_500_000_000,previous_deadline_ns=previous.deadline_ns)

    def test_default_four_and_same_action_preserve_previous_min_and_reject_nonmonotone_refs(self):
        previous=NS(deadline_ns=2_000_000_000);old=self.mapping(1,0,2)
        for profile in (None,DEMO_FOUR_CYCLE):self.assertIs(self.choose(previous,None,None,profile),previous)
        self.assertIs(self.choose(previous,old,old),previous)
        backwards=self.mapping(2,1000,1)
        self.assertIs(self.choose(previous,backwards,old),previous)
        with self.assertRaises(interval.Unavailable):interval.adapt_action_candidate(self.candidate(),
            host_issue_ns=1_500_000_000,now_ns=1_500_000_000,previous_deadline_ns=previous.deadline_ns)


if __name__=='__main__':unittest.main()

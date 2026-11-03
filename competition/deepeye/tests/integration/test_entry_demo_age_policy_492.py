"""Explicit 8s demo isolation; original default/profile gates remain strict."""
import unittest
from competition.deepeye.simulation.authority.demo30h_ai_em3_profile_v2 import selected_profile,NAV_ENTRY_C0_V1,NAV_FAST_V1
from competition.deepeye.simulation.authority.g05_csr_channels_v1 import G05CsrPolicy


class EntryDemoAgePolicyControls(unittest.TestCase):
    def test_new_typed_profile_accepts_its_explicit_demo_budget(self):
        descriptor=selected_profile(8_000_000_000,navigation_profile=NAV_ENTRY_C0_V1)
        G05CsrPolicy(8_000_000_000,8_000_000_000,0,0,demo_ai_profile=descriptor).check()
        with self.assertRaises(ValueError):G05CsrPolicy(8_000_000_001,8_000_000_000,0,0,demo_ai_profile=descriptor).check()

    def test_original_nav_and_no_descriptor_cannot_inherit_new_budget(self):
        old=selected_profile(5_000_000_000,navigation_profile=NAV_FAST_V1)
        with self.assertRaises(ValueError):G05CsrPolicy(8_000_000_000,8_000_000_000,0,0,demo_ai_profile=old).check()
        with self.assertRaises(ValueError):G05CsrPolicy(8_000_000_000,8_000_000_000,0,0).check()


if __name__=='__main__':unittest.main()

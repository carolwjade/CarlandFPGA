"""Synthetic scheduling controls; not native sensor or authority evidence."""
from types import SimpleNamespace as NS
import unittest
from competition.deepeye.tools.diagnostic.original_chain_source_pump_a import OriginalChainSourcePump as Pump
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ADJACENT_180S as NAV


class NavigationPollingControls(unittest.TestCase):
    def pump(self):
        p=object.__new__(Pump);session=NS(_chain_reply_profile=NAV);calls=[]
        p._session=session;p._enabled=True;p._failed=False;p._ever_enabled=False;p._manual_navigation=None
        p._causal=NS(_navigation_profile=NAV);p._scanner=NS(_demo_cycle_profile=NAV)
        p._check=lambda *args,**kwargs:None
        p._source=NS(poll_sample=lambda:calls.append('actual_poll'))
        return p,session,calls

    def test_explicit_selection_does_not_sample_during_wait_but_root_poll_does(self):
        self.assertTrue(hasattr(Pump,'select_navigation_explicit_only'),'explicit navigation scheduler missing')
        p,session,calls=self.pump();p._enabled=False;p.select_navigation_explicit_only(NAV);p._enabled=True
        self.assertIsNone(p.poll_once(session));self.assertEqual(calls,[])
        self.assertIsNone(p.poll_once(session,explicit=True));self.assertEqual(calls,['actual_poll'])

    def test_default_automatic_polling_stays_enabled(self):
        p,session,calls=self.pump();p.poll_once(session);self.assertEqual(calls,['actual_poll'])

    def test_selector_requires_matching_profile_and_is_pre_enable_one_use(self):
        self.assertTrue(hasattr(Pump,'select_navigation_explicit_only'),'explicit navigation scheduler missing')
        p,_,_=self.pump()
        with self.assertRaises(ValueError):p.select_navigation_explicit_only(NAV)
        p._enabled=False;p.select_navigation_explicit_only(NAV)
        with self.assertRaises(ValueError):p.select_navigation_explicit_only(NAV)
        p,_,_=self.pump();p._enabled=False;p._scanner._demo_cycle_profile=None
        with self.assertRaises(ValueError):p.select_navigation_explicit_only(NAV)


if __name__=='__main__':unittest.main()

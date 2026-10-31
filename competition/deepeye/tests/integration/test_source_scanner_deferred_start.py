"""New pre-start source scanner controls; pure software substitutions."""
import unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.tests.integration import test_original_source_cycles as old
from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as scan, functional50_b131_loader as loader

class FreshFunctional(old.Functional):
 def __init__(self):
  super().__init__();self._start_attempted=False;self._pending=None;self.book._origin=None;self.book._state='NEW';self.source.state='NEW';self.source._clock=None;self.source._origin=None;self.source._last_tick=None;self.source._polling=False
 def start(self):
  self._start_attempted=True;origin=self.clock.now;self.source._origin=origin;self.source._clock=self.clock;self.source.state='RUNNING';self.book._origin=origin;self.book._state='RUNNING'

class DeferredControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.bundle=loader.load_selected(Path.cwd())
 def test_prestart_one_activation_and_origin_zero_admission(self):
  f=FreshFunctional()
  with patch.object(scan,'_check_bundle',wraps=scan._check_bundle) as verify:
   p=scan.OriginalSourceTraceScan(f,self.bundle,source_scan_cycle_v2=True,defer_start=True)
   self.assertEqual(verify.call_count,1);self.assertIsNone(p._origin);self.assertIsNone(p._ledger);self.assertFalse(p._activated)
   with self.assertRaises(ValueError):p.admit({})
   f.start();p.activate_started_source();self.assertEqual(verify.call_count,1)
   self.assertIs(p._book,f.book);self.assertEqual(p._origin,1000000000);self.assertTrue(p._activated)
   value=f.add(0);a=p.admit(value);self.assertEqual(a.record.adc_tick_ms,0);self.assertEqual(p._ledger.snapshot.accepted_records,1)
   with self.assertRaises(ValueError):p.activate_started_source()
   self.assertTrue(p._failed);self.assertEqual(p._ledger.snapshot.accepted_records,1)
 def test_premature_activation_is_terminal(self):
  f=FreshFunctional();p=scan.OriginalSourceTraceScan(f,self.bundle,source_scan_cycle_v2=True,defer_start=True)
  with self.assertRaises(ValueError):p.activate_started_source()
  self.assertTrue(p._failed);f.start()
  with self.assertRaises(ValueError):p.activate_started_source()
  self.assertIsNone(p._ledger)
 def test_no_implicit_or_sampled_prestart(self):
  f=FreshFunctional()
  with self.assertRaises(ValueError):scan.OriginalSourceTraceScan(f,self.bundle,defer_start=True)
  f.source._count=1
  with self.assertRaises(ValueError):scan.OriginalSourceTraceScan(f,self.bundle,source_scan_cycle_v2=True,defer_start=True)

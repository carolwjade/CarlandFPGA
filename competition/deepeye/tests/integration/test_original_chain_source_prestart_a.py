"""Synthetic new pre-start controls, not native or hardware evidence."""
import runpy, threading, unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
old=runpy.run_path(str(Path(__file__).with_name('test_original_chain_source_pump_a.py')))
Pump=old['OriginalChainSourcePump']; fixture_old=old['Tests'].fixture

class PrestartTests(unittest.TestCase):
 def fixture(self):
  with patch.object(Pump,'_check',lambda self,live:None):s,f,a,_=fixture_old(None)
  f._start_attempted=False;f.source.state='NEW';f.source._clock=None;f.source._origin=None;f.source._count=0;f.source._last_tick=None;f.source._polling=False;f._pending=None
  f.book=NS(_origin=None,_samples=[],_state='NEW',_clock=f.clock,_active=None);f._retained_samples=[];f.source._source_book=f.book;f.book._source=f.source
  a._book=f.book;a._defer_start=True;a._activated=False;a._activation_attempted=False;a._ledger=None;a._origin=None;a._failed=False;a._admitted=[];a._prepared=False;a._prepare_count=0
  f.entry['book']=f.book
  return s,f,a
 def test_prepared_start_enable_real_slot_zero(self):
  s,f,a=self.fixture();pump=Pump(s,f,a);self.assertFalse(pump.enabled);self.assertIsNone(pump.poll_once(s));self.assertEqual(f.calls,0)
  f._start_attempted=True;f.source.state='RUNNING';f.source._clock=f.clock;f.source._origin=10;f.book._origin=10;a._activated=True;a._activation_attempted=True;a._origin=10;a._ledger=object()
  pump.enable();self.assertIs(pump.poll_once(s),a.admission);self.assertIs(pump.history[0].payload,f.pair[0]);self.assertEqual(f.calls,1);self.assertEqual(f.releases,1)
 def test_refuse_unactivated_and_invalid_prestate(self):
  s,f,a=self.fixture();p=Pump(s,f,a)
  with self.assertRaises(ValueError):p.enable()
  self.assertTrue(p.failed);self.assertEqual(f.calls,0)
  s,f,a=self.fixture();a._ledger=object()
  with self.assertRaises(ValueError):Pump(s,f,a)
if __name__=='__main__':unittest.main()

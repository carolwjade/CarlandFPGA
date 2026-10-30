"""One new source-cycle intermediate-history control; software fixture only."""
import unittest
from pathlib import Path
from competition.deepeye.tests.integration import test_original_source_cycles as fixture
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader

class IntermediateHistory(unittest.TestCase):
 def test_full_intermediate_history_latest_and_missing_rejected(self):
  fixture.Controls.bundle=loader.load_selected(Path.cwd());helper=fixture.Controls('test_two_original_slots_one_ledger')
  f,p,first=helper.make();ledger=p._ledger;initial=p.prepare(first,facts=fixture.facts(0),build_binding=fixture.BINDING)
  p.admit(f.add(100));latest=f.add(110);p.admit(latest);final=p.prepare(latest,facts=fixture.facts(1),build_binding=fixture.BINDING)
  self.assertEqual((initial.status,final.status),('TRACE94_PLAN_PREPARED','TRACE94_PLAN_PREPARED'));self.assertIs(p._ledger,ledger);self.assertEqual(ledger.snapshot.accepted_records,12);self.assertEqual(p._last_prepared_index,11);self.assertEqual(len(p._attempts),2)
  f,p,first=helper.make();p.prepare(first,facts=fixture.facts(0),build_binding=fixture.BINDING);f.add(100);latest=f.add(110)
  with self.assertRaises(ValueError):p.admit(latest)
  self.assertTrue(p._failed);self.assertEqual(p._ledger.snapshot.accepted_records,10)

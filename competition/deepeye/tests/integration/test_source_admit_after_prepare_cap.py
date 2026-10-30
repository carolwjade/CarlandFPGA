"""One new post-cap admission control; synthetic source only."""
import unittest
from pathlib import Path
from competition.deepeye.tests.integration import test_original_source_cycles as fixture
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader

class AdmissionAfterCap(unittest.TestCase):
 def test_admit_survives_two_prepares_third_fails_closed(self):
  fixture.Controls.bundle=loader.load_selected(Path.cwd());helper=fixture.Controls('test_two_original_slots_one_ledger')
  f,p,first=helper.make();ledger=p._ledger;book=p._book;origin=p._origin
  p.prepare(first,facts=fixture.facts(0),build_binding=fixture.BINDING)
  second=f.add(100);p.admit(second);p.prepare(second,facts=fixture.facts(1),build_binding=fixture.BINDING)
  third=f.add(110);p.admit(third)
  self.assertIs(p._ledger,ledger);self.assertIs(p._book,book);self.assertEqual(p._origin,origin);self.assertEqual(p._ledger.snapshot.accepted_records,12);self.assertEqual(p._prepare_count,2);self.assertFalse(p._failed)
  with self.assertRaisesRegex(ValueError,'cap exhausted'):p.prepare(third,facts=fixture.facts(2),build_binding=fixture.BINDING)
  self.assertTrue(p._failed);self.assertEqual(p._prepare_count,2)
  with self.assertRaises(ValueError):p.admit(f.add(120))

"""New pure registry bracket checks; no actual Root or board claim."""
import unittest
from competition.deepeye.tools import run_causal_functional_chain as c
class Tests(unittest.TestCase):
 def test_stable_registry_identity(self):
  refs=(object(),object());snap=(refs,('state',1));c._check_registry_stable(snap,(refs,('state',1)))
 def test_changed_registry_rejected(self):
  refs=(object(),object())
  with self.assertRaises(ValueError):c._check_registry_stable((refs,('state',1)),((refs[0],object()),('state',1)))
  with self.assertRaises(ValueError):c._check_registry_stable((refs,('state',1)),(refs,('state',2)))
 def test_getter_outside_hold_rejected(self):
  current={'at_qpc_ns':11,'pose_read':{'begin_qpc_ns':10,'end_qpc_ns':11}}
  c._check_registry_interval(current,9,12)
  with self.assertRaises(ValueError):c._check_registry_interval(current,12,13)
  with self.assertRaises(ValueError):c._check_registry_interval(current,9,10)
if __name__=='__main__':unittest.main()

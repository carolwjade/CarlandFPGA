import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import functional50_board_trace_batch_a as batch

class DeadlineControl(unittest.TestCase):
 def test_persist_crosses_deadline_no_mmio(self):
  intent=dict(operation_id='op',call_id=1,kind='write',offset=0x80,value=1,label='ARM',poll=False,window='TRACE_HWH_RELATIVE',phase='work',reserve_and_persist_before_effect_bytes=2048,phase_deadline_ns=100)
  class Reducer:
   operation_id='op';limits={'work_evidence':20000}
   def __init__(self):self.observations=[]
   def advance(self,obs=None,*,phase_elapsed_ns):
    self.observations.append((obs,phase_elapsed_ns));return intent if obs is None else None
  class Port:
   _count=0
   def _call(self,*args):raise AssertionError('expired intent must not call port')
  r=Reducer();p=Port()
  with tempfile.TemporaryDirectory() as d, patch.object(batch.time,'monotonic_ns',side_effect=[99,100]):
   batch._drive(p,r,'work',0,Path(d),{'work':0})
   self.assertEqual(r.observations[-1][0]['status'],'not_attempted')
   self.assertEqual(r.observations[-1][1],100)
   self.assertEqual(p._count,0)
   data=(Path(d)/'intent-00001.bin').read_bytes()
   self.assertEqual(len(data),2048);self.assertIn(b'not_attempted',data[1024:])
if __name__=='__main__':unittest.main()

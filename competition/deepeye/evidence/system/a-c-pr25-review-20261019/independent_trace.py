"""Literal candidate wire boundaries; imports no B codec or encoder."""
import ast,binascii,importlib.util,sys,unittest
from pathlib import Path
P=Path(sys.argv.pop(1));T=P/'evidence/ai/trace_candidate_decode'
spec=importlib.util.spec_from_file_location('candidate_subject',T/'candidate_decode.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
WIRE=bytes.fromhex('a55a030717020900e803000001080401100403020107000000e803000000000000d204fe62')
BIND={'session':0x01020304,'config_epoch':2,'e':0}
def altered(*,seq=9,index=7,tick=1000,quality=4):
 b=bytearray(WIRE);b[6:8]=seq.to_bytes(2,'little');b[8:12]=(tick&0xffffffff).to_bytes(4,'little')
 b[14]=quality;b[21:25]=index.to_bytes(4,'little');b[25:33]=tick.to_bytes(8,'little')
 b[-2:]=binascii.crc_hqx(b[2:-2],0xffff).to_bytes(2,'little');return bytes(b)

class IndependentTrace(unittest.TestCase):
 def test_full_tick_rollover_is_distinct_from_wire_sequence_wrap(self):
  r=C.CandidateReceiver(BIND)
  r.accept(altered(seq=65534,index=1,tick=(1<<32)-1))
  out=r.accept(altered(seq=65535,index=2,tick=1<<32))
  self.assertEqual(out['points'][0]['tick_ms'],1<<32)
  before=r.state_snapshot()
  with self.assertRaises(C.Reject):r.accept(altered(seq=0,index=3,tick=(1<<32)+1))
  self.assertEqual(r.state_snapshot(),before)
 def test_duplicate_returns_no_points_and_does_not_refresh_cache_order(self):
  r=C.CandidateReceiver(BIND);r.accept(WIRE);r.accept(altered(seq=10,index=8,tick=1001))
  before=r.state_snapshot();out=r.accept(WIRE)
  self.assertEqual(out,{'status':'duplicate','sequence':9,'points':[]})
  self.assertEqual(r.state_snapshot(),before)
 def test_source_tick_low_mismatch_rejects_even_with_recomputed_crc(self):
  b=bytearray(WIRE);b[8:12]=(1001).to_bytes(4,'little');b[-2:]=binascii.crc_hqx(b[2:-2],0xffff).to_bytes(2,'little')
  r=C.CandidateReceiver(BIND);before=r.state_snapshot()
  with self.assertRaises(C.Reject):r.accept(bytes(b))
  self.assertEqual(r.state_snapshot(),before);self.assertEqual(r.accept(WIRE)['status'],'accepted')
 def test_import_closure_remains_source_independent(self):
  for file in ('candidate_decode.py','replay.py'):
   tree=ast.parse((T/file).read_text(encoding='utf-8'))
   imports={n.module if isinstance(n,ast.ImportFrom) else a.name for n in ast.walk(tree)
            if isinstance(n,(ast.ImportFrom,ast.Import)) for a in (n.names if isinstance(n,ast.Import) else [None])}
   self.assertLessEqual(imports,{'collections','copy','json','pathlib','candidate_decode'})
 def test_reference_production_wire_stays_closed_to_candidate_type7(self):
  path=P/'evidence/ai/motion_request/reference/integration/wire.py'
  spec=importlib.util.spec_from_file_location('closed_reference_wire',path);w=importlib.util.module_from_spec(spec)
  sys.modules[spec.name]=w;spec.loader.exec_module(w)
  self.assertNotIn(7,w.PAYLOAD_LENGTHS)
  with self.assertRaisesRegex(ValueError,'unfrozen'):w.decode(WIRE)
  self.assertEqual(C.decode_frame(WIRE,BIND)['points'][0]['value'],1234)

if __name__=='__main__':unittest.main(verbosity=2)

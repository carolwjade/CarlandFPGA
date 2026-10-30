import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import functional50_board_trace_batch_a as b
from competition.deepeye.tools.diagnostic import functional50_trace_batch_client_a as client

class Control(unittest.TestCase):
 def test_unknown_prefix_is_preserved_and_accepted(self):
  class Port:
   def __init__(self,d):self._dir=d;self._count=10;self._failed=False
  class Reducer:
   def __init__(self,plan):self.operation_id='op';self.generator=None
   def begin(self):pass
   def snapshot(self):return dict(completed=True,failed=True,outstanding_intent=None,arm_attempt_owned=True,unknown_effects=True,collect_consumed=True,confirmed_wire_prefix=b'\x00\x99',results=[],errors=['BUDGET'],quiescent=False)
  plan=SimpleNamespace(facts=lambda:{'lineage':{'operation_id':'op','build_id_hex128':'1'*32}})
  bundle=SimpleNamespace(adapter=SimpleNamespace(prepare_bytes=lambda *a,**k:SimpleNamespace(status='TRACE94_PLAN_PREPARED',plan=plan)),reducer=SimpleNamespace(Reducer=Reducer))
  req=dict(schema='trace_batch_v1',id='id',operation_id='op',request_hex=b'r'.hex(),source_hex=b's'.hex(),companions_hex=[b'a'.hex(),b'b'.hex(),b'c'.hex(),b'd'.hex()],build_binding=dict(canonical_build_id_full_sha256='1'*64,source_closure_file_sha256='2'*64,operation_id='op',request_hash='3'*64))
  with tempfile.TemporaryDirectory() as d,patch.object(b,'_drive',return_value=None):
   root=Path(d);port=Port(root);wire=b.run_batch(port,bundle,b.raw(req)+b'\n',SimpleNamespace(_TracePort=Port),dict(operation_id='op',build_id='1'*32))
   value=json.loads(wire);self.assertEqual(value['status'],'UNKNOWN');self.assertEqual(value['terminal'],'UNKNOWN');self.assertTrue(value['unknown']);self.assertEqual(value['raw_wire_hex'],'0099')
   parsed,body=client._response(wire,'id','op',b.digest(b'r'),'3'*64);self.assertEqual(body,b'\x00\x99');self.assertFalse(parsed['wire_complete'])
if __name__=='__main__':unittest.main()

"""New batch-only software boundary controls; no board/native/SSH."""
import json,unittest
from competition.deepeye.tools.diagnostic import functional50_board_trace_batch_a as board
class Tests(unittest.TestCase):
 def test_nonhex_and_shape_refused(self):
  for x in ({'schema':'trace_batch_v1'}, {'schema':'trace_batch_v1','id':'a','operation_id':'op','request_hex':'zz','source_hex':'00','companions_hex':['00']*4,'build_binding':{}}):
   with self.assertRaises(ValueError):board.decode_batch_request(board.raw(x)+b'\n')
 def test_exact_bytes_bounded(self):
  x={'schema':'trace_batch_v1','id':'a','operation_id':'op','request_hex':'7b7d','source_hex':'00','companions_hex':['00']*4,'build_binding':{'canonical_build_id_full_sha256':'a'*64,'source_closure_file_sha256':'b'*64,'operation_id':'op','request_hash':'c'*64}}
  data=board.decode_batch_request(board.raw(x)+b'\n');self.assertEqual(data[0],b'{}');self.assertEqual(data[1],b'\x00');self.assertEqual(data[2],(b'\x00',)*4)
  x['companions_hex'][0]='00'*(262144+1)
  with self.assertRaises(ValueError):board.decode_batch_request(board.raw(x)+b'\n')
 def test_manifest_requires_exact_fixed_file_set(self):
  with self.assertRaises(ValueError):board.verify_manifest_structure({'schema':'trace_batch_manifest_v1','files':{}})
  import tempfile
  from pathlib import Path
  from competition.deepeye.tools.diagnostic.functional50_ssh_a import SessionSpec,_remote_command
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for name in board.FILES:
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
   manifest=board.verify_manifest_structure(json.loads(board.make_manifest_bytes(root)))
   self.assertEqual(set(manifest['files']),board.FILES)
  spec=SessionSpec((),'/usr/local/share/pynq-venv/bin/python3','/tmp/functional50_board_a.py','/tmp/plan.json','C:/unused','a'*64,'C:/unused','op')
  self.assertNotIn('trace-batch-manifest',_remote_command(spec))
  batch=SessionSpec((),spec.remote_python,'/tmp/functional50_board_trace_batch_a.py',spec.remote_plan,spec.local_script,spec.local_script_sha256,spec.evidence_parent,spec.operation_id,'trace_batch_v1','/tmp/trace-batch-manifest.json','b'*64)
  self.assertIn('/tmp/trace-batch-manifest.json',_remote_command(batch))
 def test_full_original_reducer_with_synthetic_port(self):
  import tempfile,struct,binascii
  from pathlib import Path
  from types import SimpleNamespace
  from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader
  from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as source
  from competition.deepeye.tools.diagnostic import functional50_trace_batch_client_a as client
  from competition.deepeye.tools.diagnostic import functional50_exchange_a as old_exchange
  self.assertIs(loader._Bundle,old_exchange._Bundle);self.assertIs(loader.load_selected,old_exchange.load_selected)
  bundle=loader.load_selected(Path.cwd())
  lineage=dict(operation_id='fixture',request_id='fixture-request',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='fixture-boot',session_id=4,tag=5,trigger_id=6,generation=1,request_seq=7,capture_seq=8)
  facts=dict(work_id='fixture-work',declared_by='synthetic-test',scan_id_uint63=1,view=2,frame_seq_start=5,sample_index=8,binding_receipt_id='fixture-bind',lineage=lineage)
  binding=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='fixture',request_hash='a'*64)
  payload=dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=90,em_tick_ms=None,channel_values=[None,None,None,.1],channel_counts=[None,None,None,205],quality=4104)
  draft=dict(status='complete',tick_ms=90,source_count=10,finish_qpc_ns=1090000001,adc={'begin_qpc_ns':1090000000,'end_qpc_ns':1090000001})
  request,src,companions=source._construct_bytes(payload,source._raw(payload),draft,1000000000,'a'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST')
  prepared=bundle.adapter.prepare_bytes(request,src,companions,build_binding=binding);self.assertEqual(prepared.status,'TRACE94_PLAN_PREPARED')
  lanes=prepared.plan.facts()['scan']['lanes'];frames=[]
  for lane in lanes:
   point=dict(index=lane['index'],tick_ms=lane['acquisition_tick_us'],source_tick_ms=lane['source_tick_us'],value=lane['raw_sample_uint16'],**lane['mapped_flags'])
   wire=bytearray(bundle.adapter.codec.encode_frame([point],dict(session=lane['session'],config_epoch=lane['view'],e=0),lane['channel'],lane['frame_seq']))
   wire[3]=0xe4;wire[12]=2;wire[-2:]=struct.pack('<H',binascii.crc_hqx(wire[2:-2],0xffff));frames.append(bytes(wire))
  class FakePort:
   def __init__(self,path):self._dir=path;self._count=10;self._failed=False;self.state=0;self.push=0;self.assoc=0;self.tag=0;self.current=-1;self.pos=0;self.fifo=b''.join(frames)
   def _call(self,kind,offset,value,request_id):
    self._count+=1;n=self._count;(self._dir/f'io-{n:05d}-started.json').write_text('{}')
    out=None
    if kind=='write':
     if offset==0x100:self.tag=value
     if offset==0x80:
      if value==1:self.state=3
      elif value==2:
       self.push+=1
       if self.push==4:self.state=4
      elif value==3:self.current+=1;self.state=7
      elif value==4:self.assoc+=1;self.state=9 if self.assoc==4 else 4
      elif value==5:self.state=0
      elif value==8:self.pos+=1
    else:
     identity={0:0x54353046,4:1,8:4,12:50000000,16:1000000,20:4096}
     if offset in identity:out=identity[offset]
     elif 0x60<=offset<=0x6c:out=(int('c'*32,16)>>(32*((offset-0x60)//4)))&0xffffffff
     elif offset==0x18:out=self.state
     elif offset==0x20:out=0x10 if self.state==7 else (0x22 if self.state==0 else 2)
     elif offset in (0x1c,0x34,0x44,0x4c):out=0
     elif offset==0x2c:out=self.tag
     elif offset==0x24:out=self.push
     elif offset==0x28:out=self.assoc
     elif offset==0x40:out=self.current+1
     elif offset==0x48:out=len(frames[self.current])
     elif offset==0x50:out=sum(map(len,frames[:self.current]))
     elif offset==0x7c:out=sum(map(len,frames[:self.current+1]))
     elif offset==0x30:out=0 if self.state==0 and self.pos==0 else len(self.fifo)-self.pos
     elif offset==0x38:out=self.pos
     elif offset==0x70:out=0x100+self.fifo[self.pos]
     else:raise AssertionError(hex(offset))
    (self._dir/f'io-{n:05d}-returned.json').write_text('{}');return out
  packet=dict(schema='trace_batch_v1',id='req',operation_id='fixture',request_hex=request.hex(),source_hex=src.hex(),companions_hex=[x.hex() for x in companions],build_binding=binding)
  with tempfile.TemporaryDirectory() as tmp:
   port=FakePort(Path(tmp));response=board.run_batch(port,bundle,board.raw(packet)+b'\n',SimpleNamespace(_TracePort=FakePort),dict(operation_id='fixture',build_id='c'*32))
   doc,wire=client._response(response,'req','fixture',board.digest(request),'a'*64)
   self.assertEqual(doc['status'],'COMPLETE');self.assertEqual(doc['terminal'],'QUIESCENT');self.assertEqual(wire,b''.join(frames))
   verified=bundle.adapter.correlate_collected(prepared.plan,wire,companions,doc['results']);self.assertEqual(verified['status'],'FOUR_FRAME_CORRELATION_CONSISTENT',verified.get('reason'))
   from unittest.mock import patch
   from competition.deepeye.tools.diagnostic.functional50_ssh_a import Session
   from competition.deepeye.integration.host_clock import QpcHostClock
   session=object.__new__(Session);session._protocol='trace_batch_v1';session._batch_consumed=False;session._unknown=False;session._dir=Path(tmp)/'fixture';session._dir.mkdir();session._check=lambda:None;session._call=lambda actual,timeout:response
   clock=object.__new__(QpcHostClock);session._clock=clock
   with patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    client_session=client.BatchSession(session,bundle,clock);out=client_session.exchange('req',prepared,build_binding=binding,timeout_ns=1)
   self.assertEqual((out['lower_qpc_ns'],out['upper_qpc_ns']),(10,20));self.assertEqual(out['correlation']['status'],'FOUR_FRAME_CORRELATION_CONSISTENT')
   with self.assertRaises(ValueError):client_session.exchange('req',prepared,build_binding=binding,timeout_ns=1)
  class UncertainPort(FakePort):
   def _call(self,kind,offset,value,request_id):
    self._count+=1;self._failed=True;raise OSError('synthetic effect unknown')
  with tempfile.TemporaryDirectory() as tmp:
   port=UncertainPort(Path(tmp));response=board.run_batch(port,bundle,board.raw(packet)+b'\n',SimpleNamespace(_TracePort=UncertainPort),dict(operation_id='fixture',build_id='c'*32))
   doc,wire=client._response(response,'req','fixture',board.digest(request),'a'*64)
   self.assertEqual(doc['status'],'UNKNOWN');self.assertTrue(doc['unknown']);self.assertFalse(doc['wire_complete']);self.assertEqual(port._count,11)
if __name__=='__main__':unittest.main()

"""Single new joint software control; all source, pipe and MMIO synthetic."""
import unittest,tempfile,threading,types,io,time,json,struct,binascii
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.tests.integration import test_original_chain_receipt_producer_a as fixtures
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader, original_source_trace_scan_a as scan, original_chain_receipt_producer_a as prod, original_chain_source_pump_a as pm, functional50_ssh_a as ssh, functional50_chain_v2_client_a as client, functional50_board_trace_batch_a as batch
from competition.deepeye.integration.host_clock import QpcHostClock

class Positive(unittest.TestCase):
 def test_real_fixed_b131_and_selected_client_producer_joint(self):
  helper=fixtures.Tests();self.addCleanup(helper.doCleanups)
  with tempfile.TemporaryDirectory(dir=OUT) as tmp:
   world,source,oldbundle,scanner,s,chain,clock=helper.fixture(tmp);bundle=loader.load_selected(Path.cwd());chain.bundle=bundle;scanner._bundle=bundle
   s._threads=[];s._proc.stdin=io.BytesIO()
   op='op'; line=dict(operation_id=op,request_id='new-252-source',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='new-252-boot',session_id=24,tag=25,trigger_id=26,generation=1,request_seq=27,capture_seq=28)
   facts=dict(work_id='new-252-work',declared_by='synthetic-252',scan_id_uint63=1,view=2,frame_seq_start=5,sample_index=8,binding_receipt_id='new-252-bind',lineage=line);binding=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id=op,request_hash='a'*64)
   payload=dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=90,em_tick_ms=None,channel_values=[None,None,None,.1],channel_counts=[None,None,None,205],quality=4104)
   draft=dict(status='complete',tick_ms=90,source_count=10,finish_qpc_ns=1090000001,adc={'begin_qpc_ns':1090000000,'end_qpc_ns':1090000001})
   request,src,companions=scan._construct_bytes(payload,scan._raw(payload),draft,1000000000,'f'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST');prepared=bundle.adapter.prepare_bytes(request,src,companions,build_binding=binding);self.assertEqual(prepared.status,'TRACE94_PLAN_PREPARED')
   frames=[]
   for lane in prepared.plan.facts()['scan']['lanes']:
    point=dict(index=lane['index'],tick_ms=lane['acquisition_tick_us'],source_tick_ms=lane['source_tick_us'],value=lane['raw_sample_uint16'],**lane['mapped_flags']);wire=bytearray(bundle.adapter.codec.encode_frame([point],dict(session=lane['session'],config_epoch=lane['view'],e=0),lane['channel'],lane['frame_seq']));wire[3]=0xe4;wire[12]=2;wire[-2:]=struct.pack('<H',binascii.crc_hqx(wire[2:-2],0xffff));frames.append(bytes(wire))
   class Port:
    def __init__(self,path):self._dir=path;self._count=10;self._failed=False;self.state=0;self.push=0;self.assoc=0;self.tag=0;self.current=-1;self.pos=0;self.fifo=b''.join(frames)
    def _call(self,kind,offset,value,request_id):
     self._count+=1;n=self._count;(self._dir/f'io-{n:05d}-started.json').write_text('{}');out=None
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
   port=Port(Path(tmp));packet=dict(schema='trace_batch_v1',id='scan-252',operation_id=op,request_hex=request.hex(),source_hex=src.hex(),companions_hex=[v.hex() for v in companions],build_binding=binding)
   nested=json.loads(batch.run_batch(port,bundle,batch.raw(packet)+b'\n',types.SimpleNamespace(_TracePort=Port),dict(operation_id=op,build_id='c'*32)))
   self.assertEqual(nested['status'],'COMPLETE');self.assertEqual(nested['terminal'],'QUIESCENT')
   result=dict(schema='trace_cycle_v2',index=1,request_sha256=batch.digest(request),source_sha256=batch.digest(src),response=nested,phase_io_first=11,phase_io_last=port._count,correlation_status='FOUR_FRAME_CORRELATION_CONSISTENT',directory='/synthetic/252',evidence_manifest_sha256='e'*64,authority='not_evaluated')
   response=(json.dumps(dict(schema='functional50_chain_v2',id='scan-252',operation_id=op,kind='trace_scan',status='COMPLETE',result=result,error=None,unknown=False))+'\n').encode()
   class Reader:
    def readline(self,n):return response
   s._proc.stdout=Reader();origin=list(ssh._SESSION_ORIGINS[s]);origin[7]=s._proc.stdin;origin[8]=s._proc.stdout;ssh._SESSION_ORIGINS[s]=tuple(origin);old=client._CHAIN_BINDINGS[chain];client._CHAIN_BINDINGS[chain]=(old[0],old[1],bundle,old[3],old[4],ssh._SESSION_ORIGINS[s])
   chain.select_owner_work_v1();pump=object.__new__(pm.OriginalChainSourcePump);pump._session=s;pump._source=source;pump._scanner=scanner;pump._clock=clock;pump._enabled=True;pump._failed=False;pump._history=[];pump._pending=None;s._source_pump=pump
   producer=prod.OriginalChainReceiptProducer(world,chain,scanner);producer._source_pump=pump;chain.sequence.initialized=True;chain.sequence.max_commands=2
   token=types.SimpleNamespace(_draft=draft,_handle=object(),_em_handle=None);item=dict(entry={'payload':payload},token=token,draft=draft,admission=object(),payload_bytes=scan._raw(payload),received=1090000001);scanner._admitted.append(item);producer._admission_count=1
   deadline=time.monotonic_ns()+10_000_000_000
   def prepare(sc,v,**kw):sc._result=prepared;return prepared
   with patch.dict(ssh._SESSION_PUMPS,{s:pump}),patch.object(QpcHostClock,'__call__',lambda _:time.monotonic_ns()),patch.object(pm.OriginalChainSourcePump,'_check',lambda *a:None),patch.object(pm.OriginalChainSourcePump,'poll_once',lambda *a:None),patch.object(scan.OriginalSourceTraceScan,'prepare_with_pump',prepare),patch.object(scan.OriginalSourceTraceScan,'_prepared_work_deadline',lambda *a:deadline),patch.object(scan.OriginalSourceTraceScan,'_check_prepared_dispatch',lambda *a:deadline):
    ev=producer.scan_actual('scan-252',payload,facts=facts,build_binding=binding,max_io=2000,timeout_ns=5_000_000_000);out,refs=prod.consume_original_receipt(ev)
   self.assertEqual(out['correlation']['status'],'FOUR_FRAME_CORRELATION_CONSISTENT');self.assertIs(refs['phase_receipt'],chain.phase_receipts[0]);self.assertIs(refs['token'],token);self.assertEqual(len(chain.sequence.ids),1);self.assertEqual(len(frames),4);self.assertFalse(s._unknown)
   print(json.dumps(dict(source='synthetic',frame_lengths=list(map(len,frames)),wire_bytes=sum(map(len,frames)),io_count=port._count-10,correlation=out['correlation']['status'],phase_index=refs['phase_receipt'].phase_index,packet_bytes=len(s._proc.stdin.getvalue()),cleanup=nested['cleanup_observed'],selected_client_work='real',scanner_248='fixture substituted; not covered')))

if __name__=='__main__':
 import os
 OUT=Path(os.environ['A252_EVIDENCE']);ids=['__main__.Positive.test_real_fixed_b131_and_selected_client_producer_joint'];print('selected_test_ids:',*ids,flush=True);r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(ids));raise SystemExit(not r.wasSuccessful())

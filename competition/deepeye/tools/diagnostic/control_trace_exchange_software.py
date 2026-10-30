"""NEW synthetic full B131 -> A exchange -> original Session software control."""
import binascii,hashlib,io,json,struct,tempfile,unittest,os
from contextlib import nullcontext
from pathlib import Path
from competition.deepeye.tools.diagnostic import functional50_exchange_a as ex
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh
from competition.deepeye.integration.host_clock import qpc_clock_for_new_run

class Transcript:
 def __init__(self,plan,codec):
  self.plan=plan;self.codec=codec;self.frames=[];self.stage={};self.state=0;self.push=0;self.assoc=0;self.fifo=[];self.pop=0;self.rid=9;self.tag=0;self.rx=19;self.row=None;self.commands=[];self.offsets=[]
  for lane in plan._scan['lanes']:
   point=dict(index=lane['index'],tick_ms=lane['acquisition_tick_us'],value=lane['raw_sample_uint16'],source_tick_ms=lane['source_tick_us'],**lane['mapped_flags'])
   p=codec.encode_payload([point],dict(session=lane['session'],config_epoch=lane['view'],e=0),lane['channel']);p=bytes([2])+p[1:]
   head=struct.pack('<2sBBBBHI',b'\xa5\x5a',3,0xe4,len(p),lane['view'],lane['frame_seq'],lane['acquisition_tick_us'])
   self.frames.append(head+p+struct.pack('<H',binascii.crc_hqx(head[2:]+p,0xffff)))
 def answer(self,q):
  off=q['offset'];v=q['value'];self.offsets.append((q['kind'],off))
  if q['kind']=='write':
   if off!=0x80:self.stage[off]=v
   else:
    self.commands.append(v)
    if v==1:self.state=3;self.tag=self.stage[0x100]
    elif v==2:self.push+=1;self.state=4 if self.push==4 else 3
    elif v==3:
     f=self.frames[self.assoc];self.fifo.extend(f);self.rid+=1;self.row=dict(id=self.rid,bytes=len(f),rx_before=self.rx,rx_end=self.rx+len(f));self.rx+=len(f);self.state=7
    elif v==4:self.assoc+=1;self.state=9 if self.assoc==4 else 4
    elif v==5:self.state=0
    elif v==8:self.fifo.pop(0);self.pop+=1
    else:raise AssertionError('unexpected command')
   return None
  constants={0:0x54353046,4:1,8:4,12:50000000,16:1000000,20:4096}
  if off in constants:return constants[off]
  if 0x60<=off<=0x6c:return (int(self.plan._lineage['build_id_hex128'],16)>>(8*(off-0x60)))&0xffffffff
  status=2|(0x20 if not self.fifo else 0)|(0x10 if self.state==7 else 0)
  values={0x18:self.state,0x1c:0,0x20:status,0x24:self.push,0x28:self.assoc,0x2c:self.tag,0x30:len(self.fifo),0x34:self.rx,0x38:self.pop,0x40:self.rid,0x70:0x100|self.fifo[0] if self.fifo else 0}
  if self.row:values.update({0x44:0,0x48:self.row['bytes'],0x4c:0,0x50:self.row['rx_before'],0x7c:self.row['rx_end']})
  return values[off]

class FakePipe:
 def __init__(self,transcript):self.transcript=transcript;self.pending=b''
 def write(self,raw):
  q=json.loads(raw);v=self.transcript.answer(q);self.pending=(json.dumps(dict(id=q['id'],returned=v))+'\n').encode();return len(raw)
 def flush(self):pass
 def readline(self,n):data=self.pending;self.pending=b'';return data
class FakeProcess:
 def __init__(self,t):self.pipe=FakePipe(t);self.stdin=self.stdout=self.pipe;self.stderr=io.BytesIO()
 def poll(self):return None

def original():
 h=lambda x:hashlib.sha256(x).hexdigest();source=b'new control source\x00';comps=(b'opaque-a',b'opaque-b\x00',b'opaque-c',b'opaque-d')
 lanes=[dict(channel=i,raw_sample_uint16=(i if i!=2 else None),root_quality_uint16=100+i,mapped_flags=dict(valid=i!=2,saturated=False,held=False,source_fault=i==2),staged_quality_uint4=1 if i!=2 else 8,acquisition_qpc_ns=1000,acquisition_tick_us=1,acquisition_remainder_ns=0,source_qpc_ns=1000 if i!=2 else None,source_tick_us=1 if i!=2 else None,source_remainder_ns=0 if i!=2 else None,session=1,index=i,view=1,frame_seq=i+1) for i in range(4)]
 req=dict(schema='B113_EXTERNAL_ORIGINAL_SCAN_REQUEST_V1',task=dict(task_id='DEEPEYE-IMPLEMENTATION-20261014',task_version=1,work_id='new186',requirements_sha256='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'),source_provenance={'class':'SYNTHETIC_TEST','declared_by':'control186','source_note':'synthetic only','mapping_state':'B_NEUTRAL_AWAITING_A_MAPPING'},source_payload=dict(format_label='test',bytes=len(source),sha256=h(source)),scan=dict(scan_id_uint63=1,origin_qpc_ns=0,acquisition_qpc_ns=1000,clock_domain_id='clock',lanes=lanes),lineage=dict(operation_id='op186',request_id='req',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='boot',session_id=1,tag=1,trigger_id=1,generation=1,request_seq=1,capture_seq=1),association=dict(profile_id='TRACE-PAYLOAD-1US-PRIVATE-v2',binding_receipt_id='binding',e=0,source_context_sha256='d'*64,timestamp_record_sha256='e'*64,quality_record_sha256='f'*64,receiver_qpc_ns=1000,evaluation_now_qpc_ns=1000,evaluation_clock_id='clock',receiver_clock_id='clock',freshness_limit_ns=100000000),companions=[dict(channel=i,format_label='opaque',bytes=len(v),sha256=h(v)) for i,v in enumerate(comps)])
 return json.dumps(req,separators=(',',':')).encode(),source,comps,dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='op186',request_hash='a'*64)

class FullTest(unittest.TestCase):
 def test_full(self):
  b=ex.load_selected(Path.cwd());raw,source,comps,binding=original();p=b.adapter.prepare_bytes(raw,source,comps,build_binding=binding);self.assertIsNotNone(p.plan)
  # Pure software functional control only: synthetic monotonic clock, not latency evidence.
  import itertools
  from unittest.mock import patch
  t=Transcript(p.plan,b.adapter.codec);clock=qpc_clock_for_new_run()
  leaf=patch('competition.deepeye.integration.host_clock._qpc_leaf',side_effect=itertools.count(1_000_000,1000));leaf.start();self.addCleanup(leaf.stop)
  base=Path(os.environ['A186_CONTROL_DIR']);base.mkdir(exist_ok=False)
  with nullcontext(str(base)) as tmp:
   root=Path(tmp)/'op186';root.mkdir();session=ssh.Session(ssh._SESSION_KEY,FakeProcess(t),clock,root)
   x=ex.Exchange(b,session,clock,raw,source,comps,build_binding=binding,timeout_ns=1_000_000_000)
   scan=x.scan();self.assertTrue(scan['completed']);self.assertFalse(scan['failed'])
   result=x.collect();self.assertEqual(result.get('status'),'FOUR_FRAME_CORRELATION_CONSISTENT',str(result.get('errors')));self.assertEqual(result['retained']['wire'],b''.join(t.frames));self.assertEqual(result['retained']['companions'],comps)
   clean=x.cleanup();self.assertTrue(clean['quiescent']);self.assertEqual(t.commands.count(1),1);self.assertEqual(t.commands.count(5),1)
   self.assertEqual([t.commands.count(v) for v in (2,3,4)],[4,4,4]);self.assertLessEqual(session._quota.count,5000)
   self.assertTrue(all(offset in (ssh.validate_io(kind,offset,0 if kind=='write' else None)[1],) for kind,offset in t.offsets if not (kind=='write' and offset==0x80)))
   self.assertEqual((x.directory/'source.bin').read_bytes(),source)
   for i,c in enumerate(comps):self.assertEqual((x.directory/f'companion-{i}.bin').read_bytes(),c)
   (base/'summary.json').write_text(json.dumps(dict(scope='SYNTHETIC_CLOCK_NO_BOARD',commands=t.commands,counts=session._quota.count,wire_hex=result['retained']['wire'].hex(),companions_hex=[c.hex() for c in comps],status=result['status'],quiescent=clean['quiescent'],phase_elapsed=clean['time_observations']),sort_keys=True),encoding='utf8')
if __name__=='__main__':unittest.main()

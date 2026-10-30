import unittest
from competition.deepeye.tools.diagnostic import functional50_exchange_a as m

class Tests(unittest.TestCase):
 def test_observation_exact(self):
  i={'operation_id':'op','call_id':1,'kind':'read'}
  self.assertEqual(m._observation(i,'confirmed_read',0)['value'],0)
  self.assertEqual(m._observation(i,'unknown',None)['status'],'unknown')
  with self.assertRaises(ValueError):m._observation(i,'confirmed_read',True)
  with self.assertRaises(ValueError):m._observation(i,'confirmed_write',None)
 def test_bounded_intent(self):
  i={'operation_id':'op','call_id':1,'kind':'read','offset':0,'value':None,'label':'identity','poll':False,'window':'TRACE_HWH_RELATIVE','phase':'work','reserve_and_persist_before_effect_bytes':2048,'phase_deadline_ns':100}
  m._validate_intent(i,'op')
  for field,value in [('window','G05'),('call_id',True),('offset',3),('reserve_and_persist_before_effect_bytes',0)]:
   x=dict(i);x[field]=value
   with self.assertRaises(ValueError):m._validate_intent(x,'op')
 def test_unknown_call_is_not_replayed(self):
  import tempfile
  from pathlib import Path
  from types import SimpleNamespace
  i={'operation_id':'op','call_id':1,'kind':'write','offset':128,'value':1,'label':'arm','poll':False,'window':'TRACE_HWH_RELATIVE','phase':'work','reserve_and_persist_before_effect_bytes':2048,'phase_deadline_ns':100}
  class Reducer:
   operation_id='op';limits={'work_evidence':100000}
   def __init__(self):self.calls=[]
   def advance(self,obs=None,*,phase_elapsed_ns):self.calls.append(obs);return i if obs is None else None
  class Session:
   def __init__(self):self.calls=0
   def request(self,*a,**kw):self.calls+=1;raise TimeoutError('unknown')
  with tempfile.TemporaryDirectory() as d:
   x=object.__new__(m.Exchange);x.reducer=Reducer();x.session=Session();x.directory=Path(d);x._used={'work':0};x.timeout_ns=10;x.failed=False;x._elapsed=lambda phase:1
   with self.assertRaises(TimeoutError):x._drive('work')
   self.assertTrue(x.failed);self.assertEqual(x.session.calls,1);self.assertEqual(x.reducer.calls[-1]['status'],'unknown')
   self.assertEqual((x.directory/'intent-00001.bin').stat().st_size,2048)
 def test_actual_b131_to_session_boundary(self):
  import hashlib,json,tempfile,io
  from unittest.mock import patch
  from pathlib import Path
  from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh
  from competition.deepeye.integration.host_clock import qpc_clock_for_new_run
  b=m.load_selected(Path.cwd());source=b'new synthetic source';companions=(b'a',b'b',b'c',b'd');h=lambda x:hashlib.sha256(x).hexdigest()
  lanes=[dict(channel=i,raw_sample_uint16=i,root_quality_uint16=0,mapped_flags=dict(valid=True,saturated=False,held=False,source_fault=False),staged_quality_uint4=1,acquisition_qpc_ns=1000,acquisition_tick_us=1,acquisition_remainder_ns=0,source_qpc_ns=1000,source_tick_us=1,source_remainder_ns=0,session=1,index=i,view=1,frame_seq=i+1) for i in range(4)]
  request=dict(schema='B113_EXTERNAL_ORIGINAL_SCAN_REQUEST_V1',task=dict(task_id='DEEPEYE-IMPLEMENTATION-20261014',task_version=1,work_id='new-control',requirements_sha256='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'),source_provenance={'class':'SYNTHETIC_TEST','declared_by':'control','source_note':'','mapping_state':'B_NEUTRAL_AWAITING_A_MAPPING'},source_payload=dict(format_label='test',bytes=len(source),sha256=h(source)),scan=dict(scan_id_uint63=1,origin_qpc_ns=0,acquisition_qpc_ns=1000,clock_domain_id='clock',lanes=lanes),lineage=dict(operation_id='op',request_id='req',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='boot',session_id=1,tag=1,trigger_id=1,generation=1,request_seq=1,capture_seq=1),association=dict(profile_id='TRACE-PAYLOAD-1US-PRIVATE-v2',binding_receipt_id='binding',e=0,source_context_sha256='d'*64,timestamp_record_sha256='e'*64,quality_record_sha256='f'*64,receiver_qpc_ns=1000,evaluation_now_qpc_ns=1000,evaluation_clock_id='clock',receiver_clock_id='clock',freshness_limit_ns=100000000),companions=[dict(channel=i,format_label='opaque',bytes=len(v),sha256=h(v)) for i,v in enumerate(companions)])
  raw=json.dumps(request,separators=(',',':')).encode();binding=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='op',request_hash='a'*64)
  class Proc:
   def __init__(self):self.stdin=io.BytesIO();self.stdout=io.BytesIO(b'{"id":"b131-00001","returned":0}\n');self.stderr=io.BytesIO()
   def poll(self):return None
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'op';path.mkdir();clock=qpc_clock_for_new_run();session=ssh.Session(ssh._SESSION_KEY,Proc(),clock,path)
   # Software-only seam: do not weaken the real TRACE port whitelist.
   with patch.object(m,'_preflight_trace_compatibility',return_value=None):
    x=m.Exchange(b,session,clock,raw,source,companions,build_binding=binding,timeout_ns=1_000_000_000)
   self.assertEqual(x.prepared.status,'TRACE94_PLAN_PREPARED')
   snap=x.scan();self.assertTrue(snap['failed']);self.assertEqual(snap['counters']['csr'],1);self.assertEqual(session._quota.count,1)
   self.assertEqual((x.directory/'source.bin').read_bytes(),source)
   self.assertFalse(snap['arm_attempt_owned'])
 def test_current_port_offset_contract(self):
  from competition.deepeye.tools.diagnostic.functional50_board_a import READS
  if 0x34 in READS:m._preflight_trace_compatibility()
  else:
   with self.assertRaises(ValueError):m._preflight_trace_compatibility()
 def test_no_fabricated_error_effect(self):
  i={'operation_id':'op','call_id':9,'kind':'write'}
  self.assertEqual(m._observation(i,'unknown',None)['value'],None)
  with self.assertRaises(ValueError):m._observation(i,'confirmed_write',3)
if __name__=='__main__':unittest.main()

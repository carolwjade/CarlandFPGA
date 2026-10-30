"""Software-only controls for the chain host; no board or SSH."""
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader
from competition.deepeye.integration.host_clock import QpcHostClock

class Tests(unittest.TestCase):
 def test_fixed_entry_and_legacy_reply_bound(self):
  s=ssh.SessionSpec((),'/usr/local/share/pynq-venv/bin/python3','/tmp/functional50_chain_board_a.py','/tmp/plan','C:/unused','a'*64,'C:/unused','op','functional50_chain_v1','/tmp/chain-board-manifest.json','b'*64,'/tmp/g05-policy.json')
  self.assertIn('/tmp/g05-policy.json',ssh._remote_command(s))
  with self.assertRaises(ValueError):ssh._parse_response(b' '+b' '*4096+b'\n',None,'ready')
 def test_original_session_two_one_use_operations_and_unknown(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_client_a as chain
  with tempfile.TemporaryDirectory() as tmp:
   s=object.__new__(ssh.Session);s._protocol='functional50_chain_v1';s._unknown=False;s._dir=Path(tmp)/'op';s._dir.mkdir();s._check=lambda:None
   c=object.__new__(QpcHostClock);s._clock=c
   b=object.__new__(loader._Bundle)
   replies=[]
   def call(wire,timeout):
    packet=json.loads(wire);replies.append(packet)
    return (json.dumps(dict(schema='functional50_chain_v1',id=packet['id'],operation_id='op',kind=packet['kind'],status='UNKNOWN',result=None,error='OSError',unknown=True))+'\n').encode()
   s._call=call
   with patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    client=chain.ChainSession(s,b,c)
    result=client.g05_transaction('x',tuple([1]*13),((0,0,1,1,1,1,1),),stop=False,max_polls=1,duration_ns=100,timeout_ns=100)
   self.assertEqual((result['lower_qpc_ns'],result['upper_qpc_ns']),(10,20));self.assertTrue(s._unknown)
   self.assertEqual(len(replies),1);self.assertEqual((s._dir/'chain-host'/'01-response.bin').read_bytes(),result['raw_response'])
   with self.assertRaises(ValueError):client.g05_transaction('y',tuple([1]*13),((0,0,1,1,1,1,1),),stop=False,max_polls=1,duration_ns=100,timeout_ns=100)
 def test_malformed_reply_is_unknown_and_not_replayed(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_client_a as chain
  with tempfile.TemporaryDirectory() as tmp:
   s=object.__new__(ssh.Session);s._protocol='functional50_chain_v1';s._unknown=False;s._dir=Path(tmp)/'op';s._dir.mkdir();s._check=lambda:None
   c=object.__new__(QpcHostClock);s._clock=c;s._call=lambda *_:b'{bad}\n'
   with patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    client=chain.ChainSession(s,object.__new__(loader._Bundle),c)
    with self.assertRaises(ValueError):client.g05_transaction('x',tuple([1]*13),((0,0,1,1,1,1,1),),stop=False,max_polls=1,duration_ns=100,timeout_ns=100)
   self.assertTrue(s._unknown);self.assertEqual((s._dir/'chain-host'/'01-response.bin').read_bytes(),b'{bad}\n')
 def test_actual_receipt_bytes_and_capture_shape(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_client_a as chain
  identity=tuple([1]*13);command=(0,0,1,1,1,1,1)
  capture=dict(status_before_latch=16,fault_before_latch=0,words32=[0,1,1]+[0]*29,status_before_snapshot=0,status_after_snapshot=0,result_seq=1,tick_unit='50MHz_cycles')
  facts=dict(schema='g05_csr_transaction_v1',operation_id='op',policy_sha256='b'*64,identity_words=list(identity),captures=[capture],deadline_selected_lower_board_monotonic_ns=100,deadline_board_monotonic_ns=200,stop_status=None,stop_fault=None,receipts=[dict(index=1,started_raw_hex=b'{"raw":1}\n'.hex(),returned_raw_hex=b'{"value":2}\n'.hex())],authority='not_evaluated')
  self.assertIs(chain._facts(facts,'op',identity,(command,),False),facts)
  facts['receipts'][0]['started_raw_hex']='AA'
  with self.assertRaises(ValueError):chain._facts(facts,'op',identity,(command,),False)
 def test_fixed_stream_reply_budget_is_protocol_specific(self):
  class Proc:
   def __init__(self):self.stdin=io.BytesIO();self.stdout=io.BytesIO(b'x'*5000+b'\n')
  for protocol,length in [('scalar_v1',4097),('trace_batch_v1',4097),('functional50_chain_v1',5001)]:
   s=object.__new__(ssh.Session);s._proc=Proc();s._protocol=protocol;s._threads=[];s._unknown=False
   self.assertEqual(len(s._call(None,1_000_000_000)),length)
 def test_reject_large_reply_and_wrong_identity(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_client_a as chain
  with self.assertRaises(ValueError):chain._decode(b'x'*1048576+b'\n','x','op','trace_scan')
  data=dict(schema='functional50_chain_v1',id='other',operation_id='op',kind='trace_scan',status='COMPLETE',result={},error=None,unknown=False)
  with self.assertRaises(ValueError):chain._decode((json.dumps(data)+'\n').encode(),'x','op','trace_scan')
 def test_real_preparation_retains_original_inputs_on_unknown(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_client_a as chain, original_source_trace_scan_a as source
  bundle=loader.load_selected(Path.cwd())
  lineage=dict(operation_id='fixture',request_id='fixture-request',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='fixture-boot',session_id=4,tag=5,trigger_id=6,generation=1,request_seq=7,capture_seq=8)
  facts=dict(work_id='fixture-work',declared_by='synthetic-test',scan_id_uint63=1,view=2,frame_seq_start=5,sample_index=8,binding_receipt_id='fixture-bind',lineage=lineage)
  binding=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='fixture',request_hash='a'*64)
  payload=dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=90,em_tick_ms=None,channel_values=[None,None,None,.1],channel_counts=[None,None,None,205],quality=4104)
  draft=dict(status='complete',tick_ms=90,source_count=10,finish_qpc_ns=1090000001,adc={'begin_qpc_ns':1090000000,'end_qpc_ns':1090000001})
  request,src,companions=source._construct_bytes(payload,source._raw(payload),draft,1000000000,'a'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST')
  prepared=bundle.adapter.prepare_bytes(request,src,companions,build_binding=binding)
  # Deliberately no fabricated result metadata: unknown result must preserve inputs and stop.
  with tempfile.TemporaryDirectory() as tmp:
   s=object.__new__(ssh.Session);s._protocol='functional50_chain_v1';s._unknown=False;s._dir=Path(tmp)/'fixture';s._dir.mkdir();s._check=lambda:None
   c=object.__new__(QpcHostClock);s._clock=c;sent=[]
   def exchange(wire,timeout):
    x=json.loads(wire);sent.append(x)
    return chain.raw(dict(schema=chain.SCHEMA,id=x['id'],operation_id='fixture',kind='trace_scan',status='UNKNOWN',result=None,error='OSError',unknown=True))+b'\n'
   s._call=exchange
   with patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    client=chain.ChainSession(s,bundle,c);out=client.trace_scan('trace',prepared,build_binding=binding,timeout_ns=100)
   self.assertEqual(bytes.fromhex(sent[0]['payload']['source_hex']),src);self.assertEqual([bytes.fromhex(v) for v in sent[0]['payload']['companions_hex']],list(companions))
   self.assertEqual((s._dir/'chain-host'/'request.bin').read_bytes(),request);self.assertIsNone(out['correlation']);self.assertTrue(s._unknown)
   with self.assertRaises(ValueError):client.g05_transaction('g05',tuple([1]*13),((0,0,1,1,1,1,1),),stop=False,max_polls=1,duration_ns=100,timeout_ns=100)
if __name__=='__main__':unittest.main()

"""New synthetic request/reply custody controls; no real SSH or board."""
import io,json,pickle,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.integration.host_clock import QpcHostClock
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh, functional50_b131_loader as loader, functional50_chain_v2_client_a as client

class Tests(unittest.TestCase):
 def test_real_send_allocates_one_original_receipt(self):
  with tempfile.TemporaryDirectory() as tmp:
   clock=object.__new__(QpcHostClock);s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._clock=clock;s._dir=Path(tmp)/'op';s._dir.mkdir();s._thread=threading.get_ident();s._unknown=False;s._closed=False;s._check=lambda:None
   s._proc=types.SimpleNamespace(stdin=io.BytesIO(),stdout=io.BytesIO(),stderr=io.BytesIO())
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   ready=dict(schema='chain_board_v2',state='ready',operation_id='op',manifest_sha256='b'*64);origin=(spec,s._proc,clock,(json.dumps(ready)+'\n').encode(),ready,1,2,s._proc.stdin,s._proc.stdout,s._proc.stderr)
   packet=[]
   def call(wire,timeout):
    x=json.loads(wire);packet.append(wire);return (json.dumps(dict(schema=x['schema'],id=x['id'],operation_id=x['operation_id'],kind=x['kind'],status='UNKNOWN',result=None,error='OSError',unknown=True))+'\n').encode()
   s._call=call;bundle=object.__new__(loader._Bundle)
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    chain=client.ChainSessionV2(s,bundle,clock)
    out=chain._send('init','init',dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=1000,max_io=450),100)
    receipt=out['phase_receipt'];self.assertIs(type(receipt),client.OriginalPhaseReceipt);self.assertIs(chain.phase_receipts[0],receipt)
    self.assertIs(receipt.owner,chain);self.assertIs(receipt.session,s);self.assertIs(receipt.process,s._proc);self.assertIs(receipt.clock,clock);self.assertIs(receipt.session_origin,origin)
    self.assertEqual((receipt.phase_index,receipt.kind,receipt.operation_id,receipt.request_raw,receipt.response_raw,receipt.lower_qpc_ns,receipt.upper_qpc_ns),(1,'init','op',packet[0],out['raw_response'],10,20))
    self.assertEqual(receipt.status,'UNKNOWN');self.assertTrue(receipt.unknown);self.assertTrue(s._unknown)
    with self.assertRaises((AttributeError,TypeError)):receipt.kind='status'
    with self.assertRaises(TypeError):pickle.dumps(receipt)
    with self.assertRaises(ValueError):client.OriginalPhaseReceipt(None)
    with self.assertRaises(ValueError):chain._send('again','status',{},100)
    self.assertEqual(len(chain.phase_receipts),1)
 def test_two_success_phases_remain_exact_and_producer_uses_same_object(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer, original_chain_source_pump_a as source_pump
  with tempfile.TemporaryDirectory() as tmp:
   clock=object.__new__(QpcHostClock);s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._clock=clock;s._dir=Path(tmp)/'op';s._dir.mkdir();s._thread=threading.get_ident();s._unknown=False;s._closed=False;s._check=lambda:None
   s._proc=types.SimpleNamespace(stdin=io.BytesIO(),stdout=io.BytesIO(),stderr=io.BytesIO())
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   ready=dict(schema='chain_board_v2',state='ready',operation_id='op',manifest_sha256='b'*64);origin=(spec,s._proc,clock,(json.dumps(ready)+'\n').encode(),ready,1,2,s._proc.stdin,s._proc.stdout,s._proc.stderr)
   def call(wire,timeout):
    x=json.loads(wire);return (json.dumps(dict(schema=x['schema'],id=x['id'],operation_id='op',kind=x['kind'],status='COMPLETE',result={},error=None,unknown=False))+'\n').encode()
   s._call=call
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(QpcHostClock,'__call__',side_effect=[10,20,30,40]):
    chain=client.ChainSessionV2(s,object.__new__(loader._Bundle),clock)
    a=chain._send('init','init',dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=1000,max_io=450),100)
    pump=object.__new__(source_pump.OriginalChainSourcePump);s._source_pump=pump
    with patch.dict(ssh._SESSION_PUMPS,{s:pump}):
     b=chain._send('status','status',{},100)
     self.assertEqual([v.phase_index for v in chain.phase_receipts],[1,2]);self.assertIs(a['phase_receipt'],chain.phase_receipts[0]);self.assertIs(b['phase_receipt'],chain.phase_receipts[1]);self.assertIsNone(a['phase_receipt'].source_pump);self.assertIs(b['phase_receipt'].source_pump,pump)
     owner=object.__new__(producer.OriginalChainReceiptProducer);owner._chain=chain;owner._operation_count=2;owner._operation='op';owner._session=s;owner._process=s._proc;owner._clock=clock;owner._origin=origin;owner._stdin=s._proc.stdin;owner._stdout=s._proc.stdout;owner._stderr=s._proc.stderr;owner._source_pump=pump
     self.assertIs(owner._phase(b,'status','status'),b['phase_receipt'])
     changed=dict(b,raw_response=b'fabricated\n')
     with self.assertRaises(ValueError):owner._phase(changed,'status','status')
     chain.s=object()
     with self.assertRaises(ValueError):_ = chain.phase_receipts
     chain.s=s
 def test_malformed_reply_retained_on_disk_without_fabricated_phase(self):
  with tempfile.TemporaryDirectory() as tmp:
   clock=object.__new__(QpcHostClock);s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._clock=clock;s._dir=Path(tmp)/'op';s._dir.mkdir();s._thread=threading.get_ident();s._unknown=False;s._closed=False;s._check=lambda:None;s._proc=types.SimpleNamespace(stdin=io.BytesIO(),stdout=io.BytesIO(),stderr=io.BytesIO());s._call=lambda *_:b'{bad}\n'
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy');ready=dict(schema='chain_board_v2',state='ready',operation_id='op',manifest_sha256='b'*64);origin=(spec,s._proc,clock,(json.dumps(ready)+'\n').encode(),ready,1,2,s._proc.stdin,s._proc.stdout,s._proc.stderr)
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    chain=client.ChainSessionV2(s,object.__new__(loader._Bundle),clock)
    with self.assertRaises(ValueError):chain._send('init','init',dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=1000,max_io=450),100)
    self.assertTrue(s._unknown);self.assertEqual(chain.phase_receipts,());self.assertEqual((chain.folder/'01-response.bin').read_bytes(),b'{bad}\n')
if __name__=='__main__':unittest.main()

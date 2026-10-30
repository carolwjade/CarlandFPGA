"""New v2-only software controls, no SSH or board."""
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.integration.host_clock import QpcHostClock
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh, functional50_b131_loader as loader

class Tests(unittest.TestCase):
 def test_fixed_v2_transport_and_v1_untouched(self):
  s=ssh.SessionSpec((),'/usr/local/share/pynq-venv/bin/python3','/tmp/functional50_chain_v2_board_a.py','/tmp/plan','C:/unused','a'*64,'C:/unused','op','functional50_chain_v2','/tmp/chain-v2-board-manifest.json','b'*64,'/tmp/policy')
  self.assertIn('chain_v2',ssh._remote_command(s))
  self.assertIn('chain-v2-board-manifest.json',ssh._remote_command(s))
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as board
  manifest=json.loads(board.make_manifest_bytes(Path.cwd()))
  self.assertEqual(set(manifest['files']),board.FILES)
  self.assertIn(board.BASE+'functional50_trace_cycles_a.py',manifest['files'])
 def test_v2_requires_init_then_bounded_choices(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as board
  g=__import__('competition.deepeye.tools.diagnostic.functional50_g05_a',fromlist=['x'])
  def packet(kind,payload,ident='x'):return board.raw(dict(schema='functional50_chain_v2',id=ident,operation_id='op',kind=kind,payload=payload))+b'\n'
  state=board.Sequence()
  with self.assertRaises(ValueError):board.decode_request(packet('status',{}),'op',g,state)
  init=dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=10_000_000_000,max_io=450)
  x=board.decode_request(packet('init',init),'op',g,state);state.consume(x)
  for i in range(4):x=board.decode_request(packet('status',{},'s'+str(i)),'op',g,state);state.consume(x)
  with self.assertRaises(ValueError):board.decode_request(packet('status',{},'s4'),'op',g,state)
  with self.assertRaises(ValueError):board.decode_request(packet('init',init,'new'),'op',g,state)
 def test_unknown_reply_stops_host(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_client_a as client
  with tempfile.TemporaryDirectory() as tmp:
   s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._unknown=False;s._dir=Path(tmp)/'op';s._dir.mkdir();s._check=lambda:None
   c=object.__new__(QpcHostClock);s._clock=c;sent=[]
   def call(wire,timeout):
    x=json.loads(wire);sent.append(x)
    return (json.dumps(dict(schema=x['schema'],id=x['id'],operation_id='op',kind=x['kind'],status='UNKNOWN',result=None,error='OSError',unknown=True))+'\n').encode()
   s._call=call
   with patch.object(QpcHostClock,'__call__',side_effect=[10,20]):
    session=client.ChainSessionV2(s,object.__new__(loader._Bundle),c)
    out=session.init('init',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
   self.assertTrue(s._unknown);self.assertEqual((out['lower_qpc_ns'],out['upper_qpc_ns']),(10,20))
   with self.assertRaises(ValueError):session.status('status',timeout_ns=100)
   self.assertEqual(len(sent),1)
 def test_two_cycles_and_explicit_close_are_one_use(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as board, functional50_g05_a as g05
  state=board.Sequence()
  def submit(i,k,p):
   data=board.raw(dict(schema=board.SCHEMA,id='r'+str(i),operation_id='op',kind=k,payload=p))+b'\n'
   x=board.decode_request(data,'op',g05,state);state.consume(x)
  init=dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=1000,max_io=450)
  scan=dict(request_hex='00',source_hex='01',companions_hex=['02']*4,build_binding={},max_io=900)
  submit(1,'init',init);submit(2,'trace_scan',scan);submit(3,'apply',dict(command_words=[0,0,1,1,1,1,1]));submit(4,'status',{});submit(5,'trace_scan',scan);submit(6,'apply',dict(command_words=[0,0,1,1,1,2,2]))
  with self.assertRaises(ValueError):submit(7,'trace_scan',scan)
  with self.assertRaises(ValueError):submit(7,'apply',dict(command_words=[0,0,1,1,1,3,3]))
  submit(7,'close',dict(stop=False))
  with self.assertRaises(ValueError):submit(8,'status',{})
 def test_fact_encoding_preserves_raw_bytes_and_phase(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as board, functional50_g05_session_a as session, functional50_g05_transaction_a as tx
  receipt=tx.IOReceipt(1,b'{"kind":"read"}\n',b'{"value":1}\n')
  facts=session.SessionFacts('g05_csr_session_v2','init','op','a'*64,100,1100,1,1,tuple([1]*13),1,0,None,(receipt,),(),'ACTIVE')
  result=board.facts_json(facts,session,tx)
  self.assertEqual(bytes.fromhex(result['receipts'][0]['started_raw_hex']),receipt.started_raw)
  self.assertEqual((result['phase_io_first'],result['phase_io_last']),(1,1));self.assertEqual(result['authority'],'not_evaluated')
  partial=session.UnresolvedIO(2,b'started\n',None,b'not-attempted\n')
  failed=session.SessionFacts('g05_csr_session_v2','close','op','a'*64,100,1100,None,None,tuple([1]*13),None,None,None,(receipt,),(partial,),'CLOSED_AFTER_FAILURE')
  result=board.facts_json(failed,session,tx)
  self.assertEqual(bytes.fromhex(result['unresolved_receipts'][0]['not_attempted_raw_hex']),partial.not_attempted_raw)
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_client_a as client
  client._failure_facts(result,'op')
  result['unresolved_receipts'][0]['index']=1
  with self.assertRaises(ValueError):client._failure_facts(result,'op')
 def test_board_dispatch_two_synthetic_cycles(self):
  import time,types
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as board, functional50_g05_a as g05, functional50_g05_session_a as sess, functional50_g05_transaction_a as tx, functional50_board_trace_batch_a as batch
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'op';path.mkdir();plan=dict(operation_id='op',request_sha256='a'*64,boot_id='boot',source_commit='b'*40,build_id='c'*32)
   binding={k:plan[k] for k in ('operation_id','request_sha256','boot_id','source_commit','build_id')}
   class Port:
    def __init__(self):self._dir=path;self._boot='boot';self._count=0
   port=Port();fakeboard=types.SimpleNamespace(_TracePort=Port,_G05_LOADS={port:(None,None,None,tuple(binding.items()),None,None,None,None,None)},_bytes=lambda p,n:((json.dumps(plan).encode() if p=='plan' else b'policy'),(1,2)),_json=batch._json,select_trace_cycle_v2=lambda:None,open_from_plan=lambda *a,**k:port)
   class Issuer:
    def __init__(self,*a):self._deadline=time.monotonic_ns()+5_000_000_000
   class GS:
    def __init__(self,issuer):self.issuer=issuer;self._state='ACTIVE';self.identity=None
    def fact(self,kind,capture=None,state='ACTIVE'):
     return sess.SessionFacts('g05_csr_session_v2',kind,'op','d'*64,self.issuer._deadline-5_000_000_000,self.issuer._deadline,1,1,self.identity,1,0,capture,(tx.IOReceipt(1,b'start',b'end'),),(),state)
    def init(self,identity):self.identity=identity;return self.fact('init')
    def apply_one(self,words):return self.fact('apply',tx.CaptureFacts(1,0,(0,words[5],words[6])+tuple([0]*29),1,1,1))
    def observe_status(self):return self.fact('status')
    def close(self,*,stop):return self.fact('close',state='CLOSED')
   class Cycle:
    def __init__(self,*a):self.count=0
    def bind_deadline(self,deadline):self.deadline=deadline
    def scan(self,line,*,max_io):
     self.count+=1;port._count+=1;x=batch._json(line)
     return dict(index=self.count,request_sha256=board.digest(bytes.fromhex(x['request_hex'])),source_sha256=board.digest(bytes.fromhex(x['source_hex'])),response=b'{"status":"COMPLETE"}',correlation={'status':'FOUR_FRAME_CORRELATION_CONSISTENT','retained':b'raw'},directory=Path('/board/evidence'),evidence_manifest_sha256='e'*64)
   fakeg=types.SimpleNamespace(_identity=g05._identity,_command=g05._command,_policy=lambda *a:{'limits':{'total_io':400,'begin':1,'commit':2,'latch':2,'release':2}},open_g05=lambda *a:object())
   faketx=types.SimpleNamespace(IOReceipt=tx.IOReceipt,TransactionIssuer=Issuer,Limits=tx.Limits)
   fakesess=types.SimpleNamespace(SessionFacts=sess.SessionFacts,UnresolvedIO=sess.UnresolvedIO,G05SessionV2=GS)
   binding2=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='op',request_hash='a'*64)
   scan=lambda n:dict(request_hex=('0'+str(n)),source_hex=('1'+str(n)),companions_hex=['02']*4,build_binding=binding2,max_io=900)
   choices=[('init',dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=5_000_000_000,max_io=450)),('trace_scan',scan(1)),('apply',dict(command_words=[0,0,1,1,1,1,1])),('status',{}),('trace_scan',scan(2)),('apply',dict(command_words=[0,0,1,1,1,2,2])),('close',dict(stop=False))]
   incoming=b''.join(board.raw(dict(schema=board.SCHEMA,id='r'+str(i),operation_id='op',kind=k,payload=p))+b'\n' for i,(k,p) in enumerate(choices));out=io.BytesIO()
   with patch.object(board,'verify_manifest',return_value=Path(tmp)),patch.object(board,'load_modules',return_value=(fakeboard,batch,types.SimpleNamespace(load_selected=lambda _:object()),fakeg,faketx,fakesess,types.SimpleNamespace(TraceCycles=Cycle))),patch.object(board.sys,'stdin',types.SimpleNamespace(buffer=io.BytesIO(incoming))),patch.object(board.sys,'stdout',types.SimpleNamespace(buffer=out)):
    board.main(['chain_v2','plan','manifest','f'*64,'policy'])
   replies=[json.loads(v) for v in out.getvalue().splitlines()]
   self.assertEqual([x.get('kind') for x in replies[1:]],[x[0] for x in choices]);self.assertTrue(all(x['status']=='COMPLETE' for x in replies[1:]));self.assertEqual(replies[2]['result']['correlation_status'],'FOUR_FRAME_CORRELATION_CONSISTENT')
if __name__=='__main__':unittest.main()

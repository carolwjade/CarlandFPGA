"""Software-only original-object custody and no-replay controls."""
import tempfile,threading,unittest,types,json,pickle,io
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.integration.host_clock import QpcHostClock
from competition.deepeye.tools.run_causal_functional_chain import FunctionalWorld,FunctionalSource
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh, functional50_b131_loader as loader, functional50_chain_v2_client_a as client, original_source_trace_scan_a as scan, functional50_chain_v2_board_a as protocol

class Tests(unittest.TestCase):
 def fixture(self,tmp):
  clock=object.__new__(QpcHostClock);world=object.__new__(FunctionalWorld);source=object.__new__(FunctionalSource)
  world.clock=clock;world._thread=threading.get_ident();world.operation_id='op';world.source=source;world.owner=object();world.binding=object()
  source.clock=clock;source.owner=world.owner;source.binding=world.binding;source._thread=threading.get_ident();source.book=types.SimpleNamespace(_origin=100);source.source=types.SimpleNamespace(state='RUNNING',_count=0,_origin=100);source._retained_samples=[];source._start_attempted=True
  bundle=object.__new__(loader._Bundle);scanner=object.__new__(scan.OriginalSourceTraceScan);scanner._functional=source;scanner._clock=clock;scanner._bundle=bundle;scanner._source=source.source;scanner._book=source.book;scanner._thread=threading.get_ident();scanner._source_scan_cycle_v2=True;scanner._admitted=[];scanner._prepared=False;scanner._failed=False;scanner._prepare_count=0;scanner._activated=True;scanner._origin=100;scanner._ledger=object()
  s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._clock=clock;s._proc=types.SimpleNamespace(stdin=object(),stdout=object(),stderr=object());s._dir=Path(tmp)/'op';s._dir.mkdir();s._unknown=False;s._closed=False;s._thread=threading.get_ident();s._check=lambda:None
  spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy');ready=dict(schema='chain_board_v2',state='ready',operation_id='op',manifest_sha256='b'*64);origin=(spec,s._proc,clock,(json.dumps(ready)+'\n').encode(),ready,1,2,s._proc.stdin,s._proc.stdout,s._proc.stderr)
  origin_patch=patch.dict(ssh._SESSION_ORIGINS,{s:origin});origin_patch.start();self.addCleanup(origin_patch.stop)
  ticks=iter(range(10,10000));clock_patch=patch.object(QpcHostClock,'__call__',lambda _:next(ticks));clock_patch.start();self.addCleanup(clock_patch.stop)
  chain=client.ChainSessionV2(s,bundle,clock)
  return world,source,bundle,scanner,s,chain,clock
 def issue(self,chain,ident,kind,status='COMPLETE',correlation=None):
  """Synthetic transport, but phase is allocated by the real _send path."""
  doc=dict(schema='functional50_chain_v2',id=ident,operation_id='op',kind=kind,status=status,result={} if status=='COMPLETE' else None,error=None if status=='COMPLETE' else 'OSError',unknown=status=='UNKNOWN')
  chain.s._call=lambda *_:(json.dumps(doc)+'\n').encode()
  payload=({'identity_words':[1]*13,'max_commands':2,'max_polls':64,'duration_ns':1000,'max_io':450} if kind=='init' else {'request_hex':'00','source_hex':'01','companions_hex':['02']*4,'build_binding':{},'max_io':2000} if kind=='trace_scan' else {})
  out=chain._send(ident,kind,payload,100);out['correlation']=correlation;return out
 def test_opaque_one_use_original_event_and_swap_refused(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,s,chain,clock=self.fixture(tmp)
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   origin=ssh._SESSION_ORIGINS[s]
   doc=dict(schema='functional50_chain_v2',id='x',operation_id='op',kind='init',status='COMPLETE',result={},error=None,unknown=False);raw=(json.dumps(doc)+'\n').encode()
   test=self
   def fake_init(chain,ident,*a,**k):return test.issue(chain,ident,'init')
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(client.ChainSessionV2,'init',fake_init):
    p=producer.OriginalChainReceiptProducer(world,chain,scanner);event=p.init('x',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
    self.assertNotIsInstance(event,dict)
    with self.assertRaises(TypeError):pickle.dumps(event)
    with self.assertRaises(ValueError):producer.consume_original_receipt(object())
    world.source=object()
    with self.assertRaises(ValueError):producer.consume_original_receipt(event)
    world.source=source
    facts,refs=producer.consume_original_receipt(event)
    self.assertEqual(facts['raw_response'],raw);self.assertIs(refs['session'],s);self.assertIs(refs['clock'],clock)
    with self.assertRaises(ValueError):producer.consume_original_receipt(event)
    chain.clock=object()
    with self.assertRaises(ValueError):p.status('s',timeout_ns=100)
 def test_unknown_stops_without_replay_or_stop(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,s,chain,clock=self.fixture(tmp);spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   origin=ssh._SESSION_ORIGINS[s]
   doc=dict(schema='functional50_chain_v2',id='x',operation_id='op',kind='init',status='UNKNOWN',result=None,error='OSError',unknown=True);raw=(json.dumps(doc)+'\n').encode()
   calls=[]
   test=self
   def fake_init(chain,ident,*a,**k):calls.append(ident);return test.issue(chain,ident,'init','UNKNOWN')
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(client.ChainSessionV2,'init',fake_init):
    p=producer.OriginalChainReceiptProducer(world,chain,scanner);event=p.init('x',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
    self.assertTrue(producer.consume_original_receipt(event)[0]['response']['unknown'])
    with self.assertRaises(ValueError):p.close('close',stop=False,timeout_ns=100)
    self.assertEqual(calls,['x'])
 def test_original_sample_and_preparation_are_retained_in_order(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,s,chain,clock=self.fixture(tmp)
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   origin=ssh._SESSION_ORIGINS[s]
   class Preparation:pass
   bundle.adapter=types.SimpleNamespace(Preparation=Preparation)
   payload=object();draft={'status':'complete'};token=types.SimpleNamespace(_draft=draft,_handle=object(),_em_handle=None);admission=object();item={'entry':{'payload':payload},'token':token,'draft':draft,'payload_bytes':b'source','received':15,'admission':admission}
   prepared=Preparation();prepared.original=types.SimpleNamespace(request=b'request',source=b'source',companions=(b'a',b'b',b'c',b'd'))
   def admit(self,value):self._admitted.append(item);return admission
   def prepare(self,value,*,facts,build_binding):self._result=prepared;return prepared
   test=self
   def result(chain,ident,*a,**k):
    kind='trace_scan' if ident=='scan' else 'init'
    return test.issue(chain,ident,kind,correlation={'status':'FOUR_FRAME_CORRELATION_CONSISTENT'} if kind=='trace_scan' else None)
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(client.ChainSessionV2,'init',result),patch.object(client.ChainSessionV2,'trace_scan',result),patch.object(scan.OriginalSourceTraceScan,'admit',admit),patch.object(scan.OriginalSourceTraceScan,'prepare',prepare):
    p=producer.OriginalChainReceiptProducer(world,chain,scanner)
    first=p.init('init',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
    second=p.admit_source(payload);third=p.scan_actual('scan',payload,facts={},build_binding={},max_io=2000,timeout_ns=100)
    with self.assertRaises(ValueError):producer.consume_original_receipt(third)
    producer.consume_original_receipt(first);f,refs=producer.consume_original_receipt(second)
    self.assertIs(refs['token'],token);self.assertIs(refs['draft'],draft);self.assertEqual(f['payload_bytes'],b'source')
    f,refs=producer.consume_original_receipt(third)
    self.assertIs(refs['preparation'],prepared);self.assertIs(refs['companions'],prepared.original.companions);self.assertEqual(f['correlation']['status'],'FOUR_FRAME_CORRELATION_CONSISTENT')
 def test_substitution_and_malformed_original_response_stop(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,s,chain,clock=self.fixture(tmp)
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   origin=ssh._SESSION_ORIGINS[s]
   def bad(chain,ident,*a,**k):
    chain.s._call=lambda *_:b'{bad}\n'
    return chain._send(ident,'init',dict(identity_words=[1]*13,max_commands=2,max_polls=64,duration_ns=1000,max_io=450),100)
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(client.ChainSessionV2,'init',bad):
    p=producer.OriginalChainReceiptProducer(world,chain,scanner)
    with self.assertRaises(ValueError):p.init('x',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
    with self.assertRaises(ValueError):p.status('next',timeout_ns=100)
 def test_init_before_explicit_scanner_binding(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,s,chain,clock=self.fixture(tmp)
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   origin=ssh._SESSION_ORIGINS[s]
   doc=dict(schema='functional50_chain_v2',id='x',operation_id='op',kind='init',status='COMPLETE',result={},error=None,unknown=False)
   test=self
   def init(chain,ident,*a,**k):return test.issue(chain,ident,'init')
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.object(client.ChainSessionV2,'init',init):
    p=producer.OriginalChainReceiptProducer(world,chain);event=p.init('x',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
    p.bind_scanner(scanner);self.assertIs(producer.consume_original_receipt(event)[1]['scanner'],None)
    with self.assertRaises(ValueError):p.bind_scanner(scanner)
 def test_wait_runs_only_fixed_pump_on_owner_thread(self):
  from competition.deepeye.tools.diagnostic import original_chain_source_pump_a as pump_module
  event=threading.Event();called=[];owner=threading.get_ident()
  class BlockingReader:
   def readline(self,n):event.wait(1);return b'reply\n'
  s=object.__new__(ssh.Session);s._proc=types.SimpleNamespace(stdin=io.BytesIO(),stdout=BlockingReader());s._protocol='functional50_chain_v2';s._threads=[];s._unknown=False;s._thread=owner;s._clock=object()
  pump=object.__new__(pump_module.OriginalChainSourcePump);pump._enabled=True;pump._failed=False;pump._session=s;pump._clock=s._clock;s._source_pump=pump
  def poll(self,session):called.append(threading.get_ident());event.set()
  with patch.dict(ssh._SESSION_PUMPS,{s:pump}),patch.object(pump_module.OriginalChainSourcePump,'poll_once',poll):self.assertEqual(s._call(b'one\n',1_000_000_000),b'reply\n')
  self.assertEqual(called,[owner]);self.assertEqual(s._proc.stdin.getvalue(),b'one\n')
  event2=threading.Event()
  class PendingReader:
   def readline(self,n):event2.wait(1);return b'late\n'
  t=object.__new__(ssh.Session);t._proc=types.SimpleNamespace(stdin=io.BytesIO(),stdout=PendingReader());t._protocol='functional50_chain_v2';t._threads=[];t._unknown=False;t._thread=owner;t._clock=object()
  pump2=object.__new__(pump_module.OriginalChainSourcePump);pump2._enabled=True;pump2._failed=False;pump2._session=t;pump2._clock=t._clock;t._source_pump=pump2
  def fail(self,session):raise RuntimeError('source failure')
  with patch.dict(ssh._SESSION_PUMPS,{t:pump2}),patch.object(pump_module.OriginalChainSourcePump,'poll_once',fail):
   with self.assertRaises(RuntimeError):t._call(b'once\n',1_000_000_000)
  self.assertTrue(t._unknown);self.assertTrue(t._threads[0].is_alive());self.assertEqual(t._proc.stdin.getvalue(),b'once\n')
  event2.set();t._threads[0].join(1)
 def test_pumped_source_events_precede_board_response(self):
  from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as producer, original_chain_source_pump_a as pm
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,s,chain,clock=self.fixture(tmp);s._check=lambda:None
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy')
   origin=ssh._SESSION_ORIGINS[s]
   pump=object.__new__(pm.OriginalChainSourcePump);pump._session=s;pump._source=source;pump._scanner=scanner;pump._clock=clock;pump._enabled=False;pump._failed=False;pump._history=[];pump._pending=None
   token=types.SimpleNamespace(_handle=object(),_em_handle=None);draft={'status':'complete'};token._draft=draft;payload=object();admission=object();entry={'payload':payload};item=dict(entry=entry,token=token,draft=draft,admission=admission,payload_bytes=b'payload',received=15)
   def fake_enable(self):self._enabled=True
   def fake_poll(self,session):scanner._admitted.append(item);self._history.append(pm.PumpRecord(payload,token,entry,draft,admission,15,True))
   test=self
   def response(chain,ident,*args,**kwargs):
    if ident=='status':pm.OriginalChainSourcePump.poll_once(pump,s)
    return test.issue(chain,ident,'init' if ident=='init' else 'status')
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.dict(ssh._SESSION_PUMPS,{}),patch.object(client.ChainSessionV2,'init',response),patch.object(client.ChainSessionV2,'status',response),patch.object(pm.OriginalChainSourcePump,'enable',fake_enable),patch.object(pm.OriginalChainSourcePump,'poll_once',fake_poll):
    p=producer.OriginalChainReceiptProducer(world,chain);initial=p.init('init',tuple([1]*13),max_commands=2,max_polls=64,duration_ns=1000,max_io=450,timeout_ns=100)
    p.bind_scanner(scanner);p.bind_pump(pump);p.enable_pump();response_event=p.status('status',timeout_ns=100);pending=p.take_pending_events()
    self.assertEqual(len(pending),1);producer.consume_original_receipt(initial)
    with self.assertRaises(ValueError):producer.consume_original_receipt(response_event)
    facts,refs=producer.consume_original_receipt(pending[0]);self.assertEqual(facts['kind'],'source_admission');self.assertIs(refs['token'],token)
    self.assertEqual(producer.consume_original_receipt(response_event)[0]['kind'],'status')
if __name__=='__main__':unittest.main()

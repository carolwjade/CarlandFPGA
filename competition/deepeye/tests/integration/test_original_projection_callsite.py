import unittest
from types import SimpleNamespace as N
from unittest.mock import patch
from competition.deepeye.simulation.authority.source_projection_v1 import provider

class FakeProducer:
    def __init__(self): self.ids=[];self.calls=[];self.count=0
    def _check(self):pass
    def bind_id(self,ref,label):self.ids.append((ref,label))
    def attach_config(self,*a,**k):self.calls.append(('config',a,k))
    def attach_admission(self,*a,**k):self.calls.append(('admission',a,k))
    def attach_capture(self,*a,**k):self.calls.append(('capture',a,k))
    def attach_transition(self,*a,**k):self.calls.append(('transition',a,k))
    def read_current(self):self.count+=1;return {'at_qpc_ns':31,'valid_span':{'from_qpc_ns':20,'through_qpc_ns':31}}
    def attach_registry(self,*a,**k):self.calls.append(('registry',a,k))
    def export(self,**k):return {'proof':None,'missing_paths':['external'],**k}

class Controls(unittest.TestCase):
    def fixture(self):
        root=N(boot=None,command=None); custody=N(pending=None,transitions=[]); book=N(_samples=[],_actor_custody=custody,_root=root);link=N(binding=N(),composition=N(),executor=N(_root=root));owner=N(_commits=[]);prod=FakeProducer()
        with patch.object(provider.assembler,'attach_original',return_value=prod): session=provider.ProjectionSession.attach_original(owner,link,book)
        return session,owner,link,book,prod
    def test_factory_is_explicit(self):
        self.assertTrue(callable(provider.ProjectionSession.attach_original))
        with self.assertRaises(ValueError):provider.ProjectionSession(None,None,None,None,None)
    def test_original_sample_identity_and_partial_export(self):
        s,o,l,b,p=self.fixture();sample={'tick_ms':0};b._samples.append(sample);token=N(_book=b,_draft=sample,_ended=True);cap=object();s.observe_capture(cap,token,candidate={'source':'actual supplied'},fields={});self.assertIs(p.calls[-1][1][1],sample)
        current=s.read_current();out=s.export(current_read=current,registry_ref=None,candidate_ref=cap);self.assertIsNone(out['proof']);self.assertEqual(1,p.count)
        with self.assertRaises(ValueError):s.observe_capture(object(),N(_book=b,_draft=dict(sample),_ended=True),candidate={},fields={})
        with self.assertRaises(ValueError):s.observe_capture(object(),N(_book=b,_draft=sample,_ended=False),candidate={},fields={})
    def test_closed_transition_and_missing_receipt_refused(self):
        s,o,l,b,p=self.fixture();t=N(kind='STEP',closed=False);b._actor_custody.transitions.append(t)
        with self.assertRaises(ValueError):s.observe_finished_transition(t,successor_root=b._root,fields={})
        t.closed=True;slot=N(book_transition=t,committed=True,uncertainty='unknown',receipt=None,post_root=b._root);o._commits.append(slot)
        with self.assertRaises(ValueError):s.observe_finished_transition(t,successor_root=b._root,slot=slot,fields={})
        self.assertFalse(any(x[0] is slot for x in p.ids))
    def test_registry_never_stamps_getter_or_creates_missing(self):
        s,o,l,b,p=self.fixture();current=s.read_current();view=object();obs=object()
        with self.assertRaises(ValueError):s.attach_registry(view,{},1,as_of_qpc_ns=None,observation_ref=obs)
        s.attach_registry(view,{'source':'external'},1,as_of_qpc_ns=29,observation_ref=obs)
        self.assertEqual(29,p.calls[-1][2]['as_of_qpc_ns']);self.assertNotEqual(current['at_qpc_ns'],29)
        out=s.export(current_read=current,registry_ref=view,candidate_ref=None);self.assertIsNone(out['proof'])
        with self.assertRaises(ValueError):s.bind_observed(None)
    def test_exact_c42_bytes_and_schema(self):
        import hashlib
        from pathlib import Path
        root=Path(provider.__file__).parent
        self.assertEqual('b49169ac2ab87073e31406d8448d69c7958d5e5775310f94990fe89eee8d3722',hashlib.sha256((root/'assembler.py').read_bytes()).hexdigest())
        self.assertEqual('ab1b432e9f337523fd75057fec4647f5eda2569de308e7c777507e05907bdd70',hashlib.sha256((root/'request.schema.json').read_bytes()).hexdigest())

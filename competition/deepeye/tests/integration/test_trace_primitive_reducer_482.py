"""Derived reducer primitive records: mutation isolation and foreign values."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader

class PrimitiveReducerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.module=loader.load_selected(Path.cwd()).reducer

    def reducer(self):
        m=self.module;r=object.__new__(m.Reducer)
        r.operation_id='synthetic';r.phase='work';r.phase_elapsed_ns={'work':0,'cleanup':0}
        r.pending=None;r.call_id=0;r.events=[];r.limits=dict(m.LIMITS)
        r.counts={k:0 for k in ('csr','polls','writes','pops','pop_stages','cleanup_polls')}
        r.evidence_reserved={'work':0,'cleanup':0,'final':1048576}
        r.start_consumed=True;r.collect_consumed=r.cancel_consumed=r.arm_attempt_owned=False
        r.unknown_effects=r.completed=r.quiescent=r.failed=False
        r.errors=[];r.results=[];r.prefix=bytearray();r.pending_peek=r.last_pop_id=r.unread_count=None
        r.plan=SimpleNamespace(original=None,_build={'nested':{'retained':1}})
        def intents(): yield m.read(0x30,'synthetic')
        r.generator=intents();return r

    def test_flat_record_rejects_foreign_nested_values_before_shallow_copy(self):
        self.assertTrue(hasattr(self.module,'_primitive_record'),'flat primitive grammar missing')
        for v in ({'nested':[]},{'nested':{}},{'value':object()}):
            with self.assertRaises(ValueError): self.module._primitive_record(v)
        class Foreign(str):pass
        with self.assertRaises(ValueError): self.module._primitive_record({Foreign('key'):1})
        with self.assertRaises(ValueError): self.module._primitive_record({'key':Foreign('value')})
        original={'none':None,'boolean':True,'integer':7,'text':'raw'}
        copied=self.module._primitive_record(original);original['integer']=8
        self.assertEqual(copied,{'none':None,'boolean':True,'integer':7,'text':'raw'})

    def test_returned_intent_and_observation_remain_isolated_from_events_and_pending(self):
        r=self.reducer();intent=r.advance(phase_elapsed_ns=1)
        intent['offset']=0x18;intent['label']='mutated'
        self.assertEqual(r.pending['offset'],0x30);self.assertEqual(r.events[0]['intent']['label'],'synthetic')
        obs=dict(operation_id='synthetic',call_id=1,status='confirmed_read',value=7,error_code=None)
        self.assertIsNone(r.advance(obs,phase_elapsed_ns=2));obs['value']=99
        self.assertEqual(r.events[-1]['observation']['value'],7)
        snapshot=r.snapshot();snapshot['events'][0]['intent']['offset']=99
        snapshot['events'][1]['observation']['value']=88;snapshot['build_binding']['nested']['retained']=9
        self.assertEqual(r.events[0]['intent']['offset'],0x30);self.assertEqual(r.events[1]['observation']['value'],7)
        self.assertEqual(r.plan._build['nested']['retained'],1)

    def test_unknown_effect_preserves_original_failure_and_consumes_pending(self):
        r=self.reducer();r.advance(phase_elapsed_ns=1)
        r.advance(dict(operation_id='synthetic',call_id=1,status='unknown',value=None,error_code=None),phase_elapsed_ns=2)
        self.assertTrue(r.unknown_effects);self.assertTrue(r.failed);self.assertIsNone(r.pending)
        self.assertEqual(r.errors,['OPERATION_UNKNOWN']);self.assertIsNone(r.generator)

    def test_foreign_nested_intent_never_becomes_pending_or_an_event(self):
        r=self.reducer()
        def foreign(): yield dict(kind='read',offset=0x30,value=None,label=['foreign'],poll=False)
        r.generator=foreign()
        self.assertIsNone(r.advance(phase_elapsed_ns=1))
        self.assertTrue(r.failed);self.assertIsNone(r.pending);self.assertEqual(r.events,[])
        self.assertEqual(r.errors,['FLAT_IMMUTABLE_PRIMITIVES_REQUIRED'])

if __name__=='__main__':unittest.main()

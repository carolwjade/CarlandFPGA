"""Synthetic journal persistence controls; these never execute actual MMIO."""
import json
from pathlib import Path
import tempfile
import unittest
from competition.deepeye.tools.diagnostic import functional50_board_trace_batch_a as batch


class TraceSlabControls(unittest.TestCase):
    def slab(self,path,capacity=2):
        self.assertTrue(hasattr(batch,'_AuditSlabV1'),'bounded pre-effect TRACE journal missing')
        return batch._AuditSlabV1(path,base_io=10,capacity=capacity,binding={'operation_id':'SYNTHETIC_TEST_473'},boot='synthetic-boot')

    def intent(self,n):return batch.raw(dict(call_id=n,kind='read',offset=48,value=None))

    def test_complete_pair_is_persisted_with_intent_before_effect(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'audit.bin';slab=self.slab(path)
            with self.assertRaises(ValueError):slab.record(11,'started',{'id':'x','kind':'read'})
            slab.reserve(1,self.intent(1));slab.record(11,'started',dict(id='x',kind='read',offset=48,value=None))
            self.assertIsNone(slab.pair(11))
            slab.record(11,'returned',dict(id='x',kind='read',value=7));slab.outcome(1,batch.raw(dict(status='confirmed_read',value=7)))
            pair=slab.pair(11);self.assertEqual(json.loads(pair[1])['value'],7)
            slab.finish()
            self.assertTrue(path.is_file());self.assertLessEqual(path.stat().st_size,12288)
            self.assertIn(pair[0].hex().encode(),path.read_bytes())
            with self.assertRaises(ValueError):slab.reserve(2,self.intent(2))

    def test_unknown_and_not_attempted_never_produce_a_complete_pair(self):
        with tempfile.TemporaryDirectory() as td:
            slab=self.slab(Path(td)/'audit.bin');slab.reserve(1,self.intent(1))
            slab.record(11,'started',dict(id='x',kind='read',offset=48,value=None));slab.record(11,'not-attempted',dict(id='x'))
            self.assertIsNone(slab.pair(11));slab.finish()

    def test_duplicate_and_capacity_exhaustion_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            slab=self.slab(Path(td)/'audit.bin',capacity=1);slab.reserve(1,self.intent(1))
            with self.assertRaises(ValueError):slab.reserve(1,self.intent(1))
            with self.assertRaises(ValueError):slab.reserve(2,self.intent(2))
            slab.finish()

    def test_deadline_refusal_consumes_no_io_and_cleanup_binds_next_intent(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'audit.bin';slab=self.slab(path)
            slab.reserve(1,self.intent(1));slab.outcome(1,batch.raw(dict(status='not_attempted')))
            slab.reserve(2,self.intent(2))
            slab.record(11,'started',dict(id='cleanup',kind='read',offset=48,value=None))
            slab.record(11,'returned',dict(id='cleanup',kind='read',value=0))
            slab.outcome(2,batch.raw(dict(status='confirmed_read',value=0)))
            self.assertEqual(json.loads(slab.pair(11)[0])['id'],'cleanup')
            slab.finish();data=path.read_bytes()
            self.assertEqual(int.from_bytes(data[4096+2048:4096+2052],'little'),0)
            self.assertGreater(int.from_bytes(data[8192+2048:8192+2052],'little'),0)

    def test_navigation_response_uses_its_finite_global_io_cap_only_when_selected(self):
        from competition.deepeye.tools.diagnostic import functional50_trace_batch_client_a as client
        from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ADJACENT_180S
        doc=dict(schema='trace_batch_v1',id='synthetic',operation_id='synthetic',request_sha256='a'*64,
            lineage_request_hash='b'*64,status='UNKNOWN',raw_wire_hex=None,wire_complete=False,
            results=[],io_count=6000,batch_io_count=1,cleanup_observed=False,terminal='UNKNOWN',unknown=True)
        data=batch.raw(doc)+b'\n';args=(data,'synthetic','synthetic','a'*64,'b'*64)
        with self.assertRaises(ValueError):client._response(*args)
        result,_=client._response(*args,demo_cycle_profile=NAV_ADJACENT_180S)
        self.assertTrue(result['unknown'])
        self.assertEqual(result['io_count'],6000)

    def test_binary_slab_preserves_exact_primitive_receipts_and_deadline_gap(self):
        import marshal
        from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ADJACENT_180S
        self.assertTrue(hasattr(batch,'_AuditSlabV2'),'binary pre-effect journal missing')
        with tempfile.TemporaryDirectory() as td:
            slab=batch._AuditSlabV2(Path(td)/'audit.bin',base_io=10,capacity=2,binding={'operation_id':'synthetic'},boot='synthetic',profile=NAV_ADJACENT_180S)
            intent=dict(call_id=1,kind='read',offset=48,value=None)
            slab.reserve(1,intent);slab.outcome(1,dict(status='not_attempted'))
            slab.reserve(2,dict(intent,call_id=2))
            start=dict(id='cleanup',kind='read',offset=48,value=None)
            end=dict(id='cleanup',kind='read',value=7)
            slab.record(11,'started',start);slab.record(11,'returned',end)
            slab.outcome(2,dict(status='confirmed_read',value=7))
            pair=slab.pair(11)
            self.assertEqual(marshal.loads(pair[0])['data'],start)
            self.assertEqual(marshal.loads(pair[1])['data'],end)
            slab.finish()


if __name__=='__main__':unittest.main()

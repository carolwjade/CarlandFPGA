"""Targeted fixture counterexamples; no real authentication/process/hardware."""
from pathlib import Path
import json
import sys
import unittest

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
sys.path.insert(0,str(PRODUCT))
from competition.deepeye.tests.simulation import test_pc_direct_runtime as t
r=t.runtime
ROWS=[]

class IndependentRuntime(unittest.TestCase):
    def setUp(self):
        self.f=t.PcDirectRuntimeTests();self.f.setUp()

    def test_01_stop_during_boot_verification_cannot_be_erased_by_same_boot(self):
        f=self.f
        verify=f.provider.verify_boot
        def stopped_boot(event):
            value=verify(event)
            f.owner.stop('operator STOP during BOOT verification')
            return value
        f.provider.verify_boot=stopped_boot
        try:f.activate();f.observe();f.command()
        except ValueError:pass
        result=f.step()
        ROWS.append({'case':'stop_during_boot','committed':result.committed,'reason':result.reason,'fixture_commits':f.provider.committed})
        self.assertFalse(result.committed,'BOOT activation erased a STOP raised during its own verifier')
        self.assertEqual(0,f.provider.committed)

    def test_02_rejected_reentrant_event_during_boot_remains_latched(self):
        f=self.f
        verify=f.provider.verify_boot
        def interrupted_boot(event):
            value=verify(event)
            try:f.owner.board(None)
            except ValueError:pass
            return value
        f.provider.verify_boot=interrupted_boot
        try:f.activate();f.observe();f.command()
        except ValueError:pass
        result=f.step()
        ROWS.append({'case':'reentrant_event_during_boot','committed':result.committed,'reason':result.reason,'fixture_commits':f.provider.committed})
        self.assertFalse(result.committed,'same in-flight BOOT cleared a rejected event STOP')
        self.assertEqual(0,f.provider.committed)

    def test_03_reentrant_stop_during_ai_command_admission_vetoes(self):
        f=self.f;f.activate();f.observe()
        lease=f.provider.ai_lease
        def loss(boot,now):
            f.owner.stop('source loss during AI verification')
            return lease(boot,now)
        f.provider.ai_lease=loss
        with self.assertRaises(ValueError):f.command()
        self.assertFalse(f.step().committed);self.assertEqual(0,f.provider.committed)

    def test_04_exact_observation_duplicate_cannot_extend_original_sample_age(self):
        f=self.f;f.activate();event=f.observe(sample=0)
        f.clock.value=1_100_000_000;f.owner.observe(event)
        f.command(duration=3000)
        f.clock.value=1_400_000_000;f.beat(seq=11,tick=101)
        f.clock.value=1_499_999_999
        good=f.step(dt=1);self.assertTrue(good.committed)
        f.clock.value=1_500_000_000
        bad=f.owner.step(expected_pose_revision=1,dt_ns=1)
        self.assertFalse(bad.committed);self.assertEqual(1,f.provider.committed)
        ROWS.append({'case':'exact_duplicate_original_age','last_ns_commit':good.committed,'cap_start_rejected':not bad.committed})

    def test_05_saved_successful_fence_cannot_be_reused_after_commit_returns(self):
        f=self.f;f.arm();saved=[]
        def commit(prepared,before_commit):
            saved.append(before_commit);fence=before_commit()
            f.provider.committed+=1
            return r.CommitReceipt(fence.boot,fence.command_seq,prepared[0]+1,fence.checked_ns,fence.step_end_ns)
        f.provider.commit_step=commit
        self.assertTrue(f.step().committed)
        with self.assertRaises(ValueError):saved[0]()
        f.clock.value+=1_000_000
        self.assertFalse(f.owner.step(expected_pose_revision=1,dt_ns=1).committed)
        self.assertEqual(1,f.provider.committed)

    def test_06_failed_fence_consumes_even_when_executor_suppresses_then_omits_retry(self):
        f=self.f;f.arm()
        def commit(prepared,before_commit):
            f.provider.live=False
            try:before_commit()
            except ValueError:pass
            f.provider.live=True
            return r.CommitReceipt(f.binding,3,1,f.clock.value,f.clock.value+prepared[1])
        f.provider.commit_step=commit
        result=f.step();self.assertFalse(result.committed);self.assertEqual(0,f.provider.committed)

    def test_07_last_four_eviction_never_restores_retired_sequence(self):
        f=self.f;f.activate();retired=f.observe(seq=9)
        for seq in range(10,14):f.clock.value+=1;f.observe(seq=seq)
        with self.assertRaises(ValueError):f.owner.observe(retired)
        self.assertFalse(f.step().committed);self.assertEqual(0,f.provider.committed)

    def test_08_invalid_event_during_geometry_prepare_vetoes_fence_even_if_caught(self):
        f=self.f;f.arm()
        def hook():
            try:f.owner.observe(None)
            except ValueError:pass
        f.provider.prepare_hook=hook
        self.assertFalse(f.step().committed);self.assertEqual(0,f.provider.committed)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentRuntime))
    (OUT/'independent_results.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'cases':ROWS},indent=2)+'\n',encoding='utf8')
    sys.exit(0 if result.wasSuccessful() else 1)

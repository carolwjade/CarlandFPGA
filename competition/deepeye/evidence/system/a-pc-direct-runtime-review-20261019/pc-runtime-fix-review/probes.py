"""Independent new BOOT transaction edges, deterministic fixtures only."""
from pathlib import Path
import json
import sys
import unittest
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'.local/deepeye-implementation-a'))
from competition.deepeye.tests.simulation import test_pc_direct_runtime as t
ROWS=[]

class BootBoundaryProbes(unittest.TestCase):
    def setUp(self):
        self.f=t.PcDirectRuntimeTests();self.f.setUp()

    def idle_nested(self,**arguments):
        f=self.f;f.activate()
        f.binding=f.boot_binding(generation=2,session=8)
        def verifier(event):
            result=f.owner.step(**arguments)
            self.assertFalse(result.committed)
            return event
        f.provider.verify_boot=verifier
        rejected=False
        try:f.owner.boot(f.binding)
        except ValueError:rejected=True
        try:f.beat();f.observe();f.command()
        except ValueError:pass
        result=f.step()
        ROWS.append({'case':'idle_nested_malformed_step','arguments':arguments,'boot_rejected':rejected,
                     'committed':result.committed,'fixture_commits':f.provider.committed,'reason':result.reason})
        self.assertFalse(result.committed,'invalid nested step skipped the BOOT veto generation')

    def test_invalid_duration_reentry_in_idle_boot_cannot_be_ignored(self):
        self.idle_nested(expected_pose_revision=0,dt_ns=0)

    def test_boolean_pose_revision_reentry_in_idle_boot_cannot_be_ignored(self):
        self.idle_nested(expected_pose_revision=False,dt_ns=1)

    def test_verified_proposal_with_activation_clock_error_cannot_replay(self):
        f=self.f
        def fail_clock():raise ValueError('fixture activation clock callback failed')
        def verifier(event):
            f.clock.on_read=fail_clock
            return event
        f.provider.verify_boot=verifier
        with self.assertRaises(ValueError):f.owner.boot(f.binding)
        f.provider.verify_boot=lambda event:event
        replay_rejected=False
        try:f.owner.boot(f.binding)
        except ValueError:replay_rejected=True
        try:f.beat();f.observe();f.command()
        except ValueError:pass
        result=f.step()
        ROWS.append({'case':'verified_proposal_activation_clock_error','same_binding_replay_rejected':replay_rejected,
                     'committed':result.committed,'fixture_commits':f.provider.committed,'reason':result.reason})
        self.assertTrue(replay_rejected,'valid verified proposal survived failed activation and replayed')
        self.assertFalse(result.committed)

    def test_newly_discovered_watchdog_timeout_aborts_once_then_fresh_boot_recovers(self):
        f=self.f;f.arm();f.clock.value=1_500_000_000
        abandoned=f.boot_binding(generation=2,session=8)
        with self.assertRaises(ValueError):f.owner.boot(abandoned)
        with self.assertRaises(ValueError):f.owner.boot(abandoned)
        f.binding=f.boot_binding(generation=3,session=9)
        f.owner.boot(f.binding);f.beat();f.observe();f.command()
        result=f.step()
        ROWS.append({'case':'timeout_abort_then_new_proposal','committed':result.committed,'fixture_commits':f.provider.committed})
        self.assertTrue(result.committed);self.assertEqual(1,f.provider.committed)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BootBoundaryProbes))
    (OUT/'new_probe_results.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),
       'errors':len(result.errors),'cases':ROWS},indent=2)+'\n',encoding='utf8')
    sys.exit(0 if result.wasSuccessful() else 1)

"""Public-wrapper binding and post-retirement activation edges, fixtures only."""
from pathlib import Path
import json
import sys
import unittest
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'.local/deepeye-implementation-a'))
from competition.deepeye.tests.simulation import test_pc_direct_runtime as t
ROWS=[]
METHODS=('boot','board','observe','command','stop','step')

def fixture():
    f=t.PcDirectRuntimeTests();f.setUp();f.activate()
    f.binding=f.boot_binding(generation=2,session=8)
    return f

class NewEntryProbes(unittest.TestCase):
    def test_reserved_self_keyword_cannot_bypass_public_guard(self):
        for name in METHODS:
            with self.subTest(method=name):
                f=fixture();caught=[]
                def verifier(event):
                    kwargs={'self':None}
                    if name=='step':kwargs.update(expected_pose_revision=0,dt_ns=1)
                    elif name=='stop':kwargs['reason']='operator STOP'
                    else:kwargs['event']=None
                    try:getattr(f.owner,name)(**kwargs)
                    except (TypeError,ValueError) as error:caught.append(type(error).__name__)
                    return event
                f.provider.verify_boot=verifier
                rejected=False
                try:f.owner.boot(f.binding)
                except ValueError:rejected=True
                try:f.beat();f.observe();f.command()
                except ValueError:pass
                result=f.step()
                ROWS.append({'case':'reserved_self_keyword','method':name,'caught':caught,'boot_rejected':rejected,
                             'committed':result.committed,'fixture_commits':f.provider.committed})
                self.assertFalse(result.committed,'wrapper call binding raised before recording veto')

    def test_duplicate_ordinary_arguments_are_converted_and_latched(self):
        for name in METHODS:
            with self.subTest(method=name):
                f=fixture();caught=[]
                def verifier(event):
                    try:
                        if name=='step':f.owner.step(0,expected_pose_revision=0,dt_ns=1)
                        elif name=='stop':f.owner.stop('STOP',reason='STOP')
                        else:getattr(f.owner,name)(None,event=None)
                    except (TypeError,ValueError) as error:caught.append(type(error).__name__)
                    return event
                f.provider.verify_boot=verifier
                with self.assertRaises(ValueError):f.owner.boot(f.binding)
                self.assertEqual(['ValueError'],caught)
                self.assertFalse(f.step().committed);self.assertEqual(0,f.provider.committed)
                ROWS.append({'case':'ordinary_duplicate_arguments','method':name,'latched':True})

    def test_guard_constructor_exception_retires_identity_but_new_handshake_recovers(self):
        f=fixture();original=t.runtime.watchdog.PcDirectWatchdog
        def rejected_guard(*args,**kwargs):raise RuntimeError('fixture guard construction failure')
        try:
            t.runtime.watchdog.PcDirectWatchdog=rejected_guard
            with self.assertRaises(ValueError):f.owner.boot(f.binding)
        finally:t.runtime.watchdog.PcDirectWatchdog=original
        with self.assertRaises(ValueError):f.owner.boot(f.binding)
        f.binding=f.boot_binding(generation=3,session=9)
        f.owner.boot(f.binding);f.beat();f.observe();f.command()
        self.assertTrue(f.step().committed);self.assertEqual(1,f.provider.committed)
        ROWS.append({'case':'guard_exception','old_replay_rejected':True,'fresh_recovery_commits':1})

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NewEntryProbes))
    (OUT/'new_probe_results.json').write_text(json.dumps({'tests':result.testsRun,'failing_assertions_or_subcases':len(result.failures),
       'errors':len(result.errors),'cases':ROWS},indent=2)+'\n',encoding='utf8')
    sys.exit(0 if result.wasSuccessful() else 1)

"""Pure fake actor harness review. No real ActorRegistry or native import.

Only the reviewed harness control flow runs; the registry/owner and policy
construction are completely replaced before forcing its interactive preflight.
"""
from pathlib import Path
from types import ModuleType,SimpleNamespace as N
from unittest.mock import patch
import importlib,sys,tempfile,json,unittest

from competition.deepeye.tests.isolation import test_actor_windows_live as h
from competition.deepeye.simulation.isolation import actor_fixture as f
import competition.deepeye.simulation.isolation as package

O=Path(__file__).resolve().parent
WITNESSES=[]

class FakeResources:
    def __init__(self):
        self.process=N(label='process',resource_id='original-process',native=42,terminal_confirmed=False)
        self.references=[self.process];self.profile=N(outcome=N(value='confirmed'));self.unresolved=[]
    def summary(self):return [{'label':'process','terminal_confirmed':self.process.terminal_confirmed}]

class FakeOwner:
    def __init__(self,mode):
        self.mode=mode;self._resources=FakeResources();self._process=self._original_process=self._resources.process
        self._original_native=42;self._primary_error=None;self._evidence_errors=[];self._cleanup_attempted=False
        self._cleanup_result=None;self._root=None;self.state='RUNNING_UNBOUND';self.instance_id='fake-only-original-owner'
        self._run_deadline=self._ready_deadline=0;self.polls=0
        self._backend=N(terminated=False,exit_codes={})
    def poll(self):
        self.polls+=1
        if self.polls==1:return
        if self.mode in ('natural','crash'):
            self._process.terminal_confirmed=True
            self._backend.exit_codes['original-process']=0 if self.mode=='natural' else 17
            self._primary_error=ValueError('original process terminal or life observation unknown')
            raise self._primary_error
        self._primary_error=ValueError('fixed actor/readiness/sample deadline expired')
        raise self._primary_error
    def close(self,reason):
        self._cleanup_attempted=True
        if self.mode=='unresolved':
            self.state='QUARANTINED';self._resources.unresolved=[self._process]
            self._cleanup_result=N(resources_complete=False);return
        if not self._process.terminal_confirmed:
            self._backend.terminated=True;self._backend.exit_codes['original-process']=0xdead
        self._process.terminal_confirmed=True;self._cleanup_result=N(resources_complete=True)
        self.state='QUARANTINED' if self._evidence_errors else 'CLOSED'

class Cases(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory(dir=O);self.root=Path(self.t.name);self.saved=list(h._ATTEMPTS);h._ATTEMPTS.clear()
    def tearDown(self):h._ATTEMPTS[:]=self.saved;self.t.cleanup()
    def fake_run(self,mode,case='retained-natural-exit',*,disk_failure=False,acquisition_failure=None,duplicate=False):
        attempt=self.root/(mode+'-'+case);attempt.mkdir();allow=self.root/(mode+'.allow.json')
        record={'attempt_directory':str(attempt),'staged_files':{'python.exe':'0'*64}}
        allow.write_text(json.dumps(record),encoding='utf-8')
        actor=ModuleType('competition.deepeye.simulation.isolation.actor_owner');created=[]
        actor.ActorPolicy=lambda *a,**kw:N()
        actor._persist=lambda owner:None
        class Registry:
            def __init__(self):self._owners=[];created.append(self)
            def launch(registry,policy):
                if acquisition_failure=='before':raise OSError('before owner returned')
                owner=FakeOwner(mode);registry._owners.append(owner)
                if acquisition_failure=='after':raise OSError('after owner retained')
                if case=='persistence-after-acquisition':
                    try:actor._persist(owner)
                    except BaseException as error:
                        owner._primary_error=error;owner._evidence_errors.append(error);raise
                return owner
        actor.ActorRegistry=Registry
        def reader(owner):
            def read(current):
                if mode=='reader_timeout' and current.polls>1:
                    current._primary_error=ValueError('fixture read exceeded explicit elapsed budget')
                    raise current._primary_error
                return f.READY if current.polls==1 else b''
            if mode=='reader_timeout':
                # The real _entry revokes, but does not clean up here. Cleanup
                # is performed by run_case's finally after classification.
                owner.poll=lambda: setattr(owner,'polls',owner.polls+1)
            return read
        original_save=h._save_new
        def save(path,value):
            if disk_failure and path.name=='fixture-memory-result.json':raise OSError('controlled report write failure')
            return original_save(path,value)
        if duplicate:(attempt/'execution-claimed.json').write_text('previous claim',encoding='utf-8')
        fake_sys=N(implementation=N(name='cpython'),version_info=(3,12),flags=N(interactive=1))
        import builtins
        original_import=builtins.__import__
        def safe_import(name,*args,**kwargs):
            if name.endswith('.isolation.win32') or name.endswith('.isolation.prototype'):
                raise AssertionError('native/stage import forbidden by independent review')
            if name.endswith('.isolation.actor_owner'):return actor
            return original_import(name,*args,**kwargs)
        with patch.dict(sys.modules,{actor.__name__:actor}),patch.object(package,'actor_owner',actor,create=True),\
                patch.object(h,'sys',fake_sys),patch.object(h,'validate_allow_record',lambda *a,**kw:record),\
                patch.object(h,'_fixture_reader',reader),patch.object(h,'_save_new',save),\
                patch.object(h.time,'sleep',lambda _:None),patch('builtins.__import__',safe_import):
            if duplicate:
                with self.assertRaises(FileExistsError):h.run_case(self.root,allow,case)
                self.assertEqual([],created);self.assertEqual([],h._ATTEMPTS);return None
            result=h.run_case(self.root,allow,case)
        self.assertIs(result,h._ATTEMPTS[-1]);self.assertIs(result.registry,created[0])
        if result.actor is not None:self.assertIs(result.actor,result.registry._owners[-1])
        witness={'mode':mode,'case':case,'passed':result.passed,'unresolved':result.unresolved,
            'primary':None if result.primary is None else str(result.primary),'cleanup':result.cleanup,
            'backend':None if result.actor is None else vars(result.actor._backend),'events':result.events,
            'persisted_result':json.loads((attempt/'fixture-memory-result.json').read_text('utf-8')) if (attempt/'fixture-memory-result.json').exists() else None,
            'strong_original_roots_retained':result is h._ATTEMPTS[-1] and result.registry is created[0]}
        WITNESSES.append(witness)
        return result

    def test_ready_then_nonzero_crash_is_not_successful_natural_exit(self):
        result=self.fake_run('crash')
        self.assertFalse(result.passed,'nonzero exit17 after READY was classified passed')

    def test_ready_then_reader_fault_kill_is_not_successful_natural_exit(self):
        result=self.fake_run('reader_timeout')
        self.assertFalse(result.passed)
        self.assertTrue(result.actor._backend.terminated)
        self.assertIs(result.primary,result.actor._primary_error)

    def test_normal_zero_exit_baseline_and_expiry_expected_semantics(self):
        self.assertTrue(self.fake_run('natural').passed)
        self.assertTrue(self.fake_run('expiry','fixed-unbound-expiry').passed)

    def test_expected_persistence_failure_keeps_original_primary_and_quarantine(self):
        result=self.fake_run('persistence','persistence-after-acquisition')
        self.assertTrue(result.passed);self.assertIs(result.primary,result.actor._primary_error)
        self.assertEqual('QUARANTINED',result.actor.state);self.assertTrue(result.actor._evidence_errors)
        self.assertFalse(result.unresolved)

    def test_result_write_failure_changes_memory_pass_and_retains_owner(self):
        result=self.fake_run('natural',disk_failure=True)
        self.assertFalse(result.passed);self.assertTrue(result.events[-1].get('memory_result_persistence_error'))

    def test_unknown_cleanup_retains_owner_and_stops_next_campaign(self):
        result=self.fake_run('unresolved')
        self.assertTrue(result.unresolved);self.assertFalse(result.passed)
        fake_sys=N(implementation=N(name='cpython'),version_info=(3,12),flags=N(interactive=1))
        with patch.object(h,'sys',fake_sys),patch.object(h,'_ordinary',side_effect=AssertionError('must stop before files/native')):
            with self.assertRaisesRegex(RuntimeError,'unresolved original ownership'):h.run_case(self.root,self.root/'absent','retained-natural-exit')
        self.assertIs(result.actor,result.registry._owners[-1])

    def test_before_after_acquisition_errors_keep_original_recovery_roots(self):
        for when in ('before','after'):
            with self.subTest(when=when):
                h._ATTEMPTS.clear();result=self.fake_run(when,acquisition_failure=when)
                self.assertFalse(result.passed);self.assertIsInstance(result.primary,OSError)
                self.assertEqual(when=='before',result.unresolved)

    def test_claim_replay_stops_before_fake_registry_creation(self):self.fake_run('duplicate',duplicate=True)

    def test_original_reader_continuity_elapsed_and_retirement_checks(self):
        for fault in ('none','endpoint','process','retire','slow'):
            with self.subTest(fault=fault):
                endpoint=N(native=51,attempted=False,ambiguous=False,release='kernel')
                process=object();calls=[];clock=iter((10,30 if fault=='slow' else 11))
                owner=N(_epoch=1,_policy=N(max_probe_ns=20),_time=lambda:next(clock))
                owner._resources=N(find=lambda label:endpoint,owns=lambda ref:ref is endpoint)
                def checkpoint(epoch):
                    if fault=='retire':raise ValueError('retired during read')
                owner._checkpoint=checkpoint
                def output(native):
                    self.assertEqual(51,native);calls.append('consumed');return f.READY
                owner._api=N(available_output=output)
                actor=ModuleType('competition.deepeye.simulation.isolation.actor_owner');actor._entry=lambda fn:fn
                life=ModuleType('competition.deepeye.simulation.isolation.actor_lifetime')
                refs=[process,object() if fault=='process' else process]
                life._reference=lambda who:refs.pop(0)
                life._sample=lambda who:calls.append('sample')
                with patch.dict(sys.modules,{actor.__name__:actor,life.__name__:life}):
                    reader=h._fixture_reader(owner)
                    if fault=='endpoint':endpoint.native=52
                    if fault=='none':self.assertEqual(f.READY,reader(owner));self.assertEqual(['sample','consumed','sample'],calls)
                    else:
                        with self.assertRaises(ValueError):reader(owner)
                        self.assertEqual([] if fault=='endpoint' else ['sample','consumed'],calls)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    (O/'independent-witnesses.json').write_text(json.dumps(WITNESSES,indent=2)+'\n',encoding='utf-8')
    assert not any(n.endswith('.isolation.win32') for n in sys.modules)
    raise SystemExit(0 if result.wasSuccessful() else 1)

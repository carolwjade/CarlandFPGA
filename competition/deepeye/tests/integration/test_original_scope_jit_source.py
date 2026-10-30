import sys,unittest
from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal
try:
    from competition.deepeye.simulation.authority import _root_jit_kernel as jit
except ImportError: jit=None

class NewJitIntegrationControls(unittest.TestCase):
    def test_default_selection_does_not_import_numba(self):
        self.assertFalse(causal.select_jit_kernel_profile({}))
        self.assertNotIn('numba',sys.modules)
    def test_explicit_profile_requires_exact_shape(self):
        self.assertTrue(causal.select_jit_kernel_profile({'source_kernel_profile':{'name':'root_strict_jit_ordered_kernel_v1'}}))
        for x in ('unknown',None,{'name':'root_strict_jit_ordered_kernel_v1','extra':1}):
            with self.assertRaises(ValueError):causal.select_jit_kernel_profile({'source_kernel_profile':x})
    def test_freeze_policy_mismatch_and_cross_epoch_are_refused(self):
        from competition.deepeye.simulation.authority import _world_values as values
        owner=object.__new__(loop._RootWorldOwner)
        epoch=loop._FrozenEpoch(owner,1,'request-1',{},b'',None,0,'0'*64)
        other=loop._FrozenEpoch(owner,2,'request-2',{},b'',None,0,'1'*64)
        owner._epoch=epoch;owner._epochs={id(epoch):epoch,id(other):other};owner._retired_epochs=set()
        policy=values.ValuePolicy(*(['0'*64]*5),(),(),(),run_id='test')
        with self.assertRaises(loop.WorldRejected):loop._require_epoch_policy(owner,epoch,policy)
        with self.assertRaises(loop.WorldRejected):loop._require_epoch_policy(owner,other,policy)
        malformed=loop._FrozenEpoch(owner,3,'request-3',{},b'',None,0,'bad')
        owner._epoch=malformed;owner._epochs[id(malformed)]=malformed
        with self.assertRaises(loop.WorldRejected):loop._require_epoch_policy(owner,malformed,policy)
    def test_malformed_policy_refused_before_executor_or_send(self):
        import threading
        from types import SimpleNamespace
        from competition.deepeye.simulation.authority import _world_values as values
        owner=object.__new__(loop._RootWorldOwner);owner._thread=threading.get_ident();owner._foreign=threading.Event()
        owner._busy=False;owner._vetoed=False;calls=[]
        owner._binding=SimpleNamespace(executor=SimpleNamespace(revoke=lambda reason:calls.append('revoke')))
        owner._native=SimpleNamespace(run_id='test',send=lambda *a,**k:calls.append('send'))
        epoch=loop._FrozenEpoch(owner,1,'request',{},b'',None,0,'0'*64)
        owner._epoch=epoch;owner._epochs={id(epoch):epoch};owner._retired_epochs=set()
        policy=values.ValuePolicy(*(['0'*64]*5),(),(),(),run_id='test')
        with self.assertRaises(loop.WorldRejected):owner.construct_and_bind(epoch,policy,initial_pose=None)
        with self.assertRaises(loop.WorldRejected):owner.request_freeze(snapshot_limits_sha256='0'*64,model_policy_sha256='bad')
        self.assertEqual(calls,[]);self.assertFalse(owner._vetoed);self.assertFalse(owner._busy)
    def test_explicit_twenty_record_budget_and_source_paths(self):
        from competition.deepeye.tools import run_owned_chain_headless as runner
        profile={'name':'root_strict_jit_ordered_kernel_v1'}
        self.assertEqual(20,runner._source_record_budget({'sample_records':20,'source_kernel_profile':profile}))
        with self.assertRaises(ValueError):runner._source_record_budget({'sample_records':20})
        with self.assertRaises(ValueError):runner._source_record_budget({'sample_records':21,'source_kernel_profile':profile})
        with self.assertRaises(ValueError):causal.source_paths(True)
        cfg=dict(dependency_path='a',dependency_files=[['numba/example.py','0'*64]],numpy_path='b',numpy_files=[['numpy/example.py','0'*64]])
        paths=causal.source_paths(True,cfg)
        self.assertIn('root_jit_kernel',paths);self.assertIn('jitdep:numba/example.py',paths)
        self.assertNotIn('numba',sys.modules)
    def test_backend_refuses_nonoriginal_scope(self):
        self.assertIsNotNone(jit,'new Root private JIT helper missing')
        with self.assertRaises((TypeError,ValueError)):jit._make_original_backend(None)


import hashlib,random,threading,json
from pathlib import Path
from types import SimpleNamespace
from competition.deepeye.simulation.authority import _world_loop as loop, motion_executor as motion
from competition.deepeye.simulation.authority.motion import solid_clearance as geom
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.simulation.sensors import forward_profile as f

class _Clock:
    software_fixture_only=True
    def __init__(self):self.now=1_000_000_000
    def _check(self):pass
    def __call__(self):return self.now

class _World:
    software_fixture_only=True
    _known_epoch=loop._RootWorldOwner._known_epoch
    _known_binding=loop._RootWorldOwner._known_binding
    def __init__(self,clock,kind,centre,position):
        self._test=True;self._clock=clock;self._thread=threading.get_ident();self._busy=False
        self._em_scope_active=None;self._foreign=threading.Event();self._vetoed=False
        self._veto_generation=0;self._initialized=True;self._publication=None
        self._native=SimpleNamespace(clock_binding=clock,_containment_deadline=5_000_000_000,_retired=False,state='AUTHENTICATED')
        solid=geom.Solid('one','v1',kind,centre,(1,1,1),(0,0,0,1))
        scene=geom.Scene('fixture','v1',(('rock',('one',)),),(geom.SceneObject('rock','hard_rock',(solid,)),))
        ex=object.__new__(motion.OwnedMotionExecutor);ex._owner=self._thread;ex._busy=False;ex._pending={};ex._scene=scene;ex._world_binding='fixture'
        pose=SimpleNamespace(position_m=position,orientation_xyzw=(0.,0.,0.,1.))
        phase=SimpleNamespace(context=SimpleNamespace(run_id='fixture',epoch=1))
        ex._root=motion._Root(0,0,pose,0,phase,None,None,None,True,False,False,0);self.executor=ex
        self._epoch=loop._FrozenEpoch(self,1,'fixture',{'freeze_id':'fixture'},b'',None,0)
        self._epochs={id(self._epoch):self._epoch};self._retired_epochs=set()
        self._binding=loop._Binding(self,self._epoch,SimpleNamespace(scene=scene),ex,0,1)
        self._bindings={id(self._binding):self._binding};self._status=dict(identity=self._epoch.identity,state='BOUND_STOPPED')
        self._native_observation=SimpleNamespace(alive=True)
    def poll(self):return 'BOUND_STOPPED'

def _records(root,names):
    out=[]
    for name in names:
        for p in sorted((root/name).rglob('*')):
            if p.is_file():out.append([p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()])
    return out

class ZSoftwareJitControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work=Path(__file__).resolve().parents[4]
        cls.root=Path(r'C:\Users\CarlJade\Documents\ChatGPT\FPGA多机协作开发')
        dep=cls.root/'.local/deepeye-jit-kernel-deps-20261030'
        np=Path(sys.executable).resolve().parent/'Lib/site-packages'
        cls.config=dict(dependency_path=str(dep),dependency_files=_records(dep,('numba','numba-0.68.0.dist-info','llvmlite','llvmlite-0.50.0.dist-info','llvmlite.libs','bin')),
            numpy_path=str(np),numpy_files=_records(np,('numpy','numpy-2.3.5.dist-info','numpy.libs')))
        bad=dict(cls.config); bad['dependency_files']=[x[:] for x in cls.config['dependency_files']];bad['dependency_files'][0][1]='0'*64
        with cls.assertRaisesClass(ValueError):jit.verify_dependencies(bad,cls.root,cls.work)
        if 'numba' in sys.modules:raise AssertionError('unverified package loaded')
        cls.verified=jit.verify_dependencies(cls.config,cls.root,cls.work)
        jit.load_verified(cls.verified); info=jit.warm(cls.verified)
        print('SOFTWARE_READONLY_WARM='+json.dumps(info,sort_keys=True),flush=True)
    @classmethod
    def assertRaisesClass(cls,exc):return unittest.TestCase().assertRaises(exc)
    def setup_fixture(self,kind='box',centre=(10,0,0),position=(0.,0.,0.)):
        clock=_Clock();world=_World(clock,kind,centre,position)
        field=OwnedWorldField(world.executor,material_sigma=dict(casing=None,fault=.02,void=None,water=.1,hard_rock=.01),background_sigma=.005,max_pieces=1)
        source=causal.CausalSourcePump(field.pose_reader,field.sample_sigma)
        factory=loop._make_software_em_scope_factory_for_test(world,world._binding,field,source)
        source._em_scope_factory=factory
        backend=jit._make_software_backend_for_test(factory,self.verified)
        source._profile._em_rng=random.Random(6901);source._profile._vibration_rng=random.Random(6902)
        source.start(clock.now,clock);source._last_tick=0;source._count=1;source._high=clock.now;source._polling=True
        return clock,world,field,source,factory,backend
    def test_original_payload_and_rng_with_compiled_and_cylinder_fallback(self):
        for kind in ('box','cylinder'):
            clock,world,field,source,factory,backend=self.setup_fixture(kind)
            reference=f.ForwardProfile(em_rng=random.Random(6901),vibration_rng=random.Random(6902))
            pose=field.pose_reader()
            reference.acquire_em(0,pose,context='formation',sampler=field._sample_sigma_pure)
            signatures=tuple(backend._core._run.signatures)
            with factory.begin(0) as scope:backend.acquire(0,pose,'formation',scope)
            self.assertEqual(signatures,tuple(backend._core._run.signatures))
            self.assertEqual(reference.sample_adc(0).to_payload(),source._profile.sample_adc(0).to_payload())
            self.assertEqual(reference._em_rng.getstate(),source._profile._em_rng.getstate())
            self.assertEqual(reference._vibration_rng.getstate(),source._profile._vibration_rng.getstate())
            self.assertIs(backend._acquire.__code__,f.ForwardProfile.acquire_em.__code__)
            self.assertIs(source._profile.sample_adc.__func__,f.ForwardProfile.sample_adc)
    def test_nonactive_replay_and_foreign_refused(self):
        clock,world,field,source,factory,backend=self.setup_fixture()
        with self.assertRaises(RuntimeError):
            with factory.begin(0) as scope:
                errors=[]
                thread=threading.Thread(target=lambda: self._foreign(backend,scope,field,errors));thread.start();thread.join()
                self.assertEqual(len(errors),1)
        self.assertTrue(factory._fault.is_set());self.assertEqual(source.state,'FAILED')
    @staticmethod
    def _foreign(backend,scope,field,errors):
        try:backend.acquire(0,f.Pose((0.,0.,0.),(0.,0.,0.,1.)),'formation',scope)
        except Exception as e:errors.append(e)
    def test_array_tamper_and_wrong_source_slot_fail(self):
        for mode in ('tamper','slot'):
            clock,world,field,source,factory,backend=self.setup_fixture()
            with self.assertRaises(ValueError):
                with factory.begin(0) as scope:
                    if mode=='tamper':backend._rows.flags.writeable=True;backend._rows[0,0]=42.
                    else:source._last_tick=10
                    backend.acquire(0,f.Pose((0.,0.,0.),(0.,0.,0.,1.)),'formation',scope)
            self.assertTrue(factory._fault.is_set())
    def test_subnormal_status_falls_back_original_in_same_scope(self):
        clock,world,field,source,factory,backend=self.setup_fixture(position=(5e-324,0.,0.))
        pose=field.pose_reader();reference=f.ForwardProfile(em_rng=random.Random(6901),vibration_rng=random.Random(6902))
        reference.acquire_em(0,pose,context='formation',sampler=field._sample_sigma_pure)
        args=backend._prepared;np=backend._np
        status,_,_=backend._run(backend._rows,np.asarray(pose.position_m),np.asarray(f._rotation_matrix(pose.orientation_xyzw)),*args[2:],field._background,field._epsilon)
        self.assertEqual(status,2)
        with factory.begin(0) as scope:backend.acquire(0,pose,'formation',scope)
        self.assertEqual(reference.sample_adc(0).to_payload(),source._profile.sample_adc(0).to_payload())
        self.assertEqual(reference._em_rng.getstate(),source._profile._em_rng.getstate())
    def test_mismatched_pose_is_rejected_before_profile_acquire(self):
        clock,world,field,source,factory,backend=self.setup_fixture()
        with self.assertRaises(ValueError):
            with factory.begin(0) as scope:backend.acquire(0,f.Pose((1.,0.,0.),(0.,0.,0.,1.)),'formation',scope)
        self.assertIsNone(source._profile._last_em_tick)
    def test_first_boundary_returns_none_without_em_noise(self):
        clock,world,field,source,factory,backend=self.setup_fixture(centre=(1,0,0))
        before=source._profile._em_rng.getstate();pose=field.pose_reader()
        with factory.begin(0) as scope:backend.acquire(0,pose,'formation',scope)
        self.assertFalse(source._profile._em_attempt_ok)
        self.assertEqual(before,source._profile._em_rng.getstate())
    def test_replay_veto_and_root_change_are_refused(self):
        from dataclasses import replace
        for mode in ('replay','veto','root'):
            clock,world,field,source,factory,backend=self.setup_fixture()
            with self.assertRaises((ValueError,RuntimeError)):
                with factory.begin(0) as scope:
                    pose=field.pose_reader()
                    if mode=='replay':backend.acquire(0,pose,'formation',scope)
                    elif mode=='veto':world._vetoed=True
                    else:world.executor._root=replace(world.executor._root,revision=1)
                    backend.acquire(0,pose,'formation',scope)
            self.assertTrue(factory._fault.is_set())
    def test_primary_error_and_book_partial_preserved(self):
        clock,world,field,source,factory,backend=self.setup_fixture()
        source._last_tick=None;source._count=0;source._polling=False
        class Book:
            def __init__(self):self.partial=None;self.failed=False
            def open_sample(self,tick,now):self.partial={'tick':tick};return self.partial
            def read_pose(self,token,kind='em'):return field.pose_reader()
            def fail(self,why):self.failed=True
        book=Book();source._source_book=book;source._jit_backend=backend
        original=backend._core._run;err=RuntimeError('test fixed numerical failure')
        def fail(*args):raise err
        backend._core._run=fail;backend._run=fail
        try:
            with self.assertRaises(RuntimeError) as caught:source.poll()
            self.assertIs(caught.exception,err)
            self.assertTrue(book.failed);self.assertEqual(book.partial,{'tick':0})
            self.assertEqual(source.state,'FAILED');self.assertTrue(factory._fault.is_set())
        finally:backend._core._run=original;backend._run=original
    def test_software_factory_cannot_become_production(self):
        *_,factory,backend=self.setup_fixture()
        with self.assertRaises(TypeError):jit._make_original_backend(factory,self.verified)
        with self.assertRaises(ValueError):backend._source.bind_original_jit_backend(backend)

if __name__=='__main__':unittest.main(verbosity=2)

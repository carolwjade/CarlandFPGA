import json, pathlib, sys, unittest, random, threading, os, hashlib
from types import SimpleNamespace
from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal
from competition.deepeye.simulation.authority import _root_jit_kernel as jit

class AA_Default(unittest.TestCase):
    def test_default_does_not_load_jit_packages(self):
        self.assertFalse(causal.select_jit_kernel_profile({}))
        self.assertNotIn('numba',sys.modules)

class ZLockedSignature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w=pathlib.Path(__file__).resolve().parents[4]
        cls.r=pathlib.Path(r'C:\Users\CarlJade\Documents\ChatGPT\FPGA多机协作开发')
        base=cls.r/'.planning/deepeye-resume-20261018/gen4-functional-chain-offboard-20261030-07'
        cfg=json.loads((base/'original-scope-jit-source-integration/proposed-operation-70/dependency-manifest-snapshot.json').read_text(encoding='utf-8-sig'))
        cls.v=jit.verify_dependencies(cfg,cls.r,cls.w);jit.load_verified(cls.v);cls.warm=jit.warm(cls.v)
        print('LOCKED_WARM='+json.dumps(cls.warm,sort_keys=True),flush=True)
        out=pathlib.Path(os.environ['JIT_LOCK_ARTIFACT_DIR']);out.mkdir(exist_ok=False)
        ir=cls.v.modules[1]._run.inspect_llvm(cls.v._signature);asm=cls.v.modules[1]._run.inspect_asm(cls.v._signature)
        assert hashlib.sha256(ir.encode()).hexdigest()==cls.warm['llvm_sha256']
        assert hashlib.sha256(asm.encode()).hexdigest()==cls.warm['asm_sha256']
        (out/'readonly-signature.ll').write_bytes(ir.encode('utf8'));(out/'readonly-signature.asm').write_bytes(asm.encode('utf8'))
        cls.np,cls.core=cls.v.modules
        from competition.deepeye.simulation.authority import _world_values as values
        from competition.deepeye.simulation.authority.motion.kinematics import RigidState
        from competition.deepeye.simulation.authority.motion_executor import OwnedMotionExecutor
        from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
        from competition.deepeye.simulation.sensors import forward_profile as f
        from competition.deepeye.tools.run_owned_chain_headless import _policy
        folder=base/'book-source-attempt-01';plan=json.loads((folder/'owned-world-plan-02.json').read_text(encoding='utf8'))
        snap=values.snapshot_from_wire((folder/'native-runs/source-01/original-snapshot.json').read_bytes())
        hist=json.loads((folder/'native-runs/source-01/result.json').read_text(encoding='utf8'))
        p=hist['initial_pose'];pose=RigidState(tuple(p['position_m']),tuple(p['orientation_xyzw']),0.)
        catalog=json.loads(pathlib.Path(plan['source_catalog_path']).read_text(encoding='utf8'))
        policy=_policy(pathlib.Path(plan['project_path']),catalog,dict(plan['project_files']),plan['source_bundle_sha256'],plan['run_id'])
        built=values._construct_values(snap,policy,pose,initial_monotonic_ns=0)
        ex=OwnedMotionExecutor(initial_state=built.initial_state,scene=built.scene,model=built.model,budget=built.budget)
        cls.field=OwnedWorldField(ex,**plan['field_policy']);cls.pose=f.Pose(pose.position_m,pose.orientation_xyzw);cls.f=f
        prep=cls.core._prepare(cls.field._pieces,cls.field._background,cls.field._epsilon)
        def frozen(a):return cls.np.frombuffer(a.tobytes(),dtype=a.dtype).reshape(a.shape)
        rows=frozen(cls.np.asarray(f._weight_table()[:2],dtype=cls.np.float64))
        arr=tuple(frozen(a) for a in prep[2:])
        cls.args=(rows,cls.np.asarray(cls.pose.position_m,dtype=cls.np.float64),cls.np.asarray(f._rotation_matrix(cls.pose.orientation_xyzw),dtype=cls.np.float64),*arr,cls.field._background,cls.field._epsilon)
        cls.objects=len(built.scene.objects);cls.pieces=len(cls.field._pieces)
    def test_actual_complete_field_has_exact_scanned_types(self):
        self.assertEqual((2,2),(self.objects,self.pieces))
        self.assertIsNotNone(self.v._signature)
        self.assertIs(jit._guard_arguments(self.v,self.args),self.v._entry)
    def test_incompatible_array_shapes_layout_dtype_and_alignment_are_refused(self):
        np=self.np;original=self.args
        bad=[original[0].astype(np.float32),np.zeros((2,16))[:,::2],np.ndarray((2,8),dtype=np.float64,buffer=bytearray(129),offset=1)]
        for value in bad:
            if value.flags.writeable:value.flags.writeable=False
            with self.assertRaises((ValueError,TypeError)):jit._guard_arguments(self.v,(value,*original[1:]))
        with self.assertRaises((ValueError,TypeError)):jit._guard_arguments(self.v,(np.zeros((2,8)),*original[1:]))
        with self.assertRaises((ValueError,TypeError)):jit._guard_arguments(self.v,(original[0],original[1][::2],*original[2:]))
    def test_dispatcher_is_locked_and_entry_does_not_specialize(self):
        before=tuple(self.core._run.signatures)
        entry=jit._guard_arguments(self.v,self.args);self.assertIs(entry,self.v._entry)
        self.assertFalse(self.core._run._can_compile)
        entry(*self.args)
        self.assertEqual(before,tuple(self.core._run.signatures))
        with self.assertRaises(TypeError) as caught:self.core._run(self.args[0].astype(self.np.float32),*self.args[1:])
        print('COMPILE_DISABLED='+str(caught.exception),flush=True)
        with self.assertRaises(ValueError):jit.warm(self.v)
        self.assertEqual(before,tuple(self.core._run.signatures))
    def test_dispatcher_replacement_is_rejected(self):
        old=self.core._run
        try:
            self.core._run=lambda *a:None
            with self.assertRaises(ValueError):jit._guard_arguments(self.v,self.args)
        finally:self.core._run=old




class _Clock:
    software_fixture_only=True
    def __init__(self): self.now=1_000_000_000
    def _check(self):pass
    def __call__(self):return self.now

class _World:
    software_fixture_only=True
    _known_epoch=jit.loop._RootWorldOwner._known_epoch
    _known_binding=jit.loop._RootWorldOwner._known_binding
    def __init__(self,clock,kind,position):
        from competition.deepeye.simulation.authority import _world_loop as loop, motion_executor as motion
        from competition.deepeye.simulation.authority.motion import solid_clearance as geom
        self._test=True;self._clock=clock;self._thread=threading.get_ident();self._busy=False
        self._em_scope_active=None;self._foreign=threading.Event();self._vetoed=False
        self._veto_generation=0;self._initialized=True;self._publication=None
        self._native=SimpleNamespace(clock_binding=clock,_containment_deadline=5_000_000_000,_retired=False,state='AUTHENTICATED')
        piece=geom.Solid('one','v1',kind,(10,0,0),(1,1,1),(0,0,0,1))
        scene=geom.Scene('fixture','v1',(('rock',('one',)),),(geom.SceneObject('rock','hard_rock',(piece,)),))
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

def _fixture(verified,kind,position=(0.,0.,0.)):
    from competition.deepeye.simulation.authority import _world_loop as loop
    from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
    clock=_Clock();world=_World(clock,kind,position)
    field=OwnedWorldField(world.executor,material_sigma=dict(casing=None,fault=.02,void=None,water=.1,hard_rock=.01),background_sigma=.005,max_pieces=1)
    source=causal.CausalSourcePump(field.pose_reader,field.sample_sigma)
    factory=loop._make_software_em_scope_factory_for_test(world,world._binding,field,source);source._em_scope_factory=factory
    backend=jit._make_software_backend_for_test(factory,verified)
    source._profile._em_rng=random.Random(7201);source._profile._vibration_rng=random.Random(7202)
    source.start(clock.now,clock);source._last_tick=0;source._count=1;source._high=clock.now;source._polling=True
    return field,source,factory,backend

class ZZBoundEntry(unittest.TestCase):
    # Reuse only this module's fresh fixture setup, not an old test class.
    @classmethod
    def setUpClass(cls):
        cls.v=ZLockedSignature.v;cls.core=ZLockedSignature.core;cls.f=ZLockedSignature.f;cls.args=ZLockedSignature.args;cls.np=ZLockedSignature.np
    def test_original_codeobject_and_cylinder_fallback_no_new_signature(self):
        for kind in ('box','cylinder'):
            field,source,factory,backend=_fixture(self.v,kind);pose=field.pose_reader()
            ref=self.f.ForwardProfile(em_rng=random.Random(7201),vibration_rng=random.Random(7202))
            ref.acquire_em(0,pose,context='formation',sampler=field._sample_sigma_pure)
            before=tuple(self.core._run.signatures)
            with factory.begin(0) as scope:backend.acquire(0,pose,'formation',scope)
            self.assertIs(backend._acquire.__code__,self.f.ForwardProfile.acquire_em.__code__)
            self.assertEqual(ref.sample_adc(0).to_payload(),source._profile.sample_adc(0).to_payload())
            self.assertEqual(ref._em_rng.getstate(),source._profile._em_rng.getstate())
            self.assertEqual(ref._vibration_rng.getstate(),source._profile._vibration_rng.getstate())
            print('RNG_STATE_'+kind+'='+hashlib.sha256(repr((ref._em_rng.getstate(),ref._vibration_rng.getstate())).encode()).hexdigest(),flush=True)
            self.assertEqual(before,tuple(self.core._run.signatures))
    def test_numeric_status2_falls_back_without_specialization(self):
        field,source,factory,backend=_fixture(self.v,'box',(5e-324,0.,0.));pose=field.pose_reader()
        ref=self.f.ForwardProfile(em_rng=random.Random(7201),vibration_rng=random.Random(7202))
        ref.acquire_em(0,pose,context='formation',sampler=field._sample_sigma_pure)
        args=(backend._rows,self.np.asarray(pose.position_m),self.np.asarray(self.f._rotation_matrix(pose.orientation_xyzw)),*backend._prepared[2:],field._background,field._epsilon)
        before=tuple(self.core._run.signatures)
        status,_,_=jit._guard_arguments(self.v,args)(*args)
        self.assertEqual(status,2)
        with factory.begin(0) as scope:backend.acquire(0,pose,'formation',scope)
        self.assertEqual(ref.sample_adc(0).to_payload(),source._profile.sample_adc(0).to_payload())
        self.assertEqual(ref._em_rng.getstate(),source._profile._em_rng.getstate())
        self.assertEqual(before,tuple(self.core._run.signatures))
    def test_same_bytes_new_array_identity_is_refused(self):
        field,source,factory,backend=_fixture(self.v,'box')
        backend._rows=self.np.frombuffer(backend._rows.tobytes(),dtype=self.np.float64).reshape(backend._rows.shape)
        with self.assertRaises(ValueError):
            with factory.begin(0) as scope:backend.acquire(0,field.pose_reader(),'formation',scope)
        self.assertTrue(factory._fault.is_set())
    def test_unsupported_field_also_checks_locked_entry(self):
        field,source,factory,backend=_fixture(self.v,'cylinder')
        backend._entry=lambda *a:None
        with self.assertRaises(ValueError):
            with factory.begin(0) as scope:backend.acquire(0,field.pose_reader(),'formation',scope)
        self.assertTrue(factory._fault.is_set())
    def test_reentrant_scope_and_changed_entry_refused(self):
        field,source,factory,backend=_fixture(self.v,'box')
        with self.assertRaises(ValueError):
            with factory.begin(0) as scope:
                backend._active=scope
                backend.acquire(0,field.pose_reader(),'formation',scope)
        self.assertTrue(factory._fault.is_set())
        before=self.v._entry
        try:
            self.v._entry=lambda *a:None
            with self.assertRaises(ValueError):jit._guard_arguments(self.v,self.args)
        finally:self.v._entry=before

if __name__=='__main__':unittest.main(verbosity=2)

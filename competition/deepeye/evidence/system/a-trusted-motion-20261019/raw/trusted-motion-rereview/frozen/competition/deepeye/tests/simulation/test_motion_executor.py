"""Owned numeric transactions; fixtures below do NOT authenticate live sources."""
import importlib
import json
import unittest
from unittest.mock import patch
from dataclasses import replace, FrozenInstanceError
from fractions import Fraction as F

from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt
from competition.deepeye.simulation.authority.motion import passage_phase as p
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
from competition.deepeye.simulation.authority.motion import certified_path as cp
from competition.deepeye.simulation.authority.motion import solid_clearance as s
from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
try:
    m=importlib.import_module('competition.deepeye.simulation.authority.motion_executor')
except ModuleNotFoundError as exc:
    if exc.name!='competition.deepeye.simulation.authority.motion_executor':raise
    m=None

DT=10_000_000


class MotionExecutorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m,'owned motion executor not implemented')
        self.f=rt.PcDirectRuntimeTests();self.f.setUp();self.event=self.f.arm(duration=1000)
        self.body=w.Envelope(.4,.12,.52,'explicit numerical fixture, not calibrated B asset',False)
        self.ctx=p.RunContext('run-1','fixture-scene',1,w.Layout(g.Gate('front',0,0),g.Gate('back',0,0)),self.body,'test authority only')
        self.model=s.CapsuleModel('fixture-body','v1',.4,.12,.52)
        self.scene=s.Scene('fixture-scene','v1',(),())
        self.budget=m.GeometryBudget(0,0,0,'explicit exact fixture; no live engine/asset claim')

    def make(self,position=(0,0,15.6),*,speed=.25,scene=None,state=None,limits=None,max_slices=16,budget=None):
        state=state or p.initialize(self.ctx,RigidState(position,(0,1,0,0),speed),gc.ErrorBounds(0.,0.,0.),
            pose_revision=0,monotonic_ns=0,error_budget_reference='exact fixture initialization').state
        ex=m.OwnedMotionExecutor(initial_state=state,scene=scene or self.scene,model=self.model,
            budget=budget or self.budget,limits=limits or s.Limits(),max_slices=max_slices)
        ex.activate_boot(self.f.binding)
        ex.admit_command(self.f.binding,self.event.raw)
        return ex

    def raw(self,**target):
        doc=json.loads(self.event.raw);doc['target'].update(target)
        doc['command_seq']=4;doc['candidate_id']=4
        return rt.encode(doc)

    def prepare(self,ex,dt=DT):return ex.prepare_step(self.f.binding,ex.admitted_raw,ex.renderer_view().pose_revision,dt)
    def fence(self,start=1_000_000_000,dt=DT,deadline=1_400_000_000):
        return rt.runtime.StepFence(self.f.binding,3,start,start+dt,deadline)

    def seeded(self,phase,position):
        # Explicit internal numerical phase fixture only; not an imported runtime history.
        initial=p.initialize(self.ctx,RigidState((0,0,15.6),(0,1,0,0),.25),gc.ErrorBounds(0.,0.,0.),
            pose_revision=0,monotonic_ns=0,error_budget_reference='seeded phase fixture').state
        kinds=['INITIAL_OUTSIDE','ENTRY_WINDOW']
        if phase!='ENTRY_CROSSING':kinds+=['ENTERED']
        if phase=='EXIT_CROSSING':kinds+=['EXIT_WINDOW']
        history=tuple(p.Event(k,i,i,i,'explicit seeded numerical event') for i,k in enumerate(kinds))
        return p._state(context=self.ctx,pose=RigidState(position,(0,1,0,0),.25),errors=initial.errors,
            speed_error_upper=F(0),error_budget_reference='seeded numeric phase only',pose_revision=5,
            monotonic_ns=10,phase=phase,entered=phase!='ENTRY_CROSSING',history=history,trace_hash='seeded numerical chain')

    def test_T01_prepare_never_publishes_pose_or_phase(self):
        ex=self.make();before=ex.authority_snapshot();self.prepare(ex)
        self.assertIs(before,ex.authority_snapshot());self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_T02_actual_final_interval_maps_only_new_events_and_one_publication(self):
        ex=self.make((0,0,15.522));old=ex.passage_state();h=self.prepare(ex)
        calls=[]
        def final():calls.append(1);return self.fence(start=1_000_123_456)
        receipt=ex.commit_step(h,final);state=ex.passage_state()
        self.assertEqual([1],calls);self.assertEqual(1,receipt.pose_revision)
        self.assertEqual((1_000_123_456,1_010_123_456),(receipt.start_ns,receipt.end_ns))
        self.assertEqual(old.history[0],state.history[0]);self.assertEqual('ENTRY_CROSSING',state.phase)
        self.assertEqual((receipt.start_ns,receipt.end_ns),(state.history[-1].start_ns,state.history[-1].end_ns))
        # Initial .25m/s brakes at .25m/s² toward speed_code5=.0625:
        # distance=.25*.01-.5*.25*.01²=.0024875m.
        self.assertAlmostEqual(15.5195125,state.pose.position_m[2],places=12)

    def test_T03_callback_stop_invalidates_root_even_if_callback_returns_fence(self):
        ex=self.make();h=self.prepare(ex);pose=ex.renderer_view().pose
        def stop():ex.revoke('operator STOP');return self.fence()
        with self.assertRaises(ValueError):ex.commit_step(h,stop)
        self.assertEqual(pose,ex.renderer_view().pose);self.assertEqual(0,ex.renderer_view().pose_revision)
        with self.assertRaises(ValueError):ex.commit_step(h,lambda:self.fence())

    def test_T04_same_pose_new_world_asset_epoch_boot_or_command_rejects_old_handle(self):
        for change in ('scene','asset','epoch','boot','command','revoke'):
            with self.subTest(change=change):
                ex=self.make();h=self.prepare(ex)
                if change=='boot':ex.activate_boot(self.f.boot_binding(generation=2,session=8))
                elif change=='command':
                    doc=json.loads(self.event.raw);doc['command_seq']=4;doc['candidate_id']=4
                    ex.admit_command(self.f.binding,rt.encode(doc))
                elif change=='revoke':ex.revoke('STOP')
                else:ex.invalidate_world(change+' changed')
                calls=[]
                with self.assertRaises(ValueError):ex.commit_step(h,lambda:(calls.append(1),self.fence())[1])
                self.assertFalse(calls);self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_T05_repeat_foreign_reentrant_and_failed_handles_never_repeat_motion(self):
        ex=self.make();h=self.prepare(ex);ex.commit_step(h,lambda:self.fence())
        with self.assertRaises(ValueError):ex.commit_step(h,lambda:self.fence(start=1_020_000_000))
        self.assertEqual(1,ex.renderer_view().pose_revision)
        ex=self.make();h=self.prepare(ex)
        def recursive():
            try:ex.commit_step(h,lambda:self.fence())
            except ValueError:pass
            return self.fence()
        with self.assertRaises(ValueError):ex.commit_step(h,recursive)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        other=self.make()
        with self.assertRaises(ValueError):other.commit_step(h,lambda:self.fence())

    def test_T06_real_runtime_final_checks_expired_ttl_state_sample_or_ai(self):
        for reason in ('ttl','state','sample','ai'):
            with self.subTest(reason=reason):
                self.setUp()
                if reason=='sample':
                    self.f.setUp();self.event=self.f.arm(duration=3000)
                ex=self.make();provider=self.f.provider
                # Deliver healthy STATE8 before entering the serial physics
                # step, never as a forbidden reentrant channel event.
                if reason in ('ttl','sample'):
                    times=[1_200_000_000,1_400_000_000,1_600_000_000,1_800_000_000]
                    times+=([1_900_000_000] if reason=='ttl' else [2_000_000_000,2_200_000_000,2_400_000_000])
                    for i,now in enumerate(times,1):
                        self.f.clock.value=now;self.f.beat(seq=10+i,tick=100+i)
                provider.prepare_step=ex.prepare_step
                def commit(handle,callback):
                    if reason=='ai':provider.live=False
                    elif reason=='ttl':
                        self.f.clock.value=2_000_000_000
                    elif reason=='state':self.f.clock.value=1_500_000_000
                    else:
                        # Command issue+3s and fresh STATE8 still cover now;
                        # the original 1s sample's 1.5s age cap expires.
                        self.f.clock.value=2_500_000_000
                    return ex.commit_step(handle,callback)
                provider.commit_step=commit
                result=self.f.owner.step(expected_pose_revision=0,dt_ns=DT)
                self.assertFalse(result.committed);self.assertEqual(0,ex.renderer_view().pose_revision)
                expected={'ttl':'no current command','sample':'no current command','state':'stopped:',
                          'ai':'AI fixture process died'}[reason]
                self.assertIn(expected,result.reason)

    def test_T07_deadline_equality_and_overlapping_actual_intervals_reject(self):
        ex=self.make();h=self.prepare(ex)
        with self.assertRaises(ValueError):ex.commit_step(h,lambda:self.fence(deadline=1_010_000_000))
        self.assertEqual(0,ex.renderer_view().pose_revision)
        ex=self.make();ex.commit_step(self.prepare(ex),lambda:self.fence())
        with self.assertRaises(ValueError):ex.commit_step(self.prepare(ex),lambda:self.fence(start=1_009_999_999))
        self.assertEqual(1,ex.renderer_view().pose_revision)

    def test_T08_later_slice_obstacle_or_budget_failure_never_commits_safe_prefix(self):
        part=s.Solid('thin-water','v1','box',(0,0,15.0776),(.01,.01,.00001),(0,0,0,1))
        scene=s.Scene('thin','v1',(('water',('thin-water',)),),(s.SceneObject('water','water',(part,)),))
        ex=self.make(scene=scene);raw=self.raw(speed_code=20,yaw_q=7000)
        ex.admit_command(self.f.binding,raw)
        with self.assertRaises(m.PreparationRejected) as error:self.prepare(ex)
        self.assertEqual('UNKNOWN',error.exception.status);self.assertEqual(2,error.exception.checked_slices)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        for kwargs in ({'max_slices':0},{'scene':scene,'limits':s.Limits(max_pairs=0)}):
            ex=self.make(**kwargs)
            with self.assertRaises(m.PreparationRejected):self.prepare(ex)
            self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_T09_missing_compound_piece_and_forbidden_material_union_are_not_ignored(self):
        part=s.Solid('piece','v1','box',(0,0,15.6),(.01,.01,.01),(0,0,0,1))
        with self.assertRaises(ValueError):s.Scene('bad','v1',(('rock',('piece','missing')),),(s.SceneObject('rock','hard_rock',(part,)),))
        rock=s.SceneObject('rock','hard_rock',(part,));water=s.SceneObject('water','water',(replace(part,model_id='water-piece'),))
        scene=s.Scene('union','v1',(('rock',('piece',)),('water',('water-piece',))),(rock,water))
        ex=self.make(scene=scene)
        with self.assertRaises(m.PreparationRejected) as error:self.prepare(ex)
        self.assertEqual('UNKNOWN',error.exception.status);self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_T10_sweep_floor_chord_bounds_and_rounding_error_carry_survive(self):
        ex=self.make(speed=.123456789);ex.commit_step(self.prepare(ex),lambda:self.fence())
        state=ex.passage_state();self.assertGreater(state.speed_error_upper,0)
        h=self.prepare(ex);frame=ex.prepared_audit(h)
        self.assertGreaterEqual(F(frame.path.provenance.inherited_errors.position_error_m),
            F(state.errors.position_error_m)+state.speed_error_upper*F(DT,10**9))
        for sweep in frame.sweeps:
            chord=sum((b-a)**2 for a,b in zip(sweep.start,sweep.end))
            self.assertGreaterEqual(sweep.arc_length**2,chord);self.assertGreaterEqual(sweep.budget.rotation,F(1,2000))
        nonzero=m.GeometryBudget(0,.001,0,'explicit additional asset margin')
        with self.assertRaises(ValueError):self.make(budget=nonzero)

    def test_T11_whole_tail_and_correct_role_required_for_entry_and_exit(self):
        ex=self.make((0,0,15.522));ex.commit_step(self.prepare(ex),lambda:self.fence())
        self.assertFalse(ex.passage_state().entered)
        ex=self.make(state=self.seeded('INSIDE',(0,0,-15.0)))
        ex.commit_step(self.prepare(ex),lambda:self.fence())
        self.assertEqual('EXIT_CROSSING',ex.passage_state().phase)
        self.assertNotEqual('ARRIVED',ex.passage_state().phase)
        ex=self.make(state=self.seeded('ENTRY_CROSSING',(0,0,14.481)))
        ex.commit_step(self.prepare(ex),lambda:self.fence())
        self.assertEqual('INSIDE',ex.passage_state().phase);self.assertTrue(ex.passage_state().entered)
        ex=self.make(state=self.seeded('EXIT_CROSSING',(0,0,-15.519)))
        ex.commit_step(self.prepare(ex),lambda:self.fence())
        self.assertEqual('ARRIVED',ex.passage_state().phase)
        self.ctx=replace(self.ctx,layout=w.Layout(g.Gate('front',-.15,0),g.Gate('front',.15,0)))
        ex=self.make((.15,0,15.522))
        with self.assertRaises(m.PreparationRejected):self.prepare(ex)
        self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_T12_unresolved_multislice_arrival_and_drilling_never_grant(self):
        ex=self.make(state=self.seeded('EXIT_CROSSING',(0,0,-15.519)))
        ex.admit_command(self.f.binding,self.raw(speed_code=20,yaw_q=7000))
        with self.assertRaises(m.PreparationRejected) as error:self.prepare(ex)
        self.assertEqual('UNKNOWN',error.exception.status)
        part=s.Solid('rock-piece','v1','box',(0,0,15.6),(.01,.01,.01),(0,0,0,1))
        scene=s.Scene('rock','v1',(('rock',('rock-piece',)),),(s.SceneObject('rock','hard_rock',(part,)),))
        ex=self.make(scene=scene)
        with self.assertRaises(m.PreparationRejected) as error:self.prepare(ex)
        self.assertEqual('DRILLING_REQUIRED',error.exception.status);self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_T13_new_boot_does_not_clear_trial_failure_or_old_history(self):
        ex=self.make();old=ex.passage_state();ex.revoke('proved fixture contact',trial_failed=True)
        ex.activate_boot(self.f.boot_binding(generation=2,session=8))
        with self.assertRaises(ValueError):ex.admit_command(self.f.boot_binding(generation=2,session=8),self.event.raw)
        self.assertEqual(old,ex.passage_state());self.assertTrue(ex.controller_view().trial_failed)
        ex=self.make();ex.invalidate_world('layout edited')
        with self.assertRaises(ValueError):ex.activate_boot(self.f.boot_binding(generation=2,session=8))

    def test_T14_waiting_changes_actual_mapping_but_never_integrates_pause(self):
        ex=self.make();h=self.prepare(ex)
        receipt=ex.commit_step(h,lambda:self.fence(start=1_300_000_000))
        self.assertAlmostEqual(15.5975125,ex.renderer_view().pose.position_m[2],places=12)
        self.assertEqual(1_310_000_000,receipt.end_ns)
        self.assertEqual(0,ex.passage_state().history[0].start_ns)

    def test_T15_fence_exception_consumes_handle_and_lost_receipt_reconciles_without_replay(self):
        ex=self.make();h=self.prepare(ex)
        def unavailable():raise RuntimeError('fixture liveness provider unavailable')
        with self.assertRaises(RuntimeError):ex.commit_step(h,unavailable)
        with self.assertRaises(ValueError):ex.commit_step(h,lambda:self.fence())
        self.assertEqual(0,ex.renderer_view().pose_revision)
        ex=self.make();h=self.prepare(ex)
        def lose_result():ex.commit_step(h,lambda:self.fence());raise RuntimeError('caller lost result')
        with self.assertRaises(RuntimeError):lose_result()
        self.assertEqual((1,1_010_000_000),(ex.renderer_view().pose_revision,ex.authority_snapshot().frame.fence.step_end_ns))
        with self.assertRaises(ValueError):ex.commit_step(h,lambda:self.fence())
        self.assertEqual(1,ex.renderer_view().pose_revision)

    def test_T16_controller_export_has_no_truth_proof_or_precise_collision_oracle(self):
        ex=self.make();view=ex.controller_view()
        self.assertEqual({'stopped','trial_failed'},set(view.__dataclass_fields__))
        renderer=ex.renderer_view();self.assertEqual({'pose','pose_revision'},set(renderer.__dataclass_fields__))
        with self.assertRaises(FrozenInstanceError):renderer.pose_revision=99
        self.assertFalse(hasattr(ex,'verify_boot'));self.assertFalse(hasattr(ex,'ai_lease'))

    def test_runtime_success_uses_owned_geometry_actual_clock_and_second_revision(self):
        ex=self.make();provider=self.f.provider
        def prepare(*args):
            handle=ex.prepare_step(*args);self.f.clock.value+=10_000;return handle
        provider.prepare_step=prepare;provider.commit_step=ex.commit_step
        first=self.f.owner.step(expected_pose_revision=0,dt_ns=DT)
        self.assertTrue(first.committed);self.assertEqual(1_000_010_000,first.receipt.start_ns)
        self.f.clock.value=first.receipt.end_ns
        second=self.f.owner.step(expected_pose_revision=1,dt_ns=DT)
        self.assertTrue(second.committed);self.assertEqual(2,ex.renderer_view().pose_revision)
        self.assertEqual(1_020_020_000,ex.passage_state().monotonic_ns)

    def test_caught_malformed_mutation_call_during_callback_still_vetoes(self):
        for name in ('revoke','invalidate_world','activate_boot','admit_command','prepare_step','commit_step'):
            with self.subTest(entry=name):
                ex=self.make();h=self.prepare(ex)
                def malformed():
                    try:getattr(ex,name)(self='invalid named receiver')
                    except (ValueError,TypeError):pass
                    return self.fence()
                with self.assertRaises(ValueError):ex.commit_step(h,malformed)
                self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_fence_boot_alias_cannot_run_equality_callback_after_root_check(self):
        ex=self.make();h=self.prepare(ex)
        class Alias(str):
            def __eq__(self,other):ex.revoke('STOP inside invalid alias');return True
        alias=replace(self.f.binding,run_id=Alias('run-1'))
        with self.assertRaises(ValueError):ex.commit_step(h,lambda:replace(self.fence(),boot=alias))
        self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_positive_explicit_asset_budget_is_in_workspace_and_solid_conjunction(self):
        budget=m.GeometryBudget(.0001,.0002,.0003,'fixture engine + asset + obstacle bounds')
        state=p.initialize(self.ctx,RigidState((0,0,15.6),(0,1,0,0),.25),gc.ErrorBounds(0.,0.,.0007),
            pose_revision=0,monotonic_ns=0,error_budget_reference='explicit margin partition fixture').state
        ex=self.make(state=state,budget=budget);handle=self.prepare(ex);audit=ex.prepared_audit(handle)
        for sweep in audit.sweeps:
            self.assertEqual(F(.0007),sweep.budget.numeric+sweep.budget.asset+sweep.budget.obstacle)
            self.assertEqual(F(.0002),sweep.budget.asset);self.assertEqual(F(.0003),sweep.budget.obstacle)
        ex.commit_step(handle,lambda:self.fence());self.assertEqual(1,ex.renderer_view().pose_revision)

    def test_pre_fence_publication_allocation_failure_has_no_pose_effect(self):
        ex=self.make();handle=self.prepare(ex);calls=[]
        # Controlled allocation fault at the real commit's first publication
        # container. Geometry and the owned store remain the real components.
        with patch.object(m,'CommitReceipt',side_effect=MemoryError('fixture allocation failure')):
            with self.assertRaises(MemoryError):ex.commit_step(handle,lambda:(calls.append(1),self.fence())[1])
        self.assertFalse(calls);self.assertEqual(0,ex.renderer_view().pose_revision)
        with self.assertRaises(ValueError):ex.commit_step(handle,lambda:self.fence())

    def test_real_runtime_double_fence_callback_or_missing_callback_never_publishes(self):
        ex=self.make();provider=self.f.provider;provider.prepare_step=ex.prepare_step
        def doubled(handle,callback):
            def two_calls():callback();return callback()
            return ex.commit_step(handle,two_calls)
        provider.commit_step=doubled
        self.assertFalse(self.f.owner.step(expected_pose_revision=0,dt_ns=DT).committed)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        self.setUp();ex=self.make()
        with self.assertRaises(ValueError):ex.commit_step(self.prepare(ex),None)
        self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_later_materialization_failure_retires_pending_without_losing_committed_history(self):
        for error_type in (MemoryError, ValueError, KeyboardInterrupt):
            with self.subTest(error_type=error_type.__name__):
                ex=self.make((0,0,15.522))
                ex.commit_step(self.prepare(ex),lambda:self.fence())
                committed=ex.authority_snapshot();phase=ex.passage_state();view=ex.renderer_view()
                pending=self.prepare(ex);fault=error_type('controlled later materialization failure')
                with patch.object(p,'materialize_committed_transition',side_effect=fault):
                    with self.assertRaises(error_type) as caught:ex.passage_state()
                self.assertIs(caught.exception,fault)
                self.assertTrue(ex.controller_view().stopped)
                self.assertFalse(ex.controller_view().trial_failed)
                self.assertEqual(ex.renderer_view(),view)
                self.assertIs(ex.authority_snapshot().frame,committed.frame)
                self.assertEqual(ex.passage_state(),phase)
                calls=[]
                with self.assertRaises(ValueError):
                    ex.commit_step(pending,lambda:(calls.append(1),self.fence(start=1_010_000_000))[1])
                self.assertFalse(calls)
                with self.assertRaises(ValueError):
                    ex.prepare_step(self.f.binding,self.event.raw,view.pose_revision,DT)
                self.assertEqual(ex.renderer_view(),view)

    def test_caught_materialization_failure_in_final_callback_vetoes_publication(self):
        ex=self.make();ex.commit_step(self.prepare(ex),lambda:self.fence())
        pending=self.prepare(ex);view=ex.renderer_view();calls=[]
        def final():
            calls.append(1)
            try:ex.passage_state()
            except MemoryError:pass
            return self.fence(start=1_010_000_000)
        with patch.object(p,'materialize_committed_transition',side_effect=MemoryError('controlled callback fault')):
            with self.assertRaises(ValueError):ex.commit_step(pending,final)
        self.assertEqual(calls,[1]);self.assertEqual(ex.renderer_view(),view)
        self.assertTrue(ex.controller_view().stopped)
        self.assertFalse(ex.controller_view().trial_failed)
        with self.assertRaises(ValueError):ex.commit_step(pending,final)
        self.assertEqual(calls,[1])


if __name__=='__main__':unittest.main()

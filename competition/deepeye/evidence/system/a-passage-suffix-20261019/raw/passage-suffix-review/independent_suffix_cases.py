"""Numerical seeds only, not a preceding route or authenticated live provider.

Only the certificate-corruption tests inject results; geometry/solids/runtime
checks elsewhere use actual accepted components and explicit channel fixtures.
"""
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
import json
import unittest
from unittest.mock import patch
from competition.deepeye.tests.simulation import test_motion_executor as fixtures
from competition.deepeye.simulation.authority import motion_executor as m
from competition.deepeye.simulation.authority import pc_direct_runtime as rt
from competition.deepeye.simulation.authority.motion import passage_phase as p
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
from competition.deepeye.simulation.authority.motion import certified_path as cp
from competition.deepeye.simulation.authority.motion import solid_clearance as s
from competition.deepeye.simulation.authority.motion.kinematics import RigidState

O=Path(__file__).resolve().parent;DT=10_000_000;OBSERVATIONS=[]

class IndependentSuffixCases(unittest.TestCase):
    def setUp(self):self.fx=fixtures.MotionExecutorTests();self.fx.setUp()
    def seed(self,z=-15.519,speed=.25):
        state=self.fx.seeded('EXIT_CROSSING',(0,0,z))
        if speed!=.25:
            values={n:getattr(state,n) for n in state.__dataclass_fields__ if n!='seal'}
            values['pose']=RigidState(state.pose.position_m,state.pose.orientation_xyzw,speed)
            state=p._state(**values)
        return state
    def path(self,state):
        return cp.CanonicalPath(state.pose,'fast_9600',20,7000,0,DT,
            inherited_errors=p.required_inherited_errors(state,DT),error_budget_reference=state.error_budget_reference)
    def preview(self,state,path=None,*,budget=16,cap=DT+1):
        return p.preview(state,path or self.path(state),state.context,expected_pose_revision=state.pose_revision,
            start_monotonic_ns=state.monotonic_ns,deadline_monotonic_ns=state.monotonic_ns+cap,
            hard_stop=False,max_slices=budget)

    def test_real_ramp_three_slices_retain_order_one_arrival_and_complete_end(self):
        # v0=.25-1/2048 gives an exact 1,953,125ns ramp, followed by
        # rotation-limited subdivision. Unlike the author's constant-speed seed,
        # arrival occurs on the middle of three original slices.
        state=self.seed(-15.5188,.24951171875);path=self.path(state);calls=[]
        actual=w.check_slice
        def check(prepared,index,role,**kwargs):
            proof=actual(prepared,index,role,**kwargs);calls.append((index,role,proof));return proof
        with patch.object(w,'check_slice',side_effect=check):result=self.preview(state,path)
        self.assertEqual('SAFE',result.status)
        self.assertEqual([0,1,2],[i for i,_,_ in calls]);self.assertEqual(['exit']*3,[role for _,role,_ in calls])
        self.assertEqual(tuple(proof for _,_,proof in calls),result.proofs)
        self.assertEqual(path.sample(DT).state,result.candidate.pose)
        self.assertEqual((6,10_000_010),(result.candidate.pose_revision,result.candidate.monotonic_ns))
        self.assertEqual(state.history,result.candidate.history[:len(state.history)])
        arrived=[e for e in result.candidate.history if e.kind=='ARRIVED'];self.assertEqual(1,len(arrived))
        self.assertEqual(calls[1][2].binding,arrived[0].proof_binding)
        self.assertEqual('STRICT_OUTSIDE_ACTIVE',next(f.method for f in result.proofs[2].faces if f.face=='back'))
        self.assertFalse(result.motion_grant);self.assertFalse(result.atomic_cas_completed)
        OBSERVATIONS.append({'case':'three-slice ramp','proof_count':3,'arrival_binding_index':1,
            'arrival_window':[arrived[0].start_ns,arrived[0].end_ns],'candidate_time':result.candidate.monotonic_ns})

    def test_three_slice_budget_and_original_deadline_never_publish_arrival_prefix(self):
        state=self.seed(-15.5188,.24951171875);path=self.path(state)
        for budget in (0,1,2):
            with self.subTest(budget=budget),patch.object(w,'check_slice',side_effect=AssertionError('budget must reject before any check')):
                result=self.preview(state,path,budget=budget)
                self.assertEqual('UNKNOWN',result.status);self.assertIs(state,result.candidate);self.assertEqual((),result.proofs)
        result=self.preview(state,path,budget=3);self.assertEqual('SAFE',result.status)
        clipped=self.preview(state,path,budget=3,cap=DT)
        self.assertEqual('UNKNOWN',clipped.status);self.assertIs(state,clipped.candidate)
        self.assertEqual(3,len(clipped.proofs));self.assertEqual(state.history,clipped.candidate.history)

    def test_injected_missing_duplicate_unknown_weak_faces_and_wrong_role_fail_closed(self):
        # Injected certificate corruption tests the reducer validation boundary;
        # it is not an actual geometry witness or an authentication attack.
        for corruption in ('missing','duplicate','unknown_face','weak_red','weak_other','wrong_red_method','wrong_role'):
            with self.subTest(corruption=corruption):
                state=self.seed();actual=w.check_slice;returned=[]
                def check(prepared,index,role,**kwargs):
                    proof=actual(prepared,index,role,**kwargs)
                    if index==1:
                        faces=list(proof.faces)
                        if corruption=='missing':faces=faces[:-1]
                        if corruption=='duplicate':faces[-1]=faces[0]
                        if corruption=='unknown_face':faces[0]=replace(faces[0],face='diagonal')
                        if corruption in ('weak_red','wrong_red_method'):
                            faces=[replace(f,method='APERTURE' if corruption=='weak_red' else 'STRICT_INSIDE') if f.face=='back' else f for f in faces]
                        if corruption=='weak_other':
                            i=next(i for i,f in enumerate(faces) if f.face!='back');faces[i]=replace(faces[i],method='APERTURE')
                        proof=replace(proof,faces=tuple(faces),role='entry' if corruption=='wrong_role' else proof.role)
                    returned.append(proof);return proof
                with patch.object(w,'check_slice',side_effect=check):result=self.preview(state)
                self.assertEqual('UNKNOWN',result.status);self.assertIs(state,result.candidate)
                self.assertEqual(tuple(returned),result.proofs);self.assertEqual(2,len(result.proofs))
                self.assertEqual(state.history,result.candidate.history);self.assertFalse(result.failure_candidate)

    def test_injected_final_third_slice_failure_keeps_original_history_and_status(self):
        for status in ('UNKNOWN','VIOLATION_PROVED'):
            with self.subTest(status=status):
                state=self.seed(-15.5188,.24951171875);actual=w.check_slice;indices=[]
                def check(prepared,index,role,**kwargs):
                    indices.append(index);proof=actual(prepared,index,role,**kwargs)
                    return replace(proof,status=status,reason='explicit final certificate fault') if index==2 else proof
                with patch.object(w,'check_slice',side_effect=check):result=self.preview(state)
                self.assertEqual([0,1,2],indices);self.assertEqual(status,result.status)
                self.assertIs(state,result.candidate);self.assertEqual(state.history,result.candidate.history)
                self.assertEqual(status=='VIOLATION_PROVED',result.failure_candidate)

    def test_real_final_suffix_cylinder_in_compound_scene_blocks_whole_owned_step(self):
        state=self.seed()
        thin=s.Solid('thin-final-cylinder','v1','cylinder',(0,0,-16.0414),(.008,.008,.00002),(0,0,0,1))
        far=s.Solid('far-piece','v1','box',(5,5,5),(.1,.1,.1),(0,0,0,1))
        scene=s.Scene('compound-final','v1',(('casing-object',('far-piece','thin-final-cylinder')),),
            (s.SceneObject('casing-object','casing',(far,thin)),))
        ex=self.fx.make(state=state,scene=scene);raw=self.fx.raw(speed_code=20,yaw_q=7000)
        ex.admit_command(self.fx.f.binding,raw);before=ex.renderer_view();actual=s.certify_scene;checked=[];fences=[]
        def certify(*args,**kwargs):
            result=actual(*args,**kwargs);checked.append(result);return result
        with patch.object(s,'certify_scene',side_effect=certify):
            with self.assertRaises(m.PreparationRejected) as error:
                h=ex.prepare_step(self.fx.f.binding,raw,5,DT)
                ex.commit_step(h,lambda:fences.append('must not reach final fence'))
        self.assertEqual(['CLEAR','UNKNOWN'],[r.status for r in checked])
        self.assertEqual(4,len(checked[0].pairs));self.assertEqual(2,error.exception.checked_slices)
        self.assertEqual([],fences);self.assertEqual(before,ex.renderer_view());self.assertIs(state,ex.passage_state())
        end=self.path(state).sample(DT);cap=tuple(end.state.position_m[i]+.4*end.axis[i] for i in range(3))
        self.assertLess(sum((float(thin.centre[i])-cap[i])**2 for i in range(3)),.12**2)

    def test_real_runtime_full_suffix_final_clock_and_single_publication_without_late_geometry(self):
        state=self.seed();ex=self.fx.make(state=state);fixture=self.fx.f;raw=self.fx.raw(speed_code=20,yaw_q=7000)
        fixture.owner.command(rt.VerifiedEnvelope(fixture.binding,raw));ex.admit_command(fixture.binding,raw)
        provider=fixture.provider;calls=[];after_fence=[False];checks=[];handles=[]
        def prepare(*args):
            h=ex.prepare_step(*args);handles.append(h);fixture.clock.value+=10_000;return h
        def commit(handle,callback):
            def final():
                calls.append('final');fence=callback();after_fence[0]=True;return fence
            return ex.commit_step(handle,final)
        provider.prepare_step=prepare;provider.commit_step=commit
        actual_check=w.check_slice;actual_solid=s.certify_scene;actual_plan=cp.CanonicalPath.plan;actual_digest=w.digest
        def check(*a,**kw):
            self.assertFalse(after_fence[0]);checks.append('workspace');return actual_check(*a,**kw)
        def solid(*a,**kw):
            self.assertFalse(after_fence[0]);checks.append('solid');return actual_solid(*a,**kw)
        def plan(obj,*a,**kw):self.assertFalse(after_fence[0]);return actual_plan(obj,*a,**kw)
        def digest(*a,**kw):self.assertFalse(after_fence[0]);return actual_digest(*a,**kw)
        before=ex.authority_snapshot()
        with patch.object(w,'check_slice',side_effect=check),patch.object(s,'certify_scene',side_effect=solid), \
             patch.object(cp.CanonicalPath,'plan',new=plan),patch.object(w,'digest',side_effect=digest):
            result=fixture.owner.step(expected_pose_revision=5,dt_ns=DT)
        self.assertTrue(result.committed,result.reason);self.assertEqual(['final'],calls)
        self.assertEqual(2,checks.count('workspace'));self.assertEqual(2,checks.count('solid'))
        self.assertEqual(before.revision+1,ex.authority_snapshot().revision)
        self.assertEqual((6,1_000_010_000,1_010_010_000),(result.receipt.pose_revision,result.receipt.start_ns,result.receipt.end_ns))
        materialized=ex.passage_state();self.assertEqual('ARRIVED',materialized.phase)
        self.assertEqual(state.history,materialized.history[:len(state.history)])
        self.assertEqual(self.path(state).sample(DT).state,materialized.pose)
        with self.assertRaises(ValueError):ex.commit_step(handles[0],lambda:calls.append('unexpected repeat'))
        self.assertEqual(6,ex.renderer_view().pose_revision);self.assertEqual(['final'],calls)

    def test_real_runtime_final_stop_world_and_earliest_deadline_equality_reject_whole_suffix(self):
        for fault in ('STOP','world','AI-deadline-equality'):
            with self.subTest(fault=fault):
                self.setUp();state=self.seed();ex=self.fx.make(state=state);fixture=self.fx.f;raw=self.fx.raw(speed_code=20,yaw_q=7000)
                fixture.owner.command(rt.VerifiedEnvelope(fixture.binding,raw));ex.admit_command(fixture.binding,raw)
                provider=fixture.provider;provider.prepare_step=ex.prepare_step;calls=[]
                if fault=='AI-deadline-equality':provider.ai_lease=lambda boot,now:rt.AiLease(boot,boot.ai_instance,now+DT)
                def commit(handle,callback):
                    def final():
                        calls.append('final')
                        if fault=='STOP':fixture.owner.stop('STOP at actual final callback')
                        if fault=='world':ex.invalidate_world('world change at actual final callback')
                        return callback()
                    return ex.commit_step(handle,final)
                provider.commit_step=commit;before=ex.renderer_view()
                result=fixture.owner.step(expected_pose_revision=5,dt_ns=DT)
                self.assertFalse(result.committed);self.assertEqual(['final'],calls)
                self.assertEqual(before,ex.renderer_view());self.assertIs(state,ex.passage_state())
                self.assertTrue(ex.controller_view().stopped)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentSuffixCases))
    (O/'independent-observations.json').write_text(json.dumps(OBSERVATIONS,indent=2)+'\n',encoding='utf8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

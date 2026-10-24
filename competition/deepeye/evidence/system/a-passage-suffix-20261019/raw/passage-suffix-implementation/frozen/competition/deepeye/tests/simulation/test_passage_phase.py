"""Ordered private preview state; no runtime registry/CAS or execution claims."""
import importlib
import unittest
from dataclasses import replace
from fractions import Fraction
import math

from competition.deepeye.simulation.authority.motion import certified_path as cp
from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState

try:
    p=importlib.import_module('competition.deepeye.simulation.authority.motion.passage_phase')
    w=importlib.import_module('competition.deepeye.simulation.authority.motion.workspace_boundaries')
except ModuleNotFoundError as exc:
    if exc.name not in ('competition.deepeye.simulation.authority.motion.passage_phase','competition.deepeye.simulation.authority.motion.workspace_boundaries'):raise
    p=w=None


class PassagePhaseTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(p,'passage_phase implementation missing')
        self.body=w.Envelope(.4,.12,.52,'explicit fixture',False)
        self.layout=w.Layout(g.Gate('front',0,0),g.Gate('back',0,0))
        self.context=p.RunContext('run1','scene-sha-v1',1,self.layout,self.body,'fixture owner assertion; not registry')
        self.errors=gc.ErrorBounds(0.,0.,0.)

    def initial(self,position=(0,0,15.6),q=(0,1,0,0),speed=.25,**kwargs):
        return p.initialize(self.context,RigidState(position,q,speed),self.errors,
            pose_revision=0,monotonic_ns=0,error_budget_reference='exact fixture assumptions',**kwargs)

    def path(self,state,*,yaw=0,errors=None,dt=10_000_000,speed=20):
        return cp.CanonicalPath(state.pose,'fast_9600',speed,yaw,0,dt,
             inherited_errors=errors or p.required_inherited_errors(state,dt),
             error_budget_reference='fixture carries prior bounds')

    def step(self,state,*,path=None,stop=False,deadline=None,context=None,budget=16):
        path=path or self.path(state)
        return p.preview(state,path,context or self.context,expected_pose_revision=state.pose_revision,
             start_monotonic_ns=state.monotonic_ns,deadline_monotonic_ns=deadline if deadline is not None else state.monotonic_ns+10_000_001,
             hard_stop=stop,max_slices=budget)

    def numerical_seed(self,phase,position,q=(0,1,0,0),context=None):
        # Internal numerical phase fixture, not evidence of a preceding route.
        kinds=['INITIAL_OUTSIDE','ENTRY_WINDOW']
        if phase!='ENTRY_CROSSING':kinds+=['ENTERED']
        if phase=='EXIT_CROSSING':kinds+=['EXIT_WINDOW']
        history=tuple(p.Event(kind,i,i,i,'explicit numerical seed only') for i,kind in enumerate(kinds))
        return p._state(context=context or self.context,pose=RigidState(position,q,.25),errors=self.errors,
            speed_error_upper=Fraction(0),error_budget_reference='numerical phase seed only',pose_revision=5,
            monotonic_ns=10,phase=phase,entered=phase!='ENTRY_CROSSING',history=history,trace_hash='numerical seed')

    def test_strict_outside_red_suffix_keeps_full_dt_certificates_and_one_arrival(self):
        for z in (-15.519,-15.5199):
            with self.subTest(z=z):
                state=self.numerical_seed('EXIT_CROSSING',(0,0,z));path=self.path(state,yaw=7000)
                plan=path.plan(start_monotonic_ns=10,deadline_monotonic_ns=10+10_000_001,hard_stop=False)
                result=self.step(state,path=path)
                self.assertEqual('SAFE',result.status)
                self.assertEqual(2,len(result.proofs))
                self.assertEqual([(0,7_142_857),(7_142_857,10_000_000)],
                    [(record.start.elapsed_ns,record.end.elapsed_ns) for record in plan.slices])
                self.assertEqual(plan.end.state,result.candidate.pose)
                self.assertEqual(plan.end.errors,result.candidate.errors)
                self.assertEqual((6,10_000_010),(result.candidate.pose_revision,result.candidate.monotonic_ns))
                self.assertEqual(state.history,result.candidate.history[:len(state.history)])
                arrivals=[event for event in result.candidate.history if event.kind=='ARRIVED']
                self.assertEqual(1,len(arrivals))
                self.assertEqual((10,7_142_867),(arrivals[0].start_ns,arrivals[0].end_ns))
                self.assertEqual(result.proofs[0].binding,arrivals[0].proof_binding)
                suffix=result.proofs[1]
                self.assertEqual('exit',suffix.role)
                self.assertEqual(set(w.FACES),{face.face for face in suffix.faces})
                self.assertEqual(6,len(suffix.faces))
                self.assertTrue(all(face.method==('STRICT_OUTSIDE_ACTIVE' if face.face=='back' else 'STRICT_INSIDE') for face in suffix.faces))
                self.assertGreaterEqual(suffix.rho_m,.0005)
                self.assertFalse(result.motion_grant);self.assertFalse(result.atomic_cas_completed)

    def test_aperture_only_tail_is_unknown_with_every_checked_certificate_and_original_state(self):
        state=self.numerical_seed('EXIT_CROSSING',(0,0,-15.5184))
        result=self.step(state,path=self.path(state,yaw=7000))
        self.assertEqual('UNKNOWN',result.status);self.assertIs(result.candidate,state)
        self.assertEqual(2,len(result.proofs))
        self.assertEqual('SAFE',result.proofs[1].status)
        self.assertEqual('APERTURE',next(face.method for face in result.proofs[1].faces if face.face=='back'))
        self.assertFalse(result.failure_candidate)

    def test_full_suffix_proof_is_symmetric_for_all_six_red_face_normals(self):
        a=math.sqrt(.5)
        poses={'front':((0,0,15.519),(0,0,0,1),'back'),
               'back':((0,0,-15.519),(0,1,0,0),'front'),
               'left':((-15.519,0,0),(0,-a,0,a),'right'),
               'right':((15.519,0,0),(0,a,0,a),'left'),
               'top':((0,15.519,0),(-a,0,0,a),'bottom'),
               'bottom':((0,-15.519,0),(a,0,0,a),'top')}
        for face,(position,q,blue) in poses.items():
            with self.subTest(face=face):
                context=replace(self.context,layout=w.Layout(g.Gate(blue,0,0),g.Gate(face,0,0)))
                state=self.numerical_seed('EXIT_CROSSING',position,q,context)
                result=self.step(state,path=self.path(state,yaw=7000),context=context)
                self.assertEqual('SAFE',result.status)
                self.assertEqual('ARRIVED',result.candidate.phase)
                self.assertEqual('STRICT_OUTSIDE_ACTIVE',next(f.method for f in result.proofs[-1].faces if f.face==face))

    def test_same_face_red_gate_does_not_accept_blue_aperture_as_exit(self):
        context=replace(self.context,layout=w.Layout(g.Gate('front',-.15,0),g.Gate('front',.15,0)))
        for x,status in ((.15,'SAFE'),(-.15,'UNKNOWN')):
            with self.subTest(x=x):
                state=self.numerical_seed('EXIT_CROSSING',(x,0,15.519),(0,0,0,1),context)
                result=self.step(state,path=self.path(state,yaw=7000),context=context)
                self.assertEqual(status,result.status)
                if status=='SAFE':self.assertEqual('ARRIVED',result.candidate.phase)
                else:self.assertIs(result.candidate,state)

    def test_existing_entry_and_single_slice_exit_keep_their_behavior(self):
        state=self.numerical_seed('EXIT_CROSSING',(0,0,-15.519))
        result=self.step(state,path=self.path(state,yaw=0))
        self.assertEqual(('SAFE','ARRIVED',1),(result.status,result.candidate.phase,len(result.proofs)))
        self.assertEqual('HELD',self.step(result.candidate).status)
        for z,status in ((14.481,'SAFE'),(14.4815,'UNKNOWN')):
            state=self.numerical_seed('ENTRY_CROSSING',(0,0,z))
            result=self.step(state,path=self.path(state,yaw=7000))
            self.assertEqual(status,result.status)
            if status=='SAFE':self.assertEqual('INSIDE',result.candidate.phase)
            else:self.assertIs(result.candidate,state)

    def test_tip_or_center_beyond_red_is_not_full_body_arrival(self):
        for z in (-15.,-15.3):
            state=self.numerical_seed('EXIT_CROSSING',(0,0,z))
            result=self.step(state,path=self.path(state,yaw=7000))
            self.assertEqual('SAFE',result.status)
            self.assertEqual('EXIT_CROSSING',result.candidate.phase)
            self.assertFalse(any(event.kind=='ARRIVED' for event in result.candidate.history))

    def test_suffix_cannot_bypass_direction_rim_rotation_or_nonactive_face_failure(self):
        cases=[((0,0,-15.519),(0,0,0,1),7000),
               ((15.6,0,-15.519),(0,1,0,0),7000),
               ((.03,0,-15.),(0,1,0,0),0),
               ((.0295,0,-15.),(0,1,0,0),7000)]
        for position,q,yaw in cases:
            with self.subTest(position=position,q=q,yaw=yaw):
                state=self.numerical_seed('EXIT_CROSSING',position,q)
                result=self.step(state,path=self.path(state,yaw=yaw))
                self.assertNotEqual('SAFE',result.status);self.assertIs(result.candidate,state)
        exact=replace(self.context,envelope=replace(self.body,exact_fixture=True))
        state=self.numerical_seed('EXIT_CROSSING',(.03,0,-15.),context=exact)
        result=self.step(state,path=self.path(state,yaw=0),context=exact)
        self.assertEqual('VIOLATION_PROVED',result.status);self.assertTrue(result.failure_candidate)

    def test_suffix_budget_or_stop_never_returns_a_partial_arrival(self):
        state=self.numerical_seed('EXIT_CROSSING',(0,0,-15.519));path=self.path(state,yaw=7000)
        for budget in (0,1):
            result=self.step(state,path=path,budget=budget)
            self.assertEqual('UNKNOWN',result.status);self.assertIs(result.candidate,state)
            self.assertEqual((),result.proofs)
        result=self.step(state,path=path,stop=True)
        self.assertEqual('HELD',result.status);self.assertIs(result.candidate,state)

    def test_arrived_prefix_cannot_hide_rotated_suffix_other_face_uncertainty(self):
        context=replace(self.context,layout=w.Layout(g.Gate('front',14.85,0),g.Gate('back',14.85,0)))
        state=self.numerical_seed('EXIT_CROSSING',(14.8794,0,-15.519),context=context)
        result=self.step(state,path=self.path(state,yaw=7000),context=context)
        self.assertEqual('UNKNOWN',result.status);self.assertIs(result.candidate,state)
        self.assertEqual(2,len(result.proofs))
        self.assertEqual('SAFE',result.proofs[0].status)
        self.assertTrue(next(side.outside for side in result.proofs[0].end_sides if side.face=='back'))
        self.assertEqual('UNKNOWN',result.proofs[1].status)
        self.assertEqual('ENVELOPE_NOT_CLEAR',next(face.method for face in result.proofs[1].faces if face.face=='right'))
        self.assertFalse(result.failure_candidate)

    def test_strict_suffix_cannot_turn_a_deadline_clipped_plan_into_full_dt_success(self):
        state=self.numerical_seed('EXIT_CROSSING',(0,0,-15.519));path=self.path(state,yaw=7000)
        deadline=state.monotonic_ns+10_000_000
        plan=path.plan(start_monotonic_ns=state.monotonic_ns,deadline_monotonic_ns=deadline,hard_stop=False)
        self.assertEqual(9_999_999,plan.covered_ns)
        result=self.step(state,path=path,deadline=deadline)
        self.assertEqual('UNKNOWN',result.status);self.assertIs(result.candidate,state)
        self.assertEqual(2,len(result.proofs))

    def test_initial_whole_body_outside_and_correct_orientation_are_required(self):
        self.assertEqual('SAFE',self.initial().status)
        for position,q in (((0,0,0),(0,1,0,0)),((0,0,15.2),(0,1,0,0)),((0,0,15.6),(0,0,0,1))):
            self.assertIsNone(self.initial(position,q).state)

    def test_stop_and_expired_deadline_hold_phase_pose_speed_and_revision(self):
        state=self.initial().state
        for result in (self.step(state,stop=True),self.step(state,deadline=0)):
            self.assertEqual('HELD',result.status)
            self.assertIs(result.candidate,state)
            self.assertEqual(.25,result.candidate.pose.speed_m_s)
            self.assertFalse(result.motion_grant)

    def test_tip_partial_entry_is_not_entered_and_stop_does_not_complete_it(self):
        state=self.initial((0,0,15.522)).state
        result=self.step(state)
        self.assertEqual('SAFE',result.status)
        self.assertEqual('ENTRY_CROSSING',result.candidate.phase)
        self.assertFalse(result.candidate.entered)
        self.assertIs(self.step(result.candidate,stop=True).candidate,result.candidate)

    def test_scene_gate_epoch_and_pose_change_cannot_reuse_history(self):
        state=self.initial().state;path=self.path(state)
        changed=p.RunContext('run1','scene-sha-v2',1,self.layout,self.body,'fixture owner')
        self.assertEqual('UNKNOWN',self.step(state,path=path,context=changed).status)
        changed=p.RunContext('run1','scene-sha-v1',2,self.layout,self.body,'fixture owner')
        self.assertEqual('UNKNOWN',self.step(state,path=path,context=changed).status)
        changed=p.RunContext('run1','scene-sha-v1',1,w.Layout(g.Gate('front',1,0),self.layout.red),self.body,'fixture owner')
        self.assertEqual('UNKNOWN',self.step(state,path=path,context=changed).status)
        wrong=cp.CanonicalPath(RigidState((0,0,15.5),(0,1,0,0),.25),'fast_9600',20,0,0,10_000_000,
             inherited_errors=self.errors,error_budget_reference='fixture')
        self.assertEqual('UNKNOWN',self.step(state,path=wrong).status)

    def test_budget_unknown_does_not_commit_partial_events(self):
        state=self.initial((0,0,15.522)).state
        result=self.step(state,budget=0)
        self.assertEqual('UNKNOWN',result.status)
        self.assertIs(result.candidate,state)

    def test_numeric_error_and_speed_carry_are_not_reset_on_next_command(self):
        state=self.initial(speed=.123456789).state
        after=self.step(state).candidate
        self.assertGreater(after.speed_error_upper,0)
        required=p.required_inherited_errors(after,10_000_000)
        self.assertGreaterEqual(required.position_error_m,after.errors.position_error_m)
        reset=self.path(after,errors=self.errors)
        result=self.step(after,path=reset)
        self.assertEqual('UNKNOWN',result.status)
        self.assertIs(result.candidate,after)

    def test_no_arbitrary_phase_or_external_plan_can_be_supplied(self):
        state=self.initial().state
        with self.assertRaises(TypeError):replace(state,phase='ARRIVED',entered=True)
        with self.assertRaises(TypeError):self.step(state,path=object())

    def test_partial_entry_wrong_direction_does_not_reset_or_advance(self):
        state=self.initial((0,0,15.522)).state
        after=self.step(state).candidate
        # External pose replacement is a mismatch, not a legal reverse capability.
        wrong=cp.CanonicalPath(RigidState(after.pose.position_m,(0,0,0,1),.25),'fast_9600',20,0,0,10_000_000,
             inherited_errors=after.errors,error_budget_reference='fixture')
        result=self.step(after,path=wrong)
        self.assertEqual('UNKNOWN',result.status);self.assertIs(result.candidate,after)


if __name__=='__main__':unittest.main()

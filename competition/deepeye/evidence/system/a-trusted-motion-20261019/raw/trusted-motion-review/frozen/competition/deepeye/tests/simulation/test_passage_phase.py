"""Ordered private preview state; no runtime registry/CAS or execution claims."""
import importlib
import unittest
from dataclasses import replace

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

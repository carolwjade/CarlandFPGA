"""New pure numeric controls; no native owner, board or production authentication."""
import unittest
from competition.deepeye.simulation.authority import motion_executor as m
from competition.deepeye.simulation.authority.motion import passage_phase as p, workspace_boundaries as w, solid_clearance as s, gate_geometry as g, gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
try:
    from competition.deepeye.simulation.authority import _offboard_motion_component as off
except ImportError:
    off = None

DT=10_000_000

def executor(scene=None, position=(0,0,15.6)):
    body=w.Envelope(.4,.12,.52,'numeric fixture',False)
    ctx=p.RunContext('run-1','fixture-scene',1,w.Layout(g.Gate('front',0,0),g.Gate('back',0,0)),body,'test only')
    init=p.initialize(ctx,RigidState(position,(0,1,0,0),.25),gc.ErrorBounds(0.,0.,0.),pose_revision=0,monotonic_ns=0,error_budget_reference='numeric fixture').state
    return m.OwnedMotionExecutor(initial_state=init,scene=scene or s.Scene('fixture-scene','v1',(),()),model=s.CapsuleModel('fixture-body','v1',.4,.12,.52),budget=m.GeometryBudget(0,0,0,'numeric fixture'))

class NumericComponent(unittest.TestCase):
    def component(self, scene=None, position=(0,0,15.6), yaw=0):
        self.assertIsNotNone(off,'offboard component missing')
        ex=executor(scene,position); c=off.Component(ex)
        with self.assertRaises(ValueError): c.prepare(0,DT)
        c.activate(); c.command(sequence=7,issue_ns=1_000_000_000,deadline_ns=2_000_000_000,profile='fast_9600',speed_code=5,yaw_q=yaw,pitch_q=0)
        return ex,c

    def test_real_straight_and_turning_cas(self):
        for yaw in (0,100):
            with self.subTest(yaw=yaw):
                ex,c=self.component(yaw=yaw); before=ex.authority_snapshot(); h=c.prepare(0,DT)
                self.assertIs(before,ex.authority_snapshot())
                r=c.commit(h,checked_ns=1_000_000_000,deadline_ns=1_500_000_000)
                self.assertIs(type(r),off.Receipt); self.assertEqual(1,r.pose_revision)
                self.assertIsNot(before,ex.authority_snapshot()); self.assertNotEqual(before.pose,ex.renderer_view().pose)
                self.assertEqual(1,ex.passage_state().pose_revision)
                with self.assertRaises(ValueError): c.prepare(1,DT)
                with self.assertRaises(ValueError): c.acknowledge(object())
                c.acknowledge(r)
                with self.assertRaises(ValueError): c.commit(h,checked_ns=1_020_000_000,deadline_ns=1_500_000_000)
                self.assertEqual(1,ex.renderer_view().pose_revision)

    def test_collision_and_workspace_refuse_without_cas(self):
        part=s.Solid('piece','v1','box',(0,0,15.6),(.01,.01,.01),(0,0,0,1))
        scene=s.Scene('collision','v1',(('rock',('piece',)),),(s.SceneObject('rock','hard_rock',(part,)),))
        ex,c=self.component(scene=scene)
        with self.assertRaises(m.PreparationRejected): c.prepare(0,DT)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        ex,c=self.component(position=(.15,0,15.522))
        with self.assertRaises(m.PreparationRejected): c.prepare(0,DT)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        ex,c=self.component(position=(0,0,15.6))
        with self.assertRaises(ValueError): c.prepare(0,DT+1)
        self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_expiry_and_consumed_and_revoked_reject(self):
        ex,c=self.component(); h=c.prepare(0,DT)
        with self.assertRaises(ValueError): c.commit(h,checked_ns=1_000_000_000,deadline_ns=1_010_000_000)
        with self.assertRaises(ValueError): c.commit(h,checked_ns=1_000_000_000,deadline_ns=1_500_000_000)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        ex,c=self.component(); h=c.prepare(0,DT); ex.revoke('stop')
        with self.assertRaises(ValueError): c.commit(h,checked_ns=1_000_000_000,deadline_ns=1_500_000_000)

    def test_foreign_and_production_entry_reject_fixture(self):
        ex,c=self.component(); h=c.prepare(0,DT); other,d=self.component()
        with self.assertRaises(ValueError): d.commit(h,checked_ns=1_000_000_000,deadline_ns=1_500_000_000)
        with self.assertRaises(ValueError): ex.prepare_step(None,b'',0,DT)
        with self.assertRaises(ValueError): ex.commit_step(h,lambda:None)
        self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_stale_handle_and_invalid_time_consume_without_motion(self):
        ex,c=self.component(); h=c.prepare(0,DT)
        c.command(sequence=8,issue_ns=1_000_000_000,deadline_ns=2_000_000_000,
                  profile='fast_9600',speed_code=5,yaw_q=0,pitch_q=0)
        with self.assertRaises(ValueError): c.commit(h,checked_ns=1_000_000_000,deadline_ns=1_500_000_000)
        self.assertEqual(0,ex.renderer_view().pose_revision)
        ex,c=self.component(); h=c.prepare(0,DT)
        with self.assertRaises(ValueError): c.commit(h,checked_ns=True,deadline_ns=1_500_000_000)
        self.assertTrue(ex.controller_view().stopped)
        self.assertEqual(0,ex.renderer_view().pose_revision)

    def test_two_commits_require_exact_first_receipt_acknowledgement(self):
        ex,c=self.component(); first=c.commit(c.prepare(0,DT),checked_ns=1_000_000_000,deadline_ns=1_500_000_000)
        c.acknowledge(first)
        second=c.commit(c.prepare(1,DT),checked_ns=1_020_000_000,deadline_ns=1_500_000_000)
        self.assertEqual((1,2),(first.pose_revision,second.pose_revision))
        self.assertEqual(2,ex.passage_state().pose_revision)

if __name__=='__main__': unittest.main()

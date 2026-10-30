"""NEW software registry isolation controls; no original native owner run."""
import unittest
from competition.deepeye.simulation.authority import _world_loop as world, motion_executor as m, _offboard_motion_component as off
from competition.deepeye.simulation.authority.motion import passage_phase as p, workspace_boundaries as w, solid_clearance as s, gate_geometry as g, gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState

DT=1_000_000

def executor():
    body=w.Envelope(.4,.12,.52,'separate fixture',False)
    context=p.RunContext('fixture','scene',1,w.Layout(g.Gate('front',0,0),g.Gate('back',0,0)),body,'numeric only')
    state=p.initialize(context,RigidState((0,0,15.6),(0,1,0,0),.2),gc.ErrorBounds(0.,0.,0.),pose_revision=0,monotonic_ns=0,error_budget_reference='fixture').state
    return m.OwnedMotionExecutor(initial_state=state,scene=s.Scene('scene','v1',(),()),model=s.CapsuleModel('body','v1',.4,.12,.52),budget=m.GeometryBudget(0,0,0,'fixture'))

class CustodyIsolation(unittest.TestCase):
    def register(self, ex, retired=False):
        owner=object.__new__(world._RootWorldOwner)
        binding=world._Binding(owner,None,None,ex,0,0)
        owner._bindings={id(binding):binding}; owner._binding=None if retired else binding
        world._RETAINED.append(owner)
        self.addCleanup(world._RETAINED.remove,owner)
        return owner
    def unchanged(self, ex, action):
        root=ex._root; pending=ex._pending; items=dict(pending); owner=ex._offboard_owner
        with self.assertRaises(ValueError): action()
        self.assertIs(root,ex._root); self.assertIs(pending,ex._pending)
        self.assertEqual(items,ex._pending); self.assertIs(owner,ex._offboard_owner)
    def ready(self):
        ex=executor(); c=off.Component(ex); c.activate()
        c.command(sequence=1,issue_ns=100,deadline_ns=100_000_000,profile='fast_9600',speed_code=5,yaw_q=20,pitch_q=0)
        return ex,c
    def test_constructor_live_and_retired_binding_refuse_without_mutation(self):
        for retired in (False,True):
            with self.subTest(retired=retired):
                ex=executor(); self.register(ex,retired)
                self.unchanged(ex,lambda:off.Component(ex))
    def test_preconstructed_then_bound_rejects_activation_without_mutation(self):
        ex=executor(); c=off.Component(ex); self.register(ex)
        self.unchanged(ex,c.activate)
    def test_binding_after_activation_blocks_each_facade_boundary(self):
        ex=executor(); c=off.Component(ex); c.activate(); self.register(ex)
        self.unchanged(ex,lambda:c.command(sequence=1,issue_ns=100,deadline_ns=100_000_000,profile='fast_9600',speed_code=5,yaw_q=0,pitch_q=0))
        ex,c=self.ready(); self.register(ex)
        self.unchanged(ex,lambda:c.prepare(0,DT))
        ex,c=self.ready(); h=c.prepare(0,DT); self.register(ex)
        self.unchanged(ex,lambda:c.commit(h,checked_ns=100,deadline_ns=50_000_000))
    def test_direct_executor_entries_refuse_without_revoke_or_pending_mutation(self):
        ex,c=self.ready(); h=c.prepare(0,DT); self.register(ex,True)
        cmd=off.Command(c,2,100,100_000_000,'fast_9600',5,0,0)
        f=off.Fence(c,1,100,100+DT,50_000_000)
        for operation in (lambda:ex._offboard_activate(c),lambda:ex._offboard_command(c,cmd),lambda:ex._offboard_prepare(c,0,DT),lambda:ex._offboard_commit(c,h,f),lambda:ex._prepare_geometry(ex._root,ex._root.command,True,DT),lambda:ex._commit_numeric(h,f,True,c)):
            self.unchanged(ex,operation)
    def test_independent_actual_numeric_fixture_positive(self):
        ex,c=self.ready(); before=ex._root; h=c.prepare(0,DT)
        receipt=c.commit(h,checked_ns=100,deadline_ns=50_000_000)
        self.assertIsNot(before,ex._root); self.assertEqual(1,receipt.pose_revision)
        self.assertNotEqual(before.pose,ex._root.pose)

if __name__=='__main__': unittest.main()

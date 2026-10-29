"""New current-world initialization controls; no engine or old suite execution."""
import importlib
import math
from fractions import Fraction
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion import passage_phase as passage
from competition.deepeye.simulation.authority.motion import solid_clearance as solid
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
from competition.deepeye.simulation.authority.motion.kinematics import RigidState


def optional_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as error:
        if error.name != name:
            raise
        return None


initial = optional_module('competition.deepeye.simulation.authority.world_initial_pose')
loop = optional_module('competition.deepeye.simulation.authority._world_loop')


class CurrentWorldInitializationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(initial, 'current-world initial-pose helper is missing')
        self.assertIsNotNone(loop, 'current-world owner integration is missing')

    def layout(self, face='front', u=2., v=-3., red=None):
        opposite = {'front':'back', 'back':'front', 'top':'bottom',
                    'bottom':'top', 'left':'right', 'right':'left'}
        return w.Layout(g.Gate(face, u, v), red or g.Gate(opposite[face], 0., 0.))

    def initialize(self, layout, pose):
        context = passage.RunContext('new-initialization-control', 'literal-fixture', 1,
            layout, w.Envelope(.4, .12, .52, 'literal-full-body', True), 'software-only')
        return passage.initialize(context, pose, gc.ErrorBounds(0., 0., 0.),
            pose_revision=0, monotonic_ns=100, error_budget_reference='literal-zero-fixture')

    def test_six_selected_faces_and_offsets_point_body_inward_with_proper_up(self):
        # Literal independent expectations: position, inward body+Z, body+Y.
        cases = [
            ('front', (2.,-3.,15.6), (0.,0.,-1.), (0.,1.,0.)),
            ('back', (2.,-3.,-15.6), (0.,0.,1.), (0.,1.,0.)),
            ('left', (-15.6,-3.,2.), (1.,0.,0.), (0.,1.,0.)),
            ('right', (15.6,-3.,2.), (-1.,0.,0.), (0.,1.,0.)),
            ('top', (2.,15.6,-3.), (0.,-1.,0.), (0.,0.,1.)),
            ('bottom', (2.,-15.6,-3.), (0.,1.,0.), (0.,0.,-1.)),
        ]
        for face, position, forward, up in cases:
            with self.subTest(face=face):
                layout = self.layout(face)
                pose = initial.initial_pose_for_layout(layout, standoff_m=.6)
                self.assertIs(type(pose), RigidState)
                self.assertEqual(position, pose.position_m)
                self.assertEqual(0., pose.speed_m_s)
                matrix = solid._rotation(tuple(map(Fraction, pose.orientation_xyzw)))
                for row in range(3):
                    self.assertAlmostEqual(forward[row], float(matrix[row][2]), places=12)
                    self.assertAlmostEqual(up[row], float(matrix[row][1]), places=12)
                result = self.initialize(layout, pose)
                self.assertEqual('SAFE', result.status)
                self.assertFalse(result.motion_grant)
                self.assertEqual('OUTSIDE_ENTRY', result.state.phase)

    def test_legal_edge_offsets_and_same_face_gates_remain_actual_layout_choices(self):
        for face in ('front','back','left','right','top','bottom'):
            for u, v in ((14.85,-14.85),(-14.85,14.85)):
                with self.subTest(face=face, u=u, v=v):
                    layout = self.layout(face, u, v)
                    pose = initial.initial_pose_for_layout(layout, standoff_m=.6)
                    self.assertEqual('SAFE', self.initialize(layout, pose).status)
        layout = self.layout('left', 2., -3., g.Gate('left', -2., 3.))
        self.assertEqual((-15.6,-3.,2.),
                         initial.initial_pose_for_layout(layout, standoff_m=.6).position_m)

    def test_explicit_standoff_is_strict_and_real_full_body_initializer_can_reject(self):
        layout = self.layout()
        with self.assertRaises(TypeError):
            initial.initial_pose_for_layout(layout)
        for distance in (None, True, False, 0., -.1, math.nan, math.inf, -math.inf, '.6'):
            with self.subTest(distance=distance), self.assertRaises((TypeError, ValueError)):
                initial.initial_pose_for_layout(layout, standoff_m=distance)
        for foreign in (None, {}, SimpleNamespace(blue=layout.blue, red=layout.red)):
            with self.subTest(layout=foreign), self.assertRaises((TypeError, ValueError)):
                initial.initial_pose_for_layout(foreign, standoff_m=.6)
        proposed = initial.initial_pose_for_layout(layout, standoff_m=.1)
        self.assertEqual((2.,-3.,15.1), proposed.position_m)
        self.assertEqual('UNKNOWN', self.initialize(layout, proposed).status)

    def owner(self):
        owner = loop._RootWorldOwner(loop._TEST_FACTORY, lambda: 100)
        owner._native = SimpleNamespace(run_id='explicit-pose-control')
        epoch = loop._FrozenEpoch(owner, 1, 'new-freeze', {}, b'', object(), 100)
        owner._epoch = epoch
        owner._epochs[id(epoch)] = epoch
        owner._state = 'FROZEN'
        policy = loop.values.ValuePolicy(*(['0'*64]*5), (), (), (), run_id=owner._native.run_id)
        return owner, epoch, policy

    def test_construct_forwards_exact_required_root_pose_to_real_value_boundary(self):
        owner, epoch, policy = self.owner()
        pose = initial.initial_pose_for_layout(self.layout('right'), standoff_m=.6)
        received = []
        class ReachedValueBoundary(Exception):
            pass
        def record(snapshot, actual_policy, actual_pose, *, initial_monotonic_ns):
            received.append((snapshot, actual_policy, actual_pose, initial_monotonic_ns))
            raise ReachedValueBoundary()
        with patch.object(loop.values, '_construct_values', side_effect=record):
            with self.assertRaises(ReachedValueBoundary):
                owner.construct_and_bind(epoch, policy, initial_pose=pose)
        self.assertEqual(1, len(received))
        self.assertIs(epoch.snapshot, received[0][0])
        self.assertIs(policy, received[0][1])
        self.assertIs(pose, received[0][2])
        self.assertEqual(100, received[0][3])
        self.assertIsNone(owner._binding)

    def test_missing_or_nonzero_speed_initial_pose_never_constructs_an_executor(self):
        for kind in ('missing', 'foreign', 'moving'):
            owner, epoch, policy = self.owner()
            supplied = {} if kind == 'missing' else {'initial_pose':
                object() if kind == 'foreign' else RigidState((2.,-3.,15.6),(0.,1.,0.,0.),.01)}
            with self.subTest(kind=kind), patch.object(loop.values, '_construct_values',
                    side_effect=AssertionError('invalid pose reached construction')):
                with self.assertRaises((TypeError, ValueError)):
                    owner.construct_and_bind(epoch, policy, **supplied)
            self.assertIsNone(owner._binding)
            self.assertEqual([], owner._commits)

    def test_disabled_synthetic_entry_refuses_before_touching_any_owner_or_executor(self):
        owner = object.__new__(loop._RootWorldOwner)
        before = dict(owner.__dict__)
        with self.assertRaises(loop.WorldRejected):
            owner.diagnostic_step_once(object())
        self.assertEqual(before, owner.__dict__)


if __name__ == '__main__':
    unittest.main()

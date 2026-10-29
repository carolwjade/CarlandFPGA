"""New exact-owner conductivity field controls; synthetic source admission only."""
import importlib
import math
import threading
import unittest

from competition.deepeye.tests.simulation import test_motion_executor as fixture_module
from competition.deepeye.simulation.authority.motion import solid_clearance as geometry

try:
    field_module = importlib.import_module('competition.deepeye.simulation.sensors.owned_world_field')
except ModuleNotFoundError as exc:
    if exc.name != 'competition.deepeye.simulation.sensors.owned_world_field':
        raise
    field_module = None

POLICY = {'hard_rock': .001, 'water': 1.2, 'void': None, 'fault': .2, 'casing': None}


def solid(name, kind='box', centre=(0, 0, 0), dimensions=(1, 1, 1), q=(0, 0, 0, 1)):
    return geometry.Solid(name, 'candidate-test-v1', kind, centre, dimensions, q)


def scene(objects):
    return geometry.Scene('fixture-scene', 'v1',
                          tuple((o.object_id, tuple(p.model_id for p in o.parts)) for o in objects), tuple(objects))


class OwnedWorldFieldTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(field_module, 'exact-owner world field is not implemented')
        self.fixture = fixture_module.MotionExecutorTests()
        self.fixture.setUp()

    def owner(self, objects=()):
        return self.fixture.make(scene=scene(objects))

    def field(self, owner, **kw):
        options = dict(material_sigma=POLICY, background_sigma=.02,
                       max_pieces=64, sample_epsilon_m=.0001)
        options.update(kw)
        return field_module.OwnedWorldField(owner, **options)

    def test_rotated_box_and_elliptic_cylinder_use_actual_local_matrix_and_half_sizes(self):
        box = geometry.SceneObject('water-box', 'water',
            (solid('box', centre=(3, 4, 5), dimensions=(2, .5, .25), q=(0, 0, 1, 1)),))
        cylinder = geometry.SceneObject('rock-cylinder', 'hard_rock',
            (solid('cylinder', 'cylinder', (-3, 0, 0), (1, .5, 2), (0, 1, 0, 1)),))
        field = self.field(self.owner((box, cylinder)), sample_epsilon_m=.01)
        for point, want in [((3, 5.5, 5), 1.2), ((4, 4, 5), .02),
                            ((-1.5, 0, 0), .001), ((-3, .6, 0), .02),
                            ((-3, 0, 1.1), .02), ((3, 6, 5), None),
                            ((-3, .5, 0), None), ((-1.005, 0, 0), None),
                            ((-.98, 0, 0), .02), ((math.inf, 0, 0), None),
                            ((False, 0, 0), None)]:
            with self.subTest(point=point):
                self.assertEqual(want, field.sample_sigma(*point))

    def test_layout_priority_and_explicit_unsupported_material_preserve_unknown(self):
        materials = ['hard_rock', 'water', 'void', 'fault', 'casing']
        objects = tuple(geometry.SceneObject(kind, kind, (solid(kind),)) for kind in materials)
        for count, want in [(1, .001), (2, 1.2), (3, None), (4, .2), (5, None)]:
            with self.subTest(count=count):
                f = self.field(self.owner(objects[:count]))
                self.assertEqual(want, f.sample_sigma(0, 0, 0))
        policy = dict(POLICY, casing=2.0, void=.003)
        f = self.field(self.owner(objects), material_sigma=policy)
        policy['casing'] = .5
        self.assertEqual(2., f.sample_sigma(0, 0, 0))
        self.assertIsNone(f.sample_sigma(1, 0, 0))

    def test_complete_thirty_object_sixty_part_field_covers_every_piece(self):
        materials = tuple(POLICY)
        policy = {'hard_rock': .001, 'water': 1.2, 'void': .003, 'fault': .2, 'casing': 2.}
        objects = []
        probes = []
        for index in range(30):
            x, y = -10 + 4 * (index % 5), -10 + 4 * (index // 5)
            kind = materials[index % 5]
            parts = tuple(solid(f'part-{index}-{z}', centre=(x, y, z), dimensions=(.25, .25, .25)) for z in (0, 2))
            objects.append(geometry.SceneObject(f'object-{index}', kind, parts))
            probes.extend(((x, y, z), policy[kind]) for z in (0, 2))
        f = self.field(self.owner(objects), material_sigma=policy, max_pieces=60)
        for point, expected in probes:
            with self.subTest(point=point):
                self.assertEqual(expected, f.sample_sigma(*point))
        self.assertEqual(.02, f.sample_sigma(14, 14, 14))
        with self.assertRaises(ValueError):
            self.field(self.owner(objects), max_pieces=59)
        with self.assertRaises(ValueError):
            self.field(self.owner(objects + [geometry.SceneObject('extra', 'water', (solid('extra', centre=(14, 14, 14)),))]))

    def test_any_unsupported_piece_refuses_whole_scene_and_bad_policies_refuse(self):
        good = geometry.SceneObject('good', 'water', (solid('good'),))
        for unsupported in [solid('ellipsoid', 'ellipsoid'),
            geometry.Solid('poly', 'v1', 'polytope', (3, 3, 3), (1, 1, 1), (0, 0, 0, 1),
                           ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)))]:
            with self.subTest(kind=unsupported.kind), self.assertRaises(ValueError):
                self.field(self.owner((good, geometry.SceneObject('bad', 'fault', (unsupported,)))))
        own = self.owner()
        for change in [dict(background_sigma=None), dict(background_sigma=True), dict(background_sigma=0),
                       dict(background_sigma=math.nan), dict(sample_epsilon_m=0), dict(sample_epsilon_m=math.inf),
                       dict(max_pieces=True), dict(max_pieces=257), dict(max_pieces=0),
                       dict(material_sigma={'water': 1}), dict(material_sigma=dict(POLICY, seed=1)),
                       dict(material_sigma=dict(POLICY, water=6)), dict(material_sigma=dict(POLICY, water=False))]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.field(own, **change)
        f = self.field(own, sample_epsilon_m=None)
        self.assertEqual(.02, f.sample_sigma(1, 2, 3))

    def test_pose_reader_follows_actual_new_commit_and_stop_without_mutating_owner(self):
        own = self.owner()
        f = self.field(own)
        root = own.authority_snapshot()
        before = f.pose_reader()
        self.assertIs(root, own.authority_snapshot())
        own.commit_step(self.fixture.prepare(own), lambda: self.fixture.fence())
        current = f.pose_reader()
        self.assertNotEqual(before.position_m, current.position_m)
        self.assertEqual(own.renderer_view().pose.position_m, current.position_m)
        self.assertAlmostEqual(15.5975125, current.position_m[2], places=12)
        own.revoke('synthetic STOP')
        self.assertEqual(current, f.pose_reader())
        self.assertEqual(.02, f.sample_sigma(0, 0, 0))

    def test_world_retirement_identity_digest_binding_run_epoch_and_thread_guards(self):
        for change in ['invalidate', 'scene', 'digest', 'binding', 'run', 'epoch']:
            own = self.owner()
            f = self.field(own)
            original_scene = own._scene
            original_digest = original_scene.digest
            original_binding = own._world_binding
            context = own.authority_snapshot().phase.context
            original_run, original_epoch = context.run_id, context.epoch
            with self.subTest(change=change):
                if change == 'invalidate':
                    own.invalidate_world('new world')
                elif change == 'scene':
                    own._scene = scene(())
                elif change == 'digest':
                    object.__setattr__(own._scene, 'digest', 'changed')
                elif change == 'binding':
                    own._world_binding = 'changed'
                elif change == 'run':
                    object.__setattr__(own.authority_snapshot().phase.context, 'run_id', 'foreign')
                else:
                    object.__setattr__(own.authority_snapshot().phase.context, 'epoch', 2)
                with self.assertRaises(ValueError):
                    f.pose_reader()
                own._scene = original_scene
                object.__setattr__(original_scene, 'digest', original_digest)
                own._world_binding = original_binding
                object.__setattr__(context, 'run_id', original_run)
                object.__setattr__(context, 'epoch', original_epoch)
                with self.assertRaises(ValueError):
                    f.sample_sigma(0, 0, 0)
                with self.assertRaises(ValueError):
                    f.__init__(own, material_sigma=POLICY, background_sigma=.02, max_pieces=64)
        own = self.owner()
        f = self.field(own)
        errors = []
        def foreign():
            for callback in [f.pose_reader, lambda: f.sample_sigma(0, 0, 0)]:
                try:
                    callback()
                except ValueError:
                    errors.append(True)
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        self.assertEqual([True, True], errors)
        self.assertEqual(.02, f.sample_sigma(0, 0, 0))


if __name__ == '__main__':
    unittest.main()

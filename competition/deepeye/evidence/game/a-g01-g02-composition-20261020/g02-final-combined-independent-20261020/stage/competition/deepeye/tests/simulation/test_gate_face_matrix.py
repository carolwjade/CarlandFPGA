"""Independent 36-row G02/G06 gate-face matrix.

The expectations below are explicit literals. Configuration validity and an
instantaneous whole-body plane section are not a continuous path, CCD, runtime
crossing, measured drill-envelope containment, or G02/G06 acceptance.
"""
import importlib
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[2] / 'simulation/authority/motion/gate_geometry.py'
CLEARANCE_SOURCE = Path(__file__).resolve().parents[2] / 'simulation/authority/motion/gate_clearance.py'
MODULE = 'competition.deepeye.simulation.authority.motion.gate_geometry'
CLEARANCE_MODULE = 'competition.deepeye.simulation.authority.motion.gate_clearance'

FACE_ORDER = ('top', 'bottom', 'front', 'back', 'left', 'right')
ENTRY_UV = (1.25, -2.5)
EXIT_UV = (-3.75, 4.5)
ROWS = tuple((entry, exit) for entry in FACE_ORDER for exit in FACE_ORDER)


def expected_center(face, u, v):
    if face == 'top':
        return (u, 15.0, v)
    if face == 'bottom':
        return (u, -15.0, v)
    if face == 'front':
        return (u, v, 15.0)
    if face == 'back':
        return (u, v, -15.0)
    if face == 'right':
        return (15.0, v, u)
    if face == 'left':
        return (-15.0, v, u)
    raise AssertionError('unknown explicit face ' + repr(face))


def expected_normal(face):
    return {
        'top': (0.0, 1.0, 0.0),
        'bottom': (0.0, -1.0, 0.0),
        'front': (0.0, 0.0, 1.0),
        'back': (0.0, 0.0, -1.0),
        'right': (1.0, 0.0, 0.0),
        'left': (-1.0, 0.0, 0.0),
    }[face]


def expected_abi(face):
    return {
        'top': '+Y',
        'bottom': '-Y',
        'front': '+Z',
        'back': '-Z',
        'right': '+X',
        'left': '-X',
    }[face]


def shifted(center, normal, distance):
    return tuple(c + distance * n for c, n in zip(center, normal))


class GateFaceMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = importlib.import_module(MODULE)
        cls.gc = importlib.import_module(CLEARANCE_MODULE)
        print('IMPORT_ORIGINS ' + json.dumps({'gate_geometry': cls.g.__file__, 'gate_clearance': cls.gc.__file__}))

    def setUp(self):
        self.assertEqual(Path(self.g.__file__).resolve(), SOURCE.resolve(),
                         'gate_geometry import origin must be the pinned source')
        self.assertEqual(Path(self.gc.__file__).resolve(), CLEARANCE_SOURCE.resolve(),
                         'gate_clearance import origin must be the pinned source')

    def assert_contains_radius(self, result, expected=.12, slack=1e-14):
        self.assertEqual(result.status, 'bounded')
        self.assertEqual(result.classification, 'clear')
        self.assertLessEqual(result.lower_radius_m, expected + slack)
        self.assertGreaterEqual(result.upper_radius_m, expected - slack)
        self.assertLessEqual(result.upper_radius_m - result.lower_radius_m, 1.0001e-5)

    def assert_support_contains(self, result, minimum, maximum, slack=1e-12):
        self.assertLessEqual(result.minimum.lower, minimum + slack)
        self.assertGreaterEqual(result.minimum.upper, minimum - slack)
        self.assertLessEqual(result.maximum.lower, maximum + slack)
        self.assertGreaterEqual(result.maximum.upper, maximum - slack)

    def test_matrix_is_exactly_36_ordered_pairs_with_six_same_face(self):
        self.assertEqual(len(ROWS), 36)
        self.assertEqual(len(set(ROWS)), 36)
        self.assertEqual(sum(entry == exit for entry, exit in ROWS), 6)
        self.assertEqual(sum(entry != exit for entry, exit in ROWS), 30)
        self.assertEqual(ROWS[0], ('top', 'top'))
        self.assertEqual(ROWS[1], ('top', 'bottom'))
        self.assertEqual(ROWS[6], ('bottom', 'top'))
        top_front = ROWS.index(('top', 'front'))
        front_top = ROWS.index(('front', 'top'))
        self.assertNotEqual(top_front, front_top)
        self.assertLess(top_front, front_top)

    def test_all_36_rows_bind_explicit_faces_and_g06_primitives(self):
        for row_index, (entry_face, exit_face) in enumerate(ROWS):
            with self.subTest(row=row_index, entry=entry_face, exit=exit_face):
                entry = self.g.Gate(entry_face, ENTRY_UV[0], ENTRY_UV[1])
                exit_gate = self.g.Gate(exit_face, EXIT_UV[0], EXIT_UV[1])
                self.assertEqual(entry.center_m, expected_center(entry_face, *ENTRY_UV))
                self.assertEqual(exit_gate.center_m, expected_center(exit_face, *EXIT_UV))
                self.assertEqual(entry.normal, expected_normal(entry_face))
                self.assertEqual(exit_gate.normal, expected_normal(exit_face))
                self.assertEqual(entry.abi_face, expected_abi(entry_face))
                self.assertEqual(exit_gate.abi_face, expected_abi(exit_face))
                self.assertEqual(entry.radius_m, .15)
                self.assertEqual(exit_gate.radius_m, .15)
                self.g.validate_gate_pair(entry, exit_gate)

                for role, gate in (('entry_blue', entry), ('exit_red', exit_gate)):
                    direction = -1 if role == 'entry_blue' else 1
                    axis = tuple(direction*n for n in expected_normal(gate.face))
                    capsule = self.g.Capsule(gate.center_m, axis)
                    aperture = self.g.aperture_radius_bounds(capsule, gate)
                    self.assert_contains_radius(aperture)
                    clearance = self.gc.section_clearance(
                        capsule, gate, direction=direction,
                        errors=self.gc.ErrorBounds(0., 0., 0.))
                    self.assertEqual(clearance.status, 'CLEAR_SECTION', role)
                    self.assertFalse(clearance.motion_grant, role)

                    support = self.g.plane_support(capsule, gate.plane)
                    # A normal-incidence capsule has support [-h-r,+h+r].
                    self.assert_support_contains(support, -.52, .52)
                    self.assertTrue(support.maximum.upper > 0.)
                    self.assertTrue(support.minimum.lower < 0.)

                    ahead = self.g.Capsule(shifted(gate.center_m, gate.normal, .53), gate.normal)
                    behind = self.g.Capsule(shifted(gate.center_m, gate.normal, -.53), gate.normal)
                    self.assertTrue(self.g.plane_support(ahead, gate.plane).entirely_positive)
                    self.assertTrue(self.g.plane_support(behind, gate.plane).entirely_negative)
                    wrong_direction = self.gc.section_clearance(
                        capsule, gate, direction=-direction,
                        errors=self.gc.ErrorBounds(0., 0., 0.))
                    self.assertEqual(wrong_direction.status, 'UNKNOWN')
                    self.assertFalse(wrong_direction.angle_proved)
                    self.assertFalse(wrong_direction.motion_grant)
                    tip = self.g.Capsule(shifted(gate.center_m, gate.normal, .20), axis)
                    tip_support = self.g.plane_support(tip, gate.plane)
                    self.assert_support_contains(tip_support, -.32, .72)
                    self.assertFalse(tip_support.entirely_positive)
                    self.assertFalse(tip_support.entirely_negative)
                    # 4cm tangent displacement + 12cm radius exceeds 15cm hole.
                    tangent = (1., 0., 0.) if gate.face not in ('left', 'right') else (0., 0., 1.)
                    off_axis = self.g.Capsule(shifted(gate.center_m, tangent, .04), axis)
                    refused = self.gc.section_clearance(
                        off_axis, gate, direction=direction,
                        errors=self.gc.ErrorBounds(0., 0., 0.))
                    self.assertEqual(refused.status, 'UNKNOWN')
                    self.assertFalse(refused.motion_grant)
                print('PY_MATRIX_ROW ' + json.dumps({
                    'row': row_index, 'row_id': 'entry_%s__exit_%s' % (entry_face, exit_face),
                    'entry_face': entry_face, 'exit_face': exit_face, 'result': 'pass',
                    'entry_direction': -1, 'exit_direction': 1,
                    'positive': ['explicit_center_normal_abi', 'equal_radius', 'pair_valid', 'normal_section', 'whole_body_support'],
                    'negative': ['wrong_direction_unknown', 'off_axis_unknown', 'tip_not_whole_body'],
                    'full_path_crossing': 'not_run'}))

    def test_same_face_overlap_negative_and_tangent_legal(self):
        for face in FACE_ORDER:
            with self.subTest(face=face):
                entry = self.g.Gate(face, 0., 0.)
                self.g.validate_gate_pair(entry, self.g.Gate(face, .30, 0.))
                self.g.validate_gate_pair(entry, self.g.Gate(face, 0., -.30))
                for u, v in ((0., 0.), (.299999, 0.), (0., -.299999),
                             (.21, .21)):
                    with self.subTest(face=face, overlap=(u, v)):
                        with self.assertRaises(ValueError):
                            self.g.validate_gate_pair(entry, self.g.Gate(face, u, v))
                self.assertEqual(entry.center_m, expected_center(face, 0., 0.))

    def test_edge_margin_exact_and_beyond_for_all_faces(self):
        for face in FACE_ORDER:
            with self.subTest(face=face, edge='inside'):
                gate = self.g.Gate(face, 14.85, -14.85)
                self.assertEqual(gate.center_m, expected_center(face, 14.85, -14.85))
            for u, v in ((14.850001, 0.), (0., 14.850001), (-14.850001, 0.), (0., -14.850001)):
                with self.subTest(face=face, edge=(u, v)):
                    with self.assertRaises((ValueError, TypeError)):
                        self.g.Gate(face, u, v)

    def test_strict_numeric_policy_difference_for_all_six_faces(self):
        # Preserve Python's binary64 strict limit / exact rational overlap.
        # The paired Godot test intentionally ACCEPTS the two near cases.
        # This labels a policy difference; it does not require convergence.
        from fractions import Fraction
        self.assertLess(Fraction(.2999999995), 2*Fraction(.15))
        self.assertGreater(Fraction(14.8500000005), Fraction(14.85))
        for face in FACE_ORDER:
            with self.subTest(face=face, policy='python_strict_exact'):
                entry = self.g.Gate(face, 0., 0.)
                observations = {}
                for separation, accepted in ((.30, True), (.2999999995, False), (.299999, False)):
                    with self.subTest(face=face, separation=separation):
                        exit_gate = self.g.Gate(face, separation, 0.)
                        if accepted:
                            self.g.validate_gate_pair(entry, exit_gate)
                        else:
                            with self.assertRaisesRegex(ValueError, 'same-face gate circles overlap'):
                                self.g.validate_gate_pair(entry, exit_gate)
                        observations['separation_'+str(separation)] = accepted
                for coordinate, accepted in ((14.85, True), (14.8500000005, False), (14.850001, False)):
                    with self.subTest(face=face, coordinate=coordinate):
                        if accepted:
                            gate = self.g.Gate(face, coordinate, 0.)
                            self.assertEqual(gate.u, coordinate)
                        else:
                            with self.assertRaises(ValueError):
                                self.g.Gate(face, coordinate, 0.)
                        observations['coordinate_'+str(coordinate)] = accepted
                print('PY_POLICY_ROW ' + json.dumps({'face': face, 'policy': 'python_strict_exact',
                    'observations': observations, 'editor_accepts_near_cases': True,
                    'common_near_boundary_semantics': False}))

    def test_tip_only_crossing_is_not_whole_body_passage(self):
        gate = self.g.Gate('front', 1.25, -2.5)
        tip_crossed = self.g.Capsule(shifted(gate.center_m, gate.normal, .20), gate.normal)
        support = self.g.plane_support(tip_crossed, gate.plane)
        self.assertGreater(support.maximum.upper, 0.)
        self.assertLess(support.minimum.lower, 0.)
        self.assertFalse(support.entirely_positive)
        self.assertFalse(support.entirely_negative)
        section = self.gc.section_clearance(
            self.g.Capsule(gate.center_m, gate.normal), gate,
            direction=1, errors=self.gc.ErrorBounds(0., 0., 0.))
        self.assertFalse(section.motion_grant)

    def test_candidate_capsule_limits_are_explicit(self):
        capsule = self.g.Capsule((0., 0., 15.), (0., 0., 1.))
        self.assertAlmostEqual(capsule.total_length_m, 1.04)
        self.assertEqual(capsule.envelope_status, 'candidate_requires_asset_containment_measurement')

    def test_isolated_mapping_mutations_are_detected(self):
        base_text = SOURCE.read_text(encoding='utf-8')
        mutations = (
            ("'top': (1, 15., (0., 1., 0.), '+Y'),",
             "'top': (1, 15., (0., -1., 0.), '+Y'),",
             'top-normal'),
            ("'left': (0, -15., (-1., 0., 0.), '-X'),",
             "'left': (0, 15., (-1., 0., 0.), '-X'),",
             'left-center'),
        )
        with tempfile.TemporaryDirectory(prefix='gate-face-mutation-') as temp_dir:
            for index, (old, new, label) in enumerate(mutations):
                with self.subTest(mutation=label):
                    self.assertEqual(base_text.count(old), 1)
                    mutated_text = base_text.replace(old, new)
                    path = Path(temp_dir) / ('gate_geometry_mut_%d.py' % index)
                    path.write_text(mutated_text, encoding='utf-8')
                    name = 'gate_geometry_mut_%d' % index
                    spec = importlib.util.spec_from_file_location(name, path)
                    mutated = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mutated)
                    errors = []
                    for face in FACE_ORDER:
                        gate = mutated.Gate(face, ENTRY_UV[0], ENTRY_UV[1])
                        if gate.center_m != expected_center(face, *ENTRY_UV):
                            errors.append((face, 'center', gate.center_m))
                        if gate.normal != expected_normal(face):
                            errors.append((face, 'normal', gate.normal))
                        if gate.abi_face != expected_abi(face):
                            errors.append((face, 'abi', gate.abi_face))
                    self.assertTrue(errors, 'the explicit matrix must detect ' + label)
                    self.assertEqual(errors[0][:2], ('top', 'normal') if label == 'top-normal' else ('left', 'center'))
                    print('MUTATION_CHECK ' + json.dumps({'label': label, 'source_sha256': hashlib.sha256(base_text.encode()).hexdigest(),
                        'mutant_sha256': hashlib.sha256(mutated_text.encode()).hexdigest(), 'old': old, 'new': new,
                        'detected': errors, 'result': 'pass'}))


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Renderer-only snapshots of the real numerical owner; no live authority grant."""
import importlib
import json
import math
import unittest

from competition.deepeye.tests.simulation import test_motion_executor as owner_fixture

try:
    bridge = importlib.import_module('competition.deepeye.simulation.authority.renderer_frame')
except ModuleNotFoundError as exc:
    if exc.name != 'competition.deepeye.simulation.authority.renderer_frame':
        raise
    bridge = None


def committed_frames():
    """Two actual owner commits using explicitly synthetic admitted-source fixtures."""
    fixture = owner_fixture.MotionExecutorTests()
    fixture.setUp()
    owner = fixture.make()
    frames = []
    for start in (1_000_000_000, 1_010_000_000):
        owner.commit_step(fixture.prepare(owner), lambda: fixture.fence(start=start))
        frames.append(bridge.frame_from_executor(owner))
    return owner, frames


class RendererFrameTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(bridge, 'renderer frame adapter is not implemented')

    def test_committed_owner_pose_has_only_renderer_fields_and_real_revision(self):
        owner, frames = committed_frames()
        self.assertEqual([1, 2], [f['pose_revision'] for f in frames])
        self.assertEqual([3, 4], [f['authority_revision'] for f in frames])
        self.assertEqual('run-1', frames[0]['run_id'])
        self.assertEqual([0.0, 1.0, 0.0, 0.0], frames[0]['orientation_xyzw'])
        self.assertAlmostEqual(15.5975125, frames[0]['position_m'][2], places=12)
        self.assertAlmostEqual(15.59505, frames[1]['position_m'][2], places=12)
        self.assertFalse(frames[1]['stopped'])
        self.assertEqual(set(('run_id', 'authority_revision', 'pose_revision', 'position_m',
                              'orientation_xyzw', 'stopped')), set(frames[0]))
        self.assertEqual(list(owner.renderer_view().pose.position_m), frames[1]['position_m'])
        json.dumps(frames, allow_nan=False)
        frames[1]['position_m'][2] = 999
        self.assertAlmostEqual(15.59505, owner.renderer_view().pose.position_m[2], places=12)
        owner.revoke('synthetic operator STOP')
        stopped = bridge.frame_from_executor(owner)
        self.assertTrue(stopped['stopped'])
        self.assertEqual(2, stopped['pose_revision'])
        self.assertEqual(5, stopped['authority_revision'])

    def test_invalid_frames_are_refused_instead_of_exporting_truth_or_bad_numbers(self):
        _, frames = committed_frames()
        good = frames[0]
        cases = [
            {'run_id': ''}, {'run_id': 'run\x00bad'}, {'run_id': 1},
            {'pose_revision': True}, {'pose_revision': 1.0}, {'pose_revision': -1},
            {'pose_revision': 9007199254740992}, {'stopped': 0},
            {'authority_revision': True}, {'authority_revision': 1.0},
            {'authority_revision': -1}, {'authority_revision': 9007199254740992},
            {'position_m': [0, math.nan, 0]}, {'position_m': [0, math.inf, 0]},
            {'position_m': [0, 1e100, 0]}, {'position_m': [0, True, 0]},
            {'position_m': [0, 0]}, {'orientation_xyzw': [0, 0, 0, 0]},
            {'orientation_xyzw': [0, 0, 0, 2]},
            {'orientation_xyzw': [0, 0, math.nan, 1]},
            {'scene': {}}, {'obstacles': []}, {'seed': 1},
            {'editor_history': []}, {'collision_oracle': 'CLEAR'},
        ]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                bridge.validate_frame(dict(good, **change))
        for key in good:
            bad = good.copy()
            del bad[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                bridge.validate_frame(bad)
        with self.assertRaises(TypeError):
            bridge.frame_from_executor(good)

    def test_validation_copies_json_arrays_and_keeps_unit_quaternion(self):
        _, frames = committed_frames()
        checked = bridge.validate_frame(frames[0])
        frames[0]['orientation_xyzw'][1] = 0
        self.assertEqual([0.0, 1.0, 0.0, 0.0], checked['orientation_xyzw'])


if __name__ == '__main__':
    unittest.main()

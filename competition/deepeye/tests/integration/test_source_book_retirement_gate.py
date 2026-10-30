"""NEW narrow software controls only; never load the old23 test class."""
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[4]),
    'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps']
from competition.deepeye.simulation.authority import _world_loop as loop
from competition.deepeye.simulation.authority import motion_executor as motion
from competition.deepeye.simulation.authority.motion import solid_clearance as geom
from competition.deepeye.simulation.authority.root_source_book import (
    RootSourceBook, _software_source_book_for_test)
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.tools.diagnostic.causal_pl_exchange import CausalSourcePump


class Clock:
    software_fixture_only = True

    def __init__(self):
        self.now, self.calls = 1_000_000_000, 0

    def _check(self):
        pass

    def __call__(self):
        self.calls += 1
        return self.now


class World:
    software_fixture_only = True
    _known_binding = loop._RootWorldOwner._known_binding
    _known_epoch = loop._RootWorldOwner._known_epoch
    # An explicit software API, exercising the fixed gate's real source logic.
    # This class is NOT a Root owner and never owns native resources.
    require_source_pose_current = loop._RootWorldOwner.require_source_pose_current

    def _check_thread(self):
        if threading.get_ident() != self._thread:
            raise loop.WorldRejected('software owner thread required')

    def __init__(self, clock):
        self._test, self._clock = True, clock
        self._thread = threading.get_ident()
        self._busy = self._vetoed = False
        self._foreign = threading.Event()
        self._veto_generation = 0
        self._initialized = True
        self._publication = self._em_scope_active = self._actor_link = None
        self._commits, self._renderer_revision = [], 0
        self._native = SimpleNamespace(clock_binding=clock,
            _containment_deadline=30_000_000_000, _retired=False,
            state='AUTHENTICATED')
        solid = geom.Solid('box', 'v1', 'box', (10, 0, 0), (1, 1, 1), (0, 0, 0, 1))
        scene = geom.Scene('scene', 'v1', (('rock', ('box',)),),
                           (geom.SceneObject('rock', 'hard_rock', (solid,)),))
        executor = object.__new__(motion.OwnedMotionExecutor)
        executor._owner, executor._busy, executor._pending = self._thread, False, {}
        executor._scene, executor._world_binding = scene, 'software-binding'
        pose = SimpleNamespace(position_m=(0., 0., 0.), orientation_xyzw=(0., 0., 0., 1.))
        phase = SimpleNamespace(context=SimpleNamespace(run_id='software-run', epoch=1))
        executor._root = motion._Root(0, 0, pose, 0, phase, None, None, None,
                                     True, False, False, 0)
        self.executor = executor
        self._epoch = loop._FrozenEpoch(self, 1, 'freeze', {'freeze_id': 'freeze'}, b'', None, 0)
        self._epochs, self._retired_epochs = {id(self._epoch): self._epoch}, set()
        self._binding = loop._Binding(self, self._epoch,
            SimpleNamespace(scene=scene), executor, 0, 1)
        self._bindings = {id(self._binding): self._binding}
        self._native_observation = SimpleNamespace(alive=True)
        self.polls, self.hook = 0, None

    def poll(self):
        if self._busy:
            raise AssertionError('book must poll outside owner busy')
        self.polls += 1
        if self.hook:
            self.hook()
        return 'BOUND_STOPPED'


def payload(tick=0):
    return dict(profile_id='deepeye_forward_profile_candidate_v1',
        profile_status='candidate_only',
        profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',
        source_mode='twin_fixture', adc_tick_ms=tick, em_tick_ms=None,
        channel_values=[None]*4, channel_counts=[None]*4, quality=4096)


class RetirementGateTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.world = World(self.clock)
        self.field = OwnedWorldField(self.world.executor,
            material_sigma=dict(casing=None, fault=.02, void=None,
                                water=.1, hard_rock=.01),
            background_sigma=.005, max_pieces=1)
        self.source = CausalSourcePump(self.field.pose_reader, self.field.sample_sigma)
        self.book = _software_source_book_for_test(
            self.world, self.world._binding, self.field, self.source)

    def source_start(self):
        self.clock.now += 1_000_000
        self.source.start(self.clock.now, self.clock)

    def start(self):
        self.source_start()
        self.book.start()

    def open(self):
        self.source._polling = True
        self.source._last_tick, self.source._count = 0, 1
        return self.book.open_sample(0, self.source._high)

    def unadmitted_applied(self):
        self.world._commits = [SimpleNamespace(committed=True, uncertainty=None)]
        self.world._publication = SimpleNamespace(kind='PUBLISH_VIEW', resolved=True,
            state='APPLIED', getter_admitted=False, revision=0)

    def assert_failed(self):
        evidence = self.book.evidence()
        self.assertEqual('FAILED', evidence['state'])
        self.assertEqual('FAILED', self.source.state)
        self.assertEqual('unavailable;fixed_revision_only', evidence['action_association'])

    def test_busy_start_retire_cannot_revive_running(self):
        self.source_start()
        def retire_once():
            self.world.hook = None
            self.book.retire('retired during start owner poll')
        self.world.hook = retire_once
        with self.assertRaises(RuntimeError):
            self.book.start()
        self.assert_failed()
        with self.assertRaises(RuntimeError):
            self.book.start()

    def test_stopped_initial_gate_allows_a_software_record(self):
        self.start()
        token = self.open()
        self.book.read_pose(token, 'em')
        self.book.read_pose(token, 'adc')
        handle = self.book.begin_adc(token)
        self.source._profile._last_adc_tick = 0  # Software progress; no sample_adc.
        self.book.end_adc(token, handle)
        self.book.finish_sample(token, payload())
        self.assertEqual(1, len(self.book.evidence()['samples']))
        self.assertIsNot(type(self.book), RootSourceBook)

    def test_pending_action_gate_blocks_em_pose_before_read(self):
        self.start()
        token = self.open()
        self.world._actor_link = SimpleNamespace(slot=SimpleNamespace(committed=False))
        with self.assertRaises(loop.WorldRejected):
            self.book.read_pose(token, 'em')
        self.assert_failed()
        partial = self.book.evidence()['partial_samples'][0]
        self.assertNotIn('em', partial['pose_reads'])

    def test_uncertain_action_gate_blocks_open_source_slot(self):
        self.start()
        self.world._commits = [SimpleNamespace(committed=False, uncertainty='unknown')]
        with self.assertRaises(loop.WorldRejected):
            self.open()
        self.assert_failed()
        self.assertEqual([], self.book.evidence()['samples'])

    def test_unadmitted_applied_gate_blocks_adc_pose_and_emission(self):
        self.start()
        token = self.open()
        self.book.read_pose(token, 'em')
        self.unadmitted_applied()
        with self.assertRaises(loop.WorldRejected):
            self.book.read_pose(token, 'adc')
        self.assert_failed()
        self.assertEqual([], self.book.evidence()['samples'])
        self.assertNotIn('adc', self.book.evidence()['partial_samples'][0]['pose_reads'])

    def test_gate_changed_after_adc_blocks_finish_and_preserves_partial(self):
        self.start()
        token = self.open()
        self.book.read_pose(token, 'em')
        self.book.read_pose(token, 'adc')
        handle = self.book.begin_adc(token)
        self.source._profile._last_adc_tick = 0
        self.book.end_adc(token, handle)
        self.unadmitted_applied()
        with self.assertRaises(loop.WorldRejected):
            self.book.finish_sample(token, payload())
        self.assert_failed()
        evidence = self.book.evidence()
        self.assertEqual([], evidence['samples'])
        self.assertTrue(evidence['partial_samples'][0]['adc']['profile_tick_observed'])

    def test_normal_retire_is_clockless_and_active_retire_preserves_partial(self):
        self.start()
        before = self.clock.calls, self.world.polls
        self.book.retire('normal Root cleanup')
        self.assertEqual(before, (self.clock.calls, self.world.polls))
        self.assertEqual('RETIRED', self.book.evidence()['state'])
        self.assertEqual('RUNNING', self.source.state)
        self.setUp()
        self.start()
        self.open()
        before = self.clock.calls, self.world.polls
        self.book.retire('incomplete source')
        self.assertEqual(before, (self.clock.calls, self.world.polls))
        self.assert_failed()
        self.assertEqual(1, len(self.book.evidence()['partial_samples']))


if __name__ == '__main__':
    unittest.main()

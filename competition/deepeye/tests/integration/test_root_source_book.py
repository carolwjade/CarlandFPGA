"""NEW software-only source time controls; no producer/kernel/native runs."""
from dataclasses import replace
import hashlib
import importlib
import json
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
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.simulation.sensors.forward_profile import Pose
from competition.deepeye.tools.diagnostic.causal_pl_exchange import CausalSourcePump
try:
    module = importlib.import_module(
        'competition.deepeye.simulation.authority.root_source_book')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.authority.root_source_book':
        raise
    module = None


class Clock:
    software_fixture_only = True

    def __init__(self):
        self.now = 1_000_000_000
        self.calls = 0
        self.failure = None

    def _check(self):
        if self.failure is not None:
            raise self.failure

    def __call__(self):
        self._check()
        self.calls += 1
        return self.now


class World:
    software_fixture_only = True
    _known_binding = loop._RootWorldOwner._known_binding
    _known_epoch = loop._RootWorldOwner._known_epoch

    def __init__(self, clock):
        self._test = True
        self._clock = clock
        self._thread = threading.get_ident()
        self._foreign = threading.Event()
        self._busy = self._vetoed = False
        self._veto_generation = 0
        self._initialized = True
        self._publication = None
        self._em_scope_active = None
        self._native = SimpleNamespace(clock_binding=clock,
            _containment_deadline=30_000_000_000, _retired=False,
            state='AUTHENTICATED')
        solid = geom.Solid('literal-box', 'v1', 'box', (10, 0, 0),
                           (1, 1, 1), (0, 0, 0, 1))
        scene = geom.Scene('literal-scene', 'v1', (('rock', ('literal-box',)),),
                           (geom.SceneObject('rock', 'hard_rock', (solid,)),))
        executor = object.__new__(motion.OwnedMotionExecutor)
        executor._owner = self._thread
        executor._busy = False
        executor._pending = {}
        executor._scene = scene
        executor._world_binding = 'literal-binding'
        pose = SimpleNamespace(position_m=(0., 0., 0.),
                               orientation_xyzw=(0., 0., 0., 1.))
        phase = SimpleNamespace(context=SimpleNamespace(run_id='literal-run', epoch=1))
        executor._root = motion._Root(0, 0, pose, 0, phase, None, None, None,
                                     True, False, False, 0)
        self.executor = executor
        self._epoch = loop._FrozenEpoch(self, 1, 'literal-freeze',
            {'freeze_id': 'literal-freeze'}, b'', None, 0)
        self._epochs = {id(self._epoch): self._epoch}
        self._retired_epochs = set()
        self._binding = loop._Binding(self, self._epoch,
            SimpleNamespace(scene=scene), executor, 0, 1)
        self._bindings = {id(self._binding): self._binding}
        self._native_observation = SimpleNamespace(alive=True)
        self.polls = 0
        self.hook = None

    def poll(self):
        if self._busy:
            raise AssertionError('book poll must be explicit outside owner busy')
        self.polls += 1
        if self.hook:
            self.hook()
        return 'BOUND_STOPPED'

    def close(self):
        raise AssertionError('book must never own cleanup')


def fault_payload(tick):
    return dict(profile_id='deepeye_forward_profile_candidate_v1',
        profile_status='candidate_only',
        profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',
        source_mode='twin_fixture', adc_tick_ms=tick, em_tick_ms=None,
        channel_values=[None]*4, channel_counts=[None]*4, quality=4096)


class SourceBookTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(module, 'RootSourceBook feature is missing')
        self.clock = Clock()
        self.world = World(self.clock)
        self.field = OwnedWorldField(self.world.executor,
            material_sigma=dict(casing=None, fault=.02, void=None,
                                water=.1, hard_rock=.01),
            background_sigma=.005, max_pieces=1)
        self.source = CausalSourcePump(self.field.pose_reader, self.field.sample_sigma)
        self.book = module._software_source_book_for_test(
            self.world, self.world._binding, self.field, self.source)

    def start(self):
        self.clock.now += 1_000_000
        self.source.start(self.clock.now, self.clock)
        self.book.start()

    def open(self, tick=0):
        self.clock.now = self.source._origin + tick*1_000_000
        self.source._high = self.clock.now
        self.source._last_tick = tick
        self.source._count += 1
        self.source._polling = True
        return self.book.open_sample(tick, self.clock.now)

    def complete(self, tick=0):
        token = self.open(tick)
        if tick % 50 == 0:
            self.book.read_pose(token, 'em')
        self.book.read_pose(token, 'adc')
        handle = self.book.begin_adc(token)
        # Explicit software fixture progress only: sample_adc is never executed.
        self.source._profile._last_adc_tick = tick
        self.book.end_adc(token, handle)
        payload = fault_payload(tick)
        self.book.finish_sample(token, payload)
        self.source._polling = False
        return token, payload

    def assert_failed(self):
        self.assertEqual('FAILED', self.book.evidence()['state'])
        self.assertEqual('FAILED', self.source.state)

    def test_readonly_identity_properties_have_no_hidden_io(self):
        before = self.clock.calls, self.world.polls
        self.assertIs(self.book.clock, self.clock)
        self.assertIs(self.book.source, self.source)
        with self.assertRaises(AttributeError):
            self.book.clock = Clock()
        with self.assertRaises(AttributeError):
            self.book.source = object()
        self.assertEqual(before, (self.clock.calls, self.world.polls))

    def test_nominal_and_actual_late_brackets_are_preserved_separately(self):
        self.start()
        token = self.open()
        nominal = self.source._origin
        self.clock.now = nominal + 316_000_000
        self.assertIsInstance(self.book.read_pose(token, 'em'), Pose)
        self.book.read_pose(token, 'adc')
        handle = self.book.begin_adc(token)
        self.clock.now += 1_000_000
        self.source._profile._last_adc_tick = 0
        self.book.end_adc(token, handle)
        self.book.finish_sample(token, fault_payload(0))
        evidence = self.book.evidence()
        record = evidence['samples'][0]
        self.assertEqual(nominal, record['nominal_qpc_ns'])
        self.assertEqual(nominal+316_000_000, record['pose_reads']['em']['begin_qpc_ns'])
        self.assertEqual(nominal+317_000_000, record['adc']['end_qpc_ns'])
        self.assertEqual('unavailable;fixed_revision_only', evidence['action_association'])
        self.assertFalse(evidence['native_interval_atomic'])
        self.assertNotIn('executed_actions', evidence)
        self.assertNotIn('SourceLedger_admitted', record)

    def test_canonical_payload_and_evidence_are_detached(self):
        self.start()
        _, payload = self.complete()
        first = self.book.evidence()
        record = first['samples'][0]
        raw = bytes.fromhex(record['canonical_source_hex'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), record['source_sha256'])
        self.assertEqual(payload, json.loads(raw))
        payload['quality'] = 0
        first['samples'][0]['payload']['quality'] = 0
        self.assertEqual(4096, self.book.evidence()['samples'][0]['payload']['quality'])

    def test_start_requires_original_running_source_and_is_once(self):
        with self.assertRaises(ValueError):
            self.book.start()
        self.assert_failed()
        self.setUp()
        self.start()
        with self.assertRaises(ValueError):
            self.book.start()
        self.assert_failed()

    def test_observed_must_be_original_source_high_water_in_its_bin(self):
        for offset in (-1, 10_000_000, True):
            with self.subTest(offset=offset):
                self.setUp()
                self.start()
                self.source._polling = True
                self.source._last_tick = 0
                self.source._count = 1
                observed = offset if type(offset) is bool else self.source._origin+offset
                self.source._high = observed
                self.clock.now = self.source._origin+10_000_000
                with self.assertRaises(ValueError):
                    self.book.open_sample(0, observed)
                self.assert_failed()

    def test_source_slot_must_be_consumed_polling_and_complete_prefix(self):
        for attr, value in (('_polling', False), ('_count', 2), ('_last_tick', 10)):
            with self.subTest(attr=attr):
                self.setUp()
                self.start()
                self.source._polling = True
                self.source._count = 1
                self.source._last_tick = 0
                setattr(self.source, attr, value)
                with self.assertRaises(ValueError):
                    self.book.open_sample(0, self.source._origin)
                self.assert_failed()

    def test_required_pose_reads_and_adc_bracket_cannot_be_omitted(self):
        self.start()
        token = self.open()
        with self.assertRaises(ValueError):
            self.book.finish_sample(token, fault_payload(0))
        self.assert_failed()
        self.assertEqual(1, len(self.book.evidence()['partial_samples']))

    def test_pose_kind_order_and_em_grid_are_strict(self):
        for kind in ('adc', 'other', 1):
            with self.subTest(kind=kind):
                self.setUp()
                self.start()
                token = self.open()
                with self.assertRaises(ValueError):
                    self.book.read_pose(token, kind)
                self.assert_failed()
        self.setUp()
        self.start()
        token = self.open(10)
        with self.assertRaises(ValueError):
            self.book.read_pose(token, 'em')

    def test_adc_handle_is_original_one_use_and_profile_progress_required(self):
        self.start()
        token = self.open()
        self.book.read_pose(token, 'em')
        self.book.read_pose(token, 'adc')
        handle = self.book.begin_adc(token)
        with self.assertRaises(ValueError):
            self.book.end_adc(token, handle)
        self.assert_failed()
        self.setUp()
        self.start()
        token = self.open()
        self.book.read_pose(token, 'em')
        self.book.read_pose(token, 'adc')
        self.book.begin_adc(token)
        with self.assertRaises(ValueError):
            self.book.end_adc(token, {})

    def test_finished_token_cannot_be_replayed(self):
        self.start()
        token, payload = self.complete()
        self.source._polling = True
        with self.assertRaises(ValueError):
            self.book.finish_sample(token, payload)
        self.assertEqual(1, len(self.book.evidence()['samples']))
        self.assert_failed()

    def test_payload_tick_and_whitelist_are_validated_without_admission(self):
        self.start()
        token = self.open()
        self.book.read_pose(token, 'em')
        self.book.read_pose(token, 'adc')
        handle = self.book.begin_adc(token)
        self.source._profile._last_adc_tick = 0
        self.book.end_adc(token, handle)
        payload = fault_payload(0)
        payload['truth'] = 1
        with self.assertRaises(ValueError):
            self.book.finish_sample(token, payload)
        self.assert_failed()

    def test_committed_revision_change_is_unavailable_not_empty_action_record(self):
        self.start()
        token = self.open()
        root = self.world.executor._root
        self.world.executor._root = replace(root, revision=1, pose_revision=1)
        with self.assertRaises(ValueError):
            self.book.read_pose(token, 'em')
        self.assert_failed()
        self.assertNotIn('executed_actions', self.book.evidence())

    def test_binding_field_native_clock_and_veto_mutations_fail_closed(self):
        changes = (lambda: self.world._bindings.clear(),
            lambda: setattr(self.world, '_vetoed', True),
            lambda: setattr(self.world, '_veto_generation', 1),
            lambda: self.world._foreign.set(),
            lambda: setattr(self.world._native, '_retired', True),
            lambda: setattr(self.world, '_clock', Clock()),
            lambda: setattr(self.source, '_sampler', self.field.sample_sigma),
            lambda: setattr(self.source, '_profile', object()),
            lambda: setattr(self.field, '_retired', True),
            lambda: object.__setattr__(self.field._scene.objects[0].parts[0],
                                      'centre', (20, 0, 0)))
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                self.start()
                token = self.open()
                change()
                with self.assertRaises(ValueError):
                    self.book.read_pose(token, 'em')
                self.assert_failed()

    def test_clock_regression_original_exception_and_expiry_are_not_rebased(self):
        self.start()
        token = self.open()
        self.clock.now -= 1
        with self.assertRaises(ValueError):
            self.book.read_pose(token, 'em')
        self.assert_failed()
        self.setUp()
        self.start()
        token = self.open()
        original = ArithmeticError('original raw clock failed')
        self.clock.failure = original
        with self.assertRaises(ArithmeticError) as caught:
            self.book.read_pose(token, 'em')
        self.assertIs(original, caught.exception)
        self.assert_failed()

    def test_foreign_call_only_contaminates_without_clock_or_owner_io(self):
        self.start()
        token = self.open()
        before = self.clock.calls, self.world.polls
        errors = []
        def foreign():
            try:
                self.book.read_pose(token, 'em')
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(1)
        self.assertFalse(thread.is_alive())
        self.assertEqual(1, len(errors))
        self.assertEqual(before, (self.clock.calls, self.world.polls))
        self.assertEqual('RUNNING', self.source.state)
        with self.assertRaises(RuntimeError):
            self.book.read_pose(token, 'em')
        self.assert_failed()

    def test_swallowed_reentry_is_sticky_and_original_business_error_survives(self):
        self.start()
        def reenter():
            with self.assertRaises(RuntimeError):
                self.book.start()
        self.world.hook = reenter
        with self.assertRaises(RuntimeError):
            self.open()
        self.assert_failed()
        self.setUp()
        self.start()
        primary = LookupError('original owner business error')
        def fail():
            raise primary
        self.world.hook = fail
        with self.assertRaises(LookupError) as caught:
            self.open()
        self.assertIs(primary, caught.exception)
        self.assert_failed()

    def test_pure_fail_preserves_partial_without_io_or_primary_masking(self):
        self.start()
        self.open()
        before = self.clock.calls, self.world.polls
        self.clock.failure = ArithmeticError('must not be read by fail')
        self.book.fail('original pump failed')
        self.book.fail(object())
        self.assertEqual(before, (self.clock.calls, self.world.polls))
        self.assert_failed()
        evidence = self.book.evidence()
        self.assertEqual(1, len(evidence['partial_samples']))
        self.assertEqual('original pump failed', evidence['failure_reason'])
        self.book.retire('cleanup')
        self.assert_failed()

    def test_retire_preserves_history_and_does_not_retire_source(self):
        self.start()
        self.complete()
        before = self.clock.calls, self.world.polls
        self.book.retire('Root finished')
        self.assertEqual(before, (self.clock.calls, self.world.polls))
        self.assertEqual('RETIRED', self.book.evidence()['state'])
        self.assertEqual('RUNNING', self.source.state)
        self.assertEqual(1, len(self.book.evidence()['samples']))

    def test_1001_record_bound_keeps_full_history_and_never_evicts(self):
        self.start()
        for tick in range(0, 10_001, 10):
            self.complete(tick)
        evidence = self.book.evidence()
        self.assertEqual(1001, len(evidence['samples']))
        self.assertEqual(0, evidence['samples'][0]['tick_ms'])
        with self.assertRaises(ValueError):
            self.open(10_010)
        self.assertEqual(1001, len(self.book.evidence()['samples']))
        self.assert_failed()

    def test_public_entry_cannot_accept_software_or_promote_private_core(self):
        with self.assertRaises(ValueError):
            module.RootSourceBook(self.world, self.world._binding,
                                  self.field, self.source)
        self.assertIsNot(type(self.book), module.RootSourceBook)
        with self.assertRaises(ValueError):
            module._software_source_book_for_test(
                object.__new__(loop._RootWorldOwner), self.world._binding,
                self.field, self.source)
        class Derived(module.RootSourceBook):
            pass
        with self.assertRaises(ValueError):
            Derived(self.world, self.world._binding, self.field, self.source)

    def test_post_pose_poll_failure_preserves_already_observed_bracket(self):
        self.start()
        token = self.open()
        target = self.world.polls+2
        original = LookupError('post pose poll failed')
        def after_read():
            if self.world.polls == target:
                raise original
        self.world.hook = after_read
        with self.assertRaises(LookupError) as caught:
            self.book.read_pose(token, 'em')
        self.assertIs(original, caught.exception)
        partial = self.book.evidence()['partial_samples'][0]
        self.assertIn('em', partial['pose_reads'])
        self.assertFalse(partial['pose_reads']['em']['postcheck_complete'])
        self.assert_failed()

    def test_original_revision_scalar_is_retained_separately_from_root_reference(self):
        self.start()
        token = self.open()
        # Software endpoint tamper control, never a production owner mutation.
        object.__setattr__(self.world.executor._root, 'revision', 1)
        with self.assertRaises(ValueError):
            self.book.read_pose(token, 'em')
        self.assert_failed()

    def test_expired_original_origin_cannot_start_or_extend_the_session(self):
        self.clock.now += 1_000_000
        origin = self.clock.now
        self.source.start(origin, self.clock)
        self.clock.now = origin+10_000_000_001
        with self.assertRaises(ValueError):
            self.book.start()
        self.assertEqual(origin, self.source._origin)
        self.assert_failed()
        self.setUp()
        self.start()
        token = self.open()
        self.clock.now = self.source._origin+10_000_000_001
        with self.assertRaises(ValueError):
            self.book.read_pose(token, 'em')
        self.assert_failed()


if __name__ == '__main__':
    unittest.main()

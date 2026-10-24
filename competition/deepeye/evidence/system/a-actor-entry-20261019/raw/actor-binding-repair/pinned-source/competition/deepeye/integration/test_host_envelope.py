"""Adversarial tests for the bounded host-envelope validator (records only).

These tests build and mutate in-memory envelopes. They never touch a board,
model, network, service, credential or live ledger, and passing them is a
software structure check, not product acceptance or motion permission.
"""
import copy
import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_UNSET = object()


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


wire = _load('deepeye_wire_testdep', 'wire.py')
try:
    host_envelope = _load('deepeye_host_envelope', 'host_envelope.py')
except FileNotFoundError:
    host_envelope = None

CONTEXT = dict(session=7, config_epoch=2, boot_sha256='a' * 64, transport_profile_id=1,
               source_id=3, topology_id=1, acquisition_profile_id=1)
STRESS_CONTEXT = dict(CONTEXT, transport_profile_id=2)
NOW_NS = 5_000_000_000
MODE_FAST_SENSOR_HIL = 1 | (3 << 2) | (1 << 5)


def encode(document):
    return json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def message(kind, context=None, **fields):
    document = dict(schema_version=1, context=copy.deepcopy(context or CONTEXT), kind=kind)
    document.update(fields)
    return document


def target(action=1, yaw=0, pitch=0, speed=5, duration=1000):
    return dict(action=action, yaw_q=yaw, pitch_q=pitch, speed_code=speed, duration_ms=duration)


def observation_key(context=None, seq=9):
    return dict(context=copy.deepcopy(context or CONTEXT), observed_seq=seq)


def pose(quaternion=(0.0, 0.0, 0.0, 1.0), position=(0.0, 0.0, 0.0),
         position_error=0.01, orientation_error=0.001):
    return dict(position_m=list(position), orientation_xyzw=list(quaternion),
                position_error_bound_m=position_error,
                orientation_error_bound_rad=orientation_error)


def telem_frame(epoch=2, seq=9, tick=1234, mean=(1, 2, 3, 4), ranges=(5, 6, 7, 8), quality=3):
    payload = struct.pack('<4H4HH', *(list(mean) + list(ranges) + [quality]))
    return wire.encode(wire.Frame(1, epoch, seq, tick, payload))


def event_frame(epoch=2, seq=9, tick=1234, bitmap=1, channel=2, severity=3, peak=99):
    payload = struct.pack('<HBBH', bitmap, channel, severity, peak)
    return wire.encode(wire.Frame(2, epoch, seq, tick, payload))


def telem_document(context=None, count=50, seq=9, tick=1234, epoch=None,
                   mean=(1, 2, 3, 4), ranges=(5, 6, 7, 8), quality=3,
                   receipt=None, adc_last=None, adc_first=None, native_em=None):
    active = copy.deepcopy(context or CONTEXT)
    frame = telem_frame(active['config_epoch'] if epoch is None else epoch,
                        seq, tick, mean, ranges, quality)
    return message('telem_observation', context=active, observed_seq=seq, tick_ms_raw=tick,
                   receipt_interval_ns=receipt if receipt is not None
                   else dict(lower_ns=NOW_NS - 1000, upper_ns=NOW_NS - 500),
                   adc_last_interval_ns=adc_last if adc_last is not None
                   else dict(lower_ns=NOW_NS - 900, upper_ns=NOW_NS - 100),
                   adc_first_interval_ns=adc_first, native_em_interval_ns=native_em,
                   sample_count=count, mean_counts=list(mean), range_counts=list(ranges),
                   quality_flags=quality, wire_frame_hex=frame.hex())


def event_document(context=None, seq=9, tick=1234, epoch=None, bitmap=1, channel=2,
                   severity=3, peak=99, receipt=None, trigger=None):
    active = copy.deepcopy(context or CONTEXT)
    frame = event_frame(active['config_epoch'] if epoch is None else epoch,
                        seq, tick, bitmap, channel, severity, peak)
    return message('event_observation', context=active, observed_seq=seq, tick_ms_raw=tick,
                   receipt_interval_ns=receipt if receipt is not None
                   else dict(lower_ns=NOW_NS - 1000, upper_ns=NOW_NS - 500),
                   trigger_sample_interval_ns=trigger,
                   bitmap=bitmap, channel=channel, severity=severity, peak_counts=peak,
                   wire_frame_hex=frame.hex())

def candidate_document(context=None, target_value=None, observation=_UNSET,
                       candidate_id=1, completed=None):
    active = copy.deepcopy(context or CONTEXT)
    if target_value is None:
        target_value = target()
    if observation is _UNSET:
        observation = observation_key(active)
    return message('model_candidate', context=active, candidate_id=candidate_id,
                   model_sha256='b' * 64, observation=observation,
                   completed_monotonic_ns=NOW_NS - 1 if completed is None else completed,
                   target=target_value)


def request_document(context=None, target_value=None, observation=_UNSET,
                     candidate_id=1, command_seq=3, issue=None):
    active = copy.deepcopy(context or CONTEXT)
    if target_value is None:
        target_value = target()
    if observation is _UNSET:
        observation = observation_key(active)
    return message('motion_request', context=active, candidate_id=candidate_id,
                   command_seq=command_seq, observation=observation,
                   host_issue_monotonic_ns=NOW_NS - 1 if issue is None else issue,
                   target=target_value)


def grant_document(context=None, target_value=None, observation=_UNSET,
                   action_source='board_capture', capture_seq=5, deadline=None, command_seq=3):
    active = copy.deepcopy(context or CONTEXT)
    if target_value is None:
        target_value = target()
    if observation is _UNSET:
        observation = observation_key(active)
    return message('motion_grant', context=active, command_seq=command_seq,
                   observation=observation, target=target_value, action_source=action_source,
                   deadline_monotonic_ns=NOW_NS + 1_000_000 if deadline is None else deadline,
                   capture_seq=capture_seq)


def odometry_document(pose_value=None, at_interval=None, context=None):
    return message('odometry', context=copy.deepcopy(context or CONTEXT),
                   at_interval_ns=at_interval if at_interval is not None
                   else dict(lower_ns=NOW_NS - 500, upper_ns=NOW_NS - 400),
                   pose=pose() if pose_value is None else pose_value,
                   provenance='executed_motion_integrator')


def geometry_document(entry_face='+X', entry_center=(15.0, 0.0, 0.0), exit_face='-X',
                      exit_center=(-15.0, 3.0, -4.0), entry_radius=0.15, exit_radius=0.15,
                      initial=None):
    return message('public_task_geometry', cube_half_extent_m=15, drill_radius_m=0.12,
                   drill_length_m=0.8, minimum_turn_radius_m=2, acceleration_bound_m_s2=0.25,
                   entry_blue=dict(face=entry_face, center_m=list(entry_center),
                                   radius_m=entry_radius),
                   exit_red=dict(face=exit_face, center_m=list(exit_center),
                                 radius_m=exit_radius),
                   initial_odometry=pose() if initial is None else initial)


def config_ack_frame(session=7, request_type=5, phase=2, applied_epoch=2, epoch=2):
    payload = struct.pack('<IHBBBBBHBBBH', session, 3, request_type, phase, 1, 0, 0, 100,
                          0, 0, applied_epoch, 0)
    return wire.encode(wire.Frame(9, epoch, 4, 111, payload))


def gain_ack_frame(session=7, request_type=10, phase=2, epoch=2):
    payload = struct.pack('<IHBBBHHHHB', session, 3, request_type, phase, 2, 512, 900, 0, 1, 0)
    return wire.encode(wire.Frame(11, epoch, 4, 111, payload))


def boot_ack_frame(session=7, mode=MODE_FAST_SENSOR_HIL, epoch=2):
    payload = struct.pack('<IB16sHHH', session, mode, bytes(16), 100, 50, 25)
    return wire.encode(wire.Frame(13, epoch, 4, 111, payload))


def ack3d_frame(session=7, request_type=14, phase=3, control_epoch=2, fault_flags=0,
                quality=15, epoch=2):
    payload = struct.pack('<IHBBhhBHBHBB', session, 3, request_type, phase, 57, 0, 20, 900,
                          fault_flags, 5, control_epoch, quality)
    return wire.encode(wire.Frame(15, epoch, 4, 111, payload))


def state3d_frame(session=7, phase=2, control_epoch=2, fault_flags=0, quality=15, epoch=2):
    payload = struct.pack('<IHhhBBHHHBB', session, 3, 57, 0, 20, phase, 900, fault_flags, 5,
                          control_epoch, quality)
    return wire.encode(wire.Frame(16, epoch, 4, 111, payload))


def response_document(frame, receipt=None):
    return message('board_response',
                   receipt_interval_ns=receipt if receipt is not None
                   else dict(lower_ns=NOW_NS - 100, upper_ns=NOW_NS - 50),
                   wire_frame_hex=frame.hex(), timing_record_sha256=None,
                   physical_capture_record_sha256=None)

class HostEnvelopeTests(unittest.TestCase):
    def setUp(self):
        if host_envelope is None:
            self.fail('integration/host_envelope.py is absent; bounded host-envelope validator not implemented')

    def accept(self, document, producer='hardware_bridge', context=None, now=NOW_NS, consumer=None):
        return host_envelope.validate_message(encode(document), producer=producer,
                                              context=copy.deepcopy(context or CONTEXT),
                                              now_ns=now, consumer=consumer)

    def reject(self, document, producer='hardware_bridge', context=None, now=NOW_NS, consumer=None):
        with self.assertRaises(ValueError):
            host_envelope.validate_message(encode(document), producer=producer,
                                           context=copy.deepcopy(context or CONTEXT),
                                           now_ns=now, consumer=consumer)

    def reject_raw(self, raw, producer='hardware_bridge', context=None, now=NOW_NS):
        with self.assertRaises(ValueError):
            host_envelope.validate_message(raw, producer=producer,
                                           context=copy.deepcopy(context or CONTEXT),
                                           now_ns=now)

    # --- valid examples ---------------------------------------------------
    def test_valid_telem_fast_50_and_stress_800(self):
        record = self.accept(telem_document(count=50))
        self.assertEqual(record.kind, 'telem_observation')
        self.assertEqual(record.producer, 'hardware_bridge')
        self.assertFalse(record.authority_only)
        self.accept(telem_document(context=STRESS_CONTEXT, count=800), context=STRESS_CONTEXT)

    def test_valid_mapped_sample_upper_may_extend_beyond_now(self):
        self.accept(telem_document(adc_last=dict(lower_ns=NOW_NS - 10, upper_ns=NOW_NS + 10_000_000)))

    def test_valid_event_observation(self):
        self.accept(event_document(), producer='hardware_bridge')

    def test_valid_candidate_stop_and_set_target(self):
        stop = candidate_document(target_value=target(action=0, speed=0, duration=0),
                                  observation=None)
        self.accept(stop, producer='ai_controller')
        set_target = candidate_document(target_value=target(action=1, yaw=57, speed=20,
                                                            duration=3000), completed=NOW_NS)
        self.accept(set_target, producer='ai_controller')

    def test_valid_motion_request_both_actions(self):
        self.accept(request_document(), producer='control_broker')
        stop = request_document(target_value=target(action=0, speed=0, duration=0),
                                observation=None)
        self.accept(stop, producer='control_broker')

    def test_valid_motion_grant_all_three_topologies(self):
        self.accept(grant_document(), producer='world_authority')
        pc_context = dict(CONTEXT, topology_id=2)
        self.accept(grant_document(context=pc_context, action_source='pc_direct_host',
                                   capture_seq=None), context=pc_context, producer='world_authority')
        local_context = dict(CONTEXT, topology_id=3)
        self.accept(grant_document(context=local_context, action_source='fpga_local_capture',
                                   capture_seq=9), context=local_context,
                    producer='world_authority')

    def test_valid_odometry_unit_quaternion(self):
        self.accept(odometry_document(), producer='world_authority')
        self.accept(odometry_document(pose_value=pose(quaternion=(0.5, 0.5, 0.5, 0.5))),
                    producer='world_authority')
        self.accept(odometry_document(pose_value=pose(quaternion=(0.0, 0.0, 0.0, 1.0005))),
                    producer='world_authority')

    def test_valid_public_task_geometry(self):
        self.accept(geometry_document(), producer='world_authority')
        self.accept(geometry_document(entry_center=(15.0, 14.84, 0.0)), producer='world_authority')

    def test_valid_board_response_all_five_permitted_types(self):
        for frame in (config_ack_frame(), gain_ack_frame(), boot_ack_frame(),
                      ack3d_frame(), state3d_frame()):
            with self.subTest(frame=frame.hex()[:12]):
                record = self.accept(response_document(frame))
                self.assertEqual(record.kind, 'board_response')
                self.assertTrue(record.authority_only)

    def test_board_response_consumer_default_and_unsafe_routing(self):
        document = response_document(config_ack_frame())
        self.accept(document, consumer=None)
        self.accept(document, consumer='world_authority')
        with self.assertRaises(ValueError):
            self.accept(document, consumer='ai_controller')
        with self.assertRaises(ValueError):
            self.accept(document, consumer='bogus_role')
        self.accept(telem_document(), consumer='world_authority')
        with self.assertRaises(ValueError):
            self.accept(telem_document(), consumer='bogus_role')
    # --- strict JSON identity ---------------------------------------------
    def test_bool_and_float_identities_rejected_in_integer_enum_const_fields(self):
        mutations = [
            ('context.session bool', lambda d: d['context'].__setitem__('session', True)),
            ('context.config_epoch float', lambda d: d['context'].__setitem__('config_epoch', 2.0)),
            ('context.transport_profile float', lambda d: d['context'].__setitem__('transport_profile_id', 1.0)),
            ('schema_version float', lambda d: d.__setitem__('schema_version', 1.0)),
            ('sample_count float identity', lambda d: d.__setitem__('sample_count', 50.0)),
            ('tick_ms_raw bool', lambda d: d.__setitem__('tick_ms_raw', True)),
            ('observed_seq bool', lambda d: d.__setitem__('observed_seq', False)),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                document = telem_document()
                mutate(document)
                self.reject(document)
        target_mutations = [
            ('action bool', lambda t: t.__setitem__('action', True)),
            ('duration float identity', lambda t: t.__setitem__('duration_ms', 1000.0)),
            ('speed bool', lambda t: t.__setitem__('speed_code', True)),
            ('yaw float identity', lambda t: t.__setitem__('yaw_q', 5.0)),
        ]
        for label, mutate in target_mutations:
            with self.subTest(label=label):
                document = request_document()
                mutate(document['target'])
                self.reject(document, producer='control_broker')
        with self.subTest(label='capture_seq float identity'):
            document = grant_document()
            document['capture_seq'] = 5.0
            self.reject(document, producer='world_authority')
        with self.subTest(label='gate radius bool'):
            self.reject(geometry_document(entry_radius=True), producer='world_authority')
        with self.subTest(label='pose coordinate bool'):
            self.reject(odometry_document(pose_value=pose(position=(True, 0.0, 0.0))),
                        producer='world_authority')

    def test_nested_duplicate_keys_rejected(self):
        telem_raw = encode(telem_document()).decode('utf-8')
        request_raw = encode(request_document()).decode('utf-8')
        cases = [
            ('top-level duplicate',
             telem_raw.replace('"kind":"telem_observation"',
                               '"kind":"telem_observation","kind":"telem_observation"'),
             telem_raw, 'hardware_bridge'),
            ('context duplicate',
             telem_raw.replace('"session":7', '"session":7,"session":7'),
             telem_raw, 'hardware_bridge'),
            ('interval duplicate',
             telem_raw.replace('"lower_ns":4999999000',
                               '"lower_ns":4999999000,"lower_ns":4999999000'),
             telem_raw, 'hardware_bridge'),
            ('target duplicate',
             request_raw.replace('"action":1', '"action":1,"action":1'),
             request_raw, 'control_broker'),
        ]
        for label, text, original, producer in cases:
            with self.subTest(label=label):
                self.assertNotEqual(text, original)
                self.reject_raw(text.encode('utf-8'), producer=producer)

    def test_raw_wire_crc_type_layout_mismatches_rejected(self):
        good = telem_document()
        frame = bytearray(bytes.fromhex(good['wire_frame_hex']))
        frame[-1] ^= 0x01
        self.reject(dict(good, wire_frame_hex=bytes(frame).hex()))
        self.reject(dict(good, wire_frame_hex=good['wire_frame_hex'][:-2]))
        self.reject(dict(good, wire_frame_hex=event_frame().hex()))
        self.reject(dict(good, observed_seq=10))
        self.reject(dict(good, tick_ms_raw=1235))
        self.reject(dict(good, mean_counts=[9, 2, 3, 4]))
        self.reject(dict(good, range_counts=[0, 6, 7, 8]))
        self.reject(dict(good, quality_flags=4))
        self.reject(dict(good, wire_frame_hex=telem_frame(epoch=3).hex()))

    def test_event_wire_fields_must_equal_envelope(self):
        document = event_document()
        self.accept(document)
        self.reject(dict(document, tick_ms_raw=1235))
        self.reject(dict(document, bitmap=2))
        self.reject(dict(document, channel=3))
        self.reject(dict(document, severity=4))
        self.reject(dict(document, peak_counts=100))
        self.reject(dict(document, wire_frame_hex=event_frame(epoch=3).hex()))
        corrupt = bytearray(bytes.fromhex(document['wire_frame_hex']))
        corrupt[-1] ^= 0x80
        self.reject(dict(document, wire_frame_hex=bytes(corrupt).hex()))

    # --- producer mapping -------------------------------------------------
    def test_producer_kind_map_is_enforced(self):
        self.reject(telem_document(), producer='ai_controller')
        self.reject(telem_document(), producer='control_broker')
        self.reject(candidate_document(), producer='hardware_bridge')
        self.reject(request_document(), producer='world_authority')
        self.reject(grant_document(), producer='control_broker')
        self.reject(response_document(config_ack_frame()), producer='world_authority')
        self.reject(telem_document(), producer='root_operator')
        with self.assertRaises(ValueError):
            host_envelope.validate_message(encode(telem_document()), producer=None,
                                           context=copy.deepcopy(CONTEXT), now_ns=NOW_NS)

    # --- context ----------------------------------------------------------
    def test_message_context_must_equal_active_context(self):
        document = telem_document()
        document['context']['boot_sha256'] = 'c' * 64
        self.reject(document)
        self.reject(telem_document(), context=dict(CONTEXT, session=8))

    def test_observation_context_must_equal_active_context(self):
        self.reject(request_document(observation=observation_key(dict(CONTEXT, session=8))),
                    producer='control_broker')
        self.reject(request_document(observation=observation_key(dict(CONTEXT, config_epoch=3))),
                    producer='control_broker')
        self.reject(candidate_document(observation=observation_key(dict(CONTEXT, boot_sha256='d' * 64))),
                    producer='ai_controller')

    def test_caller_context_and_now_arguments_are_strict(self):
        document = encode(telem_document())
        for bad_now in (True, 1.0, -1, 'x'):
            with self.subTest(now=bad_now):
                with self.assertRaises(ValueError):
                    host_envelope.validate_message(document, producer='hardware_bridge',
                                                   context=copy.deepcopy(CONTEXT), now_ns=bad_now)
        lowered = {key: value for key, value in CONTEXT.items() if key != 'session'}
        for bad_context in (dict(CONTEXT, session=True), lowered, dict(CONTEXT, extra=1), None):
            with self.subTest(context=bad_context):
                with self.assertRaises(ValueError):
                    host_envelope.validate_message(document, producer='hardware_bridge',
                                                   context=bad_context, now_ns=NOW_NS)

    # --- intervals and clocks ---------------------------------------------
    def test_receipt_interval_must_be_ordered_and_end_by_now(self):
        self.reject(telem_document(receipt=dict(lower_ns=100, upper_ns=50)))
        self.reject(telem_document(receipt=dict(lower_ns=NOW_NS - 10, upper_ns=NOW_NS + 1)))
        self.accept(telem_document(receipt=dict(lower_ns=NOW_NS - 10, upper_ns=NOW_NS)))
        self.reject(dict(event_document(),
                         receipt_interval_ns=dict(lower_ns=NOW_NS - 10, upper_ns=NOW_NS + 1)))
        self.reject(response_document(config_ack_frame(),
                                      receipt=dict(lower_ns=NOW_NS - 10, upper_ns=NOW_NS + 1)))

    def test_future_timestamps_rejected(self):
        self.reject(request_document(issue=NOW_NS + 1), producer='control_broker')
        self.accept(request_document(issue=NOW_NS), producer='control_broker')
        self.reject(candidate_document(completed=NOW_NS + 1), producer='ai_controller')
        self.reject(telem_document(adc_last=dict(lower_ns=NOW_NS + 1, upper_ns=NOW_NS + 2)))
        self.reject(odometry_document(at_interval=dict(lower_ns=NOW_NS + 1, upper_ns=NOW_NS + 2)),
                    producer='world_authority')
    # --- motion targets ---------------------------------------------------
    def test_stop_target_must_be_all_zero_and_may_carry_null_observation(self):
        stop = request_document(target_value=target(action=0, speed=0, duration=0),
                                observation=None)
        self.accept(stop, producer='control_broker')
        for label, mutated in [
            ('nonzero yaw', target(action=0, yaw=1, speed=0, duration=0)),
            ('nonzero pitch', target(action=0, pitch=-1, speed=0, duration=0)),
            ('nonzero speed', target(action=0, speed=1, duration=0)),
            ('nonzero duration', target(action=0, speed=0, duration=500)),
        ]:
            with self.subTest(label=label):
                self.reject(request_document(target_value=mutated, observation=None),
                            producer='control_broker')

    def test_set_target_requires_observation_and_bounded_positive_duration(self):
        self.accept(request_document(), producer='control_broker')
        self.reject(request_document(observation=None), producer='control_broker')
        self.reject(request_document(target_value=target(duration=0)), producer='control_broker')
        self.reject(request_document(target_value=target(duration=3001)), producer='control_broker')
        self.accept(request_document(target_value=target(duration=3000)), producer='control_broker')
        self.accept(request_document(context=STRESS_CONTEXT,
                                     target_value=target(duration=12000, speed=10)),
                    context=STRESS_CONTEXT, producer='control_broker')
        self.accept(request_document(context=STRESS_CONTEXT,
                                     target_value=target(duration=3001, speed=10)),
                    context=STRESS_CONTEXT, producer='control_broker')
        self.reject(request_document(context=STRESS_CONTEXT,
                                     target_value=target(duration=12001, speed=10)),
                    context=STRESS_CONTEXT, producer='control_broker')

    def test_stress_curvature_boundaries_and_zero_speed_rotation(self):
        def stress_target(yaw, pitch):
            return target(action=1, yaw=yaw, pitch=pitch, speed=20, duration=12000)

        for yaw, pitch in ((57, 0), (40, 40)):
            with self.subTest(valid=(yaw, pitch)):
                self.accept(request_document(context=STRESS_CONTEXT,
                                             target_value=stress_target(yaw, pitch)),
                            context=STRESS_CONTEXT, producer='control_broker')
        for yaw, pitch in ((58, 0), (41, 41)):
            with self.subTest(reject=(yaw, pitch)):
                self.reject(request_document(context=STRESS_CONTEXT,
                                             target_value=stress_target(yaw, pitch)),
                            context=STRESS_CONTEXT, producer='control_broker')
        self.reject(request_document(target_value=target(action=1, yaw=5, pitch=0, speed=0)),
                    producer='control_broker')
        self.accept(request_document(target_value=target(action=1, yaw=0, pitch=0, speed=0)),
                    producer='control_broker')

    def test_sample_count_must_match_transport_profile(self):
        self.reject(telem_document(count=800))
        self.reject(telem_document(context=STRESS_CONTEXT, count=50), context=STRESS_CONTEXT)

    # --- grants -----------------------------------------------------------
    def test_grant_topology_action_source_and_capture_seq_binding(self):
        hil = grant_document()
        self.accept(hil, producer='world_authority')
        self.reject(dict(hil, action_source='pc_direct_host'), producer='world_authority')
        self.reject(dict(hil, action_source='fpga_local_capture'), producer='world_authority')
        self.reject(dict(hil, capture_seq=None), producer='world_authority')
        pc_context = dict(CONTEXT, topology_id=2)
        pc = grant_document(context=pc_context, action_source='pc_direct_host', capture_seq=None)
        self.accept(pc, context=pc_context, producer='world_authority')
        self.reject(dict(pc, capture_seq=5), context=pc_context, producer='world_authority')
        self.reject(dict(pc, action_source='board_capture'), context=pc_context,
                    producer='world_authority')
        local_context = dict(CONTEXT, topology_id=3)
        local = grant_document(context=local_context, action_source='fpga_local_capture',
                               capture_seq=9)
        self.accept(local, context=local_context, producer='world_authority')
        self.reject(dict(local, capture_seq=None), context=local_context, producer='world_authority')
        self.reject(dict(local, action_source='pc_direct_host'), context=local_context,
                    producer='world_authority')

    def test_positive_grant_requires_deadline_after_now(self):
        self.reject(dict(grant_document(), deadline_monotonic_ns=NOW_NS), producer='world_authority')
        self.reject(dict(grant_document(), deadline_monotonic_ns=NOW_NS - 1),
                    producer='world_authority')
        stop = grant_document(target_value=target(action=0, speed=0, duration=0),
                              observation=None, deadline=0)
        self.accept(stop, producer='world_authority')
        self.reject(dict(stop, target=target(action=0, yaw=1, speed=0, duration=0)),
                    producer='world_authority')

    # --- board response ---------------------------------------------------
    def test_board_response_restricts_raw_types_session_and_epochs(self):
        self.reject(response_document(telem_frame()), producer='hardware_bridge')
        self.reject(response_document(event_frame()), producer='hardware_bridge')
        self.reject(response_document(config_ack_frame(session=8)), producer='hardware_bridge')
        self.reject(response_document(config_ack_frame(applied_epoch=3)), producer='hardware_bridge')
        self.reject(response_document(ack3d_frame(control_epoch=3)), producer='hardware_bridge')
        self.reject(response_document(state3d_frame(control_epoch=3)), producer='hardware_bridge')
        self.reject(response_document(config_ack_frame(epoch=3)), producer='hardware_bridge')

    def test_board_response_request_type_phase_and_mode_echo(self):
        self.reject(response_document(config_ack_frame(request_type=10)), producer='hardware_bridge')
        self.reject(response_document(ack3d_frame(request_type=12)), producer='hardware_bridge')
        self.reject(response_document(gain_ack_frame(request_type=7)), producer='hardware_bridge')
        self.reject(response_document(ack3d_frame(phase=5)), producer='hardware_bridge')
        self.reject(response_document(boot_ack_frame(mode=MODE_FAST_SENSOR_HIL + 1)),
                    producer='hardware_bridge')
        self.accept(response_document(boot_ack_frame(mode=MODE_FAST_SENSOR_HIL)),
                    producer='hardware_bridge')
        self.reject(response_document(state3d_frame(fault_flags=0x0100)), producer='hardware_bridge')
        self.reject(response_document(state3d_frame(quality=0x10)), producer='hardware_bridge')
    # --- pose and geometry ------------------------------------------------
    def test_pose_quaternion_must_be_finite_and_unit_within_tolerance(self):
        for quaternion in ((0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 2.0),
                           (0.1, 0.1, 0.1, 0.1), (0.0, 0.0, 0.0, 1.01)):
            with self.subTest(quaternion=quaternion):
                self.reject(odometry_document(pose_value=pose(quaternion=quaternion)),
                            producer='world_authority')

    def test_gate_centers_must_lie_on_selected_face_with_full_clearance(self):
        self.reject(geometry_document(entry_center=(14.9, 0.0, 0.0)), producer='world_authority')
        self.reject(geometry_document(entry_center=(-15.0, 0.0, 0.0), entry_face='+X'),
                    producer='world_authority')
        self.reject(geometry_document(entry_center=(15.0, 14.86, 0.0)), producer='world_authority')
        self.reject(geometry_document(entry_radius=0.16), producer='world_authority')
        self.reject(geometry_document(exit_radius=0.14), producer='world_authority')

    def test_hidden_truth_fields_rejected_everywhere(self):
        telem = telem_document()
        telem['context']['obstacle_id'] = 3
        self.reject(telem)
        geometry = geometry_document()
        geometry['initial_odometry']['truth_pose'] = [0.0, 0.0, 0.0]
        self.reject(geometry, producer='world_authority')
        geometry = geometry_document()
        geometry['map_seed'] = 42
        self.reject(geometry, producer='world_authority')
        candidate = candidate_document()
        candidate['editor_history'] = ['hidden']
        self.reject(candidate, producer='ai_controller')
        request = request_document()
        request['observation']['hidden_route'] = [0, 1, 2]
        self.reject(request, producer='control_broker')

    # --- parser bounds ----------------------------------------------------
    def test_message_size_and_nesting_bounds(self):
        limit = host_envelope.MAX_MESSAGE_BYTES
        self.reject_raw(b'"' + b'a' * limit + b'"')
        depth = host_envelope.MAX_NESTING_DEPTH + 4
        self.reject_raw(b'[' * depth + b']' * depth)
        self.reject_raw(encode(telem_document()) + b' trailing')
        self.reject_raw(b'')
        self.reject_raw(b'{}')
        self.reject_raw(b'null')
        with self.assertRaises(ValueError):
            host_envelope.validate_message('not-bytes', producer='hardware_bridge',
                                           context=copy.deepcopy(CONTEXT), now_ns=NOW_NS)

    def test_nonfinite_numbers_and_invalid_utf8_rejected(self):
        raw = encode(request_document()).decode('utf-8')
        self.reject_raw(raw.replace('"duration_ms":1000', '"duration_ms":1e999').encode('utf-8'),
                        producer='control_broker')
        self.reject_raw(raw.replace('"yaw_q":0', '"yaw_q":NaN').encode('utf-8'),
                        producer='control_broker')
        self.reject_raw(raw.replace('"yaw_q":0', '"yaw_q":Infinity').encode('utf-8'),
                        producer='control_broker')
        self.reject_raw(b'{"session": \xff}')
        self.reject_raw(b'"\xc3')

    # --- return record ----------------------------------------------------
    def test_returned_record_is_informational_and_inputs_not_mutated(self):
        context_copy = copy.deepcopy(CONTEXT)
        document = telem_document()
        record = host_envelope.validate_message(encode(document), producer='hardware_bridge',
                                                context=context_copy, now_ns=NOW_NS)
        self.assertEqual(record.kind, 'telem_observation')
        self.assertEqual(record.producer, 'hardware_bridge')
        self.assertIsNone(record.consumer)
        self.assertFalse(record.authority_only)
        self.assertEqual(record.document, json.loads(encode(document).decode('utf-8')))
        self.assertEqual(context_copy, CONTEXT)


if __name__ == '__main__':
    unittest.main(verbosity=2)

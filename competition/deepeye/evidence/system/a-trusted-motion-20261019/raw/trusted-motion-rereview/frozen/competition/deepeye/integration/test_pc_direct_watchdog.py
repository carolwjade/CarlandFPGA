"""Software counterexamples for the independent PC_DIRECT executor stop gate.

Real framed JSON fixtures only; no board, authentication, broker or sensor proof.
"""
import copy
from dataclasses import FrozenInstanceError
import struct
import unittest

from test_host_envelope import _load, CONTEXT, encode, wire, host_envelope
from test_host_envelope import response_document, config_ack_frame, telem_document

try:
    watchdog = _load('deepeye_pc_direct_watchdog_test', 'pc_direct_watchdog.py')
except FileNotFoundError:
    watchdog = None

PC = dict(CONTEXT, topology_id=2)


def heartbeat(*, seq=10, tick=100, lo=1000, hi=1005, context=None,
              phase=0, fault=0, session=None, epoch=None, control_epoch=None,
              ttl=0, last_control_seq=0, yaw=0, speed=0, capture_seq=0, quality=0):
    active = copy.deepcopy(PC if context is None else context)
    payload = struct.pack('<IHhBBHHHBB',
        active['session'] if session is None else session, last_control_seq, yaw, speed, phase, ttl,
        fault, capture_seq, active['config_epoch'] if control_epoch is None else control_epoch, quality)
    frame = wire.encode(wire.Frame(8, active['config_epoch'] if epoch is None else epoch,
                                   seq, tick, payload))
    doc = response_document(frame, receipt=dict(lower_ns=lo, upper_ns=hi))
    doc['context'] = active
    return doc


class PcDirectWatchdogTests(unittest.TestCase):
    def setUp(self):
        if watchdog is None:
            self.fail('PC_DIRECT executor stop gate is absent; static STATE parsing has no watchdog')
        self.guard = self.new_guard()

    def new_guard(self, **kwargs):
        return watchdog.PcDirectWatchdog(context=kwargs.pop('context', copy.deepcopy(PC)),
            heartbeat_timeout_ns=kwargs.pop('heartbeat_timeout_ns', 100),
            now_ns=kwargs.pop('now_ns', 900), **kwargs)

    def receive(self, doc=None, *, now=1010, guard=None, **route):
        return (self.guard if guard is None else guard).ingest_heartbeat(
            encode(heartbeat() if doc is None else doc), now_ns=now,
            producer=route.get('producer', 'hardware_bridge'),
            consumer=route.get('consumer', 'world_authority'))

    def arm(self, *, deadline=1200):
        self.receive()
        return self.guard.track_authority_command(command_seq=3, deadline_ns=deadline, now_ns=1010)

    def test_static_parser_accepts_state_but_startup_still_requires_stop(self):
        self.assertEqual(host_envelope.validate_message(encode(heartbeat()),
            producer='hardware_bridge', consumer='world_authority', context=PC,
            now_ns=1010).kind, 'board_response')
        state = self.guard.check(now_ns=1000)
        self.assertTrue(state.stop_required)
        self.assertFalse(state.heartbeat_healthy)
        self.assertEqual(state.reason, 'missing_heartbeat')

    def test_healthy_heartbeat_alone_never_creates_motion_or_observation(self):
        state = self.receive()
        self.assertTrue(state.heartbeat_healthy)
        self.assertTrue(state.stop_required)
        self.assertIsNone(state.active_command_seq)
        self.assertIsNone(state.command_deadline_ns)
        self.assertNotIn('observation', vars(state))
        self.assertNotIn('motion_grant', vars(state))

    def test_expiration_uses_receipt_lower_bound_with_exact_boundary(self):
        self.arm()
        self.assertFalse(self.guard.check(now_ns=1099).stop_required)
        state = self.guard.check(now_ns=1100)
        self.assertTrue(state.stop_required)
        self.assertTrue(state.latched)
        self.assertEqual(state.reason, 'heartbeat_timeout')
        self.assertEqual(state.heartbeat_deadline_ns, 1100)
        self.assertIsNone(state.active_command_seq)

    def test_late_processing_cannot_relabel_receipt_as_a_new_health_lease(self):
        with self.assertRaises(ValueError):
            self.receive(heartbeat(lo=900, hi=950), now=1000)
        self.assertTrue(self.guard.check(now_ns=1000).latched)

    def test_late_heartbeat_detects_unpolled_timeout_before_refresh(self):
        self.arm()
        with self.assertRaises(ValueError):
            self.receive(heartbeat(seq=11, tick=101, lo=1100, hi=1105), now=1110)
        state = self.guard.check(now_ns=1110)
        self.assertTrue(state.stop_required)
        self.assertEqual(state.reason, 'heartbeat_timeout')
        self.assertEqual(state.heartbeat_deadline_ns, 1100)

    def test_heartbeat_cannot_revive_a_command_after_a_polled_timeout(self):
        self.arm()
        self.guard.check(now_ns=1100)
        with self.assertRaises(ValueError):
            self.receive(heartbeat(seq=11, tick=101, lo=1110, hi=1115), now=1120)
        self.assertIsNone(self.guard.check(now_ns=1120).active_command_seq)

    def test_fault_or_rejected_phase_stops_and_normal_heartbeat_cannot_unlock(self):
        for changes, reason in (({'fault': 1}, 'board_fault'), ({'phase': 4}, 'board_rejected')):
            with self.subTest(changes=changes):
                self.guard = self.new_guard()
                self.arm()
                state = self.receive(heartbeat(seq=11, tick=101, lo=1020, hi=1025,
                                               **changes), now=1030)
                self.assertEqual(state.reason, reason)
                self.assertTrue(state.stop_required)
                self.assertTrue(state.latched)
                self.assertEqual(state.heartbeat_deadline_ns, 1100)
                with self.assertRaises(ValueError):
                    self.receive(heartbeat(seq=12, tick=102, lo=1040, hi=1045), now=1050)
                self.assertIsNone(self.guard.check(now_ns=1050).active_command_seq)

    def test_stopped_board_phase_is_a_healthy_pc_direct_diagnostic(self):
        self.assertTrue(self.receive(heartbeat(phase=0)).heartbeat_healthy)

    def test_other_known_phases_never_authorize_motion(self):
        for phase in (1, 2, 3):
            with self.subTest(phase=phase):
                state = self.receive(heartbeat(phase=phase), guard=self.new_guard())
                self.assertTrue(state.stop_required)
                self.assertIsNone(state.active_command_seq)

    def test_crc_context_session_epoch_reserved_flags_fail_closed(self):
        bad_crc = heartbeat(); packet = bytearray.fromhex(bad_crc['wire_frame_hex'])
        packet[-1] ^= 1; bad_crc['wire_frame_hex'] = packet.hex()
        wrong_context = heartbeat(); wrong_context['context']['boot_sha256'] = 'b' * 64
        capture_claim = heartbeat(); capture_claim['physical_capture_record_sha256'] = 'b' * 64
        documents = [bad_crc, wrong_context, capture_claim, heartbeat(session=8),
                     heartbeat(epoch=3), heartbeat(control_epoch=3), heartbeat(fault=256),
                     heartbeat(phase=255)]
        for document in documents:
            with self.subTest(document=document):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError): self.receive(document, now=1020)
                state = self.guard.check(now_ns=1020)
                self.assertTrue(state.stop_required)
                self.assertTrue(state.latched)
                self.assertEqual(state.heartbeat_deadline_ns, 1100)

    def test_only_explicit_hardware_bridge_to_world_authority_route(self):
        for producer, consumer in (('ai_controller', 'world_authority'),
                                   ('hardware_bridge', 'ai_controller'),
                                   ('hardware_bridge', None), (True, 'world_authority')):
            with self.subTest(producer=producer, consumer=consumer):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    self.receive(now=1020, producer=producer, consumer=consumer)
                self.assertTrue(self.guard.check(now_ns=1020).latched)

    def test_other_board_responses_and_observations_do_not_refresh_health(self):
        ack = response_document(config_ack_frame(), receipt=dict(lower_ns=1020, upper_ns=1025))
        ack['context'] = copy.deepcopy(PC)
        telem = telem_document(context=PC, receipt=dict(lower_ns=1020, upper_ns=1025),
                               adc_last=None)
        for document in (ack, telem):
            with self.subTest(kind=document['kind']):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError): self.receive(document, now=1030)
                self.assertTrue(self.guard.check(now_ns=1030).stop_required)
                self.assertEqual(self.guard.check(now_ns=1030).heartbeat_deadline_ns, 1100)

    def test_old_duplicate_and_half_range_seq_or_tick_never_refresh(self):
        for seq, tick in ((10, 100), (10, 101), (11, 100), (9, 101),
                          (11, 99), (10 + 32768, 101), (11, 100 + (1 << 31))):
            with self.subTest(seq=seq, tick=tick):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    self.receive(heartbeat(seq=seq, tick=tick, lo=1020, hi=1025), now=1030)
                state = self.guard.check(now_ns=1030)
                self.assertTrue(state.stop_required)
                self.assertEqual(state.heartbeat_deadline_ns, 1100)

    def test_replayed_raw_frame_with_new_receipt_does_not_refresh(self):
        self.arm()
        replay = heartbeat(lo=1050, hi=1055)
        with self.assertRaises(ValueError): self.receive(replay, now=1060)
        self.assertEqual(self.guard.check(now_ns=1060).heartbeat_deadline_ns, 1100)

    def test_legal_seq16_and_tick32_rollover(self):
        self.receive(heartbeat(seq=65535, tick=0xffffffff))
        state = self.receive(heartbeat(seq=0, tick=0, lo=1020, hi=1025), now=1030)
        self.assertTrue(state.heartbeat_healthy)
        self.assertEqual(state.heartbeat_sequence, 0)
        self.assertEqual(state.heartbeat_tick_ms, 0)
        self.assertEqual(state.heartbeat_deadline_ns, 1120)

    def test_cumulative_sequence_ring_cannot_make_old_id_look_new(self):
        self.receive()
        self.receive(heartbeat(seq=30010, tick=101, lo=1020, hi=1025), now=1030)
        self.receive(heartbeat(seq=60010, tick=102, lo=1040, hi=1045), now=1050)
        with self.assertRaises(ValueError):
            self.receive(heartbeat(seq=11, tick=103, lo=1060, hi=1065), now=1070)
        self.assertTrue(self.guard.check(now_ns=1070).latched)

    def test_cumulative_tick_half_range_requires_new_boot(self):
        self.receive(heartbeat(tick=0xfffffff0))
        self.receive(heartbeat(seq=11, tick=0x3ffffff0, lo=1020, hi=1025), now=1030)
        with self.assertRaises(ValueError):
            self.receive(heartbeat(seq=12, tick=0x7ffffff0, lo=1040, hi=1045), now=1050)
        self.assertTrue(self.guard.check(now_ns=1050).latched)

    def test_old_or_nonadvancing_receipt_does_not_refresh(self):
        for lo, hi in ((999, 1015), (1000, 1015), (1001, 1002)):
            with self.subTest(lo=lo, hi=hi):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    self.receive(heartbeat(seq=11, tick=101, lo=lo, hi=hi), now=1020)
                self.assertEqual(self.guard.check(now_ns=1020).heartbeat_deadline_ns, 1100)

    def test_future_reversed_and_boolean_receipt_intervals_fail_closed(self):
        for lo, hi in ((1020, 1040), (1025, 1020), (True, 1025)):
            with self.subTest(lo=lo, hi=hi):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    self.receive(heartbeat(seq=11, tick=101, lo=lo, hi=hi), now=1030)
                self.assertTrue(self.guard.check(now_ns=1030).stop_required)

    def test_explicit_strict_positive_timeout_no_default(self):
        with self.assertRaises(TypeError): watchdog.PcDirectWatchdog(context=PC, now_ns=900)
        for timeout in (True, False, 0, -1, 1.0, '100', None):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.new_guard(heartbeat_timeout_ns=timeout)

    def test_constructor_rejects_non_pc_direct_or_malformed_context(self):
        for context in (None, [], dict(PC, topology_id=1), dict(PC, topology_id=3),
                        dict(PC, session=True), dict(PC, extra='truth'),
                        dict(PC, boot_sha256='x' * 64)):
            with self.subTest(context=context), self.assertRaises(ValueError):
                self.new_guard(context=context)

    def test_all_runtime_entrypoints_stop_on_clock_regression(self):
        for operation in ('check', 'ingest', 'command', 'cancel', 'reset'):
            with self.subTest(operation=operation):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    if operation == 'check': self.guard.check(now_ns=1009)
                    elif operation == 'ingest': self.receive(now=1009)
                    elif operation == 'command':
                        self.guard.track_authority_command(command_seq=4, deadline_ns=1300, now_ns=1009)
                    elif operation == 'cancel': self.guard.cancel(now_ns=1009)
                    else: self.guard.reset(context=dict(PC, session=8), now_ns=1009)
                state = self.guard.check(now_ns=1010)
                self.assertTrue(state.latched)
                self.assertTrue(state.stop_required)
                self.assertEqual(state.reason, 'clock_regression')

    def test_bad_now_types_latch_without_poisoning_saved_high_water_time(self):
        for now in (True, -1, 1010.0, '1010', None):
            with self.subTest(now=now):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError): self.guard.check(now_ns=now)
                self.assertTrue(self.guard.check(now_ns=1010).latched)

    def test_bad_raw_types_and_malformed_json_latch_stop(self):
        for raw in (None, {}, 'text', b'{', b'{}', b'\xff'):
            with self.subTest(raw=raw):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    self.guard.ingest_heartbeat(raw, producer='hardware_bridge',
                        consumer='world_authority', now_ns=1020)
                self.assertTrue(self.guard.check(now_ns=1020).latched)

    def test_defensive_context_and_immutable_snapshot(self):
        context = copy.deepcopy(PC)
        guard = self.new_guard(context=context)
        context['session'] = 99
        snapshot = guard.context; snapshot['session'] = 88
        state = self.receive(guard=guard)
        self.assertEqual(guard.context['session'], 7)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            state.heartbeat_deadline_ns = 999999

    def test_mutating_input_buffer_after_validation_cannot_change_saved_state(self):
        raw = bytearray(encode(heartbeat()))
        self.guard.ingest_heartbeat(raw, producer='hardware_bridge',
            consumer='world_authority', now_ns=1010)
        raw[:] = b'{}'
        self.assertEqual(self.guard.check(now_ns=1020).heartbeat_deadline_ns, 1100)

    def test_commands_cannot_start_without_heartbeat(self):
        with self.assertRaises(ValueError):
            self.guard.track_authority_command(command_seq=3, deadline_ns=1200, now_ns=1000)
        self.assertTrue(self.guard.check(now_ns=1000).stop_required)

    def test_command_deadline_is_not_extended_by_healthy_heartbeat(self):
        self.arm(deadline=1080)
        state = self.receive(heartbeat(seq=11, tick=101, lo=1050, hi=1055), now=1060)
        self.assertEqual(state.heartbeat_deadline_ns, 1150)
        self.assertEqual(state.command_deadline_ns, 1080)
        state = self.guard.check(now_ns=1080)
        self.assertTrue(state.stop_required)
        self.assertFalse(state.latched)
        self.assertTrue(state.heartbeat_healthy)
        self.assertEqual(state.reason, 'command_deadline')

    def test_state_ttl_and_capture_looking_fields_do_not_renew_or_replace_command(self):
        self.arm(deadline=1080)
        state = self.receive(heartbeat(seq=11, tick=101, lo=1050, hi=1055, ttl=65535,
            last_control_seq=60000, yaw=15000, speed=20, capture_seq=65535, quality=15), now=1060)
        self.assertEqual(state.active_command_seq, 3)
        self.assertEqual(state.command_deadline_ns, 1080)
        self.assertTrue(self.guard.check(now_ns=1080).stop_required)

    def test_duplicate_command_cannot_extend_but_can_tighten_deadline(self):
        self.arm()
        state = self.guard.track_authority_command(command_seq=3, deadline_ns=9999, now_ns=1020)
        self.assertEqual(state.command_deadline_ns, 1200)
        state = self.guard.track_authority_command(command_seq=3, deadline_ns=1080, now_ns=1030)
        self.assertEqual(state.command_deadline_ns, 1080)

    def test_expired_command_cannot_be_reinstalled_even_with_new_deadline(self):
        self.arm(deadline=1050)
        self.guard.check(now_ns=1050)
        with self.assertRaises(ValueError):
            self.guard.track_authority_command(command_seq=3, deadline_ns=1300, now_ns=1060)
        self.assertIsNone(self.guard.check(now_ns=1060).active_command_seq)

    def test_cancel_and_repeat_do_not_rearm_old_command(self):
        self.arm()
        self.assertTrue(self.guard.cancel(now_ns=1020).stop_required)
        with self.assertRaises(ValueError):
            self.guard.track_authority_command(command_seq=3, deadline_ns=1300, now_ns=1030)
        self.assertIsNone(self.guard.check(now_ns=1030).active_command_seq)

    def test_normal_heartbeat_does_not_reactivate_cancelled_action(self):
        self.arm()
        self.guard.cancel(now_ns=1020)
        state = self.receive(heartbeat(seq=11, tick=101, lo=1030, hi=1035), now=1040)
        self.assertTrue(state.stop_required)
        self.assertTrue(state.heartbeat_healthy)
        self.assertIsNone(state.active_command_seq)

    def test_new_authority_command_can_follow_cancel_or_expiry_if_still_healthy(self):
        for expire in (False, True):
            with self.subTest(expire=expire):
                self.guard = self.new_guard(); self.arm(deadline=1040)
                if expire: self.guard.check(now_ns=1040)
                else: self.guard.cancel(now_ns=1040)
                state = self.guard.track_authority_command(command_seq=4, deadline_ns=1080, now_ns=1050)
                self.assertFalse(state.stop_required)
                self.assertEqual(state.active_command_seq, 4)

    def test_superseded_or_wrapped_command_seq_cannot_reactivate(self):
        for first, second, old in ((3, 4, 3), (65534, 65535, 0)):
            with self.subTest(first=first):
                self.guard = self.new_guard(); self.receive()
                self.guard.track_authority_command(command_seq=first, deadline_ns=1200, now_ns=1010)
                self.guard.track_authority_command(command_seq=second, deadline_ns=1250, now_ns=1020)
                with self.assertRaises(ValueError):
                    self.guard.track_authority_command(command_seq=old, deadline_ns=1300, now_ns=1030)
                self.assertTrue(self.guard.check(now_ns=1030).stop_required)

    def test_invalid_command_types_and_past_deadline_cancel_active_action(self):
        for sequence, deadline in ((True, 1200), (-1, 1200), (65536, 1200),
                                   (4.0, 1200), (4, True), (4, 1030), (4, -1),
                                   (4, '1200'), (4, None)):
            with self.subTest(sequence=sequence, deadline=deadline):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError):
                    self.guard.track_authority_command(command_seq=sequence,
                        deadline_ns=deadline, now_ns=1030)
                self.assertTrue(self.guard.check(now_ns=1030).stop_required)

    def test_reset_requires_unused_new_session_and_starts_stopped(self):
        self.arm(); self.guard.check(now_ns=1100)
        context8 = dict(PC, session=8)
        state = self.guard.reset(context=context8, now_ns=1110)
        context8['session'] = 99
        self.assertTrue(state.stop_required)
        self.assertFalse(state.heartbeat_healthy)
        self.assertFalse(state.latched)
        self.assertIsNone(state.command_deadline_ns)
        self.assertIsNone(state.heartbeat_deadline_ns)
        state = self.receive(heartbeat(context=dict(PC, session=8), lo=1120, hi=1125), now=1130)
        self.assertTrue(state.stop_required)
        self.assertTrue(state.heartbeat_healthy)
        with self.assertRaises(ValueError): self.guard.reset(context=PC, now_ns=1140)
        self.assertEqual(self.guard.context['session'], 8)

    def test_invalid_reset_keeps_previous_context_and_clears_action(self):
        for context in (PC, dict(PC, session=8, topology_id=1), None):
            with self.subTest(context=context):
                self.guard = self.new_guard(); self.arm()
                with self.assertRaises(ValueError): self.guard.reset(context=context, now_ns=1020)
                self.assertEqual(self.guard.context['session'], 7)
                self.assertTrue(self.guard.check(now_ns=1020).latched)
                self.assertIsNone(self.guard.check(now_ns=1020).active_command_seq)

    def test_old_session_heartbeat_cannot_seed_health_after_reset(self):
        self.arm()
        self.guard.reset(context=dict(PC, session=8), now_ns=1020)
        with self.assertRaises(ValueError): self.receive(heartbeat(lo=1030, hi=1035), now=1040)
        self.assertFalse(self.guard.check(now_ns=1040).heartbeat_healthy)

    def test_receipt_from_before_gate_activation_cannot_seed_health(self):
        self.guard = self.new_guard(now_ns=1000)
        with self.assertRaises(ValueError):
            self.receive(heartbeat(lo=999, hi=1005), now=1010)
        self.assertFalse(self.guard.check(now_ns=1010).heartbeat_healthy)


if __name__ == '__main__':
    unittest.main()

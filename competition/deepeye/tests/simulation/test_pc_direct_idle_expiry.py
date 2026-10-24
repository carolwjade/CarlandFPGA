"""New focused idle-expiry controls; synthetic channels/native boundary only.

Runtime, mailbox/candidate owner and numerical motion executor are real software.
This file explicitly selects only methods defined below; old fixture test methods
are never included in its suite. No real actor, provider, board or GUI is used.
"""
from dataclasses import FrozenInstanceError
import threading
import unittest
from unittest.mock import patch

from competition.deepeye.tests.simulation import test_actor_composition as fixture
from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt

c = fixture.c


class IdleCompositionTests(fixture.ActorCompositionTests):
    def arm_short(self, duration=20):
        self.activate()
        self.f.observe()
        return self.f.command(duration=duration)

    def assert_retired_preserving(self, before):
        root = self.comp._executor._root
        self.assertNotEqual(self.comp.status().state, 'ACTIVE')
        self.assertTrue(root.stopped)
        self.assertEqual(root.pose, before.pose)
        self.assertEqual(root.pose_revision, before.pose_revision)
        self.assertEqual(root.frame, before.frame)
        self.assertGreater(root.revision, before.revision)
        self.assertTrue(self.comp._runtime._latched)
        self.assertTrue(self.comp._progress.revoked)

    def test_idle_positive_cas_then_poll_stops_without_new_motion(self):
        # Missing poll expiry used to retain an active executor after original TTL.
        self.arm_short()
        executor = self.comp._executor
        with patch.object(executor, 'prepare_step', wraps=executor.prepare_step) as prepare, \
                patch.object(executor, 'commit_step', wraps=executor.commit_step) as commit:
            result = self.step()
            self.assertTrue(result.committed)
            self.assertEqual(result.pose_revision, 1)
            before = executor._root
            self.clock.value = 230_000_000  # issue210ms + original20ms TTL
            self.assertIsNone(self.comp.poll())
            self.assert_retired_preserving(before)
            self.assertEqual((prepare.call_count, commit.call_count), (1, 1))
            self.assertEqual(self.comp._runtime._reason, 'command_deadline')
            for method, args in ((self.comp.accept_completion, (object(),)),
                                 (self.comp.accept_command, (object(),)),
                                 (self.comp.accept_board, (object(),))):
                with self.assertRaises(c.CompositionRejected): method(*args)
            self.assertFalse(self.comp.step(expected_pose_revision=1, dt_ns=1).committed)
            self.assertEqual((prepare.call_count, commit.call_count), (1, 1))
            self.assertEqual(executor._root.pose, before.pose)
            self.assertEqual(executor._root.pose_revision, 1)

    def test_idle_heartbeat_expiry_precedes_progress_and_command(self):
        self.config = fixture.replace(self.config, heartbeat_timeout_ns=10_000_000)
        self.arm_short(duration=50)
        before = self.comp._executor._root
        self.clock.value = 220_000_000
        self.assertIsNone(self.comp.poll())
        self.assert_retired_preserving(before)
        self.assertEqual(self.comp._runtime._reason, 'heartbeat_timeout')

    def test_idle_before_deadline_does_not_prepare_move_or_renew(self):
        self.arm_short()
        executor, command = self.comp._executor, self.comp._runtime._last_command
        before = executor._root
        with patch.object(executor, 'prepare_step', wraps=executor.prepare_step) as prepare, \
                patch.object(executor, 'commit_step', wraps=executor.commit_step) as commit:
            self.clock.value = 229_999_999
            self.comp.poll()
            self.assertEqual(self.comp.status().state, 'ACTIVE')
            self.assertIs(executor._root, before)
            self.assertIs(self.comp._runtime._last_command, command)
            self.assertEqual(command.deadline_ns, 230_000_000)
            self.clock.value = 230_000_000
            self.comp.poll()
            self.assert_retired_preserving(before)
            self.assertEqual((prepare.call_count, commit.call_count), (0, 0))

    def test_idle_actual_time_after_original_actor_poll_is_checked(self):
        self.arm_short()
        before = self.comp._executor._root
        original = self.comp._actor.poll
        def delayed_poll():
            original()
            self.clock.value = 230_000_000
        self.clock.value = 229_999_999
        with patch.object(self.comp._actor, 'poll', delayed_poll):
            self.assertIsNone(self.comp.poll())
        self.assert_retired_preserving(before)

    def test_idle_original_deadline_survives_duplicate_ack_and_heartbeat(self):
        self.arm_short()
        original = self.comp._runtime._last_command
        progress = self.comp._progress.bound
        record = self.comp._command_record
        self.clock.value = 215_000_000
        self.f.beat(seq=11, tick=105)
        raw = rt.encode(dict(rt.response_document(rt.config_ack_frame()),
            context=rt.runtime.envelope._parse_message(self.comp._boot.context_json),
            receipt_interval_ns=dict(lower_ns=self.clock.value, upper_ns=self.clock.value)))
        self.comp.accept_board(self.channels.event(rt.runtime.VerifiedEnvelope(self.comp._boot, raw)))
        self.comp.accept_command(self.channels.event(record))
        self.assertEqual(self.comp._runtime._last_command.deadline_ns, original.deadline_ns)
        self.assertIs(self.comp._progress.bound, progress)
        self.clock.value = 230_000_000
        self.comp.poll()
        self.assertNotEqual(self.comp.status().state, 'ACTIVE')
        self.assertEqual(self.comp._runtime._reason, 'command_deadline')

    def test_idle_board_event_already_cleared_command_still_retires(self):
        self.arm_short()
        before = self.comp._executor._root
        self.clock.value = 230_000_000
        self.f.beat(seq=11, tick=120)
        self.assertIsNone(self.comp._runtime._command)
        self.assertIsNotNone(self.comp._runtime._last_command)
        self.assertEqual(self.comp.status().state, 'ACTIVE')
        self.comp.poll()
        self.assert_retired_preserving(before)
        self.assertEqual(self.comp._runtime._reason, 'command_deadline')

    def test_idle_unbound_and_never_commanded_waits_remain_possible(self):
        self.create()
        self.comp.poll()
        self.assertEqual(self.comp.status().state, 'RUNNING_UNBOUND')
        self.activate()
        self.clock.value = 215_000_000
        self.comp.poll()
        self.assertEqual(self.comp.status().state, 'ACTIVE')
        self.assertIsNone(self.comp._runtime._last_command)
        self.assertFalse(self.comp._runtime._latched)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision, 0)


class IdleRuntimeTests(rt.PcDirectRuntimeTests):
    def arm_short(self):
        self.activate()
        self.observe()
        return self.command(duration=20)

    def test_idle_probe_boundary_and_frozen_diagnostic_without_dependency_work(self):
        self.arm_short()
        command = self.owner._last_command
        with patch.object(self.provider, 'ai_lease', side_effect=AssertionError('no liveness callback')), \
                patch.object(self.provider, 'prepare_step', side_effect=AssertionError('no prepare')), \
                patch.object(self.provider, 'commit_step', side_effect=AssertionError('no commit')):
            self.clock.value = 1_019_999_999
            status = self.owner.check_expiry()
            self.assertFalse(status.stop_required)
            with self.assertRaises(FrozenInstanceError): status.stop_required = True
            self.clock.value = 1_020_000_000
            status = self.owner.check_expiry()
            self.assertTrue(status.stop_required)
            self.assertEqual(status.reason, 'command_deadline')
            self.assertFalse(self.owner._latched)  # Runtime's ordinary expiry stays non-latching.
            self.assertIsNone(self.owner._command)
            self.assertIs(self.owner._last_command, command)
            self.assertEqual(self.provider.committed, 0)

    def test_idle_probe_retains_expiry_after_event_then_fresh_boot_resets_history(self):
        self.arm_short()
        self.clock.value = 1_020_000_000
        self.beat(seq=11, tick=120)
        self.assertIsNone(self.owner._command)
        self.assertEqual(self.owner.check_expiry().reason, 'command_deadline')
        self.binding = self.boot_binding(generation=2, session=8)
        self.activate()
        self.assertIsNone(self.owner._last_command)
        self.assertFalse(self.owner.check_expiry().stop_required)

    def test_idle_probe_before_heartbeat_or_command_is_diagnostic_only(self):
        self.assertEqual(self.owner.check_expiry().reason, 'missing_boot')
        self.owner.boot(self.binding)
        status = self.owner.check_expiry()
        self.assertFalse(status.stop_required)
        self.assertIsNone(self.owner._last_command)
        self.beat()
        self.assertFalse(self.owner.check_expiry().stop_required)
        self.owner.stop('original operator stop')
        status = self.owner.check_expiry()
        self.assertTrue(status.stop_required)
        self.assertEqual(status.reason, 'original operator stop')

    def test_idle_probe_invalid_or_regressed_clock_latches_and_preserves_exception(self):
        self.activate()
        original = OSError('original clock failure')
        def fail(): raise original
        self.clock.on_read = fail
        with self.assertRaises(OSError) as caught: self.owner.check_expiry()
        self.assertIs(caught.exception, original)
        self.assertTrue(self.owner._latched)
        for value in (False, -1, 1.5, 'invalid', 999_999_999):
            with self.subTest(value=value):
                clock = rt.Clock()
                deps = rt.fixture_provider(clock)
                owner = rt.runtime.PcDirectRuntime(run_id='run-1', dependencies=deps,
                    clock=clock, heartbeat_timeout_ns=500_000_000)
                owner.boot(self.binding)
                clock.next_value = value
                with self.assertRaises(ValueError): owner.check_expiry()
                self.assertTrue(owner._latched)
                self.assertFalse(owner.step(expected_pose_revision=0, dt_ns=1).committed)
                self.assertEqual(deps.committed, 0)

    def test_idle_probe_caught_reentry_vetoes_outer_probe(self):
        self.arm_short()
        caught = []
        def reenter():
            try: self.owner.check_expiry()
            except ValueError as error: caught.append(error)
        self.clock.on_read = reenter
        status = self.owner.check_expiry()
        self.assertEqual(len(caught), 1)
        self.assertTrue(status.stop_required)
        self.assertTrue(self.owner._latched)
        self.assertEqual(self.provider.committed, 0)

    def test_idle_probe_during_step_vetoes_no_commit(self):
        self.arm_short()
        caught = []
        def check_during_prepare():
            try: self.owner.check_expiry()
            except ValueError as error: caught.append(error)
        self.provider.prepare_hook = check_during_prepare
        self.assertFalse(self.step().committed)
        self.assertEqual(len(caught), 1)
        self.assertTrue(self.owner._latched)
        self.assertEqual(self.provider.committed, 0)

    def test_idle_probe_foreign_thread_and_invalid_call_veto(self):
        self.arm_short()
        errors = []
        def foreign():
            try: self.owner.check_expiry()
            except ValueError as error: errors.append(error)
        worker = threading.Thread(target=foreign)
        worker.start(); worker.join()
        self.assertEqual(len(errors), 1)
        self.assertTrue(self.owner.check_expiry().stop_required)
        self.binding = self.boot_binding(generation=2, session=8)
        self.activate()
        with self.assertRaises(ValueError): self.owner.check_expiry(unexpected=True)
        self.assertTrue(self.owner._latched)
        self.assertEqual(self.provider.committed, 0)


NEW_CASES = tuple((case, name) for case in (IdleCompositionTests, IdleRuntimeTests)
                  for name in sorted(case.__dict__) if name.startswith('test_idle_'))
RED_NAMES = {'test_idle_positive_cas_then_poll_stops_without_new_motion',
             'test_idle_heartbeat_expiry_precedes_progress_and_command'}


def explicit_suite(red=False):
    return unittest.TestSuite(case(name) for case, name in NEW_CASES
                              if not red or name in RED_NAMES)


def load_tests(loader, tests, pattern):
    return explicit_suite()


if __name__ == '__main__':
    import sys
    result = unittest.TextTestRunner(verbosity=2).run(explicit_suite('--red-only' in sys.argv))
    raise SystemExit(0 if result.wasSuccessful() else 1)

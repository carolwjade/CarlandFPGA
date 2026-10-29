"""New phase/native containment compatibility; no process or socket calls."""
from types import SimpleNamespace
import unittest

from competition.deepeye.simulation.authority import _world_loop as loop
from competition.deepeye.simulation.authority import _owned_godot as native


class WorldPhaseDeadlineTests(unittest.TestCase):
    def owner(self, now, cap):
        clock = lambda: now
        boundary = native._private_test_owner(clock)
        boundary.spec = SimpleNamespace(run_id='new-phase-deadline-software-control')
        boundary._containment_deadline = cap
        boundary.hello = object()
        queued = []

        class Channel:
            def queue(self, message, deadline):
                queued.append((message, deadline))
                return object()

        boundary._channel = Channel()
        owner = loop._RootWorldOwner(loop._TEST_FACTORY, clock)
        owner._native = boundary
        owner._state = 'EDITABLE'
        owner._editable = dict(document_generation='1', raw_layout_sha256='a'*64)
        return owner, boundary, queued

    def test_freeze_uses_actual_native_send_guard_without_extending_45s_cap(self):
        owner, boundary, queued = self.owner(1_000_000_000, 45_000_000_000)
        owner.request_freeze(snapshot_limits_sha256='b'*64, model_policy_sha256='c'*64)
        self.assertEqual(1, len(queued))
        self.assertEqual(45_000_000_000, queued[0][1])
        self.assertFalse(boundary._retired)

    def test_expired_cap_rejected_before_retiring_native_send_boundary(self):
        owner, boundary, queued = self.owner(100, 99)
        with self.assertRaises(ValueError):
            owner.request_freeze(snapshot_limits_sha256='b'*64, model_policy_sha256='c'*64)
        self.assertEqual([], queued)
        self.assertFalse(boundary._retired)


if __name__ == '__main__':
    unittest.main()

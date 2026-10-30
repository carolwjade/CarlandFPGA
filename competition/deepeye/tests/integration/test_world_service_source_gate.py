"""NEW private service/gate wiring controls; no original native or source."""
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from competition.deepeye.simulation.authority import root_world_service as service
from competition.deepeye.simulation.authority import _world_loop as world


class WorldServiceSourceGateTests(unittest.TestCase):
    def fixture(self, *, committed=False, retired=False):
        events = []
        clock = object()
        executor = NS(_root=NS(pose_revision=int(committed)))
        scene = object()
        binding = NS(executor=executor, world_values=NS(scene=scene))
        native = NS(clock_binding=clock, _containment_deadline=1000,
                    _retired=False, state='AUTHENTICATED')
        source = NS(state='RETIRED' if retired else 'RUNNING',
                    _thread=threading.get_ident(), _clock=clock)
        field = NS(_executor=executor, _scene=scene,
                   _check=lambda: events.append('field'))
        owner = NS(_clock=clock, _native=native, _thread=threading.get_ident(),
            _foreign=threading.Event(), _busy=False, _initialized=True, _vetoed=False,
            _binding=binding, _actor_link=None, _renderer_revision=int(committed),
            _commits=[NS(committed=True, uncertainty=None)] if committed else [],
            _publication=NS(kind='PUBLISH_VIEW', resolved=True, state='APPLIED',
                            getter_admitted=False, revision=int(committed)),
            _check_thread=lambda: events.append('gate'))
        # The actual fixed unbound Root gate is called below. This fake's own
        # same-name function is deliberately not an admissible callback.
        owner.require_source_pose_current = lambda: self.fail('injected gate called')
        core = object.__new__(service._ServiceCore)  # Distinct exact software type.
        core._mode, core._clock, core._owner, core._source = service._SOFTWARE, clock, owner, source
        core._native, core._binding, core._field = native, binding, field
        core._deadline_ns, core._thread = 1000, threading.get_ident()
        core._failed = core._polling = False
        return core, events

    def validate(self, core, *, retired=False):
        # Only established fixture admission and field/registry scaffolding are
        # replaced. The real fixed source-gate function and its rules execute.
        with patch.object(service, '_software_inputs', lambda *args: None), \
             patch.object(service, '_field', lambda *args: core._field), \
             patch.object(world._RootWorldOwner, '_known_binding', lambda *args: core._binding):
            core._validate(retired_source=retired)

    def test_stopped_initial_source_checks_fixed_gate_before_field(self):
        core, events = self.fixture()
        self.validate(core)
        self.assertEqual(['gate', 'field'], events)
        self.assertIsNot(type(core), service.RootWorldService)

    def test_applied_without_getter_admission_cannot_reach_next_source(self):
        core, events = self.fixture(committed=True)
        with self.assertRaises(world.WorldRejected):
            self.validate(core)
        self.assertEqual(['gate'], events)

    def test_retired_source_terminal_drain_does_not_require_fresh_source_pose(self):
        core, events = self.fixture(committed=True, retired=True)
        self.validate(core, retired=True)
        self.assertEqual(['field'], events)

    def test_pending_numeric_slot_blocks_every_new_source_validation(self):
        core, events = self.fixture()
        core._owner._actor_link = NS(slot=NS(committed=False))
        with self.assertRaises(world.WorldRejected):
            self.validate(core)
        self.assertEqual(['gate'], events)


if __name__ == '__main__':
    unittest.main()

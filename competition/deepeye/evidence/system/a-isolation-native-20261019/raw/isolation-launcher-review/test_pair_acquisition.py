"""Expected failing ownership witnesses; all native acquisitions are fake."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from simulation.isolation import win32 as w
from simulation.isolation.owned_resources import OwnedResources
from simulation.isolation.resource_cleanup import Provenance, Outcome


class PairAcquisitionTests(unittest.TestCase):
    def owner_with_unknown_release(self, value):
        owner = OwnedResources(Provenance('task/v1', 'work', 'review-owner', (('source', 'a'*64),)))
        owner.bind_releaser(lambda ref: Outcome.UNKNOWN)
        old = owner.own_handle('old', value)
        self.assertIs(owner.release_once(old), Outcome.UNKNOWN)
        return owner

    def test_pipe_second_successful_acquisition_survives_first_ambiguity(self):
        owner = self.owner_with_unknown_release(81)
        native_calls = []
        def create_pipe(read, write, attributes, size):
            native_calls.append('fake CreatePipe succeeded')
            read._obj.value, write._obj.value = 81, 82
            return True
        with patch.object(w, 'CreatePipe', side_effect=create_pipe):
            with self.assertRaisesRegex(ValueError, 'ambiguous native reuse'):
                w.pipe(owner=owner, read_label='new_read', write_label='new_write')
        self.assertEqual(native_calls, ['fake CreatePipe succeeded'])
        self.assertEqual([(r.label, r.native) for r in owner.references],
                         [('old', 81), ('new_read', 81), ('new_write', 82)],
                         'successful pipe writer 82 was lost after first registration raised')

    def test_process_primary_thread_survives_first_ambiguity(self):
        owner = self.owner_with_unknown_release(91)
        pair = SimpleNamespace(hProcess=91, hThread=92, dwProcessId=99)
        with self.assertRaisesRegex(ValueError, 'ambiguous native reuse'):
            owner.own_process(pair)
        self.assertEqual([(r.label, r.native) for r in owner.references],
                         [('old', 91), ('process', 91), ('primary_thread', 92)],
                         'successful CreateProcess primary thread 92 is absent from retained ownership')


if __name__ == '__main__':
    unittest.main(verbosity=2)

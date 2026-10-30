"""NEW exact-rational selected-slot expiry controls, no board or old suite."""
from fractions import Fraction
from pathlib import Path
import hashlib
import unittest
from competition.deepeye.integration import boot_profile as profile


class SelectedSlotDeadlineTests(unittest.TestCase):
    def setUp(self):
        path = Path(profile.__file__).parents[1]/'docs/boot_profiles.json'
        self.assertEqual('06588c82bdc803800c5891ca4aa46e184e6391ddd9045a77d99297878973bd74',
                         hashlib.sha256(path.read_bytes()).hexdigest())
        self.doc = profile.load_document(path)

    def cases(self):
        for name in ('fast_9600', 'stress_300'):
            for slot in ('control_primary', 'ack_primary'):
                yield name, slot, Fraction(profile.slot_start_ms(self.doc, name, slot))

    def test_fractional_expiry_before_selected_start_refuses(self):
        for name, slot, start in self.cases():
            with self.subTest(name=name, slot=slot):
                result = profile.late_candidate_action(self.doc, name,
                    start-Fraction(1,3), start-Fraction(1,6), slot)
                self.assertEqual('stop', result['action'])

    def test_fractional_ready_at_selected_start_expiry_refuses(self):
        for name, slot, start in self.cases():
            with self.subTest(name=name, slot=slot):
                result = profile.late_candidate_action(self.doc, name,
                    start-Fraction(1,7), start, slot)
                self.assertEqual('stop', result['action'])

    def test_fractional_live_deadline_keeps_original_start(self):
        for name, slot, start in self.cases():
            with self.subTest(name=name, slot=slot):
                result = profile.late_candidate_action(self.doc, name,
                    start-Fraction(1,5), start+Fraction(1,11), slot)
                self.assertEqual('send', result['action'])
                self.assertEqual(start, result['start_ms'])

    def test_fractional_miss_keeps_existing_defer_window(self):
        for name, slot, start in self.cases():
            with self.subTest(name=name, slot=slot):
                window = Fraction(profile._profile(self.doc, name)['window_ms'])
                deadline = start+window+Fraction(1,13)
                result = profile.late_candidate_action(self.doc, name,
                    start+Fraction(1,17), deadline, slot)
                self.assertEqual('defer', result['action'])
                self.assertEqual(start+window, result['deferred_start_ms'])


if __name__ == '__main__': unittest.main()

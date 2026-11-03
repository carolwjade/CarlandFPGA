"""Direction rounding at the actual 563 actor boundary, without rerunning AI."""
import math
import unittest

from competition.deepeye.simulation.authority.demo30h_ai_em3_profile_v2 import verifier_longttl_demo_v7 as verifier


class DirectionRoundoff(unittest.TestCase):
    def test_actual_normalized_direction_one_ulp(self):
        value = [0.0, -1.0000000000000002, -2.220446049250313e-16]
        verifier._direction(value)
        self.assertLessEqual(abs(sum(x*x for x in value)-1), 1e-10)

    def test_component_and_norm_checks_retained(self):
        for value in ([0, -1.000001, 0], [1, 1, 0], [0, 0, 0],
                      [0, math.inf, 0], [0, math.nan, 0], [0, True, 0]):
            with self.subTest(value=value), self.assertRaises(verifier.Rejected):
                verifier._direction(value)

    def test_exact_unit_axes(self):
        for value in ([1,0,0], [0,-1,0], [0,0,1]):
            verifier._direction(value)


if __name__ == '__main__':
    unittest.main()

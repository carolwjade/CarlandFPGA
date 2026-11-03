"""Revision2 geometry: actual circular aperture, edge and same-face overlap."""
import math
import unittest
from competition.deepeye.simulation.authority.motion import gate_geometry as g

class HumanRevision2Gates(unittest.TestCase):
    def test_half_metre_aperture_changes_real_section(self):
        gate=g.Gate('top',0,0)
        self.assertEqual(gate.radius_m,.25)
        # Complete solid section radius .12 plus lateral .10 fits new .25,
        # whereas lateral .14 crosses it. This checks the geometric predicate.
        clear=g.aperture_radius_bounds(g.Capsule((.10,15,0),(0,1,0)),gate)
        blocked=g.aperture_radius_bounds(g.Capsule((.14,15,0),(0,1,0)),gate)
        self.assertEqual(clear.classification,'clear')
        self.assertNotEqual(blocked.classification,'clear')

    def test_circle_stays_inside_face_at_actual_radius(self):
        g.Gate('top',14.75,-14.75)
        with self.assertRaises(ValueError):g.Gate('top',math.nextafter(14.75,math.inf),0)

    def test_equal_circles_have_actual_half_metre_overlap_rule(self):
        first=g.Gate('top',0,0)
        g.validate_gate_pair(first,g.Gate('top',.5,0))
        with self.assertRaises(ValueError):g.validate_gate_pair(first,g.Gate('top',math.nextafter(.5,0),0))

if __name__=='__main__':unittest.main()

"""Quantized kinematic reference vectors, separate from physical collision tests."""
import importlib.util
import math
from pathlib import Path
import sys
import unittest

spec=importlib.util.spec_from_file_location('deepeye_motion',Path(__file__).with_name('motion.py'))
motion=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=motion
spec.loader.exec_module(motion)


class MotionTests(unittest.TestCase):
    def test_frozen_stress_axis_and_diagonal_boundaries(self):
        for yaw,pitch in ((57,0),(-57,0),(40,40),(-40,40)):
            motion.validate('stress_300',20,yaw,pitch)
        for yaw,pitch in ((58,0),(0,-58),(41,41),(-41,41)):
            with self.assertRaises(ValueError): motion.validate('stress_300',20,yaw,pitch)

    def test_zero_speed_never_turns(self):
        command=motion.validate('fast_9600',0,0,0)
        self.assertEqual(command.curvature_yaw_per_m,0)
        self.assertEqual(command.curvature_pitch_per_m,0)
        for yaw,pitch in ((1,0),(0,-1),(1,1)):
            with self.assertRaises(ValueError): motion.validate('fast_9600',0,yaw,pitch)

    def test_profile_mapping_does_not_mix(self):
        self.assertAlmostEqual(motion.validate('fast_9600',20,0,0).target_speed_m_s,.25)
        self.assertAlmostEqual(motion.validate('stress_300',20,0,0).target_speed_m_s,.002)
        motion.validate('fast_9600',20,100,100)
        with self.assertRaises(ValueError): motion.validate('stress_300',20,100,100)

    def test_rom_against_independent_formula_every_speed(self):
        for profile,step in (('fast_9600',.0125),('stress_300',.0001)):
            for speed in range(21):
                expected=math.floor((speed*step*180000/(2*math.pi))**2)
                self.assertEqual(motion.curvature_limit_squared(profile,speed),expected)

    def test_integer_and_range_checks_reject_not_clip(self):
        for args in (('bad',1,0,0),('fast_9600',21,0,0),('fast_9600',-1,0,0),('fast_9600',1,15001,0),('fast_9600',1,0,-15001),('fast_9600',1.0,0,0),('fast_9600',True,0,0)):
            with self.assertRaises(ValueError): motion.validate(*args)

    def test_rate_scales_with_actual_speed_and_stops_at_zero(self):
        cmd=motion.validate('fast_9600',20,1000,-2000)
        self.assertAlmostEqual(math.hypot(cmd.curvature_yaw_per_m,cmd.curvature_pitch_per_m),math.radians(math.hypot(1,2))/.25)
        self.assertEqual(cmd.angular_rates(0),(0.0,0.0))
        yaw,pitch=cmd.angular_rates(.125)
        self.assertAlmostEqual(yaw,math.radians(.5))
        self.assertAlmostEqual(pitch,math.radians(-1))
        for v in (-1,float('nan'),float('inf'),.251):
            with self.assertRaises(ValueError): cmd.angular_rates(v)

    def test_acceleration_and_deceleration_bound(self):
        speed=0.0
        for _ in range(100):
            nxt=motion.step_speed(speed,.25,.01)
            self.assertLessEqual(abs(nxt-speed),.00250000001)
            speed=nxt
        self.assertAlmostEqual(speed,.25)
        for _ in range(100): speed=motion.step_speed(speed,0,.01)
        self.assertEqual(speed,0)
        for dt in (0,-.01,.011,float('nan')):
            with self.assertRaises(ValueError): motion.step_speed(.1,0,dt)


if __name__=='__main__': unittest.main(verbosity=2)

import math
import random
import struct
import types
import unittest

from competition.deepeye.simulation.sensors import forward_profile as f
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
try:
    from competition.deepeye.simulation.sensors import _ordered_numpy_kernel as k
except ImportError:
    k = None


def bits(x):
    return struct.pack('>d', x)


def field(pieces, background=0.01, epsilon=0.0):
    obj = object.__new__(OwnedWorldField)
    obj._pieces, obj._background, obj._epsilon = tuple(pieces), background, epsilon
    return obj


def box(rank, sigma, centre=(0., 0., 0.), dims=(1., 1., 1.), kind='box'):
    return (rank, sigma, kind, centre, dims, ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)))


ROWS = ((0.,0.,0., 1.,2.,3.,4.,5.), (0.25,-0.,1., 0.,1.,2.,0.,3.),
        (-1.,0.5,2., 3.,0.,1.,2.,0.), (2.,0.,0., 0.5,1.,0.,1.,2.))


def original(pose, obj, rows=ROWS):
    g = dict(f._kernel_channels.__globals__)
    g['_weight_table'] = lambda: rows
    kernel = types.FunctionType(f._kernel_channels.__code__, g)
    return kernel(pose, obj._sample_sigma_pure)


class OrderedKernelControls(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(k, 'new isolated candidate module missing')

    def test_coordinates_bitwise_with_signed_zero(self):
        pose = f.Pose((-0., 1.25, -3.), (0.,0.,0.,1.))
        rot = f._rotation_matrix(pose.orientation_xyzw)
        coords = k._coordinates(pose, ROWS)
        for row, got in zip(ROWS, coords):
            for axis in range(3):
                t=pose.position_m[axis]; m=rot[axis]; dx,dy,dz=row[:3]
                expected=t + m[0]*dx + m[1]*dy + m[2]*dz
                self.assertEqual(bits(expected), bits(got[axis]))

    def test_full_field_priority_unknown_boundary_and_cylinder(self):
        pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        cases=[(), (box(1,None), box(5,0.1)),
               (box(5,0.1),box(1,0.2,centre=(1.,0.,0.))),
               (box(2,0.1),box(2,0.2)), (box(1,0.3,kind='cylinder'),)]
        for pieces in cases:
            obj=field(pieces)
            expected=original(pose,obj)
            got=k._channels(pose,obj._pieces,obj._background,obj._epsilon,ROWS)
            self.assertEqual(None if expected is None else tuple(map(bits,expected)),
                             None if got is None else tuple(map(bits,got)))

    def test_nonfinite_overflow_and_subnormal_first_fault(self):
        pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        for x in (float('inf'),float('nan'),1.7976931348623157e308,5e-324,-0.):
            rows=((x,0.,0.,1.,1.,1.,1.,1.),)+ROWS
            obj=field((box(1,0.1),))
            expected=original(pose,obj,rows)
            got=k._channels(pose,obj._pieces,obj._background,obj._epsilon,rows)
            self.assertEqual(None if expected is None else tuple(map(bits,expected)),
                             None if got is None else tuple(map(bits,got)))

    def test_ordered_accumulate_seed_and_chunk_boundary(self):
        import numpy as np
        for values in ((-0.0, 0.0), (1e16, 1.0, -1e16, 1.0), (5e-324, -0.0, -5e-324)):
            for seed in (0.0, -0.0, 1.0):
                total = seed
                for value in values:
                    total += value
                result = np.add.accumulate(np.array((seed,) + values, dtype=np.float64))[-1]
                self.assertEqual(bits(total), bits(float(result)))
        pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        rows=tuple(ROWS[i % len(ROWS)] for i in range(1031))
        obj=field(())
        self.assertEqual(tuple(map(bits,original(pose,obj,rows))),
                         tuple(map(bits,k._channels(pose,obj._pieces,obj._background,obj._epsilon,rows))))

    def test_actual_warmed_original_table(self):
        rows=f._weight_table()
        pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        obj=field(())
        expected=original(pose,obj,rows)
        actual=k._channels(pose,obj._pieces,obj._background,obj._epsilon,rows)
        self.assertEqual(tuple(map(bits,expected)), tuple(map(bits,actual)))

    def test_seeded_profile_rng_and_adc_progression(self):
        obj=field((box(1,0.04,centre=(20.,0.,0.)),))
        pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        a=f.ForwardProfile(em_rng=random.Random(41), vibration_rng=random.Random(42))
        b=f.ForwardProfile(em_rng=random.Random(41), vibration_rng=random.Random(42))
        g=dict(f.ForwardProfile.acquire_em.__globals__)
        g['_kernel_channels']=lambda p, sampler: k._channels(p,obj._pieces,obj._background,obj._epsilon,ROWS)
        candidate=types.FunctionType(f.ForwardProfile.acquire_em.__code__,g)
        h=dict(f.ForwardProfile.acquire_em.__globals__)
        h['_kernel_channels']=lambda p, sampler: original(p,obj)
        baseline=types.FunctionType(f.ForwardProfile.acquire_em.__code__,h)
        for tick in range(0, 110, 10):
            if tick % 50 == 0:
                baseline(a,tick,pose,context='formation',sampler=obj._sample_sigma_pure)
                candidate(b,tick,pose,context='formation',sampler=obj._sample_sigma_pure)
            self.assertEqual(a.sample_adc(tick).to_payload(),b.sample_adc(tick).to_payload())
        self.assertEqual(a._em_rng.getstate(),b._em_rng.getstate())
        self.assertEqual(a._vibration_rng.getstate(),b._vibration_rng.getstate())

if __name__ == '__main__':
    unittest.main(verbosity=2)

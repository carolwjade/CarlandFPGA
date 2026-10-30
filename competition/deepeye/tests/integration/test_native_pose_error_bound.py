import unittest
from fractions import Fraction as F
from itertools import product

from competition.deepeye.simulation.authority._native_pose_error_bound import (
    affine_body_bound, decode_ieee, sqrt_enclosure,
)

Z, O = F(0), F(1)
IDENTITY = ((O,Z,Z),(Z,O,Z),(Z,Z,O))  # columns
Q_ID = (Z,Z,Z,O)

class EndpointBoundTests(unittest.TestCase):
    def bound(self, columns=IDENTITY, g=(Z,Z,Z), t=(Z,Z,Z), q=Q_ID,
              half=F(2,5), radius=F(3,25), pivot=F(13,25), asset=Z):
        return affine_body_bound(t, q, columns, g, half, radius, pivot, asset)

    def test_zero_and_saved_initial_data(self):
        self.assertEqual(self.bound().getter_error, Z)
        q=(Z,F.from_float(0.7071067811865476),Z,F.from_float(0.7071067811865476))
        columns=((Z,Z,-O),(Z,O,Z),(O,Z,Z))
        t=(F.from_float(-15.6),Z,O)
        g=(decode_ieee('c179999a',32),Z,O)
        b=self.bound(columns,g,t,q)
        self.assertEqual(b.matrix_norm_upper,Z)
        self.assertEqual(b.getter_error,F(214748365,562949953421312))
        self.assertFalse(b.fits_cap(F(1,10000000)))
        self.assertTrue(b.fits_cap(b.getter_error))

    def test_each_of_twelve_components_contributes(self):
        for j in range(3):
            g=list((Z,Z,Z)); g[j]=F(1,8)
            self.assertGreaterEqual(self.bound(g=tuple(g)).getter_error,F(1,8))
        for col,row in product(range(3),repeat=2):
            m=[list(v) for v in IDENTITY]; m[col][row]+=F(1,4)
            self.assertGreaterEqual(self.bound(columns=tuple(map(tuple,m))).getter_error,F(13,100))

    def test_shear_and_translation_cover_every_corner(self):
        columns=((O,F(1,8),Z),(F(1,4),O,Z),(Z,Z,O))
        g=(F(1,3),F(-1,4),F(1,5))
        b=self.bound(columns,g,asset=F(1,10))
        self.assertEqual(b.body_radius,F(31,50))
        self.assertEqual(b.asset_error,F(1,10))
        self.assertEqual(b.total_error,b.getter_error+F(1,10))
        # Axis and cube-corner points scaled inside the proven radius.
        points=[(F(s,4),F(t,4),F(u,4)) for s,t,u in product((-1,1),repeat=3)]
        points += [(F(1,2),Z,Z),(Z,F(-1,2),Z),(Z,Z,F(1,2))]
        for p in points:
            delta=tuple(g[i]+sum((columns[j][i]-IDENTITY[j][i])*p[j] for j in range(3)) for i in range(3))
            self.assertLessEqual(sum(x*x for x in delta), b.getter_error*b.getter_error)

    def test_norm_is_outward_including_ties_and_subnormals(self):
        for x in (Z,O,F(2),F(9,4),F(1,2**1074),F(123456789,1234567)):
            lo,hi=sqrt_enclosure(x)
            self.assertLessEqual(lo*lo,x); self.assertGreaterEqual(hi*hi,x)
            self.assertLessEqual(hi-lo,F(1,2**64))
        self.assertEqual(sqrt_enclosure(F(9,4)),(F(3,2),F(3,2)))

    def test_decoder_exact_finite_and_refuses_nonfinite(self):
        self.assertEqual(decode_ieee('80000000',32),Z)
        self.assertEqual(decode_ieee('00000001',32),F(1,2**149))
        self.assertEqual(decode_ieee('0000000000000001',64),F(1,2**1074))
        self.assertEqual(decode_ieee('7f7fffff',32),F((2**24-1)*2**104))
        self.assertEqual(decode_ieee('7fefffffffffffff',64),F((2**53-1)*2**971))
        for token,width in [('7f800000',32),('7fc00000',32),('fff0000000000000',64),('7ff8000000000000',64),('0'*17,64),('zzzzzzzz',32),('3f800000',True)]:
            with self.subTest(token=token),self.assertRaises((ValueError,TypeError)):
                decode_ieee(token,width)

    def test_refuses_invalid_types_radii_and_large_inputs(self):
        bad=[dict(half=F(1),radius=F(1),pivot=F(1)),dict(asset=F(-1)),dict(q=(Z,Z,Z,Z)),dict(g=(Z,Z,True)),dict(g=[Z,Z,Z]),dict(t=(F(2**1201),Z,Z)),dict(columns=((O,Z,Z),(Z,O,Z),(Z,Z,1)))]
        for x in bad:
            with self.subTest(x=x), self.assertRaises((ValueError,TypeError)):
                self.bound(**x)
        for cap in (Z,F(-1),True,1):
            with self.assertRaises((ValueError,TypeError)):
                self.bound().fits_cap(cap)

if __name__ == '__main__':
    unittest.main(verbosity=2)

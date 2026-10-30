import math
import random
import struct
import types
import unittest
import numpy as np
from competition.deepeye.simulation.sensors import forward_profile as f
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
try:
    from competition.deepeye.simulation.sensors import _ordered_field_batch as b
except ImportError:
    b = None


def bit(x): return struct.pack('>d', x)
def B(rank, sigma, center=(0.,0.,0.), dims=(1.,1.,1.), matrix=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)), kind='box'):
    return rank,sigma,kind,center,dims,matrix

def original(pieces,bg,eps,xyz):
    q=object.__new__(OwnedWorldField); q._pieces=pieces; q._background=bg; q._epsilon=eps
    return [OwnedWorldField._sample_sigma_pure(q,*p) for p in xyz]

def cmp(v): return None if v is None else bit(v)

class FieldBatchControls(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(b, 'new field batch missing')
    def test_fsum_rounded_products_and_rounding(self):
        cases=[(1e16,1.,1e-16),(-1e16,-1.,-1e-16),(1.,-1.,0.),(-0.,-0.,-0.),
               (1.,2**-53,2**-54),(2**-1022,5e-324,-2**-1022),
               (1e308,1e308,-1e308)]
        rng=random.Random(987)
        cases.extend(tuple(rng.uniform(-1e9,1e9) for _ in range(3)) for i in range(800))
        actual, supported=b._fsum3(np.array(cases,dtype=np.float64))
        for row, value, ok in zip(cases,actual,supported):
            try: want=math.fsum(row)
            except (OverflowError,ValueError): self.assertFalse(ok); continue
            if ok: self.assertEqual(bit(want),bit(float(value)))
    def test_field_all_priorities_unknown_boundary_ties(self):
        xyz=[(0.,0.,0.),(1.,0.,0.),(math.nextafter(1.,0.),0.,0.),
             (math.nextafter(1.,math.inf),0.,0.),(3.,0.,0.),(-0.,0.,0.)]
        cases=[(),(B(1,None),B(5,0.2)),(B(5,0.2),B(1,0.3,center=(1.,0.,0.))),
               (B(2,0.1),B(2,0.3)),tuple(B(i,0.01*i) for i in range(1,6)),
               tuple(B(1,0.1,center=(float(i+5),0.,0.)) for i in range(256))]
        for pieces in cases:
            got=b._sample_points(pieces,0.005,0.,xyz)
            self.assertEqual(list(map(cmp,original(pieces,0.005,0.,xyz))),list(map(cmp,got)))
    def test_rotated_box_epsilon_and_fallback(self):
        c=math.sqrt(0.5); m=((c,-c,0.),(c,c,0.),(0.,0.,1.))
        xyz=[(0.,0.,0.),(0.5,0.5,0.),(1.,1.,0.),(5e-324,0.,0.),(float('nan'),0.,0.),(1e308,0.,0.)]
        for pieces in ((B(1,0.2,matrix=m),),(B(2,0.1,kind='cylinder'),B(4,None)),(B(4,None),B(2,0.1,kind='cylinder'))):
            self.assertEqual(list(map(cmp,original(pieces,0.01,0.01,xyz))),list(map(cmp,b._sample_points(pieces,0.01,0.01,xyz))))
    def test_integrated_fresh_profile(self):
        from competition.deepeye.simulation.sensors import _ordered_numpy_kernel as k
        rows=((0.,0.,0.,1.,1.,1.,1.,1.),(2.,0.,0.,2.,1.,1.,1.,1.),(3.,0.,0.,1.,2.,1.,1.,1.))
        pieces=(B(1,0.02),); pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        q=object.__new__(OwnedWorldField); q._pieces=pieces;q._background=.01;q._epsilon=0.
        g=dict(f._kernel_channels.__globals__);g['_weight_table']=lambda: rows
        ref=types.FunctionType(f._kernel_channels.__code__,g)
        self.assertEqual(tuple(map(bit,ref(pose,q._sample_sigma_pure))),tuple(map(bit,k._channels(pose,pieces,.01,0.,rows))))
        pa=f.ForwardProfile(em_rng=random.Random(301),vibration_rng=random.Random(302))
        pb=f.ForwardProfile(em_rng=random.Random(301),vibration_rng=random.Random(302))
        ga=dict(f.ForwardProfile.acquire_em.__globals__);ga['_kernel_channels']=lambda p,s: ref(p,q._sample_sigma_pure)
        gb=dict(ga);gb['_kernel_channels']=lambda p,s:k._channels(p,pieces,.01,0.,rows)
        a=types.FunctionType(f.ForwardProfile.acquire_em.__code__,ga); bb=types.FunctionType(f.ForwardProfile.acquire_em.__code__,gb)
        for tick in range(0,110,10):
            if tick%50==0: a(pa,tick,pose,context='formation',sampler=q._sample_sigma_pure);bb(pb,tick,pose,context='formation',sampler=q._sample_sigma_pure)
            self.assertEqual(pa.sample_adc(tick).to_payload(),pb.sample_adc(tick).to_payload())
        self.assertEqual(pa._em_rng.getstate(),pb._em_rng.getstate());self.assertEqual(pa._vibration_rng.getstate(),pb._vibration_rng.getstate())
    def test_random_rotated_scenes_and_fault_positions(self):
        rng=random.Random(56056)
        for turn in range(30):
            angle=rng.uniform(-3.,3.); c=math.cos(angle); sn=math.sin(angle)
            m=((c,-sn,0.),(sn,c,0.),(0.,0.,1.))
            pieces=tuple(B(rng.randrange(1,6),rng.choice((None,.01,.02,.3)),
                           tuple(rng.uniform(-2.,2.) for _ in range(3)),
                           tuple(rng.uniform(.1,2.) for _ in range(3)),m) for _ in range(7))
            points=[tuple(rng.uniform(-3.,3.) for _ in range(3)) for _ in range(90)]
            for at in (0,len(points)//2,len(points)-1):
                points[at]=(float('nan'),0.,0.)
            got=b._sample_points(pieces,.005,.001,points)
            self.assertEqual(list(map(cmp,original(pieces,.005,.001,points))),list(map(cmp,got)))

    def test_three_sums_cancellation_and_half_even(self):
        rng=random.Random(356)
        rows=[]
        for i in range(5000):
            x=rng.uniform(-1e30,1e30); y=-x; z=rng.uniform(-1e15,1e15)
            rows.append((x,y,z))
            rows.append((z,x,y))
        out,ok=b._fsum3(np.asarray(rows,dtype=np.float64))
        self.assertTrue(ok.all())
        for row,x in zip(rows,out): self.assertEqual(bit(math.fsum(row)),bit(float(x)))

    def test_coordinate_bits_and_five_accumulators(self):
        from competition.deepeye.simulation.sensors import _ordered_numpy_kernel as k
        p=f.Pose((-0.,4.,-2.),(0.,0.,0.,1.))
        rows=tuple((float(i)/8.,-0.,float(i)/4.,1.+i%3,2.,0.25,4.,0.5) for i in range(17))
        coords=k._coordinates(p,rows); m=f._rotation_matrix(p.orientation_xyzw)
        for row,point in zip(rows,coords):
            for j in range(3):
                x=p.position_m[j]+m[j][0]*row[0]+m[j][1]*row[1]+m[j][2]*row[2]
                self.assertEqual(bit(x),bit(point[j]))
        sigma=np.asarray([.01+(i%3)*.01 for i in range(len(rows))])
        for j in range(5):
            weights=np.asarray([r[3+j] for r in rows]); mask=weights>0
            left=0.; weighted=0.
            for w,s in zip(weights[mask],sigma[mask]): left+=float(w);weighted+=float(w)*float(s)
            acc=np.add.accumulate(np.r_[0.,weights[mask]])[-1]
            weighted_acc=np.add.accumulate(np.r_[0.,np.multiply(weights[mask],sigma[mask])])[-1]
            self.assertEqual(bit(left),bit(float(acc)));self.assertEqual(bit(weighted),bit(float(weighted_acc)))

    def test_malformed_domain_refusal(self):
        with self.assertRaises((TypeError,ValueError)): b._sample_points([],0.01,0.,[(0.,0.,0.)])
        self.assertEqual([None], b._sample_points((),0.01,0.,[(True,0.,0.)]))

if __name__=='__main__': unittest.main(verbosity=2)

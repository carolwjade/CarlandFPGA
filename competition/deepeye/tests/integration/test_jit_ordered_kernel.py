import math,random,struct,unittest,types
from competition.deepeye.simulation.sensors import forward_profile as f
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
try:
    from competition.deepeye.simulation.sensors import _jit_ordered_kernel as k
except ImportError: k=None

def bit(x): return struct.pack('>d',x)
def box(rank,sigma,center=(0.,0.,0.),kind='box'):
    return (rank,sigma,kind,center,(1.,1.,1.),((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)))
def field(pieces):
    obj=object.__new__(OwnedWorldField);obj._pieces=pieces;obj._background=.005;obj._epsilon=0.;return obj
class StrictJitControls(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(k,'new strict JIT component absent')
    def test_fsum_cancellation_halfway_and_zero(self):
        rng=random.Random(6401)
        cases=[(1e16,1.,1e-16),(-1e16,-1.,-1e-16),(1.,2**-53,2**-54),(-0.,-0.,-0.)]
        cases += [tuple(rng.uniform(-1e10,1e10) for _ in range(3)) for i in range(500)]
        cases += [(5e-324,-5e-324,-0.),(2**-1022,5e-324,-2**-1022)]
        for row in cases: self.assertEqual(bit(math.fsum(row)),bit(k._fsum3(*row)))
        with self.assertRaises(OverflowError): k._fsum3(1e308,1e308,-1e308)
    def test_field_and_whole_point_fallback(self):
        points=[(0.,0.,0.),(1.,0.,0.),(math.nextafter(1.,0.),0.,0.),(3.,0.,0.),(5e-324,0.,0.)]
        scenes=[(),(box(1,None),box(5,.1)),(box(5,.1),box(1,.2,center=(1.,0.,0.))),
                (box(1,.1,kind='cylinder'),),(box(2,.1),box(2,.2)),tuple(box(1,.1,(i+10.,0.,0.)) for i in range(256))]
        for pieces in scenes:
            obj=field(pieces); prepared=k._prepare(pieces,.005,0.)
            for p in points:
                want=obj._sample_sigma_pure(*p); got=k._sample(prepared,p)
                self.assertEqual(None if want is None else bit(want),None if got is None else bit(got))
                pose=f.Pose(p,(0.,0.,0.,1.))
                sums=k._raw_sums(pose,prepared,((0.,0.,0.,1.,1.,1.,1.,1.),))
                self.assertEqual(None if want is None else bit(want),None if sums is None else bit(sums[1][0]))
    def test_ordered_sums_and_channels(self):
        p=f.Pose((0.,0.,0.),(0.,0.,0.,1.));pieces=(box(1,.01),); obj=field(pieces)
        rows=((0.,0.,0.,1.,2.,3.,4.,5.),(2.,0.,0.,2.,1.,1.,1.,1.))
        sw,sws=k._raw_sums(p,k._prepare(pieces,.005,0.),rows)
        for j in range(5):
            a=0.;b=0.
            for row in rows:
                s=obj._sample_sigma_pure(row[0],row[1],row[2]);w=row[3+j]
                if w>0.:a+=w;b+=w*s
            self.assertEqual(bit(a),bit(sw[j]));self.assertEqual(bit(b),bit(sws[j]))
    def test_seeded_profile_and_adc(self):
        rows=((0.,0.,0.,1.,2.,3.,4.,5.),(2.,0.,0.,2.,1.,1.,1.,1.));pieces=(box(1,.01),)
        obj=field(pieces);prep=k._prepare(pieces,.005,0.);pose=f.Pose((0.,0.,0.),(0.,0.,0.,1.))
        env=dict(f._kernel_channels.__globals__);env['_weight_table']=lambda:rows
        ref=types.FunctionType(f._kernel_channels.__code__,env)
        g=dict(f.ForwardProfile.acquire_em.__globals__);g['_kernel_channels']=lambda p,s:ref(p,obj._sample_sigma_pure)
        h=dict(g);h['_kernel_channels']=lambda p,s:k._channels(p,prep,rows)
        a=types.FunctionType(f.ForwardProfile.acquire_em.__code__,g);b=types.FunctionType(f.ForwardProfile.acquire_em.__code__,h)
        aa=f.ForwardProfile(em_rng=random.Random(6402),vibration_rng=random.Random(6403));bb=f.ForwardProfile(em_rng=random.Random(6402),vibration_rng=random.Random(6403))
        for tick in range(0,110,10):
            if tick%50==0:a(aa,tick,pose,context='formation',sampler=obj._sample_sigma_pure);b(bb,tick,pose,context='formation',sampler=obj._sample_sigma_pure)
            self.assertEqual(aa.sample_adc(tick).to_payload(),bb.sample_adc(tick).to_payload())
        self.assertEqual(aa._em_rng.getstate(),bb._em_rng.getstate());self.assertEqual(aa._vibration_rng.getstate(),bb._vibration_rng.getstate())
if __name__=='__main__':unittest.main(verbosity=2)

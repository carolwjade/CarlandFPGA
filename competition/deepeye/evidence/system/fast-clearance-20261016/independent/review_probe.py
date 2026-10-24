"""Independent bounded review probes. No product mutations or product helpers in oracle."""
from pathlib import Path
from decimal import Decimal as D, localcontext, ROUND_UP, Inexact, Rounded
from fractions import Fraction
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib
import json
import math
import random
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
sys.path.insert(0, str(PRODUCT))
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion.gate_geometry import Capsule, Gate

PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
PI = D('3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647')
EPS = D('1e-90')
REPORT = {'work_id': 'A-g06-fast-clearance-review-20261016-v1', 'precision': 110,
          'limitations': ['Finite probes are not a proof for all inputs.',
                         'Curved path checks sample time and finite capsule sections.',
                         'No adapter/source authentication, Godot, assets, phase or G06 acceptance.']}

def exact(x):
    return D.from_float(float(x))

def add(x, y):
    return tuple(a+b for a, b in zip(x, y))

def sub(x, y):
    return tuple(a-b for a, b in zip(x, y))

def mul(x, t):
    return tuple(a*t for a in x)

def dot(x, y):
    return sum((a*b for a, b in zip(x, y)), D(0))

def norm(x):
    return dot(x, x).sqrt()

def unit(x):
    return mul(x, D(1)/norm(x))

def cos(x):
    term = total = D(1)
    for k in range(1, 60):
        term *= -x*x/D((2*k-1)*(2*k))
        total += term
    return total

def sin(x):
    term = total = x
    for k in range(1, 60):
        term *= -x*x/D((2*k)*(2*k+1))
        total += term
    return total

def oracle(body, gate, errors):
    p = tuple(map(exact, body.position_m))
    n = tuple(map(exact, gate.normal))
    a = unit(tuple(map(exact, body.axis)))
    c = sub(p, tuple(map(exact, gate.center_m)))
    s, an = dot(c,n), dot(a,n)
    h, r = exact(body.half_segment_m), exact(body.radius_m)
    extent = h*abs(an)+r
    beta = exact(errors.position_error_m)+(h+r)*exact(errors.angle_error_rad)+exact(errors.additional_margin_m)
    radial = None
    if an:
        m = sub(c, mul(a, s/an))
        radial = norm(m)+(r+beta)/abs(an)
    return {'a': a, 'c': c, 'n': n, 's': s, 'an': an, 'h': h, 'r': r,
            'beta': beta, 'low': s-extent, 'high': s+extent, 'radial': radial}

def sampled_section_max(p, a, h, r, gate, steps=40):
    c = sub(p, tuple(map(exact, gate.center_m)))
    n = tuple(map(exact, gate.normal))
    s, an = dot(c,n), dot(a,n)
    lower, upper = -h, h
    if an:
        t1, t2 = (-r-s)/an, (r-s)/an
        lower, upper = max(lower,min(t1,t2)), min(upper,max(t1,t2))
    if lower > upper:
        return None
    best = None
    for i in range(steps+1):
        t = lower+(upper-lower)*D(i)/D(steps)
        v = add(c,mul(a,t))
        signed = dot(v,n)
        radicand = r*r-signed*signed
        if radicand < -EPS:
            continue
        value = norm(sub(v,mul(n,signed)))+max(D(0),radicand).sqrt()
        best = value if best is None else max(best,value)
    return best

def instant_checks():
    rng = random.Random(2026101606)
    counts = Counter()
    min_export_slack = D('Infinity')
    for face in ('front','back','left','right','top','bottom'):
        for direction in (-1,1):
            gate = Gate(face,1.25,-2.5)
            n = tuple(map(exact,gate.normal))
            j = next(i for i,v in enumerate(n) if v)
            k, l = [i for i in range(3) if i != j]
            for i in range(48):
                p = list(gate.center_m)
                p[k] += rng.uniform(-.05,.05)
                p[l] += rng.uniform(-.03,.03)
                p[j] += rng.uniform(-.6,.6)
                axis = [0.,0.,0.]
                scale = (1.,1e-300,math.ulp(0.),100.)[i % 4]
                axis[j] = float(n[j])*direction*scale
                axis[k] = rng.uniform(-.11,.11)*scale
                axis[l] = rng.uniform(-.02,.02)*scale
                body = Capsule(tuple(p),tuple(axis),half_segment_m=(0.,.01,.4,2.)[i%4])
                err = gc.ErrorBounds((0.,1e-12,.0003)[i%3],(0.,.0001,.001)[i%3],0.)
                result = gc.section_clearance(body,gate,direction=direction,errors=err)
                ref = oracle(body,gate,err)
                counts[result.status] += 1
                if result.radial_upper_m is not None:
                    slack = exact(result.radial_upper_m)-ref['radial']
                    assert slack >= -EPS, (face,i,'radial export',str(slack))
                    min_export_slack = min(min_export_slack,slack)
                if result.status == 'EMPTY':
                    assert ref['low']-ref['beta'] > D('1e-12') or ref['high']+ref['beta'] < D('-1e-12')
                if result.nonempty_proved:
                    assert ref['low']+ref['beta'] < D('-1e-12') and ref['high']-ref['beta'] > D('1e-12')
                if result.angle_proved:
                    budget = PI/36-exact(err.angle_error_rad)
                    assert budget > 0 and D(direction)*ref['an'] > cos(budget)-EPS
                if result.status == 'CLEAR_SECTION':
                    assert result.nonempty_proved and result.angle_proved
                    assert ref['radial']+D('1e-12') < exact(.15)
                    sampled = sampled_section_max(tuple(map(exact,body.position_m)),ref['a'],ref['h'],ref['r'],gate)
                    assert sampled is not None and sampled < exact(.15)
                assert not result.motion_grant
    REPORT['instant'] = {'cases':sum(counts.values()),'statuses':dict(counts),
                         'minimum_export_minus_independent_upper_m':str(min_export_slack)}

def sweep_checks():
    rng = random.Random(701616)
    counts = Counter()
    time_count = witness_count = 0
    min_export_slack = D('Infinity')
    for face in ('front','back','left','right','top','bottom'):
        for direction in (-1,1):
            gate = Gate(face,0.,0.)
            n = tuple(map(exact,gate.normal))
            j = next(i for i,v in enumerate(n) if v)
            k, l = [i for i in range(3) if i != j]
            for case in range(12):
                start = list(gate.center_m)
                start[k] += rng.uniform(-.035,.035)
                start[l] += rng.uniform(-.01,.01)
                start[j] += rng.uniform(-.25,.25)
                axis = [0.,0.,0.]
                axis[j],axis[k] = float(n[j])*direction,rng.uniform(-.07,.07)
                body = Capsule(tuple(start),tuple(axis))
                finish = list(start)
                finish[j] += float(n[j])*direction*.02
                finish[k] += rng.uniform(-.002,.002)
                p0,p1 = tuple(map(exact,start)),tuple(map(exact,finish))
                delta = sub(p1,p0)
                bump = [D(0),D(0),D(0)]
                bump[k] = exact((-.001,.001,.002)[case%3])
                bump = tuple(bump)
                # p(t)=p0+t*d+t*(1-t)*b. |p'| >= |d|-|b| >0;
                # length <= |d|+|b|; curvature <= 2|b|/(|d|-|b|)^2.
                actual_length_bound = norm(delta)+norm(bump)
                length = math.nextafter(float(actual_length_bound),math.inf)
                curvature_ref = 2*norm(bump)/(norm(delta)-norm(bump))**2
                curvature = math.nextafter(float(curvature_ref),math.inf)
                theta = .0008
                err = gc.ErrorBounds(0.,0.,0.)
                bounds = gc.SliceBounds(tuple(finish),length,curvature,theta)
                result = gc.sweep_clearance(body,gate,direction=direction,errors=err,bounds=bounds)
                ref0 = oracle(body,gate,err)
                ref1 = oracle(Capsule(tuple(finish),body.axis),gate,err)
                rho = max(D('.0005'),(ref0['h']+ref0['r'])*exact(theta))+exact(curvature)*exact(length)**2/8
                # Independent endpoint formula with original radius removed.
                radial = max(ref0['radial'],ref1['radial'])+rho/abs(ref0['an'])
                if result.radial_upper_m is not None:
                    slack = exact(result.radial_upper_m)-radial
                    assert slack >= -EPS, ('sweep export',str(slack))
                    min_export_slack = min(min_export_slack,slack)
                assert exact(result.inflation_upper_m) >= rho-EPS
                if result.status == 'SAFE_IF_INTERSECTING':
                    assert radial+D('1e-12') < exact(.15)
                    assert D(direction)*ref0['an'] > cos(PI/36-exact(theta))-EPS
                counts[result.status] += 1
                # Rotate toward a perpendicular direction in the same plane,
                # with delta(t)=theta*4*t*(1-t): endpoint net zero, interior tilt.
                v = [D(0),D(0),D(0)]
                v[k],v[j] = ref0['a'][j],-ref0['a'][k]
                v = unit(tuple(v))
                for ti in range(33):
                    t = D(ti)/32
                    pos = add(add(p0,mul(delta,t)),mul(bump,t*(1-t)))
                    angle = exact(theta)*4*t*(1-t)
                    a = add(mul(ref0['a'],cos(angle)),mul(v,sin(angle)))
                    sampled = sampled_section_max(pos,a,ref0['h'],ref0['r'],gate,24)
                    time_count += 1
                    if sampled is not None:
                        witness_count += 1
                        if result.status == 'SAFE_IF_INTERSECTING':
                            assert sampled < exact(.15), (face,direction,case,ti,'false-clear witness')
                            assert sampled <= exact(result.radial_upper_m)+EPS
                    assert not result.motion_grant and not result.nonempty_proved
    REPORT['curved_sweeps'] = {'cases':sum(counts.values()),'statuses':dict(counts),
                              'sampled_times':time_count,'nonempty_sections_sampled':witness_count,
                              'minimum_export_minus_independent_upper_m':str(min_export_slack),
                              'curve':'regular 3D-embedded quadratic with certified loose L/kappa and return rotation',
                              'note':'Sampling is falsification evidence, not all-time validation.'}

def context_checks():
    gate = Gate('front',0.,0.)
    body_args = ((.001,-.002,15.01),(-.03,.04,-1.))
    def run():
        b = Capsule(*body_args)
        e = gc.ErrorBounds(.001,.00015,.00002)
        s = gc.SliceBounds((.001,-.002,15.009),.0011,.5,.0007)
        return asdict(gc.section_clearance(b,gate,direction=-1,errors=e)), asdict(gc.sweep_clearance(b,gate,direction=-1,errors=e,bounds=s))
    expected = run()
    with localcontext() as ctx:
        ctx.prec,ctx.rounding,ctx.Emax,ctx.Emin = 1,ROUND_UP,2,-2
        ctx.traps[Inexact] = ctx.traps[Rounded] = True
        gc._cos_limit_upper.cache_clear()
        assert run() == expected
        importlib.reload(gc)
        assert run() == expected
    REPORT['ambient_context'] = {'precision':1,'rounding':'ROUND_UP','Emax':2,'Emin':-2,
                                 'Inexact_and_Rounded_trapped':True,'cold_reload_and_input_construction':'passed'}

def adversarial_checks():
    gate=Gate('front',0.,0.)
    errors=gc.ErrorBounds(0.,0.,0.)
    # An actual curved middle can scrape despite clear instantaneous endpoints.
    p0=(.0294,0.,15.3)
    p1=(.0294,0.,15.32)
    body=Capsule(p0,(0.,0.,1.))
    end=Capsule(p1,(0.,0.,1.))
    assert gc.section_clearance(body,gate,direction=1,errors=errors).status=='CLEAR_SECTION'
    assert gc.section_clearance(end,gate,direction=1,errors=errors).status=='CLEAR_SECTION'
    middle=(exact(.0294)+D('.004')/4,D(0),(exact(15.3)+exact(15.32))/2)
    witness=sampled_section_max(middle,(D(0),D(0),D(1)),exact(.4),exact(.12),gate)
    assert witness > exact(.15)
    # |d|~.02, b=.004 => L<.025; kappa<32, selected kappa=40.
    result=gc.sweep_clearance(body,gate,direction=1,errors=errors,bounds=gc.SliceBounds(p1,.025,40.,0.))
    assert result.status=='UNKNOWN'
    boundary=[]
    for r in (.15,math.nextafter(.15,0.),math.nextafter(.15,math.inf),.15-5e-13,.15-2e-12):
        res=gc.section_clearance(Capsule((0.,0.,15.),(0.,0.,1.),radius_m=r),gate,direction=1,errors=errors)
        if exact(r)+D('1e-12') >= exact(.15):
            assert res.status!='CLEAR_SECTION'
        boundary.append({'radius':r,'status':res.status})
    # Theta=0 denotes a full path bound, not endpoints; the function cannot
    # authenticate a caller who lies about the path. Explicitly demonstrate this limit.
    dishonest=gc.sweep_clearance(body,gate,direction=1,errors=errors,bounds=gc.SliceBounds(p1,.025,0.,0.))
    assert dishonest.status=='SAFE_IF_INTERSECTING'
    REPORT['adversarial']={'curved_middle_radial_witness_m':str(witness),
                           'truthful_curvature_status':result.status,'false_zero_curvature_status':dishonest.status,
                           'interpretation':'False zero curvature violates the explicit caller assumptions; this is not an implementation false-clear.',
                           'radial_contact_cases':boundary}

def main():
    scope=json.loads((ROOT/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
    actual=hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert actual==PIN
    REPORT['requirements_sha256']=actual
    with localcontext() as ctx:
        ctx.prec=110
        instant_checks()
        sweep_checks()
        adversarial_checks()
        context_checks()
    before=json.loads((OUT/'source_snapshot.json').read_text())
    current={name:hashlib.sha256((PRODUCT/name).read_bytes()).hexdigest() for name in before['hashes']}
    assert before['hashes']==current, 'reviewed source changed during probes'
    REPORT['product_hashes']=current
    REPORT['source_unchanged']=True
    REPORT['result']='no false-clear reproduced under stated assumptions'
    (OUT/'probe_results.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(REPORT,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()

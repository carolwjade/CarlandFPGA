"""Private independent formula, mutation and timing audit. No product writes."""
from decimal import Decimal, localcontext
from importlib import import_module, util
from pathlib import Path
import hashlib
import io
import json
import math
import random
import statistics
import sys
import time
import types
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT/'.local/deepeye-implementation-a'
sys.path.insert(0, str(PRODUCT))
gc = import_module('competition.deepeye.simulation.authority.motion.gate_clearance')
g = import_module('competition.deepeye.simulation.authority.motion.gate_geometry')
D = Decimal.from_float
PI = Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679821480865132823066470938446')
RNG = random.Random(20261015)


def sincos(x):
    sin_term, cos_term = x, Decimal(1)
    sine, cosine = sin_term, cos_term
    for k in range(1, 60):
        sin_term *= -x*x/Decimal((2*k)*(2*k+1))
        cos_term *= -x*x/Decimal((2*k-1)*(2*k))
        sine += sin_term
        cosine += cos_term
    return sine, cosine


def norm3(v):
    return sum((x*x for x in v), Decimal(0)).sqrt()


def high_precision_oracles():
    errors = gc.ErrorBounds(0., 0., 0.)
    gate = g.Gate('front', 0., 0.)
    minima = []
    with localcontext() as context:
        context.prec = 120
        # Independent closed-form *finite capsule* maximizer: eccentricity
        # lies along the ellipse major axis and the attaining cylinder point
        # is proved inside the finite central segment.
        for _ in range(256):
            angle = math.radians(RNG.uniform(0., 4.99))
            sign = RNG.choice((-1, 1))
            ax, az = sign*math.sin(angle), sign*math.cos(angle)
            px, pz = RNG.uniform(-.025, .025), 15.+RNG.uniform(-.1, .1)
            body = g.Capsule((px, 0., pz), (ax, 0., az))
            result = gc.section_clearance(body, gate, direction=sign, errors=errors)
            length = (D(ax)**2+D(az)**2).sqrt()
            ux, uz = D(ax)/length, D(az)/length
            s = D(pz)-Decimal(15)
            centre = D(px)-s*ux/uz
            radius = D(body.radius_m)
            exact_max = abs(centre)+radius/abs(uz)
            chosen_x = centre+(radius/abs(uz) if centre >= 0 else -radius/abs(uz))
            along_axis = (chosen_x-D(px))*ux-s*uz
            assert abs(along_axis) < D(body.half_segment_m)
            assert result.radial_upper_m is not None
            slack = D(result.radial_upper_m)-exact_max
            assert slack >= 0, ('finite ellipse bound failed', slack)
            minima.append(slack)
        # Sphere and finite-endcap section formula, independent of axis-plane
        # ellipse overbound. These may legitimately return UNKNOWN.
        for index in range(256):
            half = 0. if index % 2 else .4
            extra = RNG.uniform(.000001, .119999)
            s = half+extra
            px, py = RNG.uniform(-.04, .04), RNG.uniform(-.04, .04)
            body = g.Capsule((px, py, 15.+s), (0., 0., 1.), half_segment_m=half)
            result = gc.section_clearance(body, gate, direction=1, errors=errors)
            actual_s = abs(D(body.position_m[2])-Decimal(15))-D(half)
            exact_max = (D(px)**2+D(py)**2).sqrt()+(D(.12)**2-actual_s**2).sqrt()
            assert D(result.radial_upper_m) >= exact_max
        # Exact circular-motion family, whole-time maximum is at the start.
        # For collinear eccentricity m>0, derivative of M=m+r sec(a) is
        # k sec(a)^2 * (-z + r sin(a)).  z>=.1, r*sin(a)<.011.
        # Thus M strictly decreases over the complete interval, not merely
        # at sampled times. The entire central-cylinder maximizer stays |t|<h.
        endpoint_errors = []
        for _ in range(256):
            angle = math.radians(RNG.uniform(.1, 4.8))
            ax, az = math.sin(angle), math.cos(angle)
            q = (D(ax)**2+D(az)**2).sqrt()
            ux, uz = D(ax)/q, D(az)/q
            k, length = D(.5), D(RNG.uniform(.0001, .0017))
            phi = k*length
            sn, cs = sincos(phi)
            s = D(15.1)-Decimal(15)
            px = float(D(RNG.uniform(.01, .025))+s*ux/uz)
            body = g.Capsule((px, 0., 15.1), (ax, 0., az))
            exact_end = (D(px)+(ux*sn+uz*(1-cs))/k, Decimal(0),
                         D(15.1)+(uz*sn-ux*(1-cs))/k)
            end = tuple(float(v) for v in exact_end)
            endpoint_error = norm3(tuple(D(a)-b for a, b in zip(end, exact_end)))
            endpoint_errors.append(endpoint_error)
            assert endpoint_error < D(1e-12)
            theta = math.nextafter(float(phi), math.inf)
            assert D(theta) >= phi
            bounds = gc.SliceBounds(end, float(length), .5, theta)
            result = gc.sweep_clearance(body, gate, direction=1,
                                        errors=gc.ErrorBounds(1e-12, 0., 0.), bounds=bounds)
            m0 = D(px)-s*ux/uz
            uz1, ux1 = uz*cs-ux*sn, ux*cs+uz*sn
            z1 = exact_end[2]-Decimal(15)
            m1 = exact_end[0]-z1*ux1/uz1
            assert m1 > 0 and m0 > 0 and z1 >= s > D(.12)*ux1
            assert (z1+D(.12)*abs(ux1))/uz1 < D(.4)
            exact_whole_time_max = m0+D(.12)/uz
            assert result.status == 'SAFE_IF_INTERSECTING'
            assert D(result.radial_upper_m) > exact_whole_time_max
        for _ in range(256):
            budget = D(RNG.uniform(0., math.radians(4.999)))
            threshold = gc._cos_limit_upper(budget)
            _, actual = sincos(PI/36-budget)
            assert threshold >= actual, ('cos upper failed', threshold-actual)
    return {'finite_capsule_closed_forms': 256, 'sphere_and_cap_closed_forms': 256,
            'whole_time_monotonic_arc_oracles': 256, 'cosine_threshold_checks': 256,
            'minimum_export_slack_m': str(min(minima)),
            'maximum_endpoint_rounding_m': str(max(endpoint_errors)),
            'precision': 120, 'oracle_uses_product_interval_helpers': False}


def mutation_audit():
    test_path = PRODUCT/'competition/deepeye/tests/simulation/test_gate_clearance.py'
    spec = util.spec_from_file_location('gate_clearance_private_tests', test_path)
    tests = util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    source = Path(gc.__file__).read_text(encoding='utf-8')
    mutations = {
        'ignore_direction': ('oriented = un if direction == 1 else -un', 'oriented = g._abs_bounds(un)'),
        'remove_uncertainty': ('return rb, beta', 'return rb, _I.exact(Decimal(0))'),
        'remove_rotation_floor': ("_MIN_ROTATION_INFLATION = Decimal('.0005')", "_MIN_ROTATION_INFLATION = Decimal('0')"),
        'remove_rotation_cover': ('(rb*theta).hi', 'Decimal(0)'),
        'remove_chord_cover': ('g._UP.add(rotation, chord.hi)', 'g._UP.add(rotation, Decimal(0))'),
        'ignore_end_position': ('max(g._norm(m0).hi, g._norm(m1).hi)', 'g._norm(m0).hi'),
        'ignore_slice_angle': ('g._UP.add(theta.hi, Decimal.from_float(errors.angle_error_rad))',
                               'Decimal.from_float(errors.angle_error_rad)'),
        'remove_slice_angle_cap': ('if theta.hi > _MAX_SLICE_ROTATION.lo:', 'if False:'),
        'allow_contact': ("_GUARD = Decimal('1e-12')", "_GUARD = Decimal('-1e-12')"),
    }
    results = []
    raw = []
    for name, (before, after) in mutations.items():
        assert source.count(before) == 1, (name, source.count(before))
        mutant_name = gc.__name__+'_'+name
        mutant = types.ModuleType(mutant_name)
        mutant.__package__ = gc.__package__
        sys.modules[mutant_name] = mutant
        exec(compile(source.replace(before, after), mutant_name, 'exec'), mutant.__dict__)
        tests.gc = mutant
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(tests.GateClearanceTests))
        raw.append(name+'\n'+stream.getvalue())
        results.append({'mutation': name, 'caught': not result.wasSuccessful(),
                        'failures': len(result.failures), 'errors': len(result.errors)})
    tests.gc = gc
    (HERE/'mutation-raw.txt').write_text('\n'.join(raw), encoding='utf-8')
    assert all(x['caught'] for x in results), results
    return results


def stats(values):
    ordered = sorted(values)
    return {'n': len(values), 'median_ms': statistics.median(values),
            'p95_ms': ordered[math.ceil(.95*len(values))-1], 'max_ms': max(values)}


def performance():
    gate = g.Gate('front', 0., 0.)
    errors = gc.ErrorBounds(.00001, .00001, .00001)
    timings = {'section_warm': [], 'sweep_warm': [], 'section_new_inputs': [], 'sweep_new_inputs': [],
               'section_cold_threshold': [], 'sweep_cold_threshold': []}
    counts = {}
    for index in range(2048):
        angle = math.radians(RNG.uniform(0., 4.8))
        position = (RNG.uniform(-.045, .045), RNG.uniform(-.01, .01), 15.+RNG.uniform(-.6, .6))
        axis = (math.sin(angle), 0., math.cos(angle))
        end = (position[0], position[1], position[2]+.001)
        body = g.Capsule(position, axis)
        bounds = gc.SliceBounds(end, .00101, .5, .00051)
        t0 = time.perf_counter_ns()
        result = gc.section_clearance(body, gate, direction=1, errors=errors)
        timings['section_warm'].append((time.perf_counter_ns()-t0)/1e6)
        counts['section_'+result.status] = counts.get('section_'+result.status, 0)+1
        t0 = time.perf_counter_ns()
        result = gc.sweep_clearance(body, gate, direction=1, errors=errors, bounds=bounds)
        timings['sweep_warm'].append((time.perf_counter_ns()-t0)/1e6)
        counts['sweep_'+result.status] = counts.get('sweep_'+result.status, 0)+1
        t0 = time.perf_counter_ns()
        gc.section_clearance(g.Capsule(position, axis), gate, direction=1,
                             errors=gc.ErrorBounds(.00001, .00001, .00001))
        timings['section_new_inputs'].append((time.perf_counter_ns()-t0)/1e6)
        t0 = time.perf_counter_ns()
        gc.sweep_clearance(g.Capsule(position, axis), gate, direction=1,
                           errors=gc.ErrorBounds(.00001, .00001, .00001),
                           bounds=gc.SliceBounds(end, .00101, .5, .00051))
        timings['sweep_new_inputs'].append((time.perf_counter_ns()-t0)/1e6)
    # Uncached threshold each call, separate from common-bound warm-cache case.
    for index in range(256):
        errors = gc.ErrorBounds(.00001, (index+1)*1e-7, .00001)
        for name, call in (
            ('section_cold_threshold', lambda: gc.section_clearance(body, gate, direction=1, errors=errors)),
            ('sweep_cold_threshold', lambda: gc.sweep_clearance(body, gate, direction=1, errors=errors, bounds=bounds))):
            gc._cos_limit_upper.cache_clear()
            t0 = time.perf_counter_ns()
            call()
            timings[name].append((time.perf_counter_ns()-t0)/1e6)
    return {'statistics': {name: stats(values) for name, values in timings.items()},
            'classification_counts': counts, 'raw_ms': timings,
            'scope': 'CPython local serial process; not Godot, load guarantee, deadline proof or G06 acceptance'}


def main():
    result = {'source_sha256': hashlib.sha256(Path(gc.__file__).read_bytes()).hexdigest(),
              'geometry_sha256': hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest(),
              'python': sys.version, 'oracles': high_precision_oracles(), 'mutations': mutation_audit(),
              'performance': performance()}
    (HERE/'audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    summary = dict(result)
    summary['performance'] = {k: v for k, v in result['performance'].items() if k != 'raw_ms'}
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

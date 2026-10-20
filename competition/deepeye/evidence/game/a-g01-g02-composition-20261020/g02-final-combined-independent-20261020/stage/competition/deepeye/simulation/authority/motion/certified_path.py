"""Canonical analytic numeric paths with derived whole-slice bounds.

No externally supplied MotionStep, curvature, distance or rotation is trusted.
This is an internal numeric module, not an authenticated authority registry,
watchdog, collision query, gate phase or motion grant. Explicit error sources
remain caller assertions. See docs/certified_motion_path.md for the proof.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
import math

from competition.deepeye.integration.motion import MotionCommand, validate
from .kinematics import RigidState, MAX_DT_NS
from . import gate_geometry as g
from . import gate_clearance as gc


_I = g._Interval  # Deliberate internal coupling, not a public interval ABI.
_ZERO = _I.exact(Decimal(0))
_ONE = _I.exact(Decimal(1))
_TWO = _I.exact(Decimal(2))
_FOUR = _I.exact(Decimal(4))
_Z_AXIS = (_ZERO, _ZERO, _ONE)
DERIVATION_VERSION = 'canonical-path-fraction-ns-decimal60-taylor4-v1'
COMMAND_SEMANTICS = 'validated MotionCommand binary64 values exact; initial quaternion exactly normalized'
_ASSUMPTIONS = (
    'Raw codes are revalidated here; their validated binary64 numbers define the canonical analytic path.',
    'Initial position and speed are exact binary64 values; quaternion means its exact mathematical normalization.',
    'Explicit inherited pose and additional margins are asserted upper bounds with unverified sources.',
    'All slices share one original exact speed law; rounded output speeds must not silently replace that law.',
    'Monotonic timestamps and hard STOP are numeric inputs, not verified watchdog or clock observations.',
    'Frozen records and derivation versions are provenance, not authenticated ownership, scene freshness or motion authority.',
    'Asset containment, Godot transforms and queries, world/grant CAS, gate phases and arrival require later integration.',
)


def _fraction_interval(value):
    return _I(g._DOWN.divide(Decimal(value.numerator), Decimal(value.denominator)),
              g._UP.divide(Decimal(value.numerator), Decimal(value.denominator)))


def _upper_float(value):
    """Export a nonnegative Decimal upper bound, including positive underflow."""
    if value < 0 or not value.is_finite():
        raise ValueError('finite nonnegative bound required')
    if value == 0:
        return 0.
    result = math.nextafter(float(value), math.inf)
    if not math.isfinite(result):
        raise ValueError('bound cannot be exported as finite binary64')
    return result


def _midpoint_float(interval):
    # Nominal accuracy is not assumed: the final returned value is enclosed
    # against the canonical interval after all export/normalization operations.
    return float(g._DOWN.divide(g._DOWN.add(interval.lo, interval.hi), Decimal(2)))


def _unit(vector):
    active = [part for part in vector if part != 0]
    if not active:
        raise ValueError('zero vector cannot be normalized')
    if len(active) == 1:
        return tuple(_I.exact(Decimal(1 if part > 0 else -1)) if part else _ZERO
                     for part in vector)
    parts = tuple(g._exact(part) for part in vector)
    norm = g._norm(parts)
    return tuple(part.divide(norm) for part in parts)


def _trig_from_square(square, *, cosine=False):
    """Enclose sinc(sqrt(z)) or cos(sqrt(z)) on the proved whole domain.

    Here z <= .00125**2 < .0000015626. Alternating terms decrease, so
    the polynomial ending at j=4 is above the function; subtracting the
    magnitude of j=5 is below it. Directed arithmetic encloses both bounds.
    """
    if square.lo < 0 or square.hi > Decimal('.0000015626'):
        raise ValueError('trigonometric argument outside proved domain')
    total = term = _ONE
    for j in range(1, 5):
        denominator = (2*j-1)*(2*j) if cosine else (2*j)*(2*j+1)
        term = (term*square).divide(_I.exact(Decimal(denominator)))
        total = total-term if j % 2 else total+term
    denominator = 90 if cosine else 110
    remainder = (term*square).divide(_I.exact(Decimal(denominator))).hi
    return _I(g._DOWN.subtract(total.lo, remainder), total.hi)


def _multiply_q(left, right):
    x, y, z, w = left
    a, b, c, d = right
    return (w*a+x*d+y*c-z*b, w*b-x*c+y*d+z*a,
            w*c+x*b-y*a+z*d, w*d-x*a-y*b-z*c)


def _rotate(q, v):
    x, y, z, w = q
    a, b, c = v
    tx, ty, tz = _TWO*(y*c-z*b), _TWO*(z*a-x*c), _TWO*(x*b-y*a)
    return (a+w*tx+y*tz-z*ty, b+w*ty+z*tx-x*tz, c+w*tz+x*ty-y*tx)


def _distance_upper(actual, expected):
    differences = []
    for point, interval in zip(actual, expected):
        part = point if isinstance(point, _I) else g._exact(point)
        diff = part-interval
        differences.append(_I.exact(max(diff.lo.copy_abs(), diff.hi.copy_abs())))
    return g._norm(tuple(differences)).hi


def _integer(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be integer in {minimum}..{maximum}')
    return value


@dataclass(frozen=True, slots=True)
class PathProvenance:
    raw_command: tuple
    command: MotionCommand
    start_state: RigidState
    requested_dt_ns: int
    inherited_errors: gc.ErrorBounds
    error_budget_reference: str
    derivation_version: str = field(default=DERIVATION_VERSION, init=False)
    command_semantics: str = field(default=COMMAND_SEMANTICS, init=False)


@dataclass(frozen=True, slots=True)
class CertifiedSample:
    elapsed_ns: int
    exact_distance_m: Fraction
    exact_speed_m_s: Fraction
    state: RigidState
    axis: tuple
    numerical_position_error_m: float
    numerical_orientation_error_rad: float
    numerical_axis_error_rad: float
    speed_export_error_m_s: float
    errors: gc.ErrorBounds


@dataclass(frozen=True, slots=True)
class CertifiedSlice:
    start: CertifiedSample
    end: CertifiedSample
    exact_arc_length_m: Fraction
    path_arc_upper_m: float
    gate_bounds: gc.SliceBounds
    errors: gc.ErrorBounds


@dataclass(frozen=True, slots=True)
class CertifiedPlan:
    provenance: PathProvenance
    start_monotonic_ns: int
    deadline_monotonic_ns: int
    hard_stop: bool
    covered_ns: int
    slices: tuple
    end: CertifiedSample
    reason: str
    assumptions: tuple = field(default=_ASSUMPTIONS, init=False)
    motion_grant: bool = field(default=False, init=False)
    authority_authenticated: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True, init=False)
class CanonicalPath:
    """Create one numerical path from raw codes, never from caller path bounds.

    Every error source is explicit. Zero is legal for an exact mathematical
    fixture; this module does not verify its source. State/command authority,
    registry identity and scene version must be bound by the later factory.
    """
    provenance: PathProvenance
    _v0: Fraction = field(repr=False)
    _target: Fraction = field(repr=False)
    _acceleration: Fraction = field(repr=False)
    _ramp_seconds: Fraction = field(repr=False)
    _yaw: _I = field(repr=False)
    _pitch: _I = field(repr=False)
    _curvature_squared: _I = field(repr=False)
    _curvature: _I = field(repr=False)
    _q0: tuple = field(repr=False)

    def __init__(self, state, profile, speed_code, yaw_q, pitch_q, dt_ns, *,
                 inherited_errors, error_budget_reference):
        if type(state) is not RigidState:
            raise TypeError('exact immutable RigidState required')
        _integer(dt_ns, 1, MAX_DT_NS, 'dt_ns')
        if type(profile) is not str:
            raise TypeError('profile must be a string')
        if type(inherited_errors) is not gc.ErrorBounds:
            raise TypeError('explicit immutable ErrorBounds required')
        if (type(error_budget_reference) is not str or not error_budget_reference.strip()
                or len(error_budget_reference) > 4096):
            raise ValueError('explicit nonempty error budget reference required')
        command = validate(profile, speed_code, yaw_q, pitch_q)
        if state.speed_m_s > command.max_speed_m_s:
            raise ValueError('actual speed exceeds selected profile')
        g._vector(state.position_m)  # finite bounded geometry coordinates
        v0, target = Fraction(state.speed_m_s), Fraction(command.target_speed_m_s)
        delta = target-v0
        yaw, pitch = g._exact(command.curvature_yaw_per_m), g._exact(command.curvature_pitch_per_m)
        k2 = yaw.square()+pitch.square()
        curvature = k2.sqrt_nonnegative()
        if curvature.hi > Decimal('.5'):
            raise ValueError('validated binary64 curvature not proved <= .5 / m')
        values = {
            'provenance': PathProvenance((profile, speed_code, yaw_q, pitch_q), command, state,
                                         dt_ns, inherited_errors, error_budget_reference),
            '_v0': v0, '_target': target,
            '_acceleration': Fraction(1 if delta > 0 else -1 if delta < 0 else 0, 4),
            '_ramp_seconds': 4*abs(delta), '_yaw': yaw, '_pitch': pitch,
            '_curvature_squared': k2, '_curvature': curvature,
            '_q0': _unit(state.orientation_xyzw),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def distance_speed(self, elapsed_ns):
        """Exact arc length and speed at an integer ns from the original start."""
        _integer(elapsed_ns, 0, self.provenance.requested_dt_ns, 'elapsed_ns')
        time = Fraction(elapsed_ns, 10**9)
        ramp = min(time, self._ramp_seconds)
        distance = self._v0*ramp+self._acceleration*ramp*ramp/2+self._target*(time-ramp)
        speed = self._v0+self._acceleration*ramp if time < self._ramp_seconds else self._target
        return distance, speed

    def _enclosed_pose(self, distance):
        length = _fraction_interval(distance)
        squared = self._curvature_squared*length.square()
        half_squared = squared.divide(_FOUR)
        sinc, sinc_half = _trig_from_square(squared), _trig_from_square(half_squared)
        cos_half = _trig_from_square(half_squared, cosine=True)
        half_length = length.divide(_TWO)
        dq = (-self._pitch*half_length*sinc_half, self._yaw*half_length*sinc_half, _ZERO, cos_half)
        q = _multiply_q(self._q0, dq)
        transverse = half_length*length*sinc_half.square()
        delta = _rotate(self._q0, (self._yaw*transverse, self._pitch*transverse, length*sinc))
        p = tuple(g._exact(x)+change for x, change in zip(self.provenance.start_state.position_m, delta))
        return p, q

    def _errors(self, distance, position_error, angle_error):
        inherited = self.provenance.inherited_errors
        # Any initial SO(3) error alpha moves the integrated displacement by
        # <= 2*S*sin(alpha/2) <= S*alpha over the complete original path.
        drift = _fraction_interval(distance)*g._exact(inherited.angle_error_rad)
        position = (g._exact(inherited.position_error_m)+drift+_I.exact(position_error)).hi
        angle = g._UP.add(Decimal.from_float(inherited.angle_error_rad), angle_error)
        return gc.ErrorBounds(_upper_float(position), _upper_float(angle), inherited.additional_margin_m)

    def sample(self, elapsed_ns):
        """Generate from the canonical interval, then bound final export errors."""
        distance, speed = self.distance_speed(elapsed_ns)
        p, q = self._enclosed_pose(distance)
        if distance == 0 and speed == self._v0:
            state = self.provenance.start_state
        else:
            state = RigidState(tuple(_midpoint_float(part) for part in p),
                               tuple(_midpoint_float(part) for part in q), float(speed))
        g._vector(state.position_m)
        position_error = _distance_upper(state.position_m, p)
        final_q = _unit(state.orientation_xyzw)  # exact semantics after RigidState normalization
        dot = g._dot(final_q, q)
        if dot.hi < 0:
            final_q = tuple(-part for part in final_q)
        elif dot.lo <= 0:
            raise ValueError('quaternion hemisphere cannot be certified')
        chord = _distance_upper(final_q, q)
        if chord > Decimal(1):
            raise ValueError('quaternion chord outside proved error domain')
        # SO(3) distance = 4 asin(chord/2) <= 3 chord for chord <= 1.
        orientation_error = g._UP.multiply(Decimal(3), chord)
        nominal_axis = _rotate(final_q, _Z_AXIS)
        axis = tuple(_midpoint_float(part) for part in nominal_axis)
        final_axis = _unit(axis)  # same exact-normalization semantics as Capsule
        axis_chord = _distance_upper(final_axis, _rotate(q, _Z_AXIS))
        if axis_chord > Decimal(1):
            raise ValueError('axis chord outside proved error domain')
        # Unit-vector angle = 2 asin(chord/2) <= 2 chord for chord <= 1.
        axis_error = g._UP.multiply(Decimal(2), axis_chord)
        speed_error = _fraction_interval(abs(Fraction(state.speed_m_s)-speed)).hi
        return CertifiedSample(elapsed_ns, distance, speed, state, axis,
                               _upper_float(position_error), _upper_float(orientation_error),
                               _upper_float(axis_error), _upper_float(speed_error),
                               self._errors(distance, position_error, max(orientation_error, axis_error)))

    def _slice_edges(self, duration):
        target_ns = self._ramp_seconds*10**9
        floor = target_ns.numerator//target_ns.denominator
        ceil = -(-target_ns.numerator//target_ns.denominator)
        mandatory = sorted({0, duration, *[v for v in (floor, ceil) if 0 < v < duration]})
        edges = [0]
        for end in mandatory[1:]:
            while edges[-1] < end:
                start = edges[-1]
                s0, _ = self.distance_speed(start)

                def safe(candidate):
                    s1, _ = self.distance_speed(candidate)
                    theta = _upper_float((self._curvature*_fraction_interval(s1-s0)).hi)
                    # Check the exported upper bound, not only its Decimal precursor.
                    return Decimal.from_float(theta) <= gc._MAX_SLICE_ROTATION.lo

                if safe(end):
                    edges.append(end)
                    continue
                low, high = start+1, end
                if not safe(low):
                    raise ValueError('one ns exceeds rotation proof domain')
                while low < high:
                    middle = (low+high+1)//2
                    if safe(middle):
                        low = middle
                    else:
                        high = middle-1
                edges.append(low)
        return edges

    def plan(self, *, start_monotonic_ns, deadline_monotonic_ns, hard_stop):
        """Derive contiguous slices strictly before expiry; no state is applied."""
        for name, value in (('start_monotonic_ns', start_monotonic_ns),
                            ('deadline_monotonic_ns', deadline_monotonic_ns)):
            if type(value) is not int or value < 0:
                raise ValueError(f'{name} must be a nonnegative integer')
        if type(hard_stop) is not bool:
            raise ValueError('hard_stop must be an explicit bool')
        duration = max(0, min(self.provenance.requested_dt_ns,
                              deadline_monotonic_ns-start_monotonic_ns-1))
        if hard_stop:
            duration = 0
        if duration == 0:
            return CertifiedPlan(self.provenance, start_monotonic_ns, deadline_monotonic_ns,
                                 hard_stop, 0, (), self.sample(0), 'HARD_STOP' if hard_stop else 'DEADLINE')
        edges = self._slice_edges(duration)
        endpoints = {time: self.sample(time) for time in edges}
        slices = []
        for a, b in zip(edges, edges[1:]):
            start, end = endpoints[a], endpoints[b]
            length = end.exact_distance_m-start.exact_distance_m
            arc = _fraction_interval(length)
            theta = (self._curvature*arc).hi
            chord = g._norm(tuple(g._exact(x)-g._exact(y)
                                 for x, y in zip(end.state.position_m, start.state.position_m))).hi
            bounds = gc.SliceBounds(end.state.position_m, _upper_float(max(arc.hi, chord)),
                                    _upper_float(self._curvature.hi), _upper_float(theta))
            # Endpoint chord interpolation has <= max(e0,e1) representation
            # error. Curvature handles the true curve; original-start drift
            # uses the furthest complete distance, including previous slices.
            ep = Decimal.from_float(max(start.numerical_position_error_m, end.numerical_position_error_m))
            ea = Decimal.from_float(max(start.numerical_orientation_error_rad, start.numerical_axis_error_rad))
            errors = self._errors(end.exact_distance_m, ep, ea)
            slices.append(CertifiedSlice(start, end, length, _upper_float(arc.hi), bounds, errors))
        return CertifiedPlan(self.provenance, start_monotonic_ns, deadline_monotonic_ns,
                             hard_stop, duration, tuple(slices), endpoints[duration],
                             'FULL_STEP' if duration == self.provenance.requested_dt_ns else 'DEADLINE_CAPPED')

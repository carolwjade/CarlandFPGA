"""Fast sufficient capsule/gate certificates, never motion grants.

This authority-internal module intentionally couples to gate_geometry's
reviewed outward Decimal interval helpers. Neither module is a public ABI.
Explicit error and slice bounds are caller assumptions, not measured facts.
The supplied capsule still requires actual asset/pivot containment validation.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache

from . import gate_geometry as g


_I = g._Interval
_GUARD = Decimal('1e-12')
_MIN_ROTATION_INFLATION = Decimal('.0005')
_ASSUMPTIONS = (
    'Given capsule is the tested envelope; actual asset and pivot containment are unverified here.',
    'Explicit relative position, angular and additional margins bound all relevant poses; their sources are unverified here.',
    'Finite binary64 inputs and exactly normalized axes are enclosed by Decimal60 arithmetic; Godot conversion and query error require separate margins.',
    'This geometric certificate is not a motion grant, gate phase, collision-world query or arrival result.',
)
_SLICE_ASSUMPTIONS = (
    'Arc length bounds the complete continuous centre curve, whose arclength tangent is continuous and curvature is bounded as supplied.',
    'Rotation bounds the entire slice relative to its start, e.g. total angular variation; endpoint net rotation is insufficient.',
    'Endpoint, slice and uncertainty bounds require binding to the actual integrator; no MotionStep or Godot cast is verified here.',
)


def _atan_bounds(denominator, terms=50):
    x = Fraction(1, denominator)
    total = sum(((-1)**k*x**(2*k+1)/(2*k+1) for k in range(terms)), Fraction(0))
    remainder = x**(2*terms+1)/(2*terms+1)
    return (total, total+remainder) if terms % 2 == 0 else (total-remainder, total)


def _pi_interval():
    # Exact rational alternating-series bounds and Machin's identity.
    a, b = _atan_bounds(5), _atan_bounds(239)
    lower, upper = 16*a[0]-4*b[1], 16*a[1]-4*b[0]
    return _I(g._DOWN.divide(Decimal(lower.numerator), Decimal(lower.denominator)),
              g._UP.divide(Decimal(upper.numerator), Decimal(upper.denominator)))


_PI = _pi_interval()
_MAX_SLICE_ROTATION = _PI.divide(_I.exact(Decimal(3600)))


@lru_cache(maxsize=128)
def _cos_limit_upper(angle_budget_upper):
    """Upper cos(5 degrees - budget); only this constant policy is cached."""
    limit = _PI.divide(_I.exact(Decimal(36))) - _I.exact(angle_budget_upper)
    if limit.lo <= 0:
        return None
    # 0 < limit < .09 rad. Nine cosine terms end positive, so the exact
    # polynomial is an upper bound. Every polynomial operation is enclosed.
    squared = limit.square()
    total = term = _I.exact(Decimal(1))
    for k in range(1, 9):
        term = (term*squared).divide(_I.exact(Decimal((2*k-1)*(2*k))))
        total = total-term if k % 2 else total+term
    return total.hi


@dataclass(frozen=True)
class ErrorBounds:
    """Required upper bounds: relative position, full pose angle, other length.

    All are explicit, including zero. additional_margin_m covers separately
    justified asset/transform/numeric allowances, not the rotation floor.
    Domain: position/additional [0,10] m, angle [0,1] rad.
    """
    position_error_m: float
    angle_error_rad: float
    additional_margin_m: float

    def __post_init__(self):
        for name, maximum in (('position_error_m', 10.), ('angle_error_rad', 1.),
                              ('additional_margin_m', 10.)):
            object.__setattr__(self, name, g._scalar(getattr(self, name), maximum, 0.))


@dataclass(frozen=True)
class SliceBounds:
    """Assumed whole-slice bounds, not inferred from endpoint differences.

    Endpoint uses world metres; L is arc length, kappa is curvature magnitude,
    theta bounds the whole rotation path. Domain L/kappa [0,1000], theta [0,1].
    A certificate additionally requires theta <= .05 degrees.
    """
    end_position_m: tuple
    arc_length_upper_m: float
    curvature_upper_per_m: float
    rotation_upper_rad: float

    def __post_init__(self):
        object.__setattr__(self, 'end_position_m', g._vector(self.end_position_m))
        for name, maximum in (('arc_length_upper_m', 1000.), ('curvature_upper_per_m', 1000.),
                              ('rotation_upper_rad', 1.)):
            object.__setattr__(self, name, g._scalar(getattr(self, name), maximum, 0.))


@dataclass(frozen=True)
class CertificateInputs:
    capsule: g.Capsule
    gate: g.Gate
    direction: int
    errors: ErrorBounds
    slice_bounds: SliceBounds | None


@dataclass(frozen=True)
class GateClearance:
    status: str
    radial_upper_m: float | None
    inflation_upper_m: float
    nonempty_proved: bool
    angle_proved: bool
    plane_separated: bool
    reason: str
    inputs: CertificateInputs
    assumptions: tuple
    motion_grant: bool = field(default=False, init=False)


def _inputs(capsule, gate, direction, errors, bounds=None):
    if type(capsule) is not g.Capsule or type(gate) is not g.Gate:
        raise TypeError('exact immutable Capsule and Gate values required')
    if type(errors) is not ErrorBounds:
        raise TypeError('explicit immutable ErrorBounds required')
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError('direction must be integer -1 (inward) or +1 (outward)')
    return CertificateInputs(capsule, gate, direction, errors, bounds)


def _uncertainty(capsule, errors):
    # beta >= position error + 2 Rb sin(angle_error/2) + other margins.
    rb = g._exact(capsule.half_segment_m) + g._exact(capsule.radius_m)
    beta = (g._exact(errors.position_error_m) + rb*g._exact(errors.angle_error_rad)
            + g._exact(errors.additional_margin_m))
    return rb, beta


def _angle_proved(un, direction, angle_budget_upper):
    cosine = _cos_limit_upper(angle_budget_upper)
    oriented = un if direction == 1 else -un
    # A strict sufficient test; equality/rounding ambiguity never clears.
    return cosine is not None and oriented.lo > cosine


def _axis_intersection(offset, normal, unit, s0, un):
    parallel = tuple(x-s0*n for x, n in zip(offset, normal))
    axis_parallel = tuple(a-un*n for a, n in zip(unit, normal))
    ratio = s0.divide(un)
    return tuple(x-ratio*a for x, a in zip(parallel, axis_parallel))


def _result(inputs, status, radial, inflation, nonempty, angle, separated, reason):
    assumptions = _ASSUMPTIONS + (_SLICE_ASSUMPTIONS if inputs.slice_bounds is not None else ())
    return GateClearance(status, None if radial is None else g._float_up(radial),
                         g._float_up(inflation), nonempty, angle, separated,
                         reason, inputs, assumptions)


def section_clearance(capsule, gate, *, direction, errors):
    """Return EMPTY, CLEAR_SECTION or UNKNOWN for one finite capsule section.

    EMPTY means strict separation only. CLEAR_SECTION requires strict robust
    nonempty support, the directed angle gate and strict ellipse containment.
    Invalid inputs raise; UNKNOWN and exceptions must never authorize motion.
    """
    inputs = _inputs(capsule, gate, direction, errors)
    plane = gate.plane
    low, high, s0, un, offset = g._support_intervals(capsule, plane)
    _, beta = _uncertainty(capsule, errors)
    cover = _I.exact(beta.hi)
    separated = ((low-cover).lo > _GUARD or (high+cover).hi < _GUARD.copy_negate())
    if separated:
        return _result(inputs, 'EMPTY', None, beta.hi, False, False, True,
                       'Strict support separation; no phase or arrival inference.')
    nonempty = (g._UP.add(low.hi, beta.hi) < _GUARD.copy_negate()
                and g._DOWN.subtract(high.lo, beta.hi) > _GUARD)
    angle = _angle_proved(un, direction, Decimal.from_float(errors.angle_error_rad))
    absolute = g._abs_bounds(un)
    if not angle or absolute.lo <= 0:
        return _result(inputs, 'UNKNOWN', None, beta.hi, nonempty, angle, False,
                       'Directed angle bound or nonparallel denominator not proved.')
    m = _axis_intersection(offset, plane._unit, capsule._unit, s0, un)
    upper = (g._norm(m)+(g._exact(capsule.radius_m)+cover).divide(absolute)).hi
    fits = g._UP.add(upper, _GUARD) < g._GATE_RADIUS
    status = 'CLEAR_SECTION' if nonempty and fits else 'UNKNOWN'
    reason = ('Strict nonempty section inside enclosing ellipse.' if status == 'CLEAR_SECTION'
              else 'Finite section nonemptiness or strict sufficient radial bound not proved.')
    return _result(inputs, status, upper, beta.hi, nonempty, True, False, reason)


def sweep_clearance(capsule, gate, *, direction, errors, bounds):
    """Return SAFE_IF_INTERSECTING or UNKNOWN for a whole bounded slice.

    Covers a fixed-start-axis capsule translated along the endpoint chord and
    inflated by max(.5mm,Rb*theta)+kappa*L^2/8+explicit uncertainty/margins.
    This is conditional containment at every intersection, never a gate phase.
    All supplied path bounds remain assumptions until an adapter binds them.
    """
    if type(bounds) is not SliceBounds:
        raise TypeError('explicit immutable SliceBounds required')
    inputs = _inputs(capsule, gate, direction, errors, bounds)
    # Exact rationals avoid falsely rejecting a straight path when sqrt's
    # outward upper bound is one Decimal ULP above an exactly equal length.
    chord_squared = sum(((Fraction(x)-Fraction(y))**2
                         for x, y in zip(bounds.end_position_m, capsule.position_m)), Fraction(0))
    if chord_squared > Fraction(bounds.arc_length_upper_m)**2:
        raise ValueError('arc length upper bound is smaller than endpoint chord')
    rb, beta = _uncertainty(capsule, errors)
    theta = g._exact(bounds.rotation_upper_rad)
    length = g._exact(bounds.arc_length_upper_m)
    rotation = max(_MIN_ROTATION_INFLATION, (rb*theta).hi)
    chord = (g._exact(bounds.curvature_upper_per_m)*length.square()).divide(_I.exact(Decimal(8)))
    rho = g._UP.add(g._UP.add(rotation, chord.hi), beta.hi)
    if theta.hi > _MAX_SLICE_ROTATION.lo:
        return _result(inputs, 'UNKNOWN', None, rho, False, False, False,
                       'Whole-slice rotation bound exceeds certified .05 degree limit.')
    plane = gate.plane
    low, high, s0, un, offset = g._support_intervals(capsule, plane)
    end_offset = tuple(g._exact(x)-g._exact(y) for x, y in zip(bounds.end_position_m, plane.point_m))
    end_s = g._dot(end_offset, plane._unit)
    extent = g._exact(capsule.half_segment_m)*g._abs_bounds(un)+g._exact(capsule.radius_m)
    end_low, end_high = end_s-extent, end_s+extent
    separated = (g._DOWN.subtract(min(low.lo, end_low.lo), rho) > _GUARD
                 or g._UP.add(max(high.hi, end_high.hi), rho) < _GUARD.copy_negate())
    angle_budget = g._UP.add(theta.hi, Decimal.from_float(errors.angle_error_rad))
    angle = _angle_proved(un, direction, angle_budget)
    absolute = g._abs_bounds(un)
    if not angle or absolute.lo <= 0:
        return _result(inputs, 'UNKNOWN', None, rho, False, angle, separated,
                       'Whole-slice directed angle or nonparallel denominator not proved.')
    m0 = _axis_intersection(offset, plane._unit, capsule._unit, s0, un)
    m1 = _axis_intersection(end_offset, plane._unit, capsule._unit, end_s, un)
    centres = _I.exact(max(g._norm(m0).hi, g._norm(m1).hi))
    upper = (centres+(g._exact(capsule.radius_m)+_I.exact(rho)).divide(absolute)).hi
    fits = g._UP.add(upper, _GUARD) < g._GATE_RADIUS
    status = 'SAFE_IF_INTERSECTING' if fits else 'UNKNOWN'
    reason = ('Entire inflated chord envelope fits whenever it intersects; no phase inferred.' if fits
              else 'Strict whole-slice sufficient radial bound not proved.')
    return _result(inputs, status, upper, rho, False, True, separated, reason)

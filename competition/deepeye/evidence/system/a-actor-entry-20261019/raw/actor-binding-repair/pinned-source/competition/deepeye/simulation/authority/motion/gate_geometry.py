"""Conservative capsule/plane primitives, not motion authorization or CCD.

Default segment half-length .4 plus radius .12 gives total length 1.04 m.
This candidate contains a .8 m by .24 m flat-ended cylinder; B must still
measure the complete asset and pivot before production integration.

Every arithmetic operation used to establish a bound is outward-rounded in
Decimal precision 60. Inputs mean the exact values of their finite binary64
representation. Direction vectors mean their exact mathematical normalization.
An additional 1 pm separation guard refuses numerically coincident contact.
See docs/authority_gate_geometry.md for the proof and remaining error budgets.
"""
from dataclasses import dataclass, field
from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction
import heapq
import math


_DOWN = Context(prec=60, rounding=ROUND_FLOOR)
_UP = Context(prec=60, rounding=ROUND_CEILING)
_ZERO = Decimal(0)
_ONE = Decimal(1)
_SEPARATION_GUARD = Decimal('1e-12')
_EXPORT_PADDING = Decimal('1e-20')
_GATE_RADIUS = Decimal.from_float(.15)
_FACE_DATA = {
    'top': (1, 15., (0., 1., 0.), '+Y'),
    'bottom': (1, -15., (0., -1., 0.), '-Y'),
    'front': (2, 15., (0., 0., 1.), '+Z'),
    'back': (2, -15., (0., 0., -1.), '-Z'),
    'left': (0, -15., (-1., 0., 0.), '-X'),
    'right': (0, 15., (1., 0., 0.), '+X'),
}


@dataclass(frozen=True)
class _Interval:
    lo: Decimal
    hi: Decimal

    @classmethod
    def exact(cls, value):
        return cls(value, value)

    def __add__(self, other):
        return _Interval(_DOWN.add(self.lo, other.lo), _UP.add(self.hi, other.hi))

    def __neg__(self):
        # Decimal unary minus uses the ambient context. copy_negate is exact.
        return _Interval(self.hi.copy_negate(), self.lo.copy_negate())

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        pairs = ((a, b) for a in (self.lo, self.hi) for b in (other.lo, other.hi))
        values = [( _DOWN.multiply(a,b), _UP.multiply(a,b)) for a,b in pairs]
        return _Interval(min(v[0] for v in values), max(v[1] for v in values))

    def divide(self, other):
        if other.lo <= 0 <= other.hi:
            raise ValueError('division interval includes zero')
        reciprocal = _Interval(_DOWN.divide(_ONE,other.hi),_UP.divide(_ONE,other.lo))
        return self * reciprocal

    def square(self):
        upper=max(_UP.multiply(self.lo,self.lo),_UP.multiply(self.hi,self.hi))
        lower=(_ZERO if self.lo <= 0 <= self.hi else
               min(_DOWN.multiply(self.lo,self.lo),_DOWN.multiply(self.hi,self.hi)))
        return _Interval(lower,upper)

    def sqrt_nonnegative(self):
        """Caller has proved the real expression nonnegative.

        Decimal sqrt is correctly rounded to nearest even, regardless of the
        context's rounding mode. Adjacent precision-60 numbers enclose it.
        Intersecting the input with [0,infinity) is justified by the caller,
        not an unconditional negative-radicand clamp.
        """
        if self.hi < 0:
            raise ValueError('proved nonnegative expression has negative upper bound')
        lower=max(self.lo,_ZERO)
        lo=_ZERO if lower == 0 else _DOWN.next_minus(_DOWN.sqrt(lower))
        hi=_ZERO if self.hi == 0 else _UP.next_plus(_UP.sqrt(self.hi))
        return _Interval(max(lo,_ZERO),hi)


def _exact(value):
    return _Interval.exact(Decimal.from_float(value))


def _scalar(value, maximum=1000., minimum=-1000.):
    if type(value) not in (int,float):
        raise TypeError('geometry numbers must be real int/float, never bool')
    if not minimum <= value <= maximum or not math.isfinite(value):
        raise ValueError('geometry number outside finite bounded domain')
    return float(value)


def _vector(value):
    if not isinstance(value,(tuple,list)) or len(value) != 3:
        raise ValueError('geometry vector must have exactly three components')
    return tuple(_scalar(x) for x in value)


def _norm(vector):
    total=_Interval.exact(_ZERO)
    for part in vector:
        total=total+part.square()
    return total.sqrt_nonnegative()


def _unit(value):
    active=[i for i,x in enumerate(value) if x != 0]
    if not active:
        raise ValueError('direction cannot be zero')
    if len(active)==1:
        i=active[0]
        return tuple(_Interval.exact(Decimal(1 if value[j]>0 else -1)) if j==i
                     else _Interval.exact(_ZERO) for j in range(3))
    vector=tuple(_exact(x) for x in value)
    length=_norm(vector)
    return tuple(x.divide(length) for x in vector)


def _dot(a,b):
    result=_Interval.exact(_ZERO)
    for x,y in zip(a,b):
        result=result+x*y
    return result


def _abs_bounds(value):
    lo=_ZERO if value.lo <= 0 <= value.hi else min(value.lo.copy_abs(),value.hi.copy_abs())
    return _Interval(lo,max(value.lo.copy_abs(),value.hi.copy_abs()))


def _float_down(value, nonnegative=False):
    rounded=math.nextafter(float(_DOWN.subtract(value,_EXPORT_PADDING)),-math.inf)
    return max(0.,rounded) if nonnegative else rounded


def _float_up(value):
    return math.nextafter(float(_UP.add(value,_EXPORT_PADDING)),math.inf)


@dataclass(frozen=True)
class FloatBounds:
    lower: float
    upper: float


@dataclass(frozen=True)
class Plane:
    point_m: tuple
    normal: tuple
    _unit: tuple = field(init=False,repr=False,compare=False)

    def __post_init__(self):
        object.__setattr__(self,'point_m',_vector(self.point_m))
        object.__setattr__(self,'normal',_vector(self.normal))
        object.__setattr__(self,'_unit',_unit(self.normal))


@dataclass(frozen=True)
class Capsule:
    position_m: tuple
    axis: tuple
    half_segment_m: float = .4
    radius_m: float = .12
    _unit: tuple = field(init=False,repr=False,compare=False)

    def __post_init__(self):
        object.__setattr__(self,'position_m',_vector(self.position_m))
        object.__setattr__(self,'axis',_vector(self.axis))
        object.__setattr__(self,'half_segment_m',_scalar(self.half_segment_m,10.,0.))
        object.__setattr__(self,'radius_m',_scalar(self.radius_m,10.,0.))
        if self.radius_m <= 0:
            raise ValueError('capsule radius must be positive')
        object.__setattr__(self,'_unit',_unit(self.axis))

    @property
    def total_length_m(self):
        return 2*(self.half_segment_m+self.radius_m)

    @property
    def pivot_bound_radius_m(self):
        return math.nextafter(self.half_segment_m+self.radius_m,math.inf)

    @property
    def envelope_status(self):
        return 'candidate_requires_asset_containment_measurement'


@dataclass(frozen=True)
class Gate:
    """SceneDocument face/u/v mapping, radius .15 m and cube half-size 15 m."""
    face: str
    u: float
    v: float

    def __post_init__(self):
        if type(self.face) is not str or self.face not in _FACE_DATA:
            raise ValueError('unknown SceneDocument face')
        object.__setattr__(self,'u',_scalar(self.u,14.85,-14.85))
        object.__setattr__(self,'v',_scalar(self.v,14.85,-14.85))

    @property
    def radius_m(self):
        return .15

    @property
    def center_m(self):
        axis,plane,_,_=_FACE_DATA[self.face]
        if axis==0:
            return (plane,self.v,self.u)
        if axis==1:
            return (self.u,plane,self.v)
        return (self.u,self.v,plane)

    @property
    def normal(self):
        return _FACE_DATA[self.face][2]

    @property
    def abi_face(self):
        return _FACE_DATA[self.face][3]

    @property
    def plane(self):
        return Plane(self.center_m,self.normal)


def validate_gate_pair(entry,exit):
    """Geometric editor check only; same face is legal, reachability unproven."""
    if not isinstance(entry,Gate) or not isinstance(exit,Gate):
        raise TypeError('gate pair requires two Gate values')
    if entry.face==exit.face:
        # This small rational comparison is exact for binary64 inputs and
        # permits equal/tangent editor circles, as SceneDocument requires.
        # Drill/ring tangency has a separate fail-closed radial predicate.
        du=Fraction(entry.u)-Fraction(exit.u)
        dv=Fraction(entry.v)-Fraction(exit.v)
        diameter=2*Fraction(.15)
        if du*du+dv*dv < diameter*diameter:
            raise ValueError('same-face gate circles overlap')


@dataclass(frozen=True)
class PlaneSupport:
    minimum: FloatBounds
    maximum: FloatBounds
    entirely_positive: bool
    entirely_negative: bool


def _support_intervals(capsule,plane):
    if not isinstance(capsule,Capsule) or not isinstance(plane,Plane):
        raise TypeError('support requires Capsule and Plane')
    offset=tuple(_exact(x)-_exact(y) for x,y in zip(capsule.position_m,plane.point_m))
    s0=_dot(offset,plane._unit)
    un=_dot(capsule._unit,plane._unit)
    extent=_exact(capsule.half_segment_m)*_abs_bounds(un)+_exact(capsule.radius_m)
    return s0-extent,s0+extent,s0,un,offset


def plane_support(capsule,plane):
    low,high,_,_,_=_support_intervals(capsule,plane)
    return PlaneSupport(FloatBounds(_float_down(low.lo),_float_up(low.hi)),
                        FloatBounds(_float_down(high.lo),_float_up(high.hi)),
                        low.lo>_SEPARATION_GUARD,
                        high.hi<_SEPARATION_GUARD.copy_negate())


@dataclass(frozen=True)
class SectionBounds:
    status: str
    classification: str
    lower_radius_m: float | None
    upper_radius_m: float | None
    interval_evaluations: int
    reason: str


def aperture_radius_bounds(capsule,gate,*,tolerance_m=1e-5,max_intervals=4096):
    """Bound the entire plane section's farthest distance from gate centre.

    Only a bounded, nonempty result with classification='clear' proves this
    *instantaneous section* fits. EMPTY is not entry/arrival. UNKNOWN cannot
    authorize motion. This function supplies neither sweep nor gate phases.
    """
    if not isinstance(gate,Gate):
        raise TypeError('aperture requires a Gate')
    tolerance=_scalar(tolerance_m,1e-4,0.)
    if tolerance<=0:
        raise ValueError('tolerance must be positive')
    if type(max_intervals) is not int or not 1<=max_intervals<=1000000:
        raise ValueError('max_intervals must be an integer in 1..1000000')
    plane=gate.plane
    low,high,s0,un,offset=_support_intervals(capsule,plane)
    if low.lo>_SEPARATION_GUARD or high.hi<_SEPARATION_GUARD.copy_negate():
        return SectionBounds('empty','empty',None,None,0,'strictly separated from plane')
    radius=_exact(capsule.radius_m)
    radius_sq=radius.square()
    half=Decimal.from_float(capsule.half_segment_m)
    left,right=half.copy_negate(),half
    # Outer feasible interval: division is only legal if the denominator's
    # interval excludes zero. If it includes zero, retain the full segment.
    if not un.lo<=0<=un.hi:
        feasible=(_Interval(radius.lo.copy_negate(),radius.hi)-s0).divide(un)
        left=max(left,feasible.lo)
        right=min(right,feasible.hi)
    if left>right:
        # The support was within the 1pm contact guard; do not contradict it
        # by classifying a microscopic positive gap as certified empty.
        return SectionBounds('unknown','unknown',None,None,0,'near plane contact; feasible section unresolved')
    parallel=tuple(x-s0*n for x,n in zip(offset,plane._unit))
    axis_parallel=tuple(a-un*n for a,n in zip(capsule._unit,plane._unit))

    def norm_at(t):
        point=_Interval.exact(t)
        return _norm(tuple(c+point*b for c,b in zip(parallel,axis_parallel)))

    def witness(t):
        d=s0+_Interval.exact(t)*un
        if max(d.lo.copy_abs(),d.hi.copy_abs())>radius.lo:
            return None
        # True d(t)^2 <= r^2 proved above. Its rounded lower radicand may
        # extend below zero, so intersecting with nonnegative values is safe.
        radial=(radius_sq-d.square()).sqrt_nonnegative()
        return _DOWN.add(norm_at(t).lo,radial.lo)

    def bound(a,b):
        d=s0+_Interval(a,b)*un
        min_abs=_abs_bounds(d).lo
        if min_abs>radius.hi:
            return None,None
        rad_upper=_UP.subtract(radius_sq.hi,_DOWN.multiply(min_abs,min_abs))
        if rad_upper<0:
            # No guessed clamp; inconsistency means this interval is unresolved.
            return None,Decimal('Infinity')
        disk_upper=_Interval(_ZERO,rad_upper).sqrt_nonnegative().hi
        upper=_UP.add(max(norm_at(a).hi,norm_at(b).hi),disk_upper)
        mid=_DOWN.divide(_DOWN.add(a,b),Decimal(2))
        samples=[witness(t) for t in (a,mid,b)]
        valid=[sample for sample in samples if sample is not None]
        return max(valid) if valid else None,upper

    lower,upper=bound(left,right)
    evaluations=1
    if upper is None or not upper.is_finite():
        return SectionBounds('unknown','unknown',None,None,evaluations,'section interval unresolved')
    best=lower if lower is not None else _ZERO
    has_witness=lower is not None
    queue=[(upper.copy_negate(),left,right)]
    status='bounded'
    reason='certified finite nonempty section radius bounds'
    while queue:
        global_upper=max(best,queue[0][0].copy_negate())
        # Include export conversion/padding in the caller-visible gap.
        export_lower=_float_down(best,True)
        export_upper=_float_up(global_upper)
        exported_gap=_UP.subtract(Decimal.from_float(export_upper),Decimal.from_float(export_lower))
        if has_witness and exported_gap<=Decimal.from_float(tolerance):
            break
        if evaluations+2>max_intervals:
            status,reason='unknown','interval budget exhausted'
            break
        _,a,b=heapq.heappop(queue)
        mid=_DOWN.divide(_DOWN.add(a,b),Decimal(2))
        if not a<mid<b:
            # Keep the popped interval in the bound on failure.
            heapq.heappush(queue,(global_upper.copy_negate(),a,b))
            status,reason='unknown','parameter resolution exhausted or section existence unresolved'
            break
        for c,d in ((a,mid),(mid,b)):
            lb,ub=bound(c,d)
            evaluations+=1
            if ub is None:
                continue
            if not ub.is_finite():
                return SectionBounds('unknown','unknown',None,None,evaluations,'section interval unresolved')
            if lb is not None:
                best=max(best,lb)
                has_witness=True
            heapq.heappush(queue,(ub.copy_negate(),c,d))
        if not queue:
            return SectionBounds('unknown','unknown',None,None,evaluations,'section existence unresolved')
    upper=max(best,queue[0][0].copy_negate())
    if not has_witness:
        status,reason='unknown','section existence unresolved'
    # A bound can be precise while still straddling contact. The 1pm guard is
    # separately reported in docs; it is never silently used to expand a hole.
    if status!='bounded':
        classification='unknown'
    elif _UP.add(upper,_SEPARATION_GUARD)<_GATE_RADIUS:
        classification='clear'
    elif best>=_GATE_RADIUS:
        classification='contact_or_outside'
    else:
        classification='unknown'
        reason='radial clearance cannot be strictly separated from contact'
    return SectionBounds(status,classification,_float_down(best,True),_float_up(upper),evaluations,reason)

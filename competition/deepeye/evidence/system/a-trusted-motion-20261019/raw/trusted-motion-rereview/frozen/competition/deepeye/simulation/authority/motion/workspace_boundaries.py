"""Private six-face continuous certificates derived only from CanonicalPath.

Conditional numerical evidence, not a runtime owner/scene registry or motion
grant. Existing capsule/interval/gate helpers are deliberately internal APIs.
"""
from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from fractions import Fraction
import hashlib
import json

from . import certified_path as cp
from . import gate_geometry as g
from . import gate_clearance as gc

VERSION='workspace-canonical-six-face-preview-v1'
_I=g._Interval
_GUARD=Decimal('1e-12')
_COS5_LOWER=Decimal('.99595')  # cos5deg > 1-.09²/2
FACES=tuple(g._FACE_DATA)


def _label(value):
    if type(value) is not str or not value.strip() or len(value)>4096:
        raise ValueError('explicit nonempty bounded reference required')


def _canonical(value):
    if isinstance(value,(Decimal,Fraction)):return str(value)
    if is_dataclass(value):
        return {f.name:_canonical(getattr(value,f.name)) for f in fields(value) if f.init}
    if type(value) in (tuple,list):return [_canonical(x) for x in value]
    if type(value) is dict:return {k:_canonical(v) for k,v in value.items()}
    return value


def digest(value):
    data=json.dumps([VERSION,_canonical(value)],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(data).hexdigest()


def _create(cls,**values):
    result=object.__new__(cls)
    for name,value in values.items():object.__setattr__(result,name,value)
    return result


@dataclass(frozen=True)
class Envelope:
    half_segment_m: float
    radius_m: float
    pivot_radius_m: float
    reference: str
    exact_fixture: bool

    def __post_init__(self):
        _label(self.reference)
        for name,minimum in (('half_segment_m',0.),('radius_m',0.),('pivot_radius_m',0.)):
            object.__setattr__(self,name,g._scalar(getattr(self,name),1000.,minimum))
        if self.radius_m<=0 or Fraction(self.pivot_radius_m)<Fraction(self.half_segment_m)+Fraction(self.radius_m):
            raise ValueError('positive capsule and covering pivot bound required')
        if type(self.exact_fixture) is not bool:raise TypeError('explicit fixture semantics required')


@dataclass(frozen=True)
class Layout:
    blue: g.Gate
    red: g.Gate

    def __post_init__(self):
        if type(self.blue) is not g.Gate or type(self.red) is not g.Gate:
            raise TypeError('exact immutable gates required')
        g.validate_gate_pair(self.blue,self.red)
        for gate in (self.blue,self.red):
            if any(abs(Fraction(x))+Fraction(gate.radius_m)>15 for x in (gate.u,gate.v)):
                raise ValueError('gate crosses face edge; no UI tolerance expansion')


@dataclass(frozen=True,init=False)
class PreparedPath:
    path: cp.CanonicalPath
    plan: cp.CertifiedPlan
    layout: Layout
    envelope: Envelope
    binding: str


def prepare(path,layout,envelope,*,start_monotonic_ns,deadline_monotonic_ns,hard_stop):
    if type(path) is not cp.CanonicalPath or type(layout) is not Layout or type(envelope) is not Envelope:
        raise TypeError('canonical path and immutable layout/envelope required, never external slices')
    plan=path.plan(start_monotonic_ns=start_monotonic_ns,deadline_monotonic_ns=deadline_monotonic_ns,hard_stop=hard_stop)
    binding=digest((path.provenance,start_monotonic_ns,deadline_monotonic_ns,hard_stop,plan.covered_ns,layout,envelope))
    return _create(PreparedPath,path=path,plan=plan,layout=layout,envelope=envelope,binding=binding)


def _capsule(sample,envelope):
    return g.Capsule(sample.state.position_m,sample.axis,envelope.half_segment_m,envelope.radius_m)


def _uncertainty(errors,envelope):
    return (g._exact(errors.position_error_m)+g._exact(envelope.pivot_radius_m)*g._exact(errors.angle_error_rad)
            +g._exact(errors.additional_margin_m)).hi


@dataclass(frozen=True)
class Side:
    face: str
    minimum_lower: Decimal
    minimum_upper: Decimal
    maximum_lower: Decimal
    maximum_upper: Decimal

    @property
    def inside(self):return self.maximum_upper<_GUARD.copy_negate()

    @property
    def outside(self):return self.minimum_lower>_GUARD


def point_sides(sample,envelope):
    if type(sample) is not cp.CertifiedSample or type(envelope) is not Envelope:
        raise TypeError('canonical sample and envelope required')
    capsule=_capsule(sample,envelope);eps=_uncertainty(sample.errors,envelope)
    sides=[]
    for face in FACES:
        axis,_,normal,_=g._FACE_DATA[face]
        centre=g._exact(normal[axis]*sample.state.position_m[axis])-_I.exact(Decimal(15))
        extent=g._exact(envelope.half_segment_m)*g._abs_bounds(capsule._unit[axis])+g._exact(envelope.radius_m)
        low,high=centre-extent,centre+extent
        sides.append(Side(face,g._DOWN.subtract(low.lo,eps),g._UP.add(low.hi,eps),
                          g._DOWN.subtract(high.lo,eps),g._UP.add(high.hi,eps)))
    return tuple(sides)


def _inflation(record,envelope):
    e=record.errors;b=record.gate_bounds
    rb=g._exact(envelope.pivot_radius_m)
    nominal=g._exact(envelope.half_segment_m)+g._exact(envelope.radius_m)
    theta=g._exact(b.rotation_upper_rad);angle=g._exact(e.angle_error_rad)
    rotation=max(Decimal('.0005'),(rb*theta).hi)
    old_rotation=max(Decimal('.0005'),(nominal*theta).hi)
    deficit=g._UP.add(g._UP.subtract(rotation,old_rotation),((rb-nominal)*angle).hi)
    # gate_clearance uses h+r; lift its explicit margin to the caller's larger Rb.
    adjusted=gc.ErrorBounds(e.position_error_m,e.angle_error_rad,
        cp._upper_float(g._UP.add(Decimal.from_float(e.additional_margin_m),max(Decimal(0),deficit))))
    arc=(g._exact(b.curvature_upper_per_m)*g._exact(b.arc_length_upper_m).square()).divide(_I.exact(Decimal(8))).hi
    desired=g._UP.add(g._UP.add(rotation,arc),_uncertainty(e,envelope))
    actual=g._UP.add(g._UP.add(old_rotation,arc),gc._uncertainty(_capsule(record.start,envelope),adjusted)[1].hi)
    return max(desired,actual),adjusted


@dataclass(frozen=True)
class FaceProof:
    face: str
    method: str
    lower: Decimal
    upper: Decimal
    gate_certificate: gc.GateClearance | None


@dataclass(frozen=True)
class SliceProof:
    status: str
    binding: str
    role: str
    start_sides: tuple
    end_sides: tuple
    faces: tuple
    rho_m: float
    monotone_at_gate: bool
    reason: str
    motion_grant: bool = field(default=False,init=False)


def _rim_witness(sample,envelope,gate):
    # Narrow exact analytic fixture witness, never inferred from an outer model.
    if not envelope.exact_fixture or any((sample.errors.position_error_m,sample.errors.angle_error_rad,sample.errors.additional_margin_m)):
        return False
    axis,_,normal,_=g._FACE_DATA[gate.face]
    if any(sample.axis[j] for j in range(3) if j!=axis):return False
    delta=tuple(Fraction(x)-Fraction(y) for x,y in zip(sample.state.position_m,gate.center_m))
    if abs(delta[axis])>Fraction(envelope.half_segment_m):return False
    radius=Fraction(envelope.radius_m);gate_radius=Fraction(gate.radius_m)
    return radius>=gate_radius or sum(delta[j]**2 for j in range(3) if j!=axis)>=(gate_radius-radius)**2


def check_slice(prepared,index,role,*,max_gate_checks=1):
    if type(prepared) is not PreparedPath:raise TypeError('internally prepared canonical path required')
    if type(index) is not int or not 0<=index<len(prepared.plan.slices):raise ValueError('valid derived slice index required')
    if type(role) is not str or role not in ('entry','exit'):raise ValueError('exactly one entry/exit role required')
    if type(max_gate_checks) is not int or max_gate_checks<0:raise ValueError('nonnegative aperture work budget required')
    record=prepared.plan.slices[index];envelope=prepared.envelope
    gate=prepared.layout.blue if role=='entry' else prepared.layout.red
    rho,adjusted=_inflation(record,envelope)
    capsule=_capsule(record.start,envelope)
    start_sides=point_sides(record.start,envelope);end_sides=point_sides(record.end,envelope)
    faces=[];unknown=False;violation=False;monotone=True
    for face in FACES:
        axis,_,normal,_=g._FACE_DATA[face];sign=normal[axis]
        centres=tuple(g._exact(sign*sample.state.position_m[axis])-_I.exact(Decimal(15)) for sample in (record.start,record.end))
        extent=g._exact(envelope.half_segment_m)*g._abs_bounds(capsule._unit[axis])+g._exact(envelope.radius_m)
        lower=g._DOWN.subtract(min((c-extent).lo for c in centres),rho)
        upper=g._UP.add(max((c+extent).hi for c in centres),rho)
        cert=None
        if upper<_GUARD.copy_negate():method='STRICT_INSIDE'
        elif face==gate.face and lower>_GUARD:method='STRICT_OUTSIDE_ACTIVE'
        elif face!=gate.face:
            method='ENVELOPE_NOT_CLEAR';unknown=True
            if envelope.exact_fixture and any(s.maximum_lower>_GUARD for s in (*start_sides,*end_sides) if s.face==face):
                method='EXACT_FIXTURE_WALL_WITNESS';violation=True
        else:
            method='APERTURE_UNKNOWN';unknown=True
            if any(_rim_witness(sample,envelope,gate) for sample in (record.start,record.end)):
                method='EXACT_FIXTURE_RIM_WITNESS';violation=True
            elif max_gate_checks:
                cert=gc.sweep_clearance(capsule,gate,direction=-1 if role=='entry' else 1,
                    errors=adjusted,bounds=record.gate_bounds)
                # Same canonical motion, not arbitrary jitter between side bounds.
                monotone=g._DOWN.subtract(_COS5_LOWER,(g._exact(envelope.pivot_radius_m)*g._exact(record.gate_bounds.curvature_upper_per_m)).hi)>0
                if cert.status=='SAFE_IF_INTERSECTING' and monotone:
                    method='APERTURE';unknown=False if not any(f.method in ('ENVELOPE_NOT_CLEAR','APERTURE_UNKNOWN') for f in faces) else unknown
        faces.append(FaceProof(face,method,lower,upper,cert))
    # Recompute from every face; a later good face cannot erase an earlier failure.
    unknown=any(f.method in ('ENVELOPE_NOT_CLEAR','APERTURE_UNKNOWN') for f in faces)
    status='VIOLATION_PROVED' if violation else 'UNKNOWN' if unknown else 'SAFE'
    binding=digest((prepared.binding,index,role,tuple(faces),start_sides,end_sides))
    return SliceProof(status,binding,role,start_sides,end_sides,tuple(faces),cp._upper_float(rho),monotone,
        'complete continuous six-face conjunction' if status=='SAFE' else 'exact fixture witness' if violation else 'insufficient envelope/aperture/budget evidence')

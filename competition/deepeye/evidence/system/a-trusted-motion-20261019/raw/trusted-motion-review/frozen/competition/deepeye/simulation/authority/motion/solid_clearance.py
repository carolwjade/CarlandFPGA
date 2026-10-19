"""Authority-internal sufficient solid separation; never a motion grant.

Exact encoded models are mathematical inputs, not verified B mesh imports.
Whole-path and error bounds are explicit caller assumptions. See the companion
authority_solid_clearance.md for containment, completeness and integration gates.
"""
from dataclasses import dataclass, field, fields, is_dataclass
from fractions import Fraction as F
import hashlib
import itertools
import json
import math

KERNEL_VERSION = 'solid-clearance-v1'
_MATERIALS = {'casing': 5, 'fault': 4, 'void': 3, 'hard_rock': 2, 'water': 1}


def _scalar(value):
    if type(value) not in (int, float, str, F) or type(value) is bool:
        raise TypeError('finite exact encoded scalar required')
    try:
        result = F(value)
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError('nonfinite or invalid scalar') from exc
    if max(result.numerator.bit_length(), result.denominator.bit_length()) > 4096:
        raise ValueError('encoded scalar exceeds arithmetic resource limit')
    return result


def _vector(value, size=3):
    if type(value) not in (tuple, list) or len(value) != size:
        raise ValueError('fixed-size encoded vector required')
    return tuple(_scalar(x) for x in value)


def _label(value):
    if type(value) is not str or not value.strip():
        raise ValueError('nonempty identity/version/source required')


def _dot(a, b):
    return sum((x*y for x, y in zip(a, b)), F(0))


def _canonical(value):
    if isinstance(value, F):
        return [value.numerator, value.denominator]
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value) if f.init}
    if type(value) in (tuple, list):
        return [_canonical(x) for x in value]
    if type(value) is dict:
        return {k: _canonical(v) for k, v in value.items()}
    return value


def _digest(value):
    data = json.dumps([KERNEL_VERSION, _canonical(value)], sort_keys=True,
                      separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def _seal(obj):
    object.__setattr__(obj, 'digest', _digest(obj))


def _sqrt_up(value):
    # floor(sqrt(value)*2^96) from integer isqrt; exact or one grid step up.
    scale = 1 << 96
    low = math.isqrt((value.numerator*scale*scale)//value.denominator)
    exact = low*low*value.denominator == value.numerator*scale*scale
    return F(low if exact else low+1, scale)


def _rotation(q):
    x, y, z, w = q
    d = _dot(q, q)
    if not d:
        raise ValueError('zero quaternion')
    return ((1-2*(y*y+z*z)/d, 2*(x*y-z*w)/d, 2*(x*z+y*w)/d),
            (2*(x*y+z*w)/d, 1-2*(x*x+z*z)/d, 2*(y*z-x*w)/d),
            (2*(x*z-y*w)/d, 2*(y*z+x*w)/d, 1-2*(x*x+y*y)/d))


@dataclass(frozen=True)
class ErrorBounds:
    position: F
    pose_angle: F
    numeric: F
    asset: F
    obstacle: F
    source: str

    def __post_init__(self):
        _label(self.source)
        for name in ('position', 'pose_angle', 'numeric', 'asset', 'obstacle'):
            value = _scalar(getattr(self, name))
            if value < 0:
                raise ValueError('errors must be nonnegative explicit upper bounds')
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class CapsuleModel:
    model_id: str
    version: str
    half_segment: F
    radius: F
    pivot_radius: F

    def __post_init__(self):
        _label(self.model_id); _label(self.version)
        for name in ('half_segment', 'radius', 'pivot_radius'):
            object.__setattr__(self, name, _scalar(getattr(self, name)))
        if self.half_segment < 0 or self.radius <= 0 or self.pivot_radius < self.half_segment+self.radius:
            raise ValueError('positive capsule with covering central-pivot radius required')


@dataclass(frozen=True)
class Inflation:
    rotation: F
    arc: F
    position: F
    pose: F
    numeric: F
    asset: F
    obstacle: F

    @property
    def total(self):
        return sum((getattr(self, f.name) for f in fields(self)), F(0))


@dataclass(frozen=True)
class Sweep:
    model: CapsuleModel
    start: tuple
    end: tuple
    quaternion: tuple
    arc_length: F
    curvature: F
    rotation: F
    errors: ErrorBounds
    budget: Inflation = field(init=False)
    axis: tuple = field(init=False, repr=False)
    digest: str = field(init=False)

    def __post_init__(self):
        if type(self.model) is not CapsuleModel or type(self.errors) is not ErrorBounds:
            raise TypeError('exact immutable model and explicit errors required')
        for name in ('start', 'end'):
            object.__setattr__(self, name, _vector(getattr(self, name)))
        object.__setattr__(self, 'quaternion', _vector(self.quaternion, 4))
        matrix = _rotation(self.quaternion)
        object.__setattr__(self, 'axis', tuple(row[2] for row in matrix))
        for name in ('arc_length', 'curvature', 'rotation'):
            value = _scalar(getattr(self, name))
            if value < 0:
                raise ValueError('nonnegative whole-interval path bounds required')
            object.__setattr__(self, name, value)
        chord = tuple(b-a for a, b in zip(self.start, self.end))
        if _dot(chord, chord) > self.arc_length**2:
            raise ValueError('arc length bound shorter than endpoint chord')
        e, rb = self.errors, self.model.pivot_radius
        object.__setattr__(self, 'budget', Inflation(max(F(1,2000), rb*self.rotation),
            self.curvature*self.arc_length**2/8, e.position, rb*e.pose_angle,
            e.numeric, e.asset, e.obstacle))
        _seal(self)

    def radius(self, stage):
        if type(stage) is not str or stage not in ('initial', 'full'):
            raise ValueError('initial or full stage required')
        margin = self.budget.total
        if stage == 'initial':
            margin -= self.budget.rotation+self.budget.arc
        return self.model.radius+margin

    def endpoints(self, stage):
        self.radius(stage)
        return tuple(tuple(x+sign*self.model.half_segment*u for x, u in zip(p, self.axis))
                     for p in ((self.start,) if stage == 'initial' else (self.start,self.end))
                     for sign in (-1,1))


@dataclass(frozen=True)
class Solid:
    model_id: str
    version: str
    kind: str
    centre: tuple
    dimensions: tuple
    quaternion: tuple
    vertices: tuple = ()
    matrix: tuple = field(init=False, repr=False)
    digest: str = field(init=False)

    def __post_init__(self):
        _label(self.model_id); _label(self.version)
        if type(self.kind) is not str or self.kind not in ('box', 'ellipsoid', 'cylinder', 'polytope'):
            raise ValueError('unsupported solid: reject whole scene, never skip')
        for name in ('centre', 'dimensions'):
            object.__setattr__(self, name, _vector(getattr(self, name)))
        if min(self.dimensions) <= 0:
            raise ValueError('positive local half sizes/semiaxes/scales required')
        object.__setattr__(self, 'quaternion', _vector(self.quaternion, 4))
        object.__setattr__(self, 'matrix', _rotation(self.quaternion))
        object.__setattr__(self, 'vertices', tuple(_vector(v) for v in self.vertices))
        if self.kind == 'polytope':
            # Full rank, linear work in number of vertices; no arbitrary vertex cap.
            base = self.vertices[0] if self.vertices else (0,0,0)
            edges = [tuple(x-y for x,y in zip(v,base)) for v in self.vertices]
            a = next((v for v in edges if any(v)), None)
            cross = lambda u,v:(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            n = next((cross(a,v) for v in edges if a and any(cross(a,v))), None)
            if n is None or not any(_dot(n,v) for v in edges):
                raise ValueError('polytope must have closed full-dimensional convex hull')
        elif self.vertices:
            raise ValueError('vertices belong only to polytope')
        _seal(self)


def support_upper(solid, normal):
    if type(solid) is not Solid:
        raise TypeError('immutable Solid required')
    n = _vector(normal)
    local = tuple(sum(row[j]*x for row,x in zip(solid.matrix,n)) for j in range(3))
    scaled = tuple(d*x for d,x in zip(solid.dimensions,local))
    if solid.kind == 'box':
        extent = sum(map(abs,scaled))
    elif solid.kind == 'ellipsoid':
        extent = _sqrt_up(_dot(scaled,scaled))
    elif solid.kind == 'cylinder':
        extent = _sqrt_up(scaled[0]**2+scaled[1]**2)+abs(scaled[2])
    else:
        extent = max(_dot(v,scaled) for v in solid.vertices)
    return _dot(solid.centre,n)+extent


@dataclass(frozen=True)
class PlaneCertificate:
    binding: str
    normal: tuple
    sweep_upper: F
    obstacle_lower: F
    gap: F
    stage: str
    context: str
    kernel_version: str = field(default=KERNEL_VERSION, init=False)
    motion_grant: bool = field(default=False, init=False)


def check_plane(sweep, solid, normal, *, stage='full', context=''):
    if type(sweep) is not Sweep or type(solid) is not Solid or type(context) is not str:
        raise TypeError('immutable sweep/solid and context required')
    sweep.radius(stage)
    try:
        n = _vector(normal)
    except (TypeError, ValueError):
        return None
    if not any(n):
        return None
    upper = max(_dot(p,n) for p in sweep.endpoints(stage))+sweep.radius(stage)*_sqrt_up(_dot(n,n))
    lower = -support_upper(solid,tuple(-x for x in n))
    gap = lower-upper
    if gap <= 0:
        return None
    binding = _digest((sweep.digest,solid.digest,stage,context,n))
    return PlaneCertificate(binding,n,upper,lower,gap,stage,context)


def recheck_certificate(certificate, sweep, solid, *, stage='full', context=''):
    return (type(certificate) is PlaneCertificate and
            certificate == check_plane(sweep,solid,certificate.normal,stage=stage,context=context))


@dataclass(frozen=True)
class Limits:
    max_normals: int = 64
    proposal_iterations: int = 24
    max_pairs: int = 2048
    max_support_terms: int = 200000

    def __post_init__(self):
        if any(type(getattr(self,f.name)) is not int or getattr(self,f.name)<0 for f in fields(self)):
            raise ValueError('nonnegative integer work limits required')


@dataclass(frozen=True)
class PairResult:
    status: str
    stage: str
    tried: int
    certificate: PlaneCertificate | None
    reason: str
    motion_grant: bool = field(default=False, init=False)


def _support_cost(solid):
    return 4+(len(solid.vertices) if solid.kind == 'polytope' else 3)


def _closest_simplex(points):
    """Untrusted float proposal: at most30 subsets, linear systems at most5x5."""
    best = None
    for size in range(1,min(4,len(points))+1):
        for subset in itertools.combinations(points,size):
            # Minimise |sum(w_i*p_i)|² with sum(w_i)=1 on each face.
            a = [[sum(x*y for x,y in zip(p,q)) for q in subset]+[1.,0.] for p in subset]
            a.append([1.]*size+[0.,1.])
            for col in range(size+1):
                pivot = max(range(col,size+1),key=lambda row:abs(a[row][col]))
                if abs(a[pivot][col])<1e-20:
                    break
                a[col],a[pivot] = a[pivot],a[col]
                scale = a[col][col]; a[col] = [v/scale for v in a[col]]
                for row in range(size+1):
                    if row != col:
                        scale = a[row][col]
                        a[row] = [x-scale*y for x,y in zip(a[row],a[col])]
            else:
                weights = [row[-1] for row in a[:-1]]
                if min(weights)<-1e-9 or not all(math.isfinite(x) for x in weights):
                    continue
                weights = [max(0.,w) for w in weights]; total = sum(weights)
                if not total:
                    continue
                weights = [w/total for w in weights]
                v = tuple(sum(w*p[i] for w,p in zip(weights,subset)) for i in range(3))
                square = sum(x*x for x in v)
                if best is None or square<best[0]:
                    best = (square,v,[p for p,w in zip(subset,weights) if w>1e-10])
    return None if best is None else best[1:]


def _proposals(sweep, solid, stage, cached, iterations):
    # Directions only: even cheap broadphase axes require a fresh exact check.
    yield from cached
    yield from ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
    centre = tuple((a+b)/2 for a,b in zip(sweep.start,sweep.start if stage=='initial' else sweep.end))
    delta = tuple(b-a for a,b in zip(centre,solid.centre))
    yield delta
    for j in range(3):
        axis = tuple(row[j] for row in solid.matrix)
        yield axis
        yield tuple(-x for x in axis)
    # Bounded GJK nearest-simplex proposals on Minkowski A-B.
    # Float supports need not enclose; only check_plane can issue a certificate.
    try:
        points = [tuple(map(float,p)) for p in sweep.endpoints(stage)]
        matrix = [tuple(map(float,row)) for row in solid.matrix]
        dims = tuple(map(float,solid.dimensions)); c = tuple(map(float,solid.centre))
        radius = float(sweep.radius(stage))
        def obstacle(n):
            local = tuple(sum(row[j]*x for row,x in zip(matrix,n)) for j in range(3))
            dn = tuple(d*x for d,x in zip(dims,local))
            if solid.kind == 'box':
                v = tuple(d if x>=0 else -d for d,x in zip(dims,local))
            elif solid.kind in ('ellipsoid','cylinder'):
                count = 3 if solid.kind=='ellipsoid' else 2
                length = math.hypot(*dn[:count])
                v = tuple(d*dn[i]/length if length else 0. for i,d in enumerate(dims[:count]))
                if count == 2:
                    v += (dims[2] if local[2]>=0 else -dims[2],)
            else:
                chosen = max(solid.vertices,key=lambda p:sum(float(x)*n for x,n in zip(p,dn)))
                v = tuple(float(x)*d for x,d in zip(chosen,dims))
            return tuple(x+sum(a*b for a,b in zip(row,v)) for x,row in zip(c,matrix))
        def minkowski(n):
            length = math.hypot(*n)
            p = max(points,key=lambda p:sum(a*b for a,b in zip(p,n)))
            b = obstacle(tuple(-x for x in n))
            return tuple(a+radius*x/length-y for a,x,y in zip(p,n,b))
        w = tuple(-float(x) for x in delta)
        if not any(w):
            w = (1.,0.,0.)
        simplex = []
        for _ in range(iterations):
            n = tuple(-x for x in w)
            if not all(math.isfinite(x) for x in n) or not any(n):
                break
            yield n
            v = minkowski(n)
            if v in simplex:
                break
            simplex.append(v)
            nearest = _closest_simplex(simplex)
            if nearest is None:
                break
            w,simplex = nearest
    except (OverflowError, ValueError, ZeroDivisionError):
        return
    yield from itertools.product((-1,0,1),repeat=3)


def separate(sweep, solid, *, stage='full', context='', limits=Limits(), cached_normals=()):
    if type(sweep) is not Sweep or type(solid) is not Solid or type(limits) is not Limits:
        raise TypeError('immutable geometry and work limits required')
    if type(cached_normals) is not tuple:
        raise TypeError('bounded tuple of cached directions required')
    sweep.radius(stage)
    if (limits.max_normals+limits.proposal_iterations)*_support_cost(solid)>limits.max_support_terms:
        return PairResult('UNKNOWN',stage,0,None,'support work budget insufficient')
    seen = set(); tried = 0
    for normal in _proposals(sweep,solid,stage,cached_normals[:limits.max_normals],limits.proposal_iterations):
        if tried >= limits.max_normals:
            break
        try:
            n = _vector(normal)
        except (TypeError, ValueError):
            continue
        if not any(n) or n in seen:
            continue
        seen.add(n); tried += 1
        cert = check_plane(sweep,solid,n,stage=stage,context=context)
        if cert is not None:
            return PairResult('CLEAR',stage,tried,cert,'strict exact/outward support gap')
    return PairResult('UNKNOWN',stage,tried,None,'no strict certificate; not a proved contact')


@dataclass(frozen=True)
class SceneObject:
    object_id: str
    material: str
    parts: tuple
    superhard: bool = False

    def __post_init__(self):
        _label(self.object_id)
        object.__setattr__(self, 'parts', tuple(self.parts))
        if (type(self.material) is not str or self.material not in _MATERIALS
                or type(self.superhard) is not bool):
            raise ValueError('known material policy required')
        if not self.parts or any(type(p) is not Solid for p in self.parts):
            raise TypeError('nonempty immutable convex pieces required; no omissions')
        if len({p.model_id for p in self.parts}) != len(self.parts):
            raise ValueError('duplicate piece ID')
        if self.superhard and self.material != 'hard_rock':
            raise ValueError('superhard is a rock subtype')


@dataclass(frozen=True)
class Scene:
    scene_id: str
    version: str
    manifest: tuple
    objects: tuple
    digest: str = field(init=False)

    def __post_init__(self):
        _label(self.scene_id); _label(self.version)
        object.__setattr__(self, 'manifest', tuple((oid,tuple(ids)) for oid,ids in self.manifest))
        object.__setattr__(self, 'objects', tuple(self.objects))
        expected = {}
        for oid,ids in self.manifest:
            _label(oid)
            for pid in ids:
                _label(pid)
            if oid in expected or not ids or len(set(ids)) != len(ids):
                raise ValueError('invalid independent object/piece manifest')
            expected[oid] = set(ids)
        actual = {}
        for obj in self.objects:
            if type(obj) is not SceneObject:
                raise TypeError('complete immutable SceneObject values required')
            if obj.object_id in actual:
                raise ValueError('duplicate object ID')
            actual[obj.object_id] = {p.model_id for p in obj.parts}
        if expected != actual:
            raise ValueError('missing or unexpected object/piece: whole scene rejected')
        _seal(self)


@dataclass(frozen=True)
class SceneResult:
    status: str
    binding: str
    pairs: tuple
    reason: str
    motion_grant: bool = field(default=False, init=False)


def certify_scene(sweep, scene, *, limits=Limits()):
    if type(sweep) is not Sweep or type(scene) is not Scene or type(limits) is not Limits:
        raise TypeError('complete immutable scene, sweep and work limits required')
    binding = _digest((sweep.digest,scene.digest))
    parts = [p for obj in scene.objects for p in obj.parts]
    work = 2*sum(_support_cost(p)*(limits.max_normals+limits.proposal_iterations) for p in parts)
    if 2*len(parts)>limits.max_pairs or work>limits.max_support_terms:
        return SceneResult('UNKNOWN',binding,(),'whole scene exceeds work budget; no object dropped')
    pairs = []; drilling = False
    ordered = sorted(scene.objects,key=lambda o:(o.material=='hard_rock' and not o.superhard,-_MATERIALS[o.material],o.object_id))
    for obj in ordered:
        drillable = obj.material=='hard_rock' and not obj.superhard
        for stage in ('initial','full'):
            for part in obj.parts:
                result = separate(sweep,part,stage=stage,context=scene.digest,limits=limits)
                pairs.append(result)
                if result.status != 'CLEAR':
                    if not drillable:
                        return SceneResult('UNKNOWN',binding,tuple(pairs),'forbidden union lacks clearance; no proved-contact claim')
                    drilling = True
    return SceneResult('DRILLING_REQUIRED' if drilling else 'CLEAR',binding,tuple(pairs),
        'independent drilling law required' if drilling else 'every declared piece clear at initial and full interval')

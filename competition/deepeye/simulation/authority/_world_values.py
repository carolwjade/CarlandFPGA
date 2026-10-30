"""Private pure numerical world values. No native/clock/provider acquisition.

DTOs mirror the sealed SnapshotValue contract; they are *not* authenticated live
capabilities. The original Root owner authenticates its channel/freeze, constructs
these values and later adopts only its registered original epoch/result pair.
Nominal volumes plus bounds refer to the exact recorded finite-affine model.
They do not qualify rendering/GPU arithmetic, sensors, inference or full H12.
"""
from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction as F
import base64
import binascii
import hashlib
import itertools
import json
import math
import struct

from .motion import solid_clearance as s
from .motion import gate_geometry as g
from .motion import gate_clearance as gc
from .motion import workspace_boundaries as w
from .motion import passage_phase as passage
from .motion.kinematics import RigidState
from .motion_executor import GeometryBudget
from . import _solid_pair as pair


CONTRACT = 'DEEPEYE-HUMAN-LOCK-20261014/revision1'
REQUIREMENTS = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
DOMAIN = 'exact_recorded_finite_affine_model/v1'
VERSION = 'nominal-convex-envelope-with-finite-affine-residual/v1'
GUARD = F(1,1000000)  # Root-selected private policy; not a human requirement.
KINDS = ('water','hard_rock','fault','void','casing')
PRIORITY = {'casing':5,'fault':4,'void':3,'water':2,'hard_rock':1}
BASE_HALF = {'water':(F(3),F(2),F(1)), 'hard_rock':(F(1.5),)*3,
             'fault':(F(4),F(.5),F(3)), 'void':(F(2),F(1.5),F(1.5)),
             'casing':(F(.4),F(.4),F(4))}
SIZE_LIMITS = {'water':((3,10),(2,8),(1,4)), 'hard_rock':((1,6),)*3,
               'fault':((4,15),(.5,2),(3,10)), 'void':((2,8),)*3,
               'casing':((.5,1.5),(.5,1.5),(3,20))}
_MAX_BYTES = 134217728


class ConstructionRefusal(ValueError):
    """Authority-private bounded refusal, never an actor collision oracle."""


def _int(value, minimum=0, maximum=(1 << 64)-1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ConstructionRefusal('bounded exact integer required')
    return value


def _sha(value):
    if (type(value) is not str or len(value) != 64 or
            any(c not in '0123456789abcdef' for c in value)):
        raise ConstructionRefusal('source/digest identity malformed')
    return value


def _label(value):
    if type(value) is not str or not value.strip() or len(value.encode('utf-8')) > 256:
        raise ConstructionRefusal('bounded nonempty label required')
    return value


def _vec(value, size=3):
    if type(value) is not tuple or len(value) != size:
        raise ConstructionRefusal('immutable exact vector required')
    return tuple(s._scalar(x) for x in value)


@dataclass(frozen=True)
class Affine:
    matrix: tuple
    translation: tuple

    def __post_init__(self):
        if type(self.matrix) is not tuple or len(self.matrix) != 3:
            raise ConstructionRefusal('exact three-row affine required')
        object.__setattr__(self,'matrix',tuple(_vec(row) for row in self.matrix))
        object.__setattr__(self,'translation',_vec(self.translation))

    @staticmethod
    def identity():
        return Affine(tuple(tuple(F(int(i == j)) for j in range(3)) for i in range(3)),(F(0),)*3)


@dataclass(frozen=True)
class GateValue:
    face: str
    u_bits: str
    v_bits: str


@dataclass(frozen=True)
class NormalizedObject:
    object_id: int
    kind: str
    priority: int
    position_bits: tuple
    rotation_deg_bits: tuple
    size_bits: tuple


@dataclass(frozen=True)
class NormalizedLayout:
    scalar_width: int
    objects: tuple
    gates: tuple  # entry, exit; GateValue uses binary64 independently of real_t.


@dataclass(frozen=True)
class CanonicalCompanion:
    raw_layout_bytes: bytes
    raw_sha256: str
    normalized_value_bits: NormalizedLayout
    canonical_utf8: bytes
    legacy_layout_sha256: str
    document_source_sha256: str
    canonical_source_sha256: str


@dataclass(frozen=True)
class FreezeIdentity:
    freeze_id: str
    world_epoch: int
    document_generation: int
    geometry_generation: int
    main_instance_id: int
    document_instance_id: int
    workspace_instance_id: int
    drill_root_instance_id: int
    source_bundle_sha256: str
    immutable_payload_sha256: str
    geometry_state_sha256: str


@dataclass(frozen=True)
class InventoryCounts:
    nodes: int
    objects: int
    surfaces: int
    unique_vertices: int
    indices: int
    required_geometry_nodes: int
    observer_nodes: int


@dataclass(frozen=True)
class ObjectManifest:
    object_id: int
    kind: str
    priority: int
    part_ids: tuple


@dataclass(frozen=True)
class NodeFlags:
    script_sha256: str | None
    processing: bool
    top_level: bool
    disable_scale: bool
    unguarded_geometry_writer: bool
    physics_active: bool
    geometry_write_guarded: bool
    animation_active: bool = False


@dataclass(frozen=True)
class NodeValue:
    node_id: int
    parent_id: int | None
    role: str  # ancestor, workspace, geometry, drill_pose, observer
    global_transform: Affine | None
    flags: NodeFlags
    local: Affine | None = None
    path: str = ''
    class_name: str = ''


@dataclass(frozen=True)
class CatalogEntry:
    kind: str
    part_ids: tuple


@dataclass(frozen=True)
class PartValue:
    part_id: str
    node_id: int
    kind: str  # mesh, box, ellipsoid, cylinder, capsule
    global_transform: Affine
    dimensions: tuple  # half extents; cylinder(rx,ry,half length), capsule(h,r,0)
    axis: int  # analytic cylinder/capsule native local axial coordinate0/1/2
    vertices: tuple
    indices: tuple
    geometry_sha256: str  # normative mesh/analytic identity, checked at wire conversion
    shape_disabled: bool | None
    shape_margin_m: F | None  # observed disabled descriptor value, not active solver qualification


@dataclass(frozen=True)
class ObjectWitness:
    object_id: int
    root_node_id: int
    root_affine: Affine
    proposed_quaternion: tuple
    parts: tuple


@dataclass(frozen=True)
class AssetValues:
    catalog_source_sha256: str
    catalog: tuple
    objects: tuple
    presentation_parts: tuple


@dataclass(frozen=True)
class WorkspaceValue:
    units: str
    transform: Affine
    gates: tuple


@dataclass(frozen=True)
class DrillValue:
    root_node_id: int
    root_affine: Affine
    part_ids: tuple
    parts: tuple


@dataclass(frozen=True)
class ImmutabilityAudit:
    writer_inventory_sha256: str
    document_generation: int
    geometry_generation: int
    required_node_ids: tuple


@dataclass(frozen=True)
class SnapshotValue:
    freeze_identity: FreezeIdentity
    canonical_companion: CanonicalCompanion
    inventory_counts: InventoryCounts
    independent_object_manifest: tuple
    nodes: tuple
    assets: AssetValues
    workspace: WorkspaceValue
    drill: DrillValue
    immutability_audit: ImmutabilityAudit


@dataclass(frozen=True)
class ValuePolicy:
    document_source_sha256: str
    canonical_source_sha256: str
    catalog_source_sha256: str
    writer_inventory_sha256: str
    source_bundle_sha256: str
    catalog: tuple
    presentation_part_ids: tuple
    allowed_script_sha256: tuple
    run_id: str = 'diagnostic-world-component'
    guard_m: F = GUARD
    getter_endpoint_cap_m: F = F(0)


@dataclass(frozen=True)
class ObjectBound:
    object_id: int
    affine_upper_m: F
    local_upper_m: F
    affine_norm_upper: F
    total_upper_m: F
    part_bounds: tuple


@dataclass(frozen=True)
class BudgetDerivation:
    domain: str
    policy_guard_m: F
    full_drill_containment_upper_m: F
    all_object_bounds: tuple
    obstacle_max_upper_m: F
    numeric_m: F
    asset_m: F
    obstacle_m: F
    additional_margin_f64: float
    source_pins_digest: str
    parent_getter_differences: tuple
    outside_domain: tuple
    getter_endpoint_cap_m: F = F(0)


@dataclass(frozen=True)
class CorridorProof:
    corridor: s.Solid
    pairs: tuple
    support_terms: int
    status: str
    motion_grant: bool = field(default=False,init=False)


@dataclass(frozen=True)
class WorldValues:
    snapshot_digest: str
    geometry_identity: str
    scene: s.Scene
    model: s.CapsuleModel
    layout: w.Layout
    envelope: w.Envelope
    budget: GeometryBudget
    initial_state: passage.PassageState
    budget_derivation: BudgetDerivation
    static_corridor_proofs: tuple
    initial_scene_proof: s.SceneResult
    domain: str = field(default='numerical_value_only',init=False)
    motion_grant: bool = field(default=False,init=False)


def _getter_endpoint_cap(policy):
    cap = policy.getter_endpoint_cap_m
    if (type(cap) is not F or cap.numerator.bit_length() > 256
            or cap.denominator.bit_length() > 256 or cap < 0 or cap > F(1,100)):
        raise ConstructionRefusal('endpoint getter cap must be an exact bounded Fraction in [0, 1/100] m')
    return cap


def _pack(value, work=None):
    """Reject mutable/foreign DTOs and bound canonical identity material size."""
    if work is None:
        work = [0]
    t = type(value)
    if t is F:
        s._scalar(value)
        work[0] += value.numerator.bit_length()+value.denominator.bit_length()+64
        result = ['r',str(value.numerator),str(value.denominator)]
    elif t is bytes:
        work[0] += 2*len(value)+32
        result = ['b',value.hex()]
    elif t is str:
        work[0] += 6*len(value.encode('utf-8'))+32
        result = value
    elif t in (int,bool,type(None)):
        work[0] += (value.bit_length() if t is int else 1)+32
        result = value
    elif t is tuple:
        work[0] += 2+len(value)
        result = [_pack(x,work) for x in value]
    elif is_dataclass(value) and t.__module__ == __name__:
        # Preserve the original canonical ValuePolicy bytes and resource count
        # for the default; nonzero policies are explicitly domain-separated.
        cap = _getter_endpoint_cap(value) if t is ValuePolicy else None
        fs = tuple(f for f in fields(value) if not
                   (t is ValuePolicy and f.name == 'getter_endpoint_cap_m'
                    and cap == F(0)))
        work[0] += 128+sum(len(f.name)*6 for f in fs)
        result = {f.name:_pack(getattr(value,f.name),work) for f in fs if f.init}
        if t is ValuePolicy and cap:
            key = '__getter_endpoint_cap_domain__'
            work[0] += len(key)*6
            result[key] = _pack('DEEPEYE-ENDPOINT-AFFINE-SET-GETTER-CAP-V1',work)
    else:
        raise ConstructionRefusal('only immutable internal value DTOs accepted')
    if work[0] > _MAX_BYTES:
        raise ConstructionRefusal('canonical numerical input exceeds resource domain')
    return result


def _digest(value):
    raw = json.dumps(_pack(value),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _number(token):
    if len(token) > 2048:
        raise ConstructionRefusal('numeric token exceeds resource domain')
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise ConstructionRefusal('invalid numeric token') from exc
    if not value.is_finite() or (value and abs(value.adjusted()) > 4096):
        raise ConstructionRefusal('nonfinite/unsupported numeric exponent')
    return value


def _pairs(entries):
    result = {}
    for key,value in entries:
        if key in result:
            raise ConstructionRefusal('duplicate decoded JSON key')
        result[key] = value
    return result


def _integer_token(token):
    return int(_number(token))


def _json(raw, maximum=1048576, *, integer_tokens=False):
    if type(raw) is not bytes or not 0 < len(raw) <= maximum:
        raise ConstructionRefusal('bounded original raw UTF8 bytes required')
    try:
        text = raw.decode('utf-8','strict')
    except UnicodeError as exc:
        raise ConstructionRefusal('invalid UTF8') from exc
    depth = 0
    quoted = escaped = False
    for ch in text:
        if quoted:
            if escaped: escaped = False
            elif ch == '\\': escaped = True
            elif ch == '"': quoted = False
        elif ch == '"': quoted = True
        elif ch in '[{':
            depth += 1
            if depth > 32: raise ConstructionRefusal('JSON depth exceeds32')
        elif ch in ']}': depth -= 1
    try:
        return json.loads(text,parse_int=_integer_token if integer_tokens else _number,parse_float=_number,
            parse_constant=lambda _: (_ for _ in ()).throw(ConstructionRefusal('nonfinite JSON')),
            object_pairs_hook=_pairs)
    except (ValueError,InvalidOperation,RecursionError) as exc:
        if type(exc) is ConstructionRefusal: raise
        raise ConstructionRefusal('strict JSON rejected') from exc


def _keys(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise ConstructionRefusal('exact JSON fields required')


def _integer_number(value,low,high):
    if type(value) is not Decimal or value != value.to_integral_value() or not low <= value <= high:
        raise ConstructionRefusal('exact bounded integer JSON value required')
    return int(value)


def _bits_number(value,width):
    if type(value) is not Decimal or width not in (32,64):
        raise ConstructionRefusal('exact JSON number and real_t width required')
    try:
        encoded = struct.pack('>f' if width == 32 else '>d',float(value)).hex()
    except (OverflowError,ValueError,struct.error) as exc:
        raise ConstructionRefusal('normalized real value overflow') from exc
    _decode_bits(encoded,width)
    return encoded


def _decode_bits(value,width):
    if (type(value) is not str or len(value) != width//4 or
            any(c not in '0123456789abcdef' for c in value)):
        raise ConstructionRefusal('canonical finite IEEE bit string required')
    result = struct.unpack('>f' if width == 32 else '>d',bytes.fromhex(value))[0]
    if not math.isfinite(result):
        raise ConstructionRefusal('normalized nonfinite scalar')
    return result


def _parse_raw(raw,width):
    if type(width) is not int or width not in (32,64):
        raise ConstructionRefusal('explicit actual real_t scalar width required')
    doc = _json(raw)
    _keys(doc,('schema','contract','requirements_sha256','units','layout','layout_hash'))
    if (_integer_number(doc['schema'],1,1) != 1 or doc['contract'] != CONTRACT or
            doc['requirements_sha256'] != REQUIREMENTS or doc['units'] != 'm'):
        raise ConstructionRefusal('locked layout contract mismatch')
    _sha(doc['layout_hash'])
    layout = doc['layout']; _keys(layout,('obstacles','gates'))
    objects = layout['obstacles']
    if type(objects) is not list or len(objects) > 30:
        raise ConstructionRefusal('bounded complete obstacle array required')
    normalized = []
    seen = set()
    for obj in objects:
        _keys(obj,('object_id','kind','position','rotation_deg','size','priority'))
        oid = _integer_number(obj['object_id'],1,9007199254740991)
        kind = obj['kind']
        if oid in seen or type(kind) is not str or kind not in KINDS:
            raise ConstructionRefusal('duplicate object or unsupported material')
        seen.add(oid)
        priority = _integer_number(obj['priority'],1,5)
        if priority != PRIORITY[kind]: raise ConstructionRefusal('editor material priority mismatch')
        vectors = []
        for key in ('position','rotation_deg','size'):
            _keys(obj[key],('x','y','z'))
            vectors.append(tuple(_bits_number(obj[key][axis],width) for axis in 'xyz'))
        p,rotation,size = vectors
        if any(abs(F(_decode_bits(x,width))) > 15+F(1e-9) for x in p):
            raise ConstructionRefusal('normalized object centre outside workspace')
        for x,(low,high) in zip(size,SIZE_LIMITS[kind]):
            v = F(_decode_bits(x,width))
            if not F(low)-F(1e-9) <= v <= F(high)+F(1e-9):
                raise ConstructionRefusal('normalized object size outside source domain')
        normalized.append(NormalizedObject(oid,kind,priority,p,rotation,size))
    _keys(layout['gates'],('entry','exit'))
    gates = []
    for name in ('entry','exit'):
        gate = layout['gates'][name]; _keys(gate,('face','u','v'))
        if type(gate['face']) is not str or gate['face'] not in w.FACES:
            raise ConstructionRefusal('unknown gate face')
        gates.append(GateValue(gate['face'],_bits_number(gate['u'],64),_bits_number(gate['v'],64)))
    return NormalizedLayout(width,tuple(normalized),tuple(gates)),doc['layout_hash']


def _wire_u(value,maximum=(1 << 64)-1):
    if (type(value) is not str or not 1 <= len(value) <=20 or
            any(c not in '0123456789' for c in value) or
            (len(value)>1 and value[0]=='0')):
        raise ConstructionRefusal('canonical decimal U64 string required')
    result=int(value)
    return _int(result,0,maximum)


def _wire_array(value,limit,exact=None):
    if type(value) is not list or len(value)>limit or (exact is not None and len(value)!=exact):
        raise ConstructionRefusal('bounded complete JSON array required')
    return value


def _wire_bits(value,width,size=3):
    result=tuple(_wire_array(value,size,size))
    for component in result: _decode_bits(component,width)
    return result


def _wire_affine(value,width,optional=False):
    if value is None and optional: return None
    _keys(value,('basis_columns','origin'))
    columns=tuple(_wire_bits(x,width) for x in _wire_array(value['basis_columns'],3,3))
    origin=_wire_bits(value['origin'],width)
    return Affine(tuple(tuple(F(_decode_bits(columns[j][i],width)) for j in range(3)) for i in range(3)),
        tuple(F(_decode_bits(x,width)) for x in origin))


def _wire_gate(value):
    _keys(value,('face','u_bits','v_bits'))
    _label(value['face']); _decode_bits(value['u_bits'],64); _decode_bits(value['v_bits'],64)
    return GateValue(value['face'],value['u_bits'],value['v_bits'])


def _wire_names(value):
    return tuple(_label(x) for x in _wire_array(value,4096))


def _wire_b64(value):
    if type(value) is not str or len(value)>1398104:
        raise ConstructionRefusal('bounded canonical base64 required')
    try:
        decoded=base64.b64decode(value,validate=True)
    except (ValueError,binascii.Error) as exc:
        raise ConstructionRefusal('malformed base64') from exc
    if len(decoded)>1048576 or base64.b64encode(decoded).decode('ascii')!=value:
        raise ConstructionRefusal('noncanonical/oversized base64')
    return decoded


def _mesh_digest(vertex_bits,indices,width):
    digest=hashlib.sha256(b'DEY-MESH-1'+struct.pack('>BII',width,len(vertex_bits),len(indices)))
    for vertex in vertex_bits:
        for component in vertex: digest.update(bytes.fromhex(component))
    for index in indices: digest.update(struct.pack('>I',index))
    return digest.hexdigest()


def _analytic_digest(kind,dimension_bits,axis,shape_disabled,shape_margin_bits):
    """Original observed descriptor, fixed cross-language byte recipe."""
    codes={'box':1,'ellipsoid':2,'cylinder':3,'capsule':4}
    if kind not in codes or type(axis) is not int or axis not in (0,1,2) or shape_disabled is not True:
        raise ConstructionRefusal('disabled normalized analytic descriptor required')
    if type(dimension_bits) not in (tuple,list) or len(dimension_bits)!=3:
        raise ConstructionRefusal('three analytic dimension bit strings required')
    for bits in dimension_bits:_decode_bits(bits,64)
    margin=_decode_bits(shape_margin_bits,64)
    if margin<0:raise ConstructionRefusal('finite nonnegative observed shape margin required')
    raw=b'DEY-ANALYTIC-1'+bytes((codes[kind],axis,1))
    raw+=b''.join(bytes.fromhex(bits) for bits in dimension_bits)+bytes.fromhex(shape_margin_bits)
    return hashlib.sha256(raw).hexdigest()


def _wire_part(value,width):
    _keys(value,('part_id','node_id','kind','global_transform','dimensions','axis','vertices','indices','geometry_sha256',
        'shape_disabled','shape_margin_bits'))
    kind=value['kind']; _label(kind)
    if kind not in ('mesh','box','ellipsoid','cylinder','capsule'):
        raise ConstructionRefusal('unsupported serialized part kind')
    dimensions=_wire_array(value['dimensions'],3,0 if kind=='mesh' else 3)
    dims=tuple(F(_decode_bits(x,64)) for x in dimensions)
    vertex_bits=tuple(_wire_bits(x,width) for x in _wire_array(value['vertices'],1000000))
    indices=tuple(_wire_u(x,(1 << 32)-1) for x in _wire_array(value['indices'],3000000))
    sha=_sha(value['geometry_sha256'])
    axis=_wire_u(value['axis'],2)
    if kind=='mesh':
        if value['shape_disabled'] is not None or value['shape_margin_bits'] is not None:
            raise ConstructionRefusal('mesh shape metadata must be explicit null')
        disabled=margin=None
        if not vertex_bits or not indices or len(indices)%3 or any(x>=len(vertex_bits) for x in indices):
            raise ConstructionRefusal('complete indexed triangle surface required')
        if _mesh_digest(vertex_bits,indices,width)!=sha:
            raise ConstructionRefusal('complete raw normalized mesh identity mismatch')
    else:
        if vertex_bits or indices:
            raise ConstructionRefusal('analytic volume contains unexpected sampled surface')
        if value['shape_disabled'] is not True:
            raise ConstructionRefusal('actual analytic shape must be disabled')
        disabled=True
        margin=F(_decode_bits(value['shape_margin_bits'],64))
        if margin<0:raise ConstructionRefusal('actual analytic margin must be nonnegative')
        if _analytic_digest(kind,dimensions,axis,disabled,value['shape_margin_bits'])!=sha:
            raise ConstructionRefusal('normalized observed analytic descriptor SHA mismatch')
    return PartValue(_label(value['part_id']),_wire_u(value['node_id']),kind,
        _wire_affine(value['global_transform'],width),dims,axis,
        tuple(tuple(F(_decode_bits(x,width)) for x in vertex) for vertex in vertex_bits),indices,sha,disabled,margin)


def _wire_catalog(value):
    result=[]
    for entry in _wire_array(value,6,6):
        _keys(entry,('kind','part_ids'))
        result.append(CatalogEntry(_label(entry['kind']),_wire_names(entry['part_ids'])))
    return tuple(result)


def _wire_tree_sha256(value):
    """Injective typed-wire-tree commitment, independent of JSON formatting.

    Tags: null0,false1,true2,string3,integer4,array5,object6. Length/count is
    u64BE. Integer is signed i64BE. Object keys sort by their UTF8 bytes. Only
    integral JSON numbers (the32/64 width) are in this snapshot grammar.
    """
    digest=hashlib.sha256(b'DEY-IMMUTABLE-1')
    def feed(item):
        t=type(item)
        if item is None: digest.update(b'\x00')
        elif t is bool: digest.update(b'\x02' if item else b'\x01')
        elif t is str:
            raw=item.encode('utf-8'); digest.update(b'\x03'+struct.pack('>Q',len(raw))+raw)
        elif t in (int,Decimal):
            if t is Decimal and item!=item.to_integral_value():
                raise ConstructionRefusal('integer typed wire commitment required')
            number=int(item)
            if not -(1 << 63)<=number<(1 << 63): raise ConstructionRefusal('wire integer exceeds i64')
            digest.update(b'\x04'+struct.pack('>q',number))
        elif t is list:
            digest.update(b'\x05'+struct.pack('>Q',len(item)))
            for child in item: feed(child)
        elif t is dict:
            if any(type(k) is not str for k in item): raise ConstructionRefusal('string wire keys required')
            keys=sorted(item,key=lambda k:k.encode('utf-8'))
            digest.update(b'\x06'+struct.pack('>Q',len(keys)))
            for key in keys: feed(key); feed(item[key])
        else: raise ConstructionRefusal('unsupported typed wire commitment value')
    feed(value)
    return digest.hexdigest()


def snapshot_from_wire(raw_json_document):
    """Strict complete SnapshotValue bytes -> immutable DTO; no authentication.

    Root retains the authenticated original raw payload/digest/epoch registry.
    Parsing valid values never creates a live freeze or owner capability.
    """
    try:
        return _snapshot_from_wire(raw_json_document)
    except ConstructionRefusal:
        raise
    except (ValueError,TypeError,ArithmeticError,KeyError,AttributeError,UnicodeError,struct.error) as exc:
        raise ConstructionRefusal('strict complete snapshot value conversion refused') from exc


def _snapshot_from_wire(raw):
    doc=_json(raw,_MAX_BYTES,integer_tokens=True)
    _keys(doc,('freeze_identity','canonical_companion','inventory_counts','independent_object_manifest',
        'nodes','assets','workspace','drill','immutability_audit'))
    comp=doc['canonical_companion']
    _keys(comp,('raw_layout_bytes_base64','raw_sha256','normalized_value_bits','canonical_utf8_base64',
        'legacy_layout_sha256','document_source_sha256','canonical_source_sha256'))
    normalized=comp['normalized_value_bits']; _keys(normalized,('scalar_width','objects','gates'))
    width=_int(normalized['scalar_width'],32,64)
    if width not in (32,64): raise ConstructionRefusal('actual scalar width32 or64 required')
    objects=[]
    for item in _wire_array(normalized['objects'],30):
        _keys(item,('object_id','kind','priority','position_bits','rotation_deg_bits','size_bits'))
        objects.append(NormalizedObject(_wire_u(item['object_id'],9007199254740991),_label(item['kind']),
            _wire_u(item['priority'],5),_wire_bits(item['position_bits'],width),
            _wire_bits(item['rotation_deg_bits'],width),_wire_bits(item['size_bits'],width)))
    gates=tuple(_wire_gate(x) for x in _wire_array(normalized['gates'],2,2))
    companion=CanonicalCompanion(_wire_b64(comp['raw_layout_bytes_base64']),_sha(comp['raw_sha256']),
        NormalizedLayout(width,tuple(objects),gates),_wire_b64(comp['canonical_utf8_base64']),
        _sha(comp['legacy_layout_sha256']),_sha(comp['document_source_sha256']),_sha(comp['canonical_source_sha256']))
    identity=doc['freeze_identity']
    identity_fields=tuple(f.name for f in fields(FreezeIdentity)); _keys(identity,identity_fields)
    values={}
    for name in identity_fields:
        value=identity[name]
        values[name]=(_label(value) if name=='freeze_id' else _sha(value) if name.endswith('sha256') else _wire_u(value))
    ident=FreezeIdentity(**values)
    count=doc['inventory_counts']; count_fields=tuple(f.name for f in fields(InventoryCounts)); _keys(count,count_fields)
    counts=InventoryCounts(**{name:_wire_u(count[name]) for name in count_fields})
    if counts.nodes>4096 or counts.objects>30 or counts.surfaces>64 or counts.unique_vertices>1000000 or counts.indices>3000000:
        raise ConstructionRefusal('complete snapshot inventory exceeds supported work domain')
    manifest=[]
    for entry in _wire_array(doc['independent_object_manifest'],30):
        _keys(entry,('object_id','kind','priority','part_ids'))
        manifest.append(ObjectManifest(_wire_u(entry['object_id'],9007199254740991),_label(entry['kind']),
            _wire_u(entry['priority'],5),_wire_names(entry['part_ids'])))
    nodes=[]
    for item in _wire_array(doc['nodes'],4096):
        _keys(item,('node_id','parent_id','role','path','class_name','local','global_transform','flags'))
        flag=item['flags']; flag_fields=tuple(f.name for f in fields(NodeFlags)); _keys(flag,flag_fields)
        for name in flag_fields:
            if name!='script_sha256' and type(flag[name]) is not bool:
                raise ConstructionRefusal('boolean actual node flags required')
        script=flag['script_sha256']
        if script is not None: _sha(script)
        if type(item['path']) is not str or not item['path'] or len(item['path'].encode('utf-8'))>4096:
            raise ConstructionRefusal('bounded original node path required')
        nodes.append(NodeValue(_wire_u(item['node_id']),None if item['parent_id'] is None else _wire_u(item['parent_id']),
            _label(item['role']),_wire_affine(item['global_transform'],width,True),NodeFlags(**flag),
            _wire_affine(item['local'],width,True),item['path'],_label(item['class_name'])))
    assets=doc['assets']; _keys(assets,('catalog_source_sha256','catalog','objects','presentation_parts'))
    witnesses=[]
    for obj in _wire_array(assets['objects'],30):
        _keys(obj,('object_id','root_node_id','root_affine','proposed_quaternion','parts'))
        witnesses.append(ObjectWitness(_wire_u(obj['object_id'],9007199254740991),_wire_u(obj['root_node_id']),
            _wire_affine(obj['root_affine'],width),tuple(F(_decode_bits(x,64)) for x in _wire_bits(obj['proposed_quaternion'],64,4)),
            tuple(_wire_part(x,width) for x in _wire_array(obj['parts'],4096))))
    presentation=tuple(_wire_part(x,width) for x in _wire_array(assets['presentation_parts'],4096))
    asset_values=AssetValues(_sha(assets['catalog_source_sha256']),_wire_catalog(assets['catalog']),tuple(witnesses),presentation)
    workspace=doc['workspace']; _keys(workspace,('units','transform','gates'))
    ws=WorkspaceValue(workspace['units'],_wire_affine(workspace['transform'],width),
        tuple(_wire_gate(x) for x in _wire_array(workspace['gates'],2,2)))
    drill=doc['drill']; _keys(drill,('root_node_id','root_affine','part_ids','parts'))
    body=DrillValue(_wire_u(drill['root_node_id']),_wire_affine(drill['root_affine'],width),_wire_names(drill['part_ids']),
        tuple(_wire_part(x,width) for x in _wire_array(drill['parts'],4096)))
    audit=doc['immutability_audit']; _keys(audit,('writer_inventory_sha256','document_generation','geometry_generation','required_node_ids'))
    immutable=ImmutabilityAudit(_sha(audit['writer_inventory_sha256']),_wire_u(audit['document_generation']),
        _wire_u(audit['geometry_generation']),tuple(_wire_u(x) for x in _wire_array(audit['required_node_ids'],4096)))
    result=SnapshotValue(ident,companion,counts,tuple(manifest),tuple(nodes),asset_values,ws,body,immutable)
    if _wire_tree_sha256({k:v for k,v in doc.items() if k!='freeze_identity'})!=ident.immutable_payload_sha256:
        raise ConstructionRefusal('complete non-self-referential immutable payload commitment mismatch')
    _pack(result)  # refuse any unsupported mutable/oversized identity material
    return result


def _mul(a,b):
    return tuple(tuple(sum((a[i][k]*b[k][j] for k in range(3)),F(0)) for j in range(3)) for i in range(3))


def _mv(a,b):
    return tuple(sum((row[j]*b[j] for j in range(3)),F(0)) for row in a)


def _norm(x):
    return s._sqrt_up(sum((v*v for v in x),F(0)))


def _frobenius(a):
    return _norm(tuple(x for row in a for x in row))


def _inverse(a):
    # Exact algebraic inverse of the actual encoded affine; no SO(3) assumption.
    # Cyclic row/column order already supplies the cofactor sign for a3x3.
    cof = tuple(tuple((
        a[(i+1)%3][(j+1)%3]*a[(i+2)%3][(j+2)%3]-
        a[(i+1)%3][(j+2)%3]*a[(i+2)%3][(j+1)%3])
        for j in range(3)) for i in range(3))
    determinant = sum((a[0][j]*cof[0][j] for j in range(3)),F(0))
    if determinant == 0: raise ConstructionRefusal('singular actual root affine')
    result = tuple(tuple(cof[j][i]/determinant for j in range(3)) for i in range(3))
    # A mistaken inverse cannot quietly lose a part: exact identity is decisive.
    if _mul(a,result) != Affine.identity().matrix:
        raise ConstructionRefusal('exact affine inverse identity failed')
    for row in result: _vec(row)
    return result


def _relative(root,part):
    inverse = _inverse(root.matrix)
    return Affine(_mul(inverse,part.matrix),_mv(inverse,tuple(x-y for x,y in zip(part.translation,root.translation))))


def _affine_residual(actual,base_half,dimensions,quaternion,kind):
    base_half = _vec(tuple(base_half)); dimensions = _vec(tuple(dimensions))
    rotation = s._rotation(_vec(tuple(quaternion),4))
    matrix = tuple(tuple(actual.matrix[i][j]*base_half[j]-rotation[i][j]*dimensions[j]
        for j in range(3)) for i in range(3))
    # Caller chooses t0 == actual root origin; translation error is exactly0 in
    # this encoded model, not an unknown later presentation evaluation error.
    rows = tuple((sum(map(abs,row),F(0)) if kind == 'box' else
        s._sqrt_up(row[0]**2+row[1]**2)+abs(row[2])) for row in matrix)
    return _norm(rows)


def _axis_permutation(axis):
    if type(axis) is not int or axis not in (0,1,2):
        raise ConstructionRefusal('explicit native primitive axis required')
    # Columns map canonical Z-axis geometry into the actual native local axis.
    return (((0,0,1),(1,0,0),(0,1,0)),
            ((1,0,0),(0,0,1),(0,-1,0)),
            ((1,0,0),(0,1,0),(0,0,1)))[axis]


def _canonical_linear(local,axis):
    return _mul(local.matrix,tuple(tuple(F(x) for x in row) for row in _axis_permutation(axis)))


def _point(local,point):
    return tuple(x+y for x,y in zip(_mv(local.matrix,point),local.translation))


def _point_bound(point,target,half):
    if target == 'box':
        return _norm(tuple(max(F(0),abs(x)-b) for x,b in zip(point,half)))
    if target == 'cylinder':
        rho = s._sqrt_up((point[0]/half[0])**2+(point[1]/half[1])**2)
        radial = max(half[0],half[1])*max(F(0),rho-1)
        axial = max(F(0),abs(point[2])-half[2])
        return _norm((radial,axial))
    # Distance to the complete nominal capsule (segment[-h,h] + Euclidean ball).
    distance = _norm((point[0],point[1],max(F(0),abs(point[2])-half[0])))
    return max(F(0),distance-half[1])


def _analytic_extents(part,local):
    if part.kind == 'box':
        return tuple(sum((abs(x)*d for x,d in zip(row,part.dimensions)),F(0)) for row in local.matrix)
    if part.kind == 'ellipsoid':
        return tuple(_norm(tuple(x*d for x,d in zip(row,part.dimensions))) for row in local.matrix)
    canonical = _canonical_linear(local,part.axis)
    if part.kind == 'cylinder':
        rx,ry,h = part.dimensions
        return tuple(s._sqrt_up((row[0]*rx)**2+(row[1]*ry)**2)+abs(row[2])*h for row in canonical)
    h,r,_ = part.dimensions
    return tuple(abs(row[2])*h+_norm(row)*r for row in canonical)


def _part_bound(part,root,target,half):
    local = _relative(root,part.global_transform)
    if part.kind == 'mesh':
        return max((_point_bound(_point(local,p),target,half) for p in part.vertices),default=F(0))
    if target == 'cylinder' and part.kind == 'cylinder':
        # Compare two complete images of one unit cylinder; all sign changes
        # preserve its volume. Includes internal Rx, snapping and unequal radii.
        actual = _canonical_linear(local,part.axis)
        answers = []
        for signs in itertools.product((-1,1),repeat=3):
            matrix = tuple(tuple(actual[i][j]*part.dimensions[j]*signs[j]-F(int(i==j))*half[j]
                for j in range(3)) for i in range(3))
            rows = tuple(abs(local.translation[i])+s._sqrt_up(row[0]**2+row[1]**2)+abs(row[2])
                for i,row in enumerate(matrix))
            answers.append(_norm(rows))
        return min(answers)
    if target == 'capsule' and part.kind == 'capsule':
        actual = _canonical_linear(local,part.axis)
        h,r,_ = part.dimensions
        answers = []
        for signs in itertools.product((-1,1),repeat=3):
            a = tuple(tuple(row[j]*signs[j] for j in range(3)) for row in actual)
            endpoints = tuple(tuple(local.translation[i]+sign*a[i][2]*h for i in range(3)) for sign in (-1,1))
            line = max(_norm((p[0],p[1],max(F(0),abs(p[2])-half[0]))) for p in endpoints)
            residual = tuple(tuple(a[i][j]-int(i==j) for j in range(3)) for i in range(3))
            answers.append(line+max(F(0),r-half[1])+r*_frobenius(residual))
        return min(answers)
    extents = _analytic_extents(part,local)
    if target == 'box':
        return _norm(tuple(max(F(0),abs(t)+e-b) for t,e,b in zip(local.translation,extents,half)))
    # Whole analytic volume is within this exact/outward AABB. Full corners,
    # not a sampled circle/ring, bound its containment into a convex target.
    return max(_point_bound(tuple(t+sign*e for t,sign,e in zip(local.translation,signs,extents)),target,half)
        for signs in itertools.product((-1,1),repeat=3))


def _validate_parts(parts,names,nodes,root_id,counts,*,presentation=False):
    if (type(parts) is not tuple or (not parts and not presentation) or len(parts) > 4096 or
            tuple(p.part_id for p in parts) != names):
        raise ConstructionRefusal('complete independent part inventory required')
    if len(set(names)) != len(names) or any(type(n) is not str or not n for n in names):
        raise ConstructionRefusal('duplicate/invalid source part IDs')
    analytic = False
    used_nodes = set()
    node_kinds = {}
    for p in parts:
        if type(p) is not PartValue or p.kind not in ('mesh','box','ellipsoid','cylinder','capsule'):
            raise ConstructionRefusal('unsupported full part volume')
        _label(p.part_id); _sha(p.geometry_sha256); _int(p.node_id,1)
        allowed_roles=('geometry','observer') if presentation else ('geometry',)
        if p.node_id not in nodes or nodes[p.node_id].role not in allowed_roles:
            raise ConstructionRefusal('part node missing/duplicated/not geometry')
        if p.node_id in node_kinds and (node_kinds[p.node_id]!='mesh' or p.kind!='mesh'):
            raise ConstructionRefusal('analytic/mesh node reused ambiguously')
        node_kinds[p.node_id]=p.kind
        expected_class='MeshInstance3D' if p.kind=='mesh' else 'CollisionShape3D'
        if nodes[p.node_id].class_name!=expected_class:
            raise ConstructionRefusal('actual part node class/volume kind mismatch')
        used_nodes.add(p.node_id)
        if p.global_transform != nodes[p.node_id].global_transform:
            raise ConstructionRefusal('part original node affine mismatch')
        parent = p.node_id
        while parent is not None and parent != root_id:
            parent = nodes[parent].parent_id
        if parent != root_id: raise ConstructionRefusal('part outside its original owner subtree')
        _axis_permutation(p.axis)
        if p.kind == 'mesh':
            if p.shape_disabled is not None or p.shape_margin_m is not None:
                raise ConstructionRefusal('mesh descriptor shape metadata must be null')
            if (p.dimensions != () or type(p.vertices) is not tuple or not p.vertices or
                    len(p.vertices) > 1000000 or type(p.indices) is not tuple or
                    not p.indices or len(p.indices)%3 or len(p.indices)>3000000):
                raise ConstructionRefusal('complete bounded triangle stream required')
            for vertex in p.vertices: _vec(vertex)
            for index in p.indices: _int(index,0,len(p.vertices)-1)
            payload = (p.vertices,p.indices)
            prior = counts.get(p.geometry_sha256)
            if prior is not None and prior != payload:
                raise ConstructionRefusal('same raw mesh identity has conflicting complete geometry')
            counts[p.geometry_sha256] = payload
        else:
            analytic = True
            if p.shape_disabled is not True or type(p.shape_margin_m) is not F or p.shape_margin_m<0:
                raise ConstructionRefusal('explicit disabled analytic and nonnegative exact observed margin required')
            s._scalar(p.shape_margin_m)
            dims = _vec(p.dimensions)
            if p.vertices != () or p.indices != ():
                raise ConstructionRefusal('analytic volumes cannot use sampled mesh substitutes')
            if p.kind == 'capsule':
                if dims[0] < 0 or dims[1] <= 0 or dims[2] != 0:
                    raise ConstructionRefusal('complete capsule(h,r,0) descriptor required')
            elif min(dims) <= 0:
                raise ConstructionRefusal('positive full analytic half dimensions required')
    if not analytic and not presentation:
        raise ConstructionRefusal('full analytic disabled collision descriptor missing')
    return used_nodes


def _check_nodes(snapshot,policy):
    counts = snapshot.inventory_counts
    if type(counts) is not InventoryCounts or type(snapshot.nodes) is not tuple or len(snapshot.nodes)>4096:
        raise ConstructionRefusal('bounded complete node inventory required')
    nodes = {}
    paths = set()
    required = []
    for f in fields(counts): _int(getattr(counts,f.name))
    for node in snapshot.nodes:
        if type(node) is not NodeValue or type(node.flags) is not NodeFlags:
            raise ConstructionRefusal('exact immutable node/flag records required')
        _int(node.node_id,1)
        if node.node_id in nodes: raise ConstructionRefusal('duplicate original node ID')
        if node.parent_id is not None: _int(node.parent_id,1)
        if node.role not in ('ancestor','workspace','geometry','drill_pose','observer'):
            raise ConstructionRefusal('unclassified node inventory')
        _label(node.class_name)
        if type(node.path) is not str or not node.path or len(node.path.encode('utf-8'))>4096 or node.path in paths:
            raise ConstructionRefusal('complete unique bounded original node paths required')
        paths.add(node.path)
        if node.role == 'observer':
            if any(value is not None and type(value) is not Affine for value in (node.local,node.global_transform)):
                raise ConstructionRefusal('actual optional observer affine malformed')
        elif type(node.global_transform) is not Affine or type(node.local) is not Affine:
            raise ConstructionRefusal('complete actual geometry local/global affine records required')
        for f in fields(node.flags):
            value = getattr(node.flags,f.name)
            if f.name != 'script_sha256' and type(value) is not bool:
                raise ConstructionRefusal('exact actual node flags required')
        flag = node.flags
        if flag.unguarded_geometry_writer:
            raise ConstructionRefusal('known unguarded geometry/resource writer in node inventory')
        if node.role != 'observer':
            required.append(node.node_id)
            if node.class_name not in ('Node3D','MeshInstance3D','StaticBody3D','CollisionShape3D','Marker3D'):
                raise ConstructionRefusal('unsupported geometry/ancestor engine class')
            if (flag.top_level or flag.disable_scale or flag.unguarded_geometry_writer or
                    flag.physics_active or flag.animation_active or not flag.geometry_write_guarded):
                raise ConstructionRefusal('unqualified geometry/ancestor mutability')
            if flag.script_sha256 is not None and flag.script_sha256 not in policy.allowed_script_sha256:
                raise ConstructionRefusal('foreign geometry/ancestor script')
        # processing is deliberately permitted: Main/camera/UI stay alive.
        if flag.script_sha256 is not None: _sha(flag.script_sha256)
        nodes[node.node_id] = node
    differences = []
    for node in snapshot.nodes:
        visited = set()
        current = node.node_id
        while current is not None:
            if current in visited or current not in nodes:
                raise ConstructionRefusal('node parent cycle/missing ancestor')
            visited.add(current)
            if node.role != 'observer' and nodes[current].role == 'observer':
                raise ConstructionRefusal('geometry ancestor classified as mere observer')
            current = nodes[current].parent_id
        if node.parent_id is not None and node.role != 'observer':
            parent = nodes[node.parent_id].global_transform
            expected_m = _mul(parent.matrix,node.local.matrix)
            expected_t = tuple(x+y for x,y in zip(_mv(parent.matrix,node.local.translation),parent.translation))
            delta_m = tuple(tuple(node.global_transform.matrix[i][j]-expected_m[i][j] for j in range(3)) for i in range(3))
            delta_t = tuple(x-y for x,y in zip(node.global_transform.translation,expected_t))
            differences.append((node.node_id,delta_m,delta_t))
    audit = snapshot.immutability_audit
    if type(audit) is not ImmutabilityAudit or audit.required_node_ids != tuple(required):
        raise ConstructionRefusal('independent complete geometry/ancestor inventory mismatch')
    _int(audit.document_generation); _int(audit.geometry_generation)
    for node_id in audit.required_node_ids: _int(node_id,1)
    if (audit.writer_inventory_sha256 != policy.writer_inventory_sha256 or
            audit.document_generation != snapshot.freeze_identity.document_generation or
            audit.geometry_generation != snapshot.freeze_identity.geometry_generation):
        raise ConstructionRefusal('frozen writer audit/generation mismatch')
    if (counts.nodes != len(nodes) or counts.required_geometry_nodes != len(required) or
            counts.observer_nodes != len(nodes)-len(required)):
        raise ConstructionRefusal('full node count mismatch')
    return nodes,tuple(differences)


def _corridor(gate,identity):
    q = {'front':(0,0,0,1),'back':(0,1,0,0),'top':(-1,0,0,1),
         'bottom':(1,0,0,1),'right':(0,1,0,1),'left':(0,-1,0,1)}[gate.face]
    centre = tuple(F(x)-F(n)/2 for x,n in zip(gate.center_m,gate.normal))
    return s.Solid(identity,VERSION,'cylinder',centre,(F(.15),F(.15),F(.5)),q)


def _corridor_proofs(scene,layout,margin,context):
    result = []
    spent = 0
    pairs = 0
    for colour,gate in (('blue',layout.blue),('red',layout.red)):
        corridor = _corridor(gate,context+':'+colour)
        certificates = []
        for obj in scene.objects:  # includes rock: empty alignment is stronger than drilling law.
            for part in obj.parts:
                pairs += 1
                if pairs > 60: raise ConstructionRefusal('full static pair budget exhausted')
                proof = pair.certify_pair(corridor,part,margin=margin,context=context,
                    remaining_support_terms=100000-spent)
                spent += proof.support_terms
                certificates.append(proof)
                if proof.status != 'CLEAR':
                    raise ConstructionRefusal('complete inner alignment volume not certified')
        result.append(CorridorProof(corridor,tuple(certificates),spent,'CLEAR'))
    return tuple(result)


def _upper_float(value):
    rounded = float(value)
    if not math.isfinite(rounded): raise ConstructionRefusal('budget float export overflow')
    if F(rounded) < value: rounded = math.nextafter(rounded,math.inf)
    if not math.isfinite(rounded) or F(rounded)<value:
        raise ConstructionRefusal('outward budget export failed')
    return rounded


def _construct_values(snapshot,policy,initial_pose,*,initial_monotonic_ns):
    """Build one complete numerical value result or refuse; no effect/grant.

    The timestamp, labels and hashes are values. They never attest to a retained
    process, clock, original socket or actual authenticated frozen world.
    """
    try:
        return _construct(snapshot,policy,initial_pose,initial_monotonic_ns)
    except ConstructionRefusal:
        raise
    except (ValueError,TypeError,ArithmeticError,KeyError,AttributeError) as exc:
        raise ConstructionRefusal('inconsistent or unsupported numerical value input') from exc


def _construct(snapshot,policy,initial_pose,initial_monotonic_ns):
    if type(snapshot) is not SnapshotValue or type(policy) is not ValuePolicy:
        raise ConstructionRefusal('exact private value DTOs required')
    if type(initial_pose) is not RigidState or initial_pose.speed_m_s != 0:
        raise ConstructionRefusal('explicit zero-speed initial rigid pose required')
    _int(initial_monotonic_ns); _label(policy.run_id)
    if type(policy.guard_m) is not F or policy.guard_m != GUARD:
        raise ConstructionRefusal('selected positive private policy guard required')
    cap = _getter_endpoint_cap(policy)
    if type(policy.allowed_script_sha256) is not tuple:
        raise ConstructionRefusal('immutable approved script inventory required')
    for name in ('document_source_sha256','canonical_source_sha256','catalog_source_sha256',
                 'writer_inventory_sha256','source_bundle_sha256'):
        _sha(getattr(policy,name))
    for digest in policy.allowed_script_sha256: _sha(digest)
    if type(snapshot.assets) is not AssetValues or type(snapshot.drill) is not DrillValue:
        raise ConstructionRefusal('complete actual assets and drill required')
    if type(snapshot.independent_object_manifest) is not tuple or len(snapshot.independent_object_manifest)>30:
        raise ConstructionRefusal('bounded independent object inventory required')
    if type(snapshot.assets.objects) is not tuple or len(snapshot.assets.objects)>30:
        raise ConstructionRefusal('bounded full object witness inventory required')
    if (type(snapshot.assets.presentation_parts) is not tuple or len(snapshot.assets.presentation_parts)>4096 or
            type(policy.presentation_part_ids) is not tuple):
        raise ConstructionRefusal('explicit complete presentation inventory required')
    # This also refuses mutable subrecords, foreign types and excessive exact
    # arithmetic/identity material before geometry construction.
    snapshot_digest = _digest(snapshot)
    policy_digest = _digest(policy)
    ident = snapshot.freeze_identity
    if type(ident) is not FreezeIdentity: raise ConstructionRefusal('freeze values missing')
    _label(ident.freeze_id)
    for name in ('world_epoch','document_generation','geometry_generation',
                 'main_instance_id','document_instance_id','workspace_instance_id','drill_root_instance_id'):
        _int(getattr(ident,name),1 if name.endswith('instance_id') or name=='world_epoch' else 0)
    for name in ('source_bundle_sha256','immutable_payload_sha256','geometry_state_sha256'):
        _sha(getattr(ident,name))
    if ident.source_bundle_sha256 != policy.source_bundle_sha256:
        raise ConstructionRefusal('approved source bundle mismatch')
    comp = snapshot.canonical_companion
    if type(comp) is not CanonicalCompanion or type(comp.normalized_value_bits) is not NormalizedLayout:
        raise ConstructionRefusal('trusted document canonical companion missing')
    if (comp.document_source_sha256 != policy.document_source_sha256 or
            comp.canonical_source_sha256 != policy.canonical_source_sha256):
        raise ConstructionRefusal('trusted document/codec source mismatch')
    if hashlib.sha256(comp.raw_layout_bytes).hexdigest() != _sha(comp.raw_sha256):
        raise ConstructionRefusal('original raw layout digest mismatch')
    normalized,legacy = _parse_raw(comp.raw_layout_bytes,comp.normalized_value_bits.scalar_width)
    for obj in comp.normalized_value_bits.objects:
        if type(obj) is not NormalizedObject: raise ConstructionRefusal('typed normalized object required')
        _int(obj.object_id,1,9007199254740991); _int(obj.priority,1,5)
    if normalized != comp.normalized_value_bits:
        raise ConstructionRefusal('complete actual normalized IEEE values mismatch')
    if (type(comp.canonical_utf8) is not bytes or not 0 < len(comp.canonical_utf8) <=1048576 or
            hashlib.sha256(comp.canonical_utf8).hexdigest()!=_sha(comp.legacy_layout_sha256) or
            legacy != comp.legacy_layout_sha256):
        raise ConstructionRefusal('trusted document canonical byte commitment mismatch')
    comp.canonical_utf8.decode('utf-8','strict')
    # Canonical formatting is the original trusted source's companion assertion;
    # no universal Python printf equivalence or six-decimal truth rounding.
    if snapshot.assets.catalog_source_sha256 != policy.catalog_source_sha256 or snapshot.assets.catalog != policy.catalog:
        raise ConstructionRefusal('independently approved complete asset catalog mismatch')
    catalog = {}
    for entry in policy.catalog:
        if type(entry) is not CatalogEntry or entry.kind in catalog or entry.kind not in (*KINDS,'drill'):
            raise ConstructionRefusal('complete source catalog entries required')
        if type(entry.part_ids) is not tuple or not entry.part_ids or len(entry.part_ids)>4096:
            raise ConstructionRefusal('bounded complete catalog parts required')
        for name in entry.part_ids: _label(name)
        if len(set(entry.part_ids))!=len(entry.part_ids): raise ConstructionRefusal('duplicate catalog part')
        catalog[entry.kind] = entry.part_ids
    if set(catalog)!=set((*KINDS,'drill')):
        raise ConstructionRefusal('all supported source material/drill catalogs required')
    nodes,parent_differences = _check_nodes(snapshot,policy)
    if (ident.main_instance_id not in nodes or ident.workspace_instance_id not in nodes or
            ident.drill_root_instance_id not in nodes):
        raise ConstructionRefusal('original main/workspace/drill reference values absent')
    ws = snapshot.workspace
    if (type(ws) is not WorkspaceValue or ws.units!='m' or ws.transform!=Affine.identity() or
            nodes[ident.workspace_instance_id].global_transform!=ws.transform or
            nodes[ident.workspace_instance_id].role!='workspace' or ws.gates!=normalized.gates):
        raise ConstructionRefusal('canonical identity workspace/metres/gates mismatch')
    parent=nodes[ident.workspace_instance_id].parent_id
    while parent is not None:
        if nodes[parent].global_transform!=Affine.identity():
            raise ConstructionRefusal('unexpected transformed workspace ancestor')
        parent=nodes[parent].parent_id
    gates=tuple(g.Gate(x.face,_decode_bits(x.u_bits,64),_decode_bits(x.v_bits,64)) for x in normalized.gates)
    layout=w.Layout(*gates)
    expected=tuple(ObjectManifest(x.object_id,x.kind,x.priority,catalog[x.kind]) for x in normalized.objects)
    for manifest in snapshot.independent_object_manifest:
        if type(manifest) is not ObjectManifest: raise ConstructionRefusal('typed independent manifest required')
        _int(manifest.object_id,1,9007199254740991); _int(manifest.priority,1,5)
    if snapshot.independent_object_manifest!=expected:
        raise ConstructionRefusal('raw independent object/part/material manifest mismatch')
    if tuple(o.object_id for o in snapshot.assets.objects)!=tuple(x.object_id for x in normalized.objects):
        raise ConstructionRefusal('full ordered raw object inventory mismatch')
    geometry_identity=_digest((DOMAIN,VERSION,snapshot_digest,policy_digest,ident.world_epoch))
    scene_objects=[]; scene_manifest=[]; bounds=[]; mesh_payloads={}; used_part_nodes=set()
    width=normalized.scalar_width
    for raw,obj in zip(normalized.objects,snapshot.assets.objects):
        if type(obj) is not ObjectWitness or obj.root_node_id not in nodes or type(obj.root_affine) is not Affine:
            raise ConstructionRefusal('actual original object root missing')
        _int(obj.object_id,1,9007199254740991); _int(obj.root_node_id,1)
        if nodes[obj.root_node_id].role!='geometry' or nodes[obj.root_node_id].global_transform!=obj.root_affine:
            raise ConstructionRefusal('actual root/affine node correspondence mismatch')
        parent=obj.root_node_id
        while parent is not None and parent!=ident.workspace_instance_id:
            if parent==ident.drill_root_instance_id:
                raise ConstructionRefusal('static numerical obstacle inherits moving drill pose')
            parent=nodes[parent].parent_id
        if parent!=ident.workspace_instance_id: raise ConstructionRefusal('object outside canonical workspace')
        position=tuple(F(_decode_bits(x,width)) for x in raw.position_bits)
        if obj.root_affine.translation!=position:
            raise ConstructionRefusal('actual root translation differs from normalized source position')
        fresh=_validate_parts(obj.parts,catalog[raw.kind],nodes,obj.root_node_id,mesh_payloads)
        for part in obj.parts:
            parent=part.node_id
            while parent is not None and parent!=ident.workspace_instance_id:
                if parent==ident.drill_root_instance_id:
                    raise ConstructionRefusal('static numerical obstacle part inherits moving drill pose')
                parent=nodes[parent].parent_id
        if used_part_nodes.intersection(fresh): raise ConstructionRefusal('geometry part reused between objects')
        used_part_nodes.update(fresh)
        dims=tuple(F(_decode_bits(x,width))/2 for x in raw.size_bits)
        kind='cylinder' if raw.kind=='casing' else 'box'
        base=BASE_HALF[raw.kind]
        affine=_affine_residual(obj.root_affine,base,dims,obj.proposed_quaternion,kind)
        local_bounds=tuple((p.part_id,_part_bound(p,obj.root_affine,kind,base)) for p in obj.parts)
        local=max((x[1] for x in local_bounds),default=F(0))
        norm=_frobenius(obj.root_affine.matrix)
        total=affine+norm*local
        bounds.append(ObjectBound(raw.object_id,affine,local,norm,total,local_bounds))
        oid='editor-object:'+str(raw.object_id)
        piece=oid+':nominal-envelope:v1'
        solid=s.Solid(piece,VERSION,kind,position,dims,obj.proposed_quaternion)
        scene_manifest.append((oid,(piece,)))
        scene_objects.append(s.SceneObject(oid,raw.kind,(solid,),superhard=False))
    drill=snapshot.drill
    _int(drill.root_node_id,1)
    if (drill.root_node_id!=ident.drill_root_instance_id or nodes[drill.root_node_id].role!='drill_pose' or
            drill.root_affine!=nodes[drill.root_node_id].global_transform or drill.part_ids!=catalog['drill']):
        raise ConstructionRefusal('original complete drill/root correspondence missing')
    fresh=_validate_parts(drill.parts,drill.part_ids,nodes,drill.root_node_id,mesh_payloads)
    if used_part_nodes.intersection(fresh): raise ConstructionRefusal('drill and obstacle share geometry node')
    used_part_nodes.update(fresh)
    present=_validate_parts(snapshot.assets.presentation_parts,policy.presentation_part_ids,nodes,
        ident.main_instance_id,mesh_payloads,presentation=True)
    if used_part_nodes.intersection(present): raise ConstructionRefusal('presentation and numeric object parts overlap')
    all_parts=tuple(p for obj in snapshot.assets.objects for p in obj.parts)+drill.parts+snapshot.assets.presentation_parts
    covered_mesh_nodes={p.node_id for p in all_parts if p.kind=='mesh'}
    required_mesh_nodes={n.node_id for n in snapshot.nodes if n.class_name=='MeshInstance3D'}
    if covered_mesh_nodes!=required_mesh_nodes:
        raise ConstructionRefusal('complete original MeshInstance3D surface inventory missing/unexpected')
    covered_shape_nodes={p.node_id for p in all_parts if p.kind!='mesh'}
    required_shape_nodes={n.node_id for n in snapshot.nodes if n.class_name=='CollisionShape3D'}
    if covered_shape_nodes!=required_shape_nodes:
        raise ConstructionRefusal('complete original analytic collision descriptor inventory missing/unexpected')
    counts=snapshot.inventory_counts
    if (counts.objects!=len(normalized.objects) or counts.surfaces!=len(mesh_payloads) or
            counts.unique_vertices!=sum(len(x[0]) for x in mesh_payloads.values()) or
            counts.indices!=sum(len(x[1]) for x in mesh_payloads.values()) or
            not 0<=counts.surfaces<=64 or not 0<=counts.unique_vertices<=1000000 or not 0<=counts.indices<=3000000):
        raise ConstructionRefusal('complete unique surface/vertex/index inventory mismatch')
    envelope=w.Envelope(.4,.12,.52,geometry_identity,False)
    model=s.CapsuleModel('full-drill:'+geometry_identity,VERSION,F(envelope.half_segment_m),
        F(envelope.radius_m),F(envelope.pivot_radius_m))
    body=(model.half_segment,model.radius,F(0))
    drill_upper=max((_part_bound(p,drill.root_affine,'capsule',body) for p in drill.parts),default=F(0))
    obstacle_upper=max((x.total_upper_m for x in bounds),default=F(0))
    numeric=GUARD+cap; asset=GUARD+drill_upper; obstacle=GUARD+obstacle_upper
    total=numeric+asset+obstacle
    additional=_upper_float(total)
    source=geometry_identity+':'+policy_digest
    if cap:
        source += ':endpoint-affine-set-v1:'+str(cap.numerator)+'/'+str(cap.denominator)
    budget=GeometryBudget(numeric,asset,obstacle,source)
    scene=s.Scene(geometry_identity,VERSION,tuple(scene_manifest),tuple(scene_objects))
    corridors=_corridor_proofs(scene,layout,total,geometry_identity)
    sweep=s.Sweep(model,initial_pose.position_m,initial_pose.position_m,initial_pose.orientation_xyzw,
        0,0,0,s.ErrorBounds(0,0,numeric,asset,obstacle,budget.source))
    initial_scene=s.certify_scene(sweep,scene)
    if initial_scene.status!='CLEAR': raise ConstructionRefusal('full initial capsule scene clearance not certified')
    context=passage.RunContext(policy.run_id,geometry_identity,ident.world_epoch,layout,envelope,
        'value-only:'+ident.freeze_id)
    initialized=passage.initialize(context,initial_pose,gc.ErrorBounds(0.,0.,additional),
        pose_revision=0,monotonic_ns=initial_monotonic_ns,error_budget_reference=budget.source)
    if initialized.status!='SAFE' or initialized.state is None:
        raise ConstructionRefusal('strict whole-body legal outside-blue initializer not certified')
    if F(initialized.state.errors.additional_margin_m)<total:
        raise ConstructionRefusal('exact exported budget partition not covered')
    derivation=BudgetDerivation(DOMAIN,GUARD,drill_upper,tuple(bounds),obstacle_upper,
        numeric,asset,obstacle,additional,policy_digest,parent_differences,
        ('GPU/render-frame arithmetic and presentation correspondence remain unqualified outside this exact finite-affine model',
         'later CPU/GPU evaluation beyond recorded getter values has no invented zero bound',
         'ADC/causal sensors and AI/model/provider qualification remain separate acceptance evidence',
         'mesh topology/closed visual solids and active physics shape-margin semantics remain unqualified',
         'initial position/angle errors0 describe exactly encoded numerical initial pose only; CP carries later numerical export errors'),
        getter_endpoint_cap_m=cap)
    return WorldValues(snapshot_digest,geometry_identity,scene,model,layout,envelope,budget,
        initialized.state,derivation,corridors,initial_scene)


__all__ = []

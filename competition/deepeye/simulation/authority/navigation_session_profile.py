"""Explicit finite navigation revision; no authority or hardware acceptance."""
from dataclasses import dataclass
import hashlib
import json

_SOURCE_PINS = (('root_source_book','c83f35ad9b6985f8949e899b195898832b88cbd4ff8a314979c08a412b271e4e'),
                ('_actor_source_custody','0cb3438533a7fec25ac4dc7c0072de7c6de7e3acff5a84ecaf7d1636614ed671'),
                ('original_world_actor_link','38e731c392f41b0b9d3b1852bea49c081f8398501cab996544ae36adbac108fb'),
                ('_world_loop','ac9d07ea8941665d8cb1bfb83425941d98215a53bfcfed78c3d6836fc092a763'))
_VALUES = ('DEEPEYE-NAV-ADJACENT-180S-V3', 180_000_000_000,
           1_000_000_000, 1001, 2048, 16, 16, 128, 293, 16, 50,
           4_194_304, 2048, 3000, 100_000_000, 500_000_000, 32768, 2000, 24, .05, _SOURCE_PINS)
_SHA = hashlib.sha256(json.dumps(('DEEPEYE-TYPED-NAVIGATION-PROFILE-V3', *_VALUES),
    separators=(',', ':')).encode('ascii')).hexdigest()

_LONG_VALUES = (_VALUES[0].replace('ADJACENT','FAST-LONGTTL'), *_VALUES[1:13], 12000, *_VALUES[14:])
_LONG_SHA = hashlib.sha256(json.dumps(('DEEPEYE-TYPED-FAST-LONGTTL-NAVIGATION-V1', *_LONG_VALUES), separators=(',', ':')).encode('ascii')).hexdigest()

_ROUTE_VALUES = ('DEEPEYE-NAV-ROUTE-LONGTTL-600S-V1',600_000_000_000,
    1_000_000_000,1001,4096,64,64,512,1172,64,194,16_777_216,8192,
    12000,100_000_000,500_000_000,131072,2000,24,.05,_SOURCE_PINS)
_ROUTE_SHA = hashlib.sha256(json.dumps(('DEEPEYE-TYPED-ROUTE-LONGTTL-NAVIGATION-V1',*_ROUTE_VALUES),separators=(',',':')).encode('ascii')).hexdigest()

@dataclass(frozen=True)
class NavigationSessionProfile:
    profile_id: str
    duration_ns: int
    sample_period_ns: int
    max_source_records: int
    max_book_records: int
    max_commands: int
    max_scans: int
    capture_polls: int
    total_status_reads: int
    status_phases: int
    max_requests: int
    max_reply_bytes: int
    max_io: int
    max_command_ttl_ms: int
    max_step_ns: int
    reserve_source_ipc_ns: int
    max_trace_io: int
    max_trace_scan_io: int
    max_public_items: int
    exit_clearance_margin_m: float
    source_pins: tuple
    sha256: str

    def __post_init__(self):
        values = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != 'sha256')
        if (type(self.profile_id) is not str or (values, self.sha256) not in ((_VALUES, _SHA), (_LONG_VALUES, _LONG_SHA), (_ROUTE_VALUES, _ROUTE_SHA))
                or any(type(x) is not int for x in values[1:-2])
                or type(self.exit_clearance_margin_m) is not float
                or type(self.source_pins) is not tuple
                or type(self.sha256) is not str):
            raise ValueError('exact typed/hash-bound navigation revision required')


NAV_ADJACENT_180S = NavigationSessionProfile(*_VALUES, _SHA)
NAV_FAST_LONGTTL_180S = NavigationSessionProfile(*_LONG_VALUES, _LONG_SHA)
NAV_ROUTE_LONGTTL_600S_V1 = NavigationSessionProfile(*_ROUTE_VALUES, _ROUTE_SHA)


def validate_profile(value):
    if value is not None:
        if type(value) is not NavigationSessionProfile:
            raise TypeError('typed navigation revision or default None required')
        value.__post_init__()
    return value


def to_wire(value):
    validate_profile(value)
    return None if value is None else dict(profile_id=value.profile_id, sha256=value.sha256)


def from_wire(value):
    for selected in (NAV_ADJACENT_180S, NAV_FAST_LONGTTL_180S, NAV_ROUTE_LONGTTL_600S_V1):
        if type(value) is dict and value == to_wire(selected):
            return selected
    raise ValueError('exact navigation wire identity required')


def duration_ns(value):
    validate_profile(value)
    return 10_000_000_000 if value is None else value.duration_ns


def prospective_io(value):
    validate_profile(value)
    if value is None:
        raise ValueError('explicit navigation revision required')
    return 42 + 78*value.max_commands + 2*value.capture_polls + 15*value.status_phases


def rolling_refs(value, observations, actions, current_observation):
    """Select original refs only; caller retains the complete private journals."""
    validate_profile(value)
    if value is None or type(observations) is not tuple or type(actions) is not tuple:
        raise ValueError('explicit navigation and immutable original ref sequences required')
    if len(observations)>value.max_source_records or len(actions)>value.max_book_records:
        raise ValueError('original journal limits exceeded')
    entries=[]
    for kind, sequence in enumerate((observations, actions)):
        for order, item in enumerate(sequence):
            if (type(item) is not tuple or len(item)!=2 or type(item[0]) is not int
                    or not 0<=item[0]<(1<<63)):
                raise ValueError('actual bounded observed time/reference required')
            entries.append((item[0],kind,order,item[1]))
    selected=sorted(entries,key=lambda x:x[:3])[-value.max_public_items:]
    public_observations=tuple(x[3] for x in selected if x[1]==0)
    if not any(item is current_observation for item in public_observations):
        raise ValueError('latest original observation fell outside rolling public window')
    return public_observations,tuple(x[3] for x in selected if x[1]==1)


def is_longttl(value):
    validate_profile(value)
    return value is NAV_FAST_LONGTTL_180S or value is NAV_ROUTE_LONGTTL_600S_V1


def longttl_for_g05(policy):
    """Return the exact explicit demo identity, never inferred from a duration."""
    if policy is None:
        return None
    from .g05_csr_channels_v1 import G05CsrPolicy
    from .demo30h_ai_em3_profile_v2 import DemoEM3AIProfile, NAV_ENTRY_LONG_TTL_V4, NAV_ROUTE_LONGTTL_V5
    if type(policy) is not G05CsrPolicy:
        raise TypeError('exact G05 policy required')
    descriptor = policy.demo_ai_profile
    if type(descriptor) is DemoEM3AIProfile and descriptor.navigation_profile is NAV_ROUTE_LONGTTL_V5:
        policy.check()
        return NAV_ROUTE_LONGTTL_600S_V1
    if type(descriptor) is DemoEM3AIProfile and descriptor.navigation_profile is NAV_ENTRY_LONG_TTL_V4:
        policy.check()
        return NAV_FAST_LONGTTL_180S
    return None

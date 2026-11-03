"""Explicit numerical demo horizon; no clock, motion or authority grant.

None preserves the original 10ms domain. Only the fixed typed/hash-committed
100ms profile and explicit500ms profile are accepted; collision, budget and final real-time fences remain
the caller's existing obligations.
"""
from dataclasses import dataclass
import hashlib
import json

from .kinematics import MAX_DT_NS

DOMAIN = 'DEEPEYE-EXPLICIT-DEMO-MOTION-HORIZON-V1'
_ID = 'DEEPEYE-DEMO-100MS-HORIZON-V1'
_MAX = 100_000_000
_SHA = hashlib.sha256(json.dumps((DOMAIN,_ID,_MAX),ensure_ascii=False,
    separators=(',',':')).encode('utf-8')).hexdigest()
_ID500 = 'DEEPEYE-DEMO-500MS-HORIZON-V1'
_MAX500 = 500_000_000
_SHA500 = '6dd2a1cb71f89915c3576be84a585771c701ca6e63501f93a64658d557dc8960'
_MARKER = ':motion-horizon-v1:'


@dataclass(frozen=True)
class MotionHorizonProfile:
    profile_id: str
    max_dt_ns: int
    sha256: str

    def __post_init__(self):
        if (type(self.profile_id) is not str or type(self.max_dt_ns) is not int
                or type(self.sha256) is not str or
                (self.profile_id,self.max_dt_ns,self.sha256) not in
                ((_ID,_MAX,_SHA),(_ID500,_MAX500,_SHA500))):
            raise ValueError('only exact typed/hash-bound100ms or500ms demo horizons are supported')


DEMO_100MS = MotionHorizonProfile(_ID,_MAX,_SHA)
DEMO_500MS = MotionHorizonProfile(_ID500,_MAX500,_SHA500)


def validate_profile(profile):
    if profile is not None:
        if type(profile) is not MotionHorizonProfile:
            raise TypeError('explicit immutable MotionHorizonProfile or default None required')
        profile.__post_init__()
        if profile.profile_id == _ID500 and profile is not DEMO_500MS:
            raise ValueError('exact selected500ms singleton required')
    return profile


def max_dt_ns(profile):
    validate_profile(profile)
    return MAX_DT_NS if profile is None else profile.max_dt_ns


def commitment(profile):
    validate_profile(profile)
    return None if profile is None else (profile.profile_id,profile.max_dt_ns,profile.sha256)


def require_reference(reference,profile):
    validate_profile(profile)
    if type(reference) is not str or not reference.strip():
        raise ValueError('explicit nonempty budget reference required')
    if profile is None:
        if _MARKER in reference:
            raise ValueError('default motion cannot consume a demo-profile budget reference')
    elif reference.count(_MARKER) != 1 or not reference.endswith(_MARKER+profile.sha256):
        raise ValueError('motion profile and original budget reference must carry the same SHA')
    return reference


def bind_reference(reference,profile):
    validate_profile(profile)
    if profile is None or (type(reference) is str and _MARKER in reference):
        return require_reference(reference,profile)
    return require_reference(reference+_MARKER+profile.sha256,profile)

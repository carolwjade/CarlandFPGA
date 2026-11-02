"""Explicit numerical demo horizon; no clock, motion or authority grant.

None preserves the original 10ms domain. Only the fixed typed/hash-committed
100ms profile is accepted; collision, budget and final real-time fences remain
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
_MARKER = ':motion-horizon-v1:'


@dataclass(frozen=True)
class MotionHorizonProfile:
    profile_id: str
    max_dt_ns: int
    sha256: str

    def __post_init__(self):
        if (type(self.profile_id) is not str or self.profile_id != _ID
                or type(self.max_dt_ns) is not int or self.max_dt_ns != _MAX
                or type(self.sha256) is not str or self.sha256 != _SHA):
            raise ValueError('only the exact typed/hash-bound 100ms demo horizon is supported')


DEMO_100MS = MotionHorizonProfile(_ID,_MAX,_SHA)


def validate_profile(profile):
    if profile is not None:
        if type(profile) is not MotionHorizonProfile:
            raise TypeError('explicit immutable MotionHorizonProfile or default None required')
        profile.__post_init__()
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

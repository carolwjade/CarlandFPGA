"""Explicit fixed four-cycle protocol policy; no hardware or authority grant."""
from dataclasses import dataclass
import hashlib
import json
from ...simulation.authority import navigation_session_profile as navigation

_ID='DEEPEYE-DEMO-FOUR-CYCLE-V1'
_VALUES=(_ID,4,4,16,61,4,14,10_000_000_000,450)
_SHA=hashlib.sha256(json.dumps(('DEEPEYE-EXPLICIT-FOUR-CYCLE-PROFILE-V1',*_VALUES),
    separators=(',',':')).encode('ascii')).hexdigest()

@dataclass(frozen=True)
class DemoFourCycleProfile:
    profile_id:str
    max_commands:int
    max_scans:int
    capture_polls:int
    total_status_reads:int
    status_phases:int
    max_requests:int
    duration_ns:int
    max_io:int
    sha256:str
    def __post_init__(self):
        values=(self.profile_id,self.max_commands,self.max_scans,self.capture_polls,
            self.total_status_reads,self.status_phases,self.max_requests,self.duration_ns,self.max_io)
        if (type(self.profile_id) is not str or any(type(x) is not int for x in values[1:])
                or values!=_VALUES or type(self.sha256) is not str or self.sha256!=_SHA):
            raise ValueError('only the exact typed/hash-bound four-cycle demo policy is supported')

DEMO_FOUR_CYCLE=DemoFourCycleProfile(*_VALUES,_SHA)

def validate_profile(value):
    if value is not None:
        if type(value) is navigation.NavigationSessionProfile:
            return navigation.validate_profile(value)
        if type(value) is not DemoFourCycleProfile:raise TypeError('typed four-cycle policy or default None required')
        value.__post_init__()
    return value

def to_wire(value):
    validate_profile(value)
    return None if value is None else dict(profile_id=value.profile_id,sha256=value.sha256)

def from_wire(value):
    if type(value) is dict and value in (navigation.to_wire(navigation.NAV_ADJACENT_180S), navigation.to_wire(navigation.NAV_FAST_LONGTTL_180S)):
        return navigation.from_wire(value)
    if type(value) is not dict or value!=to_wire(DEMO_FOUR_CYCLE):
        raise ValueError('exact four-cycle wire policy identity required')
    return DEMO_FOUR_CYCLE

def command_cap(value):
    validate_profile(value);return 2 if value is None else value.max_commands

def scan_cap(value):
    validate_profile(value);return 2 if value is None else value.max_scans

def request_cap(value):
    validate_profile(value);return 10 if value is None else value.max_requests

def validate_caps(value,*,max_commands,max_polls,duration_ns,max_io):
    validate_profile(value)
    if is_navigation(value):
        if (type(max_commands) is not int or max_commands!=16
                or type(max_polls) is not int or max_polls!=128
                or type(duration_ns) is not int or duration_ns!=value.duration_ns
                or type(max_io) is not int or not navigation.prospective_io(value)<=max_io<=2048):
            raise ValueError('navigation requires16 commands/128 capture polls/180s and complete prospective I/O capacity')
        return navigation.prospective_io(value)
    if not (type(max_commands) is int and 1<=max_commands<=command_cap(value)
            and type(max_polls) is int and 4<=max_polls<=64
            and type(duration_ns) is int and 0<duration_ns<=10_000_000_000
            and type(max_io) is int and 1<=max_io<=450):
        raise ValueError('explicit finite session caps required')
    if value is not None and (max_commands!=4 or max_polls!=16 or max_io<438):
        raise ValueError('four-cycle demo requires four commands,16 capture polls and438..450 G05 I/Os')
    return 102+76*max_commands+2*max_polls

def is_navigation(value):
    validate_profile(value)
    return type(value) is navigation.NavigationSessionProfile

def duration_cap(value):
    return value.duration_ns if is_navigation(value) else 10_000_000_000

def poll_cap(value):
    return 128 if is_navigation(value) else 64

def io_cap(value):
    return 2048 if is_navigation(value) else 450

def reply_cap(value):
    return 4_194_304 if is_navigation(value) else 1_048_576

def status_phase_cap(value):
    return 16 if is_navigation(value) else 4

def trace_io_cap(value):
    return value.max_trace_io if is_navigation(value) else 5000

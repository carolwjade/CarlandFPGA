"""Minimal live-demo canonical law; no motion grant or collision proof.

Root's authenticated native installer must apply full-body sweep/portal safety
before accepting each actual frame. This module never touches UI, board, source
truth, or original STEP/custody. Formal geometry qualification remains not_run.
"""
from dataclasses import dataclass
from fractions import Fraction
import hashlib,json,math
from competition.deepeye.integration import motion
from competition.deepeye.simulation.authority.motion.kinematics import RigidState,_pose

CONTRACT_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
SCHEMA='deepeye_live_canonical_law_v1'
ACCELERATION_M_S2=.25

def _uint(x,minimum=0):
    if type(x) is not int or not minimum<=x<(1<<63):raise ValueError('strict uint63 required')
    return x

def _label(x):
    if type(x) is not str or not 1<=len(x)<=128 or not x.isascii():raise ValueError('bounded identity required')
    return x

def _raw(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')

@dataclass(frozen=True)
class Target:
    action:int
    yaw_q:int
    pitch_q:int
    speed_code:int
    duration_ms:int
    def __post_init__(self):
        if any(type(x) is not int for x in (self.action,self.yaw_q,self.pitch_q,self.speed_code,self.duration_ms)):raise ValueError('strict integer target fields required')
        if type(self.action) is not int or self.action not in (0,1):raise ValueError('action must be STOP0 or DRIVE1')
        if self.action==0:
            if (self.yaw_q,self.pitch_q,self.speed_code,self.duration_ms)!=(0,0,0,0):raise ValueError('exact STOP target required')
        elif type(self.duration_ms) is not int or not 1<=self.duration_ms<=12000 or not 1<=self.speed_code<=20:
            raise ValueError('actual FAST target duration/speed outside physical limits')
        motion.validate('fast_9600',self.speed_code,self.yaw_q,self.pitch_q)
    @classmethod
    def from_actual_capture_target(cls,target):
        if type(target) is not dict or set(target)!={'action','yaw_q','pitch_q','speed_code','duration_ms'}:raise ValueError('exact measured target shape')
        # Shape/mapping only; caller must supply the original captured FPGA fact.
        return cls(**target)

@dataclass(frozen=True)
class LiveLaw:
    world_epoch:str
    segment_id:str
    control_seq:int
    start:RigidState
    target:Target
    parent_segment_id:str|None=None
    @classmethod
    def create(cls,world_epoch,segment_id,control_seq,start,target,*,parent_segment_id=None):
        _label(world_epoch);_label(segment_id);_uint(control_seq,1)
        if type(start) is not RigidState or type(target) is not Target:raise TypeError('canonical start and exact target required')
        if parent_segment_id is not None:_label(parent_segment_id)
        return cls(world_epoch,segment_id,control_seq,start,target,parent_segment_id)
    @property
    def mapped(self):return motion.validate('fast_9600',self.target.speed_code,self.target.yaw_q,self.target.pitch_q)
    @property
    def ramp_ns(self):
        delta=abs(Fraction(self.mapped.target_speed_m_s)-Fraction(self.start.speed_m_s))*4*10**9
        return (delta.numerator+delta.denominator-1)//delta.denominator
    def distance_speed(self,elapsed_ns):
        _uint(elapsed_ns)
        # Same acceleration/ramp law as CanonicalPath; no span-end clamp/STOP.
        v0=Fraction(self.start.speed_m_s);vt=Fraction(self.mapped.target_speed_m_s)
        t=Fraction(elapsed_ns,10**9);a=Fraction(1 if vt>v0 else -1 if vt<v0 else 0,4)
        ramp=min(t,4*abs(vt-v0))
        return v0*ramp+a*ramp*ramp/2+vt*(t-ramp),(v0+a*ramp if t<4*abs(vt-v0) else vt)
    def sample(self,elapsed_ns):
        distance,speed=self.distance_speed(elapsed_ns)
        return _pose(self.start,self.mapped,float(distance),float(speed))
    def native_packet(self,*,host_start_qpc_ns,grant_deadline_qpc_ns,clock_map_id):
        _uint(host_start_qpc_ns);_uint(grant_deadline_qpc_ns);_label(clock_map_id)
        if grant_deadline_qpc_ns<=host_start_qpc_ns:raise ValueError('real board grant already expired')
        mapped=self.mapped;delta=mapped.target_speed_m_s-self.start.speed_m_s
        span=dict(offset_ns='0',dt_ns=str(grant_deadline_qpc_ns-host_start_qpc_ns),
            start_position_m=list(self.start.position_m),start_orientation_xyzw=list(self.start.orientation_xyzw),
            start_speed_m_s=self.start.speed_m_s,target_speed_m_s=mapped.target_speed_m_s,
            acceleration_m_s2=.25 if delta>0 else -.25 if delta<0 else 0.,ramp_ns=str(self.ramp_ns),
            yaw_curvature_per_m=mapped.curvature_yaw_per_m,pitch_curvature_per_m=mapped.curvature_pitch_per_m,
            proof_sha256=None)
        packet=dict(schema=SCHEMA,requirements_sha256=CONTRACT_SHA256,world_epoch=self.world_epoch,
            segment_id=self.segment_id,parent_segment_id=self.parent_segment_id,control_seq=str(self.control_seq),
            host_start_qpc_ns=str(host_start_qpc_ns),clock_map_id=clock_map_id,
            duration_ns=str(grant_deadline_qpc_ns-host_start_qpc_ns),drive_deadline_qpc_ns=str(grant_deadline_qpc_ns),
            spans=[span],hold_last_target=True,stop_on_span_boundary=False,
            normal_update='continue same actual captured direction/speed until actual successor; real safety deadlines still apply',
            brake_deceleration_m_s2=.25,formal_geometry_proof='not_run',runtime_volume_guard_required=True)
        packet['law_sha256']=hashlib.sha256(_raw(packet)).hexdigest()
        return packet

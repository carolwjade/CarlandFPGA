"""810 explicit live-demo advice mapping. Pure suggestion, never motion grant.

No truth/route/goal lookup, clock read, IO, model invocation or board effect.
Root must independently check original advice freshness/epoch before this call,
then consume only actual measured PWM through791/798/native volume guards.
"""
from fractions import Fraction
import math
from competition.deepeye.integration.motion import validate,curvature_limit_squared

CONTRACT_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
PROFILE='continuous_command_map_810_horizon035_v1'
STEERING_HORIZON_M=0.35

def _need(ok,reason):
    if not ok:raise ValueError(reason)

def _number(v,low,high):
    _need(type(v) in (int,float) and math.isfinite(v) and low<=v<=high,'FINITE_SCALAR_BOUND')
    return float(v)

def _zero(reason):return dict(yaw_q=0,pitch_q=0,speed_code=0,reason=reason)

def _body_direction(world,quaternion):
    _need(type(world) in (list,tuple) and len(world)==3,'DIRECTION3')
    d=tuple(_number(v,-1.000001,1.000001) for v in world)
    dn=math.sqrt(sum(v*v for v in d));_need(abs(dn-1.0)<=1e-5,'UNIT_WORLD_DIRECTION')
    d=tuple(v/dn for v in d)
    _need(type(quaternion) in (list,tuple) and len(quaternion)==4,'QUATERNION4')
    q=tuple(_number(v,-1.000001,1.000001) for v in quaternion)
    qn=math.sqrt(sum(v*v for v in q));_need(abs(qn-1.0)<=1e-5,'UNIT_OWN_ORIENTATION')
    x,y,z,w=(v/qn for v in q)
    # World -> CURRENT body using inverse unit quaternion. Never reuse an old
    # source-frame yaw_delta after the actual native pose has moved/turned.
    ux,uy,uz=-x,-y,-z
    cross=(uy*d[2]-uz*d[1],uz*d[0]-ux*d[2],ux*d[1]-uy*d[0])
    cross2=(uy*cross[2]-uz*cross[1],uz*cross[0]-ux*cross[2],ux*cross[1]-uy*cross[0])
    return tuple(d[i]+2*w*cross[i]+2*cross2[i] for i in range(3))

def command_for_advice(advice,current_native,operatorcap,paused):
    """Return exact {yaw_q,pitch_q,speed_code,reason}; default paths unchanged.

    current_native is794's raw public state, not798's {native,host} wrapper.
    advice is797's actual completed ADVISE/STOP dictionary. World direction is
    authoritative for this calculation; old source-frame yaw/pitch deltas are
    diagnostic. Entry stays straight until whole-body phase INSIDE.
    """
    _need(type(advice) is dict and type(current_native) is dict,'PLAIN_RECORDS')
    _need(type(paused) is bool,'PAUSE_BOOL')
    cap=_number(operatorcap,0.0,0.25)
    if paused:return _zero('operator_paused')
    if cap==0:return _zero('operator_cap_zero')
    _need(advice.get('status') in ('ADVISE','STOP'),'ACTUAL_ADVICE_STATUS')
    if advice['status']=='STOP':return _zero('ai_stop')
    if current_native.get('fault',''):
        return _zero('native_fault')
    if current_native.get('ready') is not True:return _zero('native_not_ready')
    phase=current_native.get('phase')
    _need(phase in ('INITIAL_OUTSIDE','ENTRY_CROSSING','INSIDE','EXIT_CROSSING','ARRIVED'),'PUBLIC_PHASE')
    limit=_number(advice.get('speed_limit_m_s'),0.0,0.25)
    # FAST step is exactly1/80m/s. Quantize downward with exact float-rational
    # comparison: a positive minimum code is never manufactured above a limit.
    allowed=min(Fraction(limit),Fraction(cap),Fraction(1,4))
    code=min(20,(allowed*80).numerator//(allowed*80).denominator)
    if code==0:return _zero('limit_below_min_positive_code')
    mapped=validate('fast_9600',code,0,0)
    _need(Fraction(code,80)<=Fraction(limit) and Fraction(code,80)<=Fraction(cap),'NO_SPEED_UPWARD_ROUNDING')
    if phase in ('INITIAL_OUTSIDE','ENTRY_CROSSING'):
        return dict(yaw_q=0,pitch_q=0,speed_code=code,reason='entry_straight_ai_speed')
    direction=advice.get('target_direction_world')
    if 'direction_world' in advice:
        other=advice['direction_world']
        _need(type(other) in (list,tuple) and len(other)==3 and
              type(direction) in (list,tuple) and len(direction)==3 and
              all(abs(_number(a,-1.000001,1.000001)-_number(b,-1.000001,1.000001))<=1e-9 for a,b in zip(direction,other)),
              'CONSISTENT_ACTUAL_WORLD_DIRECTION')
    dx,dy,dz=_body_direction(direction,current_native.get('orientation_xyzw'))
    lateral=math.hypot(dx,dy)
    if lateral<=1e-14:
        if dz<0:return _zero('antipodal_direction_has_no_unique_turn')
        return dict(yaw_q=0,pitch_q=0,speed_code=code,reason='advice_forward')
    angle=math.atan2(lateral,dz)
    curvature=min(0.5,angle/STEERING_HORIZON_M)
    factor=curvature*mapped.target_speed_m_s*180000/math.pi/lateral
    yaw=math.trunc(dx*factor);pitch=math.trunc(dy*factor)
    rom=curvature_limit_squared('fast_9600',code)
    # Integer-only final contraction preserves signs and never increases either
    # component. The loop is intrinsically bounded by |yaw|+|pitch|<=30000.
    while yaw*yaw+pitch*pitch>rom:
        if abs(yaw)>=abs(pitch):yaw-=1 if yaw>0 else -1
        else:pitch-=1 if pitch>0 else -1
    validate('fast_9600',code,yaw,pitch)
    return dict(yaw_q=yaw,pitch_q=pitch,speed_code=code,reason='advice_horizon_0p35m')

"""Public gate-frame approach advice, without motion authority or hidden geometry.

Spatial demand is recomputed from actual lateral/heading error, curvature and
pose age. It is an engineering acquisition/feasibility estimate, not a proof
that an unknown obstacle corridor is clear. Native full-volume Guard is required.
"""
from __future__ import annotations
import copy
import math
from dataclasses import dataclass

REQUIREMENTS_SHA256 = '2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
PROFILE_ID = 'public_gate_curvature_approach_984_v1'


def number(v):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v):
        raise ValueError('finite ordinary number required')
    return float(v)


def vector(v,n=3):
    if not isinstance(v,(list,tuple)) or len(v)!=n:
        raise ValueError('fixed public/own vector required')
    return [number(x) for x in v]


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def unit(v):
    length=math.hypot(*v)
    if length<1e-12:raise ValueError('nonzero direction required')
    return [x/length for x in v]


def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def rotate(q,v):
    q=vector(q,4)
    if abs(dot(q,q)-1)>1e-6:raise ValueError('actual unit quaternion required')
    t=[2*x for x in cross(q[:3],v)];c=cross(q[:3],t)
    return [v[i]+q[3]*t[i]+c[i] for i in range(3)]


def ns(v):
    if type(v) is int and v>=0:return v
    if type(v) is str and v.isascii() and v.isdecimal():return int(v)
    raise ValueError('original QPC nanoseconds required')


@dataclass(frozen=True)
class GateApproachProfile:
    capsule_half_length_m: float=.4
    capsule_radius_m: float=.12
    lateral_margin_share: float=.5
    tracking_horizon_m: float=.35
    reference_curvature_share: float=.8

    def __post_init__(self):
        if (self.capsule_half_length_m!=.4 or self.capsule_radius_m!=.12
                or not .25<=number(self.lateral_margin_share)<=.75
                or self.tracking_horizon_m!=.35
                or not .5<=number(self.reference_curvature_share)<=1.):
            raise ValueError('actual capsule dimensions and bounded dimensionless gains required')


def gate_geometry(*,position_m,forward_world,exit_center_m,exit_normal_world,
                  gate_radius_m,speed_m_s,pose_age_s,curvature_limit_per_m,
                  workspace_planes,profile=None):
    """Pure proposal. Planes mean dot(position,normal_world)<=offset_m.

    All vectors transform equivariantly under a common rigid transform. No world
    axis, obstacle, route waypoint or fixed metre-based return interval is used.
    """
    cfg=GateApproachProfile() if profile is None else profile
    if type(cfg) is not GateApproachProfile:raise ValueError('explicit approach profile required')
    p,f,g,n=vector(position_m),unit(vector(forward_world)),vector(exit_center_m),unit(vector(exit_normal_world))
    radius,v,age,k=map(number,(gate_radius_m,speed_m_s,pose_age_s,curvature_limit_per_m))
    if radius!=.25 or not 0<=v<=.25 or not 0<=age<=.25 or not 0<=k<=.5:
        raise ValueError('real revision2 radius/FAST speed/age/curvature bounds required')
    h,b=cfg.capsule_half_length_m,cfg.capsule_radius_m
    delta=[x-y for x,y in zip(p,g)];remaining=-dot(delta,n)
    lateral=[d+remaining*a for d,a in zip(delta,n)]
    cos_heading=max(-1.,min(1.,dot(f,n)));theta=math.acos(cos_heading)
    projected_axis=[x-cos_heading*a for x,a in zip(f,n)]
    projection=max(math.hypot(*[e+h*x for e,x in zip(lateral,projected_axis)]),
                   math.hypot(*[e-h*x for e,x in zip(lateral,projected_axis)]))+b
    travel=v*age
    uncertainty=travel+h*math.sin(min(math.pi/2,k*travel))
    clearance=radius-b-uncertainty
    result=dict(profile_id=PROFILE_ID,authorization='none',status='UNSOLVED',reason='',
        remaining_m=remaining,lateral_error_world=lateral,lateral_error_m=math.hypot(*lateral),
        heading_error_rad=theta,capsule_projection_m=projection,
        capsule_projection_with_age_m=projection+uncertainty,
        age_distance_allowance_m=uncertainty,available_aperture_clearance_m=clearance,
        aperture_ready=False,workspace_checked=False,global_obstacle_route_solved=False,
        native_full_volume_guard_required=True,formal_all29='not_run',direction_world=list(n))
    def unsolved(reason):result['reason']=reason;return result
    if clearance<=0:return unsolved('pose_age_consumes_aperture_margin')
    rho=math.hypot(*lateral);tol=clearance*cfg.lateral_margin_share
    angle_tol=math.asin(min(1.,(clearance-tol)/h))
    ready=(projection+uncertainty<=radius and cos_heading>0)
    result.update(aperture_ready=ready,lateral_tolerance_m=tol,heading_tolerance_rad=angle_tol)
    if theta>=math.pi/2:return unsolved('heading_requires_unplanned_turn_or_reverse')
    if k==0 and (theta>1e-8 or rho>tol):return unsolved('no_curvature_for_alignment')
    gain=1/cfg.tracking_horizon_m
    if k:
        turn_radius=1/k
        heading_drift=turn_radius*(1-math.cos(theta))
        initial_slope=math.tan(theta)
        reference_k=k*cfg.reference_curvature_share
        # Quintic Hermite e(u)=e0*h00(u)+S*m0*h10(u), ending at
        # e=e'=e''=0, starts with actual heading m0=f_perp/(f.n).
        # |h00''|<6 and |h10''|<6, so |e''| <=6*rho/S²+6*|m0|/S.
        # Since curvature <=|e''|, this quadratic bounds REFERENCE curvature.
        curvature_span=(6*initial_slope+math.sqrt(36*initial_slope**2+
            24*reference_k*rho))/(2*reference_k)
        convergence_span=cfg.tracking_horizon_m*max(1.,
            math.log1p(rho/tol)+math.log1p(theta/angle_tol))
        span=max(curvature_span,convergence_span)
        peak_heading=math.atan(1.875*rho/span+initial_slope)
        settling_tail=cfg.tracking_horizon_m*math.log(max(1.,peak_heading/angle_tol))
        notice=cfg.tracking_horizon_m+travel
    else:
        turn_radius=heading_drift=curvature_span=convergence_span=span=settling_tail=notice=0.
    leading_support=h+b+uncertainty
    required=max(curvature_span,convergence_span)+leading_support+settling_tail
    direction=unit([a-gain*e for a,e in zip(n,lateral)])
    result.update(required_approach_m=required,activation_remaining_m=required+notice,
        turn_radius_m=turn_radius,curvature_span_m=curvature_span,
        convergence_span_m=convergence_span,reference_span_m=span,
        settling_tail_m=settling_tail,
        leading_body_allowance_m=leading_support,cross_track_gain_per_m=gain,
        direction_world=direction,estimated_lateral_envelope_m=rho+heading_drift)
    if workspace_planes is None:return unsolved('public_workspace_not_supplied')
    if not isinstance(workspace_planes,(list,tuple)) or not 4<=len(workspace_planes)<=64:
        raise ValueError('finite public convex workspace planes required')
    exit_face=False
    for plane in workspace_planes:
        if type(plane) is not dict or set(plane)!={'normal_world','offset_m'}:
            raise ValueError('public boundary planes only; no scene/obstacle records')
        pn=vector(plane['normal_world']);offset=number(plane['offset_m'])
        if abs(math.hypot(*pn)-1)>1e-6:raise ValueError('unit workspace normals required')
        if dot(pn,n)>1-1e-6 and abs(dot(g,pn)-offset)<1e-6:
            exit_face=True;continue  # Real native aperture guard remains mandatory.
        axis_here=[a-remaining*b_ for a,b_ in zip(g,n)]
        axial_max=max(dot(axis_here,pn),dot(g,pn))
        lateral_plane=math.sqrt(max(0.,1-dot(pn,n)**2))
        envelope=axial_max+(rho+heading_drift)*lateral_plane+h+b+uncertainty
        if envelope>offset:return unsolved('public_workspace_insufficient_for_approach_envelope')
    if not exit_face:return unsolved('exit_not_on_supplied_public_workspace_face')
    result['workspace_checked']=True
    if not ready and remaining<required:
        return unsolved('insufficient_forward_distance_replan_required')
    result.update(status='READY' if ready else 'AVAILABLE',reason='public_gate_candidate_only')
    return result


class PublicGateApproach:
    def __init__(self,profile,epoch):
        if type(profile) is not GateApproachProfile or type(epoch) is not str or not epoch:
            raise ValueError('explicit profile and epoch required')
        self.profile,self.epoch=profile,epoch
        self.active=False
        self._gate=None
        self._reference=None
        self._last_episode=0

    def adapt(self,advice,current_pose,public_goal,now_qpc_ns,*,
              curvature_limit_per_m=.5,workspace_planes=None,paused=False):
        """Detached opt-in post-adapter; never raises speed or edits source facts.

        Pass real effective advice and its original source facts, current own
        snapshot, and public workspace planes. Missing space is UNSOLVED/STOP.
        There is no automatic reverse, route search, or hidden-scene fallback.
        """
        out=copy.deepcopy(advice)
        def stop(reason):
            out.update(status='STOP',reason=reason,speed_limit_m_s=0.,
                       target_direction_world=[0.,0.,0.],direction_world=[0.,0.,0.])
            return out
        if advice.get('policy',{}).get('gate_control_mode')!='external_public_dynamic':
            raise ValueError('explicit external_public_dynamic upstream mode required')
        if advice.get('status')!='ADVISE':return out
        if (advice.get('world_epoch')!=self.epoch
                or current_pose.get('world_epoch',self.epoch)!=self.epoch):
            return stop('public_gate_epoch_mismatch')
        if type(paused) is not bool:raise ValueError('explicit pause required')
        if paused:return stop('user_paused')
        if current_pose.get('ready',True) is not True or current_pose.get('fault',''):
            return stop('current_native_not_ready')
        allowed={'entry_center_m','entry_inward_normal_world','exit_center_m',
                 'exit_outward_normal_world','gate_radius_m','exit_clearance_m'}
        if set(public_goal)-allowed:raise ValueError('public gate fields only')
        gate=(tuple(vector(public_goal['exit_center_m'])),tuple(vector(public_goal['exit_outward_normal_world'])),number(public_goal['gate_radius_m']))
        if self._gate is not None and gate!=self._gate:raise ValueError('new gate requires new epoch/adapter')
        now,acq,done,inferred,at=map(ns,(now_qpc_ns,advice['source_acquisition_qpc_ns'],
            advice['source_completed_qpc_ns'],advice['inference_completed_qpc_ns'],current_pose['at_qpc_ns']))
        if not (acq<=done<=inferred<=now and acq<=at<=now):return stop('future_or_reversed_time')
        old=advice['engineering_profile']
        if now-acq>min(5.,number(old['max_source_age_s']))*1e9:return stop('original_sample_expired')
        if now-at>min(.25,number(old['max_current_pose_age_s']))*1e9:return stop('current_pose_expired')
        quality=advice['quality']
        if type(quality) is not int or not 0<=quality<=0x1fff or quality&7!=7 or quality&0x17f0:
            return stop('invalid_faulted_saturated_or_held_em')
        q=vector(current_pose['orientation_xyzw'],4);forward=rotate(q,[0.,0.,1.])
        source=advice['source_pose'];source_forward=rotate(source['orientation_xyzw'],[0.,0.,1.])
        if (math.dist(vector(current_pose['position_m']),vector(source['position_m']))>.25
                or dot(forward,source_forward)<math.cos(math.radians(15.))):
            return stop('original_observation_pose_inapplicable')
        if current_pose.get('phase')=='ARRIVED':return stop('actual_arrived')
        if current_pose.get('phase') in ('INITIAL_OUTSIDE','ENTRY_CROSSING'):
            return out  # Original entry writer remains authoritative.
        speed=number(advice['speed_limit_m_s'])
        geometry=gate_geometry(position_m=current_pose['position_m'],forward_world=forward,
            exit_center_m=gate[0],exit_normal_world=gate[1],gate_radius_m=gate[2],
            speed_m_s=max(speed,number(current_pose['speed_m_s'])),pose_age_s=(now-at)/1e9,
            curvature_limit_per_m=curvature_limit_per_m,workspace_planes=workspace_planes,profile=self.profile)
        out['public_gate_approach']=geometry
        self._gate=gate
        observed=advice.get('policy',{})
        episode=observed.get('episode_number',0)
        if type(episode) is not int or episode<self._last_episode:
            return stop('observed_episode_order_changed')
        new_episode=episode>self._last_episode
        self._last_episode=episode
        signal=observed.get('observed_signal_anomaly')
        if type(signal) is not bool:
            raise ValueError('actual upstream anomaly flag required in external mode')
        settling_observation=(episode>0 and observed.get('episode_armed') is False)
        sensor_priority=new_episode or signal or settling_observation
        geometry.update(observed_avoidance_priority=sensor_priority,new_observed_episode=new_episode)
        if sensor_priority:
            # A gate reference may never erase a newly observed water/rock
            # response. The owner sees need_replan; native Guard stays decisive.
            self.active=False;self._reference=None
            geometry.update(status='YIELD_TO_OBSERVED_AVOIDANCE',active=False,
                need_replan=(geometry['status']=='UNSOLVED' or
                    geometry.get('remaining_m',0)<geometry.get('required_approach_m',math.inf)),
                gate_reference_suspended=True)
            return out
        reason=geometry['reason']
        tracking_existing=self._reference is not None
        if geometry['status']=='UNSOLVED' and not (tracking_existing and
                reason=='insufficient_forward_distance_replan_required'):
            return stop('public_gate_approach_unsolved:'+reason)
        self.active=self.active or geometry['remaining_m']<=geometry['activation_remaining_m']
        geometry['active']=self.active
        if not self.active:return out
        normal=unit(list(gate[1]));remaining=geometry['remaining_m']
        if self._reference is None:
            cosine=dot(forward,normal)
            self._reference=dict(start_remaining_m=remaining,
                span_m=geometry['reference_span_m'],lateral_start=geometry['lateral_error_world'],
                slope_start=[(f-cosine*n)/cosine for f,n in zip(forward,normal)])
        ref=self._reference;span=ref['span_m']
        u=max(0.,min(1.,(ref['start_remaining_m']-remaining)/span)) if span else 1.
        h00=1-10*u**3+15*u**4-6*u**5;h10=u-6*u**3+8*u**4-3*u**5
        d00=-30*u**2+60*u**3-30*u**4;d10=1-18*u**2+32*u**3-15*u**4
        reference=[e*h00+span*m*h10 for e,m in zip(ref['lateral_start'],ref['slope_start'])]
        slope=[e*d00/span+m*d10 for e,m in zip(ref['lateral_start'],ref['slope_start'])] if span else [0.,0.,0.]
        error=[e-r for e,r in zip(geometry['lateral_error_world'],reference)]
        direction=unit([n+m-geometry['cross_track_gain_per_m']*e for n,m,e in zip(normal,slope,error)])
        geometry.update(status='TRACKING_REFERENCE',reason='existing_public_reference',
            reference_progress=u,reference_lateral_world=reference,
            reference_slope_world=slope,reference_start=copy.deepcopy(ref),
            actual_reference_error_world=error,direction_world=direction,
            need_replan=False)
        if remaining<=geometry['leading_body_allowance_m'] and not geometry['aperture_ready']:
            geometry['need_replan']=True
            return stop('public_gate_approach_unsolved:not_aligned_before_leading_body_contact')
        body=rotate([-q[0],-q[1],-q[2],q[3]],direction)
        out.update(status='ADVISE',reason='public_gate_dynamic_approach',
            target_direction_world=direction,direction_world=list(direction),
            yaw_delta_deg=math.degrees(math.atan2(body[0],body[2])),
            pitch_delta_deg=math.degrees(math.atan2(body[1],math.hypot(body[0],body[2]))),
            speed_limit_m_s=speed,current_pose=copy.deepcopy(current_pose))
        return out

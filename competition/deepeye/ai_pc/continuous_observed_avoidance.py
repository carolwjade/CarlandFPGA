"""Opt-in, observed-only fast demo policy; advice alone grants no motion authority.

No scene, obstacle list, route, source callable, clock or transport is accepted.
The original 797/core/default paths are unchanged. Actual PWM admission and native
full-volume guard remain mandatory. This reactive exploration policy does not
guarantee a collision-free route or any completion time.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from statistics import median

REQUIREMENTS_SHA256 = '2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
PROFILE_ID = 'observed_multiple_fast_demo_975_v1'
ORIGINAL_PROFILE_ID = 'deepeye_continuous_em3_advice_candidate_797_v1'
ORIGINAL_CORE_SHA256 = 'fad1eda8c0d9e31f35d2f4c98d48dbd0678d49b283cbb0e10051ac003b9cb8fa'


def _number(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError('finite ordinary numeric value required')
    return float(x)


def _ns(x):
    if type(x) is int and x >= 0:
        return x
    if type(x) is str and x.isascii() and x.isdecimal():
        return int(x)
    raise ValueError('original nonnegative QPC nanoseconds required')


def _vec(x, count=3):
    if not isinstance(x, (list, tuple)) or len(x) != count:
        raise ValueError('fixed public vector required')
    return [_number(v) for v in x]


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _unit(v):
    length = math.hypot(*v)
    if length < 1e-12:
        raise ValueError('nonzero direction required')
    return [x/length for x in v]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _rotate(q, v):
    q = _vec(q, 4)
    if abs(_dot(q, q)-1.) > 1e-6:
        raise ValueError('unit own/source quaternion required')
    t = [2*x for x in _cross(q[:3], v)]
    c = _cross(q[:3], t)
    return [v[i]+q[3]*t[i]+c[i] for i in range(3)]


@dataclass(frozen=True)
class FastObservedProfile:
    """Explicit human-authorized speed law, independent of missing-C3 penalties."""
    profile_id: str = PROFILE_ID
    cruise_m_s: float = .225
    avoid_m_s: float = .1875
    lane_offset_m: float = 2.5
    lane_increment_m: float = 1.
    max_lane_offset_m: float = 4.5
    lookahead_m: float = 4.
    return_start_m: float = 8.5
    return_end_m: float = 2.
    cross_track_gain_per_m: float = 1.
    terminal_speed_m_s: float = .125
    quiet_sources_to_rearm: int = 3
    baseline_samples: int = 3
    # Sensitive digital-proxy trigger for the explicitly noiseless793 EM source;
    # approximately three ADC counts, not calibrated range/free-space evidence.
    c0_trigger: float = .003
    gradient_trigger: float = .003
    max_source_age_s: float = 5.
    max_current_pose_age_s: float = .25

    def __post_init__(self):
        if (self.profile_id != PROFILE_ID or type(self.baseline_samples) is not int
                or not 2 <= self.baseline_samples <= 8
                or type(self.quiet_sources_to_rearm) is not int
                or not 2 <= self.quiet_sources_to_rearm <= 8):
            raise ValueError('explicit observed-lane engineering profile required')
        for value in (self.cruise_m_s, self.avoid_m_s, self.lane_offset_m,
                      self.lane_increment_m, self.max_lane_offset_m,
                      self.cross_track_gain_per_m, self.terminal_speed_m_s,
                      self.lookahead_m, self.return_start_m, self.return_end_m,
                      self.c0_trigger, self.gradient_trigger, self.max_source_age_s,
                      self.max_current_pose_age_s):
            if _number(value) <= 0:
                raise ValueError('positive finite engineering bounds required')
        if not (self.avoid_m_s <= self.cruise_m_s <= .25
                and self.terminal_speed_m_s <= self.avoid_m_s
                and self.lane_offset_m <= self.max_lane_offset_m <= 8.
                and self.return_end_m < self.return_start_m
                and self.max_source_age_s <= 5.
                and self.max_current_pose_age_s <= .25):
            raise ValueError('speed/freshness bounds cannot be enlarged')


class ObservedAvoidance:
    def __init__(self, profile, epoch):
        if type(profile) is not FastObservedProfile or type(epoch) is not str or not epoch:
            raise ValueError('explicit profile and world epoch required')
        self.profile, self.epoch = profile, epoch
        self._goal = None
        self._baseline = []
        self._last_source = None
        self._side = None
        self._trigger = None
        self._episode = 0
        self._episode_armed = True
        self._quiet_sources = 0
        self._lane_amplitude = 0.
        self._episode_chain = '0'*64

    def adapt(self, advice, current_pose, public_goal, now_qpc_ns,
              paused=False, operator_cap=.25):
        """Return detached profile advice; original acquisition/feature facts stay intact.

        Call once per completed real 797 advice, or repeat the same original advice
        while it remains applicable. Repeats never add baseline samples or refresh
        time. Root must pass its *current latched* cap and still enforce admission.
        """
        if type(advice) is not dict or type(current_pose) is not dict or type(public_goal) is not dict:
            raise ValueError('ordinary advice, own pose and public goal dictionaries required')
        allowed = {'entry_center_m', 'entry_inward_normal_world', 'exit_center_m',
                   'exit_outward_normal_world', 'gate_radius_m', 'exit_clearance_m'}
        if set(public_goal)-allowed or not {'entry_center_m', 'exit_center_m',
                'exit_outward_normal_world', 'gate_radius_m'} <= set(public_goal):
            raise ValueError('only original public gate geometry accepted')
        entry, exit_pos = _vec(public_goal['entry_center_m']), _vec(public_goal['exit_center_m'])
        axis = _unit([b-a for a, b in zip(entry, exit_pos)])
        normal = _vec(public_goal['exit_outward_normal_world'])
        if (abs(math.hypot(*normal)-1.) > 1e-6 or _dot(normal, axis) < .95
                or _number(public_goal['gate_radius_m']) != .25):
            raise ValueError('this opt-in policy requires opposite, aligned public gates')
        if 'entry_inward_normal_world' in public_goal:
            inward = _vec(public_goal['entry_inward_normal_world'])
            if abs(math.hypot(*inward)-1.) > 1e-6 or _dot(inward, axis) < .95:
                raise ValueError('entry inward normal must match public opposite-gate axis')
        goal_binding = (tuple(entry), tuple(exit_pos), tuple(normal), public_goal['gate_radius_m'])
        if self._goal is not None and self._goal != goal_binding:
            raise ValueError('new public layout requires new policy/epoch')
        now, cap = _ns(now_qpc_ns), _number(operator_cap)
        if type(paused) is not bool or not 0 <= cap <= .25:
            raise ValueError('explicit pause and operator cap within .25m/s required')
        result = copy.deepcopy(advice)
        policy = dict(profile_id=PROFILE_ID, requirements_sha256=REQUIREMENTS_SHA256,
            authorization='none', basic_demo_only=True, final_quality='not_run',
            original_status=advice.get('status'), original_reason=advice.get('reason'),
            original_speed_limit_m_s=advice.get('speed_limit_m_s'),
            speed_law='explicit_fast_demo_without_missing_c3_speed_attenuation',
            public_axis_world=axis, baseline_samples=len(self._baseline),
            lane_latched=self._side is not None, lane_side_world=copy.deepcopy(self._side),
            lane_offset_m=0., trigger_source=copy.deepcopy(self._trigger),
            episode_number=self._episode, episode_armed=self._episode_armed,
            quiet_source_count=self._quiet_sources, lane_amplitude_m=self._lane_amplitude,
            episode_digest_chain=self._episode_chain)
        result['policy'] = policy

        def stop(reason):
            result.update(status='STOP', reason=reason, speed_limit_m_s=0.,
                target_direction_world=[0., 0., 0.], direction_world=[0., 0., 0.])
            return result

        if advice.get('world_epoch') != self.epoch or current_pose.get('world_epoch', self.epoch) != self.epoch:
            return stop('observed_policy_world_epoch_mismatch')
        if (advice.get('schema') != ORIGINAL_PROFILE_ID
                or advice.get('requirements_sha256') != REQUIREMENTS_SHA256
                or advice.get('numeric_source_sha256') != ORIGINAL_CORE_SHA256):
            return stop('foreign_original_advice_profile')
        if paused or cap == 0:
            return stop('user_paused' if paused else 'user_speed_cap_zero')
        if current_pose.get('phase') == 'ARRIVED':
            return stop('actual_arrived')
        if current_pose.get('ready', True) is not True or current_pose.get('fault', ''):
            return stop('current_native_not_ready')
        if advice.get('status') not in ('ADVISE', 'STOP'):
            return stop('unknown_original_advice_status')
        if advice['status'] == 'STOP' and advice.get('reason') != 'candidate_risk_limit':
            return stop(advice.get('reason', 'original_stop'))
        acquired = _ns(advice['source_acquisition_qpc_ns'])
        completed = _ns(advice['source_completed_qpc_ns'])
        inferred = _ns(advice['inference_completed_qpc_ns'])
        current_at = _ns(current_pose['at_qpc_ns'])
        old_profile = advice['engineering_profile']
        source_age = min(self.profile.max_source_age_s, _number(old_profile['max_source_age_s']))
        pose_age = min(self.profile.max_current_pose_age_s, _number(old_profile['max_current_pose_age_s']))
        if not (acquired <= completed <= inferred <= now and acquired <= current_at <= now):
            return stop('future_or_reversed_time')
        if source_age <= 0 or now-acquired > source_age*1e9:
            return stop('original_sample_expired')
        if pose_age <= 0 or now-current_at > pose_age*1e9:
            return stop('current_pose_expired')
        quality = advice['quality']
        if type(quality) is not int or not 0 <= quality <= 0x1fff or quality & 7 != 7 or quality & 0x17f0:
            return stop('invalid_faulted_saturated_or_held_em')
        values = advice['decoded_features']
        if (not isinstance(values, (list, tuple)) or len(values) != 4 or values[3] is not None
                or advice.get('c3_observed') is not False or quality & 0x888):
            return stop('foreign_or_non_em3_profile')
        c0, c1, c2 = [_number(v) for v in values[:3]]
        position, source_position = _vec(current_pose['position_m']), _vec(advice['source_pose']['position_m'])
        q, source_q = _vec(current_pose['orientation_xyzw'], 4), _vec(advice['source_pose']['orientation_xyzw'], 4)
        forward, source_forward = _rotate(q, [0., 0., 1.]), _rotate(source_q, [0., 0., 1.])
        if (math.dist(position, source_position) > .25
                or _dot(forward, source_forward) < math.cos(math.radians(15.))):
            return stop('original_observation_pose_inapplicable')
        source_key = (acquired, advice['board_frame_sha256'])
        if self._last_source is not None and (acquired < self._last_source[0]
                or acquired == self._last_source[0] and source_key != self._last_source):
            return stop('original_source_order_or_identity_changed')
        self._goal = goal_binding
        is_new_source = source_key != self._last_source
        if is_new_source:
            if len(self._baseline) < self.profile.baseline_samples:
                self._baseline.append(c0)
            self._last_source = source_key
        baseline = median(self._baseline)
        delta = c0-baseline
        trigger = (len(self._baseline) >= self.profile.baseline_samples and
            (abs(delta) >= self.profile.c0_trigger or math.hypot(c1, c2) >= self.profile.gradient_trigger))
        quiet = (abs(delta) < self.profile.c0_trigger*.5
                 and math.hypot(c1,c2) < self.profile.gradient_trigger*.5)
        if is_new_source and self._episode:
            self._quiet_sources = min(self.profile.quiet_sources_to_rearm,
                self._quiet_sources+1) if quiet else 0
            if self._quiet_sources >= self.profile.quiet_sources_to_rearm:
                self._episode_armed = True
        if is_new_source and trigger and self._episode_armed:
            # Move predicted C0 back toward its *observed initial* baseline.
            sign = 1. if delta >= 0 else -1.
            lateral = _rotate(source_q, [-sign*c1, -sign*c2, 0.])
            lateral = [x-_dot(lateral, axis)*a for x, a in zip(lateral, axis)]
            if math.hypot(*lateral) < 1e-9:
                # Deterministic exploration breaks an exactly symmetric signal;
                # it does not claim the selected side has observed free space.
                right = _rotate(source_q, [1.,0.,0.])
                lateral = [r-_dot(right,axis)*a for r,a in zip(right,axis)]
                if math.hypot(*lateral) < 1e-9:
                    reference = min(([1.,0.,0.], [0.,1.,0.], [0.,0.,1.]), key=lambda v: abs(_dot(axis,v)))
                    lateral = _cross(axis, reference)
            candidate_side = _unit(lateral)
            side_decision = 'initial_observed_side'
            if self._side is None:
                self._side = candidate_side
            elif _dot(candidate_side,self._side) >= 0:
                # Re-evaluate each NEW observed episode, while avoiding a sudden
                # cross-through of the already encountered anomaly.
                self._side = _unit([a+b for a,b in zip(self._side,candidate_side)])
                side_decision = 'new_gradient_same_side_adjustment'
            else:
                side_decision = 'new_gradient_conflict_keep_observed_side_memory'
            self._lane_amplitude = min(self.profile.max_lane_offset_m,
                self.profile.lane_offset_m if self._episode == 0 else
                self._lane_amplitude+self.profile.lane_increment_m)
            self._episode += 1
            self._episode_armed = False
            self._quiet_sources = 0
            self._trigger = dict(source_acquisition_qpc_ns=advice['source_acquisition_qpc_ns'],
                board_frame_sha256=advice['board_frame_sha256'], baseline_c0=baseline,
                source_record_sha256=advice.get('source_record_sha256'),
                delta_c0=delta, c1=c1, c2=c2, symmetric_exploration=math.hypot(c1,c2)<1e-9,
                episode_number=self._episode, candidate_side_world=candidate_side,
                side_decision=side_decision, lane_amplitude_m=self._lane_amplitude)
            self._episode_chain = hashlib.sha256((self._episode_chain+json.dumps(
                self._trigger,sort_keys=True,separators=(',',':'),allow_nan=False)).encode()).hexdigest()
        if advice['status'] == 'STOP' and self._side is None:
            return stop('candidate_risk_limit')
        remaining = _dot([g-p for g, p in zip(exit_pos, position)], axis)
        u = max(0., min(1., (remaining-self.profile.return_end_m)/(
            self.profile.return_start_m-self.profile.return_end_m)))
        # Quintic reference with zero first/second derivatives at both ends.
        # Progress s increases as remaining decreases, hence the negative slope.
        blend = u*u*u*(10.+u*(-15.+6.*u))
        slope = -self._lane_amplitude*30.*u*u*(1.-u)*(1.-u)/(
            self.profile.return_start_m-self.profile.return_end_m)
        offset = self._lane_amplitude*blend
        along = _dot([p-e for p, e in zip(position, entry)], axis)
        side = self._side or [0.,0.,0.]
        lateral_position = [p-e-along*a for p,e,a in zip(position,entry,axis)]
        reference = [offset*v for v in side]
        error = [p-r for p,r in zip(lateral_position,reference)]
        tangent = [a+slope*v for a,v in zip(axis,side)]
        vector = [t-self.profile.cross_track_gain_per_m*e for t,e in zip(tangent,error)]
        # Diagnostic one-metre vector endpoint, NOT an endpoint/lookahead law.
        target = [p+v for p,v in zip(position,vector)]
        terminal_guidance = remaining <= self.profile.return_end_m
        direction = _unit(vector)
        body = _rotate([-q[0],-q[1],-q[2],q[3]], direction)
        speed = min(cap, self.profile.avoid_m_s if self._side else self.profile.cruise_m_s)
        if remaining <= self.profile.return_start_m:
            speed = min(speed,self.profile.terminal_speed_m_s)
        policy.update(baseline_samples=len(self._baseline), baseline_c0=baseline,
            lane_latched=self._side is not None, lane_side_world=copy.deepcopy(self._side),
            lane_offset_m=offset, trigger_source=copy.deepcopy(self._trigger),
            lane_amplitude_m=self._lane_amplitude, episode_number=self._episode,
            episode_armed=self._episode_armed, quiet_source_count=self._quiet_sources,
            episode_digest_chain=self._episode_chain,
            reference_offset_m=offset, reference_slope_per_m=slope,
            reference_lateral_world=reference, actual_cross_track_world=lateral_position,
            cross_track_error_world=error, reference_tangent_world=tangent,
            vector_field_world=vector, legacy_lookahead_not_used=True,
            public_remaining_m=remaining, public_target_m=target,
            terminal_public_guidance=terminal_guidance,
            source_age_s=(now-acquired)/1e9, no_observed_free_space_claim=True)
        result.update(status='ADVISE', reason='observed_multiple_lane_fast_demo',
            target_direction_world=direction, direction_world=list(direction),
            yaw_delta_deg=math.degrees(math.atan2(body[0],body[2])),
            pitch_delta_deg=math.degrees(math.atan2(body[1],math.hypot(body[0],body[2]))),
            speed_limit_m_s=speed, current_pose=copy.deepcopy(current_pose))
        return result

"""Pure 3D rigid motion for the A world authority, not motion authorization.

Coordinates are body +Z forward, +Y up, +X right. Validated commands supply
curvature, with body rotation vector per metre (-pitch, yaw, 0). The SE(3)
integral follows actual travelled distance, including acceleration ramps.

This module has no scene, collision oracle, sensor/observation, process boundary
or authority grant. A caller must enforce all of those before applying a pose.
In particular speed code zero brakes; an authority hard STOP must not advance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from competition.deepeye.integration.motion import MotionCommand, validate


ACCELERATION_M_S2 = 0.25
MAX_DT_NS = 10_000_000
QUATERNION_NORM_TOLERANCE = 1e-12


def _number(value: object, name: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number, not bool")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _vector(value: object, size: int, name: str) -> tuple[float, ...]:
    if type(value) not in (tuple, list) or len(value) != size:
        raise ValueError(f"{name} must contain exactly {size} numbers")
    return tuple(_number(component, name) for component in value)


@dataclass(frozen=True, slots=True)
class RigidState:
    """Snapshot of body origin, body-to-world unit quaternion (xyzw), and speed.

    Vectors supplied as lists are copied to tuples. Unit-norm roundoff up to
    1e-12 is accepted and normalized; nonunit orientations are rejected.
    The global FAST speed ceiling is checked here, the selected profile in
    advance(). No position in this value is exposed as a controller observation.
    """

    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    speed_m_s: float

    def __post_init__(self) -> None:
        position = _vector(self.position_m, 3, "position_m")
        orientation = _vector(self.orientation_xyzw, 4, "orientation_xyzw")
        norm = math.hypot(*orientation)
        if not math.isfinite(norm) or abs(norm - 1.0) > QUATERNION_NORM_TOLERANCE:
            raise ValueError("orientation_xyzw must have unit norm")
        speed = _number(self.speed_m_s, "speed_m_s")
        if not 0 <= speed <= 0.25:
            raise ValueError("speed_m_s must be in 0..0.25")
        object.__setattr__(self, "position_m", position)
        object.__setattr__(self, "orientation_xyzw", tuple(v / norm for v in orientation))
        object.__setattr__(self, "speed_m_s", speed)


@dataclass(frozen=True, slots=True)
class MotionSample:
    """A point on one motion step; distance samples may have fractional ns."""

    elapsed_ns: float
    distance_m: float
    state: RigidState


def _sinc(angle: float) -> float:
    # sin(x)/x is well-conditioned near zero. Only the exact removable
    # singularity is special-cased; legal arbitrarily small turns survive.
    return 1.0 if angle == 0 else math.sin(angle) / angle


def _multiply_quaternions(left, right):
    x, y, z, w = left
    a, b, c, d = right
    return (w*a + x*d + y*c - z*b,
            w*b - x*c + y*d + z*a,
            w*c + x*b - y*a + z*d,
            w*d - x*a - y*b - z*c)


def _rotate_vector(q, vector):
    x, y, z, w = q
    a, b, c = vector
    # v + 2*w*(q_xyz cross v) + 2*q_xyz cross (q_xyz cross v).
    tx, ty, tz = 2*(y*c-z*b), 2*(z*a-x*c), 2*(x*b-y*a)
    return (a + w*tx + y*tz-z*ty,
            b + w*ty + z*tx-x*tz,
            c + w*tz + x*ty-y*tx)


def _pose(start: RigidState, command: MotionCommand, distance: float, speed: float) -> RigidState:
    if distance == 0 and speed == start.speed_m_s:
        return start  # Immutable value: preserve an unmoved pose exactly.
    yaw, pitch = command.curvature_yaw_per_m, command.curvature_pitch_per_m
    angle = math.hypot(yaw, pitch) * distance
    half_sinc = _sinc(angle / 2)
    half_distance_sinc = 0.5 * distance * half_sinc
    delta_q = (-pitch*half_distance_sinc, yaw*half_distance_sinc, 0.0, math.cos(angle/2))
    # Integral exp([k]x*s)e_z ds, k=(-pitch,yaw,0).  The transverse
    # coefficient is s^2*(1-cos(angle))/angle^2; the half-angle identity
    # avoids catastrophic cancellation without erasing tiny curved motion.
    transverse = 0.5 * distance * distance * half_sinc * half_sinc
    local_delta = (yaw*transverse, pitch*transverse, distance*_sinc(angle))
    world_delta = _rotate_vector(start.orientation_xyzw, local_delta)
    return RigidState(tuple(p+d for p, d in zip(start.position_m, world_delta)),
                      _multiply_quaternions(start.orientation_xyzw, delta_q), speed)


@dataclass(frozen=True, slots=True, init=False)
class MotionStep:
    """Immutable analytic path segment with bounded time and distance samples.

    Construct through advance(). All fields needed by sampling are immutable;
    no input container or callback is retained. A pose sample is not a swept
    volume test. Use the full rigid transform when sweeping an actual body.
    """

    start_state: RigidState
    end_state: RigidState
    dt_ns: int
    distance_m: float
    _command: MotionCommand = field(repr=False)
    _acceleration_m_s2: float = field(repr=False)
    _ramp_duration_s: float = field(repr=False)
    _ramp_distance_m: float = field(repr=False)
    _ramp_end_speed_m_s: float = field(repr=False)

    def __init__(self, state: RigidState, profile: str, speed_code: int,
                 yaw_q: int, pitch_q: int, dt_ns: int) -> None:
        if type(state) is not RigidState:
            raise ValueError("state must be a RigidState")
        if type(dt_ns) is not int or not 1 <= dt_ns <= MAX_DT_NS:
            raise ValueError("dt_ns must be integer 1..10000000")
        command = validate(profile, speed_code, yaw_q, pitch_q)
        start = state  # RigidState already validated and snapshotted its vectors.
        if start.speed_m_s > command.max_speed_m_s:
            raise ValueError("actual speed exceeds selected profile; stop before profile change")
        duration = dt_ns * 1e-9
        delta = command.target_speed_m_s - start.speed_m_s
        acceleration = math.copysign(ACCELERATION_M_S2, delta) if delta else 0.0
        time_to_target = abs(delta) / ACCELERATION_M_S2
        ramp_duration = min(duration, time_to_target)
        ramp_end_speed = (command.target_speed_m_s if time_to_target <= duration
                          else start.speed_m_s + acceleration*ramp_duration)
        ramp_distance = 0.5*(start.speed_m_s + ramp_end_speed)*ramp_duration
        distance = ramp_distance + ramp_end_speed*(duration - ramp_duration)
        object.__setattr__(self, "start_state", start)
        object.__setattr__(self, "dt_ns", dt_ns)
        object.__setattr__(self, "distance_m", distance)
        object.__setattr__(self, "_command", command)
        object.__setattr__(self, "_acceleration_m_s2", acceleration)
        object.__setattr__(self, "_ramp_duration_s", ramp_duration)
        object.__setattr__(self, "_ramp_distance_m", ramp_distance)
        object.__setattr__(self, "_ramp_end_speed_m_s", ramp_end_speed)
        object.__setattr__(self, "end_state", _pose(start, command, distance, ramp_end_speed))

    def _distance_and_speed(self, elapsed_s: float) -> tuple[float, float]:
        if elapsed_s < self._ramp_duration_s:
            speed = self.start_state.speed_m_s + self._acceleration_m_s2*elapsed_s
            distance = (self.start_state.speed_m_s + 0.5*self._acceleration_m_s2*elapsed_s)*elapsed_s
            return distance, speed
        return (self._ramp_distance_m
                + self._ramp_end_speed_m_s*(elapsed_s - self._ramp_duration_s),
                self._ramp_end_speed_m_s)

    def sample_at_time_ns(self, elapsed_ns: int) -> MotionSample:
        """Sample integer local time 0..dt_ns, including both endpoints."""
        if type(elapsed_ns) is not int or not 0 <= elapsed_ns <= self.dt_ns:
            raise ValueError("elapsed_ns must be integer inside this step")
        distance, speed = self._distance_and_speed(elapsed_ns*1e-9)
        return MotionSample(float(elapsed_ns), distance, _pose(self.start_state, self._command, distance, speed))

    def sample_at_distance_m(self, distance_m: float) -> MotionSample:
        """Sample 0..distance_m and report the earliest time reaching it.

        This inverse is single-valued except for stopped intervals, where the
        earliest point is returned. Fractional nanoseconds are retained. Values
        outside the domain, including the next representable float, are errors.
        """
        distance = _number(distance_m, "distance_m")
        if not 0 <= distance <= self.distance_m:
            raise ValueError("distance_m must be inside this step")
        if distance == 0:
            elapsed_s = 0.0
        elif distance == self._ramp_distance_m:
            elapsed_s = self._ramp_duration_s
        elif distance == self.distance_m:
            elapsed_s = self.dt_ns*1e-9
        elif distance < self._ramp_distance_m:
            # Rationalized positive root of s=v0*t+a*t^2/2. This avoids
            # subtracting nearly equal roots during low-distance sampling.
            v0, acceleration = self.start_state.speed_m_s, self._acceleration_m_s2
            if acceleration > 0:
                # Take roots before products: both v0**2 and 2*a*s can
                # underflow for a legal subnormal distance. hypot scales
                # its inputs and keeps that case finite and invertible.
                root = math.hypot(v0, math.sqrt(2*acceleration)*math.sqrt(distance))
            else:
                root = math.sqrt(max(0.0, v0*v0 + 2*acceleration*distance))
            elapsed_s = 2*distance / (v0 + root)
        else:
            elapsed_s = (self._ramp_duration_s
                         + (distance-self._ramp_distance_m) / self._ramp_end_speed_m_s)
        # The input domain was validated above. Bound only roundoff in the
        # inverse, never accept or clip an out-of-domain requested distance.
        elapsed_s = min(self.dt_ns*1e-9, max(0.0, elapsed_s))
        _, speed = self._distance_and_speed(elapsed_s)
        return MotionSample(elapsed_s*1e9, distance, _pose(self.start_state, self._command, distance, speed))


def advance(state: RigidState, profile: str, speed_code: int, yaw_q: int,
            pitch_q: int, dt_ns: int) -> MotionStep:
    """Validate a quantized command and integrate one 1ns..10ms rigid step.

    Validation delegates to the same conservative integer postquantization ROM
    used by integration.motion. The outer authority must reject an expired or
    otherwise unauthorized command *before* calling/applying this integrator.
    """
    return MotionStep(state, profile, speed_code, yaw_q, pitch_q, dt_ns)

"""Candidate authority-local forward sensor profile (software checkpoint only).

Owner: A (competition/deepeye/simulation/).  Task DEEPEYE-IMPLEMENTATION-20261014/v1.
This module produces the four-channel authority-local sensor record that the
world authority hands to hardware_bridge.  It is a CANDIDATE simplified
empirical kernel: not a Maxwell/full-wave solver, not a calibrated instrument
model and not formally frozen as ``em_surrogate_v2``.  G03 (independent 3D
FDEM applicability, omitted-field/noise bound, mesh convergence) and G09
remain not_run; green software unit tests prove nothing about physical
detection performance.

Source-backed facts (brief paraphrase, primary URLs):
* Halliburton EarthStar3DX launch page (2025-05-19),
  https://www.halliburton.com/en/about-us/press-release/halliburton-launches-earthstar-3dx-horizontal-look-ahead-resistivity-service
  markets look-ahead up to 50 ft = 15.24 m before bit penetration.  That is a
  maximum marketed capability of one commercial service, not a guarantee for
  any formation and not this model's capability.
* SLB IriSphere, https://www.slb.com/resource-library/interview/drl/irisphere-see-ahead-bit
  reports up to 100 ft with 160 ft transmitter/receiver spacing and relies on
  pre-job sensitivity modelling and inversion.  It is NOT the capability of
  the 0.8 m simulated drill; its range must not be borrowed.
* ADI ADXL354/ADXL355 RevD,
  https://www.analog.com/media/en/technical-documentation/data-sheets/adxl354_adxl355.pdf
  Table 2 (PDF pp. 5-7): selectable +/-2/4/8 g, 20-bit internal ADC,
  22.5 ug/sqrt(Hz) typical noise density at +/-2 g.  Figures 11-13 (PDF p. 13)
  show frequency-dependent transfer functions, not broadband flat unity gain.
* Scientific background: Heagy et al. 2017, DOI 10.1016/j.cageo.2017.06.018,
  https://storage.googleapis.com/simpeg/papers/2017/1-s2.0-S0098300416303946-main.pdf
  Maxwell finite-volume EM forward problems with sources/receivers/material
  properties.  Its Figure 11 / Section 5.3 steel-cased well setup is a
  DIFFERENT experiment and does not validate this empirical kernel.

Project assumptions frozen for this checkpoint (not vendor data): 8 m support
radius, 30 deg cone half-angle, +/-20 deg differential lobes, 20 Hz native EM
update, 100 ms first-order response, 0.03 log10 white noise, random-walk
0.002 per sqrt(s), 0.2..2000 ohm m resistivity envelope, +/-2 differential
limit, 0.25 m quadrature step, 0.25 m near-field softening, and the vibration
model below.  A formal omitted-field/noise bound, independent 3D FDEM
comparison and mesh convergence remain NOT RUN, so these values stay
candidate-only.

Kernel: body axes are forward +Z and up +Y; a pose is a finite position and a
normalized xyzw quaternion (scale is normalized; zero, NaN, Inf and degenerate
orientations are refused before any scene query).  Conductivity sigma (S/m) is
read only through an authority-local callback; labels, object ids, map seeds,
screens, editor state and collision oracles never enter this module.  A
deterministic body-local lattice quadrature (0.25 m step, r <= 8 m) covers five
beams (forward, +/-20 deg yaw, +/-20 deg pitch; each 30 deg half-angle,
boundary included) with weights

    w = cos^2(theta) * exp(-r/4) / (r + 0.25)^2 * dV

and, per lobe, sigma_app = sum(w*sigma)/sum(w), log10rho = -log10(sigma_app);
background and objects enter only through their conductivity.  Channels:
C0 = log10rho(forward); C1 = log10rho(+yaw) - log10rho(-yaw);
C2 = log10rho(+pitch) - log10rho(-pitch).  Positive yaw rotates forward toward
local +X (right), positive pitch toward local +Y (up); C1 > 0 therefore means
the +X side appears more resistive (less conductive) than the -X side.  These
signs are project definitions, not a vendor convention.  No nearest-obstacle
distance and no material class lookup exist here.

Prototype numerical limitation: samples outside the 8 m support or outside
every beam are cropped.  That is NOT evidence that the physical response is
zero there; it is a prototype software cropping rule until an independent
forward model and bounded omitted-field noise/error budget exist.

Applicability: the authority must declare the medium context.  "formation" is
supported; "air" (air-ranging probe) and "conducting_shield" (opaque
conducting casing/shield) cannot be observed by this kernel and are reported
as invalid EM channels with the source_fault bit instead of fabricated
through-shield observations.  The kernel does not model magnetic casing,
shielding, anisotropy or full-wave effects, and it makes no "free space" or
"no object" claim from lack of contrast: it only reports an apparent
conductivity-weighted response.  A null/non-finite/non-positive/out-of-
envelope conductivity sample anywhere queried invalidates the EM channels with
source_fault; it is never silently replaced by background fill.

Temporal discipline: EM updates only on actual 20 Hz acquisitions
(acquire_em, tick multiples of 50 ms) using a causal first-order response
alpha = 1 - exp(-dt / 0.1 s) over the true elapsed seconds since the previous
successful acquisition; white noise and random-walk increments
(sigma * sqrt(dt)) are drawn per channel on acquisition only.  The 100 Hz ADC
path (sample_adc, tick multiples of 10 ms) observes zero-order-held EM values
with the original EM tick, never re-queries the conductivity callback, never
re-draws EM noise, and never fabricates an observation for a skipped slot or a
heartbeat gap > 100 ms.  Acquisitions may not be backfilled once an ADC read at
the same or a later tick occurred; non-monotonic, duplicate and off-grid ticks
are rejected.  The module cannot authenticate wall-clock time: the authority
must drive ticks from its real 100 Hz schedule.

Vibration (channel 3) is contact-only: the authority supplies the signed,
already-occurred contact/load acceleration in g for the current ADC tick
(never a future collision query); no contact means instrument noise only.  The
project model bandlimits it with an AR(1) lowpass at 100 Hz,
y[n] = a*y[n-1] + (1-a)*x[n] with a = 1/3, whose 25 Hz ENBW matches the
112.5 ug RMS acceleration noise value implied by the ADXL355 22.5 ug/sqrt(Hz)
density over 25 Hz, driven by sigma = 112.5 ug * sqrt((1+a)/(1-a)).  This is a
simplified project filter/ENBW assumption, NOT an ADXL355 register
configuration and not an equivalence claim to the real part.  Bandlimited
samples are clipped at +/-2 g (saturation flagged; the RMS consumes clipped
samples), the reported value is the trailing 100 ms (10 sample) RMS over the
100 Hz ADC grid, and startup or gapped windows are invalid rather than
backfilled.  Noise before/after the RMS window must not be equated with a raw
noise density.

Outward record: a frozen dataclass serialized through an explicit whitelist
(profile id/status/note, source mode, ADC tick, original EM tick, four values
or explicit null, four normalized 12-bit counts or null, and a quality word:
bits 0-3 valid, 4-7 saturated, 8-11 held, 12 source_fault, 13-15 untouched
zero).  It never contains obstacle coordinates, types, ids or boundaries,
scene/map seeds, editor history, collision queries or distances, detection
labels, callback internals or RNG state.  Counts are a normalized proxy, not
measured DAC/XADC calibration, gain or noise.  Integration note: the frozen
host contract currently defines only board telem/event observations and has no
raw authority-to-bridge sample kind, so this record has no host-schema
counterpart yet; that gap is reported rather than patched here.
"""
from __future__ import annotations

import functools
import math
import numbers
import random
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple

PROFILE_ID = "deepeye_forward_profile_candidate_v1"
PROFILE_STATUS = "candidate_only"
PROFILE_NOTE = "not_calibrated;not_em_surrogate_v2;not_formally_frozen"
SOURCE_MODE = "twin_fixture"

CHANNEL_NAMES = (
    "log10_rho_apparent",
    "yaw_log10_rho_difference",
    "pitch_log10_rho_difference",
    "near_bit_vibration_rms_g",
)

EM_PERIOD_MS = 50
ADC_PERIOD_MS = 10
HEARTBEAT_TIMEOUT_MS = 100
MAX_TICK_MS = (1 << 31) - 1

STEP_M = 0.25
SUPPORT_M = 8.0
CONE_HALF_ANGLE_DEG = 30.0
LOBE_OFFSET_DEG = 20.0
NEAR_FIELD_SOFTENING_M = 0.25

TAU_S = 0.1
WHITE_SIGMA_LOG10 = 0.03
RW_SIGMA_PER_SQRT_S = 0.002

RHO_MIN_OHM_M = 0.2
RHO_MAX_OHM_M = 2000.0
SIGMA_MIN_S_PER_M = 1.0 / RHO_MAX_OHM_M
SIGMA_MAX_S_PER_M = 1.0 / RHO_MIN_OHM_M
LOG10_RHO_MIN = math.log10(RHO_MIN_OHM_M)
LOG10_RHO_MAX = math.log10(RHO_MAX_OHM_M)
DIFF_LIMIT = 2.0

VIB_RANGE_G = 2.0
VIB_ENBW_HZ = 25.0
VIB_NOISE_RMS_G = 112.5e-6
VIB_AR_A = 1.0 / 3.0
VIB_DRIVE_SIGMA_G = VIB_NOISE_RMS_G * math.sqrt((1.0 + VIB_AR_A) / (1.0 - VIB_AR_A))
VIB_WINDOW_SAMPLES = 10

COUNTS_MAX = 4095

CONTEXT_FORMATION = "formation"
CONTEXT_AIR = "air"
CONTEXT_CONDUCTING_SHIELD = "conducting_shield"
SUPPORTED_CONTEXTS = frozenset({CONTEXT_FORMATION})
KNOWN_CONTEXTS = frozenset({CONTEXT_FORMATION, CONTEXT_AIR, CONTEXT_CONDUCTING_SHIELD})

_EM_CHANNEL_LIMITS = (
    (LOG10_RHO_MIN, LOG10_RHO_MAX),
    (-DIFF_LIMIT, DIFF_LIMIT),
    (-DIFF_LIMIT, DIFF_LIMIT),
)

def _finite_float(value, name):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError("%s must be a finite real number, got %r" % (name, value))
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite, got %r" % (name, value))
    return result


def _fixed_length(values, length, name):
    try:
        items = tuple(values)
    except TypeError:
        raise ValueError("%s must be a %d-sequence of finite reals" % (name, length))
    if len(items) != length:
        raise ValueError("%s must have exactly %d components, got %d" % (name, length, len(items)))
    return tuple(
        _finite_float(item, "%s[%d]" % (name, index)) for index, item in enumerate(items)
    )


def _strict_tick(value, name, period_ms):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer millisecond tick, got %r" % (name, value))
    if value < 0 or value > MAX_TICK_MS:
        raise ValueError("%s=%d is outside 0..%d" % (name, value, MAX_TICK_MS))
    if value % period_ms != 0:
        raise ValueError("%s=%d is off the %d ms grid" % (name, value, period_ms))
    return value


def _channel_index(channel):
    if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel < len(CHANNEL_NAMES):
        raise ValueError("channel index must be an int in 0..%d, got %r" % (len(CHANNEL_NAMES) - 1, channel))
    return channel


@dataclass(frozen=True)
class Pose:
    """Finite body pose: world position in metres and normalized xyzw quaternion.

    The orientation is validated (finite, non-degenerate) and normalized, so a
    zero/NaN/Inf or near-zero quaternion is refused before any scene query.
    Body axes: forward +Z, up +Y.
    """

    position_m: Tuple[float, float, float]
    orientation_xyzw: Tuple[float, float, float, float]

    def __post_init__(self):
        position = _fixed_length(self.position_m, 3, "position_m")
        raw = _fixed_length(self.orientation_xyzw, 4, "orientation_xyzw")
        norm = math.sqrt(sum(component * component for component in raw))
        if not math.isfinite(norm) or norm < 1e-9:
            raise ValueError("degenerate orientation quaternion (norm %r)" % (norm,))
        object.__setattr__(self, "position_m", position)
        object.__setattr__(self, "orientation_xyzw", tuple(component / norm for component in raw))


@dataclass(frozen=True)
class SensorSample:
    """Fixed-whitelist authority-to-bridge sample record (see module docstring)."""

    profile_id: str
    profile_status: str
    profile_note: str
    source_mode: str
    adc_tick_ms: int
    em_tick_ms: Optional[int]
    channel_values: Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]
    channel_counts: Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]
    quality: int

    def is_valid(self, channel):
        return bool(self.quality & (1 << _channel_index(channel)))

    def is_saturated(self, channel):
        return bool(self.quality & (1 << (4 + _channel_index(channel))))

    def is_held(self, channel):
        return bool(self.quality & (1 << (8 + _channel_index(channel))))

    @property
    def source_fault(self):
        return bool(self.quality & (1 << 12))

    def to_payload(self):
        """Explicit serializer: exact key whitelist, no __dict__, no internals."""
        return {
            "profile_id": self.profile_id,
            "profile_status": self.profile_status,
            "profile_note": self.profile_note,
            "source_mode": self.source_mode,
            "adc_tick_ms": int(self.adc_tick_ms),
            "em_tick_ms": None if self.em_tick_ms is None else int(self.em_tick_ms),
            "channel_values": [
                None if value is None else float(value) for value in self.channel_values
            ],
            "channel_counts": [
                None if value is None else int(value) for value in self.channel_counts
            ],
            "quality": int(self.quality),
        }


def _rotation_matrix(orientation_xyzw):
    x, y, z, w = orientation_xyzw
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (
        (1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)),
        (2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)),
        (2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)),
    )


def _valid_sigma(value):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        return False
    sample = float(value)
    if not math.isfinite(sample):
        return False
    return SIGMA_MIN_S_PER_M <= sample <= SIGMA_MAX_S_PER_M


def _counts_from_value(value, low, high):
    scaled = int(round((value - low) / (high - low) * COUNTS_MAX))
    if scaled < 0:
        return 0
    if scaled > COUNTS_MAX:
        return COUNTS_MAX
    return scaled


@functools.lru_cache(maxsize=1)
def _weight_table():
    """Deterministic body-local lattice rows: (dx, dy, dz, w_forward, w_+yaw, w_-yaw, w_+pitch, w_-pitch).

    Only rows with at least one non-zero lobe weight exist; the r = 0 centre
    sample is defined as lying on every lobe axis (cos(theta) = 1).  Points
    outside r <= 8 m or outside every beam are absent (prototype cropping).
    """
    sin_offset = math.sin(math.radians(LOBE_OFFSET_DEG))
    cos_offset = math.cos(math.radians(LOBE_OFFSET_DEG))
    axes = (
        (0.0, 0.0, 1.0),
        (sin_offset, 0.0, cos_offset),
        (-sin_offset, 0.0, cos_offset),
        (0.0, sin_offset, cos_offset),
        (0.0, -sin_offset, cos_offset),
    )
    cos_cone = math.cos(math.radians(CONE_HALF_ANGLE_DEG))
    d_v = STEP_M ** 3
    limit = int(round(SUPPORT_M / STEP_M))
    rows = []

    def lobe_weights(cosines, radius):
        weights = []
        for cosine in cosines:
            if cosine >= cos_cone:
                weight = (
                    cosine * cosine
                    * math.exp(-radius / 4.0)
                    / ((radius + NEAR_FIELD_SOFTENING_M) ** 2)
                    * d_v
                )
            else:
                weight = 0.0
            weights.append(weight)
        return weights

    centre = lobe_weights((1.0, 1.0, 1.0, 1.0, 1.0), 0.0)
    rows.append((0.0, 0.0, 0.0, centre[0], centre[1], centre[2], centre[3], centre[4]))

    for i in range(0, limit + 1):
        dx = i * STEP_M
        for j in range(0, limit + 1):
            dy = j * STEP_M
            for k in range(1, limit + 1):
                dz = k * STEP_M
                r2 = dx * dx + dy * dy + dz * dz
                if r2 > SUPPORT_M * SUPPORT_M:
                    continue
                radius = math.sqrt(r2)
                ux, uy, uz = dx / radius, dy / radius, dz / radius
                cosines = tuple(ux * a[0] + uy * a[1] + uz * a[2] for a in axes)
                weights = lobe_weights(cosines, radius)
                if not any(weights):
                    continue
                forward, yaw_plus, yaw_minus, pitch_plus, pitch_minus = weights
                rows.append((dx, dy, dz, forward, yaw_plus, yaw_minus, pitch_plus, pitch_minus))
                if i > 0:
                    rows.append((-dx, dy, dz, forward, yaw_minus, yaw_plus, pitch_plus, pitch_minus))
                if j > 0:
                    rows.append((dx, -dy, dz, forward, yaw_plus, yaw_minus, pitch_minus, pitch_plus))
                if i > 0 and j > 0:
                    rows.append((-dx, -dy, dz, forward, yaw_minus, yaw_plus, pitch_minus, pitch_plus))
    return tuple(rows)

def _kernel_channels(pose_obj, sampler):
    """Weighted-conductivity channels for one pose; None if any sample is invalid.

    The conductivity callback is authority-local only.  All samples are queried
    before any noise is drawn, so a fault changes no filter, walk or RNG state.
    """
    rows = _weight_table()
    tx, ty, tz = pose_obj.position_m
    rotation = _rotation_matrix(pose_obj.orientation_xyzw)
    m00, m01, m02 = rotation[0]
    m10, m11, m12 = rotation[1]
    m20, m21, m22 = rotation[2]
    sum_w = [0.0, 0.0, 0.0, 0.0, 0.0]
    sum_ws = [0.0, 0.0, 0.0, 0.0, 0.0]
    for row in rows:
        dx, dy, dz = row[0], row[1], row[2]
        wx = tx + m00 * dx + m01 * dy + m02 * dz
        wy = ty + m10 * dx + m11 * dy + m12 * dz
        wz = tz + m20 * dx + m21 * dy + m22 * dz
        sigma = sampler(wx, wy, wz)
        if not _valid_sigma(sigma):
            return None
        sigma = float(sigma)
        for lobe in range(5):
            weight = row[3 + lobe]
            if weight > 0.0:
                sum_w[lobe] += weight
                sum_ws[lobe] += weight * sigma
    log10_rho = [-math.log10(sum_ws[lobe] / sum_w[lobe]) for lobe in range(5)]
    return (log10_rho[0], log10_rho[1] - log10_rho[2], log10_rho[3] - log10_rho[4])


class ForwardProfile:
    """Causal authority-local candidate profile (acquire_em + sample_adc split).

    Noise streams: ``em_rng`` is consumed only on real EM acquisitions (white
    noise and random-walk increments); ``vibration_rng`` only on ADC samples.
    They must be independent and are for repeatable tests only - never a scene
    seed and never serialized.  Draw order per successful acquisition: three
    white draws (C0, C1, C2) then, for non-initial acquisitions, three
    random-walk draws (C0, C1, C2).  Per ADC sample: one vibration drive draw.
    """

    def __init__(self, *, em_rng=None, vibration_rng=None):
        if em_rng is None:
            em_rng = random.Random()
        if vibration_rng is None:
            vibration_rng = random.Random()
        if em_rng is vibration_rng:
            raise ValueError("em_rng and vibration_rng must be independent RNG objects")
        for rng, name in ((em_rng, "em_rng"), (vibration_rng, "vibration_rng")):
            if not callable(getattr(rng, "gauss", None)):
                raise ValueError("%s must provide gauss(mu, sigma)" % name)
        self._em_rng = em_rng
        self._vibration_rng = vibration_rng
        self._last_em_tick = None
        self._last_adc_tick = None
        self._em_attempt_tick = None
        self._em_attempt_ok = False
        self._em_success_tick = None
        self._em_values = None
        self._em_saturated = (False, False, False)
        self._em_response = (0.0, 0.0, 0.0)
        self._em_walk = (0.0, 0.0, 0.0)
        self._vibration_state = 0.0
        self._vibration_window = deque()

    def acquire_em(self, tick_ms, pose, *, context, sampler):
        """One real 20 Hz acquisition (tick on the 50 ms grid); returns None.

        Validation rejections (grid/clock/pose/context/sampler) raise ValueError
        and leave every state untouched, including the acquisition slot.
        Unsupported but known contexts ("air", "conducting_shield") and invalid
        conductivity samples consume the slot and record a source fault; they
        never query or fabricate readings.
        Callback/noise exceptions propagate, but consume the acquisition and
        invalidate held EM until a later successful acquisition. Catching an
        exception at the authority boundary cannot keep stale EM valid.
        """
        tick = _strict_tick(tick_ms, "tick_ms", EM_PERIOD_MS)
        if self._last_em_tick is not None and tick <= self._last_em_tick:
            raise ValueError(
                "EM tick %d is not after the previous acquisition tick %d"
                % (tick, self._last_em_tick)
            )
        if self._last_adc_tick is not None and tick <= self._last_adc_tick:
            raise ValueError(
                "EM tick %d is not after the last ADC read tick %d (no backfill of past samples)"
                % (tick, self._last_adc_tick)
            )
        if not isinstance(pose, Pose):
            raise ValueError("pose must be a validated Pose, got %s" % (type(pose).__name__,))
        if context not in KNOWN_CONTEXTS:
            raise ValueError("unknown EM context %r" % (context,))
        supported = context in SUPPORTED_CONTEXTS
        if supported and not callable(sampler):
            raise ValueError("sampler must be callable for supported medium context")
        self._last_em_tick = tick
        self._em_attempt_tick = tick
        self._em_attempt_ok = False
        if not supported:
            self._em_attempt_ok = False
            return None
        raw = _kernel_channels(pose, sampler)
        if raw is None:
            self._em_attempt_ok = False
            return None
        white = (
            self._em_rng.gauss(0.0, WHITE_SIGMA_LOG10),
            self._em_rng.gauss(0.0, WHITE_SIGMA_LOG10),
            self._em_rng.gauss(0.0, WHITE_SIGMA_LOG10),
        )
        if self._em_success_tick is None:
            response = raw
            walk = (0.0, 0.0, 0.0)
        else:
            dt_s = (tick - self._em_success_tick) / 1000.0
            alpha = 1.0 - math.exp(-dt_s / TAU_S)
            previous = self._em_response
            response = (
                previous[0] + alpha * (raw[0] - previous[0]),
                previous[1] + alpha * (raw[1] - previous[1]),
                previous[2] + alpha * (raw[2] - previous[2]),
            )
            walk = (
                self._em_walk[0] + self._em_rng.gauss(0.0, RW_SIGMA_PER_SQRT_S * math.sqrt(dt_s)),
                self._em_walk[1] + self._em_rng.gauss(0.0, RW_SIGMA_PER_SQRT_S * math.sqrt(dt_s)),
                self._em_walk[2] + self._em_rng.gauss(0.0, RW_SIGMA_PER_SQRT_S * math.sqrt(dt_s)),
            )
        values = []
        saturated = []
        for index in range(3):
            value = response[index] + walk[index] + white[index]
            low, high = _EM_CHANNEL_LIMITS[index]
            if value > high:
                values.append(high)
                saturated.append(True)
            elif value < low:
                values.append(low)
                saturated.append(True)
            else:
                values.append(value)
                saturated.append(False)
        self._em_response = response
        self._em_walk = walk
        self._em_values = tuple(values)
        self._em_saturated = tuple(saturated)
        self._em_success_tick = tick
        self._em_attempt_ok = True
        return None

    def sample_adc(self, tick_ms, *, contact_accel_g=None):
        """One 100 Hz ADC read (10 ms grid): held EM plus fresh vibration.

        The read never touches the conductivity callback and never draws EM
        noise; it observes only acquisitions at or before this tick.
        ``contact_accel_g`` is the authority-local, already-occurred signed
        contact/load acceleration in g for this tick (None = no contact) and is
        never serialized.
        """
        tick = _strict_tick(tick_ms, "tick_ms", ADC_PERIOD_MS)
        if self._last_adc_tick is not None and tick <= self._last_adc_tick:
            raise ValueError(
                "ADC tick %d is not after the previous ADC tick %d" % (tick, self._last_adc_tick)
            )
        if self._last_em_tick is not None and tick < self._last_em_tick:
            raise ValueError(
                "ADC tick %d is before the last EM acquisition tick %d (time reversal)"
                % (tick, self._last_em_tick)
            )
        if contact_accel_g is None:
            contact = 0.0
        else:
            contact = _finite_float(contact_accel_g, "contact_accel_g")
        self._last_adc_tick = tick

        noise = self._vibration_rng.gauss(0.0, VIB_DRIVE_SIGMA_G)
        state = VIB_AR_A * self._vibration_state + (1.0 - VIB_AR_A) * (contact + noise)
        self._vibration_state = state
        if state > VIB_RANGE_G:
            window_sample, clipped = VIB_RANGE_G, True
        elif state < -VIB_RANGE_G:
            window_sample, clipped = -VIB_RANGE_G, True
        else:
            window_sample, clipped = state, False
        window = self._vibration_window
        window.append((tick, window_sample, clipped))
        oldest_needed = tick - (VIB_WINDOW_SAMPLES - 1) * ADC_PERIOD_MS
        while window and window[0][0] < oldest_needed:
            window.popleft()
        vibration_valid = len(window) == VIB_WINDOW_SAMPLES and window[0][0] == oldest_needed
        if vibration_valid:
            total = 0.0
            vibration_saturated = False
            for _sample_tick, sample_value, sample_clipped in window:
                total += sample_value * sample_value
                vibration_saturated = vibration_saturated or sample_clipped
            vibration_value = math.sqrt(total / VIB_WINDOW_SAMPLES)
        else:
            vibration_value = None
            vibration_saturated = False

        if self._em_attempt_tick is None:
            source_fault = True
        elif not self._em_attempt_ok and tick >= self._em_attempt_tick:
            source_fault = True
        elif self._em_success_tick is None:
            source_fault = True
        else:
            gap = tick - self._em_success_tick
            if gap > HEARTBEAT_TIMEOUT_MS:
                source_fault = True
            else:
                source_fault = False

        if source_fault:
            em_valid = False
            em_held = False
        else:
            em_valid = True
            em_held = (tick - self._em_success_tick) > 0

        if em_valid:
            em_tick = self._em_success_tick
            em_values = self._em_values
            em_saturated = self._em_saturated
        else:
            em_tick = None
            em_values = None
            em_saturated = (False, False, False)

        channel_values = []
        channel_counts = []
        for index in range(3):
            if em_valid:
                value = em_values[index]
                channel_values.append(value)
                channel_counts.append(_counts_from_value(value, *_EM_CHANNEL_LIMITS[index]))
            else:
                channel_values.append(None)
                channel_counts.append(None)
        channel_values.append(vibration_value)
        channel_counts.append(
            None if vibration_value is None else _counts_from_value(vibration_value, 0.0, VIB_RANGE_G)
        )

        quality = 0
        if em_valid:
            for index in range(3):
                quality |= 1 << index
                if em_saturated[index]:
                    quality |= 1 << (4 + index)
                if em_held:
                    quality |= 1 << (8 + index)
        if vibration_valid:
            quality |= 1 << 3
            if vibration_saturated:
                quality |= 1 << 7
        if source_fault:
            quality |= 1 << 12

        return SensorSample(
            profile_id=PROFILE_ID,
            profile_status=PROFILE_STATUS,
            profile_note=PROFILE_NOTE,
            source_mode=SOURCE_MODE,
            adc_tick_ms=tick,
            em_tick_ms=em_tick,
            channel_values=tuple(channel_values),
            channel_counts=tuple(channel_counts),
            quality=quality,
        )

"""Isolated candidate simulated sensor for accepted continuous native snapshots.

Root alone supplies complete private world/material data and authenticates the
actual accepted snapshot before submit(). This module grants no motion/source
authority. It never imports old RootBook, native, collision or board code.
The trusted-process private attributes are not an operating-system boundary.

Only the original spatial EM kernel, scalar sigma sampler and count conversion
are reused. Old grid/ADC/temporal/noise/custody semantics are NOT claimed here.
One worker binds one world epoch; after an edit Root retires it and constructs
a new one. Keep this worker and all private inputs away from control algorithms.
"""
from __future__ import annotations

import ast
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, is_dataclass
import hashlib
import json
import math
import numbers
from pathlib import Path
import sys
import threading
import time
from types import ModuleType
import uuid

REQUIREMENTS_SHA256 = "2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d"
_FORWARD_SHA256 = "6a5f70a6acdaa6de52fc72d678d452956861370e1d143b70219ced107c5a04c9"
_SIGMA_SHA256 = "c7eec4a9fe5e57434d11a0d807d15fcf7dc215ab55db7b01700bf0d9bf5d4c37"
_RANK = {"casing": 5, "fault": 4, "void": 3, "water": 2, "hard_rock": 1}
_MAX_NS = (1 << 63) - 1


def _ns(value):
    if type(value) is not int or not 0 <= value <= _MAX_NS:
        raise ValueError("uint63 QPC nanoseconds required")
    return value


def _label(value):
    if type(value) is not str or not 1 <= len(value) <= 128 or not value.isascii():
        raise ValueError("bounded public identity required")
    return value


def _real(value):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError("finite real scalar required")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("finite real scalar required")
    return value


def _vector(value, size):
    value = tuple(_real(x) for x in value)
    if len(value) != size:
        raise ValueError("fixed size vector required")
    return value


@dataclass(frozen=True)
class SnapshotPose:
    """Detached immutable accepted input; construction is NOT authentication.

    This flat form also accepts the frozen 784 SnapshotPose through submit();
    that form is copied from segment/pose without traversing its readback.
    Position, normalized xyzw and speed are retained, never predicted/replaced.
    """
    segment_id: str
    world_epoch: str
    at_qpc_ns: int
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    speed_m_s: float

    def __post_init__(self):
        _label(self.segment_id)
        _label(self.world_epoch)
        _ns(self.at_qpc_ns)
        position = _vector(self.position_m, 3)
        orientation = _vector(self.orientation_xyzw, 4)
        norm = math.hypot(*orientation)
        if abs(norm - 1.) > 1e-6:
            raise ValueError("accepted normalized orientation required")
        speed = _real(self.speed_m_s)
        if speed < 0:
            raise ValueError("nonnegative accepted speed required")
        object.__setattr__(self, "position_m", position)
        object.__setattr__(self, "orientation_xyzw", orientation)
        object.__setattr__(self, "speed_m_s", speed)


def _snapshot(value):
    if not is_dataclass(value) or not value.__dataclass_params__.frozen:
        raise TypeError("immutable accepted snapshot required")
    if isinstance(value, SnapshotPose):
        return value, value.at_qpc_ns
    if getattr(value, "field_return_qpc_ns", None) is not None:
        raise ValueError("snapshot already has a field completion")
    if hasattr(value, "segment_id"):
        copied = SnapshotPose(value.segment_id, value.world_epoch, value.at_qpc_ns,
            value.position_m, value.orientation_xyzw, value.speed_m_s)
    else:
        copied = SnapshotPose(value.segment.segment_id, value.segment.world_epoch,
            value.at_qpc_ns, value.pose.position_m, value.pose.orientation_xyzw,
            value.pose.speed_m_s)
    # The original 784 read-return bracket is relevant to completion, but its
    # readback object is never traversed, serialized, or replaced by this code.
    read_return = _ns(getattr(value, "read_return_qpc_ns", copied.at_qpc_ns))
    if read_return < copied.at_qpc_ns:
        raise ValueError("snapshot read bracket precedes acquisition")
    return copied, read_return


@dataclass(frozen=True)
class SensorResult:
    snapshot: SnapshotPose
    completed_qpc_ns: int
    channel_counts: tuple[int | None, int | None, int | None, int | None]
    quality: int
    boundary_policy: str
    sample_epsilon_m: float

    def to_payload(self):
        """Exhaustive whitelist; no asdict(), truth, exceptions or raw objects."""
        s = self.snapshot
        return dict(
            schema="deepeye_live_sensor_candidate_v1",
            requirements_sha256=REQUIREMENTS_SHA256,
            world_epoch=s.world_epoch, segment_id=s.segment_id,
            at_qpc_ns=str(s.at_qpc_ns), position_m=list(s.position_m),
            orientation_xyzw=list(s.orientation_xyzw), speed_m_s=s.speed_m_s,
            completed_qpc_ns=str(self.completed_qpc_ns),
            channel_counts=list(self.channel_counts), quality=self.quality,
            profile=dict(
                profile_id="live_snapshot_spatial_em_candidate_v1",
                source_mode="candidate_simulated_sensor", profile_status="candidate_only",
                formal_qualification="not_run",
                acquisition="accepted_snapshot_spatial_kernel_only",
                temporal_filter_noise="not_applied_in_this_isolated_scope",
                channel_names=["log10_rho_apparent", "yaw_log10_rho_difference",
                               "pitch_log10_rho_difference", "near_bit_vibration_rms_g"],
                channel_limits=[[-0.6989700043360187, 3.3010299956639813],
                                [-2., 2.], [-2., 2.], [0., 2.]],
                counts_max=4095, counts_calibration="normalized_proxy_only",
                support_m=8., quadrature_step_m=0.25,
                cone_half_angle_deg=30., lobe_offset_deg=20.,
                near_field_softening_m=0.25, body_forward="+Z", body_up="+Y",
                boundary_policy=self.boundary_policy, sample_epsilon_m=self.sample_epsilon_m,
                c3_status="null_no_contact_history",
                quality_encoding="bits0..3_valid;4..7_saturated;8..11_held;12_source_fault",
            ))


def _verified_bytes(path, digest):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("pinned numeric dependency changed; Root review required")
    return data


def _numeric_modules(source_root):
    """Execute pinned pure source only; never import its authority dependencies.

    The unchanged _sample_sigma_pure AST is bound to a NEW _SnapshotSigma class.
    No OwnedWorldField object is forged; no old checks/receipts are bypassed.
    """
    root = Path(source_root)
    contract = json.loads((root / "docs/competition/deepeye-2026/immutable_scope.json").read_text(
        encoding="utf-8-sig"))
    digest = hashlib.sha256(json.dumps(contract["requirements"], ensure_ascii=False,
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if (contract["contract_id"] != "DEEPEYE-HUMAN-LOCK-20261014"
            or contract["revision"] != 2 or digest != REQUIREMENTS_SHA256
            or contract["requirements_sha256"] != REQUIREMENTS_SHA256):
        raise ValueError("human revision2 requirements mismatch")
    directory = root / "competition/deepeye/simulation/sensors"
    forward_path = directory / "forward_profile.py"
    sigma_path = directory / "owned_world_field.py"
    forward_bytes = _verified_bytes(forward_path, _FORWARD_SHA256)
    sigma_bytes = _verified_bytes(sigma_path, _SIGMA_SHA256)
    forward_name = "_live_sensor793_forward_" + uuid.uuid4().hex
    forward = ModuleType(forward_name)
    sys.modules[forward_name] = forward
    try:
        exec(compile(forward_bytes, str(forward_path), "exec"), forward.__dict__)
    finally:
        del sys.modules[forward_name]
    source = ast.parse(sigma_bytes, filename=str(sigma_path))
    sampler = next(method for node in source.body
        if isinstance(node, ast.ClassDef) and node.name == "OwnedWorldField"
        for method in node.body
        if isinstance(method, ast.FunctionDef) and method.name == "_sample_sigma_pure")
    scalar = next(node for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == "_number")
    # The only profile-dependent numeric branch compares a singleton. It is an
    # isolated sentinel for that arithmetic branch, never an old source receipt.
    closed_boundary = object()
    namespace = dict(math=math, numbers=numbers,
        DEMO_KNOWN_BOX_CLOSED_BOUNDARY_V1=closed_boundary)
    exec(compile(ast.Module(body=[scalar, sampler], type_ignores=[]),
                 str(sigma_path) + "::isolated_numeric_only", "exec"), namespace)
    return forward, namespace["_sample_sigma_pure"], closed_boundary


class _SnapshotSigma:
    """Private immutable scalar tuples; new isolated scope, no old owner type."""
    __slots__ = ("_pieces", "_background", "_epsilon", "_demo_boundary_profile",
                 "_boundary_count", "_boundary_records", "_em_scope_factory", "_sample")

    def __init__(self, pieces, background, epsilon, boundary, sample):
        self._pieces, self._background, self._epsilon = pieces, background, epsilon
        self._demo_boundary_profile = boundary
        self._boundary_count, self._boundary_records = 0, []
        self._em_scope_factory, self._sample = None, sample

    def sample_sigma(self, x, y, z):
        return self._sample(self, x, y, z)


class LiveSensorWorker:
    """Root-private, one-epoch asynchronous worker; one in-flight job, no queue.

    private_pieces: complete iterable of dict(material, kind, centre, dimensions,
    matrix); dimensions are nominal HALF sizes; matrix maps local to world.
    Box and elliptical cylinder use the original sigma classification.
    All five material policies are explicit; None means unknown, never air.
    background_sigma is an explicit engineering assumption in S/m.

    submit(snapshot) -> Future[SensorResult] or None if busy. Do not wait on the
    motion/render path. latest(world_epoch) is nonblocking; Root assesses age
    from at_qpc_ns (not completion) and retains original native readback itself.
    No task duration, sample-count or segment-duration cap is imposed here.
    """

    def __init__(self, *, source_root, world_epoch, private_pieces,
                 background_sigma, material_sigma, sample_epsilon_m=None,
                 boundary_policy="strict_unknown", clock_ns=time.perf_counter_ns):
        self._epoch = _label(world_epoch)
        if not callable(clock_ns):
            raise TypeError("same host QPC nanosecond clock required")
        self._clock = clock_ns
        self._forward, sample, closed_boundary = _numeric_modules(source_root)
        if type(material_sigma) is not dict or set(material_sigma) != set(_RANK):
            raise ValueError("complete explicit five-material sigma policy required")

        def sigma(value):
            value = _real(value)
            if not self._forward.SIGMA_MIN_S_PER_M <= value <= self._forward.SIGMA_MAX_S_PER_M:
                raise ValueError("sigma outside original candidate envelope")
            return value

        policy = {k: None if v is None else sigma(v) for k, v in material_sigma.items()}
        background = sigma(background_sigma)
        epsilon = 0. if sample_epsilon_m is None else _real(sample_epsilon_m)
        if sample_epsilon_m is not None and epsilon <= 0:
            raise ValueError("explicit boundary uncertainty band must be positive")
        if boundary_policy not in ("strict_unknown", "known_box_closed_candidate"):
            raise ValueError("unknown numeric boundary policy")
        if boundary_policy == "known_box_closed_candidate" and epsilon != 0.:
            raise ValueError("closed nominal boundary cannot replace uncertainty band")
        compiled = []
        for part in private_pieces:
            if len(compiled) >= 256:
                raise ValueError("complete world exceeds original piece support")
            if type(part) is not dict or set(part) != {
                    "material", "kind", "centre", "dimensions", "matrix"}:
                raise ValueError("exact private piece shape required; never skip a piece")
            if part["material"] not in _RANK or part["kind"] not in ("box", "cylinder"):
                raise ValueError("unsupported private piece; whole field refused")
            centre, dimensions = _vector(part["centre"], 3), _vector(part["dimensions"], 3)
            matrix = tuple(_vector(row, 3) for row in part["matrix"])
            if len(matrix) != 3 or min(dimensions) <= 0:
                raise ValueError("positive half sizes and finite 3x3 rotation required")
            for i in range(3):
                for j in range(3):
                    if abs(math.fsum(matrix[k][i] * matrix[k][j] for k in range(3))
                           - (1. if i == j else 0.)) > 1e-6:
                        raise ValueError("orthonormal private piece rotation required")
            determinant = (matrix[0][0] * (matrix[1][1]*matrix[2][2]-matrix[1][2]*matrix[2][1])
                - matrix[0][1] * (matrix[1][0]*matrix[2][2]-matrix[1][2]*matrix[2][0])
                + matrix[0][2] * (matrix[1][0]*matrix[2][1]-matrix[1][1]*matrix[2][0]))
            if abs(determinant - 1.) > 1e-6:
                raise ValueError("right-handed private piece rotation required")
            compiled.append((_RANK[part["material"]], policy[part["material"]],
                part["kind"], centre, dimensions, matrix))
        self._field = _SnapshotSigma(tuple(compiled), background, epsilon,
            closed_boundary if boundary_policy == "known_box_closed_candidate" else None, sample)
        self._boundary_policy, self._epsilon = boundary_policy, epsilon
        self._lock = threading.Lock()
        self._closed, self._future, self._latest, self._last_at = False, None, None, -1
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="live-sensor793")

    @classmethod
    def from_private_scene(cls, *, private_scene, **kwargs):
        """Compile all old Scene.objects/parts without importing old authority.

        Root supplies the complete epoch-matching scene. This is numerical
        adaptation only, with no scene/native custody or collision authority.
        """
        if len(private_scene.objects) > 30:
            raise ValueError("complete world exceeds original object support")
        parts = [dict(material=obj.material, kind=part.kind, centre=part.centre,
                      dimensions=part.dimensions, matrix=part.matrix)
                 for obj in private_scene.objects for part in obj.parts]
        return cls(private_pieces=parts, **kwargs)

    def submit(self, snapshot) -> Future | None:
        snapshot, read_return = _snapshot(snapshot)
        with self._lock:
            if self._closed:
                raise RuntimeError("source worker retired")
            if snapshot.world_epoch != self._epoch:
                raise ValueError("source world epoch mismatch; construct a new worker")
            if snapshot.at_qpc_ns <= self._last_at:
                raise ValueError("duplicate or reordered acquisition refused")
            now = _ns(self._clock())
            if now < read_return or now < snapshot.at_qpc_ns:
                raise ValueError("future snapshot or wrong QPC clock domain")
            if self._future is not None and not self._future.done():
                return None  # No queue/backfill, no implicit stop or sample synthesis.
            self._last_at = snapshot.at_qpc_ns
            self._future = self._pool.submit(self._evaluate, snapshot, now)
            return self._future

    def _evaluate(self, snapshot, received_qpc_ns):
        counts, quality = (None, None, None, None), 1 << 12
        try:
            pose = self._forward.Pose(snapshot.position_m, snapshot.orientation_xyzw)
            raw = self._forward._kernel_channels(pose, self._field.sample_sigma)
            if raw is not None:
                values, quality = [], 7
                for i, (value, (low, high)) in enumerate(zip(raw, self._forward._EM_CHANNEL_LIMITS)):
                    value = _real(value)
                    if not low <= value <= high:
                        quality |= 1 << (4 + i)
                    value = min(high, max(low, value))
                    values.append(self._forward._counts_from_value(value, low, high))
                if len(values) != 3:
                    raise ValueError("incomplete numerical result")
                counts = (*values, None)
        except Exception:
            # Exceptions may embed private coordinates/materials. Do not retain,
            # log, attach to a Future, or return those exception objects/text.
            counts, quality = (None, None, None, None), 1 << 12
        completed = _ns(self._clock())
        if completed < received_qpc_ns:
            raise ValueError("source completion QPC clock regressed")
        result = SensorResult(snapshot, completed, counts, quality,
                              self._boundary_policy, self._epsilon)
        with self._lock:
            if not self._closed:
                self._latest = result
        return result

    def latest(self, world_epoch) -> SensorResult | None:
        with self._lock:
            return None if self._closed or world_epoch != self._epoch else self._latest

    def close(self, *, wait=True):
        # Root calls close outside the frame path. wait=False does not claim an
        # already executing numerical call was terminated; its result is retired.
        with self._lock:
            self._closed, self._latest = True, None
        self._pool.shutdown(wait=wait, cancel_futures=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


__all__ = ["SnapshotPose", "SensorResult", "LiveSensorWorker", "REQUIREMENTS_SHA256"]

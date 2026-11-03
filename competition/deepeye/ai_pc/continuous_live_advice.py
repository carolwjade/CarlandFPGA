"""Candidate continuous EM3 advice. Pure inference; no motion/board authority.

Root authenticates FPGA E4 counts and original acquisition identity before use.
Only pinned numerical AST is reused, never old validators or qualification.
"""
from __future__ import annotations

import ast
from concurrent.futures import Future, ThreadPoolExecutor
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import threading
import time
from types import SimpleNamespace

REQUIREMENTS_SHA256 = "2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d"
CORE_SHA256 = "fad1eda8c0d9e31f35d2f4c98d48dbd0678d49b283cbb0e10051ac003b9cb8fa"
CORE_RELATIVE_PATH = "competition/deepeye/ai_pc/demo30h_owned_em3_package_v8/em3_core.py"
PROFILE_ID = "deepeye_continuous_em3_advice_candidate_797_v1"


@dataclass(frozen=True)
class LiveProfile:
    """Explicit uncalibrated engineering policy, not a sensor/board guarantee."""
    background_c0: float = 1.0
    max_source_age_s: float = 5.0
    max_current_pose_age_s: float = 0.25
    initial_speed_cap_m_s: float = 0.025
    max_steer_deg: float = 8.0
    exit_lookahead_m: float = 0.5

    def __post_init__(self):
        for value in asdict(self).values():
            _finite(value)
        if not (-0.6989700043360187 <= self.background_c0 <= 3.3010299956639813
                and 0 < self.max_source_age_s <= 5.0 and 0 < self.max_current_pose_age_s <= 0.25
                and 0 < self.initial_speed_cap_m_s <= 0.25
                and 0 < self.max_steer_deg <= 15 and 0 < self.exit_lookahead_m <= 1000):
            raise ValueError("live engineering profile outside supported policy")


def _finite(value):
    if type(value) not in (int, float):
        raise ValueError("finite numeric scalar required")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("finite numeric scalar required")
    return float(value)


def _ns(value):
    if type(value) is str and re.fullmatch(r"0|[1-9][0-9]{0,18}", value):
        converted = int(value)
        if converted < (1 << 63):
            return converted
    if type(value) is int and 0 <= value < (1 << 63):
        return value
    raise ValueError("QPC nanoseconds must be integer or canonical decimal string")


def _label(value):
    if type(value) is not str or not 1 <= len(value) <= 128 or not value.isascii():
        raise ValueError("bounded public identity required")
    return value


def _keys(value, required, optional=frozenset()):
    if type(value) is not dict or not required <= value.keys() or value.keys() - required - optional:
        raise ValueError("exact public input fields required")


def _vector(value, length):
    if type(value) not in (list, tuple) or len(value) != length:
        raise ValueError("fixed length public vector required")
    result = [_finite(v) for v in value]
    if any(abs(v) > 1000 for v in result):
        raise ValueError("public spatial coordinate outside candidate 1000 m envelope")
    return result


def _pose(pose, *, snapshot=False):
    required = {"position_m", "orientation_xyzw"}
    if snapshot:
        required |= {"at_qpc_ns", "speed_m_s"}
    _keys(pose, required)
    _vector(pose["position_m"], 3)
    q = _vector(pose["orientation_xyzw"], 4)
    if abs(math.hypot(*q) - 1.) > 1e-6:
        raise ValueError("normalized original own orientation required")
    if snapshot:
        _ns(pose["at_qpc_ns"])
        if _finite(pose["speed_m_s"]) < 0:
            raise ValueError("nonnegative own speed required")


def _load_numeric(source_root):
    """Hash entire source, execute only selected unchanged numerical AST nodes.

    The ranking loop and directional-risk assignments are copied unchanged from
    recommend() into new functions with small explicit numerical inputs. The
    original recommend(), _validate(), binding/grid/custody code never executes.
    """
    root = Path(source_root)
    contract = json.loads((root / "docs/competition/deepeye-2026/immutable_scope.json").read_text(
        encoding="utf-8-sig"))
    requirements_hash = hashlib.sha256(json.dumps(contract["requirements"], ensure_ascii=False,
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if (contract.get("contract_id") != "DEEPEYE-HUMAN-LOCK-20261014"
            or contract.get("revision") != 2 or requirements_hash != REQUIREMENTS_SHA256
            or contract.get("requirements_sha256") != REQUIREMENTS_SHA256):
        raise ValueError("pinned revision2 requirements mismatch")
    path = root / CORE_RELATIVE_PATH
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != CORE_SHA256:
        raise ValueError("pinned EM3 numeric source changed; Root review required")
    tree = ast.parse(data, filename=str(path))
    functions = {"_need", "_integer", "decode_counts", "_rotate", "_norm", "_clip",
                 "_direction_supported", "_poses_applicable", "_contact_penalty", "_risk"}
    constants = {"MAX_REUSE_DISPLACEMENT_M", "MAX_REUSE_FORWARD_ANGLE_DEG",
                 "MAX_NATIVE_DIRECTION_ANGLE_DEG", "_ANGLE_DOT_TOLERANCE",
                 "C3_MISSING_RISK_PENALTY", "C3_MISSING_UNCERTAINTY_PENALTY",
                 "C3_MISSING_SPEED_CAP_M_S", "DEMO_AGE_NORMALIZATION_MS"}
    selected = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
        elif isinstance(node, ast.ClassDef) and node.name == "Rejected":
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in constants for target in node.targets):
            selected.append(node)
    recommend = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "recommend")

    def assigns(node, name):
        return isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets)

    first = next(i for i, n in enumerate(recommend.body) if assigns(n, "inverse_native"))
    loop = recommend.body[first + 2]
    if not isinstance(loop, ast.For) or not isinstance(loop.target, ast.Name) or loop.target.id != "x":
        raise ValueError("pinned ranking AST structure mismatch")
    wrapper = ast.parse('''
def rank(values, q, native_q, goal, position_m, map_cells, executed_actions, background_c0):
    request = {"pose": {"position_m": position_m}, "executed_actions": executed_actions}
    result = {"map_cells": map_cells}
''').body[0]
    wrapper.body += copy.deepcopy(recommend.body[first:first + 3])
    wrapper.body += ast.parse("return min(candidates) if candidates else None").body
    directional = ast.parse("def directional_risk(values, native, background_c0):\n    pass").body[0]
    inner = next(n for n in loop.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                 and n.target.id == "y")
    directional.body = copy.deepcopy([n for n in inner.body if assigns(n, "predicted") or assigns(n, "risk")])
    if len(directional.body) != 2:
        raise ValueError("pinned directional risk AST structure mismatch")
    directional.body += ast.parse("return risk").body
    namespace = {"math": math}
    module = ast.fix_missing_locations(ast.Module(body=selected + [wrapper, directional], type_ignores=[]))
    exec(compile(module, str(path) + "::numeric_only_live797", "exec"), namespace)
    return SimpleNamespace(**{key: value for key, value in namespace.items() if key != "__builtins__"})


def _validated_copy(request, numeric):
    _keys(request, {"world_epoch", "observation", "current_pose", "public_goal",
                    "executed_actions", "user_speed_cap_m_s", "paused"})
    _label(request["world_epoch"])
    if type(request["paused"]) is not bool or _finite(request["user_speed_cap_m_s"]) < 0:
        raise ValueError("explicit pause and nonnegative user speed cap required")
    obs = request["observation"]
    _keys(obs, {"world_epoch", "segment_id", "at_qpc_ns", "completed_qpc_ns", "position_m",
                "orientation_xyzw", "speed_m_s", "channel_counts", "quality", "board_frame_sha256"},
          {"source_record_sha256", "board_return_qpc_ns"})
    _label(obs["world_epoch"]); _label(obs["segment_id"])
    for field in ("board_frame_sha256", "source_record_sha256"):
        if field in obs and (type(obs[field]) is not str or re.fullmatch("[0-9a-f]{64}", obs[field]) is None):
            raise ValueError("original lowercase SHA256 required")
    for field in ("at_qpc_ns", "completed_qpc_ns", "board_return_qpc_ns"):
        if field in obs:
            _ns(obs[field])
    _pose({k: obs[k] for k in ("at_qpc_ns", "position_m", "orientation_xyzw", "speed_m_s")}, snapshot=True)
    numeric.decode_counts(obs["channel_counts"])
    quality = obs["quality"]
    if type(quality) is not int or not 0 <= quality <= 0x1fff:
        raise ValueError("13 bit quality required")
    for i, count in enumerate(obs["channel_counts"]):
        if (count is not None) != bool(quality & (1 << i)):
            raise ValueError("count/null quality mismatch")
        if count is None and quality & ((16 << i) | (256 << i)):
            raise ValueError("invalid channel saturation/held flags")
    if obs["channel_counts"][3] is not None or quality & 0x888:
        raise ValueError("live EM3 profile requires genuinely null C3")
    _pose(request["current_pose"], snapshot=True)
    goal = request["public_goal"]
    _keys(goal, {"exit_center_m", "exit_outward_normal_world", "gate_radius_m"},
          {"entry_center_m", "entry_inward_normal_world", "exit_clearance_m"})
    _vector(goal["exit_center_m"], 3)
    normal = _vector(goal["exit_outward_normal_world"], 3)
    if abs(math.hypot(*normal) - 1.) > 1e-6 or _finite(goal["gate_radius_m"]) != 0.25:
        raise ValueError("unit outward normal and revision2 0.25 m gate radius required")
    if "entry_center_m" in goal:
        _vector(goal["entry_center_m"], 3)
    if "entry_inward_normal_world" in goal:
        if abs(math.hypot(*_vector(goal["entry_inward_normal_world"], 3)) - 1.) > 1e-6:
            raise ValueError("unit entry normal required")
    if "exit_clearance_m" in goal and not 0 < _finite(goal["exit_clearance_m"]) <= 1000:
        raise ValueError("positive public own-body clearance required")
    actions = request["executed_actions"]
    if type(actions) is not list:
        raise ValueError("executed action history must be an array")
    last = -1
    for action in actions:
        _keys(action, {"world_epoch", "at_qpc_ns", "from_pose", "to_pose"})
        _label(action["world_epoch"])
        stamp = _ns(action["at_qpc_ns"])
        if stamp < last:
            raise ValueError("executed action time reversed")
        last = stamp
        _pose(action["from_pose"]); _pose(action["to_pose"])
    # All values have been checked before copying: no opaque source/native objects.
    return copy.deepcopy(request)


def _stop(result, reason):
    result.update(status="STOP", reason=reason, speed_limit_m_s=0.,
                  target_direction_world=[0., 0., 0.], direction_world=[0., 0., 0.])
    return result


def _guidance(goal, position, lookahead):
    normal = goal["exit_outward_normal_world"]
    delta = [g - p for g, p in zip(goal["exit_center_m"], position)]
    along = sum(a * b for a, b in zip(delta, normal))
    lateral = [v - along * n for v, n in zip(delta, normal)]
    clearance = goal.get("exit_clearance_m", lookahead)
    # Aim through the centre plane and onward along its outward normal. Near the
    # portal lateral correction is stronger; reaching centre never means success.
    gain = 1. + lookahead / (lookahead + abs(along))
    vector = [gain * l + max(lookahead, along + clearance) * n for l, n in zip(lateral, normal)]
    length = math.hypot(*vector)
    return [v / length for v in vector]


def _moderate(forward, target, max_angle_deg):
    cosine = max(-1., min(1., sum(a * b for a, b in zip(forward, target))))
    angle = math.acos(cosine)
    limit = math.radians(max_angle_deg)
    if angle > limit:
        lateral = [t - cosine * f for t, f in zip(target, forward)]
        length = math.hypot(*lateral)
        target = [math.cos(limit) * f + math.sin(limit) * l / length for f, l in zip(forward, lateral)]
    length = math.hypot(*target)
    return [v / length for v in target]


class LiveAIWorker:
    """Epoch-bound pure core plus optional one-inflight/no-backlog Future wrapper.

    Construct outside motion path. infer(request, now_qpc_ns=...) is synchronous
    and clock-free; submit(request) never waits for inference. Root rechecks the
    original epoch/acquisition/own pose and live pause before acting on advice.
    """

    def __init__(self, *, source_root, world_epoch, profile=None, clock_ns=time.perf_counter_ns):
        self.world_epoch = _label(world_epoch)
        self.profile = LiveProfile() if profile is None else profile
        if type(self.profile) is not LiveProfile or not callable(clock_ns):
            raise TypeError("LiveProfile and same-domain QPC clock required")
        self._numeric = _load_numeric(source_root)
        self._clock = clock_ns
        self._lock = threading.Lock()
        self._closed, self._future, self._latest, self._last_at = False, None, None, -1
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="live-ai797")

    def infer(self, request, *, now_qpc_ns):
        """Pure deterministic numerical advice, with no inference-completion claim."""
        req = _validated_copy(request, self._numeric)
        return self._infer(req, _ns(now_qpc_ns))

    def _infer(self, req, now):
        n, p = self._numeric, self.profile
        obs, current = req["observation"], req["current_pose"]
        acquired, completed, current_at = (_ns(obs["at_qpc_ns"]),
            _ns(obs["completed_qpc_ns"]), _ns(current["at_qpc_ns"]))
        values = n.decode_counts(obs["channel_counts"])
        source_pose = {k: copy.deepcopy(obs[k]) for k in ("position_m", "orientation_xyzw", "speed_m_s")}
        result = dict(schema=PROFILE_ID, candidate_only=True, authorization="none", status="STOP",
            reason="unassessed", world_epoch=req["world_epoch"], segment_id=obs["segment_id"],
            source_acquisition_qpc_ns=obs["at_qpc_ns"], source_completed_qpc_ns=obs["completed_qpc_ns"],
            board_frame_sha256=obs["board_frame_sha256"], source_pose=source_pose,
            current_pose=copy.deepcopy(current), evaluated_qpc_ns=str(now), inference_completed_qpc_ns=None,
            decoded_features=values, quality=obs["quality"], missing_feature_mask=(~obs["quality"]) & 15,
            c3_observed=False, missing_c3_risk_penalty=n.C3_MISSING_RISK_PENALTY,
            missing_c3_uncertainty_penalty=n.C3_MISSING_UNCERTAINTY_PENALTY,
            risk=1., uncertainty=1., speed_limit_m_s=0., target_direction_world=[0., 0., 0.],
            direction_world=[0., 0., 0.], yaw_delta_deg=0., pitch_delta_deg=0.,
            numeric_source_sha256=CORE_SHA256, requirements_sha256=REQUIREMENTS_SHA256,
            engineering_profile=asdict(p), prior_package_qualification="not_inherited")
        for key in ("source_record_sha256", "board_return_qpc_ns"):
            if key in obs:
                result[key] = obs[key]
        if (req["world_epoch"] != self.world_epoch or obs["world_epoch"] != self.world_epoch
                or any(a["world_epoch"] != self.world_epoch for a in req["executed_actions"])):
            return _stop(result, "world_epoch_mismatch")
        if (not acquired <= completed <= now or not acquired <= current_at <= now
                or any(_ns(a["at_qpc_ns"]) > current_at for a in req["executed_actions"])
                or ("board_return_qpc_ns" in obs and not completed <= _ns(obs["board_return_qpc_ns"]) <= now)):
            return _stop(result, "future_or_reversed_time")
        age_s = (now - acquired) / 1e9
        result["source_age_s"] = age_s
        if age_s > p.max_source_age_s:
            return _stop(result, "original_sample_expired")
        if (now - current_at) / 1e9 > p.max_current_pose_age_s:
            return _stop(result, "current_pose_expired")
        if obs["quality"] & 7 != 7 or obs["quality"] & 0x17f0:
            return _stop(result, "invalid_faulted_saturated_or_held_em")
        result["risk"] = n._risk(values, p.background_c0)
        # Same original uncertainty arithmetic, using real continuous source age.
        result["uncertainty"] = n._clip(0.5 + 0.4 * age_s * 1000 / n.DEMO_AGE_NORMALIZATION_MS
            + 2 / 4095 + n.C3_MISSING_UNCERTAINTY_PENALTY)
        native = {k: obs[k] for k in ("position_m", "orientation_xyzw")}
        if not n._poses_applicable(native, native, current):
            result["uncertainty"] = 1.
            return _stop(result, "original_observation_pose_inapplicable")
        if req["paused"] or req["user_speed_cap_m_s"] == 0:
            return _stop(result, "user_paused" if req["paused"] else "user_speed_cap_zero")
        if result["uncertainty"] >= 1.:
            return _stop(result, "observation_uncertainty_limit")
        goal = _guidance(req["public_goal"], current["position_m"], p.exit_lookahead_m)
        map_cells = [{"pose": native, "risk": result["risk"]}]
        chosen = n.rank(values, current["orientation_xyzw"], native["orientation_xyzw"], goal,
            current["position_m"], map_cells, req["executed_actions"][-1:], p.background_c0)
        if chosen is None:
            return _stop(result, "no_observed_forward_goal_progress")
        forward = n._rotate(current["orientation_xyzw"], [0., 0., 1.])
        forward_length = math.hypot(*forward)
        forward = [v / forward_length for v in forward]
        direction = _moderate(forward, chosen[5], p.max_steer_deg)
        inverse_native = [-v for v in native["orientation_xyzw"][:3]] + [native["orientation_xyzw"][3]]
        # Re-evaluate the ACTUAL moderated direction with unchanged risk math.
        result["risk"] = n.directional_risk(values, n._rotate(inverse_native, direction), p.background_c0)
        if result["risk"] >= 0.8:
            return _stop(result, "candidate_risk_limit")
        inverse_current = [-v for v in current["orientation_xyzw"][:3]] + [current["orientation_xyzw"][3]]
        body = n._rotate(inverse_current, direction)
        alignment = max(0., sum(a * b for a, b in zip(forward, goal)))
        speed = min(req["user_speed_cap_m_s"], p.initial_speed_cap_m_s,
                    n.C3_MISSING_SPEED_CAP_M_S) * (1. - result["risk"]) * (
                    1. - 0.5 * result["uncertainty"]) * (0.25 + 0.75 * alignment * alignment)
        result.update(status="ADVISE", reason="continuous_em3_public_exit_search",
            target_direction_world=direction, direction_world=list(direction),
            yaw_delta_deg=math.degrees(math.atan2(body[0], body[2])),
            pitch_delta_deg=math.degrees(math.atan2(body[1], math.hypot(body[0], body[2]))),
            speed_limit_m_s=speed, public_goal_direction_world=goal)
        return result

    def submit(self, request) -> Future | None:
        """Return None immediately when busy; no observation/action backlog."""
        with self._lock:
            if self._closed:
                raise RuntimeError("AI worker retired")
            if self._future is not None and not self._future.done():
                return None
            copied = _validated_copy(request, self._numeric)
            if copied["world_epoch"] != self.world_epoch or copied["observation"]["world_epoch"] != self.world_epoch:
                raise ValueError("old world epoch; construct an epoch-matching worker")
            acquired = _ns(copied["observation"]["at_qpc_ns"])
            if acquired <= self._last_at:
                raise ValueError("duplicate or reordered source acquisition")
            self._last_at = acquired
            self._future = self._pool.submit(self._run, copied)
            return self._future

    def _run(self, req):
        started = _ns(self._clock())
        result = self._infer(req, started)
        completed = _ns(self._clock())
        if completed < started:
            raise ValueError("inference QPC clock regressed")
        # Inference completion never renews source or current-own-pose validity.
        if (completed - _ns(req["observation"]["at_qpc_ns"])) / 1e9 > self.profile.max_source_age_s:
            _stop(result, "original_sample_expired")
        elif (completed - _ns(req["current_pose"]["at_qpc_ns"])) / 1e9 > self.profile.max_current_pose_age_s:
            _stop(result, "current_pose_expired")
        result["inference_completed_qpc_ns"] = str(completed)
        with self._lock:
            if not self._closed:
                self._latest = copy.deepcopy(result)
        return result

    def latest(self, world_epoch):
        """Detached last completed advice, no age renewal. Root checks before use."""
        with self._lock:
            if self._closed or world_epoch != self.world_epoch:
                return None
            return copy.deepcopy(self._latest)

    def close(self, *, wait=True):
        with self._lock:
            self._closed, self._latest = True, None
        self._pool.shutdown(wait=wait, cancel_futures=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


__all__ = ["LiveAIWorker", "LiveProfile", "PROFILE_ID", "CORE_SHA256", "REQUIREMENTS_SHA256"]

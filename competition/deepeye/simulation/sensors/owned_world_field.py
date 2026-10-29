"""Root-private conductivity approximation over the motion owner's exact scene.

Frozen numerical classes are not proof of native scene custody or material
physics. Callbacks must stay in Root; no controller/mapper receives this field.
"""
import math
import numbers

from ..authority.motion_executor import OwnedMotionExecutor
from ..authority.motion import solid_clearance as geometry
from . import forward_profile as forward


_PRIORITY = {'casing': 5, 'fault': 4, 'void': 3, 'water': 2, 'hard_rock': 1}
_MAX_PIECES = 256


def _number(value):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError('finite real scalar required')
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError('finite representable scalar required') from exc
    if not math.isfinite(result):
        raise ValueError('finite representable scalar required')
    return result


def _sigma(value):
    result = _number(value)
    if not forward.SIGMA_MIN_S_PER_M <= result <= forward.SIGMA_MAX_S_PER_M:
        raise ValueError('explicit conductivity outside forward envelope')
    return result


class OwnedWorldField:
    """Bind once to all pieces of one exact owner scene; no rebind or adoption.

    `max_pieces`, background and all five material policies are mandatory Root
    inputs. `None` material policy means unknown conductivity, not zero/air.
    Optional epsilon is an explicit positive candidate boundary band in metres;
    omission means exact nominal boundaries are unknown, not zero physical error.
    """
    __slots__ = ('_executor', '_scene', '_scene_id', '_scene_digest', '_binding',
                 '_run', '_epoch', '_retired', '_pieces', '_background', '_epsilon')

    def __init__(self, executor, *, material_sigma, background_sigma, max_pieces,
                 sample_epsilon_m=None):
        if hasattr(self, '_executor'):
            raise ValueError('field is already bound; no source restart/adoption')
        if type(executor) is not OwnedMotionExecutor:
            raise TypeError('exact existing OwnedMotionExecutor required')
        root = executor.authority_snapshot()  # Original owner-thread check first.
        scene = executor._scene
        if root.world_invalid or type(scene) is not geometry.Scene:
            raise ValueError('current complete owner world required')
        if type(material_sigma) is not dict or set(material_sigma) != set(_PRIORITY):
            raise ValueError('explicit policy for exactly all five materials required')
        sigma = {kind: None if value is None else _sigma(value)
                 for kind, value in material_sigma.items()}
        background = _sigma(background_sigma)
        if type(max_pieces) is not int or not 1 <= max_pieces <= _MAX_PIECES:
            raise ValueError('explicit piece budget must be 1..256')
        epsilon = 0. if sample_epsilon_m is None else _number(sample_epsilon_m)
        if sample_epsilon_m is not None and epsilon <= 0:
            raise ValueError('explicit sample epsilon must be positive')
        if len(scene.objects) > 30 or sum(len(o.parts) for o in scene.objects) > max_pieces:
            raise ValueError('whole scene exceeds object/piece budget')
        pieces = []
        for obj in scene.objects:
            for part in obj.parts:
                if type(part) is not geometry.Solid or part.kind not in ('box', 'cylinder'):
                    raise ValueError('unsupported piece refuses whole field; never skip')
                centre = tuple(_number(v) for v in part.centre)
                dimensions = tuple(_number(v) for v in part.dimensions)
                matrix = tuple(tuple(_number(v) for v in row) for row in part.matrix)
                if min(dimensions) <= 0:
                    raise ValueError('positive representable nominal half sizes required')
                pieces.append((_PRIORITY[obj.material], sigma[obj.material],
                               part.kind, centre, dimensions, matrix))
        # Refuse unsupported geometry before digest traversal (a polytope may
        # carry an arbitrarily large vertex list). Supported pieces are bounded.
        if geometry._digest(scene) != scene.digest:
            raise ValueError('owner scene numerical digest mismatch')
        self._executor = executor
        self._scene = scene
        self._scene_id = scene.scene_id
        self._scene_digest = scene.digest
        self._binding = executor._world_binding
        self._run = root.phase.context.run_id
        self._epoch = root.phase.context.epoch
        self._retired = False
        self._pieces = tuple(pieces)  # Complete read-only compiled scalar tuples.
        self._background = background
        self._epsilon = epsilon

    def _check(self):
        root = self._executor.authority_snapshot()
        scene = self._executor._scene
        context = root.phase.context
        if (self._retired or root.world_invalid or scene is not self._scene
                or scene.scene_id != self._scene_id or scene.digest != self._scene_digest
                or self._executor._world_binding != self._binding
                or context.run_id != self._run or context.epoch != self._epoch):
            self._retired = True
            raise ValueError('owned world field retired; original binding no longer current')
        return root

    def pose_reader(self):
        """Return fresh forward.Pose from the same current committed owner view."""
        root = self._check()
        view = self._executor.renderer_view()
        if view.pose is not root.pose or view.pose_revision != root.pose_revision:
            self._retired = True
            raise ValueError('serialized current owner pose mismatch')
        return forward.Pose(view.pose.position_m, view.pose.orientation_xyzw)

    def sample_sigma(self, x, y, z):
        """Only numeric S/m or None; never a material/position/distance DTO."""
        self._check()
        try:
            point = tuple(_number(v) for v in (x, y, z))
        except ValueError:
            return None
        priority = 0
        result = self._background
        for rank, sigma, kind, centre, dimensions, matrix in self._pieces:
            try:
                delta = tuple(v - c for v, c in zip(point, centre))
                local = tuple(math.fsum(matrix[i][j] * delta[i] for i in range(3)) for j in range(3))
                if not all(math.isfinite(v) for v in local):
                    return None
                axial = abs(local[2]) - dimensions[2]
                if kind == 'box':
                    gaps = tuple(abs(v) - d for v, d in zip(local, dimensions))
                    outside = any(gap > self._epsilon for gap in gaps)
                    inside = all(gap < -self._epsilon for gap in gaps)
                else:
                    radial = math.hypot(local[0] / dimensions[0], local[1] / dimensions[1]) - 1.
                    band = self._epsilon / min(dimensions[0], dimensions[1])
                    if not math.isfinite(radial) or not math.isfinite(band):
                        return None
                    outside = axial > self._epsilon or radial > band
                    inside = axial < -self._epsilon and radial < -band
            except (OverflowError, ValueError):
                return None
            if outside:
                continue
            if not inside:
                return None  # No quiet background substitution at any ambiguity.
            if rank > priority:
                priority, result = rank, sigma
        return result

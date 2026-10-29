"""Fixed-whitelist presentation snapshots, never controller input or authority.

Call only in the existing motion owner's serialized thread after publication.
No layout, sensor oracle, source authentication, BOOT or motion grant is exported.
"""
import math

from .motion_executor import OwnedMotionExecutor


_FIELDS = frozenset(('run_id', 'authority_revision', 'pose_revision',
                     'position_m', 'orientation_xyzw', 'stopped'))
_MAX_REVISION = 2**53 - 1  # Exact across JSON and Godot's JSON numeric representation.
_MAX_POSITION = 3.4028234663852886e38  # Finite in the existing float32 Godot build.


def _revision(value):
    if type(value) is not int or not 0 <= value <= _MAX_REVISION:
        raise ValueError('strict nonnegative JSON-safe integer revision required')
    return value


def _numbers(value, size):
    if type(value) not in (list, tuple) or len(value) != size:
        raise ValueError('fixed-length numeric array required')
    result = []
    for component in value:
        if type(component) not in (int, float):
            raise ValueError('finite numeric component required')
        try:
            number = float(component)
        except (OverflowError, ValueError) as exc:
            raise ValueError('finite numeric component required') from exc
        if not math.isfinite(number):
            raise ValueError('finite numeric component required')
        result.append(number)
    return result


def validate_frame(frame):
    """Validate/copy a presentation frame; this does not authenticate its source."""
    if type(frame) is not dict or set(frame) != _FIELDS:
        raise ValueError('exact renderer frame whitelist required')
    run_id = frame['run_id']
    if (type(run_id) is not str or not 1 <= len(run_id) <= 128
            or any(ord(c) < 32 or ord(c) == 127 for c in run_id)):
        raise ValueError('bounded run identifier without control characters required')
    authority_revision = _revision(frame['authority_revision'])
    pose_revision = _revision(frame['pose_revision'])
    position = _numbers(frame['position_m'], 3)
    orientation = _numbers(frame['orientation_xyzw'], 4)
    if any(abs(c) > _MAX_POSITION for c in position):
        raise ValueError('position exceeds finite native representation')
    if abs(math.hypot(*orientation) - 1.0) > 1e-6:
        raise ValueError('normalized nonzero xyzw quaternion required')
    if type(frame['stopped']) is not bool:
        raise ValueError('strict stopped boolean required')
    return {'run_id': run_id, 'authority_revision': authority_revision,
            'pose_revision': pose_revision, 'position_m': position,
            'orientation_xyzw': orientation, 'stopped': frame['stopped']}


def frame_from_executor(executor):
    """Select only real owner state; never recursively serialize the owner root.

    These exact-class methods perform owner-thread checks and no user callbacks.
    The caller must retain the owner's existing serialization through this read.
    The root supplies its actual state revision and run identity; RendererView
    supplies the committed body pose/revision, ControllerView the stopped flag.
    """
    if type(executor) is not OwnedMotionExecutor:
        raise TypeError('existing owned motion executor required')
    root = executor.authority_snapshot()
    view = executor.renderer_view()
    status = executor.controller_view()
    return validate_frame({'run_id': root.phase.context.run_id,
                          'authority_revision': root.revision,
                          'pose_revision': view.pose_revision,
                          'position_m': view.pose.position_m,
                          'orientation_xyzw': view.pose.orientation_xyzw,
                          'stopped': status.stopped})

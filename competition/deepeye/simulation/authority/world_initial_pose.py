"""Root proposal outside the selected blue gate; no clearance or motion grant."""
import math

from .motion.kinematics import RigidState
from .motion.workspace_boundaries import Layout


_H = math.sqrt(.5)
# Body-to-world xyzw. Body +Z is inward; side-face body up is world +Y.
# Top/bottom use world +Z/-Z as up, retaining a proper right-handed frame.
_ORIENTATIONS = {
    'front': (0., 1., 0., 0.),
    'back': (0., 0., 0., 1.),
    'left': (0., _H, 0., _H),
    'right': (0., -_H, 0., _H),
    'top': (_H, 0., 0., _H),
    'bottom': (-_H, 0., 0., _H),
}


def initial_pose_for_layout(layout, *, standoff_m):
    """Propose zero-speed body origin at an explicit outward gate standoff.

    The actual WorldValues initializer/corridor/scene/asset checks must still
    accept the proposal. A small positive standoff is never silently enlarged.
    No obstacle truth, route, alternate entry, default distance or fallback.
    """
    if type(layout) is not Layout:
        raise TypeError('actual immutable workspace Layout required')
    # Reapply the existing gate-pair/edge contract, never expand its tolerance.
    Layout(layout.blue, layout.red)
    if type(standoff_m) not in (int, float):
        raise ValueError('explicit finite positive standoff required')
    try:
        distance = float(standoff_m)
    except (OverflowError, ValueError) as error:
        raise ValueError('explicit finite positive standoff required') from error
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError('explicit finite positive standoff required')
    blue = layout.blue
    position = tuple(center + normal * distance
                     for center, normal in zip(blue.center_m, blue.normal))
    return RigidState(position, _ORIENTATIONS[blue.face], 0.)

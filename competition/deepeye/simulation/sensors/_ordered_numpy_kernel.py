"""Unconnected experimental numerical component; no runtime registration.

Inputs are trusted Root-private compiled tuples, not a security boundary.
Supported boxes use a bounded candidate batch path; unsupported points fall back.
"""
import math
import numpy as np

from . import forward_profile as forward
from ._ordered_field_batch import _sample_points

_PROFILE = 'ordered-numpy-field-batch-candidate-1'
_CHUNK = 1024


def _coordinates(pose, rows):
    """Separated float64 operations in source expression order."""
    if not rows:
        return ()
    r = np.asarray([row[:3] for row in rows], dtype=np.float64)
    rotation = forward._rotation_matrix(pose.orientation_xyzw)
    result = []
    with np.errstate(all='ignore'):
        for axis in range(3):
            m = rotation[axis]
            value = np.add(np.float64(pose.position_m[axis]), np.multiply(np.float64(m[0]), r[:, 0]))
            value = np.add(value, np.multiply(np.float64(m[1]), r[:, 1]))
            value = np.add(value, np.multiply(np.float64(m[2]), r[:, 2]))
            result.append(value)
    return tuple(tuple(float(result[j][i]) for j in range(3)) for i in range(len(rows)))


def _channels(pose, pieces, background, epsilon, rows):
    """Return only 3 raw channels or None; accepts no sampler/provider.

    Bounded box classification uses the private candidate batch field. Any
    unsupported point falls back to the complete original scalar traversal.
    """
    if type(pieces) is not tuple or type(rows) is not tuple:
        raise TypeError('immutable compiled tuples required')
    sw = [0.0] * 5
    sws = [0.0] * 5
    for start in range(0, len(rows), _CHUNK):
        chunk = rows[start:start + _CHUNK]
        coords = _coordinates(pose, chunk)
        sigmas = _sample_points(pieces, background, epsilon, coords)
        for sigma in sigmas:
            if not forward._valid_sigma(sigma):
                return None
        with np.errstate(all='ignore'):
            sigma_array = np.asarray(sigmas, dtype=np.float64)
            for lobe in range(5):
                weights = np.asarray([row[3 + lobe] for row in chunk], dtype=np.float64)
                mask = weights > 0.0
                selected = weights[mask]
                if selected.size:
                    a = np.empty(selected.size + 1, dtype=np.float64)
                    a[0] = sw[lobe]
                    a[1:] = selected
                    sw[lobe] = float(np.add.accumulate(a)[-1])
                    a[0] = sws[lobe]
                    a[1:] = np.multiply(selected, sigma_array[mask])
                    sws[lobe] = float(np.add.accumulate(a)[-1])
    log10_rho = [-math.log10(sws[i] / sw[i]) for i in range(5)]
    return (log10_rho[0], log10_rho[1] - log10_rho[2], log10_rho[3] - log10_rho[4])

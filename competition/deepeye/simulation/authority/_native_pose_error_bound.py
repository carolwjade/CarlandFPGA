"""Exact, inactive endpoint affine displacement bound for a contained body.

No authority, native lifetime, source admission, or rendering claim is made.
"""
from dataclasses import dataclass
from fractions import Fraction
from math import isqrt

_MAX_BITS = 1200  # Allows all finite IEEE binary64 values, including subnormals.
_SCALE = 1 << 64


def _fraction(value):
    if type(value) is not Fraction:
        raise TypeError('exact Fraction required')
    if value.numerator.bit_length() > _MAX_BITS or value.denominator.bit_length() > _MAX_BITS:
        raise ValueError('rational input exceeds resource domain')
    return value


def _tuple(value, length):
    if type(value) is not tuple or len(value) != length:
        raise TypeError('fixed immutable tuple required')
    return tuple(_fraction(x) for x in value)


def decode_ieee(token, width):
    """Decode a finite, big-endian IEEE scalar exactly; signed zeros coincide."""
    if type(width) is not int or width not in (32, 64):
        raise ValueError('width must be 32 or 64')
    if type(token) is not str or len(token) != width // 4 or any(c not in '0123456789abcdefABCDEF' for c in token):
        raise ValueError('invalid scalar encoding')
    raw = int(token, 16)
    exponent_bits, fraction_bits, bias = (8, 23, 127) if width == 32 else (11, 52, 1023)
    exponent = (raw >> fraction_bits) & ((1 << exponent_bits) - 1)
    mantissa = raw & ((1 << fraction_bits) - 1)
    if exponent == (1 << exponent_bits) - 1:
        raise ValueError('nonfinite scalar')
    if exponent:
        mantissa |= 1 << fraction_bits
        power = exponent - bias - fraction_bits
    else:
        power = 1 - bias - fraction_bits
    numerator = -mantissa if raw >> (width - 1) else mantissa
    return Fraction(numerator << power, 1) if power >= 0 else Fraction(numerator, 1 << -power)


def _sqrt_enclosure(value):
    scaled = value.numerator * _SCALE * _SCALE // value.denominator
    lower_int = isqrt(scaled)
    exact = lower_int * lower_int * value.denominator == value.numerator * _SCALE * _SCALE
    return Fraction(lower_int, _SCALE), Fraction(lower_int if exact else lower_int + 1, _SCALE)


def sqrt_enclosure(value):
    """Return dyadic lower and upper square-root bounds, both inclusive."""
    value = _fraction(value)
    if value < 0:
        raise ValueError('nonnegative square required')
    return _sqrt_enclosure(value)


def _rotation(q):
    x, y, z, w = q
    d = x*x + y*y + z*z + w*w
    if not d:
        raise ValueError('zero quaternion')
    return ((1-2*(y*y+z*z)/d, 2*(x*y-z*w)/d, 2*(x*z+y*w)/d),
            (2*(x*y+z*w)/d, 1-2*(x*x+z*z)/d, 2*(y*z-x*w)/d),
            (2*(x*z-y*w)/d, 2*(y*z+x*w)/d, 1-2*(x*x+y*y)/d))


@dataclass(frozen=True)
class EndpointBound:
    translation_norm_upper: Fraction
    matrix_norm_upper: Fraction
    body_radius: Fraction
    asset_error: Fraction
    getter_error: Fraction
    total_error: Fraction

    def fits_cap(self, cap):
        """Compare getter contribution to an external cap, not authority."""
        cap = _fraction(cap)
        if cap <= 0:
            raise ValueError('positive cap required')
        return self.getter_error <= cap


def affine_body_bound(position, quaternion, global_columns, global_origin,
                      half_segment, capsule_radius, pivot_radius, asset_error):
    """Bound actual affine image versus ideal capsule at one endpoint.

    Caller must establish that the entire root-space asset is contained in the
    nominal capsule expanded by asset_error, and that getter words correspond
    to the same pose. No such provenance is inferred or checked here.
    """
    position = _tuple(position, 3)
    quaternion = _tuple(quaternion, 4)
    origin = _tuple(global_origin, 3)
    if type(global_columns) is not tuple or len(global_columns) != 3:
        raise TypeError('three immutable basis columns required')
    columns = tuple(_tuple(col, 3) for col in global_columns)
    half, radius, pivot, asset = map(_fraction, (half_segment, capsule_radius, pivot_radius, asset_error))
    if half < 0 or radius <= 0 or pivot < half + radius or asset < 0:
        raise ValueError('invalid containing capsule or asset radius')
    rotation = _rotation(quaternion)
    t2 = sum(((origin[i] - position[i])**2 for i in range(3)), Fraction(0))
    m2 = sum(((columns[j][i] - rotation[i][j])**2 for i in range(3) for j in range(3)), Fraction(0))
    t_upper, m_upper = _sqrt_enclosure(t2)[1], _sqrt_enclosure(m2)[1]
    body_radius = pivot + asset
    getter = t_upper + m_upper * body_radius
    return EndpointBound(t_upper, m_upper, body_radius, asset, getter, getter + asset)

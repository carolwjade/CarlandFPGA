"""Private full Solid-vs-Solid sufficient separation, never an owner/grant.

Exact support values and outward integer-root bounds are reused unchanged from
the existing kernel. UNKNOWN never asserts collision or unreachability.
"""
from dataclasses import dataclass, field
from fractions import Fraction as F

from .motion import solid_clearance as s


@dataclass(frozen=True)
class PairCertificate:
    binding: str
    normal: tuple
    left_upper: F
    right_lower: F
    margin: F
    gap: F
    context: str
    motion_grant: bool = field(default=False, init=False)


@dataclass(frozen=True)
class PairResult:
    status: str
    binding: str
    normals_tried: int
    support_terms: int
    certificate: PairCertificate | None
    reason: str
    motion_grant: bool = field(default=False, init=False)


def _cost(value):
    return 3 + (len(value.vertices) * 3 if value.kind == 'polytope' else 9)


def _normals(left, right, proposals):
    delta = tuple(b-a for a,b in zip(left.centre,right.centre))
    seeds = [delta, tuple(-x for x in delta)]
    seeds += [tuple(F(int(i == j)) for i in range(3)) for j in range(3)]
    seeds += [tuple(-F(int(i == j)) for i in range(3)) for j in range(3)]
    for matrix in (left.matrix,right.matrix):
        for j in range(3):
            n = tuple(row[j] for row in matrix)
            seeds.extend((n,tuple(-x for x in n)))
    seeds.extend(proposals)
    seen = set()
    for proposed in seeds:
        n = s._vector(proposed)
        if not any(n):
            continue
        # Positive normalization deduplicates directions without reversing them.
        scale = next(abs(x) for x in n if x)
        n = tuple(x/scale for x in n)
        if n not in seen:
            seen.add(n)
            yield n


def certify_pair(left, right, *, margin, context='', proposals=(),
                 max_normals=32, remaining_support_terms=100000):
    """Bounded exact sufficient check of the *complete* two convex volumes.

    The caller owns scene-wide work accounting. A strict gap of the outward
    support bounds is sufficient. A missed separating direction is UNKNOWN.
    """
    if type(left) is not s.Solid or type(right) is not s.Solid:
        raise TypeError('complete immutable Solid values required')
    margin = s._scalar(margin)
    if margin < 0 or type(context) is not str:
        raise ValueError('explicit nonnegative margin and context required')
    if type(max_normals) is not int or not 1 <= max_normals <= 32:
        raise ValueError('at most32 proposed normals per pair')
    if (type(remaining_support_terms) is not int or
            not 0 <= remaining_support_terms <= 100000):
        raise ValueError('bounded remaining scene support budget required')
    if type(proposals) not in (tuple,list) or len(proposals) > 12:
        raise ValueError('bounded finite proposal tuple required')
    binding = s._digest(('solid-pair-v1',left.digest,right.digest,margin,context))
    tried = spent = 0
    cost = _cost(left)+_cost(right)
    for normal in _normals(left,right,proposals):
        if tried >= max_normals or spent+cost > remaining_support_terms:
            return PairResult('UNKNOWN',binding,tried,spent,None,'support work budget exhausted')
        tried += 1
        spent += cost
        upper = s.support_upper(left,normal)
        lower = -s.support_upper(right,tuple(-x for x in normal))
        gap = lower-upper-margin*s._sqrt_up(s._dot(normal,normal))
        if gap > 0:
            certificate = PairCertificate(binding,normal,upper,lower,margin,gap,context)
            return PairResult('CLEAR',binding,tried,spent,certificate,'strict exact/outward support gap')
    return PairResult('UNKNOWN',binding,tried,spent,None,'no strict separation certificate')


__all__ = []

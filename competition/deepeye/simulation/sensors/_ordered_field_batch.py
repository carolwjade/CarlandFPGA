"""Private experimental batch field. Never a controller or a security boundary."""
import numpy as np
from .owned_world_field import OwnedWorldField

# Domain prevents overflow/underflow in input products and the finite expansion.
_LIMIT = 1e50
_FLOOR = 1e-50

def _domain(a):
    a = np.asarray(a, dtype=np.float64)
    return np.all(np.isfinite(a) & ((a == 0.0) | ((np.abs(a) >= _FLOOR) & (np.abs(a) <= _LIMIT))), axis=-1)

def _fsum3(products):
    """Three finite inputs: CPython 3.12 math_fsum partials and half-even fix.

    Returns (value, supported mask). Unsupported lanes must use original scalar.
    """
    a = np.asarray(products, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 3:
        raise ValueError('three products required')
    count = len(a)
    ok = _domain(a)
    p = np.zeros((3,count), dtype=np.float64)
    n = np.zeros(count, dtype=np.int8)
    with np.errstate(all='ignore'):
        for column in range(3):
            x = a[:,column].copy()
            dest = np.zeros(count, dtype=np.int8)
            for j in range(3):
                active = ok & (j < n)
                y = p[j].copy()
                swap = active & (np.abs(x) < np.abs(y))
                xx = np.where(swap, y, x)
                yy = np.where(swap, x, y)
                hi = np.add(xx, yy)
                yr = np.subtract(hi, xx)
                lo = np.subtract(yy, yr)
                keep = active & (lo != 0.)
                for i in range(3):
                    take = keep & (dest == i)
                    p[i,take] = lo[take]
                dest += keep.astype(np.int8)
                x = np.where(active,hi,x)
                ok &= ~active | np.isfinite(hi)
            n = dest
            keep = ok & (x != 0.)
            for i in range(3):
                take = keep & (n == i)
                p[i,take] = x[take]
            n += keep.astype(np.int8)
        hi = np.zeros(count,dtype=np.float64)
        for i in range(3):
            take = ok & (n == i+1)
            hi[take] = p[i,take]
        n = np.where(n > 0,n-1,0)
        lo = np.zeros(count,dtype=np.float64)
        running = ok.copy()
        for _ in range(2):
            active = running & (n > 0)
            index = np.maximum(n-1,0)
            y = p[index,np.arange(count)]
            x = hi.copy()
            summed = np.add(x,y)
            yr = np.subtract(summed,x)
            next_lo = np.subtract(y,yr)
            hi = np.where(active,summed,hi)
            lo = np.where(active,next_lo,lo)
            n = np.where(active,n-1,n)
            running &= ~active | (next_lo == 0.)
        lower = p[np.maximum(n-1,0),np.arange(count)]
        fix = ok & (n > 0) & (((lo < 0.) & (lower < 0.)) | ((lo > 0.) & (lower > 0.)))
        y = np.multiply(lo,2.0)
        x = np.add(hi,y)
        yr = np.subtract(x,hi)
        hi = np.where(fix & (y == yr),x,hi)
    return hi, ok

def _sample_points(pieces, background, epsilon, points):
    """Trusted compiled tuples only; preserve whole scalar point fallback."""
    if type(pieces) is not tuple:
        raise TypeError('compiled tuple required')
    field=object.__new__(OwnedWorldField)
    field._pieces,field._background,field._epsilon=pieces,background,epsilon
    if any(len(point) != 3 or any(type(v) is not float for v in point) for point in points):
        return [OwnedWorldField._sample_sigma_pure(field,*point) for point in points]
    pts = np.asarray(points,dtype=np.float64)
    if pts.size == 0:
        return []
    if pts.ndim != 2 or pts.shape[1] != 3:
        raise ValueError('three-dimensional points required')
    n=len(pts)
    safe=_domain(pts)
    values=[background]*n
    rank=np.zeros(n,dtype=np.int16)
    valid=np.ones(n,dtype=bool)
    # If any piece cannot be handled, all points get original full scalar traversal.
    for piece in pieces:
        r,sigma,kind,centre,dims,matrix=piece
        if kind != 'box' or not bool(_domain(np.asarray([*centre,*dims,*matrix[0],*matrix[1],*matrix[2],epsilon]))):
            safe[:]=False
            break
    with np.errstate(all='ignore'):
        for r,sigma,kind,centre,dims,matrix in pieces:
            if not safe.any(): break
            delta=np.subtract(pts,np.asarray(centre,dtype=np.float64))
            safe &= _domain(delta)
            local=[]
            for j in range(3):
                products=np.multiply(delta,np.asarray([matrix[i][j] for i in range(3)],dtype=np.float64))
                v, ok=_fsum3(products)
                safe &= ok
                local.append(v)
            loc=np.column_stack(local)
            gaps=np.subtract(np.abs(loc),np.asarray(dims,dtype=np.float64))
            outside=np.any(gaps > epsilon,axis=1)
            inside=np.all(gaps < -epsilon,axis=1)
            boundary=safe & ~outside & ~inside
            valid &= ~boundary
            higher=safe & inside & (r > rank)
            rank=np.where(higher,r,rank)
            for idx in np.flatnonzero(higher): values[int(idx)]=sigma
    for idx in range(n):
        if not safe[idx]:
            values[idx]=OwnedWorldField._sample_sigma_pure(field,*tuple(float(x) for x in pts[idx]))
        elif not valid[idx]:
            values[idx]=None
    return values

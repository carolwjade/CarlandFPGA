"""Inactive strict serial JIT candidate; trusted private inputs only."""
import math
import numpy as np
from numba import njit
from . import forward_profile as forward
from .owned_world_field import OwnedWorldField

PROFILE='strict-jit-ordered-v1-candidate'

@njit(fastmath=False, parallel=False, cache=False, inline='always')
def _finite_sum3(a,b,c):
    # Literal CPython math_fsum finite partial expansion, three inputs.
    p0=0.;p1=0.;p2=0.; n=0
    for step in range(3):
        x=a if step==0 else (b if step==1 else c)
        dest=0
        for j in range(n):
            y=p0 if j==0 else (p1 if j==1 else p2)
            if abs(x)<abs(y): x,y=y,x
            hi=x+y; yr=hi-x; lo=y-yr
            if lo!=0.:
                if dest==0:p0=lo
                elif dest==1:p1=lo
                else:p2=lo
                dest+=1
            x=hi
        n=dest
        if x!=0.:
            if n==0:p0=x
            elif n==1:p1=x
            else:p2=x
            n+=1
    hi=0.;lo=0.
    if n>0:
        n-=1;hi=p0 if n==0 else (p1 if n==1 else p2)
        while n>0:
            x=hi;n-=1;y=p0 if n==0 else (p1 if n==1 else p2)
            hi=x+y;yr=hi-x;lo=y-yr
            if lo!=0.: break
        if n>0:
            q=p0 if n==1 else p1
            if (lo<0. and q<0.) or (lo>0. and q>0.):
                y=lo*2.;x=hi+y;yr=x-hi
                if y==yr:hi=x
    return hi

def _fsum3(a,b,c):
    if any(not math.isfinite(x) or (x and not 1e-80 <= abs(x) <= 1e80) for x in (a,b,c)):
        return math.fsum((a,b,c))
    return float(_finite_sum3(a,b,c))

@njit(fastmath=False, parallel=False, cache=False, inline='always')
def _safe(x):
    return math.isfinite(x) and (x==0. or (abs(x)>=1e-80 and abs(x)<=1e80))

@njit(fastmath=False, parallel=False, cache=False)
def _run(rows,position,rot,ranks,sigmas,unknown,centres,dims,matrices,bg,eps):
    sw=np.zeros(5,np.float64);sws=np.zeros(5,np.float64)
    for row in rows:
        dx=row[0];dy=row[1];dz=row[2]
        xyz=np.empty(3,np.float64)
        for j in range(3):
            xyz[j]=((position[j]+rot[j,0]*dx)+rot[j,1]*dy)+rot[j,2]*dz
            if not _safe(xyz[j]):return 2,sw,sws
        rank=0; sigma=bg; isunknown=False
        for p in range(len(ranks)):
            d0=xyz[0]-centres[p,0];d1=xyz[1]-centres[p,1];d2=xyz[2]-centres[p,2]
            if not (_safe(d0) and _safe(d1) and _safe(d2)):return 2,sw,sws
            outside=False;inside=True
            for j in range(3):
                a=matrices[p,0,j]*d0;b=matrices[p,1,j]*d1;c=matrices[p,2,j]*d2
                if not (_safe(a) and _safe(b) and _safe(c)):return 2,sw,sws
                local=_finite_sum3(a,b,c)
                gap=abs(local)-dims[p,j]
                if gap>eps:outside=True
                if not gap < -eps:inside=False
            if outside:continue
            if not inside:return 1,sw,sws
            if ranks[p]>rank:
                rank=ranks[p];sigma=sigmas[p];isunknown=unknown[p]
        if isunknown:return 1,sw,sws
        if not (forward.SIGMA_MIN_S_PER_M<=sigma<=forward.SIGMA_MAX_S_PER_M): return 1,sw,sws
        for j in range(5):
            weight=row[3+j]
            if weight>0.:
                sw[j]+=weight
                sws[j]+=weight*sigma
    return 0,sw,sws


def _prepare(pieces,background,epsilon):
    if type(pieces) is not tuple: raise TypeError('trusted compiled tuple required')
    field=object.__new__(OwnedWorldField)
    field._pieces,field._background,field._epsilon=pieces,background,epsilon
    eligible=True; ranks=[]; sigmas=[]; unknown=[];centres=[];dims=[];matrices=[]
    for rank,sigma,kind,centre,dim,matrix in pieces:
        if kind!='box':eligible=False
        allnums=(*centre,*dim,*(v for row in matrix for v in row),epsilon,background)
        if any(not math.isfinite(x) or (x and not 1e-80<=abs(x)<=1e80) for x in allnums):eligible=False
        ranks.append(rank);sigmas.append(0. if sigma is None else sigma);unknown.append(sigma is None)
        centres.append(centre);dims.append(dim);matrices.append(matrix)
    count=len(pieces)
    return (field,eligible,np.asarray(ranks,dtype=np.int64),np.asarray(sigmas,dtype=np.float64),np.asarray(unknown,dtype=np.bool_),np.asarray(centres,dtype=np.float64).reshape(count,3),np.asarray(dims,dtype=np.float64).reshape(count,3),np.asarray(matrices,dtype=np.float64).reshape(count,3,3))

def _sample(prepared,point):
    return OwnedWorldField._sample_sigma_pure(prepared[0],*point)

def _scalar_sums(pose,field,rows):
    tx,ty,tz=pose.position_m;m=forward._rotation_matrix(pose.orientation_xyzw)
    sw=[0.]*5;sws=[0.]*5
    for row in rows:
        x,y,z=row[:3]
        wx=tx+m[0][0]*x+m[0][1]*y+m[0][2]*z
        wy=ty+m[1][0]*x+m[1][1]*y+m[1][2]*z
        wz=tz+m[2][0]*x+m[2][1]*y+m[2][2]*z
        sigma=OwnedWorldField._sample_sigma_pure(field,wx,wy,wz)
        if not forward._valid_sigma(sigma):return None
        sigma=float(sigma)
        for i in range(5):
            weight=row[3+i]
            if weight>0.:sw[i]+=weight;sws[i]+=weight*sigma
    return tuple(sw),tuple(sws)

def _raw_sums(pose,prepared,rows):
    field,eligible,ranks,sigmas,unknown,centres,dims,matrices=prepared
    if not eligible:return _scalar_sums(pose,field,rows)
    rowarray=np.asarray(rows,dtype=np.float64)
    position=np.asarray(pose.position_m,dtype=np.float64)
    rot=np.asarray(forward._rotation_matrix(pose.orientation_xyzw),dtype=np.float64)
    status,sw,sws=_run(rowarray,position,rot,ranks,sigmas,unknown,centres,dims,matrices,field._background,field._epsilon)
    if status==2:return _scalar_sums(pose,field,rows)
    if status==1:return None
    return tuple(float(x) for x in sw),tuple(float(x) for x in sws)

def _channels(pose,prepared,rows):
    sums=_raw_sums(pose,prepared,rows)
    if sums is None:return None
    sw,sws=sums
    logs=[-math.log10(sws[i]/sw[i]) for i in range(5)]
    return logs[0],logs[1]-logs[2],logs[3]-logs[4]

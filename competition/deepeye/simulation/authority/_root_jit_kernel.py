"""Fixed, default-inactive, original Root EM-scope JIT association."""
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import threading
from types import FunctionType, MethodType

from ..sensors import forward_profile as forward
from . import _world_loop as loop

_FORWARD_SHA='6a5f70a6acdaa6de52fc72d678d452956861370e1d143b70219ced107c5a04c9'
_CORE_SHA='81707c193e2ff85c40d7c2183d39a03a07b4c27ebd0713130e01da29ffc55214'
_DEPENDENCY_MANIFEST_SHA='4a6fa45aee4f522f0660e0f8401c71fdc5286ecd4fad112ed76b103f6b82875f'
_NUMPY_MANIFEST_SHA='1d9c45f5c650f06437cf7d3f2a986d0b585c966caf6200a134c790acb983d13a'

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _manifest_sha(records):
    return hashlib.sha256(json.dumps(sorted(records),ensure_ascii=False,
                          separators=(',',':')).encode('utf-8')).hexdigest()

def _verify_tree(root, records, allowed):
    root=Path(root).resolve(strict=True)
    if type(records) is not list or not records:
        raise ValueError('complete dependency manifest required')
    expected={}
    for item in records:
        if type(item) is not list or len(item)!=2 or any(type(x) is not str for x in item):
            raise ValueError('invalid dependency record')
        name,digest=item; rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name or rel.parts[0] not in allowed:
            raise ValueError('unapproved dependency path')
        if name in expected or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('duplicate or invalid dependency hash')
        expected[name]=digest
    actual={}
    for top in allowed:
        area=root/top
        if not area.exists(): raise ValueError('required package directory missing')
        for path in area.rglob('*'):
            if path.is_symlink(): raise ValueError('dependency symlink refused')
            if path.is_file(): actual[path.relative_to(root).as_posix()]=_sha(path)
    if actual != expected: raise ValueError('dependency inventory/hash mismatch')
    return root

class _Verified:
    __slots__=('dep','numpy','worktree','modules','llvm_dll',
               '_signature','_entry','_dispatcher','_typeof')
    def __init__(self, key, dep, numpy, worktree):
        if key is not _KEY: raise ValueError('verified dependencies required')
        self.dep,self.numpy,self.worktree,self.modules,self.llvm_dll=dep,numpy,worktree,None,None
        self._signature=self._entry=self._dispatcher=self._typeof=None
_KEY=object()

def verify_dependencies(config, project_root, worktree):
    """Hash exact package trees and origins before first numerical import."""
    if type(config) is not dict or set(config)!={'dependency_path','dependency_files','numpy_path','numpy_files'}:
        raise ValueError('exact JIT dependency manifest required')
    if (any(name in sys.modules or any(k.startswith(name+'.') for k in sys.modules)
            for name in ('numpy','numba','llvmlite'))
            or 'competition.deepeye.simulation.sensors._jit_ordered_kernel' in sys.modules):
        raise ValueError('JIT numerical packages already imported')
    root=Path(project_root).resolve(strict=True); work=Path(worktree).resolve(strict=True)
    dep=Path(config['dependency_path']).resolve(strict=True)
    if dep != (root/'.local/deepeye-jit-kernel-deps-20261030').resolve(strict=True):
        raise ValueError('exact owned dependency target required')
    numpy=Path(config['numpy_path']).resolve(strict=True)
    if numpy != (Path(sys.executable).resolve().parent/'Lib/site-packages').resolve(strict=True):
        raise ValueError('exact primary runtime numpy path required')
    if (_manifest_sha(config['dependency_files']) != _DEPENDENCY_MANIFEST_SHA
            or _manifest_sha(config['numpy_files']) != _NUMPY_MANIFEST_SHA):
        raise ValueError('pinned task64 dependency manifest identity mismatch')
    _verify_tree(dep,config['dependency_files'],('numba','numba-0.68.0.dist-info','llvmlite','llvmlite-0.50.0.dist-info','llvmlite.libs','bin'))
    _verify_tree(numpy,config['numpy_files'],('numpy','numpy-2.3.5.dist-info','numpy.libs'))
    core=work/'competition/deepeye/simulation/sensors/_jit_ordered_kernel.py'
    if _sha(core)!=_CORE_SHA or _sha(forward.__file__)!=_FORWARD_SHA:
        raise ValueError('pinned core or forward source mismatch')
    if Path(forward.__file__).resolve() != work/'competition/deepeye/simulation/sensors/forward_profile.py':
        raise ValueError('forward module origin mismatch')
    for name,area in (('numba',dep),('llvmlite',dep),('numpy',numpy)):
        spec=importlib.util.find_spec(name)
        if spec is None or Path(spec.origin).resolve()!=area/name/'__init__.py':
            raise ValueError('numerical import origin mismatch: '+name)
    if not (dep/'llvmlite/binding/llvmlite.dll').is_file():
        raise ValueError('pinned LLVM DLL absent')
    return _Verified(_KEY,dep,numpy,work)

def load_verified(verified):
    if type(verified) is not _Verified or verified.modules is not None:
        raise ValueError('one-use verified runtime required')
    np=importlib.import_module('numpy');nb=importlib.import_module('numba');ll=importlib.import_module('llvmlite')
    if (np.__version__,nb.__version__,ll.__version__) != ('2.3.5','0.68.0','0.50.0'):
        raise ValueError('numerical package versions differ')
    for name,area in (('numba',verified.dep),('llvmlite',verified.dep),('numpy',verified.numpy)):
        if Path(sys.modules[name].__file__).resolve()!=area/name/'__init__.py':
            raise ValueError('loaded numerical origin mismatch')
        for module_name, module in tuple(sys.modules.items()):
            if module_name.startswith(name+'.') and getattr(module,'__file__',None):
                if not Path(module.__file__).resolve().is_relative_to(area/name):
                    raise ValueError('loaded numerical submodule origin mismatch')
    core=importlib.import_module('competition.deepeye.simulation.sensors._jit_ordered_kernel')
    if Path(core.__file__).resolve()!=verified.worktree/'competition/deepeye/simulation/sensors/_jit_ordered_kernel.py':
        raise ValueError('loaded fixed kernel origin mismatch')
    from llvmlite.binding import ffi
    import ctypes
    expected=(verified.dep/'llvmlite/binding/llvmlite.dll').resolve()
    if Path(ffi.lib._name).resolve()!=expected:
        raise ValueError('LLVM requested library path mismatch')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_ulong]
    kernel.GetModuleFileNameW.restype=ctypes.c_ulong
    buf=ctypes.create_unicode_buffer(32768)
    if not kernel.GetModuleFileNameW(ffi.lib._handle,buf,len(buf)) or Path(buf.value).resolve()!=expected:
        raise ValueError('actual loaded LLVM module path mismatch')
    verified.llvm_dll=dict(path=str(expected),sha256=_sha(expected))
    verified.modules=(np,core)
    verified._typeof=nb.typeof
    return verified

def warm(verified):
    if type(verified) is not _Verified or verified.modules is None:
        raise ValueError('verified numerical runtime required')
    np,core=verified.modules
    if (verified._signature is not None or len(core._run.signatures)!=0
            or len(core._run.overloads)!=0 or not core._run._can_compile):
        raise ValueError('fresh unspecialized fixed dispatcher required')
    # No scene, pose, sensor or clock: compile the immutable-array signature.
    def frozen(a):return np.frombuffer(a.tobytes(),dtype=a.dtype).reshape(a.shape)
    rows=np.zeros((1,8),dtype=np.float64);rows[:,3:]=1.;rows=frozen(rows)
    ranks=frozen(np.zeros(0,dtype=np.int64));sigma=frozen(np.zeros(0,dtype=np.float64))
    unknown=frozen(np.zeros(0,dtype=np.bool_));xyz=frozen(np.zeros((0,3),dtype=np.float64))
    mats=frozen(np.zeros((0,3,3),dtype=np.float64))
    core._run(rows,np.zeros(3),np.eye(3),ranks,sigma,unknown,xyz,xyz,mats,.005,0.)
    import re
    if len(core._run.signatures)!=1 or len(core._run.overloads)!=1:
        raise ValueError('exactly one readonly compiled signature required')
    signature=core._run.signatures[0]
    ir=core._run.inspect_llvm(signature);asm=core._run.inspect_asm(signature)
    if (re.search(r'\b(?:fast|reassoc|contract|afn|nnan|ninf|nsz|arcp)\b|llvm\.(?:fma|fmuladd)',ir)
            or re.search(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*',asm,re.I)):
        raise ValueError('readonly compiled signature contains forbidden floating operations')
    entry=core._run.overloads[signature].entry_point
    core._run.disable_compile()
    verified._signature,verified._entry,verified._dispatcher=signature,entry,core._run
    _guard_arguments(verified,(rows,np.zeros(3),np.eye(3),ranks,sigma,unknown,xyz,xyz,mats,.005,0.))
    return dict(signature=str(signature),llvm_sha256=hashlib.sha256(ir.encode()).hexdigest(),
                asm_sha256=hashlib.sha256(asm.encode()).hexdigest(),forbidden_scan='clear',
                llvm_dll=verified.llvm_dll)

def _guard_arguments(verified,args):
    """Admit only the already-scanned, locked dispatcher and exact ABI."""
    if type(verified) is not _Verified or verified.modules is None or type(args) is not tuple or len(args)!=11:
        raise ValueError('verified fixed argument tuple required')
    np,core=verified.modules
    dispatcher=verified._dispatcher;signature=verified._signature;entry=verified._entry
    if (dispatcher is None or signature is None or entry is None or core._run is not dispatcher
            or dispatcher._can_compile or tuple(dispatcher.signatures)!=(signature,)
            or len(dispatcher.overloads)!=1 or signature not in dispatcher.overloads
            or dispatcher.overloads[signature].entry_point is not entry):
        raise ValueError('scanned compiled entry association lost')
    for i in range(9):
        a=args[i]
        if (type(a) is not np.ndarray or not a.flags.c_contiguous or not a.flags.aligned
                or bool(a.flags.writeable)!=(i in (1,2))):
            raise ValueError('fixed array layout/alignment/writeability required')
    rows,pos,rot,ranks,sigmas,unknown,centres,dims,matrices,bg,eps=args
    if (rows.ndim!=2 or rows.shape[1]!=8 or pos.shape!=(3,) or rot.shape!=(3,3)
            or ranks.ndim!=1 or sigmas.shape!=ranks.shape or unknown.shape!=ranks.shape
            or centres.shape!=(len(ranks),3) or dims.shape!=(len(ranks),3)
            or matrices.shape!=(len(ranks),3,3) or type(bg) is not float or type(eps) is not float):
        raise ValueError('fixed compiled field argument shapes required')
    if tuple(verified._typeof(arg) for arg in args)!=signature:
        raise ValueError('actual argument types differ from scanned signature')
    return entry

class _Backend:
    def __init__(self, key, factory, verified):
        if key is not _KEY or type(verified) is not _Verified or verified.modules is None:
            raise ValueError('verified fixed backend required')
        if factory._source.state!='NEW' or factory._source._count!=0 or factory._source._origin is not None:
            raise ValueError('fresh unstarted source required')
        factory._check(None)
        self._factory,self._source,self._thread=factory,factory._source,threading.get_ident()
        self._verified=verified
        self._np,self._core=verified.modules
        fn=forward.ForwardProfile.acquire_em
        if fn.__closure__ is not None or type(self._source._profile) is not forward.ForwardProfile:
            raise ValueError('original forward code object required')
        import types
        module_code=compile(Path(forward.__file__).read_bytes(), str(forward.__file__), 'exec')
        classes=[x for x in module_code.co_consts if isinstance(x,types.CodeType) and x.co_name=='ForwardProfile']
        codes=[x for x in classes[0].co_consts if isinstance(x,types.CodeType) and x.co_name=='acquire_em'] if len(classes)==1 else []
        if len(codes)!=1 or fn.__code__!=codes[0] or fn.__globals__ is not forward.__dict__:
            raise ValueError('original acquire_em code does not match pinned source')
        for name in ('_kernel_channels','_rotation_matrix','_valid_sigma','_weight_table'):
            expected=[x for x in module_code.co_consts if isinstance(x,types.CodeType) and x.co_name==name]
            actual=getattr(forward,name)
            if name=='_weight_table':actual=getattr(actual,'__wrapped__',None)
            if (len(expected)!=1 or type(actual) is not FunctionType
                    or actual.__code__!=expected[0] or actual.__globals__ is not forward.__dict__):
                raise ValueError('original forward helper differs: '+name)
        self._fallback=forward._kernel_channels
        self._rotation=forward._rotation_matrix
        self._run=self._core._run
        def frozen(a):return self._np.frombuffer(a.tobytes(),dtype=a.dtype).reshape(a.shape)
        self._rows=frozen(self._np.asarray(forward._weight_table(),dtype=self._np.float64))
        raw=self._core._prepare(factory._pieces,factory._background,factory._epsilon)
        self._prepared=(raw[0],raw[1],*(frozen(a) for a in raw[2:]))
        self._array_refs=(self._rows,*self._prepared[2:])
        self._digests=tuple(hashlib.sha256(a.tobytes()).digest() for a in (self._rows,*self._prepared[2:]))
        self._entry=_guard_arguments(verified,(self._rows,self._np.zeros(3),self._np.eye(3),
                                     *self._prepared[2:],factory._background,factory._epsilon))
        self._active=None;self._used=None
        g=dict(fn.__globals__);g['_kernel_channels']=self._kernel
        self._acquire=FunctionType(fn.__code__,g,fn.__name__,fn.__defaults__,fn.__closure__)
        self._acquire.__kwdefaults__=fn.__kwdefaults__
        if self._acquire.__code__ is not fn.__code__:
            raise ValueError('original forward code mismatch')
    def _check_arrays(self):
        arrays=(self._rows,*self._prepared[2:])
        if (forward._kernel_channels is not self._fallback or forward._rotation_matrix is not self._rotation
                or self._core._run is not self._run
                or len(arrays)!=len(self._array_refs)
                or any(a is not b for a,b in zip(arrays,self._array_refs))
                or any(a.flags.writeable for a in arrays)
                or tuple(hashlib.sha256(a.tobytes()).digest() for a in arrays)!=self._digests):
            raise ValueError('prepared arrays modified')
    def acquire(self,tick,pose,medium,scope):
        f=self._factory
        try:
            if (threading.get_ident()!=self._thread or type(scope) is not loop._EmAcquisitionScope
                    or scope._factory is not f or not scope._active or scope._ended
                    or f._active is not scope or f._owner._em_scope_active is not scope
                    or scope._tick!=tick or self._active is not None or self._used is scope
                    or self._source._last_tick!=tick or self._source._polling is not True):
                raise ValueError('one active consumed original EM scope required')
            current=f._check(tick)
            if current[0] is not scope._snapshot[0] or current[1] is not scope._snapshot[1] or current[2:]!=scope._snapshot[2:]:
                raise ValueError('original scope root snapshot changed')
            expected=forward.Pose(current[1].position_m,current[1].orientation_xyzw)
            import struct
            if (type(pose) is not forward.Pose or
                    struct.pack('>7d',*(pose.position_m+pose.orientation_xyzw)) !=
                    struct.pack('>7d',*(expected.position_m+expected.orientation_xyzw))):
                raise ValueError('pose must match original committed scope snapshot')
            self._check_arrays();self._used=scope;self._active=scope
            return self._acquire(self._source._profile,tick,pose,context=medium,sampler=scope.sampler)
        except BaseException:
            f._fail();raise
        finally:self._active=None
    def _kernel(self,pose,sampler):
        scope=self._active;f=self._factory
        if (scope is None or type(sampler) is not MethodType or sampler.__self__ is not scope
                or sampler.__func__ is not loop._EmAcquisitionScope._sample_sigma or scope._sampling
                or not scope._active or f._fault.is_set() or threading.get_ident()!=self._thread):
            f._fail();raise ValueError('fixed active scoped sampler required')
        np=self._np;field=f._field
        args=self._prepared
        inputs=(self._rows,np.asarray(pose.position_m,dtype=np.float64),
            np.asarray(forward._rotation_matrix(pose.orientation_xyzw),dtype=np.float64),
            *args[2:],field._background,field._epsilon)
        entry=_guard_arguments(self._verified,inputs)
        if entry is not self._entry:
            raise ValueError('original scanned compiled entry changed')
        if not self._prepared[1]:return forward._kernel_channels(pose,sampler)
        scope._sampling=True
        try:
            status,sw,sws=entry(*inputs)
        finally:scope._sampling=False
        self._check_arrays()
        if status==2:return forward._kernel_channels(pose,sampler)
        if status==1:return None
        if status!=0:raise ValueError('unknown fixed kernel result')
        logs=[-math.log10(float(sws[i])/float(sw[i])) for i in range(5)]
        return logs[0],logs[1]-logs[2],logs[3]-logs[4]

class _OriginalBackend(_Backend):pass
class _SoftwareBackend(_Backend):
    software_fixture_only=True

def _valid_backend_association(source, backend):
    if getattr(backend,'_source',None) is not source or getattr(backend,'_factory',None) is not source._em_scope_factory:
        return False
    factory=backend._factory
    if type(backend) is _OriginalBackend:
        return type(factory) is loop._OriginalEmScopeFactory
    return (type(backend) is _SoftwareBackend and type(factory) is loop._EmScopeFactoryCore
            and factory._key is loop._EM_SCOPE_SOFTWARE
            and not isinstance(factory._owner,loop._RootWorldOwner)
            and not loop.native.is_original_owner(factory._native))

def _make_original_backend(factory,verified=None):
    if type(factory) is not loop._OriginalEmScopeFactory:raise TypeError('exact original factory required')
    return _OriginalBackend(_KEY,factory,verified)

def _make_software_backend_for_test(factory,verified):
    if (type(factory) is not loop._EmScopeFactoryCore or factory._key is not loop._EM_SCOPE_SOFTWARE
            or isinstance(factory._owner,loop._RootWorldOwner) or loop.native.is_original_owner(factory._native)):
        raise TypeError('distinct software-only factory required')
    return _SoftwareBackend(_KEY,factory,verified)

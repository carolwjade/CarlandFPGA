"""NEW fixed real NumPy C22 CPU child with borrowed original Win32 HANDLEs.
No fd conversion, stdout READY, fake core, provider callback or wire override.
Only the separately released new private owner may launch this staged source.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'

def need(value,message):
    if value is not True: raise ValueError(message)

def unique(pairs):
    value={}
    for key,item in pairs:
        need(key not in value,'duplicate child layout key'); value[key]=item
    return value

def pin(path):
    size=0; digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            size+=len(block); digest.update(block)
    return dict(bytes=size,sha256=digest.hexdigest())

_STAGE_ROOT=Path(__file__).resolve().parent

def plain(path):
    # The Root owner verified ancestors before CreateProcess. The restricted
    # child verifies its closed stage only, without asking for parent access.
    need(path.is_absolute() and path.is_relative_to(_STAGE_ROOT),'closed private stage path required')
    for part in (path,*path.parents):
        if not part.is_relative_to(_STAGE_ROOT):break
        need(not part.is_symlink() and not (hasattr(part,'is_junction') and part.is_junction()) and not (getattr(part.lstat(),'st_file_attributes',0)&0x400),'child aliases forbidden')
    return path

def main():
    entered=time.monotonic_ns()
    need(os.name=='nt' and sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode is True,'exact Windows -I -S -B launch required')
    need(len(sys.argv)==5 and re.fullmatch('[0-9a-f]{64}',sys.argv[1]) is not None,'layout SHA and three original HANDLEs required')
    handles=[]
    for label in sys.argv[2:]:
        need(re.fullmatch('[1-9][0-9]{0,19}',label) is not None,'exact positive HANDLE decimal required')
        value=int(label); need(value<(1<<64),'HANDLE range invalid'); handles.append(value)
    need(len(set(handles))==3,'three distinct original HANDLEs required')
    ready,input_handle,output_handle=handles
    here=plain(Path(__file__).resolve().parent)
    raw=plain(here/'child-layout.json').read_bytes()
    need(len(raw)<=2*1024*1024 and hashlib.sha256(raw).hexdigest()==sys.argv[1],'exact child layout SHA required')
    layout=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite layout')))
    need(layout.keys()=={'schema','requirements_sha256','runtime_closure_sha256','numpy_version','files'} and type(layout['schema']) is int and layout['schema']==1 and layout['requirements_sha256']==CONTRACT and layout['numpy_version']=='2.5.4','exact Root CPU layout required')
    need(type(layout['files']) is list and 1<=len(layout['files'])<=20000,'bounded explicit child closure required')
    total=0; names=set()
    for row in layout['files']:
        need(type(row) is dict and row.keys()=={'path','bytes','sha256'},'exact child file pin required')
        name=row['path']; need(type(name) is str and name not in names and '\\' not in name and ':' not in name and not name.startswith('/') and all(x not in ('','.','..') for x in name.split('/')),'simple unique child path required')
        names.add(name); target=plain(here/name)
        need(target.is_file() and target.stat().st_nlink==1 and pin(target)=={'bytes':row['bytes'],'sha256':row['sha256']},'closed child file mismatch')
        total+=row['bytes']; need(total<=268435456,'retained stage cap exceeded')
    actual={path.relative_to(here).as_posix() for path in here.rglob('*') if path.is_file()}
    need(actual==names|{'child-layout.json'},'extra/unmanifested child file forbidden')
    need(Path(sys.executable).resolve()==here/'runtime/python.exe','staged base Python only')
    sys.path[:0]=[str(here/'product'),str(here/'runtime/Lib/site-packages')]
    # CPython's fixed native modules operate on the original borrowed HANDLEs.
    # No fd conversion, duplicate handles, dynamic FFI or alternate factory.
    import _winapi
    import _overlapped
    for handle in handles:
        need(os.get_handle_inheritable(handle) is True,'actual inherited original HANDLE flag required')
    need(_winapi.GetFileType(input_handle)==3 and _winapi.GetFileType(output_handle)==3,'original synchronous pipe HANDLEs required')
    from ai_pc.cpu_package import numpy_process_endpoint as endpoint
    need(Path(endpoint.__file__).resolve()==here/'product/ai_pc/cpu_package/numpy_process_endpoint.py','exact C22 entrypoint origin required')
    core=endpoint._new_core()  # The one real fixed constructor; NO forward or start_session.
    from ai_pc.cpu_package.numpy_stream_core import FrozenNumpyForceStream
    need(type(core) is FrozenNumpyForceStream,'exact real fixed core required')
    state=core.state()
    need(state.active_generation is None and state.active_epoch is None and state.sessions_started==0 and state.lifetime_deliveries==0 and state.lifetime_bytes==0,'no fabricated readiness/session/learning call')
    backend=core.backend_description()
    need(backend['backend_id']=='numpy-2.5.4-cpu-float32-einsum-optimize-false-v1' and backend['numpy_version']=='2.5.4','actual fixed NumPy CPU backend required')
    need(type(backend['parameter_count']) is int and backend['parameter_count']==4916 and backend['all_float32_readonly'] is True and type(backend['forward_attempts']) is int and backend['forward_attempts']==0,'all original learned parameters loaded, no readiness forward')
    need(backend['thread_environment']=={name:'1' for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')} and backend['dot_or_matmul_in_numeric_leaf'] is False,'actual fixed pre-import thread environment and leaf strategy required')
    need('torch' not in sys.modules and 'onnx' not in sys.modules,'no Torch/ONNX runtime fallback')
    used=False
    def held_fixed_core():
        nonlocal used
        need(used is False,'held real core consumed exactly once')
        used=True
        return core
    endpoint._new_core=held_fixed_core  # Fixed Root-owned handoff only; no selectable callback/factory.
    endpoint._load_parser()  # Pin/import parser before feedback window; no start or forward.
    def read_original(size):
        need(type(size) is int and 1<=size<=16384,'bounded C22 read required')
        try:data,error=_winapi.ReadFile(input_handle,size,False)
        except OSError as exc:
            if getattr(exc,'winerror',None)==109:return b''
            raise
        need(type(data) is bytes and type(error) is int and error==0 and len(data)<=size,'original synchronous C22 read result invalid')
        return data
    def write_original(raw):
        need(type(raw) is bytes and 1<=len(raw)<=6160,'one original full C22 response bound required')
        count,error=_winapi.WriteFile(output_handle,raw,False)
        need(type(count) is int and type(error) is int and error==0 and 0<=count<=len(raw),'original synchronous C22 write result invalid')
        return count  # EndpointDriver rejects short write; no remainder/retry.
    driver=endpoint.EndpointDriver(read_original,write_original,limits=endpoint.EndpointLimits(max_frames=2,max_observations=1,max_input_bytes=32768,max_output_bytes=8192))
    need(time.monotonic_ns()-entered<40_000_000_000,'fixed cold preparation bound exceeded')
    _overlapped.SetEvent(ready)  # One original signal; raises on failure; no readiness forward.
    outcome=driver.run()
    need(outcome.exit_code==0 and outcome.observations_called==1 and outcome.responses_emitted==2 and outcome.cleanup_failed is False and used is True,'actual C22 serial endpoint failed')
    # Keep original process live long enough for parent to record ENDED and STOP.
    # No tail read, output, session restart, model call or STOP acknowledgement.
    while time.monotonic_ns()-entered<45_000_000_000: time.sleep(.005)
    return 0

if __name__=='__main__':
    try: code=main()
    except BaseException as error:
        # Private failure-only source variant. Healthy wire behavior is unchanged.
        # Parent captures this before READY as unauthenticated diagnostic only.
        try:
            raw=json.dumps(dict(kind='private_child_startup_or_endpoint_failure',type=type(error).__name__[:80],message=str(error)[:512]),ensure_ascii=True)+'\n'
            if len(raw.encode('ascii'))<=2048:
                sys.stderr.write(raw);sys.stderr.flush()
        except BaseException:pass
        code=2
    sys.exit(code)

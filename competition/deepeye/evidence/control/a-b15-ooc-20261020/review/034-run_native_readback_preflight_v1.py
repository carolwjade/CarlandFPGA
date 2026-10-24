import ctypes as c,datetime,hashlib,json,msvcrt,os,pathlib,re,time
from ctypes import wintypes as w
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[2];F=D.parent/'a-b15-ooc-synthesis-fix2-20261020'
alias=pathlib.Path('C:/Users/CarlJade/AppData/Local/Temp/deepeye-b15-review-20261020-v1')
def check(v,s):
 if not v:raise AssertionError(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
 with (D/name).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
check(alias.is_dir() and alias.resolve()==D and str(alias).isascii(),'exact authorized alias')
check(not (D/'native-readback-started.json').exists() and not (D/'native-readback-result.json').exists(),'one native readback only')
old=json.loads((F/'inputs.json').read_bytes());dcppath=F/'artifacts/synthesized.dcp';sourcealias=pathlib.Path(old['alias']);check(sourcealias.resolve()==F,'original DCP alias identity')
batch=pathlib.Path(old['batch']);launcher=ROOT/'.local/toolchain/LaunchVivadoLicensed.vbs';license_value=os.environ.get('XILINXD_LICENSE_FILE')
if not license_value:license_value=re.search(r'^\s*licenseFile = "([^"]+)"',launcher.read_text(encoding='utf-8-sig'),re.M)[1]
check(batch.is_file() and sha(batch)==old['launcher_sha256'],'pinned existing Vivado launcher')
temp=alias/'native-temp';temp.mkdir();allowed={'SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT','USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA','ALLUSERSPROFILE','HOMEDRIVE','HOMEPATH','USERNAME','OS','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS','SYSTEMDRIVE','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','COMMONPROGRAMFILES','COMMONPROGRAMFILES(X86)'}
env={k:v for k,v in os.environ.items() if k.upper() in allowed};env.update(XILINXD_LICENSE_FILE=license_value,TEMP=str(temp),TMP=str(temp),OMP_NUM_THREADS='1')
environment=c.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(env.items(),key=lambda kv:kv[0].upper()))+'\0\0')
class Basic(c.Structure):_fields_=[('process_time',c.c_int64),('job_time',c.c_int64),('flags',w.DWORD),('min_ws',c.c_size_t),('max_ws',c.c_size_t),('active_limit',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class IO(c.Structure):_fields_=[(n,c.c_uint64) for n in ['reads','writes','other','read_bytes','write_bytes','other_bytes']]
class Extended(c.Structure):_fields_=[('basic',Basic),('io',IO),('process_memory',c.c_size_t),('job_memory',c.c_size_t),('peak_process_memory',c.c_size_t),('peak_job_memory',c.c_size_t)]
class Startup(c.Structure):_fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),('x',w.DWORD),('y',w.DWORD),('xs',w.DWORD),('ys',w.DWORD),('xc',w.DWORD),('yc',w.DWORD),('fill',w.DWORD),('flags',w.DWORD),('show',w.WORD),('reserved_size',w.WORD),('reserved2',c.POINTER(w.BYTE)),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
class Process(c.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
class Accounting(c.Structure):_fields_=[('user',c.c_int64),('kernel',c.c_int64),('period_user',c.c_int64),('period_kernel',c.c_int64),('page_faults',w.DWORD),('total_processes',w.DWORD),('active_processes',w.DWORD),('terminated_processes',w.DWORD)]
k=c.WinDLL('kernel32',use_last_error=True)
defs={'CreateJobObjectW':([c.c_void_p,w.LPCWSTR],w.HANDLE),'SetInformationJobObject':([w.HANDLE,c.c_int,c.c_void_p,w.DWORD],w.BOOL),'QueryInformationJobObject':([w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p],w.BOOL),'AssignProcessToJobObject':([w.HANDLE,w.HANDLE],w.BOOL),'CreateProcessW':([w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(Startup),c.POINTER(Process)],w.BOOL),'SetHandleInformation':([w.HANDLE,w.DWORD,w.DWORD],w.BOOL),'ResumeThread':([w.HANDLE],w.DWORD),'WaitForSingleObject':([w.HANDLE,w.DWORD],w.DWORD),'GetExitCodeProcess':([w.HANDLE,c.POINTER(w.DWORD)],w.BOOL),'TerminateJobObject':([w.HANDLE,w.UINT],w.BOOL),'TerminateProcess':([w.HANDLE,w.UINT],w.BOOL),'CloseHandle':([w.HANDLE],w.BOOL)}
for name,(args,restype) in defs.items():f=getattr(k,name);f.argtypes=args;f.restype=restype
def must(x):
 if not x:raise c.WinError(c.get_last_error())
cmdexe=pathlib.Path(os.environ['SystemRoot'])/'System32/cmd.exe';command=f'"{cmdexe}" /d /s /c ""{batch}" -mode batch -notrace -source readback.tcl -log readback.log -journal readback.jou"'
sourcefiles=[pathlib.Path(__file__),D/'readback.tcl',dcppath,D/'expected-ports.json',batch,launcher];before={str(p):sha(p) for p in sourcefiles};save('native-inputs-before.json',before)
job=k.CreateJobObjectW(None,None);must(job);info=Process();resumed=False;start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
 limits=Extended();limits.basic.flags=0x200|0x2000|0x20;limits.basic.priority=0x4000;limits.job_memory=4294967296;must(k.SetInformationJobObject(job,9,c.byref(limits),c.sizeof(limits)))
 verified=Extended();must(k.QueryInformationJobObject(job,9,c.byref(verified),c.sizeof(verified),None));check(verified.job_memory==4294967296 and verified.basic.priority==0x4000,'actual enforced job limits')
 with (D/'native-stdout.txt').open('xb') as out,(D/'native-stderr.txt').open('xb') as err,open(os.devnull,'rb') as inp:
  handles=[msvcrt.get_osfhandle(f.fileno()) for f in [inp,out,err]];si=Startup();si.cb=c.sizeof(si);si.flags=0x101;si.show=0;si.stdin,si.stdout,si.stderr=handles
  for h in handles:must(k.SetHandleInformation(h,1,1))
  try:must(k.CreateProcessW(str(cmdexe),c.create_unicode_buffer(command),None,None,True,0x08000000|0x4|0x400|0x4000,environment,str(alias),c.byref(si),c.byref(info)))
  finally:
   for h in handles:must(k.SetHandleInformation(h,1,0))
  must(k.AssignProcessToJobObject(job,info.process))
  save('native-readback-started.json',{'command':command,'started_utc':started,'pid':info.pid,'cwd_alias':str(alias),'cwd_resolved':str(alias.resolve()),'creation':'CREATE_NO_WINDOW, SW_HIDE, suspended; private job assigned before resume','job_flags':verified.basic.flags,'priority_class':verified.basic.priority,'memory_cap_bytes':verified.job_memory,'timeout_seconds':50,'maxThreads':1,'environment_names_only':sorted(env),'input_hashes':before,'scope':'one open_checkpoint; no synthesis/implementation/bitstream/hardware/GUI'})
  check(k.ResumeThread(info.thread)!=0xffffffff,'resume owned suspended process');resumed=True
  wait=k.WaitForSingleObject(info.process,max(1,int((50-(time.monotonic()-start))*1000)));timeout=wait==0x102
  if timeout:must(k.TerminateJobObject(job,124));k.WaitForSingleObject(info.process,2000)
  else:check(wait==0,'native wait')
  code=w.DWORD();must(k.GetExitCodeProcess(info.process,c.byref(code)));usage=Extended();must(k.QueryInformationJobObject(job,9,c.byref(usage),c.sizeof(usage),None));account=Accounting();must(k.QueryInformationJobObject(job,1,c.byref(account),c.sizeof(account),None));residual=int(account.active_processes)
  if residual:must(k.TerminateJobObject(job,125))
  text=(D/'native-stdout.txt').read_text(encoding='utf-8',errors='replace');log=(D/'readback.log').read_text(encoding='utf-8',errors='replace') if (D/'readback.log').exists() else '';errors=re.findall(r'^(?:ERROR:|B15_CHECKPOINT_READBACK_FAIL).*$',text+'\n'+log,re.M);warnings=re.findall(r'^(?:WARNING:|CRITICAL WARNING:).*$',log,re.M)
 after={str(p):sha(p) for p in sourcefiles};save('native-inputs-after.json',after);check(before==after,'native inputs unchanged')
 passed=code.value==0 and not timeout and not errors and len(re.findall(r'^B15_CHECKPOINT_READBACK_PASS\r?$',text,re.M))==1 and all((D/p).is_file() for p in ['readback-facts.txt','readback-ports.txt','readback-utilization.rpt'])
 result={'status':'pass' if passed else 'failed','started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration_seconds':time.monotonic()-start,'batch_exit_code':code.value,'timeout':timeout,'peak_job_committed_memory_bytes':usage.peak_job_memory,'actual_job_memory_cap_bytes':verified.job_memory,'actual_job_priority_class':verified.basic.priority,'total_job_processes':account.total_processes,'residual_processes_before_job_close':residual,'kill_on_close':True,'error_lines':errors,'warning_lines':warnings,'input_hashes_unchanged':True,'stdout_sha256':sha(D/'native-stdout.txt'),'stderr_sha256':sha(D/'native-stderr.txt'),'new_synthesis_runs':0,'new_open_checkpoint_runs':1,'implementation_board_all29':'not_run'};save('native-readback-result.json',result);print(json.dumps(result));check(passed,'native readback failed; do not replay')
except BaseException:
 if info.process:
  k.TerminateJobObject(job,125) if resumed else k.TerminateProcess(info.process,125);k.WaitForSingleObject(info.process,2000)
 raise
finally:
 for h in [info.thread,info.process,job]:
  if h:k.CloseHandle(h)

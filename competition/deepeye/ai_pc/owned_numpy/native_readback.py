"""Actual read-only native queries, loaded ONLY after a separate Root release.

No OpenProcess/PID lookup, endpoint opening, cancellation, termination, API patch
or backend injection. The only new HANDLE is a query-only original-Job duplicate.
"""
import ctypes as C
from ctypes import wintypes as W

P=C.c_void_p
K=C.WinDLL('kernel32',use_last_error=True)
A=C.WinDLL('advapi32',use_last_error=True)

def bind(dll,name,args,result=W.BOOL):
    fn=getattr(dll,name); fn.argtypes=args; fn.restype=result; return fn

GetCurrentProcess=bind(K,'GetCurrentProcess',[],W.HANDLE)
DuplicateHandle=bind(K,'DuplicateHandle',[W.HANDLE,W.HANDLE,W.HANDLE,C.POINTER(W.HANDLE),W.DWORD,W.BOOL,W.DWORD])
CloseHandle=bind(K,'CloseHandle',[W.HANDLE])
GetFlags=bind(K,'GetHandleInformation',[W.HANDLE,C.POINTER(W.DWORD)])
QueryJob=bind(K,'QueryInformationJobObject',[W.HANDLE,C.c_int,P,W.DWORD,P])
GetSecurityInfo=bind(A,'GetSecurityInfo',[W.HANDLE,C.c_int,W.DWORD,P,P,C.POINTER(P),P,C.POINTER(P)],W.DWORD)
GetControl=bind(A,'GetSecurityDescriptorControl',[P,C.POINTER(W.WORD),C.POINTER(W.DWORD)])
GetAce=bind(A,'GetAce',[P,W.DWORD,C.POINTER(P)])
SidText=bind(A,'ConvertSidToStringSidW',[P,C.POINTER(P)])
LocalFree=bind(K,'LocalFree',[P],P)

def check(ok,label):
    if not ok: raise C.WinError(C.get_last_error(),label)

class ACL(C.Structure):
    _fields_=[('revision',C.c_ubyte),('sbz1',C.c_ubyte),('size',W.WORD),('count',W.WORD),('sbz2',W.WORD)]

class ACCOUNTING(C.Structure):
    _fields_=[('TotalUserTime',C.c_longlong),('TotalKernelTime',C.c_longlong),
      ('ThisPeriodTotalUserTime',C.c_longlong),('ThisPeriodTotalKernelTime',C.c_longlong),
      ('TotalPageFaultCount',W.DWORD),('TotalProcesses',W.DWORD),
      ('ActiveProcesses',W.DWORD),('TotalTerminatedProcesses',W.DWORD)]

def pipe_acl(original_native):
    """Query the already-owned pipe kernel object; free only query allocations."""
    sd=P(); dacl=P(); error=GetSecurityInfo(original_native,6,4,None,None,C.byref(dacl),None,C.byref(sd))
    if error: raise OSError(error,'GetSecurityInfo original pipe')
    primary=None
    try:
        if not sd or not dacl: raise ValueError('actual non-null protected DACL required')
        control=W.WORD(); revision=W.DWORD()
        check(GetControl(sd,C.byref(control),C.byref(revision)),'GetSecurityDescriptorControl')
        header=C.cast(dacl,C.POINTER(ACL)).contents
        if header.count>16 or header.size>4096: raise ValueError('bounded pipe ACL required')
        rows=[]
        for i in range(header.count):
            ace=P(); check(GetAce(dacl,i,C.byref(ace)),'GetAce')
            raw=C.string_at(ace,8); ace_type,flags=raw[0],raw[1]
            size=int.from_bytes(raw[2:4],'little'); mask=int.from_bytes(raw[4:8],'little')
            if ace_type!=0 or size<12 or size>512: raise ValueError('one simple allow ACE required')
            sid=P(); check(SidText(ace.value+8,C.byref(sid)),'ConvertSidToStringSidW')
            try: text=C.wstring_at(sid)
            finally:
                if LocalFree(sid): raise OSError('LocalFree query SID failed')
            rows.append({'type':ace_type,'flags':flags,'size':size,'mask':mask,'sid':text})
        return {'control':control.value,'revision':revision.value,'protected':bool(control.value&0x1000),
                'acl_revision':header.revision,'acl_size':header.size,'aces':rows}
    except BaseException as error:
        primary=error; raise
    finally:
        if sd and LocalFree(sd):
            if primary is None: raise OSError('LocalFree query descriptor failed')
            primary.add_note('LocalFree query descriptor failed')

class OriginalJobQuery:
    def __init__(self,original):
        self.original=original; self.handle=None; self.close_attempted=False; self.close_returned=None
        duplicate=W.HANDLE(); current=GetCurrentProcess()
        check(DuplicateHandle(current,original,current,C.byref(duplicate),4,False,0),
              'DuplicateHandle original Job query-only')
        self.handle=duplicate.value
    def snapshot(self):
        if self.close_attempted: raise ValueError('Job query duplicate already close-claimed')
        flags=W.DWORD(); check(GetFlags(self.handle,C.byref(flags)),'GetHandleInformation Job query duplicate')
        if flags.value!=0: raise ValueError('actual query duplicate must be non-inheritable')
        value=ACCOUNTING(); check(QueryJob(self.handle,1,C.byref(value),C.sizeof(value),None),'Query original Job accounting')
        return {'original_job_native':self.original,'query_duplicate_native':self.handle,
          'desired_access':4,'actual_handle_flags':flags.value,'inheritable':False,
          'accounting':{n:getattr(value,n) for n,_ in value._fields_}}
    def close_after_empty(self):
        if self.close_attempted: raise ValueError('no duplicate close replay')
        row=self.snapshot()
        if row['accounting']['ActiveProcesses']!=0: raise ValueError('Job not empty; duplicate retained')
        self.close_attempted=True
        ok=CloseHandle(self.handle); self.close_returned=bool(ok)
        check(ok,'CloseHandle original Job query duplicate once')
        return {'close_attempted':True,'close_returned':True,'last_accounting':row}

"""Narrow ctypes bindings. Every kernel object created here belongs to one run."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess

if os.name != 'nt':
    raise OSError('AppContainer prototype requires Windows')

P = C.c_void_p
SIZE = C.c_size_t
K = C.WinDLL('kernel32', use_last_error=True)
A = C.WinDLL('advapi32', use_last_error=True)
U = C.WinDLL('userenv', use_last_error=True)
O = C.WinDLL('ole32', use_last_error=True)


def bind(dll, name, args, result=W.BOOL):
    fn = getattr(dll, name)
    fn.argtypes, fn.restype = args, result
    return fn


CloseHandle = bind(K, 'CloseHandle', [W.HANDLE])
LocalFree = bind(K, 'LocalFree', [P], P)
FreeSid = bind(A, 'FreeSid', [P], P)
OpenProcessToken = bind(A, 'OpenProcessToken', [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)])
GetTokenInformation = bind(A, 'GetTokenInformation', [W.HANDLE, C.c_int, P, W.DWORD, C.POINTER(W.DWORD)])
ConvertSidToStringSidW = bind(A, 'ConvertSidToStringSidW', [P, C.POINTER(W.LPWSTR)])
GetCurrentProcess = bind(K, 'GetCurrentProcess', [], W.HANDLE)
OpenProcess = bind(K, 'OpenProcess', [W.DWORD, W.BOOL, W.DWORD], W.HANDLE)
CreateProfile = bind(U, 'CreateAppContainerProfile', [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, P, W.DWORD, C.POINTER(P)], C.c_long)
DeleteProfile = bind(U, 'DeleteAppContainerProfile', [W.LPCWSTR], C.c_long)
GetProfilePath = bind(U, 'GetAppContainerFolderPath', [W.LPCWSTR, C.POINTER(W.LPWSTR)], C.c_long)
CoTaskMemFree = bind(O, 'CoTaskMemFree', [P], None)
ConvertSD = bind(A, 'ConvertStringSecurityDescriptorToSecurityDescriptorW', [W.LPCWSTR, W.DWORD, C.POINTER(P), C.POINTER(W.DWORD)])
GetSecurityDescriptorDacl = bind(A, 'GetSecurityDescriptorDacl', [P, C.POINTER(W.BOOL), C.POINTER(P), C.POINTER(W.BOOL)])
SetNamedSecurityInfoW = bind(A, 'SetNamedSecurityInfoW', [W.LPWSTR, C.c_int, W.DWORD, P, P, P, P], W.DWORD)


def check(ok, operation):
    if not ok:
        raise C.WinError(C.get_last_error(), operation)


def check_hr(hr, operation):
    if hr < 0:
        raise OSError(f'{operation}: HRESULT 0x{hr & 0xffffffff:08x}')


def sid_text(sid):
    out = W.LPWSTR()
    check(ConvertSidToStringSidW(sid, C.byref(out)), 'ConvertSidToStringSidW')
    try:
        return out.value
    finally:
        LocalFree(C.cast(out, P))


def token_buffer(token, kind):
    size = W.DWORD()
    GetTokenInformation(token, kind, None, 0, C.byref(size))
    if not size.value:
        raise C.WinError(C.get_last_error(), 'GetTokenInformation size')
    buf = C.create_string_buffer(size.value)
    check(GetTokenInformation(token, kind, buf, size, C.byref(size)), 'GetTokenInformation')
    return buf


def user_sid():
    token = W.HANDLE()
    check(OpenProcessToken(GetCurrentProcess(), 8, C.byref(token)), 'OpenProcessToken self')
    try:
        buf = token_buffer(token, 1)
        return sid_text(C.cast(buf, C.POINTER(P))[0])
    finally:
        CloseHandle(token)


def set_new_object_acl(path, run_root, user, package=None):
    """Apply ACL before populating a fresh, exclusively owned directory.

    Directory ACLs propagate to existing children, including hardlink aliases
    outside the logical root. Refuse populated directories, never recurse over
    and try to repair them. The trusted parent must own this preparation phase
    exclusively; this helper is not a defence against concurrent trusted edits.
    """
    path, root = Path(path).absolute(), Path(run_root).absolute()
    if '..' in path.parts or '..' in root.parts:
        raise ValueError('ACL target must not contain parent traversal')
    if not path.is_relative_to(root) or not path.exists():
        raise ValueError('ACL target must be an existing task-owned object')
    for part in (path, *path.parents):
        if (part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction())
                or getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('ACL target contains reparse point')
    path, root = path.resolve(strict=True), root.resolve(strict=True)
    if not path.is_relative_to(root) or (path.is_file() and path.stat().st_nlink > 1):
        raise ValueError('ACL target aliases an object outside task ownership')
    if path.is_dir() and next(path.iterdir(), None) is not None:
        raise ValueError('ACL directory must be empty before applying inheritable permissions')
    acl = f'D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;{user})'
    if package:
        acl += f'(A;OICI;0x1200a9;;;{package})'
    sd, dacl = P(), P()
    present, defaulted = W.BOOL(), W.BOOL()
    check(ConvertSD(acl, 1, C.byref(sd), None), 'ConvertStringSecurityDescriptor')
    try:
        check(GetSecurityDescriptorDacl(sd, C.byref(present), C.byref(dacl), C.byref(defaulted)), 'GetSecurityDescriptorDacl')
        err = SetNamedSecurityInfoW(str(path), 1, 4 | 0x80000000, None, None, dacl, None)
        if err:
            raise C.WinError(err, 'SetNamedSecurityInfoW')
    finally:
        LocalFree(sd)
    return {'path': str(path), 'sddl': acl}


class SA(C.Structure):
    _fields_ = [('nLength', W.DWORD), ('lpSecurityDescriptor', P), ('bInheritHandle', W.BOOL)]


class STARTUPINFO(C.Structure):
    _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR), ('lpDesktop', W.LPWSTR),
                ('lpTitle', W.LPWSTR), ('dwX', W.DWORD), ('dwY', W.DWORD),
                ('dwXSize', W.DWORD), ('dwYSize', W.DWORD), ('dwXCountChars', W.DWORD),
                ('dwYCountChars', W.DWORD), ('dwFillAttribute', W.DWORD),
                ('dwFlags', W.DWORD), ('wShowWindow', W.WORD), ('cbReserved2', W.WORD),
                ('lpReserved2', P), ('hStdInput', W.HANDLE), ('hStdOutput', W.HANDLE),
                ('hStdError', W.HANDLE)]


class STARTUPINFOEX(C.Structure):
    _fields_ = [('StartupInfo', STARTUPINFO), ('lpAttributeList', P)]


class PI(C.Structure):
    _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE),
                ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]


class SECURITY_CAPABILITIES(C.Structure):
    _fields_ = [('AppContainerSid', P), ('Capabilities', P),
                ('CapabilityCount', W.DWORD), ('Reserved', W.DWORD)]


class BASIC_LIMIT(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_longlong), ('PerJobUserTimeLimit', C.c_longlong),
                ('LimitFlags', W.DWORD), ('MinimumWorkingSetSize', SIZE),
                ('MaximumWorkingSetSize', SIZE), ('ActiveProcessLimit', W.DWORD),
                ('Affinity', SIZE), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]


class IO_COUNTERS(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in ('ReadOperationCount', 'WriteOperationCount',
                'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class EXTENDED_LIMIT(C.Structure):
    _fields_ = [('BasicLimitInformation', BASIC_LIMIT), ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', SIZE), ('JobMemoryLimit', SIZE),
                ('PeakProcessMemoryUsed', SIZE), ('PeakJobMemoryUsed', SIZE)]


CreatePipe = bind(K, 'CreatePipe', [C.POINTER(W.HANDLE), C.POINTER(W.HANDLE), C.POINTER(SA), W.DWORD])
SetHandleInformation = bind(K, 'SetHandleInformation', [W.HANDLE, W.DWORD, W.DWORD])
GetHandleInformation = bind(K, 'GetHandleInformation', [W.HANDLE, C.POINTER(W.DWORD)])
PeekNamedPipe = bind(K, 'PeekNamedPipe', [W.HANDLE, P, W.DWORD, P, C.POINTER(W.DWORD), P])
ReadFile = bind(K, 'ReadFile', [W.HANDLE, P, W.DWORD, C.POINTER(W.DWORD), P])
WriteFile = bind(K, 'WriteFile', [W.HANDLE, P, W.DWORD, C.POINTER(W.DWORD), P])
CreateFileW = bind(K, 'CreateFileW', [W.LPCWSTR, W.DWORD, W.DWORD, C.POINTER(SA), W.DWORD, W.DWORD, W.HANDLE], W.HANDLE)
CreateJob = bind(K, 'CreateJobObjectW', [P, W.LPCWSTR], W.HANDLE)
SetJobInfo = bind(K, 'SetInformationJobObject', [W.HANDLE, C.c_int, P, W.DWORD])
QueryJobInfo = bind(K, 'QueryInformationJobObject', [W.HANDLE, C.c_int, P, W.DWORD, P])
AssignJob = bind(K, 'AssignProcessToJobObject', [W.HANDLE, W.HANDLE])
IsProcessInJob = bind(K, 'IsProcessInJob', [W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)])
InitAttributes = bind(K, 'InitializeProcThreadAttributeList', [P, W.DWORD, W.DWORD, C.POINTER(SIZE)])
UpdateAttribute = bind(K, 'UpdateProcThreadAttribute', [P, W.DWORD, SIZE, P, SIZE, P, P])
DeleteAttributes = bind(K, 'DeleteProcThreadAttributeList', [P], None)
CreateProcess = bind(K, 'CreateProcessW', [W.LPCWSTR, W.LPWSTR, P, P, W.BOOL, W.DWORD, P, W.LPCWSTR, C.POINTER(STARTUPINFOEX), C.POINTER(PI)])
GetMitigation = bind(K, 'GetProcessMitigationPolicy', [W.HANDLE, C.c_int, P, SIZE])
ResumeThread = bind(K, 'ResumeThread', [W.HANDLE], W.DWORD)
Wait = bind(K, 'WaitForSingleObject', [W.HANDLE, W.DWORD], W.DWORD)
TerminateProcess = bind(K, 'TerminateProcess', [W.HANDLE, W.UINT])
GetExitCodeProcess = bind(K, 'GetExitCodeProcess', [W.HANDLE, C.POINTER(W.DWORD)])
GetProcessTimes = bind(K, 'GetProcessTimes', [W.HANDLE, C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME)])


def pipe():
    r, w = W.HANDLE(), W.HANDLE()
    sa = SA(C.sizeof(SA), None, True)
    check(CreatePipe(C.byref(r), C.byref(w), C.byref(sa), 16384), 'CreatePipe')
    return r.value, w.value


def write(handle, value):
    count = W.DWORD()
    check(WriteFile(handle, value, len(value), C.byref(count), None), 'WriteFile')
    if count.value != len(value):
        raise OSError('short pipe write')


def read(handle, size=8192):
    buf, count = C.create_string_buffer(size), W.DWORD()
    check(ReadFile(handle, buf, size, C.byref(count), None), 'ReadFile')
    return buf.raw[:count.value]


def handle_flags(handle):
    flags = W.DWORD()
    check(GetHandleInformation(handle, C.byref(flags)), 'GetHandleInformation')
    return flags.value


def available_output(handle):
    count = W.DWORD()
    if not PeekNamedPipe(handle, None, 0, None, C.byref(count), None):
        error = C.get_last_error()
        if error == 109:
            return b''
        raise C.WinError(error, 'PeekNamedPipe')
    return read(handle, min(count.value, 8192)) if count.value else b''


def create_job():
    job = CreateJob(None, None)
    check(job, 'CreateJobObjectW')
    try:
        info = EXTENDED_LIMIT()
        info.BasicLimitInformation.LimitFlags = 0x2000 | 0x8 | 0x100  # kill, one child, 256 MiB
        info.BasicLimitInformation.ActiveProcessLimit = 1
        info.ProcessMemoryLimit = 256 * 1024 * 1024
        check(SetJobInfo(job, 9, C.byref(info), C.sizeof(info)), 'SetInformationJobObject limits')
        ui = W.DWORD(0xff)
        check(SetJobInfo(job, 4, C.byref(ui), C.sizeof(ui)), 'SetInformationJobObject UI')
        return job
    except BaseException:
        CloseHandle(job)
        raise


def create_suspended(exe, argv, cwd, environment, sid, input_handle, output_handle):
    values = [(0x20009, SECURITY_CAPABILITIES(sid, None, 0, 0)),
              (0x20002, (W.HANDLE * 2)(input_handle, output_handle)),
              (0x20007, C.c_ulonglong(1 << 28)),
              (0x2000e, W.DWORD(1))]
    size = SIZE()
    InitAttributes(None, len(values), 0, C.byref(size))
    buf = C.create_string_buffer(size.value)
    check(InitAttributes(buf, len(values), 0, C.byref(size)), 'InitializeProcThreadAttributeList')
    try:
        for key, value in values:
            check(UpdateAttribute(buf, 0, key, C.byref(value), C.sizeof(value), None, None), f'UpdateProcThreadAttribute 0x{key:x}')
        si = STARTUPINFOEX()
        si.StartupInfo.cb = C.sizeof(si)
        si.StartupInfo.dwFlags = 0x100 | 1
        si.StartupInfo.hStdInput = input_handle
        si.StartupInfo.hStdOutput = si.StartupInfo.hStdError = output_handle
        si.lpAttributeList = C.cast(buf, P)
        pi = PI()
        cmd = C.create_unicode_buffer(subprocess.list2cmdline([str(exe), *map(str, argv)]))
        env = C.create_unicode_buffer('\0'.join(f'{k}={v}' for k, v in sorted(environment.items())) + '\0\0')
        # DETACHED_PROCESS avoids console initialization under Win32k lockdown.
        # CREATE_NO_WINDOW produced STATUS_DLL_INIT_FAILED on the target host.
        flags = 0x00080000 | 0x00000400 | 0x00000004 | 0x00000008
        check(CreateProcess(str(exe), cmd, None, None, True, flags, env, str(cwd), C.byref(si), C.byref(pi)), 'CreateProcessW AppContainer suspended')
        return pi
    finally:
        DeleteAttributes(buf)


def inspect_process(process, job, expected_sid):
    token = W.HANDLE()
    check(OpenProcessToken(process, 8, C.byref(token)), 'OpenProcessToken child')
    try:
        is_ac = C.cast(token_buffer(token, 29), C.POINTER(W.DWORD))[0]
        sid_buf = token_buffer(token, 31)
        actual_sid = sid_text(C.cast(sid_buf, C.POINTER(P))[0])
        caps = C.cast(token_buffer(token, 30), C.POINTER(W.DWORD))[0]
    finally:
        CloseHandle(token)
    policies = {}
    for name, number in [('win32k', 4), ('child', 13), ('strict_handle', 3)]:
        value = W.DWORD()
        check(GetMitigation(process, number, C.byref(value), C.sizeof(value)), f'GetProcessMitigationPolicy {name}')
        policies[name] = value.value
    member = W.BOOL()
    check(IsProcessInJob(process, job, C.byref(member)), 'IsProcessInJob')
    limits, ui = EXTENDED_LIMIT(), W.DWORD()
    check(QueryJobInfo(job, 9, C.byref(limits), C.sizeof(limits), None), 'QueryInformationJobObject limits')
    check(QueryJobInfo(job, 4, C.byref(ui), C.sizeof(ui), None), 'QueryInformationJobObject UI')
    job_values = {'limit_flags': limits.BasicLimitInformation.LimitFlags,
                  'active_process_limit': limits.BasicLimitInformation.ActiveProcessLimit,
                  'process_memory_limit': limits.ProcessMemoryLimit, 'ui_restrictions': ui.value}
    job_matches = job_values == {'limit_flags': 0x2108, 'active_process_limit': 1,
                                'process_memory_limit': 268435456, 'ui_restrictions': 255}
    times = [W.FILETIME() for _ in range(4)]
    check(GetProcessTimes(process, *(C.byref(t) for t in times)), 'GetProcessTimes')
    return {'is_appcontainer': bool(is_ac), 'appcontainer_sid': actual_sid,
            'sid_matches': actual_sid == expected_sid, 'capability_count': caps,
            'win32k_disabled': bool(policies['win32k'] & 1),
            'child_process_restricted': bool(policies['child'] & 1),
            'mitigation_raw': policies, 'in_job': bool(member.value),
            'job_limits': job_values, 'job_limits_match': job_matches,
            'creation_filetime': times[0].dwHighDateTime << 32 | times[0].dwLowDateTime}

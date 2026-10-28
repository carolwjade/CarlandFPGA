"""Narrow ctypes bindings. Every kernel object created here belongs to one run."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import sys

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


def create_profile(name, *, owner):
    sid = P()
    check_hr(CreateProfile(name, name, 'Temporary DeepEye CPU boundary fixture', None, 0,
                           C.byref(sid)), 'CreateAppContainerProfile')
    pending_io = getattr(owner, '_pending_io', None)
    capsules = (None if pending_io is None else (
        pending_io.capture_native('profile', name, 'profile'),
        pending_io.capture_native('profile_sid', sid, 'sid')))
    owner.own_profile(name, sid)
    if capsules is not None:
        pending_io.registered_native(capsules[0], owner.find('profile'))
        pending_io.registered_native(capsules[1], owner.find('profile_sid'))
    return sid


def profile_path(sid, *, owner):
    raw = W.LPWSTR()
    check_hr(GetProfilePath(sid, C.byref(raw)), 'GetAppContainerFolderPath')
    ref = _own_fresh(owner, 'profile_path_string', C.cast(raw, P), release='cotask')
    try:
        if not raw.value:
            raise OSError('profile path was not returned')
        path = Path(raw.value)
        owner.set_profile_path(path)
        return path
    finally:
        _release_temporary(owner, ref, lambda: CoTaskMemFree(C.cast(raw, P)))


def profile_absent(path):
    if path is None:
        return None
    try:
        Path(path).stat()
    except FileNotFoundError:
        return True
    except OSError:
        return None
    return False


def own_canary(path, *, owner):
    sa = SA(C.sizeof(SA), None, True)
    handle = CreateFileW(str(path), 0x80000000, 7, C.byref(sa), 3, 0x80, None)
    check(handle != C.c_void_p(-1).value, 'CreateFileW canary parent')
    return owner.own_handle('canary', handle)


def canary_read(handle, size):
    return read(handle, size)


def parent_controls(*, owner):
    for access in (8, 16, 32, 64, 128):
        handle = OpenProcess(access, False, os.getpid())
        check(handle, f'OpenProcess parent positive control {access}')
        ref = owner.own_handle('parent_positive_control', handle)
        owner.release_checked(ref)
    return True


def exit_code(handle):
    code = W.DWORD()
    check(GetExitCodeProcess(handle, C.byref(code)), 'GetExitCodeProcess')
    return code.value


def _release_temporary(owner, ref, release):
    """Do not replace an active primary error with a helper release failure."""
    primary_active = sys.exc_info()[0] is not None
    if owner is not None:
        try:
            owner.release_checked(ref, preserve_primary=primary_active)
        except BaseException as error:
            if not primary_active: raise
            pending_io = getattr(owner, '_pending_io', None)
            if pending_io is not None: pending_io.errors.append(error)
    else:
        # Legacy standalone callers get a checked local contract, without a
        # returned recovery registry. The launcher always supplies its owner.
        try:
            release()
        except BaseException:
            if not primary_active:
                raise


def _own_fresh(owner, label, native, **options):
    """Retain a new raw native return before ledger registration may fail."""
    pending_io = getattr(owner, '_pending_io', None)
    capsule = (None if pending_io is None else pending_io.capture_native(
        label, native, options.get('release', 'kernel'), options.get('keepalive')))
    reference = owner.own_handle(label, native, **options)
    if capsule is not None: pending_io.registered_native(capsule, reference)
    return reference


def sid_text(sid, *, owner=None):
    out = W.LPWSTR()
    check(ConvertSidToStringSidW(sid, C.byref(out)), 'ConvertSidToStringSidW')
    ref = _own_fresh(owner, 'sid_string', C.cast(out, P), release='local') if owner else None
    try:
        return out.value
    finally:
        _release_temporary(owner, ref, lambda: check(not LocalFree(C.cast(out, P)), 'LocalFree SID string'))


def token_buffer(token, kind):
    size = W.DWORD()
    GetTokenInformation(token, kind, None, 0, C.byref(size))
    if not size.value:
        raise C.WinError(C.get_last_error(), 'GetTokenInformation size')
    buf = C.create_string_buffer(size.value)
    check(GetTokenInformation(token, kind, buf, size, C.byref(size)), 'GetTokenInformation')
    return buf


def user_sid(*, owner=None):
    token = W.HANDLE()
    check(OpenProcessToken(GetCurrentProcess(), 8, C.byref(token)), 'OpenProcessToken self')
    ref = _own_fresh(owner, 'self_token', token) if owner else None
    try:
        buf = token_buffer(token, 1)
        return sid_text(C.cast(buf, C.POINTER(P))[0], owner=owner)
    finally:
        _release_temporary(owner, ref, lambda: check(CloseHandle(token), 'CloseHandle self token'))


def set_new_object_acl(path, run_root, user, package=None, *, owner=None):
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
    ref = _own_fresh(owner, 'security_descriptor', sd, release='local') if owner else None
    try:
        check(GetSecurityDescriptorDacl(sd, C.byref(present), C.byref(dacl), C.byref(defaulted)), 'GetSecurityDescriptorDacl')
        err = SetNamedSecurityInfoW(str(path), 1, 4 | 0x80000000, None, None, dacl, None)
        if err:
            raise C.WinError(err, 'SetNamedSecurityInfoW')
    finally:
        _release_temporary(owner, ref, lambda: check(not LocalFree(sd), 'LocalFree security descriptor'))
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
CreateNamedPipeW = bind(K, 'CreateNamedPipeW', [W.LPCWSTR, W.DWORD, W.DWORD, W.DWORD,
    W.DWORD, W.DWORD, W.DWORD, C.POINTER(SA)], W.HANDLE)
ConnectNamedPipe = bind(K, 'ConnectNamedPipe', [W.HANDLE, P])
CreateEventW = bind(K, 'CreateEventW', [C.POINTER(SA), W.BOOL, W.BOOL, W.LPCWSTR], W.HANDLE)
GetOverlappedResult = bind(K, 'GetOverlappedResult', [W.HANDLE, P, C.POINTER(W.DWORD), W.BOOL])
CancelIoEx = bind(K, 'CancelIoEx', [W.HANDLE, P])


def logon_sid(*, owner):
    """Actual unique SE_GROUP_LOGON_ID from this original parent token."""
    class SID_AND_ATTRIBUTES(C.Structure):
        _fields_ = [('Sid', P), ('Attributes', W.DWORD)]
    class TOKEN_GROUPS(C.Structure):
        _fields_ = [('GroupCount', W.DWORD), ('Groups', SID_AND_ATTRIBUTES * 1)]
    token = W.HANDLE()
    check(OpenProcessToken(GetCurrentProcess(), 8, C.byref(token)), 'OpenProcessToken logon SID')
    ref = _own_fresh(owner, 'logon_token', token)
    try:
        buf = token_buffer(token, 2)
        count = C.cast(buf, C.POINTER(W.DWORD))[0]
        if not 1 <= count <= 1024:
            raise ValueError('bounded actual token group list required')
        if TOKEN_GROUPS.Groups.offset + count * C.sizeof(SID_AND_ATTRIBUTES) > C.sizeof(buf):
            raise ValueError('token group buffer truncated')
        groups = (SID_AND_ATTRIBUTES * count).from_buffer(buf, TOKEN_GROUPS.Groups.offset)
        matches = [group for group in groups if group.Attributes & 0xc0000000 == 0xc0000000]
        if len(matches) != 1:
            raise ValueError('one actual token logon SID required')
        text = sid_text(matches[0].Sid, owner=owner)
        if not text.startswith('S-1-5-5-'):
            raise ValueError('actual logon SID shape rejected')
        return text
    finally:
        _release_temporary(owner, ref, lambda: check(CloseHandle(token), 'CloseHandle logon token'))


def overlapped_server(name, label, direction, logon, *, owner):
    """One owned first-instance server; client pairing is done by the owner."""
    sd = P()
    check(ConvertSD('D:P(A;;GA;;;' + logon + ')', 1, C.byref(sd), None), 'ConvertStringSecurityDescriptor pipe')
    descriptor = _own_fresh(owner, 'pipe_security_descriptor', sd, release='local')
    try:
        sa = SA(C.sizeof(SA), sd, False)
        mode = {'inbound': 1, 'outbound': 2}[direction] | 0x40000000 | 0x00080000
        handle = CreateNamedPipeW(name, mode, 0x8, 1, 16384, 16384, 0, C.byref(sa))
        error = C.get_last_error() if handle == C.c_void_p(-1).value or handle is None else 0
        if error or handle is None or handle == C.c_void_p(-1).value:
            raise C.WinError(error, 'CreateNamedPipeW first instance')
        _own_fresh(owner, label, handle)
        return handle
    finally:
        _release_temporary(owner, descriptor, lambda: check(not LocalFree(sd), 'LocalFree pipe descriptor'))


def synchronous_client(name, label, direction, *, owner):
    sa = SA(C.sizeof(SA), None, True)
    access = {'inbound': 0x40000000, 'outbound': 0x80000000}[direction]
    handle = CreateFileW(name, access, 0, C.byref(sa), 3, 0x80, None)
    error = C.get_last_error() if handle == C.c_void_p(-1).value or handle is None else 0
    if error or handle is None or handle == C.c_void_p(-1).value:
        raise C.WinError(error, 'CreateFileW original synchronous child endpoint')
    _own_fresh(owner, label, handle)
    return handle


def overlapped_event(label, *, owner):
    handle = CreateEventW(None, True, False, None)
    error = C.get_last_error() if not handle else 0
    if not handle: raise C.WinError(error, 'CreateEventW manual-reset original IO')
    _own_fresh(owner, label, handle)
    return handle


def model_ready_event(*, owner):
    # NEW unnamed inherited event, registered in the same original resource cohort.
    sa = SA(C.sizeof(SA), None, True)
    handle = CreateEventW(C.byref(sa), True, False, None)
    error = C.get_last_error() if not handle else 0
    if not handle: raise C.WinError(error, 'CreateEventW original model-ready')
    _own_fresh(owner, 'model_ready', handle)
    return handle


def pipe_connect(op):
    result = ConnectNamedPipe(op.native, C.byref(op.overlapped))
    error = C.get_last_error() if not result else 0
    return result, error


def pipe_write(op):
    result = WriteFile(op.native, op.buffer, op.size, None, C.byref(op.overlapped))
    error = C.get_last_error() if not result else 0
    return result, error


def pipe_read(op):
    result = ReadFile(op.native, op.buffer, op.size, None, C.byref(op.overlapped))
    error = C.get_last_error() if not result else 0
    return result, error


def pipe_result(op):
    count = W.DWORD()
    result = GetOverlappedResult(op.native, C.byref(op.overlapped), C.byref(count), False)
    error = C.get_last_error() if not result else 0
    return result, error, count.value if result and op.kind != 'connect' else None


def pipe_cancel(op):
    result = CancelIoEx(op.native, C.byref(op.overlapped))
    error = C.get_last_error() if not result else 0
    return result, error


def terminate_original(handle):
    result = TerminateProcess(handle, 0xdead)
    error = C.get_last_error() if not result else 0
    return result, error


def pipe(*, owner, read_label, write_label):
    r, w = W.HANDLE(), W.HANDLE()
    sa = SA(C.sizeof(SA), None, True)
    check(CreatePipe(C.byref(r), C.byref(w), C.byref(sa), 16384), 'CreatePipe')
    owner.own_pair((read_label, r, {}), (write_label, w, {}))
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


def create_job(*, owner):
    job = CreateJob(None, None)
    check(job, 'CreateJobObjectW')
    _own_fresh(owner, 'job', job, recovery=True)
    info = EXTENDED_LIMIT()
    info.BasicLimitInformation.LimitFlags = 0x2000 | 0x8 | 0x100  # kill, one child, 256 MiB
    info.BasicLimitInformation.ActiveProcessLimit = 1
    info.ProcessMemoryLimit = 256 * 1024 * 1024
    check(SetJobInfo(job, 9, C.byref(info), C.sizeof(info)), 'SetInformationJobObject limits')
    ui = W.DWORD(0xff)
    check(SetJobInfo(job, 4, C.byref(ui), C.sizeof(ui)), 'SetInformationJobObject UI')
    return job


def create_suspended(exe, argv, cwd, environment, sid, input_handle, output_handle, *, owner):
    values = [(0x20009, SECURITY_CAPABILITIES(sid, None, 0, 0)),
              (0x20002, (W.HANDLE * 3)(input_handle, output_handle, owner.find('model_ready').native)),
              (0x20007, C.c_ulonglong(1 << 28)),
              (0x2000e, W.DWORD(1))]
    size = SIZE()
    InitAttributes(None, len(values), 0, C.byref(size))
    buf = C.create_string_buffer(size.value)
    check(InitAttributes(buf, len(values), 0, C.byref(size)), 'InitializeProcThreadAttributeList')
    attributes = _own_fresh(owner, 'attributes', C.cast(buf, P), release='attributes', keepalive=(buf, values))
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
        pending_io = owner._pending_io
        if pending_io is not None: pending_io.process_started(pi)
        created = CreateProcess(str(exe), cmd, None, None, True, flags, env, str(cwd), C.byref(si), C.byref(pi))
        create_error = C.get_last_error() if not created else 0
        if pending_io is not None: pending_io.process_returned(created, pi)
        if not created: raise C.WinError(create_error, 'CreateProcessW AppContainer suspended')
        owner.own_process(pi)
        return pi
    finally:
        _release_temporary(owner, attributes, lambda: DeleteAttributes(buf))


def inspect_process(process, job, expected_sid, *, owner=None):
    token = W.HANDLE()
    check(OpenProcessToken(process, 8, C.byref(token)), 'OpenProcessToken child')
    ref = _own_fresh(owner, 'child_token', token) if owner else None
    try:
        is_ac = C.cast(token_buffer(token, 29), C.POINTER(W.DWORD))[0]
        sid_buf = token_buffer(token, 31)
        actual_sid = sid_text(C.cast(sid_buf, C.POINTER(P))[0], owner=owner)
        caps = C.cast(token_buffer(token, 30), C.POINTER(W.DWORD))[0]
    finally:
        _release_temporary(owner, ref, lambda: check(CloseHandle(token), 'CloseHandle child token'))
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

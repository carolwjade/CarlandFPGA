"""One new hidden Vivado batch process tree with explicit resource limits."""
import ctypes as ct
from ctypes import wintypes as wt
from datetime import datetime, timezone
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import re
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GiB = 1024 ** 3


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BasicLimits(ct.Structure):
    _fields_ = [
        ("process_time", ct.c_int64), ("job_time", ct.c_int64),
        ("flags", wt.DWORD), ("min_working_set", ct.c_size_t),
        ("max_working_set", ct.c_size_t), ("active_processes", wt.DWORD),
        ("affinity", ct.c_size_t), ("priority", wt.DWORD),
        ("scheduling", wt.DWORD)]


class IOCounters(ct.Structure):
    _fields_ = [(name, ct.c_uint64) for name in (
        "read_operations", "write_operations", "other_operations",
        "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(ct.Structure):
    _fields_ = [
        ("basic", BasicLimits), ("io", IOCounters),
        ("process_memory", ct.c_size_t), ("job_memory", ct.c_size_t),
        ("peak_process_memory", ct.c_size_t), ("peak_job_memory", ct.c_size_t)]


class StartupInfo(ct.Structure):
    _fields_ = [
        ("cb", wt.DWORD), ("reserved", wt.LPWSTR), ("desktop", wt.LPWSTR),
        ("title", wt.LPWSTR), ("x", wt.DWORD), ("y", wt.DWORD),
        ("x_size", wt.DWORD), ("y_size", wt.DWORD),
        ("x_chars", wt.DWORD), ("y_chars", wt.DWORD),
        ("fill", wt.DWORD), ("flags", wt.DWORD), ("show", wt.WORD),
        ("reserved2_size", wt.WORD), ("reserved2", ct.POINTER(wt.BYTE)),
        ("stdin", wt.HANDLE), ("stdout", wt.HANDLE), ("stderr", wt.HANDLE)]


class ProcessInfo(ct.Structure):
    _fields_ = [
        ("process", wt.HANDLE), ("thread", wt.HANDLE),
        ("pid", wt.DWORD), ("tid", wt.DWORD)]


k = ct.WinDLL("kernel32", use_last_error=True)
k.CreateJobObjectW.argtypes = [ct.c_void_p, wt.LPCWSTR]
k.CreateJobObjectW.restype = wt.HANDLE
k.SetInformationJobObject.argtypes = [wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD]
k.SetInformationJobObject.restype = wt.BOOL
k.QueryInformationJobObject.argtypes = [wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD, ct.c_void_p]
k.QueryInformationJobObject.restype = wt.BOOL
k.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
k.AssignProcessToJobObject.restype = wt.BOOL
k.CreateProcessW.argtypes = [
    wt.LPCWSTR, wt.LPWSTR, ct.c_void_p, ct.c_void_p, wt.BOOL, wt.DWORD,
    ct.c_void_p, wt.LPCWSTR, ct.POINTER(StartupInfo), ct.POINTER(ProcessInfo)]
k.CreateProcessW.restype = wt.BOOL
k.SetHandleInformation.argtypes = [wt.HANDLE, wt.DWORD, wt.DWORD]
k.SetHandleInformation.restype = wt.BOOL
k.ResumeThread.argtypes = [wt.HANDLE]
k.ResumeThread.restype = wt.DWORD
k.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
k.WaitForSingleObject.restype = wt.DWORD
k.GetExitCodeProcess.argtypes = [wt.HANDLE, ct.POINTER(wt.DWORD)]
k.GetExitCodeProcess.restype = wt.BOOL
k.TerminateJobObject.argtypes = [wt.HANDLE, wt.UINT]
k.TerminateJobObject.restype = wt.BOOL
k.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
k.TerminateProcess.restype = wt.BOOL
k.CloseHandle.argtypes = [wt.HANDLE]
k.CloseHandle.restype = wt.BOOL


def must(ok):
    if not ok:
        raise ct.WinError(ct.get_last_error())


inputs = json.loads((HERE / "inputs.json").read_bytes())
alias = Path(inputs["alias"])
assert alias.resolve() == HERE and alias.is_dir() and str(alias).isascii()
assert not (HERE / "run-started.json").exists()
assert not (HERE / "run-result.json").exists()
for row in inputs["sources"]:
    assert digest(HERE / row["snapshot"]) == row["sha256"]
launcher = (ROOT / ".local/toolchain/LaunchVivadoLicensed.vbs").read_text(encoding="utf-8-sig")
license_value = os.environ.get("XILINXD_LICENSE_FILE") or re.search(
    r'^\s*licenseFile = "([^"]+)"', launcher, re.M)[1]
batch = Path(inputs["batch"])
assert batch.is_file()
temporary = alias / "runtime-temp"
temporary.mkdir()
allowed_env = {
    "SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "USERPROFILE",
    "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "ALLUSERSPROFILE",
    "HOMEDRIVE", "HOMEPATH", "USERNAME", "OS", "PROCESSOR_ARCHITECTURE",
    "NUMBER_OF_PROCESSORS", "SYSTEMDRIVE", "PROGRAMFILES", "PROGRAMFILES(X86)",
    "PROGRAMW6432", "COMMONPROGRAMFILES", "COMMONPROGRAMFILES(X86)"}
env = {name: value for name, value in os.environ.items() if name.upper() in allowed_env}
env["XILINXD_LICENSE_FILE"] = license_value
env["TEMP"] = env["TMP"] = str(temporary)
env["OMP_NUM_THREADS"] = "1"
environment = ct.create_unicode_buffer(
    "\0".join(f"{name}={value}" for name, value in sorted(env.items(), key=lambda row: row[0].upper())) + "\0\0")
command_exe = Path(os.environ["SystemRoot"]) / "System32/cmd.exe"
command = f'"{command_exe}" /d /s /c ""{batch}" -mode batch -notrace -source synthesize.tcl -log vivado.log -journal vivado.jou"'
started = datetime.now(timezone.utc).isoformat()
input_hashes = {name: digest(HERE / name) for name in ("inputs.json", "synthesize.tcl", "run_hidden.py")}
job = k.CreateJobObjectW(None, None)
must(job)
info = ProcessInfo()
resumed = False
start_time = time.monotonic()
try:
    limits = ExtendedLimits()
    # JOB_MEMORY | KILL_ON_JOB_CLOSE | PRIORITY_CLASS, without breakaway.
    limits.basic.flags = 0x200 | 0x2000 | 0x20
    limits.basic.priority = 0x4000  # BELOW_NORMAL_PRIORITY_CLASS
    limits.job_memory = 4 * GiB
    must(k.SetInformationJobObject(job, 9, ct.byref(limits), ct.sizeof(limits)))
    with (HERE / "stdout.txt").open("xb") as stdout, (HERE / "stderr.txt").open("xb") as stderr, open(os.devnull, "rb") as stdin:
        si = StartupInfo()
        si.cb = ct.sizeof(si)
        si.flags = 0x100 | 1  # USESTDHANDLES | USESHOWWINDOW
        si.show = 0
        handles = [msvcrt.get_osfhandle(f.fileno()) for f in (stdin, stdout, stderr)]
        for handle in handles:
            must(k.SetHandleInformation(handle, 1, 1))
        si.stdin, si.stdout, si.stderr = handles
        try:
            must(k.CreateProcessW(
                str(command_exe), ct.create_unicode_buffer(command),
                None, None, True,
                0x08000000 | 0x4 | 0x400 | 0x4000,
                environment, str(alias), ct.byref(si), ct.byref(info)))
        finally:
            for handle in handles:
                must(k.SetHandleInformation(handle, 1, 0))
        must(k.AssignProcessToJobObject(job, info.process))
        save(HERE / "run-started.json", {
            "started_utc": started, "pid": info.pid, "command": command,
            "cwd_alias": str(alias), "resolved_cwd": str(alias.resolve()),
            "resource_limits": {"threads": 1, "job_memory_bytes": 4 * GiB,
                                "timeout_seconds": 240, "priority": "below_normal"},
            "creation": "suspended; assigned to private kill-on-close job before resume",
            "gui": False, "environment_names_only": sorted(env), "input_hashes": input_hashes})
        if k.ResumeThread(info.thread) == 0xFFFFFFFF:
            raise ct.WinError(ct.get_last_error())
        resumed = True
        print(json.dumps({"started": True, "pid": info.pid, "hidden": True,
                          "one_thread": True, "timeout_seconds": 240}), flush=True)
        waited = k.WaitForSingleObject(info.process, 240000)
        timed_out = waited == 0x102
        if timed_out:
            must(k.TerminateJobObject(job, 124))
            assert k.WaitForSingleObject(info.process, 10000) == 0
        elif waited != 0:
            raise ct.WinError(ct.get_last_error())
        code = wt.DWORD()
        must(k.GetExitCodeProcess(info.process, ct.byref(code)))
        usage = ExtendedLimits()
        must(k.QueryInformationJobObject(job, 9, ct.byref(usage), ct.sizeof(usage), None))
    text = (HERE / "stdout.txt").read_text(encoding="utf-8", errors="replace")
    err = (HERE / "stderr.txt").read_text(encoding="utf-8", errors="replace")
    log = (HERE / "vivado.log").read_text(encoding="utf-8", errors="replace") if (HERE / "vivado.log").exists() else ""
    required = ["synthesis-facts.txt", "artifacts/synthesized.dcp", "artifacts/synthesized.v", "utilization.rpt", "synthesis_drc.rpt"]
    absent = [name for name in required if not (HERE / name).is_file()]
    exact_pass = len(re.findall(r"^DEEPEYE_OOC_SYNTHESIS_PASS\r?$", text, re.M)) == 1
    errors = re.findall(r"^(?:ERROR:|DEEPEYE_OOC_SYNTHESIS_FAIL).*$", text + "\n" + err + "\n" + log, re.M)
    warnings = re.findall(r"^(?:CRITICAL WARNING:|WARNING:).*$", log, re.M)
    for row in inputs["sources"]:
        assert digest(HERE / row["snapshot"]) == row["sha256"]
    assert all(digest(HERE / name) == value for name, value in input_hashes.items())
    passed = code.value == 0 and not timed_out and exact_pass and not absent and not errors
    result = {
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": time.monotonic() - start_time, "pid": info.pid,
        "exit_code": code.value, "timeout": timed_out,
        "peak_job_committed_memory_bytes": usage.peak_job_memory,
        "exact_stdout_pass_marker": exact_pass, "missing_outputs": absent,
        "error_lines": errors, "warning_lines": warnings,
        "source_inputs_unchanged": True, "batch_synthesis_candidate": "pass" if passed else "failed",
        "independent_review": "pending", "timing_implementation_board_all29": "not_run"}
    save(HERE / "run-result.json", result)
    print(json.dumps(result), flush=True)
except BaseException as exc:
    if info.process:
        if resumed:
            k.TerminateJobObject(job, 125)
        else:
            k.TerminateProcess(info.process, 125)
        k.WaitForSingleObject(info.process, 10000)
    save(HERE / "runner-failure.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "type": type(exc).__name__,
        "message": str(exc), "pid": info.pid, "resumed": resumed})
    raise
finally:
    for handle in (info.thread, info.process, job):
        if handle:
            k.CloseHandle(handle)

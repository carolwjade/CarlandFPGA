"""Bound one newly created Windows process tree; never find/kill by image name."""
import ctypes as ct
from ctypes import wintypes as wt
from datetime import datetime, timezone
import json
import msvcrt
import os
from pathlib import Path
import shutil
import stat
import subprocess
import threading
import time
from boundary import PolicyError, check_no_links, file_hash, require, save_new

class BasicLimits(ct.Structure):
    _fields_ = [("process_time", ct.c_int64), ("job_time", ct.c_int64),
                ("flags", wt.DWORD), ("min_ws", ct.c_size_t), ("max_ws", ct.c_size_t),
                ("active", wt.DWORD), ("affinity", ct.c_size_t),
                ("priority", wt.DWORD), ("scheduling", wt.DWORD)]
class IOCounters(ct.Structure):
    _fields_ = [(n, ct.c_uint64) for n in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
class ExtendedLimits(ct.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IOCounters), ("process_memory", ct.c_size_t),
                ("job_memory", ct.c_size_t), ("peak_process", ct.c_size_t), ("peak_job", ct.c_size_t)]
class Accounting(ct.Structure):
    _fields_ = [(n, ct.c_int64) for n in ("user", "kernel", "period_user", "period_kernel")] + [
        ("faults", wt.DWORD), ("total", wt.DWORD), ("active", wt.DWORD), ("terminated", wt.DWORD)]
class Startup(ct.Structure):
    _fields_ = [("cb", wt.DWORD), ("reserved", wt.LPWSTR), ("desktop", wt.LPWSTR), ("title", wt.LPWSTR),
                ("x", wt.DWORD), ("y", wt.DWORD), ("xs", wt.DWORD), ("ys", wt.DWORD),
                ("xc", wt.DWORD), ("yc", wt.DWORD), ("fill", wt.DWORD), ("flags", wt.DWORD),
                ("show", wt.WORD), ("reserved_count", wt.WORD), ("reserved_bytes", ct.POINTER(wt.BYTE)),
                ("stdin", wt.HANDLE), ("stdout", wt.HANDLE), ("stderr", wt.HANDLE)]
class StartupEx(ct.Structure):
    _fields_ = [("si", Startup), ("attributes", ct.c_void_p)]
class Process(ct.Structure):
    _fields_ = [("process", wt.HANDLE), ("thread", wt.HANDLE), ("pid", wt.DWORD), ("tid", wt.DWORD)]

k = ct.WinDLL("kernel32", use_last_error=True)
def api(name, args, ret=wt.BOOL):
    f = getattr(k, name)
    f.argtypes, f.restype = args, ret
    return f
api("CreateJobObjectW", [ct.c_void_p, wt.LPCWSTR], wt.HANDLE)
api("SetInformationJobObject", [wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD])
api("QueryInformationJobObject", [wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD, ct.c_void_p])
api("AssignProcessToJobObject", [wt.HANDLE, wt.HANDLE])
api("CreateProcessW", [wt.LPCWSTR, wt.LPWSTR, ct.c_void_p, ct.c_void_p, wt.BOOL, wt.DWORD,
                      ct.c_void_p, wt.LPCWSTR, ct.c_void_p, ct.POINTER(Process)])
api("InitializeProcThreadAttributeList", [ct.c_void_p, wt.DWORD, wt.DWORD, ct.POINTER(ct.c_size_t)])
api("UpdateProcThreadAttribute", [ct.c_void_p, wt.DWORD, ct.c_size_t, ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.c_void_p])
api("DeleteProcThreadAttributeList", [ct.c_void_p], None)
api("ResumeThread", [wt.HANDLE], wt.DWORD)
api("WaitForSingleObject", [wt.HANDLE, wt.DWORD], wt.DWORD)
api("GetExitCodeProcess", [wt.HANDLE, ct.POINTER(wt.DWORD)])
api("TerminateJobObject", [wt.HANDLE, wt.UINT])
api("TerminateProcess", [wt.HANDLE, wt.UINT])
api("CloseHandle", [wt.HANDLE])
api("OpenProcess", [wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE)
api("QueryFullProcessImageNameW", [wt.HANDLE, wt.DWORD, wt.LPWSTR, ct.POINTER(wt.DWORD)])
api("IsProcessInJob", [wt.HANDLE, wt.HANDLE, ct.POINTER(wt.BOOL)])
api("GetProcessTimes", [wt.HANDLE, *([ct.POINTER(wt.FILETIME)]*4)])
api("GetProcessId", [wt.HANDLE], wt.DWORD)

_unconfirmed_trees = []

def must(ok):
    if not ok:
        raise ct.WinError(ct.get_last_error())

def job_pids(job):
    raw = ct.create_string_buffer(8 + 64*ct.sizeof(ct.c_size_t))
    must(k.QueryInformationJobObject(job, 3, raw, len(raw), None))
    assigned, count = (wt.DWORD*2).from_buffer(raw)
    require(count <= 64 and assigned <= 64, "process inventory overflow")
    return list((ct.c_size_t*count).from_buffer(raw, 8))

def process_identity(pid, job):
    handle = k.OpenProcess(0x1000 | 0x100000, False, pid)
    must(handle)
    try:
        member = wt.BOOL()
        must(k.IsProcessInJob(handle, job, ct.byref(member)))
        require(member.value, "worker outside private job")
        buf, size = ct.create_unicode_buffer(32768), wt.DWORD(32768)
        must(k.QueryFullProcessImageNameW(handle, 0, buf, ct.byref(size)))
        path = check_no_links(buf.value)
        return {"pid": pid, "image": str(path), "image_sha256": file_hash(path)}
    finally:
        k.CloseHandle(handle)

class HeldMembers:
    """Retain process objects through signal confirmation, not just PID lists."""
    def __init__(self, pid, handle):
        self.handles = {pid: handle}
        self.creation = {pid: self.created_at(handle)}
        self.absent_before_open = []
        self.empty_job_pending = []

    @staticmethod
    def created_at(handle):
        created, exited, kernel, user = (wt.FILETIME() for _ in range(4))
        must(k.GetProcessTimes(handle, ct.byref(created), ct.byref(exited),
                              ct.byref(kernel), ct.byref(user)))
        return (created.dwHighDateTime << 32) | created.dwLowDateTime

    def observe(self, job, pids):
        for pid in pids:
            if pid in self.handles:
                continue
            handle = k.OpenProcess(0x1000 | 0x100000, False, pid)
            if not handle:
                error = ct.get_last_error()
                if error == 87:  # Exact PID no longer exists, not a held handle.
                    self.absent_before_open.append(pid)
                    continue
                raise ct.WinError(error)
            try:
                member = wt.BOOL()
                must(k.IsProcessInJob(handle, job, ct.byref(member)))
                require(member.value, "reported member no longer belongs to own job")
                self.creation[pid] = self.created_at(handle)
                self.handles[pid] = handle
            except BaseException:
                k.CloseHandle(handle)
                raise

    def pending(self):
        pending = []
        for pid, handle in self.handles.items():
            waited = k.WaitForSingleObject(handle, 0)
            require(waited in (0, 0x102), "owned member handle wait failed")
            if waited != 0:
                pending.append(pid)
        return pending

    def wait_terminated(self, job, seconds=5):
        deadline = time.monotonic() + seconds
        while True:
            pids = job_pids(job)
            self.observe(job, pids)
            pending = self.pending()
            if not pids and not pending:
                return True
            if not pids and pending and len(self.empty_job_pending) < 32:
                self.empty_job_pending.append({"pending_pids": pending})
            if time.monotonic() >= deadline:
                return False
            time.sleep(.01)

    def evidence(self):
        rows = []
        for pid, handle in self.handles.items():
            waited = k.WaitForSingleObject(handle, 0)
            code = wt.DWORD()
            must(k.GetExitCodeProcess(handle, ct.byref(code)))
            rows.append({"pid": pid, "creation_filetime": self.creation[pid],
                         "wait_result": waited, "signaled": waited == 0,
                         "exit_code": code.value})
        return {"held_members": rows, "absent_before_handle_open": self.absent_before_open,
                "empty_job_with_pending_handles": self.empty_job_pending}

    def close(self):
        for handle in self.handles.values():
            k.CloseHandle(handle)
        self.handles.clear()

def fence_previous_trees():
    # No next tree starts while an exact retained member is still nonsignaled.
    for previous in _unconfirmed_trees:
        require(not previous.pending(), "previous owned member termination unconfirmed")
    for previous in _unconfirmed_trees:
        previous.close()
    _unconfirmed_trees.clear()

def measure_tree(root):
    if not os.path.lexists(root):
        return 0, 0
    check_no_links(root)
    total, count, stack = 0, 0, [Path(root)]
    while stack:
        for item in os.scandir(stack.pop()):
            s = os.lstat(item.path)
            require(not stat.S_ISLNK(s.st_mode) and not getattr(s, "st_file_attributes", 0) & 0x400,
                    "watched tree link/reparse")
            count += 1
            require(count <= 100000, "watched tree scan cap")
            if stat.S_ISDIR(s.st_mode):
                stack.append(Path(item.path))
            else:
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "watched tree nonregular/hardlink")
                total += s.st_size
    return total, count

def run_bounded(argv, env, cwd, evidence, budget, watch_roots, on_tick=None):
    """No retries; one private job; bounded pipes; suspended assignment first.

    on_tick(job, pids) is trusted outer-runner code only. Tree/free-space quotas
    are sampled at 20 ms and can overshoot; job memory/process counts are OS
    limits, and persisted stdout/stderr never exceed their byte limits.
    """
    require(os.name == "nt", "Windows required")
    fence_previous_trees()
    require(0 < budget["seconds"] <= 50, "stage time limit")
    cwd = check_no_links(cwd)
    evidence = check_no_links(evidence, missing_ok=True)
    require(not os.path.lexists(evidence), "existing attempt: no retry")
    evidence.mkdir()
    require(shutil.disk_usage(evidence).free >= budget["free_reserve_bytes"], "free reserve before launch")
    job, proc, assigned, resumed = None, Process(), False, False
    handles, fds, threads, faults = [], [], [], []
    stop = threading.Event()
    lock = threading.Lock()
    output_counts = {}
    seen = set()
    started = time.monotonic()
    reason = None
    terminated = False
    result = None
    peak_tree = 0
    members = None
    try:
        job = k.CreateJobObjectW(None, None)
        must(job)
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000 | 0x200 | 0x100 | 0x8 | 0x20
        limits.basic.priority = 0x4000
        limits.basic.active = budget["active_processes"]
        limits.process_memory, limits.job_memory = budget["process_memory_bytes"], budget["job_memory_bytes"]
        must(k.SetInformationJobObject(job, 9, ct.byref(limits), ct.sizeof(limits)))
        applied = ExtendedLimits()
        must(k.QueryInformationJobObject(job, 9, ct.byref(applied), ct.sizeof(applied), None))
        require(applied.job_memory == budget["job_memory_bytes"] and
                applied.process_memory == budget["process_memory_bytes"] and
                applied.basic.active == budget["active_processes"], "OS job limit readback")

        def spool(fd, name, cap):
            received, stored = 0, 0
            try:
                with (evidence / (name + ".txt")).open("xb") as stream:
                    while True:
                        data = os.read(fd, 65536)
                        if not data:
                            break
                        received += len(data)
                        piece = data[:max(0, cap-stored)]
                        stream.write(piece)
                        stream.flush()
                        stored += len(piece)
                        if received > cap:
                            with lock:
                                if name + "_budget" not in faults:
                                    faults.append(name + "_budget")
                            stop.set()
            except BaseException as exc:
                with lock:
                    faults.append(name + "_log_io_" + type(exc).__name__)
                stop.set()
            finally:
                os.close(fd)
                output_counts[name] = {"received_bytes": received, "persisted_bytes": stored}

        stdin = open(os.devnull, "rb")
        handles.append(stdin)
        inherited = [msvcrt.get_osfhandle(stdin.fileno())]
        for name in ("stdout", "stderr"):
            readfd, writefd = os.pipe()
            fds.append(writefd)
            os.set_inheritable(writefd, True)
            inherited.append(msvcrt.get_osfhandle(writefd))
            thread = threading.Thread(target=spool, args=(readfd, name, budget[name+"_bytes"]), daemon=True)
            thread.start()
            threads.append(thread)
        os.set_handle_inheritable(inherited[0], True)
        si = StartupEx()
        si.si.cb, si.si.flags, si.si.show = ct.sizeof(si), 0x100 | 1, 0
        si.si.stdin, si.si.stdout, si.si.stderr = inherited
        size = ct.c_size_t()
        k.InitializeProcThreadAttributeList(None, 1, 0, ct.byref(size))
        attrs = ct.create_string_buffer(size.value)
        si.attributes = ct.cast(attrs, ct.c_void_p)
        must(k.InitializeProcThreadAttributeList(si.attributes, 1, 0, ct.byref(size)))
        try:
            handle_array = (wt.HANDLE*len(inherited))(*inherited)
            must(k.UpdateProcThreadAttribute(si.attributes, 0, 0x20002, handle_array,
                                            ct.sizeof(handle_array), None, None))
            environment = ct.create_unicode_buffer("\0".join(
                n+"="+v for n,v in sorted(env.items(), key=lambda x:x[0].upper())) + "\0\0")
            command = ct.create_unicode_buffer(subprocess.list2cmdline(argv))
            must(k.CreateProcessW(argv[0], command, None, None, True,
                                  0x08000000 | 0x4 | 0x400 | 0x4000 | 0x80000,
                                  environment, str(cwd), ct.byref(si), ct.byref(proc)))
        finally:
            k.DeleteProcThreadAttributeList(si.attributes)
            os.set_handle_inheritable(inherited[0], False)
            for fd in fds:
                os.close(fd)
            fds.clear()
        must(k.AssignProcessToJobObject(job, proc.process))
        assigned = True
        members = HeldMembers(proc.pid, proc.process)
        seen.add(proc.pid)
        launch_identity = process_identity(proc.pid, job)
        save_new(evidence / "started.json", {
            "utc": datetime.now(timezone.utc).isoformat(), "argv": argv, "cwd": str(cwd),
            "environment": env, "launcher": launch_identity, "budget": budget,
            "private_job": True, "assigned_before_resume": True,
            "inherited_handles": ["owned_stdin_null", "owned_stdout_pipe", "owned_stderr_pipe"],
            "hidden": True, "priority": "below_normal",
            "readback_limits": {"job_memory_bytes": applied.job_memory,
                                "process_memory_bytes": applied.process_memory,
                                "active_processes": applied.basic.active}})
        if k.ResumeThread(proc.thread) == 0xFFFFFFFF:
            raise ct.WinError(ct.get_last_error())
        resumed = True
        while True:
            pids = job_pids(job)
            seen.update(pids)
            members.observe(job, pids)
            if on_tick is not None:
                on_tick(job, pids)
            sizes = [measure_tree(p) for p in watch_roots]
            total, count = sum(x[0] for x in sizes), sum(x[1] for x in sizes)
            peak_tree = max(peak_tree, total)
            if total > budget["tree_bytes"] or count > budget["tree_entries"]:
                reason = "tree_budget"
            elif shutil.disk_usage(evidence).free < budget["free_reserve_bytes"]:
                reason = "free_reserve"
            elif stop.is_set():
                reason = faults[0]
            elif time.monotonic() - started > budget["seconds"]:
                reason = "timeout"
            for component in budget.get("components", []):
                component_bytes, component_entries = measure_tree(component["path"])
                if component_bytes > component["bytes"] or component_entries > component["entries"]:
                    reason = "component_budget"
            if reason:
                break
            if not pids:
                break
            time.sleep(.02)
        if reason:
            must(k.TerminateJobObject(job, 124 if reason == "timeout" else 125))
        # Job accounting/list can reach zero before a held worker handle
        # signals. Exit code alone (including a kill code) is not termination.
        terminated = members.wait_terminated(job)
        require(terminated, "owned job termination unconfirmed")
        require(k.WaitForSingleObject(proc.process, 1000) == 0, "launcher termination unconfirmed")
        code = wt.DWORD()
        must(k.GetExitCodeProcess(proc.process, ct.byref(code)))
        for thread in threads:
            thread.join(2)
        require(not any(t.is_alive() for t in threads), "pipe drain unresolved")
        if faults and reason is None:
            reason = faults[0]
        usage, accounting = ExtendedLimits(), Accounting()
        must(k.QueryInformationJobObject(job, 9, ct.byref(usage), ct.sizeof(usage), None))
        must(k.QueryInformationJobObject(job, 1, ct.byref(accounting), ct.sizeof(accounting), None))
        result = {"status": "success" if code.value == 0 and not reason else "failed",
                  "exit_code": code.value, "stop_reason": reason, "seconds": time.monotonic()-started,
                  "launcher_pid": proc.pid, "observed_job_pids": sorted(seen),
                  "all_processes_terminated": terminated, "active_processes_final": accounting.active,
                  "total_job_processes": accounting.total, "peak_job_memory_bytes": usage.peak_job,
                  "peak_tree_bytes_observed": peak_tree, "outputs": output_counts,
                  "faults": faults, **members.evidence()}
    except BaseException as exc:
        if proc.process:
            if assigned:
                must(k.TerminateJobObject(job, 125))
                if members is None:
                    members = HeldMembers(proc.pid, proc.process)
                terminated = members.wait_terminated(job)
            else:
                # A process created by this call and still suspended only.
                must(k.TerminateProcess(proc.process, 125))
                terminated = k.WaitForSingleObject(proc.process, 5000) == 0
        for fd in fds:
            os.close(fd)
        fds.clear()
        for thread in threads:
            thread.join(2)
        actual_exit = None
        if proc.process and terminated and k.WaitForSingleObject(proc.process, 1000) == 0:
            observed_exit = wt.DWORD()
            if k.GetExitCodeProcess(proc.process, ct.byref(observed_exit)):
                actual_exit = observed_exit.value
        result = {"status": "failed", "exit_code": actual_exit,
                  "stop_reason": "runner_exception_" + type(exc).__name__,
                  "diagnostic": str(exc)[:240],
                  "seconds": time.monotonic()-started,
                  "launcher_pid": proc.pid or None, "observed_job_pids": sorted(seen),
                  "all_processes_terminated": terminated if proc.process else True,
                  "resumed": resumed, "faults": faults,
                  **(members.evidence() if members else {})}
    finally:
        for f in handles:
            f.close()
        if members is not None:
            if terminated and not members.pending():
                members.close()
            else:
                _unconfirmed_trees.append(members)
        elif proc.process:
            k.CloseHandle(proc.process)
        for handle in (proc.thread, job):
            if handle:
                k.CloseHandle(handle)
    result["logs"] = {n: {"sha256": file_hash(evidence/(n+".txt")),
                         "bytes": (evidence/(n+".txt")).stat().st_size}
                      for n in ("stdout", "stderr") if (evidence/(n+".txt")).exists()}
    save_new(evidence / "terminal.json", result)
    return result

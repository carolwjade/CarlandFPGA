# Windows CPU AppContainer P1a prototype

This is an executable **CPU boundary fixture**, not G03 acceptance or the four
product processes. H01–H15 remain unchanged, under contract
`DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## What runs

`simulation.isolation.prototype` creates a unique task directory and a new
unpackaged AppContainer profile. It copies CPython 3.12 executable/DLL bytes and
pure standard-library modules to that task directory, with a per-file/ZIP-member
SHA256 manifest and an explicit `._pth`. The shared Python installation is only
read. The task stage grants its new package SID read/execute; the task truth
canary grants only SYSTEM and the current user. No broad All Application Packages
ACE is added. The helper rejects traversal, reparse paths and multi-link file
ACL targets. It is not a broker for untrusted callers or a defence against a
privileged same-user host changing the launcher's objects concurrently.

The trusted parent creates two one-way anonymous pipes: an observation read end
for the child and a bounded probe-report write end. Exactly those two handles
appear in `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`. A real canary handle is deliberately
marked inheritable but excluded; parent endpoint and canary flags are read back.
No parent process/token, truth file, device, shared texture or Job handle is in
the allowlist. The fixture's numeric parent PID denotes this short-lived Python
launcher, never Codex or another service.

The child starts suspended with zero capabilities, Win32k disabled and child
process creation restricted. The launcher assigns its own Job and independently
reads token SID/AppContainer status, capability count, mitigation flags, creation
time, Job membership and Job limits before resuming. Job limits are kill-on-close,
one active process, 256 MiB per process and all eight documented UI restrictions
(`0xff`). An explicit five-key environment contains SystemRoot, WINDIR, TEMP,
TMP and LOCALAPPDATA. No parent PATH, Python search path or credential variable
is copied. LOCALAPPDATA is a nonsecret profile-resolution input and grants no
filesystem permission. The child is detached and hidden.

The fixture runs a benign three-weight CPU dot product (output 23), receives a
known causal observation over its authorized pipe, and calls native Win32 APIs
through CPython's built-in `_winapi`. It attempts `CreateFile` on an existing,
parent-readable truth canary and `OpenProcess` on the test parent with each of
VM_OPERATION, VM_READ, VM_WRITE, DUP_HANDLE and CREATE_PROCESS. It finally calls
`ReadFile` on the excluded canary handle. The report protocol is length-bounded
and ordered. Missing files, missing libraries, absent targets or arbitrary
process crashes do not count as denied access.

## Running and evidence

From `competition/deepeye`, with the project's CPython 3.12 environment:

```powershell
python -B -X utf8 -m unittest discover -s tests/isolation -p test_policy.py -v
python -B -X utf8 -m simulation.isolation.prototype --evidence-parent <existing-task-evidence-directory>
```

Real OS tests are explicitly enabled by supplying a dedicated evidence parent:

```powershell
$env:DEEPEYE_ISOLATION_EVIDENCE_PARENT = '<existing-task-evidence-directory>'
python -B -X utf8 -m unittest discover -s tests/isolation -v
```

Every attempt retains `receipt.json`, a runtime manifest, original fixture stdout
and any failure traceback. The receipt contains the exact launcher source hashes,
new profile/SID, created objects, requested ACLs, independent kernel readback and
cleanup state. A normal test failure is never overwritten or relabelled as a
later passing run. No executable-profile reuse is supported. On timeout or
verification failure the launcher terminates only its own process handle and
waits for the actual terminal state. It deletes only its newly created profile,
after terminal confirmation; evidence and runtime copies are retained. A failed
cleanup keeps the verdict failed and records the remaining profile identity.

## Verified on A, 2026-10-15

Windows 11 build 26200, non-elevated caller, CPython 3.12.14. Ten policy/protocol
tests and two opt-in live OS tests passed. The second live test replaces the
fixture with a fixed sleeper: the 100 ms timeout fails closed, the launcher kills
its own child, waits for termination and deletes the profile.

| Evidence | Result |
| --- | --- |
| New AppContainer token and exact SID | Independently verified |
| Capabilities | 0 |
| Win32k / child-process restriction | Both enabled; queried before resume |
| Job limits | Queried `0x2108`, active count 1, 256 MiB, UI `0xff` |
| Benign model / authorized pipe | Both succeeded, CPU result 23 |
| Existing truth canary | `CreateFile` denied, Win32 error 5 |
| Five dangerous process access masks | All denied, Win32 error 5 |
| Excluded inheritable canary handle | Native invalid-handle termination `0xc0000008` |
| Cleanup | Child terminal; newly created profile deleted |

The target's actual StrictHandle policy is `3`. Accordingly the canary probe
raises `STATUS_INVALID_HANDLE` and terminates the child, rather than returning
Win32 error 6. This expected negative probe is accepted only when the trusted
StrictHandle readback has its exception bit, all positive and preceding negative
controls passed, the final ordered marker names exactly the excluded handle,
and the process exit status is exactly `0xc0000008`. A generic crash cannot pass.

Final successful receipt: `r-18f248d1f8f3/receipt.json`, SHA256
`ede0b3404d80f8be9021ed562fcf311868f200ee348381a8e6623a658f56b04d`.
Final expected timeout receipt: `r-ce5c047e0404/receipt.json`, SHA256
`c1de9197876156a2e35bfb99e97cb86fc5b55cd48a31b25fbfddad06c6c80da9`.
The A director retains these under its private
`.planning/deepeye-implementation-a/process-isolation-prototype-20261015/`.

## Compatibility failures retained

1. Omitting LOCALAPPDATA caused `CreateProcessW` error 203. Adding only that
   nonsecret path fixed creation; the complete parent environment was never used.
2. `CREATE_NO_WINDOW` caused early `0xc0000142` DLL initialization failure, including
   with a plain Python fixture. A diagnostic Job-UI-zero run still failed and was
   marked diagnostic-only. The final launcher uses `DETACHED_PROCESS` while
   retaining all token, mitigation and Job restrictions.
3. `_ctypes.pyd` could not initialize its native dependencies under Win32k
   lockdown. The final fixture uses built-in `_winapi` for the requested native
   boundary calls. This does not claim arbitrary Python extensions or AMD/GPU
   libraries are compatible, and Win32k was not disabled to make them load.

Independent review found a lexical `..` escape in the reusable ACL helper before
final delivery. It was fixed with an early traversal rejection and resolved-path
containment check, with a failing-then-passing regression test. The actual fixed
stage call sites had not exercised that escape.

An additional independent review found two further defects, repaired by the main
on 2026-10-16. A complete fixture frame could replace failed earlier measurements;
the parser now requires cumulative, type-preserving evidence, positive controls
before both completion paths, and rejects duplicate/nonfinite JSON fields.
An inheritable directory ACL could propagate through an existing child hardlink
to an alias outside the logical run root. The helper now refuses populated
directories before making the native ACL call. Root ACL preparation consequently
precedes its first receipt write; the receipt still precedes profile/process
creation. This assumes exclusive trusted preparation, not resistance to a
concurrent trusted user rewriting the directory.

The main's repaired check ran 13 policy/protocol tests and two real Windows
normal/timeout tests, all passing. A separate reviewer reran those15, then
identified exponent-overflow JSON numbers and nested-list bool/int aliases.
Those parser-only cases were repaired and independently rechecked:12 protocol
cases and14 unit tests passed on the final policy. OS runs bind the preceding
policy hash; they are not relabeled as fresh runs of the final parser. Original independent reproductions and the
intermediate empty-directory ordering failure remain preserved in the private
`process-isolation-main-review-20261016/` and `process-isolation-main-fix-20261016/`
directories. A separate review also observed an actual child-creation denial
(Win32 error 367), unknown RuntimeError rejection, and confirmed cleanup for all
seven of its own runs. These are bounded CPU P1a results, not G03 acceptance.

## Remaining work

LPAC, GDI desktop capture, DXGI, WGC, shared textures/sections, debugger IPC,
network denial probes, backend/model runtime compatibility, Job parent-crash
behaviour, four product processes, authority integration, FPGA hardware and full
G03 causal secrecy remain **not_run**. Current P1a proves only the explicit file,
process, inherited-handle, positive CPU/pipe and normal/timeout lifecycle cases.
It does not prove every possible Windows IPC path or screen API inaccessible.
No account, credential, driver, service, global setting, existing desktop ACL,
shared runtime ACL or hardware resource was changed.

## Official API references

- [AppContainer launch and profile environment](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)
- [Startup attributes, handle list and restrictions](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)
- [Creation flags, including DETACHED_PROCESS](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
- [Token information classes](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-token_information_class)
- [Process mitigation policies](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-process_mitigation_policy)
- [Job UI restrictions](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_ui_restrictions)
- [CPython Windows embedded distribution and path isolation](https://docs.python.org/3.12/using/windows.html#the-embeddable-package)

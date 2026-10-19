# Trusted-owner resource cleanup coordinator

`simulation/isolation/resource_cleanup.py` is a synchronous, injected cleanup
coordinator. That pure module has no OS backend, resource discovery, PID/path
removal, network, process creation or profile creation. The CPU fixture launcher
now supplies the separate owner registry and Windows backend described below;
this integration still needs independent review and fresh native verification.
The coordinator's lock rejects concurrent/reentrant calls on one coordinator;
it neither acquires an OS resource lease nor prevents a different program from
acting on those resources.

The fixed contract remains `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15,
requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
Offline coordinator tests do not establish G03, four-process isolation, runtime,
AI, game, hardware or board acceptance. Those remain **not_run**.

## Caller contract

The future trusted launcher supplies one `Provenance`, an exhaustive tuple of
`Resource` records, a `Backend`, and a callable report sink. There are no defaults.
Provenance freezes the task/version identifier, work identifier, owner identifier
and named SHA256 source bindings, including the future launcher/fixture manifests
and immutable requirements. Resource identifiers must be unique within this work;
owner identifiers must match. These are supplied owner assertions, not OS
attestation, authorization or verified source integrity.

`Resource.identity` is an exact already-owned opaque backend reference. The backend
must retain/canonicalize those references and verify its own handle/object identity
where needed. The coordinator never reconstructs a target from a guessed PID,
filename, directory or display label. Registering the same reference object twice
is rejected; two different wrappers pointing to the same OS object cannot be
detected here. The trusted launcher must guarantee exclusive ownership, no aliases
and a single coordinator for the plan. It must not construct another coordinator
as a way to retry an unknown effect.

Kinds are `process`, `handle`, `thread`, `socket` and `profile`. The plan must include
fixture resources as well as child resources. Each resource whose closure is a
prerequisite for profile removal names that profile in `profile_id`. Recovery
handles, job controls, worker threads or sockets that must remain available while
a process is unconfirmed name every required process in `recovery_for`. Omission
of resources/dependencies cannot be discovered without an OS backend: the future
launcher must establish plan completeness before acquisition/cleanup. Resources
needed only for recovery can close once those processes are confirmed terminal.

## Execution and results

Call `CleanupCoordinator(provenance, resources, backend, report_sink).cleanup(error)`
once, passing the original exception if any. The exception type/text is captured
before any sink/backend callback; even a broken exception `__str__` cannot abort
cleanup. A rejected reentry does not replace the outer primary failure. Plans and
returned records are frozen snapshots; opaque identity internals remain the
backend's responsibility.

1. Attempt termination of each owned process, then always call `wait_terminal`,
   including when termination failed or threw. Only the literal `True` from an
   actual held-identity terminal readback confirms termination. A terminate request
   acknowledgement is insufficient. Close the process reference only after that
   readback; otherwise retain it for recovery.
2. Attempt each independent handle/thread/socket close, even if another action or
   log failed. Retain resources whose `recovery_for` processes are unconfirmed.
   Backends must implement bounded thread shutdown/join and socket/handle closure
   within the `close` contract; a stop request alone is not confirmed closure.
3. Remove each profile only after **all** declared profile dependents are confirmed
   closed (including process references after terminal readback). Independent
   profiles can finish despite another profile's unresolved dependency.

Side-effect callbacks return exactly `Outcome.CONFIRMED`, `FAILED` or `UNKNOWN`.
`CONFIRMED` means the backend actually confirmed the effect, including closed
handles/joined threads and profile deletion/absence, rather than merely accepting
a request. `FAILED` means a definitive observed failure. Exceptions, malformed
returns and explicitly `UNKNOWN` results remain uncertain and retain ownership.
`wait_terminal` is a readback rather than an effect; false, unknown, malformed or
exceptional readback preserves process/recovery references. If termination threw
but subsequent terminal readback and close succeed, ownership may be resolved,
while the original termination error remains in the report and success stays false.

`CleanupResult` separates:

- `resources_complete`: every planned resource is confirmed closed/removed.
- `evidence_complete`: every report-sink invocation returned successfully.
- `success`: both above, no primary failure, and no cleanup errors.

`resources` retains each identity, closure and terminal flags, every action outcome
and any gate reason; `unresolved` lists resources whose ownership is still held.
`primary_error`, `cleanup_errors` and `audit_errors` preserve separate failures.
An attempted action is never treated as completed merely because it was called.

The sink receives immutable sequenced `AuditEvent` values before/after actions and
at blocked/start/finish boundaries. The final event carries a result snapshot;
the returned result additionally reflects failure of that final sink invocation.
The sink is responsible for serialization and its own flush/fsync/durability
contract. A return only acknowledges that contract; this module does not attest
the storage medium. Any sink exception, even after a partial write, marks evidence
incomplete. Later safe resource actions and later sink invocations still proceed.
Repeated writes of the failed event are not attempted. Sink events should retain
sequence IDs so an external auditor can recognize gaps or partial persistence.

## Recovery boundary

Every coordinator is single-attempt: a second call raises `CleanupRejected`, whether
the first completed, failed or had unknown effects. Overlapping/reentrant calls are
also rejected immediately. No completed, failed or unknown side effect is retried.
If an unexpected implementation/runtime interruption prevents a return, the
coordinator remains attempted and the trusted owner retains the original plan;
do not infer successful closure or release its handles from missing evidence.

Recovery requires separately authorized owner reconciliation on exact held
identities, independent readback of uncertain effects and an explicit new action
plan. Do not blindly replay close/delete/terminate, particularly if an OS handle
could have been closed and reused. A healthy new sink does not authorize replay.
There is no automatic cross-process recovery or retry API in this component.

Launcher integration must independently validate its complete resource
plan, bounded backend operations, real terminal/close/removal readback, ownership
retention on every acquisition/error path and durable evidence/recovery under real
OS failures. This offline implementation does not replace those validations.

Run only its pure tests from `competition/deepeye`:

```powershell
python -B -X utf8 -m unittest discover -s tests/isolation -p test_resource_cleanup.py -v
```

The fake backend exercises action order/count, exact references, each sink/action
boundary failure, terminal/nonterminal readback, unknown closes/removal, retained
primary and cleanup/audit errors, profile gates, independent cleanup, duplicate
ownership and reentry/repeat rejection. It creates no native fixtures or profiles.

## CPU fixture integration candidate, 2026-10-19

`owned_resources.py` records every successful acquisition before reporting.
`windows_cleanup.py` binds those exact references to checked Windows releases;
`prototype.py` now uses this path. `resource_cleanup.py` remains unchanged.
This backend covers only the CPU fixture's kernel handles, process/primary-thread
handles, profile/SID and helper allocations. It is not a general socket, Python
thread, GPU, UI or four-product-process backend.

`OwnedResources` assigns a fresh reference instance to each acquisition. An early
release result is cached before any later report. Unknown/failed releases remain
owned and are never issued again by final cleanup. A numeric value may be reused
normally only after confirmed prior release. If a new successful acquisition
collides with an older unknown release, both records remain ambiguous and the
acquisition raises; no automatic action uses that ambiguous value. A live duplicate
without a preceding release is rejected as an invalid ownership assertion.

The native helpers record a job before limit setup, and both CreateProcess handles
before returning or releasing the attribute list. Profile and SID are recorded
before SID conversion, path lookup or persistence. Attribute backing buffers stay
strongly referenced when release is unresolved; SID storage is also retained while
an attribute list that may reference it is unresolved. The following bounded
helper release contracts are recorded in the same owner ledger:

| Allocation | Release acknowledgement |
| --- | --- |
| Tokens, pipes, canary, Job, process and primary-thread handles | `CloseHandle` returns nonzero; no retry after an unknown result |
| Profile SID | `FreeSid` returns NULL |
| Converted SID string / ACL security descriptor | `LocalFree` returns NULL |
| Profile-path string | `CoTaskMemFree` returns normally; its API has no status result |
| Attribute-list storage | `DeleteProcThreadAttributeList` returns normally; backing Python buffers remain held if it throws |
| Other ctypes/Python temporary buffers and scoped file objects | Python/helper scope contract; no independent OS allocation inventory claim |

The void-return acknowledgements are bounded API contracts, not externally
attested heap reclamation. Standalone legacy SID/token/ACL inspection helpers
without an owner retain only their local checked-release contract; the actual
launcher always supplies its owner. Allocation failure in Python's own in-memory
registration, abrupt process death, and mutation by another trusted owner remain
outside the synchronous fault-injection guarantee.

Before requesting termination, the backend waits on the original held handle
with zero timeout. A terminal process receives no terminate request. A separate
bounded wait confirms terminal state before closing that handle. Unknown terminal
state retains process, primary thread and Job controls. Exit-code readback errors
remain distinct owner errors. Profile removal additionally requires a known path,
all dependent releases confirmed, successful HRESULT and an explicit absence
readback. Access/stat errors or unknown path never mean absence.

`run(...)` still returns `(receipt_path, evidence)`. `evidence` is a `RunEvidence`
dict subclass: keep `evidence.ownership` alive if unresolved. It holds the exact
live references, backing buffers and one-attempt state for separately authorized
reconciliation. JSON and ordinary `dict(evidence)` do not retain that context.
The CLI is not a live recovery interface: exiting it does not prove terminal
cleanup or authorize PID-based recovery. Use the library in a trusted owner when
investigating potentially unresolved operations; no automatic recovery is added.

Receipt writes serialize before writing, flush/fsync a new owned `.pending` file,
then replace the receipt. Failed/partial attempts are preserved. This does not
claim crash-proof directory-entry persistence. Primary failure, helper release
errors, coordinator cleanup errors, audit errors and final save errors remain
separate. All logging errors are contained while safe cleanup continues. Output
capture uses one Peek plus a maximum 8192-byte read, never waiting for pipe EOF.

The returned verdict requires confirmed resource completion, acknowledged evidence
writes and empty error/unresolved lists. A final write failure changes the in-memory
verdict to failed. An earlier disk snapshot may be stale or provisional, including
when a sink writes successfully then raises; it is never relabeled as the final
returned result. Keep failed evidence and use sequence IDs/readback for audit.

Three opt-in native tests are prepared in `test_windows_live.py`: normal, timeout,
and persistent evidence failure after process creation. They have not run for
this integration candidate. Main must first independently review exact frozen
bytes, then use a new dedicated evidence directory for each validation stage and
preserve all attempts. These cases still do not establish G03 or product isolation.

API contracts: [TerminateProcess and asynchronous termination](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess),
[CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle),
[DeleteAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile),
[FreeSid](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-freesid).

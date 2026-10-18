# Trusted-owner resource cleanup coordinator

`simulation/isolation/resource_cleanup.py` is a synchronous, injected cleanup
coordinator. It has no OS backend, resource discovery, PID/path removal, launcher
integration, network, process creation or profile creation. It is not activated by
existing runners. Its lock rejects concurrent/reentrant calls on one coordinator;
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

Future launcher integration must independently validate its complete resource
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

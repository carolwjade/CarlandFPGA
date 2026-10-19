# Retained native harness preparation: independent review

Work A-actor-native-harness-independent-review-20261019-v1; original job
child-286812f797964cf7985276d49f701dc1; reviewer /root/r03_review_20261018.
Recommendation to main: repair ANH-R1 and independently recheck its frozen
bytes before any actual native attempt. This review does not grant execution.

## ANH-R1 — nonzero crash after READY is reported as successful natural exit

Reviewed `tests/isolation/test_actor_windows_live.py:231-232` accepts the normal
case whenever the previously accumulated frame is exactly READY and the
original process reference is terminal_confirmed. Final checks at253-256 add
resource completion/profile release/CLOSED but do not check an original process
exit code or cleanup backend termination provenance. `_snapshot` also omits
backend exit_codes/terminated. Terminal observation establishes that a process
ended, not that the cooperative fixture returned normally.

Independent fake witness calls the actual frozen `run_case` control flow:

1. Completely replaced fake Registry returns its strongly retained fake owner.
   First public poll succeeds and the reader emits exactly READY.
2. Next poll records original terminal and raises the same lifecycle terminal
   ValueError. The fake cleanup backend has original-process exit code17 and
   terminated=False, representing a crash after READY rather than owner kill.
3. Original-resource/profile cleanup completes and owner state is CLOSED.
4. Actual harness returns passed=True, unresolved=False. Its actual x-written
   fixture-memory-result.json also contains passed=true. The serialized result
   contains no exit17 observation because the snapshot never records it.

`review_cases.Cases.test_ready_then_nonzero_crash_is_not_successful_natural_exit`
asserts passed must be false and is RED. The final independent2 run is9 methods,
8pass/1failure/0skip, exit1. Both initial and final raw logs are preserved.
`independent-witnesses.json` records backend17, passed=true, exact persisted
result content and retained original roots; independent1-witnesses.json keeps
the initial version. No actual process, PID, handle, registry, native module,
runtime stage or OS security operation was created.

The fake is an explicit controller seam, not proof of a Windows crash. Its
terminal/cleanup semantics are consistent with the original frozen sources:
actor_lifetime._sample sets terminal_confirmed only on strict integer0 and
raises; the original actor guard revokes while leaving cleanup to finally;
WindowsCleanupBackend.wait_terminal stores the process resource_id's exit
code, and successful resource release does not imply exit code0. A real child
can emit READY and then fail before/while sleeping; the harness currently
cannot distinguish that from its intended natural return. This is an evidence
classification defect, not an observed product motion or security escape.

Minimal next-owner correction: capture the exact original process resource_id
before retirement; after cleanup require its recorded exit code to be a strict
built-in integer0 for this normal fixture, with backend.terminated exactly
False. Persist both observations and their source meaning in the final snapshot.
Missing, non-int, nonzero or owner-terminated outcomes must remain failed even
when resources/profile release succeeded. Preserve original primary exceptions,
raw observations, no-overwrite artifacts and unresolved recovery roots; do not
rewrite actor cleanup or weaken expected expiry/persistence semantics to make
the normal case pass. This review changes no candidate file.

The missing backend check is recommended as explicit evidence, but is not
reported as a second independently demonstrated ordinary-path bug. In the
actual guard, reader failure does not itself run cleanup. Our separate reader
timeout witness correctly fails before finally kills the process. We do not
invent an early-cleanup callback path to claim another false pass.

## Passing checks and bounded observations

The author's full10 offline tests passed and3 native methods genuinely skipped
under ordinary noninteractive CPython; exit0,13 discovered. No native opt-in
was enabled for that run, and no Win32 module was imported. Fixture fake
_winapi tests are in-memory protocol checks, not a native run.

Eight other independent methods passed:

* Zero-exit natural baseline and exact unbound readiness=lifetime expiry use
  their expected case semantics. The expiry is not a bound actor lifetime test.
* Reader timeout after READY stays failed, retains the same original primary
  exception, and final cleanup records forced termination in the fake backend.
* Expected post-acquisition persistence injection preserves exact exception
  identity, original owner/registry and QUARANTINED evidence errors even when
  resource release completes. passed here means the expected negative fixture
  matched, never successful durable evidence or product readiness.
* Failure writing the case result changes the returned in-memory passed to
  false and retains the original context plus persistence error event.
* Incomplete cleanup preserves unresolved original owner/resources; another
  case refuses before file access or registry construction.
* Before-return and after-owner-retained acquisition errors preserve the
  original registry/context and primary error; a missing owner stays unresolved.
* An existing execution-claimed marker raises FileExistsError before even fake
  Registry construction and before a new NativeAttempt is appended.
* The actual private reader checks original output native identity, process
  continuity, retired epoch and elapsed equality boundary; failures after read
  are treated as consumed bytes, not retried. This helper test substitutes the
  decorator/sample/reference seams; production guard/thread/registry checks
  were inspected against the original frozen source rather than claimed tested
  with a real owner or moving repair.

All platform/interactive forcing was inside a context where ActorPolicy,
ActorRegistry and the entire imported actor_owner module were replaced before
run_case could reach them. Import guards explicitly prohibited win32/prototype.
No actual ActorRegistry constructor or prepare_stage/stage_runtime ran.
Temporary directories under this review contain only fake controller records
or offline validator sample files, never a runtime copy or runnable stage.

## Gate, lifetime and evidence boundaries

Static read and author offline tests confirm exact main/contract/case/attempt
and complete source/stage hash validation, source substitution rejection,
case aliases/traversal/extra stage-file rejection, ordinary single-link/reparse
checks, and x-created execution claims. The filesystem link/reparse logic was
inspected, not tested through real link/ACL operations. The fresh UUID is
enforced by prepare_stage; the trusted main must use that path and review
the false/null proposal before writing an exact separate allow. A supplied
allow is main provenance, not a cryptographic signature or adversarial
same-user TOCTOU defense.

The one-shot claim is retired before native imports. `_ATTEMPTS` retains the
context before registry acquisition and refuses a later unresolved campaign.
Errors before the owned acquisition can conservatively leave a retained
unresolved context; they are not silently retried. Snapshot/report failure can
raise rather than return, but the recovery roots already remain in _ATTEMPTS.
This depends on the instructed retained interpreter remaining alive; it does
not prove survival after interpreter exit/hang.

Reader protocol accepts at most256 bytes total, while available_output's
existing helper can consume8192 before rejection. The exact frame is fixture
READY, not AI authentication or BOOT readiness. EXIT WriteFile is disabled,
with synchronous no-cancellation limitation accurately documented. Six-second
parent polling and post-call clock checks do not cancel a stuck synchronous
native helper. Successful sample Wait258 and terminal Wait0 are explicitly
source-implied, not raw independently captured returns.

Case-result writes are exclusive, and a failure sets in-memory passed=false.
Actor receipt hashes are labelled observed snapshots which may predate injected
failure; no stale receipt is overwritten as final success. The real unresolved
handle/profile lifecycle and actual persistence behavior remain native not_run.
The review's fake result-write and injection observations do not change that.

## Exact provenance and compatibility

Author source-manifest6474920de9d6ddd99eab6a7aa9ff66010fbcf40ba05a3b29954c4ebe3afdf9fa,
report2802dfb59ad44f092f8dfae2c2bd353668d2307fa72c0f1720098d7bea0cca21,
receipte49045602ccdb76c61c72316d3ab2f40ade16f91528a2c393a599b6e81163628
and actual original completed/terminal author job were read. All three candidate
live/frozen/raw Git-object/Git-clean bytes match, stable before/after tests:

|Candidate|SHA256|
|---|---|
|actor_fixture.py|47946ba137eb61aa9d4d2357487c28210314bd4642ad7b1b4d781d052abab3b6|
|test_actor_windows_live.py|cbfc8afe2b8a727bafbbaa30f1dd3e224834fe9e81a45e1f3e19b5e994b74d27|
|actor_native_probe.md|2a5393335e166175505293b233dc8b3b842a99c0ae709882caa6e00317bf4c96|

`source-provenance.json` SHA256
132f3d773fe2e6fd7916e3d508affc41313ce3c7cd9857a260400778d7a537b3
pins candidate copies plus original actor_owner/lifetime frozen archive and
Git3f702903 windows_cleanup/owned_resources/resource_cleanup/win32 references.
Original ActorPolicy has14 fields matching the harness's14 positional values.
Private helper signatures/field uses match that original source. Concurrent
actor repair was not imported or accepted; no claim about actual native ABI
compatibility with its moving bytes follows. Future execution needs its final
independent acceptance and a fresh exact allow/stage after this harness repair.

Reproduce from ROOT with `.local/venv/Scripts/python.exe -B -X utf8
.planning/deepeye-resume-20261018/actor-native-review/run.py <new-label>` for
the independent9 methods; new labels preserve existing logs. Offline command
argv/cwd/process-only PYTHONPATH/TEMP and exact before/after hashes are in
offline.command.json; independent1/2 likewise. Only this review directory was
written; product, prior evidence, index/commits/providers/credentials/services
and board remained untouched.

H01–H15 remain fixed under DEEPEYE-HUMAN-LOCK-20261014/revision1 with canonical
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 recomputed.
All29 formal cards, native execution, actual AI/BOOT/provider, complete H12,
Run/game/hardware remain not_run. Main decides repair scope and any later
actual native authorization after independent closure.

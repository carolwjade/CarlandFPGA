# Independent reconciliation of three actual Windows CPU actor fixtures

Work A-actor-native-evidence-review-20261019-v1; original job
child-000d3740dbee4f6cb8422c1cc22bf527; reviewer /root/r03_review_20261018.
No new blocking inconsistency in the reviewed lifecycle evidence after the
separately confirmed handoff-pin correction below. This conclusion is bounded
to three CPU fixtures and their original retained-owner records. Main owns
acceptance; it is not AI/BOOT/PC_DIRECT product or formal-card acceptance.

## Actual cases and outcomes

|Case / attempt|Original process reference native value|Recorded terminal/exit|Retained owner / fixture meaning|
|---|---:|---|---|
|natural / afabf8e730984984ad6e3e3e54cd62eb|868|int0, owner_terminated=False|CLOSED; normal_exit_success/evidence_success true|
|unbound expiry / fe2055ceae4c4f9c808c645af05c8de5|920|int57005 (0xDEAD), owner_terminated=True|CLOSED; expected negative matched, both success fields false|
|persistence injection / 9db110fa0af943e1ac31740bad9d3e6a|980|int57005 (0xDEAD), owner_terminated=True|QUARANTINED; expected negative matched, both success fields false|

All three have their own registry retaining exactly its original actor and
scoped process:15 resource identity. Same resource_id across owners does not
mean the same process; native handle integers also cannot be used for later
adoption. Original object/id/native continuity, terminal_confirmed and original
backend exit provenance agree across fixture-memory-result, main-return and
retained-main-readback. All18 resources per case are attempted/confirmed and
nonambiguous; unresolved lists are empty. Thus54 recorded owned references
are resolved at this observed checkpoint. No new native query or cleanup was
used to reach that conclusion.

The natural and expiry raw stdout files are exactly22 bytes
`DEEPEYE-ACTOR/1 READY\n`; their reported hex matches. Natural case elapsed
2.750s and202 parent events include201 successful public polls plus the final
terminal rejection. Expiry elapsed2.094s and157 events include156 successful
public polls plus the exact fixed actor/readiness/sample deadline rejection.
These are one-case observations, not latency guarantees or raw per-call Wait
captures. The owner-primary ValueErrors remain in both snapshots and receipts;
the outer harness context-primary is null because those rejections were the
expected case boundary.

Persistence injection elapsed.375s, no public polling/events, empty stdout and
no READY. The injected `_persist` error occurs after original process ownership
registration during launch, before normal return/readiness. Its exact original
OSError is retained by both context and actor, with44 matching evidence errors,
evidence_complete=false and QUARANTINED state. Empty stdout is the expected
pre-READY failure observation, not a missing successful protocol run.

The main interpreter's execution-tool results show the three explicit case
commands returned to the retained prompt in session48521; main-return records
grow retained_contexts1/2/3. This is case return completion. No outer interpreter
exit0 is claimed: the interpreter intentionally remains retained. I sent no
input, signal or other operation to it.

## Cleanup, profile and persistence evidence are separate

Original WindowsCleanupBackend stores exit_codes under the owned resource_id
and its successful owner-TerminateProcess flag. The source's cleanup order is
terminate/check -> held-handle terminal readback and GetExitCodeProcess ->
process close -> dependent/reference release -> profile removal. Reference
terminal flags/exit maps plus complete outcomes at the exact pinned source
support that order. Raw Wait0/258 calls were not independently intercepted or
timestamp-captured; successful public poll's258 and terminal flag's0 remain
explicit source-derived semantics. None was invented from PID discovery.

The original backend profile_delete_hresult is0 and profile_absence isTrue
for all three. Main's later retained-object/filesystem readback also reports
each original profile path absent, resources confirmed and owner_errors empty.
I reconciled those original observations without performing a fresh profile,
process or OS security probe. Readback identifies retained context/actor
objects with Python identity checks and confirms the snapshot stayed unchanged.

The natural and expiry actor receipts are CLOSED,18 resources and
resources_complete/evidence_complete true, but **cleanup.success=false**.
That raw field is preserved: generic CleanupCoordinator.success also requires
no primary exception, whereas these cases intentionally retire on terminal or
deadline ValueError. It is not evidence that those resource releases failed,
and it must not be rewritten as universal cleanup success. The natural fixture
classification additionally has the original int0/False termination proof;
expiry remains explicitly expected-negative rather than normal/evidence success.

The persistence actor's disk receipt is deliberately stale: ALLOCATING, only3
resources, cleanup=null, primary_error=null, no recorded evidence errors. It
predates the injected write failure and cannot prove the final18-reference
cleanup or QUARANTINED state. Its recorded SHA256 matches unchanged on disk and
is labelled an observed snapshot, never replaced. Final in-memory cleanup,
exact primary identity and44 errors are instead corroborated by exclusive
fixture-memory-result, main-return, the retained-owner readback and the known
injection scope. That preserved failure is not a successful durable actor
receipt. No actor receipt or older report was modified in this review.

## Authorization, source and runtime identity

Per-case false/null allow proposals, main stage audits, enabled allow and
main-approval records agree on the exact fresh UUID attempt and one case.
Main approval uses sole director01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2,
accepted independent rereview receipt4d8cde10a943948d82b70daf0a67b3f9eec793315e91f09b1163d182c7a8400d,
and candidate manifest415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3.
Allow/approval/audit/claim hashes match. Each approval precedes its invocation;
each subsequent approval follows the preceding return. Three exclusive claim
files, invocation files, return files and execute_case's no-retry checks agree
with one invocation per named attempt. This does not claim an independently
complete OS process inventory beyond the retained campaign records.

All38 historical signed source hashes match invocation/return/allow and current
file bytes, including accepted actor7/helpers and the repaired harness. Sources
are compared by exact bytes, not a potentially moving HEAD or newly added
unrelated module. Readback's imported project-module paths/hashes resolve to
the same PRODUCT files; no actor_composition import was recorded.

Each source-stage has exactly10 approved files, all matching hashes. The actor's
actual copied runtime also has exactly those10 files with identical approved
bytes. Each archive's CRC and all592 member hashes/sizes match its original
standard-library source manifest; member bytes are identical across cases.
Whole zip hashes may differ between prepared archives, and each is compared
to its own approved archive rather than another case's container bytes.
Original vendor/runtime source files and generated pth/zip hashes are included
in the inspected-file manifest. The final cooperative fixture hash is
47946ba137eb61aa9d4d2357487c28210314bd4642ad7b1b4d781d052abab3b6;
the legacy fixture in origin-stage-manifest remains explicitly superseded
historical provenance. Receipt provenance binds that case's10 staged hashes
and fixed requirements to its own instance/owner identity.

Main's initial stage audit exit1 is retained. It expected LF in python312._pth,
while the pinned Windows stage_runtime wrote CRLF. The archived initial audit,
failure record and corrected audit are preserved. All actual approved stages
and copied pth bytes are `python312.zip\r\nDLLs\r\n.\r\n`; no stage/runtime
bytes were altered to hide the initial audit failure. This was an offline
audit-expectation correction, not a native case retry.

## Hash handoff correction and reviewer audit history

Assignment initially supplied a65-character readback pin containing one extra5.
The first reviewer check failed rather than accepting it. Main independently
read Get-FileHash and saved actor-native-evidence-review-pin-correction.json;
the original assignment and old failed check remain unchanged. Correct64-digit
SHA256 of the38871-byte retained-main-readback.json is
a360b90f7a89f11da67e63b4050fef0cf10318a83a34af32d50546281816030d.
Its readback UTC remains2026-10-19T12:21:36.577938+00:00. No native operation was
repeated for the correction. Both main and reviewer hash observations agree.

The review's audit1 then stopped on an overly literal `>>> ` prompt matcher:
persistence tool output ends in `>>>` plus ANSI cursor movement rather than a
plain space. The raw terminal artifact was preserved; the file-only matcher
was corrected to accept the actual prompt marker while structured records
continued to be compared exactly. audit2 and audit-final exit0. These are
reviewer parser failures, not case failures or relaxed native acceptance gates.

Final reconciliation.json records all cases and exact semantics. The
inspected-manifest.json contains758 unique inspected original artifact/source/
stage/runtime/vendor-file paths with size and SHA256. A final read-only
rehash verifies this complete set stayed unchanged. Audit command argv/cwd,
raw stdout/stderr and initial failures are saved in this review directory.

## Boundaries

This review parsed, hashed and decompressed existing files only. It imported
no product, native, Win32 or interactive harness module; constructed no stage,
registry/process/profile; reopened no process; replayed no cleanup; and made
no service/board/network/Git/product Run change. Original session48521 remains
untouched. No runtime test or regression was redundantly rerun.

These observations support three actual Windows CPU fixture lifecycle paths,
including expected expiry and failed evidence persistence. They do not prove
real project AI/readiness/BOOT authentication, ai_lease routing, causal IPC,
full PC_DIRECT/HIL execution, sample-to-CAS survival, owner-hang recovery or
game/board acceptance. Synchronous helper cancellation and EXIT-write remain
not_run as previously documented. H01–H15 under
DEEPEYE-HUMAN-LOCK-20261014/revision1 and canonical requirements
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 were verified
unchanged. All29 formal cards remain not_run. Main decides the next accepted
integration step from this bounded evidence.

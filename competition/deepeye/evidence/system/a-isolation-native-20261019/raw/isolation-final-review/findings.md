# Final independent isolation pair repair and native harness review

**No remaining blocking source finding within the reviewed bounded scope.**
IL-R1 is repaired on the exact new candidate; the independently found harness
IL-H1 is also repaired. The named three fresh native fixtures are suitable for
main's separately gated execution against these reviewed sources. This report
does not execute or accept those fixtures, OS isolation, G03 or the product.

Task DEEPEYE-IMPLEMENTATION-20261014/v1; work
A-isolation-final-review-20261019-v1; original job
`child-5877d2f4017b47a6ba9738620be73eb3`; independent reviewer
`/root/r03_review_20261018`. Original-endpoint validation returned
execution_allowed=true before both prepared and final review phases. Sole A
Desktop main remains generation2. H01–H15 requirements canonical hash was
recomputed as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## Candidate and ownership

Actual author completion was read: child-a2db60ebe47f4c1c9bd1be8cd4c44fc6,
completed/terminal=true/duplicate=false. Report SHA256
`86644a7451273a1d0acc8523404e37268247cb061688a323bb4cfb9627e4a180` and manifest
SHA256 `4752b00aa62688041a493e28c0b8bb95bff015dc8f9d11d648c255f7e3d02567`
were independently verified. All12 live product files equal that manifest and
the author's frozen copies; this review saved its own `frozen/` copies.

The independently generated `independent-candidate.diff` confirms precisely four
changes from the original reviewed candidate: `owned_resources.py`, `win32.py`,
`test_owned_resources.py`, `test_windows_cleanup.py`. Other eight candidate
files are byte-identical. The accepted coordinator remains
`4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f`.
All236 inherited dependencies and123 historical author/review evidence files
match the repair baseline. `dependency-stability.json` records each comparison.
No HEAD-based assumption or reset was used; concurrent motion work is outside
this candidate and was not treated as isolation drift.

## IL-R1 resolution

The first original ambiguity exception no longer prevents recording the second
successful acquisition. `_record_handle` returns a retained reference plus its
deferred ambiguity; `_record_pair` attempts both registrations before surfacing
the first original error. `own_handle` preserves its prior single-item contract.
Actual CreatePipe uses pair registration; actual CreateProcess delegates its
process/thread pair to it. CreateProfile's profile/SID pair is also retained and
bound before surfacing ambiguity. The profile pointer and SID dependency are
set before the error is raised.

The unchanged original two behavioral witnesses were copied byte-for-byte,
run against this candidate and both pass. Original RED is preserved in the
prior review and repair records. The new narrow independent matrix uses actual
`win32.pipe`, `win32.create_suspended` and `win32.create_profile`, replacing only
their native functions with fakes. For each helper, first-member, second-member
and both-member numeric collisions retain every returned member.

The independent tracker observes the real `_record_handle` results and proves
the surfaced exception is the **same first original exception object**. The
CreateProcess matrix also forces a secondary DeleteAttributes error and confirms
that it is separately retained without replacing the primary ambiguity. During
cleanup, ambiguous native values are not closed again. Safe pipe companions
close once. An unambiguous primary thread remains a recovery control while its
process identity/terminal state is ambiguous. When only the thread is ambiguous,
the independently confirmed process may close once without retrying the thread.
Profile/SID dependencies prevent deleting a profile with an unresolved SID;
an unambiguous SID may be freed once without replaying an ambiguous profile.

The guarantee remains bounded to valid trusted-owner synchronous registration.
It does not resolve OS numeric identity ambiguity, recover after owner-process
death, remove Python memory-exhaustion limitations or authorize automatic replay.
No broader fault campaign was performed and no additional blocker was found.

## Harness IL-H1 resolution and prepared native scope

Initial reviewed harness `d3990462...` retained owner references before first
acquisition and preserved CloseHandle last-error, but `hold_unresolved` could
escape on diagnostic output or stdin OSError. Two independent fake witnesses
failed; original RED is retained in `harness-check.*.log` and the old source copy.

Main's narrow repaired harness SHA256 is
`2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613`.
Both unchanged assertion methods now independently pass, exit0, with the full
test class AST unchanged. Diagnostic/read errors enter a retaining wait instead
of allowing interpreter exit; traceback-output failure is contained before
holding. Five other fake observer checks pass on unchanged observer/wrapper AST:
native return/error delegation, original held-handle terminal readback, first
acquisition exception ownership, original process-pair return and ownership/memory
retention on observation-save exception. Strong LIVE_OWNERS references survive
even if the launcher fails to return RunEvidence. The fake sentinel bounds tests;
it is never installed in the main harness.

The prepared normal, 100ms-timeout and persistent-save-failure fixtures are
unchanged in the repaired 12-file candidate. Each uses a fresh exclusive run and
random profile identity; the main harness requires a fresh exclusive attempt
directory, checks the pinned manifest before and after, delegates to real native
operations when main runs it, and independently reads the still-held process
handle before close. It never reopens a PID. Returned-memory evidence is separate
from an earlier stale receipt, especially for the intentional persistence failure.
The main observer stats only the newly reported profile path and retains exact
errors. Unknown ownership stops the campaign and retains the original live owner;
its status channel performs no native recovery or automatic close retry.

No native execution gate exists at review finalization. Main must create its own
accepted-review gate bound to the exact reviewed manifest and retain unchanged
accepted dependencies/harness for execution. The recorded coordinator/fixture
and other dependency hashes identify the source scope alongside the12 candidate
files. This is suitability for those three named CPU fixtures only, not an
execution result or authorization to expand to other profiles/processes/services.

## Actual independent verification

All Python commands use ROOT `.local/venv/Scripts/python.exe -B -X utf8`.
Per-run `.command.json` files retain argv/cwd/exits, owned TEMP/TMP and an unset
native opt-in. Raw stdout/stderr bytes are saved separately. The copied offline
driver stubs unrelated token setup for policy precondition cases; these fail
before native ACL operations. Real native tests are skipped.

| Run | Actual outcome |
|---|---|
| Offline suite once against final candidate | 75 discovered /72 passed /3 native skipped; exit0 |
| Original unchanged pair witnesses | 2 passed; exit0 |
| Original unchanged timeout/audit/profile/output boundaries | 3 passed; exit0 |
| New independent actual-helper pair matrices | 3 methods, nine first/second/both subcases passed; exit0 |
| Prepared observer tests | 5 passed; exit0 |
| Original harness I/O-retention witnesses | 2 failures before repair, 2 passes after; exits1/0 |

`product-before.json`, `product-after.json`, `frozen/` and the original manifest
bind the tested bytes. Source, harness and staged witness hashes remained stable
after all checks. The only preparation scaffold failure was a misspelled Python
encoding name (`utf8-sig`); it was corrected to `utf-8-sig` without product or
test-gate changes. The final preparation integrity script then passed.

## Result and limits

IL-R1 and IL-H1 are closed by independent source/fake evidence in this exact
bounded review. Main retains the native execution and acceptance decision.
Three real fixtures, actual cleanup/ACL behavior, four-process isolation, live
AI/runtime/game, G03, both control paths, hardware/board and all formal cards
remain **not_run**. No native result is inferred from unit/fake PASS.

Writes were confined to `isolation-final-review/`. No product/main harness/old
report edit, opt-in, gate, real profile/process/ACL operation, service, hardware,
credential/provider change, external transport, Git mutation or new agent was
performed. Source is read-only and review evidence is now finalized for original
native_complete.

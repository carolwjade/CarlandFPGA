# Native cleanup and trusted motion checkpoint — 2026-10-19

The A main accepts this implementation increment: the CPU launcher retains
ownership across acquisition/reporting failures, and the trusted motion executor
publishes a complete checked step through the existing final runtime fence.
Unknown history-materialization failures stop subsequent motion while preserving
the already committed pose and history.

This checkpoint includes three actual Windows CPU fixture cases and independent
review of their saved evidence. It does not activate a product Run or establish
four-process isolation, meaningful live AI, either complete H12 control chain,
game, hardware, board or full R03 acceptance. All 29 formal taskbook cards remain
`not_run`. `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 and requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` are unchanged.

## Exact reviewed implementation

| Increment | Source manifest SHA256 | Review |
|---|---|---|
| Twelve launcher/backend/test/documentation files | `21c42710a33a2c1be2355129cfb113e5f23e261571dd8d8a35a2845f38fe7e63` | Source/paired-acquisition review, then independent byte bridge to Git LF bytes |
| Four motion executor/helper/test/documentation files | `1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533` | Independent full suite, original adversarial cases and repaired continuation cases |

The source snapshots and each original failure, repair and review are retained
in [isolation evidence](../evidence/system/a-isolation-native-20261019/manifest.json)
and [motion evidence](../evidence/system/a-trusted-motion-20261019/manifest.json).
These manifests identify raw byte hashes, not a claim that every archived
intermediate candidate passed. Runtime executables, private lease/control data
and truth-canary contents are excluded from the publication; their original
local execution artifacts are retained.

The isolated launcher records the entire successful CreatePipe, CreateProcess
and profile/SID pair even if registration of the first member raises. Ambiguous
ownership is retained for reconciliation instead of issuing an unsafe repeated
close. The same live owner receives cleanup and evidence failures; a failed
receipt write cannot erase the original exception or make a stale receipt final.
The accepted pure cleanup coordinator is unchanged at SHA256
`4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f`.

The launcher review ran 75 discovered tests: 72 passed and three opt-in native
cases skipped. Independent original pair counterexamples, boundary checks and
nine pair-matrix subcases passed after repair. A separate harness defect that
could discard unresolved ownership on console failure was reproduced and fixed
before native execution. Its two original failure cases then passed. The one
subsequent source-byte change was exactly 307 CRLF-to-LF terminators in
`prototype.py`; AST equality, all other eleven files and Git clean bytes were
independently checked. No behavior was changed for publication.

## Actual Windows execution

The main ran the reviewed harness once as `attempt-01` using Python 3.12.14 and
the source manifest above. Official execution session 87134 finished with exit
code 0. All three named tests ran once without skipping. The independent
[native evidence review](../evidence/system/a-isolation-native-20261019/raw/isolation-native-evidence-review/findings.md)
reconciles exact source/runtime inputs, original logs and saved observations;
it did not rerun the fixtures or query a new process handle.

| Case | Product result | Process and resource evidence |
|---|---|---|
| Normal CPU/pipe and denied-access boundary fixture | Pass within `CPU_P1a_only` | Original held process handle signalled before close; expected fatal excluded-handle status `0xC0000008`; 24 resources confirmed; fresh profile absent |
| 100 ms timeout | Failed with the original `TimeoutError`, as expected | Original process terminated with `0xDEAD`, observed signalled before close; 24 resources confirmed; fresh profile absent |
| Persistent receipt write failure after suspended process creation | Failed with the original `OSError`, as expected | Original process terminated with `0xDEAD`, observed signalled before close; 22 resources confirmed; fresh profile absent; evidence completeness remains false |

All three results have no unresolved resource references. Terminal observations
use the original still-held process handles, followed by successful closes;
profile removal is corroborated by a separate path-absence observation. The
normal fixture first produced CPU result 23 and the authorized pipe response,
then received access-denied error 5 for the truth file and five dangerous parent
process access masks. Only afterward did its deliberate excluded-handle attempt
cause the expected strict-handle termination. That nonzero status is not a
general successful-exit rule.

The timeout and write-failure tests pass because their expected product failures
and cleanup occurred. The final write-failure result is in returned memory and
its separately saved observation; its earlier `receipt.json` remains an
incomplete historical snapshot. AppContainer capabilities, Win32k/child
restrictions, two-handle inheritance and Job limits were not relaxed. The
write-failure case stops before resume and does not claim successful mitigation
attestation. Original services, queues, credentials and the physical board were
not selected by this campaign.

Earlier author-stage statements in `isolation_resource_cleanup.md` and
`process_isolation_prototype.md` describe the frozen submission before this
review/run. This checkpoint supplies the later result for exactly these three
cases; earlier P1a/P1b receipts remain bound to their original source bytes.

## Trusted motion execution

The executor prepares every geometry slice before movement, rejects a step with
any unresolved slice, and checks the same admitted BOOT/command identity through
the original final callback. A single root publication changes pose, passage
proof and actual-time commit frame together. It neither extends command
freshness nor moves a safe prefix of an otherwise rejected step.

Independent review reproduced a later history-materialization failure that let
an old admission continue. The repair revokes pending/future motion before
rethrowing the original exception. The already committed pose/frame/history
remain intact; an unknown error does not invent a collision or successful
arrival. Full 137-method suite, original eight independent methods and three new
continuation methods passed at the exact four-file manifest. Source and test
commands, raw logs and the original failing witness are published together.

Actual authenticated source/BOOT/clock/AI-lifetime providers, complete
world/asset-registry delivery, renderer/material integration and both live
control topologies still need integration. Multi-slice full-body passage proof
is the next bounded G06 dependency. Neither a numerical preview nor successful
stopping is a complete-route result. Human-selected editing, camera, equal-size
blue/red gates, hidden truth and meaningful PC AI remain mandatory.

## Reproduction and acceptance boundary

The published source tests run with the project's pinned Python/dependency
environment. Original exact argv/cwd/environment are in the raw review
`commands.json` files. The five-module motion suite is:

```text
python -B -m unittest -v competition.deepeye.tests.simulation.test_motion_executor competition.deepeye.tests.simulation.test_passage_phase competition.deepeye.tests.simulation.test_workspace_boundaries competition.deepeye.tests.simulation.test_solid_clearance competition.deepeye.tests.simulation.test_pc_direct_runtime
```

Native reruns need a fresh main-reviewed attempt and fresh ownership; the
archived gate is evidence of this execution, not reusable permission to select
old processes/profiles. The harness retains unresolved live owners instead of
silently treating parent teardown as verified cleanup.

This software checkpoint leaves formal statuses unchanged. Feishu 21001 remains
an independent communications blocker; it does not gate these local tasks.

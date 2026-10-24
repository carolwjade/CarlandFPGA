# Owner-bound launcher cleanup independent review

**Repair requested: paired acquisition can lose a successfully returned second handle when registering the first raises on ambiguous numeric reuse.** Two fake-only witnesses fail on the exact frozen candidate. Main has read and confirmed those witnesses and deferred native fixture execution. No author-owned source was changed by this reviewer.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-isolation-launcher-review-20261019-v1`; reviewer `/root/pc_direct_review_20261018`; job `child-90b0411c7bac4ee8904308e23e114516`. Native validation required and returned execution_allowed=true before review and before finalization. Sole A Desktop director remains generation 2. `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 and canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` are unchanged and independently verified.

## Exact frozen candidate

Author `source-manifest.json` SHA256 **0bdabec4a3c465e269c090bffd8fb690b2797750f47c4e4c7165e8e4d6a51376**; report SHA256 **1ad8e50427a88a4fdcfec70839de9b32ddff7fe6d0f97272095c8390308a742b**. All 12 current product files exactly match the author's frozen files and this review's `frozen/` snapshots. All 236 baseline dependencies, including historical P1b evidence and the accepted coordinator, match before and after review. Seven pre-existing owned-file before copies match the author baseline; `candidate.diff` records all 12 before-to-candidate changes. The newly added files have an empty before side.

Accepted `resource_cleanup.py` remains SHA256 `4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f`. This result binds exact file hashes, not the product's unrelated concurrent dirty files or the author's former HEAD. The allowed main HEAD movement to `addb2c944ea8f659c48a783c5af1853be8d24d65` does not substitute for the source manifest.

## IL-R1: preserve the complete native acquisition pair before surfacing ambiguity

Product paths below are relative to `competition/deepeye/`:

- `simulation/isolation/owned_resources.py:94` appends the new ambiguous record, then immediately raises. `own_process()` calls this at line 113 before registering the primary thread at line 114.
- `simulation/isolation/win32.py:272` registers the read end after successful CreatePipe. If that raises, line 273 never records the already-created write end. `create_suspended():346` delegates the successful CreateProcess pair to the same non-atomic `own_process()` sequence.

This is one defect class with two confirmed affected paths. Relevant frozen hashes are `owned_resources.py` **17b50e8641e20b6a2ddbc1a74c2b8452c1d1da7b37ad8ca9fc46a1178233a4ba** and `win32.py` **2673d482aad87ac2af8cf83a032772f194be389521f222c84373245c387d115f**.

Minimal pipe witness:

1. Register old kernel reference 81; its one release returns UNKNOWN (which can represent a close whose effect is uncertain).
2. Fake the actual `CreatePipe` binding to succeed and return read 81 / write 82.
3. Call actual `win32.pipe(owner=..., read_label='new_read', write_label='new_write')`.
4. The first registration raises `ValueError('new acquisition retained with ambiguous native reuse')`. The ledger retains only `old:81` and `new_read:81`; **successful writer 82 is absent**, so returned ownership cannot retain or clean it.

Minimal process witness:

1. Register old 91 and cache UNKNOWN release.
2. Call actual `owner.own_process(hProcess=91, hThread=92, dwProcessId=99)` representing a successful returned native pair.
3. The ledger retains old 91 and process 91 but **omits primary_thread 92**. In the actual native helper this occurs after successful CreateProcess and before helper return.

`test_pair_acquisition.py` and `pair-acquisition-counterexample.stderr.log` preserve both behavioral assertions: **2 tests, 2 failures, exit 1**, no fixture process or profile. This is not a memory-exhaustion or malicious-reflection scenario. It composes the explicitly supported ambiguous-reuse boundary with a multi-resource acquisition. We do not claim the current normal fresh launcher has already encountered that numeric reuse on Windows; its ordinary early-release failures usually unwind before later acquisition. The source's declared complete-acquisition retention contract nevertheless fails at these actual helper/registry boundaries. The existing single-resource reuse test misses the second successful resource.

Proposed repair: register **every successful result in the pair** before raising a deferred ambiguity/acquisition error. Preserve all new and old ambiguous identities and original error; never automatically close an ambiguous value. The unambiguous companion must remain in the owner plan and obey its normal dependency/recovery gate. A batch registration primitive or a pair-specific exception-safe registration path can provide that guarantee. Extend both pipe and process regressions, and exercise the actual mocked CreateProcess helper as well as registry direct calls. Do not reopen PIDs or retry unknown CloseHandle operations. Author/main owns implementation and subsequent independent re-review.

## Actual validation

All commands used ROOT `.local/venv/Scripts/python.exe -B -X utf8`. `commands.json`, `extra-command.json` and `extra-command-final.json` retain exact child argv/cwd/environment/exits. Raw stdout/stderr remain alongside them. The copied author driver removes `DEEPEYE_ISOLATION_EVIDENCE_PARENT`; TEMP, TMP and all temporary test products are under this review directory.

| Run | Actual outcome |
| --- | --- |
| Author offline suite, run once | 69 discovered / 66 passed / 3 native cases skipped, exit 0 |
| Independent pair-acquisition counterexamples | 2 failures, exit 1; expected defect witnesses |
| Independent backend/orchestration checks, corrected setup | 3 passed, exit 0 |
| Initial extra-check harness setup | 2 passed / 1 setup error, exit 1; preserved separately |

The setup error was in the review harness: a fixed 32-byte `os.urandom` return also intercepted uuid4's 16-byte request. It raised before launcher acquisition. `test_independent_boundaries.setup-error.py` and the original `independent-boundaries.*.log` preserve it; the corrected stub returns the requested length. Only the same three checks were rerun, with distinct `*-final` logs. This error is not attributed to the product.

The three additional passing checks independently confirm: (a) TimeoutError plus cleanup audit persistence failure retains the original primary exception and live process/thread/Job/profile, closes the safe output reader, and waits only on original handle 70 at timeout 100 / zero / 5000 ms; (b) profile-absence PermissionError retains profile ownership and never replays DeleteProfile; (c) output capture invokes one Peek and one capped 8192-byte read even when a fake pipe reports a million available bytes. These checks do not repair or negate IL-R1.

## Other source observations and prepared native cases

Actual launcher/backend/helper source was inspected against the before copies. Successful single resources are generally recorded before reporting; early release results are cached, failed/unknown operations remain held, and the coordinator is one-attempt. Terminal state uses the held process reference rather than PID reopening. Unknown terminal keeps process, primary-thread and Job recovery controls. Profile removal requires a known path, confirmed dependent releases, successful HRESULT and explicit absence. Attribute buffers and unresolved SID-dependent storage remain referenced. Logging/final-save failures feed separate evidence errors and prevent a PASS; `RunEvidence.ownership` and `.primary_exception` preserve live context and original error outside JSON. These are finite code/fake-test observations, not OS attestation or an exhaustive failure proof.

Security policy values appear preserved: zero AppContainer capabilities, Win32k/child restrictions, the two inherited pipe handles, Job limit 0x2108 / one process / 256 MiB / UI 0xff, five-key environment, detached+suspended creation, staged runtime and fresh-empty-directory ACL rules. No actual ACL/profile readback or mutation was performed.

The three opt-in native cases were read, not executed: normal runs the boundary fixture; timeout substitutes a fixed sleeping fixture and requests 100 ms; persistent-save failure triggers once a process PID is recorded, before resume, and checks cleanup plus a separate returned-memory snapshot rather than promoting the stale receipt. They statically target their named paths, but none covers paired ambiguity. Native approval/execution remains solely with main after repair/review. The CLI is still not a durable recovery owner; retaining JSON alone cannot retain unresolved native handles.

## Scope and completion

Review writes are confined to `.planning/deepeye-resume-20261018/isolation-launcher-review/`. Product and historical evidence were read-only. No original launcher execution, native fixture/process/profile/ACL operation, service, hardware, credentials, external send, Git mutation, additional agent or formal-ledger change occurred.

All three real Windows fixtures, actual OS cleanup/ownership, four-product-process isolation, G03, AI/game/runtime/hardware/board and formal acceptance remain **not_run**. This review closes with a concrete repair request; it is not candidate approval. Main confirmed the two witnesses and paused native fixtures while the author-owned candidate remained frozen.

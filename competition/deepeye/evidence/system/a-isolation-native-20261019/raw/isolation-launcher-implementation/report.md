# Owner-bound Windows launcher cleanup candidate

Implemented the assigned actual launcher/acquisition/backend integration, with
only fake/offline author validation. **Ready for independent source review; no
native acceptance is claimed.** Exactly 12 authorized product files are frozen.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`, work
`A-isolation-launcher-cleanup-20261019-v1`, job
`child-945461d772d64f47a58956851d0811d2`, canonical agent
`/root/worker_results_review_20261018`. Original-endpoint validation returned
execution_allowed=true initially and after the platform interruption. Before
interruption only baseline/test-driver files existed; no native resources or
uncertain side effects were replayed. Sole director remains Desktop
`01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. H01–H15 remain fixed at
requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## Concrete implementation

- `owned_resources.py` records exact acquisition instances in memory; early
  confirmed/failed/unknown releases are cached once. Confirmed numeric reuse gets
  a new reference. Unknown numeric reuse retains both ambiguous records and fails
  acquisition without automatically acting on either binding. Foreign references
  cannot be released through another owner.
- `windows_cleanup.py` checks the original process handle before terminate, then
  performs an independent bounded terminal wait. Unknown termination retains
  process, primary-thread and Job controls; independent handles still close.
  Profile deletion requires a known path, every dependent release confirmed,
  successful HRESULT and explicit absence. Unknown stat/path is never absence.
- `win32.py` records profile/SID before conversion/persistence, Job before setup,
  both process handles before helper return/attribute release, and tokens, local
  strings/descriptors, profile-path strings and attribute-list allocations.
  Unknown attribute storage retains its backing Python buffers and SID storage.
  Helper cleanup failure does not replace an active primary exception.
- `prototype.py` now uses this actual path. Its two-value return is compatible:
  the evidence dict subclass additionally holds `.ownership` and the original
  `.primary_exception` in memory. Unknown resources keep a live context rather
  than losing the only held recovery references. JSON intentionally excludes it.
  Every report/serialization/flush/fsync/final-save error is contained while safe
  cleanup continues. Output capture uses available bytes with an 8192-byte cap;
  no pipe-EOF-dependent read can hang behind an unknown writer close.
- `policy.py` now refuses successful CPU evidence when cleanup/evidence flags are
  absent, false or bool aliases, when any cleanup/audit/owner/evidence errors
  exist, or when ownership is unresolved. Historical receipts remain historical
  and are not retroactively relabeled with this schema/verdict.

The zero-capability AppContainer, Win32k/child restrictions, two-handle allowlist,
Job limits `0x2108`/one process/256MiB/UI `0xff`, five-key environment, detached
suspended creation, staged-runtime manifest and empty-new-directory ACL checks
remain in source. These are source-level preservation observations, not fresh
OS readbacks. The accepted pure coordinator is unchanged, SHA256
`4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f`.

## RED/GREEN and actual execution boundary

Exact commands, working directories, exit codes and source hashes are saved in
each `red*.json` / `green*.json`. Raw stdout/stderr bytes and combined logs remain
beside them. The driver executes only `unit_suite.py` using the project Python
with `-B -X utf8`, from product `competition/deepeye`.

1. Initial RED: 60 discovered, 21 failures, 2 native skips, exit1. Missing ownership
   implementation and missing returned context failed explicit assertions; the
   existing coordinator/policy cases ran as well.
2. Initial GREEN: 60 discovered, 58 passed, 2 native skips, exit0.
3. Second RED: 65 discovered, 15 failing assertions/subtests, 2 skips, exit1.
   Genuine counterexamples showed final/audit evidence failure could still PASS
   and direct profile release lacked its dependent gate. One helper test failure
   was a harness artifact: the policy-only user-SID stub had been scoped across
   the whole suite. It was narrowed to policy tests, preserving the failed log.
   Second GREEN: 63 passed, 2 native skips, exit0.
4. Third RED: 67 discovered, 2 failures and 1 compatibility-key error, 2 skips,
   exit1. These exposed SID release before uncertain attribute storage, missing
   real fsync in the receipt writer, and loss of the legacy primary-error `type`
   field. Third GREEN: 65 passed, 2 native skips, exit0.
5. Fourth RED: 69 discovered, 1 failure, 3 native skips, exit1: a successful new
   acquisition after an unknown numeric release was rejected without retaining
   its reference. Both ambiguous records are now retained. Fourth and final
   GREEN: **69 discovered / 66 passed / 3 explicitly skipped native tests, exit0**.

Tests exercise actual launcher orchestration with injected APIs, actual helpers
with replaced native acquisition/release calls, primary-error retention, checked
early close, numeric reuse, Job/process helper failures, terminal failure,
profile gates, every coordinator sink boundary, final serialization/write/fsync
failure and returned ownership. Existing policy ACL tests retain their filesystem
precondition checks while an unrelated setup token read is stubbed; invalid ACL
targets are rejected before native ACL calls. All test temporary files are routed
to this evidence directory. The suite explicitly removes the native opt-in env
variable in its own process. No AppContainer, profile, fixture process, service,
queue, board or real ACL mutation was created/run by this job.

## Exact frozen bytes

| Product path | Bytes | SHA256 |
| --- | ---: | --- |
| `competition/deepeye/simulation/isolation/owned_resources.py` | 7148 | `17b50e8641e20b6a2ddbc1a74c2b8452c1d1da7b37ad8ca9fc46a1178233a4ba` |
| `competition/deepeye/simulation/isolation/windows_cleanup.py` | 4184 | `ca1771e1828fb8800b57ab3051f85df2e73601efe5e7874f42c8bca50361102d` |
| `competition/deepeye/simulation/isolation/prototype.py` | 16571 | `af54c6a5240be4e585f1c621034f5b687f79199595b82d54b2278253ceb4e452` |
| `competition/deepeye/simulation/isolation/win32.py` | 17791 | `2673d482aad87ac2af8cf83a032772f194be389521f222c84373245c387d115f` |
| `competition/deepeye/simulation/isolation/policy.py` | 7119 | `a1945451dd6324f3cce2768cff8127f1a3755c8856061bf24d954b9a844afa11` |
| `competition/deepeye/tests/isolation/test_owned_resources.py` | 3682 | `ec42e4d35c1d365e677ebcd2cc3fd187d274c49d7c557a47975d4a95444ed316` |
| `competition/deepeye/tests/isolation/test_windows_cleanup.py` | 8948 | `4f20b5b9072d507298265ea950597263544907d6979cfc409e5d35352499fb80` |
| `competition/deepeye/tests/isolation/test_prototype_cleanup.py` | 9062 | `c7dfe79aad09418d8901cd1f34c059647ada32b5de086a773304e0bee90bbd24` |
| `competition/deepeye/tests/isolation/test_policy.py` | 11085 | `0596d77ade275426dfbdba6fc897f08eab258b734d324682105427b64afedf8f` |
| `competition/deepeye/tests/isolation/test_windows_live.py` | 4344 | `bfce80b3fa26be12d6f27e6994552a7dab776fd06a0df28860a4863955c5da74` |
| `competition/deepeye/docs/isolation_resource_cleanup.md` | 13427 | `135bee5d4a9fda0786456435b5e72c298e99d39b6a92aacc5635dd4a256c2518` |
| `competition/deepeye/docs/process_isolation_prototype.md` | 11697 | `f6caa7f58d95bf70c418cf3d66dc2f953f1d1480220cfc6bd1e38be78af4cdac` |

`source-manifest.json` and `frozen/` match the final tested bytes. **236 unowned
dependencies are unchanged**, comprising 227 historical P1b files and nine other
product/design/scope inputs. Before copies and baseline hashes are retained.
Historical P1a/P1b launchers/evidence were never executed or rewritten. No Git
index/commit/push/reset/clean or formal-ledger operation was performed. Observed
HEAD at freeze was `9d29d4c87b964de98479fe62067aeb0da91ace63`; main subsequently reported its
non-overlapping publication commit `addb2c944ea8f659c48a783c5af1853be8d24d65`.
Acceptance binds this exact source manifest, not an assertion that unrelated
main-owned dirty bytes or the whole checkout stayed fixed.

## Limits and immediate next dependency

Main/independent reviewer should inspect the exact 12-file candidate, then run
the prepared three opt-in `test_windows_live.py` cases with a new dedicated
evidence parent: normal, timeout and persistent receipt failure after process
creation. Preserve every generated run/profile identity, source/runtime hashes,
returned ownership, errors and raw output. In the injected persistence case the
earlier `receipt.json` is stale; a separate expected-failure in-memory snapshot is
prepared only after cleanup. Do not label that stale receipt as the final result.
Independent native terminal/profile readback is still required before adoption.

This backend covers the named CPU fixture handles and helper allocations only.
It does not implement sockets, arbitrary Python-thread shutdown, GPU/UI runtime
or four-product-process containment. Local owner assertions and mutable trusted
registry state are not OS permissions/attestation or cross-process ownership
locks. CoTaskMemFree and DeleteProcThreadAttributeList have void-return bounded
helper contracts; Python buffers/scoped file objects are not an independently
measured global allocation inventory. Abrupt owner death, Python registration
memory exhaustion and other trusted writers are outside the synchronous guarantee.

Keep returned `RunEvidence.ownership` alive when unresolved; serialization/copying
cannot preserve live handles. The CLI is not a recovery owner, and its exit/OS
teardown is not confirmed cleanup. No blind retry/reopen-by-PID or automatic
unknown-effect replay exists. Receipt writes use a new owned pending file,
flush/fsync and replace; failed partial files are kept. Directory-entry crash
durability and sink success-after-side-effect exceptions remain separate audit
questions. The returned in-memory verdict reflects final write failure, while a
disk snapshot can remain provisional.

All new native cases, G03, four-process/runtime/AI/game/hardware/board and formal
product acceptance remain **not_run**. H01–H15 are unchanged.

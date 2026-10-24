# Isolation cleanup coordinator: independent bounded review

Result: no blocking defect found within the documented trusted-owner/backend contract. The software primitive is suitable for the main's bounded offline approval. This review does not accept real resource cleanup, launcher integration, OS isolation or G03.

Reviewer `/root/pc_direct_review_20261018`; work `A-G03-ISOLATION-CLEANUP-REVIEW-20261019-v1`; native job `child-f05e904bbb104a3ba3043354efa848a9`. This job was authenticated and execution_allowed=true before review and again before finalization. Sole director remains Desktop generation 2, thread `01a13d7e-dcf1-7272-a738-a637dd62ff9d`.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 retained. Canonical requirements hash independently matched `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## Exact reviewed candidate

Product-relative frozen files (SHA256):

| File | SHA256 |
| --- | --- |
| competition/deepeye/simulation/isolation/resource_cleanup.py | 4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f |
| competition/deepeye/tests/isolation/test_resource_cleanup.py | 9236b45d3978619912425fda170b4ee1964c53b63e31ba79dae739b2cb7e8292 |
| competition/deepeye/docs/isolation_resource_cleanup.md | f0a1b929bbacd7466d8929620c07cb16d2261c69626a2bdf5a1e16c8105fee63 |

All three and the author's 12 declared dependencies matched expected size/hash before and after testing and at finalization. The author report, receipt binding and all evidence-manifest entries were independently hash checked; see `author-artifact-check.json`. Prior RED/GREEN artifacts were preserved and not rerun. This review did not import or execute any archived runner, native launcher, prototype, win32 actor or profile tool.

## Current independent execution

Both commands used the repository `.local/venv/Scripts/python.exe -B -X utf8`, cwd product `competition/deepeye`, no bytecode, and per-process PYTHONPATH bound only to that directory. TEMP/TMP pointed inside this review's ownership.

| Suite | Command after interpreter flags | Exit | Result |
| --- | --- | --- | --- |
| Author current source | `-m unittest discover -s tests/isolation -p test_resource_cleanup.py -v` | 0 | 23 passed |
| Independent | absolute `isolation-cleanup-review/test_independent_cleanup.py` | 0 | 8 passed |

Exact argv/cwd/environment and raw stdout/stderr are retained in `commands.json` and the corresponding `author-23.*.log` / `independent-8.*.log`. `harness-execution.json` records the outer invocation. Tests invoke Python-only fake callbacks; no OS ownership/termination/deletion behavior was exercised. The independent suite also checks that win32/prototype/ctypes actor modules were not loaded in its test process.

## Findings and practical limits

1. Unknown close/remove/terminate outcomes are recorded separately from confirmation. Every side effect is attempted at most once per coordinator, and repeat/reentrant cleanup is rejected without new callbacks. A termination exception still allows an independent terminal readback; literal True is required before releasing process ownership. Unknown terminal state retains both process reference and every declared recovery reference.
2. Sink failures, including partial persistence and BaseException, do not skip later safe actions. Original failure text is captured before callbacks. Cleanup and audit errors remain separate. Resources can finish while success remains false because an earlier action or evidence write failed.
3. Profile deletion waits for every declared dependent resource to close, including fixture resources and process references. Failure in one profile does not prevent independent cleanup. A shared recovery resource remains held until every declared process is confirmed terminal. The independent suite checks callback order and exact counts, including a plan whose profile appears first.
4. Exact duplicate reference objects are rejected before callbacks. Different wrappers for one OS object, omitted resources, exclusive ownership, bounded backend operations and truthful confirmation are the explicit trusted caller/backend obligations. They are not established by these tests. The coordinator's instance lock is not a cross-instance or OS lease.
5. The finish AuditEvent contains a provisional snapshot taken before its own sink call. If that final persistence fails, the returned result correctly changes evidence_complete/success to false while retaining resources_complete. The doc states this distinction and our counterexample confirms it. An eventual adapter must not promote that provisional event to a durable completed receipt on its own.

No repair request is raised for the frozen three-file candidate. The finite conclusion applies only to complete, exclusive plans and conforming trusted callbacks. This primitive cannot discover or attest OS ownership, guarantee real cleanup, or authorize retry/reconstruction after an unknown effect.

## Smallest next implementation step and proposed ownership

Main should assign a separate trusted backend/launcher integration design and fake acquisition-error-path tests. That owner must explicitly bind exact held resource identities, build a complete profile/recovery dependency plan, bound each backend call, and preserve the coordinator plus unresolved references after an uncertain effect. Returned final results must drive durable receipts; an explicitly authorized reconciliation plan must precede any retry. Integration into the historical launcher and any actual Windows probe require a separate bounded assignment; none was performed here. Proposed ownership is new backend/adapter and its tests, leaving these reviewed three files frozen unless the main approves a specific contract change.

G03, actual four-process isolation/cleanup, current resident/native runtime, product activation, full game, AI, hardware/board and full acceptance remain **not_run**. Historical P1b evidence retains its earlier finite provenance limits.

## Write scope

All reviewer-created files are under `.planning/deepeye-resume-20261018/isolation-cleanup-review/`. Product/prior evidence were read-only; the 15 declared candidate/dependency files remained byte-identical. This is a scoped hash check, not a claim of a workspace-wide filesystem audit. No git commit/push, service/ACL/profile/board operation, native launcher/probe, external message, or additional agent was used.

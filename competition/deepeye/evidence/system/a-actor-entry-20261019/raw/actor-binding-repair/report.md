# Actor binding retirement repair — author candidate

Original job `child-bc96ffdb98124a4682293803674ac807`, canonical author
`/root/worker_results_review_20261018`. Main accepted AOR-R1/R2/R3 from independent findings
SHA256 `85c01193a3878a41cbd69fd516e649efb67e7a82a1de45fac01534ab2a6bdeca` and receipt
`67801b054f57f8e031c73c4bcec51d630762a9572be569a2e0bd6278c218b0c9`.
This is an implementation result pending independent review, not main acceptance.

Seven-file combined manifest SHA256:
`98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670`.
Six repair-owned paths were changed, with unchanged `actor_lifetime.py` included only as a
read-only dependency. `candidate/` preserves exact copies. No product writes follow freeze.

## Repairs

| Finding | Change and evidence |
| --- | --- |
| AOR-R1, public-lifecycle availability defect | Capture the actual runtime and executor activation identities independently when attaching callbacks, including partial binding. Retire owner state/epoch first as before. Immediately before each callback, compare that target's current activation to its captured original; executor comparison occurs after STOP callback returns. Late close/poll/old or malformed lease entries on CLOSED/QUARANTINED owners cannot stop fresh BOOTs. A still-original target remains revocable in a mixed old/new pair. |
| AOR-R2, injected dependency-shape defense | Both initial Wait and terminal Wait require `type(state) is int` before comparing 0/258. Bool, IntEnum, numeric subclasses, float, None and unexpected integers cannot falsely establish terminal state or release process/job/profile recovery controls. |
| AOR-R3, injected dependency-shape defense | Capture all four inheritance readbacks, then require exact integer masks and `(1,1,0,0)` before resume. A malformed readback follows original cleanup and never resumes. |

The callback fence applies at the common `_revoke` boundary, rather than only blocking
duplicate cleanup or depending on local state labels. Runtime `_boot` and executor `_root.boot`
are the pinned private activation seams. A partial pair captures each actual activation,
not just the proposed common BOOT. STOP failure still cannot skip an applicable executor
revoke, caught reentry cannot restore an owner or recursively dispatch STOP, primary
exceptions remain preserved, and native cleanup still has one original attempt/quarantine.

R2/R3 do not show Windows returned malformed results: existing native DWORD helpers return
plain integers. Their tests exercise fake dependency drift. No other helper was modified.
Documentation now correctly distinguishes the helper's 8192-byte native output-read hard
cap from smaller `output_limit`, which is a post-read acceptance/discard limit.

## Pinned execution and RED/GREEN

The evidence tree was built from exact commit
`3f702903f1e16fa72eae15f03ba431b78de24bd0`: 56 tracked simulation/integration/tests blobs,
plus three import-required JSON schema blobs from that same commit. Every Git blob ID and
SHA256 is recorded in `baseline.json`/`schema-pins.json`. Original five frozen actor files
were overlaid from author manifest
`2bace7921cd89ff2cf7e9d1dd8b87dbd1be6f4d34abd1ac3cc3d37026dc39630`, then only the six
repair-owned files were overlaid from this task. No changing live G06 file was copied.
Tests ran with this tree as cwd and process-only PYTHONPATH/TEMP/TMP overrides recorded
in each result JSON. No Git index/branch/worktree or global path was changed.

The first `red-independent8` did not run tests: the initial isolated tree lacked
`docs/host_contract.json`. Its preserved traceback points to pinned-source actor/runtime/
watchdog files and the missing pinned JSON path, not live PRODUCT. That initial command
did not collect a full module-origin dump, so it is not claimed as a complete process import
audit. It is a scaffolding failure, not RED proof of an accepted finding. Adding the three
same-commit JSON dependencies fixed scaffolding without using live source fallback.

| Raw result label | Actual result |
| --- | --- |
| `red-independent8-pinned` | Exact original eight methods, exit 1, six failing assertions/subtests in the three accepted finding methods |
| `red-expanded` | 148 methods, exit 1, 40 failed assertions/subtests, zero errors; all accepted findings and expanded retirement/type cases were red before production repair |
| `green-repair` | 148 methods, exit 0, zero skipped: original 116 actor/runtime regressions + five new actor repair methods + exact eight independent methods + 19 affected shared-cleanup methods |
| `final-independent8` | Exact original eight methods separately pass, exit 0, zero skipped; imported project module paths and hashes audited into `final-independent8.module-origins.json` |

The reviewer script is copied byte-for-byte with unchanged assertions, SHA256
`de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f`. Its final witness output
is isolated under `runs/final-independent8/`. The old review's RED witness files and full
manifest are unchanged; this task's raw RED logs and per-run source hashes are preserved.
The final independent pass includes its deliberate unwired-provider counterexample: that
method demonstrates a remaining trusted composition obligation, not successful monitoring
or actual AI safety. No negative witness was relabeled as product acceptance.

Expanded regressions cover CLOSED and QUARANTINED owners across close, poll, old lease and
malformed lease; fresh replacement remains able to commit one numerical pose afterward.
Mixed runtime-new/executor-old and runtime-old/executor-new activations are checked
independently. A STOP callback that advances the executor cannot cause the later executor
callback to stop that successor. Same-original binding and partial-activation failure still
receive STOP/revoke. Strict boundary cases include Bool/IntEnum/int subclass/float/None and
unexpected integers; malformed terminal results retain original recovery ownership.

All original 52 actor and 16 cleanup test method ASTs remain identical; only new methods
were added. Existing 64 runtime tests use the unchanged committed runtime/test bytes.
`actor_lifetime.py` is exactly unchanged. Eight nonmoving live helper/runtime/lifetime
dependencies equal their tested pinned copies; unrelated live G06 movement is intentionally
not compared or included in this evidence. No broader old native suite was opted in.
Shared-cleanup mock tests import the existing ctypes binding module, but process/handle
operations exercised by those tests are fake/patched; no actual native actor or OS fixture
was launched.

All seven bundle files are UTF-8 LF without BOM; raw Git object equals Git clean object
without staging or writing objects. The exact Python source hashes from the 148-method
GREEN run match the frozen candidate. Only documentation clarification followed that run;
the final eight-method run records all final overlay hashes. Original source before-images,
59 committed dependency blobs/schema pins, command argv/environment, raw stdout/stderr,
module origins, candidate copies and final manifest remain available for independent review.

## Frozen core hashes

- `actor_owner.py`: `810a51ac68c9c456f956d7f6a2c9239f3e73032db00e0e0846536e28a7b6de7e`
- `windows_cleanup.py`: `1861316badcaacd2b47b2e311e3779595cac7055c074e72c4b9a4381ffad1eb3`
- Unchanged `actor_lifetime.py`: `f73df762802e632d182e7de5c65ee2bbe2e9ed11660269c083dfbfa4d0e136b0`

## Remaining gates

Main's separately frozen new G06 candidate was not used in these tests. New-G06 plus this
repair requires the main's later actual joint regression and independent review. Neither
has been claimed here. No real native launch, product Run, package/network acquisition,
installation, driver/service/board or external task effect occurred. The metadata variant
job remains historical failed/terminal, with no further torch request.

Post-sample death, creation-to-AssignJob owner-death window, authority hang supervision,
job-last-holder conditions, authenticated readiness/BOOT/channel providers, persistent
causal IPC, actual useful project AI and product composition remain separate dependencies.
The cleanup and actor tests do not establish OS deployment, real process supervision or
game/hardware behavior. Next action is main-owned exact-byte independent review and later
joint regression, followed only then by separately authorized bounded native evidence.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 canonical SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` remains unchanged.
All29 formal cards, actual native actor, real AI, complete H12 chains, game/board and
product Run remain **not_run** by this delivery.

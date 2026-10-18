# Pure cleanup coordinator implementation

Implemented the approved bounded cleanup design in exactly three new product files.
This is offline implementation evidence pending main's independent review; it is
not launcher activation or final product acceptance.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; job
`child-1b7d68d1176b4ea2994e6123233f5b7e`; agent
`/root/worker_results_review_20261018`. Original-endpoint native validation allowed
execution. Sole director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`,
generation 2. Both root/product immutable requirements verify canonical SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`, H01–H15.

## Behavior and historical defects

| Historical P1b defect | New bounded behavior | Observable regression |
| --- | --- | --- |
| event/persist failures interrupt termination/close | Every sink call catches its failure; later safe actions continue | Inject failure at each of 18 normal sink boundaries and at every backend boundary; assert exact action order/count and retained failures |
| close pops ownership before completion; cleanup marks closed after errors | Per-resource operation outcomes and ownership retained until confirmed; unknown is never replayed | Failure/unknown/malformed close preserves resource/profile; second cleanup rejects without a callback |
| aggregate omits fixture failures; profile deleted before fixtures | Explicit process/handle/thread/socket/profile plan; every declared profile dependent must be confirmed closed first | Fixture handle/thread/socket failures gate profile; mixed failures still close independent resources |
| terminate request could stand in for terminal state | Independent held-identity wait/readback required even after terminate exception | Terminal readback permits safe closes but retains terminate error; false/unknown/exception keeps process and recovery handle |

Primary error is snapshotted before callbacks; cleanup and audit failures remain
separate. Backend exceptions/malformed returns mean UNKNOWN. Confirmed resources,
complete evidence and overall success have distinct flags. Reentry/overlap and
repeat calls on the same coordinator are rejected. Exact same reference double
registration is rejected before any callback. Frozen task/source provenance and
resource ownership are supplied assertions, not OS attestation or permissions.

## RED/GREEN verification

All commands and working directories are recorded verbatim as argument arrays in
`red.json`, `green.json`, `red2.json`, `green2.json`; raw stdout/stderr bytes and
combined logs are preserved separately. Test command, from the product's
`competition/deepeye` directory:

```text
ROOT/.local/venv/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/isolation -p test_resource_cleanup.py -v
```

- Cycle 1 RED: 20 failures, exit 1, deliberate assertion that the new coordinator
  does not exist. No import-error-only or skipped success claim.
- Cycle 1 GREEN: 20 tests passed, exit 0, first implementation.
- Cycle 2 RED: 23 tests, 1 real behavioral failure, exit 1: duplicate exact reference
  was accepted and could be closed twice. The other added action-boundary and
  independent-second-process counterexamples passed.
- Cycle 2 GREEN: **23 tests passed, exit 0**, including duplicate-reference rejection.

`test_resource_cleanup.cycle1.py` and `resource_cleanup.cycle1.py` retain the exact
cycle-1 bytes. Final test source equals the cycle-2 RED test bytes; final production
source contains the duplicate-reference guard added afterward. The final three
files equal the bytes tested in `green2.json` and the frozen copies byte for byte.
The suite runs only the new pure coordinator, injected fakes and stdlib. No native
fixture, profile, OS cleanup/probe, historical runner, service, launcher, network,
credential, hardware or viewer/AI code was invoked or changed.

## Frozen product bytes

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `competition/deepeye/simulation/isolation/resource_cleanup.py` | 11539 | `4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f` |
| `competition/deepeye/tests/isolation/test_resource_cleanup.py` | 16407 | `9236b45d3978619912425fda170b4ee1964c53b63e31ba79dae739b2cb7e8292` |
| `competition/deepeye/docs/isolation_resource_cleanup.md` | 7737 | `f0a1b929bbacd7466d8929620c07cb16d2261c69626a2bdf5a1e16c8105fee63` |

`baseline.json` and `dependencies-after.json` bind **12 unchanged existing files**:
all existing isolation modules/tests, product AGENTS, root immutable scope,
historical runner and independent P1b review. The coordinator imports no existing
project dependency; existing native helpers were read only, never imported/run.
No commit, push, index or ledger operation was performed. Unrelated main-owned
source/commits may change concurrently; this report makes no whole-tree-clean or
whole-index-unchanged claim.

## Remaining dependency and limits

Main independently reviews these three source files and evidence before adoption.
Then a separately assigned future trusted-launcher/backend task must demonstrate
exhaustive resource/dependency capture, one canonical reference per owned object,
exclusive ownership/single coordinator, bounded OS callbacks and actual
terminal/close/thread-join/profile-absence readback. This coordinator cannot detect
two different wrappers of one OS object, omitted resources, or a second program
claiming ownership. Its local lock prevents overlap on one instance only.

Unknown effects require explicit owner reconciliation/readback and a new authorized
plan, never recreation of the coordinator to blindly replay. A sink may fail after
partially persisting an event: that event is not retried; evidence stays incomplete.
The finish event carries the pre-final-sink snapshot; the returned result includes
failure of that final sink call, so a persisted provisional snapshot alone cannot
prove evidence completion.

No existing runner adopts the component. Launcher integration, real OS cleanup,
four-product-process isolation, G03, runtime, AI, game, hardware, board and all final
acceptance gates remain **not_run**. H01–H15 are unchanged.

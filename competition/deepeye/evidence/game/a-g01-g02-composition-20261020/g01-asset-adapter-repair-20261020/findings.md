# Bounded G01 asset-adapter repair evidence

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; native job `child-d9f9c52cb946453183722e1957978fe0`; agent `/root/g01_asset_adapter_repair_20261020`. This implements the main's prescribed F1-F4 repairs and supplies evidence for independent re-review. The main retains all adoption and acceptance decisions.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`; canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. The current transfer was active for Desktop director `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. H01-H15 and all 29 formal cards remain unchanged; every card remains `not_run`.

## Changes and bounded results

- **F1:** Metadata consumed by validation is type-checked before conversions or string operations. Version must be integer 1, license a nonempty String, asset ID a String, bounds dictionaries with finite Vector3 min/max and positive volume, and radius a finite positive number. Creation consumes `_validate_asset_result`'s explicit Dictionary and defaults missing `ok` to rejection. `_validate_asset` retains its previous diagnostic String interface so the unchanged reviewer's ten malformed-asset assertions continue to test actual rejection; it delegates to the explicit result. No unchecked metadata String constructor remains.
- **F2:** Before binding the factory, validate static flags, exact argument count, absence of optional/variadic arguments, String kind argument, and declared Node3D return type. Before the unproven call, persist a diagnostic in a unique per-creation pending record. Remove that record only after a valid return or explicit recorded rejection; an aborted caller leaves a degraded report and diagnostic. A later successful call uses a different key and cannot erase an earlier unfinished call. The wrong-signature fixture now degrades before any factory invocation (`frame=0`, `drill=0`, `obstacle=0`), without its former runtime error.
- **F3:** At creation, Visual must have actual mesh instances, nonempty surfaces and valid finite raw vertex arrays/faces, and at least one nondegenerate triangle per mesh. Empty/null mesh data and hidden mesh paths are rejected. Raw vertices are checked before `get_faces()` so the deliberate NaN fixture is rejected without introducing an engine normalization warning. These checks are not repeated during transform-only updates.
- **F4:** Fallback labels use all eight local mesh-AABB corners transformed by the full fallback global transform. Selection inverse-transforms the world ray into the actual fallback-local AABB and leaves its direction unnormalized, preserving world-ray t for comparison with real assets. Coverage includes a rotated, translated, nonuniform parent with induced shear, identity behavior, and a nearer real asset competing against a farther fallback under anisotropic parent scale.

The complete before/after product manifests show changes only in `viewer/asset_presenter.gd`, `viewer/main.gd`, and `tests/test_viewer_asset_integration.gd`. All unowned product bytes, including B asset sources and A UI/editor/codec/tests, are unchanged. `repair.diff` derives directly from the preserved original stage and current product bytes. The frozen stage matches all product source pins.

## Fresh verification of the frozen source

All ten frozen processes recorded exact argv/cwd, PID, pinned executable SHA256, before/after stage manifests, raw stdout/stderr hashes, exit status, timeout and terminal state. Every process was terminal, exit 0, with no timeout and no `SCRIPT ERROR` or `ERROR:`. Read the raw stderr for the limitations below.

| Receipt label | Actual result |
|---|---|
| `frozen-import` | Headless import exit 0 |
| `frozen-integration` | 136 checks / 0 failures |
| `frozen-independent` | Unchanged corrected reviewer harness: 54 / 0 |
| `frozen-negative-bad-license` | Unchanged failure oracle: 14 / 0 |
| `frozen-negative-signature` | Unchanged failure oracle: 10 / 0 |
| `frozen-negative-empty-visual` | Unchanged failure oracle: 14 / 0 |
| `frozen-negative-null` | Unchanged failure oracle: 16 / 0, exact transformed label and displayed-center pick repaired |
| `frozen-persistence` | 628 / 0 |
| `frozen-editor` | 696 / 0 |
| `frozen-g02-ui-fit` | 266 / 0 |

`B622-exact-reuse.json` verifies the prior B-only 622/0 run's actual terminal/exit/executable/argv and raw-log hashes. Its executing harness, project configuration and complete world/assets dependencies still match exactly; that harness does not load A's changed viewer/presenter or integration test. No fresh 622 run is claimed.

The unchanged reviewer oracles and private B mutations are pinned in `unchanged-oracles.json` and each frozen fixture manifest. The four original RED receipts were verified against current original product pins and retained in their original evidence directory. `original-red-reuse.json` binds their receipts and raw logs. In addition, the exact final integration harness was run on the original product in a fresh private stage: `frozen-harness-red` terminated exit 1 with **136 checks / 11 failures**, preserving the original invalid-license runtime errors and explicit geometry/transform failures. The same exact harness then has the frozen-source 136/0 receipt above. The original snapshot and all old RED evidence remain untouched.

## Preserved errors and limits

The platform interruption happened after candidate import had actually finished; its existing terminal receipt was read and retained, not replayed. The same job was revalidated with `execution_allowed=true` into a new `native-revalidate-response.json`; no new lease was reserved.

Earlier candidate/final-named stages and their receipts are superseded by the `frozen-*` receipts. One candidate NaN check emitted a normalization warning before raw-vertex guarding was added. The earlier Dictionary validator temporarily changed the meaning of the independent harness's `.is_empty()` malformed checks; the final implementation restores the String diagnostic query, and the unchanged 54-check harness was rerun on the frozen source. These intermediate receipts are retained and are not final evidence. `frozen-ui-fit` is an erroneous invocation of nonexistent `test_ui_fit.gd`, exit 1 with file-not-found errors; the corrected `frozen-g02-ui-fit` uses the actual pinned script `test_g02_ui_fit.gd`. No failed invocation is promoted to a pass.

Inherited Unicode NUL diagnostics remain: four during import and three in the ordinary frozen runs. Persistence also retains the existing deliberate excessive-exponent and invalid-UTF-8 fixture diagnostics. Therefore **engine-clean is not satisfied**. The original reviewer's invalid first-attempt 49/0/runtime-error evidence remains in its original directory, and its exact harness is also preserved locally; it is never treated as a pass.

No GUI, live editor interaction, Git command/commit/push, network, B/UI/editor source write, board, Run, service, provider/credential change, peer message or child was performed. All Godot runs were bounded headless subprocesses in this assignment's evidence directory. `terminal-process-readback.json` records zero matching Godot/Python processes. There is no native visual-quality, GPU timing/FPS, physical collision/crossing, causal sensor, PC-AI, control-chain, board/system or formal product acceptance claim. Independent re-review by the main remains pending.

## Frozen identities

- Engine SHA256: `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`.
- Source-after manifest SHA256: `dcbb63df5f52a62d953f2e7f63372c343796d661ac1dd626900b7fb1cc9ebee6`.
- Exact repair diff SHA256: `96e3c47e5729e3f813e22934cacec104840a524691a13c2d2ab3eabd777e0849`.
- Repair receipt SHA256: `9056113536888d0e24ce92aa9015e0019cb7016cd00ef770bbae78a00b5155e2`.

The finishing workflow is scoped by the main's explicit freeze-and-complete assignment: preserve this existing workspace for independent re-review, with no Git integration or cleanup.

# Bounded A presentation implementation

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`, work `A-G01-ASSET-ADAPTER-IMPLEMENTATION-20261020-v1`, native job `child-3f85afc8948f4778b622d2c11b1fd4fe`, agent `/root/g01_asset_adapter_impl_20261020`. The sole A main retains review and acceptance. H01-H15 and canonical requirements hash `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` were freshly verified. Active transfer/director generation 2 was read. No Git, network, GUI, board, Run, service, provider, credential, queue or lock operation was performed. Native lease validation/completion use only the assigned private guard; secrets are excluded from evidence.

The actual viewer now instantiates the unchanged B frame, 28-part PDC drill and all five obstacle kinds. `asset_presenter.gd` uses a fixed lazy factory path, checks all four dependency paths and static methods, validates metadata/tree safety, rejects enabled colliders, reconciles IDs/kinds, and preserves meshes/materials on transform updates. Placement scales rotation columns by document nominal size / declared envelope size, preserving original pivots. World bounds transform eight corners including the parent; picking uses the affine inverse without normalizing local ray directions. A labels use actual world bounds; selection stays the nominal editing envelope.

Failed assets use the retained real A greyboxes, explicit resource-failure labels and a persistent degraded UI report. Failed same-kind instances are not retried on repeated sync; kind changes replace stale fallbacks. B materials, meshes, scripts, licenses and UIDs remain unchanged. The drill stays static at origin with unit scale and +Z orientation. A drill-focus button uses actual visual bounds, viewport aspect/keep-aspect FOV, 1.25 framing margin, .02 m near and .5 m minimum distance. Existing permanent help, 24 px action status, 15 px font/tooltip behavior and current lighting are preserved.

Persistence still saves only existing geometry parameters through the existing codec/store. Neither scene_document nor codec nor validators changed. The old greybox drill assertions now run on the explicitly constructed real fallback; none of those geometry assertions were removed. Only the two approved persistence representation helpers were migrated to presenter roots, adding ID/kind/instance/basis/world-vertex checks. No hidden proxy geometry was added.

`red-integration-actual.json` records the genuine pre-implementation failure: `actual viewer binds asset presenter`, checks=1 failures=1, exit 1, no script parser error. Final source tests all exited 0 and have terminal=true, timeout=false:

| Command script | Result |
|---|---|
| test_viewer_asset_integration.gd | 122 checks, 0 failures |
| unchanged test_asset_contract.gd | 622 checks, 0 failures |
| test_editor_document.gd | 696 checks, 0 failures |
| test_layout_persistence.gd | 628 checks, 0 failures |
| unchanged test_g02_ui_fit.gd | 266 checks, 0 failures |
| missing fixed dependency fixture | 15 checks, 0 failures |
| null obstacle factory fixture | 19 checks, 0 failures |
| enabled collider fixture | 19 checks, 0 failures |

The 30-instance integration campaign measured 30 B obstacle meshes and 41,544 obstacle triangles. A gate cost was 6 meshes/11,136 triangles, ticks 15 meshes/180 triangles, direct corner/selection meshes 9; 48 Label3D nodes in the whole world including 30 obstacle labels. One cold document-add sequence took 146,708 us. For 100 updates, scene no-op sync median/max were 175/408 us; full document transform-update median/max were 4,281/5,867 us. Raw samples are in the final integration stdout/receipt, with OS/CPU/engine data in source-pin-check.json. There were zero new factory calls or root/mesh/material identity changes for those updates, and no node growth over ten create/clear cycles. These are CPU-side observations, not GPU FPS.

The engine-clean gate is **not satisfied**: the viewer emits three `Unicode parsing error ... Unexpected NUL character` diagnostics. A fresh run of the exact original source-before editor also passed 696/0 with the same three diagnostics, proving they predate this adapter. Their underlying cause is not resolved in this assignment. Candidate tests contain no `SCRIPT ERROR`. B's intentional bogus_kind ERROR and persistence's exponent/invalid-byte rejection diagnostics are preserved separately. All failed parser/harness attempts and the two verified own-process terminations are retained in raw evidence; they are not counted as successful checks.

Source-before/source-after copies, per-run full manifests, exact argv/cwd/PID/executable hash/stdout/stderr/exit/terminal data, candidate.diff, implementation-receipt.json and terminal-process-readback.json are retained. All nine changed product files are within assignment ownership, unowned source drift=0, all 15 B source pins match. No assigned Godot process remains. Main may inspect the final stage using its separately assigned GUI process; this child performed no native visual judgment.

Native visual readability/interaction, GPU performance, physical collision/crossing, H08 OS isolation, sensors, AI, both control modes, board and system remain unproven. All 29 formal cards stay `not_run`. This handoff grants no product acceptance.

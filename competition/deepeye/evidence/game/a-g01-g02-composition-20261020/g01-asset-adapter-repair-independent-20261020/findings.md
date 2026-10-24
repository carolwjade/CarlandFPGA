# G01 F1-F4 independent repair review

Task DEEPEYE-IMPLEMENTATION-20261014/v1; native job child-754808b3064e4a158cfff208a1baaaf3; agent /root/g01_asset_adapter_repair_independent_20261020. Evidence only for the sole A director. No adoption decision is made.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1 and canonical requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 were verified before testing. All H01-H15 are preserved. Active transfer names Desktop director 01a13d7e-dcf1-7272-a738-a637dd62ff9d, generation 2; current node configuration names A / fpga-main. All 29 formal cards remain not_run.

## Findings

No new actionable defect was found in the assigned F1-F4 repair diff and the bounded checks below. This is a software evidence result, not formal G01 acceptance.

- F1: Explicit type checks precede string operations on license/version/asset-ID metadata. Creation consumes an explicit validation Dictionary; missing success/error fields do not become an empty-string success. The unchanged dictionary-license failure oracle now rejects the asset, retains a visible fallback and persistent diagnostic, and permits later valid-kind recovery without erasing failure history: 14 checks / 0 failures.
- F2: The fixed static factory signatures are checked before binding. The unchanged wrong-arity fixture reports degraded with zero factory calls and no script error: 10 / 0. Source inspection confirms each unproven creation gets a distinct pending diagnostic before the factory call, and later calls erase only their own key. An aborted call therefore cannot be made ready by a later success. This call-abort conclusion is source inspection; the unchanged signature oracle now exits at preflight, so it does not separately execute a post-preflight runtime abort. No additional factory ABI policy or unrelated fuzz campaign was introduced.
- F3: Creation inspects actual Visual mesh data, visibility, nonempty surfaces, finite raw vertices/faces and nondegenerate triangles. Empty Visual is rejected by the unchanged oracle: 14 / 0. Reused exact integration evidence also checks null/empty/nonfinite mesh data and non-string metadata; the repaired diagnostic String interface remains compatible with the corrected independent harness. Geometry validation is confined to creation, not transform-only updates.
- F4: Full global transforms are applied to all eight fallback AABB corners for labels. Picking uses the inverse affine transform and retains the unnormalized local ray direction, keeping t comparable with the real-asset path. The unchanged null-factory oracle passes 16 / 0: label actual/expected both (10.67287, 7.7, -1.448521), picked/expected ID both 1. The exact reused integration harness covers induced shear, identity behavior and nearer-real versus farther-fallback ordering under anisotropic scale.

The complete repaired presenter, changed main functions and added integration assertions were inspected. The actual normalized diff was independently reconstructed from the author's preserved original-stage and current product and matched repair.diff exactly. This repair adds no authority, motion, persistence schema, network, sensor, AI or control-chain connection. Original fixed B factory files remain unchanged in product; only copies under this review folder contain the original test mutations.

## Fresh and reused evidence

Fresh private-stage headless runs: import exit 0; corrected independent harness 54/0; original bad-license 14/0, signature 10/0, empty-visual 14/0 and null-factory 16/0. All six processes have recorded argv, cwd, PID, pinned executable SHA256, before/after stage manifests, raw stdout/stderr hashes, exit 0, timeout=false and terminal=true. The original failure and corrected independent harness bytes are unchanged. Original four RED receipts remain exit 1 with 7/3/7/2 failures, respectively.

The fresh independent harness checks actual vertices under composed rotations, translation and nonuniform parent scale, asymmetric pivot retention, nearest world-ray t, misses, kind replacement/removal/recovery, retained mesh/material identities across 25 updates, twelve clear cycles, ten malformed assets, parameter-only export, injection rejection and disconnected viewer controls.

`exact-evidence-reuse.json` verifies 136 integration, 696 editor, 628 persistence and 266 UI-fit assertions against all current product source files in both executing before/after manifests and current retained stages. Each actual receipt, argv/cwd, terminal, exit, executable identity and raw log hash was checked. The B-only 622 harness and complete transitive world/assets/project dependencies match its older executing manifest and retained stage; it preloads the asset library and three geometry modules and does not load the changed A viewer. Broad suites were not rerun.

The reuse audit initially encountered an older receipt schema and then the intentional B unknown-kind ERROR. Both audit failures are preserved in audit-first-attempt-error.txt and are not passing evidence. The final audit verifies the actual older engine_sha256/source_manifest fields and explicitly requires the one bogus_kind error and its test stack; it does not discard diagnostics.

## Integrity and limits

Repair receipt SHA256: 9056113536888d0e24ce92aa9015e0019cb7016cd00ef770bbae78a00b5155e2. Pinned engine SHA256: ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424. Current presenter/main/integration-test hashes match the main's assignment. The author's native completion is actual terminal with exact persisted result text. All 885 main-sealed nonsecret artifacts were hash-checked before review and again afterward. Full product source manifests before/after are equal; zero remaining Godot/Python processes match this assignment's evidence path.

Four inherited Unicode NUL diagnostics occur during fresh import and three during each ordinary fresh test. Reused persistence evidence retains deliberate excessive-exponent and malformed UTF-8 diagnostics. B622 retains its intentional unknown-kind error. Original RED, intermediate errors, erroneous test invocation and the invalid first-attempt 49-check harness are retained and not promoted to passing evidence. Engine-clean remains unsatisfied.

Every Godot execution was headless in the assigned evidence directory with private APPDATA/LOCALAPPDATA. No GUI window, focus, mouse, keyboard, screenshot or display-setting action was used; the human's subsequent background-only instruction is consistent with this scope. Product, old author/reviewer evidence and imported B sources were read-only. No Git, Run, board, service, credential/provider, peer or child effects occurred.

Native visual quality, wheel/camera interaction, GPU performance, physical collision/crossing, causal sensing, PC AI, both control chains, board/system and all 29 formal cards remain not_run. The main alone decides adoption and next work.

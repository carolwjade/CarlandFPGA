# G02 Layout Persistence Independent Review

- Task: `DEEPEYE-IMPLEMENTATION-20261014/v1`
- Work: `A-G02-LAYOUT-PERSISTENCE-REVIEW-20261020-v1`
- Review child/job: `child-ffab680842604466bbb1ead6549b1c11`, instance `deepseek-a-29`
- Responsible main: Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2
- PRODUCT: `.local/deepeye-implementation-a`, head at review start `678e01dd097f326e5bf724dc9db9e6b3e388384d`
- Immutable contract: `DEEPEYE-HUMAN-LOCK-20261014/revision1`; H01-H15 canonical hash `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
- Verdict: **PASS for the bounded headless software-candidate scope only.** No blocking implementation defect was found. This is not G02, formal29, native-UI, product, board, isolation, AI, physical-collision, or dual-H12 acceptance.

## Findings

### LOW-01 - Author manifest mixes raw and Git-clean documentation identities

`competition/deepeye/docs/layout_persistence.md` has actual CRLF bytes, SHA256 `2f796aef1b0f276bea66ca54741dcc1b1c6284d156f6d7301fc9595307897a5c`, and raw Git blob `9313993a5a3a8435a9bd0bce7f4ce94d2d3e8572`. The manifest entry at `.planning/deepeye-resume-20261018/g02-layout-continuation-20261020/author/manifest.json:78-81` records SHA256 for those actual bytes but `git_blob_sha1` `adc8a2abaebd0d1ff283b05ab9b0a9931e2ceb23`, which is the clean-LF object. The main audit already makes this distinction at `.planning/deepeye-resume-20261018/g02-layout-author-handoff-audit.json:14-18`.

Impact is limited to byte/provenance handling: the six candidate SHA256 values and all five GDScript raw blobs match. Publication or later evidence copying must preserve/handle the CRLF documentation bytes explicitly and must not describe the clean-LF blob as the raw worktree object. The author manifest was not edited.

### INFO-01 - Concurrent Save As replacement is a confirmed platform limitation, not a sequential contract failure

The store prechecks the target (`simulator/editor/layout_store.gd:53` and `:84-86`), writes a same-directory temporary file, rereads it, then uses `DirAccess.rename_absolute` (`:87-90`). The documentation explicitly disclaims an atomic concurrent no-overwrite primitive at `docs/layout_persistence.md:67-78`.

The disposable pinned-engine probe `runs/rename-probe-01/stdout.log` returned `RENAME_EXISTING_ERR=0` and changed target bytes to `4e45575c6e` (`NEW\n`) when the destination existed at rename time. This confirms that another actor can race the final precheck and cause replacement on this platform. It does **not** violate sequential Save As: an existing target at entry is rejected and preserved, and no repository or author file was used as the probe target. The implementation does not claim concurrent atomicity. The remaining risk is real and unimplemented; documentation alone is not proof of final save safety under concurrent writers.

### INFO-02 - The tested UI path is real source wiring, but not native or visual acceptance

The actual toolbar buttons are created at `simulator/ui/shell.gd:224-235`, the explicit non-native `FileDialog` and its `file_selected`/`canceled` connections at `:345-354`, enablement in `:517-520`, dialog configuration in `:575-590`, and both callbacks in `:611-674`. This path is source-present and exercised headlessly. It has not been clicked with a mouse, visually laid out, accessibility-tested, or checked at 1080p/1440p and 125%/150% scaling.

### INFO-03 - Private storage does not establish AI or OS confidentiality

The saved representation is geometry-only and excludes `run_state`, link/control data, seed, model, route, resource, and truth fields (`simulator/editor/layout_codec.gd:10-17,32-36,62-109`; `simulator/editor/scene_document.gd:365-420`). The default location is viewer user data (`simulator/editor/layout_store.gd:12-13`). The user may select another explicit local path. No AI whitelist, OS isolation, filesystem sandbox, or proof that another process cannot read the chosen path is established. Such claims remain `not_run`.

## Correctness Review

- **Codec and boundaries:** strict schema/version/contract/requirements/unit fields, unknown/missing-field checks, duplicate object IDs, finite numeric types, exact integer IDs, object/byte/depth limits, kind-specific sizes, cube positions, gate faces/margins, and same-face separation are implemented at `layout_codec.gd:32-36`, `:62-109`, `:111-187`, `:189-252`, and `:286-333`.
- **Filesystem boundary:** bounded read, UTF-8 round-trip check, size recheck after read, parent/absolute-path checks, temp write/flush/reread, and publish error handling are at `layout_store.gd:15-44`, `:46-95`, `:97-104`, and `:110-116`. Production code contains no `ResourceLoader`, `eval`, dynamic `load`, process execution, network, or automatic directory scan.
- **Transaction and semantics:** export/import are in `scene_document.gd:367-420`; import validates before mutation, replaces the original geometry only, resets undo/redo and selection, marks seed unknown and origin as file layout, and never restores run/link/control state. Geometry edits invalidate seed provenance at `:721-729`; original layout packing is at `:741-758`.
- **Existing view path:** the untouched viewer connects `layout_changed` and `gates_changed` at `simulator/viewer/main.gd:69-70`; the persistence suite checks original scene meshes and gate transforms after the handler roundtrip.
- **Dialog state and cancellation:** `_dialog_action` is consumed before work (`shell.gd:611-613`), editability is rechecked (`:619-621`), failed reads/exports/writes do not mutate the document, and cancellation clears the action and reports no change (`:665-674`). The independent flow counterexample added state-change, stale second callback, and post-success cancellation checks; all 11 passed.

## Independent Execution

All engine processes used the pinned executable SHA256 `c8f0a6bc45a19b33541501e57f6f7cd972ab18453743266339d495cbbe846643`, version `4.7.2.stable.official.ed1daf0bf`, with fresh review staging and process-scoped user/cache/TEMP paths. Exit and raw output are under `runs/`.

- `runs/persistence-01`: exit 0, `TESTS checks=618 failures=0`, `RESULT PASS`.
- `runs/editor-01`: exit 0, untouched suite `TESTS checks=696 failures=0`, `RESULT PASS`.
- `runs/smoke-01`: exit 0, `SCENE_SMOKE_PASS document=1 shell=1 file_dialog=1`.
- `runs/flow-counterexample-01`: exit 0, `COUNTEREXAMPLE_FLOW checks=11 failures=0`.
- `runs/rename-probe-01`: exit 0; destination-exists behavior recorded as a limitation.
- `runs/import-origin-01`: exit 0; all six loaded-script/scene origin lines resolve under `stage/counterexample-import-origin-01/simulator`, not PRODUCT.

The 618/696/smoke figures are the reviewer's fresh staged runs, not merely author claims. Expected engine parser warnings for deliberately invalid UTF-8/exponent rejection cases remain in stderr; they are retained and are not treated as passes or failures by themselves.

## Integrity and Scope

The pre-run and post-run pin audits each passed 74/74 at the task pinned head `678e01dd097f326e5bf724dc9db9e6b3e388384d`, with identical six-source, five-dependency, and 48-evidence sections (`evidence/pins-before.stdout.json`, `evidence/pins-after.stdout.json`, exit 0). During finalization, external main commits advanced PRODUCT HEAD to scoped snapshot `a2feee7b40391f60224dad7d603d8dbec0341c1b` (commit time `2026-10-20T01:47:45+08:00`). The latest strict replay has exactly one failure, `product_head`; its other 73 checks pass, the task pinned head is an ancestor, and the scoped six-file/five-dependency diff from the task-pinned head to the snapshot is empty (`evidence/pins-final-strict-02.stdout.json`, `evidence/final-scope-audit-03/stdout.json`). The six actual source hashes remain pinned and the scoped status remains exactly two modifications and four untracked candidate files; scoped `git diff --check` exited 0. No commit, push, service, board, driver, group message, or PRODUCT cache write occurred. The existing PRODUCT `.godot` directory has a 2026-10-15 last-write timestamp and was not created or modified by this review; every reviewed engine run used a staged project.

The original author job `child-9d0281a0ffd54a8c99db1ad653d1d39c` is terminal, and its predecessor timeout/partial failures remain preserved. Review tooling failures are retained in `evidence/reviewer-tooling-failures.md`; none is a candidate failure.

## Not Run / Genuine Limits

- All 29 taskbook cards and H01-H15 remain `not_run`; no G02 operation record or native-UI evidence exists.
- No real mouse/keyboard/FileDialog usability, visual/layout, scaling, accessibility, or screenshot evidence.
- No OS isolation, process containment, AI access test, physical collision, full crossing, route/control, board/Run, service/driver, or dual-H12 evidence.
- Concurrent Save As has no proven exclusive/no-overwrite/atomic primitive; the Windows rename replacement behavior is documented and observed.
- The non-owned mutable `.planning/deepeye-resume-20261018/task_plan.md` changed during review from inspected 16118 bytes / `d3e968c1…` to 16204 bytes / `bb18eab6…`. It is outside the candidate and immutable contract scope; the H01-H15 canonical contract was independently re-verified.
- Production gate remains unavailable and Run/link authority remains unchanged. No fake real-inference, bridge, hardware, or acceptance claim is made.

Main owns adoption and any later formal/native verification.
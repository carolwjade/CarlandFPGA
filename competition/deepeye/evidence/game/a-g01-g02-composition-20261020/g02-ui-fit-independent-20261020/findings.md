# Independent G02 UI-fit review

Task DEEPEYE-IMPLEMENTATION-20261014/v1; work A-G02-UI-FIT-INDEPENDENT-20261020-v1;
job child-11b147871bb64f319d60edc419256d62; agent /root/g02_ui_fit_review_20261020.
Bounded review completed with one medium boundary finding and one low evidence finding.
No blocker/high issue was established in this headless scope. The main owns disposition
and acceptance. This is not an unconditional UI-fit pass.

## M1: Long accepted failure status can consume the central-area margin

Location: competition/deepeye/simulator/ui/shell.gd:271-291, 854-863, 955-957.
The new wrapped ActionStatus Label has no height bound in the bottom VBox, while
_set_file_failure accepts up to 512 characters. In the independent stage, calling
_set_file_failure("review_boundary", "边".repeat(512)) at 1920x1080 produces a
521-character six-line status, increases BottomBand from 110 to 159 pixels, and
reduces the actual central rectangle from 1352x934 (60.897377%) to 1352x885
(57.702546%). The independent probe exits 1 with 15 checks / 1 failure.

This is a direct-helper boundary reproduction. Reachability of a 512-character
Chinese reason through an ordinary current file operation was not established;
the current codec truncates several error inputs more tightly. Do not describe
this as an observed normal file-open failure or native DPI failure. The result
shows that the accepted status bound is not sufficient to guarantee the layout's
60% invariant. Preserve the failing log and have the main decide whether to bound
the visible status height with scroll/details/truncation, then test that boundary.
No product source was changed by this review.

## L1: Author source-pin claim is too broad for focused/RED evidence

Location: author findings.md paragraph beginning "Every owned engine process"
and the following provenance paragraph; author logs/focused/{command,result}.json
and logs/red-focused/{command,result}.json.
The final runner records source pins, but those two saved runs contain neither
source_before_sha256 nor source_after_sha256. The fresh editor696, persistence618
and scene-smoke records do have both. The manifest and source snapshots verify
artifact integrity, not the absent execution-time association for focused/RED.
Narrow the author statement accordingly. The independent focused run here
records all 17 staged source hashes before and after, unchanged, and passes
180 checks / 0 failures; it resolves current candidate focused execution origin,
without retroactively adding provenance to the earlier RED run.

## Verified software evidence

- All 101 author manifest artifact entries match their recorded byte counts and
  SHA-256 values. The author completion receipt records the expected job as completed.
- Candidate project.godot, ui/shell.gd and tests/test_g02_ui_fit.gd match all three
  assignment hashes. All other selected dependencies match the baseline selection;
  all 17 simulator sources are unchanged between this review's before/after audit.
- Full project/shell diff inspected against preserved baseline files whose hashes
  match the responsible main's b45bee841768c9d2c248fd164cf3fd21238c285d selection.
  The baseline content was not freshly extracted with Git in this review; that
  association is recorded rather than overstated. The product ref read during
  review was b45bee841768c9d2c248fd164cf3fd21238c285d. Later main evidence-only HEAD
  movement is independent of these source byte identities.
- Fresh direct pinned Godot 4.7.2 runs: editor import exit 0; focused 180/0 exit 0;
  unchanged editor regression 696/0 exit 0; independent boundary 15/1 exit 1.
  Every engine process terminated normally, without timeout or forced termination.
- Fresh focused measurements reproduce 60.897377% at 1920x1080 and 70.203993%
  at 2560x1440. 1280x720 has positive area/reachability, with no 60% claim.
- Wrapped long side labels, vertical scroll reachability, contained Save/Open
  buttons, final Chinese dialog mode/title, permanent help/action separation,
  and disabled Run/pause/continue pass the focused checks.
- Additional independent checks pass: wheel/right-click input in all four new
  top/bottom gutters leaves camera/document unchanged; an already-open dialog
  remains contained when resizing 2560x1440 to 1280x720; permanent camera help
  survives the long status. The independent probe never invokes product Run.
- Source import cache and runtime resource paths point into this review's stage:
  viewer/main.gd, ui/shell.gd, editor/scene_document.gd, layout_codec.gd, layout_store.gd.
  Stage sources were copied from PRODUCT; generated imports/user/cache/temp/logs
  are confined to this review directory.
- Author persistence 618/0 and smoke exit 0 were reused after their artifacts,
  pins and selected dependencies were verified; these already-passing broad
  checks were not needlessly repeated. Persistence exponent diagnostics trace
  to explicit rejection fixtures at test lines 267/270/289; invalid UTF8 fixtures
  are deliberate. The repeated startup Unexpected NUL diagnostics are separate,
  remain unresolved, and are retained in raw stderr. Clean stderr is not claimed.
- Original RED, invalid FileDialog.get_rect call, and pointer-release test failure
  evidence was read and preserved. This review's initial manifest-key audit error
  is retained in initial-audit-failure.txt and did not touch PRODUCT.

## Scope and acceptance limits

The active generation-2 Desktop director transfer and node-A role/config were
read. Root and PRODUCT canonical requirements arrays independently hash to
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
Contract DEEPEYE-HUMAN-LOCK-20261014/revision1, H01-H15, remains unchanged.

All 29 formal acceptance cards remain not_run, including G02. Headless geometry
does not prove rendered readability, native OS titlebar/DPI/125%-150% scaling,
real input, game quality, full-path visibility, board/control/AI/H12 behavior or
formal product acceptance. No GUI, board, install, service/config/credential,
Git mutation, external messaging, delegation, or product edits occurred.

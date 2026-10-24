# Current PC_DIRECT heartbeat audit

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-PC-DIRECT-CURRENT-REVIEW-20261018-v1`.
Reviewer `/root/pc_direct_review_20261018`; original native job `child-9972ae175d344d20ab92479647dbef00` validated with `execution_allowed=true` before project reads/tests.
Sole director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2.
Product checkout HEAD `b3db473370c6ee4fed476db6fc89f8fdb8c945bd`, including inherited dirty/untracked files recorded in `git-status-before.stdout.log`.

The existing watchdog remains a tested software veto. No actionable defect was reproduced in that component. The complete legitimate PC_DIRECT heartbeat path is absent from the current adopted runtime. This audit does not grant motion or product acceptance. Final decisions belong to the director.

## Concrete integration gaps

1. **There is no production heartbeat owner or receiver-to-watchdog dispatch.** The AST scan of non-test Python sources (excluding evidence) finds zero calls to `PcDirectWatchdog`, `ingest_heartbeat`, or `track_authority_command`. Text scan of Python/GDScript finds only the watchdog definitions. `host_envelope.py:561` validates STATE8 inside `board_response`, but the returned record is static information, not transport authentication or delivery. A live hardware bridge must deliver original bytes/receipt bounds through the authenticated authority-only channel; authority must dispatch STATE8 separately from other ACK/STATE types and serialize watchdog lifecycle. No such adopted adapter is present. Feeding all board responses directly to `ingest_heartbeat` would latch STOP on valid non-STATE8 responses, so dispatch must preserve the existing parser/guard distinction.

2. **No adopted authority joins heartbeat, real observation freshness, command provenance and AI liveness.** `pc_direct_watchdog.py:205` deliberately accepts only an already-authorized command identity/deadline. Neither it nor the envelope validator owns the observation ledger, exact BOOT completion, process identity, or AI lifetime. The current product `ai_pc` directory contains `host_timing/reference.py`; `ai_pc/control_broker` is absent in this checkout. This says nothing about C's independently delivered code/evidence. Taskbook §8.8 (lines 264–274) requires fresh actual FPGA observations and heartbeat, authenticated PC commands, original TTL, AI-failure STOP and a PC_DIRECT source label. These obligations need a real authority adapter and adoption of the separately owned broker path; passing role strings or a synthetic healthy heartbeat cannot satisfy them.

3. **No physics commit loop consumes the veto.** `simulator/viewer/main.gd:11` explicitly declares no physics/drill motion, and `simulator/ui/shell.gd:282–293` keeps Run/continue disabled pending an authority/mode bridge. There is no `_physics_process` in the viewer. Current `simulation/authority/motion/passage_phase.py:133–185` offers a preview, with `motion_grant=False`, `atomic_cas_completed=False`, and explicit owner recheck/CAS obligation. Thus heartbeat timeout, command expiry, AI death or STOP cannot yet be traced into an actual per-step commit/render path. This is a missing runtime, not evidence that the stopped viewer is currently moving unsafely.

The current formal timing entrypoint confirms the gap: `verify_game.py --suite timing` with this audit's explicit evidence directory exits **2**, `status=blocked`, `formal_acceptance=false`. It lists complete authenticated control paths, same-trace TTL/fault cases, disconnect/model crash/restart and physical-board evidence as missing. Its reference-only timing branch runs the watchdog tests; it is not an end-to-end heartbeat test.

## Reconciliation and fresh checks

- Old worker receipt: `.planning/deepeye-implementation-a/app-pc-direct-watchdog-20261015/receipt.json`; previous independent boundary review: `.planning/deepeye-implementation-a/main-review-20261015/review.md`. Both already distinguish a software veto from runtime integration. Director-review `final_receipt.json` remains historical R03/PR evidence and explicitly says formal R03 was not run; no reinterpretation of it was made.
- Current watchdog **40**, STATE8 heartbeat **5**, host-envelope **34** tests: **79 passed**, each process exit **0**. Exact argv, working directory, per-process dependency path, raw stdout/stderr and output hashes are in the three test JSON/log pairs.
- All 27 old regression input hashes were compared with current bytes. Only `integration/motion.py` and `integration/test_motion.py` differ. Watchdog implementation (`7156d067f2c3629c527c0bd82bfdd9670409479e573c77ff077b3a030ccf98f1`), its 40-test file (`49b9861d5c2912154b73e4440710476601c52a1b845d4e198c75941963c34cea`), its documentation, host envelope, STATE8 tests, wire and timing contract are unchanged. The old 189-test regression is historical; it was not claimed as a fresh current full regression. The new 79-test run uses current motion.py through the validator dependency.
- A configuration read restricted to `node_id` and `project_id` confirmed A / fpga-main. No credentials were output. Root and product requirements arrays and the fixed design commit `1011259415a0916054eb580687612580bc1e5f09` recompute to `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`, H01–H15 intact.
- `source-before.json` and `source-after.json` contain hashes of relevant integration/docs/simulation/simulator/tools/AI sources and pinned scope/taskbook inputs. No differences were observed. Final verification and inherited Git status preservation are recorded in `final-verification.json`.

## Proposed next ownership for director approval/assignment

Reserve only these **new** product files for a bounded A authority adapter:

```
competition/deepeye/simulation/authority/pc_direct_runtime.py
competition/deepeye/tests/simulation/test_pc_direct_runtime.py
competition/deepeye/docs/pc_direct_runtime.md
```

First implement the single-owner STOP-by-default authority state machine around the existing watchdog, with separate authenticated board-response and broker/observation inputs, explicit original command deadlines, AI-process-death invalidation, and a fresh veto check immediately before each atomic pose commit. The adapter must not create observations, authenticate supplied booleans, or convert preview/heartbeat health into grants. Missing provenance/timing measurements must remain stopped/unknown. Use caller-owned fixture records to test expiry and invalidation locally, labeling them software fixtures. Keep the existing watchdog, C-owned broker, motion primitives and Godot UI files outside this first assignment. A later separately owned activation step must connect actual authenticated bridge/broker and executor/render entrypoints; that activation is required before any runtime-path completion claim. Director must check active ownership before assigning these names.

No product changes, Git commit/push, services, board operations, OS permission probes, credentials/configuration changes, default ledger writes, new agents or external messages were made. Writes are confined to this audit directory. API21001 was not treated as a blocker. Board measurements, actual FPGA observation path, AI usefulness, full G06/C05/H12 acceptance and all other formal product gates remain **not_run** by this audit.

Reproduce the bounded audit from the owning repository root:

```
.local/venv/Scripts/python.exe -B -X utf8 .planning/deepeye-resume-20261018/pc-direct-review/audit.py
.local/venv/Scripts/python.exe -B -X utf8 .planning/deepeye-resume-20261018/pc-direct-review/entrypoint_probe.py
```

Both driver commands exited 0; the latter intentionally asserts the product timing entrypoint's exit 2 / blocked result. Existing logs are preserved; use a new output directory for any future rerun rather than replacing this evidence.

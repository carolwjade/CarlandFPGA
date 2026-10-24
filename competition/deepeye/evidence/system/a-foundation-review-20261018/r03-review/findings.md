# R03 current-source independent bounded review

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-R03-CURRENT-CHECK-20261018-v1`; agent `/root/r03_review_20261018`. Product HEAD `b3db473370c6ee4fed476db6fc89f8fdb8c945bd`. Director `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. Human contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. All H01-H15 preserved. Native lease validated before project reads; private credentials excluded from this report.

## Exact checklist and harness

Normative R03: `docs/competition/deepeye-2026/taskbook_final.md:340` and task R03 in `execution_plan_final.json` (design v5). A owns ABI/pipeline and B/C independently interoperate. R03 has no prior DAG dependency.

| Required deliverable/behavior | Current implementation and bounded evidence boundary |
|---|---|
| `docs/interface.json`, register table, `tests/vectors`, `tools/pipeline.py` | Present; register table actually lives at `competition/deepeye/docs/registers.csv`. Pipeline default ownership still names `competition/deepeye/registers.csv`, so the director should align ownership claims when assigning register work. No source edit made. |
| ABI3 dual-axis lengths, CRC, endian, session, request type+seq correlation, FAST/STRESS window and sliding-window budgets | `tools/check_interface.py` orchestrates 13 software subprocesses plus BOOT software binding and all-mode schedule verification. It hashes actual docs/integration/tools/tests artifacts. |
| Status must not invoke models; stable work_id deduplication; conflict denial; failed/unknown never replayed | `tools/pipeline.py verify --selftest` runs the actual 24-test `tests/test_pipeline.py`; temporary ledgers, local Git fixtures, no registered product runners. |
| Bounded malformed format/length and seq/epoch rollover vectors | Present local wire/host/contract vectors and checks establish bounded software behavior; end-to-end stateful runtime integration remains declared open. |
| A-owned Godot skeleton (`project.godot`, export presets, minimum startup) | Files exist. R03's Python harness does not start Godot or prove interactive game acceptance. |
| Public quantum/encoding, speed-curvature ROM, summary window, quality, timestamps; independent STRESS vectors `(57,0)` accept, `(58,0)` reject, `(40,40)` accept, `(41,41)` reject, zero-speed nonzero reject | Interface/motion/BOOT reference definitions and local contract-vector tests exist; local vectors are not B/C exact-candidate independent interoperability receipts. |
| Latest-completed bounded mailbox, no starvation under 150/250 ms compute, no old completion overwrite; PL last four TELEM records | Contract declares these behaviors; complete runtime integration remains explicitly open. |
| Freshness/session/profile/epoch, old observations and lost ACK, absolute candidate-ready timing after USB/packing, duplicate ACK/STATE never renew deadline | Reference tests cover clocks, heartbeat/watchdog and envelopes. Real USB/clock/holdover/capture calibration and complete mode-specific runtime are separate gates. |

Actual harness command is `<ROOT>/.local/venv/Scripts/python.exe -B -X utf8 tools/check_interface.py`, cwd an assigned clean checkout's `competition/deepeye`. It calls 11 `integration/test_*.py` programs, `tests/test_boot_profile.py`, then `tools/pipeline.py verify --selftest`. Full mode deliberately returns exit 2/status blocked if all reference checks pass; `--reference-only` merely changes this to a software-reference status. Neither route accepts R03 or enables hardware. The six remaining gate strings come from `docs/interface.json`; they are declarations, not six live acceptance procedures executed by this harness.

## Comparison with prior fixed snapshot

`66aa291d7f01cc3cfefb8c30c4e8ad3aec6547bd` to current HEAD adds exactly three files: certified-motion-path documentation, `certified_path.py`, and its test (954 lines). `source_comparison.json` records exact Git-blob SHA256 and equality for pipeline, pipeline tests, checker, interface, taskbook and plan. Each is unchanged and matches current working bytes. The source snapshot retains inherited dirty `.gitattributes` and all untracked geometry/AI files rather than relabeling them as committed. This R03 harness does not execute the new certified-path tests or inherited untracked geometry/AI suites.

The old `clean-r03-probes-20261016/receipt.json` records 13 exit-zero subprocesses, 245 discovered / 244 pass / one intentional recursion skip; full entrypoint exit 2, R03 not_run, hardware false. It is a comparison baseline, not the fresh result. Fresh results are recorded separately in `receipt.json` after execution.

## Full-gate blockers, unchanged in current interface

1. TRACE payload/codec finalization and independent vectors. Interface says B supplies codec and A accepts; TRACE cannot ENABLE until frozen.
2. Register bitfields, reset semantics and matched HWH integration.
3. Stateful observation history/latest-completed mailbox/request replay and seq/epoch rollover integration.
4. B/C independent byte interoperability on the published exact candidate.
5. Host process ACL isolation and mode-specific end-to-end runtime.
6. Measured USB/clock/holdover/channel calibration and actual IO capture before ENABLE.

Earliest actionable A-owned dependency visible in this checkout: freeze the complete register bitfield/access/reset/timestamp contract and deterministic independent register vectors. `docs/registers.csv` still contains `bitfields_pending_A_freeze` for control/status/shadow/apply/queue/capture fields, `enum_pending_A_freeze` for profile/motion profile, and `semantics_pending_A_freeze` for sample/capture tick words. This local contract work precedes matched-HWH/physical-IO validation and does not require changing OS security or operating hardware. The quality main chooses the implementation assignment and acceptance order.

`RUNNERS = {}` remains true. No default acceptance ledger is created by this review. Frozen design cards remain not_run; a local reference pass does not change them. No services, credentials, product sources, old reports, OS ACLs, real isolation probes or hardware are changed. Disposable symlink/junction containment fixtures in the existing pipeline suite are confined to the owned report's temporary directory; they do not test actual product process isolation.

Exploration note: a read of guessed `tools/verify_r03.py` and guessed `integration/trace_payload.py` failed because those files do not exist. The actual existing checker and trace tests were inspected; no missing file was created or gate weakened.

## Fresh verification result

The assigned clean managed checkout `C:/Users/CarlJade/.codex/worktrees/deepeye-r03-current/FPGA多机协作开发` was verified at the exact current HEAD with empty Git status and the pinned H01-H15 hash. Full `tools/check_interface.py` returned **exit 2 / blocked / R03 not_run / hardware_enable_eligible false**. All 13 software subprocesses returned zero: **245 discovered, 244 passed, one intentional nested-selftest recursion skip**. All recorded artifact hashes match. Before/after manifests match for both this clean checkout and the original product at the postcheck; default ledger remains absent. A subsequent read-only status command also returned zero, and all 29 frozen design-plan cards are confirmed not_run. `receipt.json`, `final_result.json`, `command.json`, per-check raw logs, and source manifests preserve the evidence.

An earlier direct current-product selftest is deliberately retained: exit 1, 24 discovered, two fixture-checkout failures and one recursion skip. Both failed `git checkout` calls reported `Filename too long` under the required deep report-local TEMP. The clean rerun used **process-only** `GIT_CONFIG_COUNT` / `core.longpaths=true` inherited by fixture Git subprocesses; it did not write global/repository configuration, shorten or omit tests, or weaken any gate. Both previously failing fixture tests passed in the fresh full run. All temporary fixtures and output remained in the owned report directory. The earlier result is not relabeled as passing.

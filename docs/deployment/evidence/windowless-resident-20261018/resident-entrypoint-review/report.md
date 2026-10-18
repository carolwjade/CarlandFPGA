# Resident entrypoint independent review

No blocking regression found in the three reviewed files. The change selects an existing same-directory `pythonw.exe` before scheduler access and changes only the resident action executable. The supplied interpreter remains the synchronous stop/wait command. This conclusion is limited to the reviewed source delta and mocked scheduler behavior, not the cause of the original termination or indefinite process survival.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-RESIDENT-ENTRYPOINT-REVIEW-20261018-v1`; reviewer `/root/pc_direct_review_20261018`; original job `child-82517bc5cc0d4d11a9e36083479cc6b2`. Director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. Only this evidence directory was written. The canonical owning-root and product H01–H15 requirements arrays match `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. The separate control-plane worktree has no DeepEye immutable_scope file; the canonical files were used without creating or modifying one there.

Reviewed root: `C:/Users/CarlJade/.codex/worktrees/mesh-authority-bind-repair/FPGA多机协作开发`.

| Read-only source | SHA256 |
| --- | --- |
| `deploy/register-autostart.ps1` | `14ac40aebfb7a31c83c480b39fc2e5db5e28f12e1076680955e0a4e33be99aee` |
| `tests/test_autostart_registration.py` | `709d8fbc6fa8fb2a2927ca0f8c4c2382051be644ed6fee9784768cb8b0073f53` |
| `docs/deployment/WINDOWLESS_RESIDENT_2026-10-18.md` | `d06e81cc23d96d45edfe3a75383c6af9d12d1a6e60c9c59985cd749a744debde` |

All three source hashes stayed unchanged through review. The script hash matches the author's saved GREEN receipt. The exact reviewed HEAD and paths are recorded in `receipt.json`.

The diff from HEAD adds the sibling path/leaf prerequisite and substitutes that path in New-ScheduledTaskAction. Node/task identity, original arguments/quoting, working directory, trigger/settings and existing stop fence remain unchanged. The missing sibling now deliberately rejects an installation that previously could register a console resident. No search/fallback to another interpreter is introduced. Same-directory selection alone is not proof that arbitrary future interpreter pairs share an environment; the saved local comparison establishes the actual tested pair, not every deployment.

## Checks and failure boundaries

- The author's two real PowerShell executions passed with every scheduler cmdlet mocked: selected sibling/unchanged arguments and working directory, and missing sibling rejection before lookup/write/start.
- Eight independent mocked scenarios passed, across five test methods: owned existing task, failing synchronous wait, foreign task, missing config, missing supplied interpreter, missing sibling, sibling path that is a directory, and omitted StartNow.
- The owned-existing scenario confirms execution order `lookup → action/trigger/settings → stop → synchronous supplied-interpreter stub → set → start`; the received `-m fpga_mesh.service --wait-stopped --config <original path> --timeout 20` arguments are preserved. The stub is a harmless `.ps1` fixture; no real service executable is supplied or launched.
- Missing config/interpreter/windowless leaf produces **zero scheduler calls**, including lookup. Foreign task ownership produces lookup only and no stop/mutation/start.
- A nonzero wait-stopped result prevents Set and Start. The existing Stop has already happened by then, as in the inherited source. Therefore “failure before any scheduler side effect” applies to the new missing-sibling prerequisite, **not every later failure in registration**. No broader claim should be made.

`author-mocked-tests.json` records the exact Python command, working directory, raw stdout/stderr and exit 0. Each independent scenario saves its exact PowerShell command, fixture capture, exit and raw output. Initial independent execution had one fixture assertion failure because a `.ps1` stub preserves numeric timeout `20` as an integer while a native executable receives string argv. The original log is preserved. Only that one assertion was corrected/normalized and rerun, passing in `independent-corrected-one.log`; the four already passing methods were not repeated. No product change was needed.

The review driver also preserved two evidence-processing failures: initial scope lookup in the separate worktree, and saved XML bytes declaring UTF-16 although written as UTF-8 text. Neither ran or changed a live task. Saved XML was decoded to Unicode before parsing; source XML bytes remained unchanged. Independent comparison includes namespace, attributes, text and indexed repeated siblings and finds exactly one semantic change:

```
/Task/Actions/Exec/Command
same venv python.exe → same venv pythonw.exe
```

`xml-semantic-independent.json` contains both original XML hashes and the exact change. No other semantic action/settings/identity change was observed in that saved pair.

## Evidence limits

The original saved interpreter-comparison-v2 reports Python 3.12.14, matching venv/base prefixes, runtime import success and service-output redirect success for both executables. I read its raw probe and windowless log; I did not launch additional real interpreter/service actors. Read-only inspection of supervisor/service confirms the supervisor uses `sys.executable` for its worker, keeps its existing no-window/suspended job path and installs service_output around the resident loop. This supports compatibility reasoning but does not prove every startup/failure path or ongoing service survival.

Saved health PID25944 is a historical snapshot, not a fresh health or liveness observation by this review. The source of `0xC000013A` remains unknown. Removing the console entrypoint does not identify who sent a termination signal and cannot guarantee survival of host/platform/process failures. Documentation correctly preserves these limits and does not claim API21001, peer upgrade, product runtime or board recovery.

No live registration, scheduler cmdlet, stop/start/restart, service update, credentials/configuration/ledger mutation, OS ACL probe, hardware operation, external message, new agent or Git write was performed. All 29 full product cards and formal board/runtime/game acceptance remain `not_run` by this review. Main retains acceptance and deployment authority.

# Progress Log

## 2026-09-30

- Read the v0.6 design document in full.
- Loaded `using-superpowers`, `planning-with-files`, `verification-before-completion`, `openai-docs`, `executing-plans`, `using-git-worktrees`, `finishing-a-development-branch`, `test-driven-development` and its test-writing reference.
- Confirmed the repository is a normal checkout with no commits; created `codex/fpga-multi-agent-deploy`.
- Inventoried local runtimes and external dependencies.
- Confirmed Codex CLI `0.159.0`, app-server JSON Schema generation, bundled Python 3.12 and Node 24.
- Fetched DeepSeek official Responses API, Codex integration and changelog documentation.
- OpenAI official web access was not reliable in this environment; recorded the limitation.
- Next: write P0 tests and observe RED.
- Wrote `tests/test_protocol.py` and observed the expected import failure (RED).
- Implemented `fpga_mesh/protocol.py` and package exports.
- P0 GREEN: 7/7 protocol tests pass.
- Next: write P1 tests and observe RED.
- Wrote P1 store/controller tests and observed expected missing-module RED.
- Implemented SQLite inbound/outbox/task persistence and event-driven controller.
- Fixed failure retry so a failed event is attempted once per run and remains recoverable after restart.
- Added local persistent peer transport with offline queue and duplicate delivery handling.
- P1 GREEN: 20/20 tests across protocol, store, controller and transport.
- Next: implement P2 with isolated Codex homes and a fake-supported app-server adapter.
- Generated the app-server JSON Schema bundle for `codex-cli 0.159.0`.
- Added isolated Astra/DeepSeek Codex homes, pool lifecycle, route guard, JSON-RPC, app-server adapter and quota monitor.
- Verified a real isolated DeepSeek app-server thread with `modelProvider=deepseek`, `model=deepseek-flash`, `reasoningEffort=max`; a minimal turn returned `OK` and `turn/completed`.
- Added Feishu six-role routing, delegation checks, shared child identity and recovery-gap handling.
- Added persistent HMAC HTTP peer transport, append-only ownership claim coordination and Git checkpoint/push retry.
- Added an exclusive hardware queue with operation-id idempotency, safe stop and unknown-after-restart handling.
- P2-P5 local implementation tests pass; real Astra subscription, Feishu, Tailscale, GitHub private repo and FPGA hardware remain unavailable and are recorded as skipped.
- Next: CLI/runtime wiring, node templates, local simulation and final deployment status.
- Added CLI/runtime wiring, node templates, deployment scripts and operations documentation.
- Full verification run passed 67/67 tests.
- Local three-node simulation passed with zero idle model calls and successful offline recovery.
- Live DeepSeek app-server verification passed with `deepseek-flash` / `deepseek` / `max` and response `OK`.
- DeepSeek account balance query returned API availability without storing balance amounts.
- Generated `docs/deployment/DEPLOYMENT_STATUS.md`.
- Final full verification passed 67/67 tests; local simulation and live DeepSeek/balance checks passed again.
- Secret scan found no credential material outside ignored local/artifact directories.
- Next: commit the branch and shut down the machine.

## 2026-10-03

- Followed the previous branch and design v0.6; kept fixed six Feishu identities and a dynamic, Astra-controlled child count.
- Added persistent child jobs, local authenticated control, native Codex dynamic tools, MCP/CLI fallback, real app-server invocation, and a per-task Astra effort selector.
- Wrote failing tests before implementing and fixed independent review findings for RPC string IDs, selector interruption, environment isolation, tool-result serialization, and scale/claim concurrency. Added a human-version race test.
- Verified real Astra→DeepSeek delegation (`CHILD_OK`), three concurrent DeepSeek children all at `max`, and one Astra thread moving `low`→`high` with matching persisted metadata.
- Installed A under ignored workspace `.local/deployment` and registered `FPGA-Mesh-Node-A` as a logon task. Diagnosed Task Scheduler's inability to see the prior AppData directory. Background service returned `SERVICE_OK` at `max`; stop/start recovered standby workers and job history.
- Updated operations and deployment status with the unverified native dropdown visual behavior and remaining external gates.
- Next: final full verification, secret scan, commit, and previously requested shutdown.
- Final hardened regression: 116/116 tests pass. Live Astra effort selection again persisted `low` then `high` on one thread; scheduled A service restarted and returned `FINAL_RUNTIME_OK` via DeepSeek at `max` with the one-hour watchdog loaded.

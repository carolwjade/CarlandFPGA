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

## 2026-10-07

- 确认 GitHub 仓库改为公开，绑定本机 `origin`；飞书群当前只有真人，没有六个应用，群 ID 尚待人提供。
- 添加官方飞书长连接的 Astra 入站、双角色出站、去重与持久发送队列；DeepSeek 不监听群。修复人类新指令抢占、跨机项目/来源校验、一个同伴离线不阻塞另一个、签名健康探针和配额预警。
- 完成 B/C 引导脚本、角色指令、队友 Codex 提示和本地配置生成器。密钥仅保存在本地文件，公开仓库采用 fork/PR。
- A 已安装/登录 Tailscale，创建限于 Tailscale 的 Windows 防火墙规则，本地签名健康端点与后台 DeepSeek 派工通过。计划任务改为直接管理 Python，清理旧孤儿进程。
- 全量本地回归 152/152 通过；真实 Astra→DeepSeek 返回 `CHILD_OK`，父 `low`、子 `max`。下一步：远端 GitHub 首推/读回、分发包解包烟测、飞书授权与群 ID 到位后的联调。
- 从飞书桌面端 `FPGA/AI/DEV` 群设置读出 Chat ID `oc_e0de73230fd64dd2da3e52fc781dffb1`；Bots 页面为空，并提示这是外部群，仅接受自定义机器人或允许外部共享的应用机器人。群邀请链接无需提供给应用机器人，且短期过期。
- 全量回归增至 167/167，通过本地 Git 快进认领、失联节点恢复、永久暂停及过期消息等测试。GitHub Desktop 发布 `main`，远端 `git ls-remote` 读回 `88930ff6a33eaad1636514292c888f11ed49abd4`。
- 首次分发 ZIP 的 405 文件 CRC/逐文件 SHA-256 与解包副本 167/167 测试通过。按队友路径从公开 GitHub 克隆 B 节点时发现 Windows Store Python 别名和 PowerShell 参数数组拼接问题；已修复为自动寻找 Codex 捆绑 Python、分别传递参数和值。随后实跑接入脚本生成 B 本地配置并通过 167/167 测试，未提供密钥时保持飞书和直连关闭。可编辑安装生成的 `*.egg-info/` 已加入忽略规则，防止阻碍下一次快进更新。
- 再查飞书开发者后台：企业自建应用创建表单提示默认仅当前组织内部可用且发布需管理员审核；外部群应用机器人还须实际获准外部共享。未把表单可打开误记为六机器人已创建或已入群。

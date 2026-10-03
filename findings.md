# Findings

## Source of Truth

- Design: `docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md`, version v0.6, dated 2026-09-29.
- The design explicitly says P0/P1 can be validated with local test doubles and do not require GitHub, Feishu, credentials, or real hardware.
- P2-P5 require external inputs that are not present in the design file.

## Local Environment

- Codex CLI: `0.159.0`.
- App-server: experimental, supports `stdio://`, `unix://`, WebSocket and JSON Schema generation.
- Bundled Python: `3.12.14`; pip `26.2.1`.
- Bundled Node.js: `v24.19.0`.
- Git: `2.53.0.windows.3`.
- `tailscale`: not found.
- `git-lfs`: not found.
- `docker`: not found.
- Global `~/.codex/config.toml` currently selects `gpt-6-astra` through the local `codex_model_router_v2` provider and must not be modified by this deployment.
- Global `~/.codex/models.json` contains `deepseek-flash` and `deepseek-v4-pro`.
- `codex login status` reports an API-key login, not a verified member ChatGPT subscription login.

## External Inputs Still Missing

- Node-to-member mapping and operating systems for B/C.
- GitHub private repository URL, account ownership and commit identity.
- Feishu group ID, three human member identities and six app credentials.
- DeepSeek billing-account relationship and API credentials for isolated child homes.
- Real Tailscale installation and authentication on all three machines.
- FPGA board model, driver, toolchain, capture interface and test connection.

These values are intentionally left blank in generated configuration.

## Protocol Decisions

- Messages are immutable after persistence; edits create a new revision.
- Idempotency keys are based on the platform event identity where available and on stable content-derived IDs for local events.
- Ownership is append-only and becomes effective only after a remote fast-forward push succeeds and is read back.
- `instance_id` is unique and never reused after reaping.
- Waiting is event-driven; no idle poll may invoke a model.
- Hardware operations are idempotent by `operation_id`; an interrupted operation becomes `unknown` and requires reconciliation before retry.

## Verification Limits

- OpenAI documentation pages attempted on 2026-09-30 timed out or returned HTTP 403 from this environment. The implementation uses the locally generated `codex app-server` JSON Schema for the fixed local CLI version.
- DeepSeek official documentation was fetched successfully on 2026-09-30: `deepseek-flash` is the V4.1 Flash alias, supports reasoning effort `max`, and the Responses API base URL is `https://api.deepseek.com`.
- No real Feishu, Tailscale, GitHub private repository or FPGA operation may be claimed from local tests.

## 2026-10-03 Follow-up: Native parent-child calling

- Current Desktop-bundled Codex is `0.160.0` and this machine now reports ChatGPT login. Astra live turns use `modelProvider=openai` and `gpt-6-astra`; isolated children use `deepseek-flash` / `deepseek` / `max`.
- `thread/start.dynamicTools` exposes five child-control tools to a native Astra turn. A live Astra turn delegated to DeepSeek, waited for the job, and returned the persisted `CHILD_OK` result. Per-thread MCP registration worked at protocol level but the Code Mode tool catalog did not expose it; the CLI/MCP bridges remain fallback interfaces.
- A separate Astra selector turn chose `low` then `high` for simple and complex tasks on one thread; `thread/read.reasoningEffort` reflected each choice. The selector itself costs a GPT call, so a net usage-saving claim still requires a representative comparison.
- The Codex Desktop bottom-right picker could not be visually verified through allowed tooling. The backend metadata evidence does not establish that this current chat's picker changes when an independent background Astra thread changes effort.
- A Windows scheduled task cannot see the AppData installation path created in this execution context, while it can see the workspace. Installing under ignored `.local/deployment` fixed the service: task running, live DeepSeek assignment returned `SERVICE_OK` at `max`, stop/start recovered two standby children and persisted result. Scheduled tasks are triggered at logon, not before login.
- Feishu credentials, B/C machines, Tailscale, GitHub private remote, real FPGA board and quality/usage/time comparison remain external gates.

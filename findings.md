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

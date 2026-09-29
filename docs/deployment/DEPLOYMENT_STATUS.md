# FPGA Multi-Agent Deployment Status

Date: 2026-09-30

Branch: `codex/fpga-multi-agent-deploy`

Source design: `docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.6

## Verified

| Area | Evidence | Result |
| --- | --- | --- |
| P0 protocol | `python -m unittest discover -s tests -v` | 67/67 tests pass |
| P1 local controller | `artifacts/verification/local_simulation.json` | A/B/C processed messages; duplicate produced one dispatch; offline outbox queued and recovered; idle model calls = 0; pending outbox = 0 |
| P2 Codex version | `codex --version` | `codex-cli 0.159.0` |
| P2 app-server contract | `codex app-server generate-json-schema --out generated/codex-app-server/0.159.0` | JSON Schema bundle generated for the pinned local CLI |
| P2 DeepSeek route | `artifacts/verification/deepseek_live_verification.json` | Live app-server turn completed with `model=deepseek-flash`, `modelProvider=deepseek`, `reasoningEffort=max`; response `OK` |
| P2 DeepSeek account | `artifacts/verification/deepseek_balance_summary.json` | Account reports API availability; currency list recorded without balance amounts |
| P3 Feishu protocol | `tests/test_feishu.py` | Six fixed roles, Astra-only subscriptions, human-source checks, duplicate/edit routing, delegation scopes, shared DeepSeek identity, recovery gaps |
| P4 peer transport | `tests/test_http_transport.py` | Local HTTP delivery, HMAC rejection, offline retry |
| P4 ownership | `tests/test_coordination.py` | First append wins; receipt loss queries remote; unavailable remote remains pending |
| P4 Git | `tests/test_git_manager.py` | Task branch checkpoint and retry preserve local commits without force push |
| P4 large artifacts | `tests/test_git_manager.py` | SHA-256 manifest, size and LFS classification verified; Git LFS installation remains skipped |
| P5 hardware | `tests/test_hardware.py` | Exclusive serialization, operation-id idempotency, safe stop, unknown state after restart |

## Skipped External Gates

These items are intentionally left blank because they require a human login,
external credentials, other machines, or physical hardware.

| Gate | Required input | Current state |
| --- | --- | --- |
| Astra subscription login | Each member completes the official ChatGPT login on their own machine | Skipped. Current local login reports an API key and the global provider is a local router; no global config was modified |
| Astra live turn | Valid member subscription or an explicitly approved alternate route | Skipped |
| Feishu event stream | Group ID, three human identities, six app IDs and app secrets | Skipped. Only the deterministic role/router contract is active |
| Tailscale | Installation/login on A, B and C; two-way routes | Skipped. Local HMAC HTTP transport is verified instead |
| GitHub private repository | Repository URL, accounts, author identity, LFS quota | Skipped. Local bare-repository Git behavior is verified instead |
| FPGA board | Board model, driver, toolchain, capture interface and test connection | Skipped. Fake adapter and queue semantics are verified instead |
| Three physical machines | Distinct network locations and member-owned sessions | Skipped |

## Secret Hygiene

- No API keys, Feishu secrets or `auth.json` contents are committed.
- Generated child homes contain only `config.toml` and `models.json`; credentials come from `DEEPSEEK_API_KEY`.
- The live verification report records route metadata and response text, not credentials or account balance amounts.
- `.local/`, `artifacts/`, logs and SQLite state are excluded from Git.

## Verification Command

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\verify-all.ps1 `
  -Python "C:\Users\CarlJade\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  -Output "artifacts\verification"
```

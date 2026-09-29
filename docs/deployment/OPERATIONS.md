# FPGA Mesh Operations

## Per-node Inputs

| Input | Storage |
| --- | --- |
| Node ID and peer URLs | `deploy/configs/node-*.toml` |
| Shared peer secret | environment variable named by `security.secret_env` |
| DeepSeek API key | `DEEPSEEK_API_KEY` on the child-instance machine |
| ChatGPT subscription login | official Codex login flow in the Astra Codex Home |
| Feishu app secrets | local credential store; config stores only a reference |
| GitHub remote and author | local Git config or node deployment config |
| FPGA toolchain | A-machine local configuration; never committed |

## Start and Stop

```powershell
pwsh -File deploy\install.ps1 -Node A
pwsh -File deploy\run-node.ps1 -Node A -Config deploy\configs\node-a.toml
```

The process is event-driven. When there is no actionable message, the
controller does not create a model request. A stopped process keeps its SQLite
inbox and outbox for recovery on restart.

## Verification Layers

1. Protocol/unit tests prove deterministic behavior.
2. `simulate` proves three local nodes, duplicate handling and offline retry.
3. `live-check-deepseek` proves the actual DeepSeek app-server route and `max` effort.
4. Feishu, Tailscale, GitHub and FPGA checks are separate live acceptance gates.

Do not mark layer 3 or 4 as passed from a local test double or from a model
display name. Record skipped external checks as `SKIPPED`, not `PASS`.

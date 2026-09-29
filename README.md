# FPGA 三机多 Agent 控制器

本仓库实现 `docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md`
中可在一台机器上验证的 P0-P5 控制平面。模型、飞书、Tailscale、GitHub
私有仓库和 FPGA 板卡属于外接系统，缺少凭据或硬件时不会伪造通过。

## Quick Start

```powershell
$py = "C:\Users\CarlJade\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -m unittest discover -s tests -v
& $py -m fpga_mesh.cli simulate --root .local/sim --output artifacts/local_simulation.json
& $py -m fpga_mesh.cli init-configs --output deploy/configs
```

DeepSeek 真实路由检查只在 `DEEPSEEK_API_KEY` 已通过环境变量注入时执行：

```powershell
& $py -m fpga_mesh.cli live-check-deepseek `
  --root .local/live-check `
  --output artifacts/deepseek_live_verification.json
```

## Runtime

- `fpga_mesh.protocol`: 版本化消息、任务所有权、委托和硬件操作模型。
- `fpga_mesh.store`: SQLite 事件、收件箱、发件箱和任务版本。
- `fpga_mesh.controller`: 只对有新输入的事件启动模型回合，空闲等待不轮询。
- `fpga_mesh.codex`: 隔离 Codex Home、`deepseek-flash` / `deepseek` / `max` 路由守卫。
- `fpga_mesh.pool`: 默认两个待命子实例、动态扩缩、回收身份不复用。
- `fpga_mesh.gateway`: 仅在收到可操作消息后连接 app-server。
- `fpga_mesh.feishu`: 六个固定身份、人类来源校验、委托和恢复缺口。
- `fpga_mesh.http_transport`: HMAC 校验的节点间 HTTP 收发与离线补发。
- `fpga_mesh.coordination`: 追加式认领、普通快进语义和回执丢失核对。
- `fpga_mesh.git_manager`: 任务分支、检查点、推送失败保留本地提交。
- `fpga_mesh.hardware`: 独占实验队列、`operation_id` 幂等和状态不明恢复。

## Deployment

1. 复制 `deploy/configs/node-*.toml`，填写本机节点、Tailscale URL 和非敏感引用。
2. 将 `FPGA_MESH_SHARED_SECRET` 和 `DEEPSEEK_API_KEY` 放入本机凭据存储或进程环境，不写入 Git。
3. 每个成员在自己的机器完成 ChatGPT 官方登录；子实例使用独立 DeepSeek API 账户关系。
4. 安装并登录 Tailscale，确认 A-B、A-C、B-C 双向可达。
5. 配置 GitHub 私有仓库、提交身份和 Git LFS；仓库 URL 与账号只写本地配置。
6. A 机连接并配置 FPGA 工具链，启用 `hardware_enabled = true`。
7. 启动节点：

```powershell
pwsh -File scripts\run-node.ps1 -Node A -Config deploy\configs\node-a.toml
```

所有 `*.local`、`.local/`、`artifacts/` 和凭据文件均被 `.gitignore` 排除。

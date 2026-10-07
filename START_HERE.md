# 给 B/C 队友

把本 ZIP 和 [deploy/TEAMMATE_PROMPT.md](deploy/TEAMMATE_PROMPT.md) 交给各自的 Codex 会话。说明自己是 B 还是 C；Codex 将运行 `deploy/Join-FPGAMesh.ps1`，从公开仓库同步最新版，并完成各机本地配置。

公开 ZIP **没有** DeepSeek API key、飞书应用 Secret、跨机 HMAC 密钥或 ChatGPT 登录信息。成员在本机准备密钥文件并完成自己的网页登录/飞书授权。群 `FPGA/AI/DEV` 的 ID 已内置为 `oc_e0de73230fd64dd2da3e52fc781dffb1`；A 当前 Tailscale 地址是 `100.121.238.56`，队友获得各自 100.x 地址后互填另外两台的 URL。无法完成的授权会保留为未验收项，不影响已完成的本地工作。

仓库：<https://github.com/carolwjade/CarlandFPGA>。公开克隆不等于写权限，B/C 默认使用自己的 fork 和 PR。

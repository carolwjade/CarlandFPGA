# 给 B/C 队友

这是**多机协作 ZIP**，与 `pynq-z2-single-node` **单机技能 ZIP** 分开。把本 ZIP 和[队友 Codex 提示](deploy/TEAMMATE_PROMPT.md)交给各自的 Codex 会话，说明本机是 B 还是 C。Codex 从解压目录运行 `pwsh -NoProfile -File deploy/Join-FPGAMesh.ps1 -Node B`（C 机改 C），脚本同步公开仓库、尝试安装缺失工具、配置本机主从与跨机服务，并逐项产生真实验收证据。单机技能需要时另从技能 ZIP 安装，不影响多机接入。

每个新飞书身份先发布并加入 `FPGA/AI/DEV`，再由入口脚本用该身份**发送一条入群自测消息，并读回同一条消息**。两个身份分别通过才报告六角色中的本机两角色已上线；失败会留下本机回执供重试，不把网络/权限失败误报为成功。DeepSeek 只在此部署检查中读取一次，不开常驻群监听。

公开 ZIP **没有** DeepSeek API key、飞书应用 Secret、跨机 HMAC 密钥或 ChatGPT 登录信息。成员在本机准备密钥文件并完成自己的网页登录/飞书授权。群 `FPGA/AI/DEV` 的 ID 已内置为 `oc_e0de73230fd64dd2da3e52fc781dffb1`；A 当前观察到的 Tailscale 地址是 `100.121.238.56`，使用前仍应重新向 A 核验。队友取得各自 100.x 地址后互填另外两台的 URL。授权暂缺时脚本继续可独立完成的步骤，输出本机 `setup-status.json` 和 `NEXT_STEPS.md`，补齐后原命令重跑；具体真人操作见[人工步骤](deploy/HUMAN_STEPS.md)。

仓库：<https://github.com/carolwjade/CarlandFPGA>。公开克隆不等于写权限，B/C 默认使用自己的 fork 和 PR；自动认领未指定负责人的共享任务还需仓库所有者给予上游 collaborator 权限。

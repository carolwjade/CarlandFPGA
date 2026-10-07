# CarlandFPGA 三机协作控制器

本项目把三位成员各自的 Codex/ChatGPT 订阅用作 Astra 主 Agent。每台电脑有由该 Astra 自主调度的 DeepSeek V4.1 Flash 子实例池，默认两个待命，实际数量可伸缩；子实例工作回合固定最高 `max` 推理档位。六个飞书角色分别是三位 Astra 与每机一个共用的 DeepSeek 形象。只有 A 机接板卡，B/C 通过同伴消息提交方案并获取实测结果。

公开源码仓库：[carolwjade/CarlandFPGA](https://github.com/carolwjade/CarlandFPGA)。公开克隆不等于写入权限；其他成员默认在自己的 fork 上提交并向此仓库发 PR。API 密钥、飞书应用 Secret、跨机共享密钥和各机 SQLite 状态都只保存在本机被忽略的 `.local/` 路径。

队友把 [分发提示](deploy/TEAMMATE_PROMPT.md) 和分发 ZIP 交给自己的 Codex 会话。安装入口是 [Join-FPGAMesh.ps1](deploy/Join-FPGAMesh.ps1)，可克隆仓库、建立依赖环境、生成本地配置、注册开机任务，并在成员授权后注册本机两个飞书应用。授权、群 ID、共享网络、GitHub fork 登录和板卡工具链仍须由对应的人/电脑提供；程序不会把本地模拟写成线上验收。

本机回归：

```powershell
& .local\venv\Scripts\python.exe -m unittest discover -s tests -q
```

详细操作和逐项验收见 [运行说明](docs/deployment/OPERATIONS.md) 与 [部署状态](docs/deployment/DEPLOYMENT_STATUS.md)。设计依据见 [多 Agent 设计稿](docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md)。

# CarlandFPGA 三机协作控制器

本项目把三位成员各自的 Codex/ChatGPT 订阅用作 Astra 主 Agent。每台电脑有由该 Astra 自主调度的 DeepSeek V4.1 Flash 子实例池，默认两个待命，实际数量可伸缩；子实例工作回合固定最高 `max` 推理档位。六个飞书角色分别是三位 Astra 与每机一个共用的 DeepSeek 形象。只有 A 机接板卡，B/C 通过同伴消息提交方案并获取实测结果。

交付分为**两个独立 ZIP**：多机协作包用于 B/C 自动接入 GitHub、Tailscale、飞书和本机主从 Agent；[pynq-z2-single-node 技能](https://github.com/carolwjade/CarlandFPGA/blob/main/skills/pynq-z2-single-node/SKILL.md)包仅包含单机 PYNQ-Z2 开发流程，可用包内 `skills/pynq-z2-single-node/Install.ps1` 独立安装。单机技能覆盖本机预检、RTL/仿真、Vivado 构建、实板证据及与三机控制器兼容的交接清单，不依赖三机服务；使用及验收边界见[单机运行说明](https://github.com/carolwjade/CarlandFPGA/blob/main/docs/deployment/SINGLE_NODE_PYNQ_Z2.md)。

公开源码仓库：[carolwjade/CarlandFPGA](https://github.com/carolwjade/CarlandFPGA)。公开克隆不等于写入权限；其他成员默认在自己的 fork 上提交并向此仓库发 PR。API 密钥、飞书应用 Secret、跨机共享密钥和各机 SQLite 状态都只保存在本机被忽略的 `.local/` 路径。

队友把[分发提示](deploy/TEAMMATE_PROMPT.md)和**多机协作 ZIP**交给自己的 Codex 会话。入口 [Join-FPGAMesh.ps1](deploy/Join-FPGAMesh.ps1) 会尝试安装缺失工具、克隆仓库、建 GitHub fork、创建本机依赖与配置、注册两个飞书应用、逐身份发信读回、真实验证主从调用，并在登录与密钥就绪后注册常驻任务。每次输出本机 `setup-status.json` 与 `NEXT_STEPS.md`；外部授权暂缺时继续独立步骤，补齐后重跑。对应真人的详细流程见[人工步骤](deploy/HUMAN_STEPS.md)。群 ID 已由 A 机取得并内置；飞书实名认证/发布/入群、三方密钥和账号登录仍由各成员完成，仓库所有者须授予上游写权限才可自动认领未指派共享任务。

两个 ZIP 均从**已提交且干净**的 Git 文件生成，各自附 `MANIFEST.json`、修订号和逐文件 SHA-256：

```powershell
python -m fpga_mesh.distribution --profile mesh --output artifacts/CarlandFPGA-mesh.zip
python -m fpga_mesh.distribution --profile pynq-skill --output artifacts/pynq-z2-single-node.zip
```

本机回归：

```powershell
& .local\venv\Scripts\python.exe -m unittest discover -s tests -q
```

详细操作和逐项验收见 [运行说明](docs/deployment/OPERATIONS.md) 与 [部署状态](docs/deployment/DEPLOYMENT_STATUS.md)。设计依据见 [多 Agent 设计稿](docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md)。

# CarlandFPGA 三机协作控制器

本项目只有两个项目级技能：[fpga-multi-node](.agents/skills/fpga-multi-node/SKILL.md) 管理协作、模型、交接与恢复；[pynq-z2-single-node](.agents/skills/pynq-z2-single-node/SKILL.md) 管理设计、工具、metadata 与实板方法。两者统一放在项目 `.agents/skills`，分 A 主机和 B/C 共用客机两个角色 ZIP；按既有 node_id 安装，根 AGENTS 配置全部项目新会话入口。版本 2026.10.13.3 的经验含真实 metadata/BRAM 修复，安装同时清理旧全局副本与可发现备份；凭据、状态和运行服务保留。

本项目把三位成员各自的 Codex/ChatGPT 订阅用于 GPT 主会话。独立任务自动建立会话，模型与推理深度按任务选择；本机所有主会话共享原 Astra 飞书身份。执行工作优先交给指定 API key 的 DeepSeek Flash，始终为最高 `max`；没有默认数量，按需启用与回收。特殊需要保留 GPT 原生 subagent 入口，两入口共享任务去重和文件所有权账本。决策、验收、重难点、关键优化、评估由质量主模型完成。全部 DeepSeek 实例共用本机 DeepSeek 群身份，六个群角色及权限不变。只有 A 机接板卡。

GPT 主会话与原生角色均使用 Codex 官方 `openai` 通道。双击 [更新官方模型](deploy/更新官方模型.cmd)，再点击页面的“更新官方模型”，即可重新读取官方目录、推理档位及新模型的原生入口；`official-latest` 跟随官方默认。更新失败保留旧目录、角色和正在执行的任务，不修改账号凭据。新模型须已由官方向当前账号/客户端开放，原生角色定义在新加载的会话生效。十个旧角色的实际迁移及双入口验收见 [官方模型路由验收](docs/deployment/OFFICIAL_MODEL_ROUTING_ACCEPTANCE_2026-10-10.md)。

运行控制器 ZIP 与技能 ZIP 分开。两个角色包都只提供这两个技能，B/C 保留独立设计/仿真/构建与证据工具，去掉物理上传入口；A 保留实板工具。技能的共同清单工具只有一个来源，按需引用；安装及清理见 [项目内升级](.agents/skills/fpga-multi-node/INSTALL.md)。

公开源码仓库：[carolwjade/CarlandFPGA](https://github.com/carolwjade/CarlandFPGA)。公开克隆不等于写入权限；其他成员默认在自己的 fork 上提交并向此仓库发 PR。API 密钥、飞书应用 Secret、跨机共享密钥和各机 SQLite 状态都只保存在本机被忽略的 `.local/` 路径。

队友把[分发提示](deploy/TEAMMATE_PROMPT.md)和**多机协作 ZIP**交给自己的 Codex 会话。入口 [Join-FPGAMesh.ps1](deploy/Join-FPGAMesh.ps1) 会尝试安装缺失工具、克隆仓库、建 GitHub fork、创建本机依赖与配置、注册两个飞书应用、逐身份发信读回、真实验证主从调用，并在登录与密钥就绪后注册常驻任务。每次输出本机 `setup-status.json` 与 `NEXT_STEPS.md`；外部授权暂缺时继续独立步骤，补齐后重跑。对应真人的详细流程见[人工步骤](deploy/HUMAN_STEPS.md)。群 ID 已由 A 机取得并内置；飞书实名认证/发布/入群、三方密钥和账号登录仍由各成员完成，仓库所有者须授予上游写权限才可自动认领未指派共享任务。

角色 ZIP 从干净、已提交、跟踪的源码生成，带完整 revision、版本和逐文件 SHA-256。根 .agents/skills 是 A 版；客机包由 packaging 中两个角色模板与共同来源生成，不把 A 角色复制到 B/C。新版只在项目新会话生效。

```powershell
python -m fpga_mesh.distribution --profile mesh --output artifacts/CarlandFPGA-mesh.zip
python -m fpga_mesh.distribution --profile project-skills-a --output artifacts/skills-2026.10.13.3-a.zip
python -m fpga_mesh.distribution --profile project-skills-bc --output artifacts/skills-2026.10.13.3-bc.zip
```

本机回归：

```powershell
& .local\venv\Scripts\python.exe -m unittest discover -s tests -q
```

详细操作和逐项验收见 [运行说明](docs/deployment/OPERATIONS.md) 与 [部署状态](docs/deployment/DEPLOYMENT_STATUS.md)。设计依据见 [多 Agent 设计稿](docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md)。

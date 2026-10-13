# FPGA Mesh 部署与运行

多机任务统一使用项目根的 [fpga-multi-node 技能](../../.agents/skills/fpga-multi-node/SKILL.md)。A 安装主机包，B/C 使用同一个客机包并依据既有 node_id 安装。根 AGENTS 将它设为全部项目会话入口。身份、会话/派工、静默在场、等待与恢复见技能 [协议](../../.agents/skills/fpga-multi-node/references/protocol.md)；代码/证据/板卡交接见 [交接闭环](../../.agents/skills/fpga-multi-node/references/handoff.md)。这里仅保留部署命令，不重复协作指导。

## 安装与更新入口

新节点部署使用多机运行包及 `deploy/TEAMMATE_PROMPT.md`：

```powershell
pwsh -NoProfile -File deploy/Join-FPGAMesh.ps1 -Node B
```

C 改 `-Node C`。原脚本保留本机登录、密钥引用和同伴地址；输出 `.local/deployment/node-<节点>/setup-status.json` 与 `NEXT_STEPS.md`。云端授权和账号步骤见 [人工步骤](../../deploy/HUMAN_STEPS.md)。飞书每机既有两个应用按各自真实发信/读回核验；机器人要发布并加入目标群，DeepSeek 不开常驻群监听。Webhook 不替代 Astra 人类指令入口。

**已接入节点**走 [原地更新](IN_PLACE_UPDATE_2026-10-11.md)，先 CheckOnly，保留本地补丁、配置、凭据、状态与原服务。不要重新 Join 或用旧远端覆盖新本地源码。

协作技能独立于运行包，以两个 profile 从已提交源码生成：

```powershell
python -m fpga_mesh.distribution --profile mesh-skill-a --output artifacts/fpga-multi-node-host-a.zip
python -m fpga_mesh.distribution --profile mesh-skill-bc --output artifacts/fpga-multi-node-client-bc.zip
```

解压对应包，按包内 `INSTALL.md` 使用现有 Python 执行 `scripts/install.py --project-root <原项目> --node <本机>`。它只安装项目技能与 AGENTS 入口，不重启控制器。PYNQ 单机工具仍独立，B/C 不能安装 A 的板卡上传包。

## 常驻服务诊断

本机配置为 `.local/deployment/node-<a|b|c>/node-<a|b|c>.toml`；原计划任务为 `FPGA-Mesh-Node-<A|B|C>`。监督器/工作进程独占锁，Windows Job Object 清理子进程树，程序退避恢复。当前 PID 用 health 读回；node 目录中的 `supervisor.json`、`service.log` 保存现场。

```powershell
Get-ScheduledTask -TaskName 'FPGA-Mesh-Node-A' | Select-Object State
& .local/venv/Scripts/python.exe -X utf8 -m fpga_mesh.project_cli health
& .local/venv/Scripts/python.exe -X utf8 -m fpga_mesh.project_cli session_list
```

模型目录只读刷新用 `fpga_models_refresh` / `project_cli models_refresh` 或 `deploy/更新官方模型.cmd`；真实访问看完成回合。Astra 文件权限只读审计：

```powershell
& .local/venv/Scripts/python.exe -X utf8 -m fpga_mesh.feishu_permissions --config <既有配置>
```

凭据、SQLite 和私人硬件标识不公开。异常维护按技能 [实际问题处理](../../.agents/skills/fpga-multi-node/references/recovery.md) 定位；不为技能安装执行停服/故障注入。阶段结束保留常驻监听，程序等待不调用模型。历史部署记录保留原时间和证据，不当作当前节点验收。

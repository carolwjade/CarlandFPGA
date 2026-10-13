---
name: pynq-z2-single-node
description: Use when developing or verifying PYNQ-Z2 FPGA work on client node @NODE@ without physical board access, including RTL simulation, Vivado reports, Git handoff, and review of A's board feedback.
---

# PYNQ-Z2 单机开发：客机节点 @NODE@

本包安装到节点 @NODE@。先读取同目录 `client-role.json`，确认 `node` 为 `@NODE@` 且 `board_access` 为 `false`；若机器身份不符，改用对应客机包。该节点可独立设计、仿真、综合和实现，但不连接、上传、配置或声称测过物理 PYNQ-Z2。只有 A 机上板。课题初稿中的器件、链路速率与指标都是候选，先按当次任务确定验收条件。

## 本机开发

1. 在 CarlandFPGA 仓库的节点 @NODE@ 功能分支工作。记录任务 ID/版本、输入输出、时钟/复位、实际本机工具版本和目标器件。运行 `python <skill-dir>/scripts/preflight.py`；它只发现 Vivado/ModelSim 路径，`board.status=not_checked` 不代表硬件可用。
2. 用独立黄金模型、可重放激励和真实日志验证 RTL。若本机有 Vivado，可保存综合、实现、DRC、未约束路径、利用率和实现后时序报告；若无工具，将该阶段记为 `blocked` 或 `not_run`。需要板级资料时读 [PYNQ-Z2 参考](references/pynq-z2.md)；任务选择随钻测井链路时再读 [候选检查](references/telemetry-option.md)。
3. 保存源文件、约束、测试脚本、可公开的原始日志和必要的 `.bit/.hwh` 对应关系。仓库忽略 `logs/`、`*.log` 和 `artifacts/`，供交接的日志应保留原始字节并放到任务目录内的 `.txt` 文件，再确认 Git 实际跟踪。仿真、综合、实现和 A 机板测分别记状态；客机的硬件阶段始终是 `blocked` 或 `not_run`，不得因存在 bitstream 记为 `passed`。

## 本机证据与协作入口

按 [本机清单工具](references/handoff.md) 生成并核对代码、日志与文件哈希。多机派工、PR 与 A 板测反馈统一使用项目根 `.agents/skills/fpga-multi-node/SKILL.md` 的客机入口；本技能仅维护单机设计、工具和证据生成。

安装本包不会启用三机控制器的硬件队列，也不向客机提供 `board_run.py`。`Install.ps1` 仅安装本技能；多机控制器另由其部署包安装。

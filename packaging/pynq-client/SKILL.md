---
name: pynq-z2-single-node
description: Use for PYNQ-Z2 FPGA development on client B or C, including RTL and CDC verification, Vivado builds, real metadata fixtures, test preparation and reading host A's board evidence.
---

# PYNQ-Z2 单机开发：客机 B/C

本包供 B/C 共用，先读 [角色声明](skill-role.json)，以既有 node_id 确认本机 B 或 C、board_access=false。本机独立设计、仿真、综合、实现和准备板测；只有 A 连接、上传、复位或操作物理板卡。设计目标由当次任务决定，初稿中的器件、速率、压缩和应用指标都是候选。

1. 记录任务/版本、文件归属、完整源码 SHA、器件、接口、时钟/复位和验收条件。运行 `python -X utf8 <skill-dir>/scripts/preflight.py`；它只发现路径，不能当作工具运行或板卡检查。按需读 [工具链](references/windows-toolchain.md)、[板卡资料](references/pynq-z2.md)。
2. 建立独立黄金模型与可重放激励，保留真实 RTL 回归日志。覆盖边界、背压、FIFO 满空及设计要求的协议字段；跨域按同步释放、单侧复位策略与 FIFO busy 契约验证。仿真不替代 CDC/RDC 或板上证明。
3. 实际有 Vivado 才运行综合、实现和 bitstream，保存命令、版本、约束、资源、DRC、未约束路径与实现后时序。成对 `.bit/.hwh` 保留同次构建与哈希；缺工具为 blocked，未安排为 not_run。
4. metadata 修复使用 A 返回的真实 ip_dict/mem_dict 与完整 HWH 制成 fixture，按 [metadata 与实板流程](references/board-verification.md) 校验 BRAM 身份、地址和拒绝条件。mock 通过不能当作真实 parser 兼容。计划明确写入范围、原值快照、复位保持和失败恢复，让 A 审阅执行。
5. 本机硬件阶段保持 blocked/not_run；读取 A 反馈后将它作为 A 的测量证据引用。新源码或输入需要新操作与清单，不能继承旧 head 板测通过。

清单、原始字节与阶段状态统一见 [共同证据规范](../fpga-multi-node/references/handoff.md)；唯一工具为 `.agents/skills/fpga-multi-node/scripts/handoff.py`，不依赖运行服务。PR、派工和 A 反馈回读统一见 [多机技能](../fpga-multi-node/SKILL.md)。本客机包没有 board_run/board_probe 或物理依赖；[安装方法](INSTALL.md)只在本项目生效。

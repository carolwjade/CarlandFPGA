---
name: pynq-z2-single-node
description: Use for PYNQ-Z2 FPGA development on host A, including RTL and CDC verification, Vivado builds, PYNQ metadata compatibility, trusted uploads, BRAM tests and physical evidence collection.
---

# PYNQ-Z2 单机开发：主机 A

本技能的 A 版是项目内唯一物理板卡入口。先读 [角色声明](skill-role.json)，核对本机既有 node_id；B/C 使用无板卡入口的共用客机版。本地设计与证据工具可独立运行，无需启动多机服务。初稿的 AD7606、300 bps、压缩率、延迟、Ryzen AI 和最终应用仍由本次任务选择，不能当作既定指标。

## 一次开发迭代

1. 固定任务/版本、源码提交、文件归属、器件、接口、时钟/复位及验收条件。读取实际 Git 状态，保留本地改动；记录工具与镜像的本轮版本。
2. 用 `python -X utf8 <skill-dir>/scripts/preflight.py` 查本地工具路径，必要时传 `--vivado-home`、`--modelsim-home`。它不运行工具，`board.status=not_checked` 不证明板卡连接。按需读 [工具链](references/windows-toolchain.md) 和 [板卡资料](references/pynq-z2.md)。
3. 用独立黄金模型、可重放激励和真实日志验证 RTL；按设计覆盖边界、背压、FIFO 满空、CRC/序号。跨时钟/复位遵守各域同步释放与 FIFO 契约，检查单侧复位、停止时钟、释放顺序和传输中重启；XPM rst/busy 门控须按实际版本核对。仿真不证明亚稳态或板上行为。
4. 使用现有 Vivado Tcl/仿真器复现综合、实现与 bitstream，保存命令、版本、约束、资源、DRC、未约束路径、实现后时序及适用的 recovery/removal。PYNQ 的 `.bit/.hwh` 必须来自同一构建；综合估计不能替代实现结果。
5. 上板前按 [metadata 与实板流程](references/board-verification.md) 核对真实 parser、HWH、地址和安全清理。物理独占覆盖准备、上传、加载、执行、采集与清理；实际结果逐阶段记录，缺条件为 blocked，本轮没安排为 not_run。

## 上传和实际执行

优先复用已固定的 SSH 主机公钥和本机专用密钥。首次引导才使用 `scripts/board_run.py` 经已登录的 USB 串口固定板卡公钥，并选择直连以太网 IPv6 链路；依赖见 [安装说明](INSTALL.md)。传 `--script` 只选择实际运行文件，先审阅其副作用及清理方案。默认上传 `board_probe.py` 是板端 Python 烟测，不能作为 BRAM/RTL 功能结论。凭据留在原存储，不写 Git/ZIP/日志。

上传前后核对原始字节 SHA-256；板端用实际 PYNQ 虚拟环境、正确权限和工作目录。metadata 异常先只读采集，复现真实 schema 后修改；不能反复加载或试写地址。未知副作用先查原 operation，主模型另定恢复工作；恢复失败保留原数据、错误和安全状态。

## 证据和协作

请求、清单工具与阶段状态统一见 [共同证据规范](../fpga-multi-node/references/handoff.md)，唯一 `handoff.py` 在多机技能中，可用 Python 标准库独立运行。派工、PR 反馈和 B/C 回读只维护在 [多机技能](../fpga-multi-node/SKILL.md)，本技能维护设计与物理方法。安装技能不启用 `hardware_enabled`。

遇到相同现场问题再读 [metadata 与实板流程](references/board-verification.md)；只有任务选择遥测链路时才读 [候选方案](references/telemetry-option.md)。历史成功只证明当时记录的测量范围，不代替本轮现场。

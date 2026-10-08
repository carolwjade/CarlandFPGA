# PYNQ-Z2 单机 FPGA 开发技能设计（2026-10-08）

## 目标和边界

在三机协作仓库内交付可独立安装的 pynq-z2-single-node Codex 技能。它服务于一台电脑上的 FPGA 设计、验证、Vivado 构建与 PYNQ-Z2 板测，并用可校验的交接清单与现有三机控制器协作。技能不依赖三机服务才能使用；三机服务当前也不会因为安装技能而自动获得板卡执行能力。

用户提供的选题初稿和两个 ZIP 是参考材料。AD7606、300 bps、差分/RLE/字典压缩、4:1～8:1、微秒级延迟、Ryzen AI 和数字孪生都是可选项目参数或后续验收目标，不预设为实现要求。本轮不生成未定型的 RTL、采集板接口或演示结果。

## 结构

- skills/pynq-z2-single-node/SKILL.md：从需求冻结到 RTL、仿真、综合实现、板测和交接的工作流入口。
- references/pynq-z2.md：官方板卡器件、PYNQ 镜像/Overlay 兼容性、约束文件与工具选择。器件为 XC7Z020-1CLG400C；Vivado part 为 xc7z020clg400-1。PYNQ-Z2 使用仍支持该板的 3.1.1 镜像；PYNQ 4.0 已移除该板支持。工具与镜像版本在每次实际执行前重新核实。
- references/telemetry-option.md：将附件中的低速回传、采样、压缩、数字孪生方法转成条件检查，不复制附件技能或其自动触发策略。
- scripts/preflight.py：只读探测本机 Vivado、ModelSim 和板卡状态，板卡未实测时标为 not_checked。
- scripts/handoff.py：建立/核验 JSON 交接清单。输入 request 字段与 HardwareRequest 对齐；文件必须位于指定根目录，列出大小与 SHA-256。阶段结果区分 passed、failed、blocked、not_run；passed 至少附带可哈希的真实日志。哈希证实文件未变，不代替对测试内容的技术审阅。
- tests/test_pynq_z2_single_node.py：覆盖路径越界、缺失/篡改文件、阶段证据、请求哈希和与现有 HardwareRequest 的兼容性。

## 单机流程和协作接口

操作者先记录任务 ID、版本、代码提交、板卡与工具状态。再以独立黄金模型驱动 RTL 回归，检查协议帧长度/CRC/序号、FIFO 满空/背压、跨时钟和复位释放；只有设计确实存在对应模块时才运行这些专项检查。综合与实现检查实际资源和时序报告，阈值来自批准的项目方案。PYNQ 板测时保存与 .bit 匹配的 .hwh、加载/运行日志和测量结果；缺少 Vivado、镜像、外围器件或实板时明确记录 blocked/not_run。

三机协作中，B/C 可独立开发和仿真，经现有同伴消息发给 A 代码提交、测试建议及交接清单。只有 A 机可以安排物理板卡操作。现有 HardwareService 尚无真实 PYNQ-Z2 适配器、自动提交工具和完整的未知状态保护，故本技能只交付可验证的请求/证据接口，不开启 hardware_enabled 或暗示已经执行板测。

## 工具选择和依据

公众号文章介绍 Codex + DeepSeek + Vivado MCP 的本地自动化形式；官方 AMD 也提供 Vivado MCP Server。技能优先按当前机器上实际可用的 Vivado Tcl/仿真工具工作，检测到可信的官方 MCP 后可用其能力，但不依赖它，也不沿用文章要求的全局 Full Access 设置。目标板器件以 AMD PYNQ-Z2 页面为准；板文件与约束以 XilinxBoardStore/PYNQ 3.1.1 对应版本为准。

来源：
- https://mp.weixin.qq.com/s/0UOMTskrAL640sUBV0A01Q
- https://www.amd.com/en/corporate/university-program/aup-boards/pynq-z2.html
- https://github.com/Xilinx/XilinxBoardStore/tree/master/boards/TUL/pynq-z2/A.0
- https://github.com/Xilinx/PYNQ/blob/3.1.1/boards/Pynq-Z2/base/vivado/constraints/base.xdc
- https://github.com/Xilinx/PYNQ/blob/master/docs/source/changelog.rst
- https://pynq.readthedocs.io/en/latest/pynq_libraries/overlay.html
- https://www.amd.com/en/support/downloads/ross-agentic-ai.html

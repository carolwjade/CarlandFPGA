# PYNQ-Z2 板卡与工具核对

## 目标器件和构建材料

- AMD 列出的 PYNQ-Z2 SoC 是 **XC7Z020-1CLG400C**。Vivado 器件名是 **`xc7z020clg400-1`**，可从 TUL 的 [`board.xml`](https://raw.githubusercontent.com/Xilinx/XilinxBoardStore/master/boards/TUL/pynq-z2/A.0/board.xml) 复核。板卡修订、板文件路径和当前 Vivado 可用器件都应在实际运行时核对。[AMD 板卡页](https://www.amd.com/en/corporate/university-program/aup-boards/pynq-z2.html)
- 需要板级 PS 预设时，使用 [Xilinx Board Store 的 TUL/pynq-z2/A.0](https://github.com/Xilinx/XilinxBoardStore/tree/master/boards/TUL/pynq-z2/A.0) 与当前 Vivado 兼容的板文件；不需要板级预设时可按器件名建工程。两种路径都要单独校对实际外设与 I/O 约束。[PYNQ 板卡设置说明](https://pynq.readthedocs.io/en/v2.5.1/overlay_design_methodology/board_settings.html)
- PYNQ 3.1.1 的 [PYNQ-Z2 镜像在旧版下载区](https://www.pynq.io/boards.html)；[PYNQ 4.0 变更记录](https://pynq.readthedocs.io/en/latest/changelog.html) 明确移除了 PYNQ-Z2 支持。选镜像、Vivado 和 Overlay 依赖时先核对所用版本；不要因文档出现新版 PYNQ 就升级该板至 4.0。
- 可参考 [PYNQ 3.1.1 基础工程 XDC](https://github.com/Xilinx/PYNQ/blob/3.1.1/boards/Pynq-Z2/base/vivado/constraints/base.xdc) 与板卡原理图逐个映射设计实际使用的引脚、时钟和电平。不要整份复制基础约束后假定自定义外设已正确连线。若连接外部采样器或通信模块，先核对接口电压、方向、共用引脚和上电次序。

## 可复现的证据

| 阶段 | 应保存的实际输出 | 边界 |
| --- | --- | --- |
| 仿真 | 激励/种子、黄金模型对比、运行日志、失败波形 | 只证明所跑场景；CDC/RDC 另查 |
| 综合与实现 | Tcl/工程设置、XDC、利用率、DRC、未约束路径、实现后时序报告 | 分清综合估计与布局布线后结果 |
| PYNQ 板测 | 镜像/板卡版本、同次构建 `.bit`/`.hwh`、加载日志和实测数据 | 无实板即不可声明通过 |

PYNQ [`Overlay`](https://pynq.readthedocs.io/en/latest/pynq_libraries/overlay.html) 由 `.bit` 加载逻辑并解析匹配的 `.hwh`；两者应同名且出自同一次构建。只有成功加载并执行测试才计为板测证据。

## 自动化通道

优先使用当前机器已经验证的 Vivado Tcl/命令行和仿真工具。AMD 的 [Ross/Vivado MCP 下载页](https://www.amd.com/en/support/downloads/ross-agentic-ai.html) 提供官方 Vivado MCP Server；若已配置，先确认服务器来源、可调用工具、目标工程与权限，再选用。MCP 返回值也须关联实际 Vivado 日志与报告。用户提供的[公众号方案](https://mp.weixin.qq.com/s/0UOMTskrAL640sUBV0A01Q)可启发模型分工，不能替代本机工具与板卡状态核验。

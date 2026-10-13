# metadata 兼容与可恢复实板验证

本页来自真实 PYNQ-Z2 连接、base Overlay metadata 故障和 BRAM 修复。方法供 A 执行、B/C 准备 fixture 和测试计划；历史地址、GPIO 编号与版本不能套到新板。

## 实际运行环境

保存 A 主机 UTC 起止时间、板端时间、板卡/镜像、Python/PYNQ、权限、cwd、环境及已加载 Overlay。2026-10-13 板端为 PYNQ 3.0.1、CPython 3.10.4，板端时钟仍为 2022 年，本轮用 A 主机时间关联，不为测试便利修改系统时钟。这些是现场记录，不是固定要求。

系统 python3 曾无法导入 pynq，改用实际虚拟环境解释器；已装包也可能被 `/home/xilinx/pynq` 源码遮蔽，已采用 `/tmp` 工作目录及核实的 `BOARD=Pynq-Z2`、`XILINX_XRT=/usr` 环境。先读取现有环境与包路径，不能用变量伪造板型。sudo 非交互失败与缺权限分别记录；凭据经既有私密通道，不留在命令、脚本、Git 或日志。

串口回显曾包含结束标记，解析必须匹配实际执行产生的独立行。首次经物理串口固定 SSH 主机公钥，之后复用可信连接，密钥不符先停。上传后比较两端 SHA-256，再执行该字节版本。烟测、PL 加载、metadata 解析、MMIO、功能与清理各有独立结论。

## metadata 异常先只读复现

1. 保存真实 parser 的 ip_dict、mem_dict、GPIO 描述和匹配 `.bit/.hwh` 哈希，读取完整 HWH，不猜测典型字典。旧脚本在 PL 加载后发生 KeyError，MMIO/reset 调用为零，这是 metadata 失败，不能报告 BRAM 功能通过。
2. RuntimeMetadataParser 会把 BRAM 目标移到 mem_dict，其中 `type="DDR4"` 是合成标签，不能当作硬件 VLNV。识别目标用同次 HWH 的 MODULE 身份、FULLNAME/INSTANCE 和 PS 可达 MEMRANGE；FULLNAME 的斜杠路径与 INSTANCE 的下划线名对应实际模块。
3. HWH ADDRESSBLOCK 的 RANGE=4096 曾表示 ECC/控制寄存器，PS MEMRANGE 才给出此次可达窗口 64 KiB。交叉核对所有存在的 phys_addr/addr_range 与 base_address/size 对；冲突、缺身份、错误模式或 streaming 目标在 GPIO/MMIO 前拒绝。不能只看类名、type 或一个字段就试写。
4. 用真实 schema 与完整 HWH 建 fixture，先证实旧代码在真实结构上失败，再验证修复及拒绝条件。最初 host mock 的 22 项通过遗漏 mem_dict 结构；最终 28 项 host 回归仍须独立实板确认。fixture harness 自身的 NameError 不算旧实现有效失败证据。

兼容逻辑保持可核对身份和范围，不给未知 parser 增加猜测或固定地址 fallback。只读诊断成功不授权写入。

## BRAM 写入、复位和清理

- A 独占实验，先明确测试窗口、宽度、对齐、原始数据保存位置、复位策略及清理失败行为。`GPIO(..., 'out')` 默认拉低可能造成 MicroBlaze 复位短脉冲；已采用 sysfs `direction=high` 原子保持复位并立即回读。全局编号通过实际 GPIO.get_gpio_pin 得出；960 是本次结果，不是通用常量。
- AXI GPIO 输出 DATA 读零或 PYNQ 输出 read() 缓存不能证明输出锁存状态，readout 也不受该对象支持。功能判据采用真实 BRAM MMIO 写读。GPIO 起初未导出时，只能保存加载/导出后可观察状态，不能声称知道导出前锁存值。
- 本次计划保持 MicroBlaze reset，先快照 16 个原始 32 位字，再做 3 轮 × 8 种 pattern × 16 字 = 384 次比较。最后写回全部 16 字并逐字读回核对，随后恢复已观察到的 reset 值/方向；只有本测试创建的 export 才 unexport。
- 异常路径同样清理。原值写回或回读失败时保持 reset 安全状态、非零退出，保存原始数据与错误；不能先释放复位、覆盖旧日志或自动重烧。独立观察清理后 sysfs export 与 fpga manager 状态。

判定包含期望/观察比较、范围、退出码、原值恢复和复位清理。本次实证覆盖 `0xFC00..0xFC3C` 的 64 字节窗口，未测整个 64 KiB、吞吐率或 MicroBlaze 应用；这是测量范围，不能扩大结论。PL 加载不保证恢复了之前 Overlay。

## 字节和操作身份

新源码、fixture、范围或请求需要新 operation_id、request_hash、manifest 与 tested_commit，保留旧失败。Windows git archive/文本重定向曾转换 CRLF，上传与 Git blob 不一致；采用 subprocess `git show` 原始 bytes，保护日志/bit/hwh 的 .gitattributes，发布前核对 blob 与上传 SHA。排除被转码的早期运行，不回写历史证据。

评论文本的换行可按明确的平台规范比较，原始测量、脚本、日志和二进制必须逐字节一致。报告绑定同一 PR 的实际冻结 head，后来新 head 不自动继承通过。

## 现场证据入口

- [B metadata 修复 PR #9](https://github.com/carolwjade/CarlandFPGA/pull/9)：源码 `9b618204473c8fda1bffbaf436080d77a34db5fc`，冻结板测 head `692f58bce38ff81d03204e46faf3c3792c5ff8f2`；C review、A 测量反馈与客机回读均在该 PR。
- [A 原始回证 PR #7](https://github.com/carolwjade/CarlandFPGA/pull/7)：measurement 提交 `7246b2e0af33840df5f077a725f441c9240740a2`；操作 `BOARD-20261013-A:B:base-bram-v3-metadata-r1`，request_hash `69380c4062746f68bd35d6f1823ad98df6a72927a8a8f010d738319938171e7f`，实测 384/384、16 原值恢复、清理后 GPIO 未导出、manager operating。

链接是历史证据入口，不能当作本轮 live 状态。按需读任务原始文件与匹配提交，不将大 HWH 或私密连接记录复制进技能包。

# 协同开发基础实用验收

结论：**基础实用范围通过，本轮按简化标准收尾。** 此结论采用真人在 2026-10-13（北京时间）的最新要求：达到协同开发基础实用标准即可，简化验收、尽快完成。此前严格离线试验范围不再阻塞本次基础验收；未完成的试验仍记为未验证。

本轮：`MESH-20261011-132845-c94f2686`。收尾任务：`task-d18dccc4ffd2a23ee3695535`，版本 `1791823953305`，协调分支已确认负责人 A。

| 日常能力 | 已有实测依据 | 结论 |
| --- | --- | --- |
| ABC 在线相互通信、处理任务并回传 | A/B、A/C 原探针有实际模型完成记录；B/C 原消息投递、处理及完成报告已对齐 | 可用于日常协作 |
| B/C 代码提交、A 验证反馈、队友读回 | PR #2、#4 的指定提交已有 A 检查和实际反馈回执；本次重新读取 GitHub，提交未变 | 交接链路可用 |
| 飞书入口与普通新主会话接入 | 既有真人群指令、节点报告；新普通主会话实际加载工具、向 B 发信并收到匹配回复 | 基础入口可用 |
| C 网络离线时 A/B 继续工作 | 原自然离线窗口中 A/B 双向实际模型完成，已有主模型验收记录 | 该场景通过 |

本次只复核既有证据、当前控制器状态和 GitHub 提交/反馈，不重复模型探针或全套测试。新会话接入证据证明工具访问及真实收发，不扩展为所有会话管理行为均已验收。

## 交接记录

- [B PR #2](https://github.com/carolwjade/CarlandFPGA/pull/2)：`d6fa624a86e32c26997eeac07e3297ab3c9a78a4`；[A 反馈](https://github.com/carolwjade/CarlandFPGA/pull/2#pullrequestreview-5490050521)；B 已回读同一提交及反馈。
- [C PR #4](https://github.com/carolwjade/CarlandFPGA/pull/4)：`0c44e6fa05b37cadb810fab29c0e729880b18dd9`；[A 反馈](https://github.com/carolwjade/CarlandFPGA/pull/4#pullrequestreview-5490272933)；C 已回读同一提交及反馈。该回执不单独证明读回回合本身已结束。
- 两个 PR 目前仍为 open；这里的交接完成不表示已合并或部署。

## 当前状态与保留限制

收尾检查时 A 控制器与飞书连接正常，C 在线，B 在 A 的当前健康视图中不可达；不能称三机此刻全在线。对 B 的收尾通知由原持久队列保留，恢复后自动投递；C 的通知已获传输确认。该确认不等于 C 已完成本次通知的处理。

A 完全离线时 B/C 同窗双向通信及相关专门恢复试验尚未完成，列为后续增强验证，不标通过。已有普通队列恢复记录保留，但不扩大为上述未完成场景的证明。

取消本轮尚未执行的离线试验准备/GO 等待，不再启动 ARM、Stop 或故障注入。保留原服务、配置、凭据、队列和历史证据。本轮未进行 FPGA 烧录或板测。跨节点源码存在已记录的本地例外，不宣称三个 Git HEAD 完全一致。

## 本机证据索引

原始证据保存在 A 本机 `artifacts/mesh-acceptance/MESH-20261011-132845-c94f2686/`，不将私有运行状态或凭据上传到公开仓库：

- `acceptance-matrix-current.json`：简化收尾前的详细历史矩阵。
- `B-pr2-readback-received-v1.json`、`C-pr4-readback-receipt-accepted-v1.json`：正式交接反馈回执。
- `C-probe-terminal-received-v1.json`、`A-C-existing-B-receipts-reconciliation-v3/A-reconciliation.json`：模型完成与原消息核对。
- `A-new-ordinary-chat-proof-v1.json`、`new-chat-B-receipt-v1.json`：新会话实际接入及匹配回复。
- `C-offline-evidence-verdict-v8.md`：自然 C 离线子项及其取证限制。
- `basic-practical-closeout-v1.json`：本次结论、当前状态及收尾通知状态。

本记录替代此前报告的“等待专项离线试验才可结束”条件；历史证据和未验证状态不改写。

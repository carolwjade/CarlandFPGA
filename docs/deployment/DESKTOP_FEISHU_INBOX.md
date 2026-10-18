# 飞书群消息接入现任 Desktop 主会话

原节点控制器的 Feishu SDK 先验证群、真人发送者和明确节点目标，再把原消息写入持久 spool 和收件账本。已配置 Desktop 路由时，普通消息不再启动按消息派生的后台会话。配置失效时保留收件并报告故障；已有收件目录可阻止重启后回落到旧路由。

## 绑定与部署

先用原 Update/stop_idle_node 流程部署已审阅提交，保留本地源码、配置、凭据、账本和失败证据。原 state_dir 中放置 `desktop-group-owner.json`，包含 `project_id`、`node_id`、`group_id`、`thread_id`、正整数 `generation`、`task_id`、`status: "active"`、`codex_executable`、其 `codex_sha256`、`codex_home` 与 `cwd`。这些值必须来自现任 Desktop 的授权移交记录；线程和代次须匹配既有 `external-task-owners.json`，不能以新配置夺取所有权。

只使用实测过的官方 `codex queue --thread ... --message ...`，固定当前安装二进制哈希。程序写自己的 inbox SQLite，通过官方 CLI 入队，不改 Codex SQLite、不调用 thread/resume、不创建第二个目标 writer。Desktop 更新后重新核验二进制及实际消费，不能沿用旧路径猜测成功。

2026-10-17/18 的隔离 App 会话实测：空闲时消费；忙碌时保留到当前轮次结束。应用关闭、线程未加载或被中断时不承诺自动启动。主会话保持同一身份并用有界回合推进；程序等待没有模型推理，读消息、回复和执行仍消耗 token。

## 收件与回复

CLI 队列携带 receipt ID、原信封 SHA256、认领文件路径和明确 relay 来源。主会话用已认证的 `project_cli desktop_inbox_claim --args-file ...` 读取原信封并认领。仅首次有效认领返回 `effects_allowed=true`；暂停、已替换版本、错误代次和重复认领不授权执行。无明确节点的共享新任务继续走原远端所有权认领。附件引用、引用消息和原始内容保持为资料；保存元数据不代表已下载或阅读附件。

结束处理后，使用 `desktop_inbox_complete` 提交原 `receipt_id/thread_id/generation/claim_id` 及 `result.reply_text`（1–2800 字符）。原 outbox 使用固定 `desktop-result:<receipt_id>` 排队回复。完成结果先持久化，跨数据库中断后可恢复同一回复。收件、CLI 入队、主会话读取、处理完成、回复排队和平台送达是分开的状态。

`desktop_inbox_list` 支持所有送达状态及 completed 分页。`health.desktop_inbox` 报告当前绑定、收件状态和 spool 故障。不得把 pending/unknown 当作已读或已回复。CLI 结果不明不自动重放；核对真实队列/会话证据后，原主通过 `desktop_inbox_reconcile` 登记证据哈希与明确结果。已认领操作不因重复通知再次执行。

## 发件故障与历史覆盖

原 sender 按应用身份保持 FIFO，不同角色可独立进展。SDK 隐式重试关闭，明确的未发送拒绝按原 operation_id 退避；超时、分片证据不完整、缺消息 ID、进程中断和旧版未跟踪的 pending 进入 unknown hold。保留原行，核对实际平台证据后由原 owner reconcile；哈希本身不证明送达。

WebSocket connected 不证明 token 或发送可用。`21001` 是已有应用的访问控制拒绝；记录时间和平台请求 ID，交由原应用 owner/平台查明具体规则。不能用重建机器人、复制凭据或盲加 scope 替代修复。既有 Astra 代转须标明实际发送者与来源，并保留原 A 队列状态。

断线补收需固定上界、重叠全分页、话题回复和修改/撤回核对，再与实时收件去重。当前 SDK 回调不保证提供 header event_id；缺失保持 null。已删除、不可见或平台拒绝访问期间的内容不能声称全部找回。真实验收须记录真人平台 message_id → 本主线程/代次 → 实际读取与结果 → 回复 message_id → 群内读回。

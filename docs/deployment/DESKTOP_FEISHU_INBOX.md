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

## 同伴汇报进入已有负责人

需要送入本 Desktop 的 peer task，须同时出现在 `desktop-group-owner.json` 的 `peer_tasks` 对象（`task_id: 正整数版本`）和既有 `external-task-owners.json` 中。后者的 `owner_kind: desktop`、`thread_id`、`director_generation`、`task_version` 必须匹配。主任务和通信子任务逐项登记；不会把全部未知任务归给本主会话。登记须由现任负责人按已有任务授权进行，并保留修改前配置与任务归属证据。

原 peer HTTP 的 HMAC、来源与收件人检查先执行。已登记的汇报持久化到 `desktop-peer-spool` 和同一收件账本，再 ACK 原传输。原 controller 恢复升级前 pending peer 收件时也使用该入口，失败保留原行，不回落到后台模型。原来 completed/failed 的后台结果保持原状态，不能重写成 Desktop 已读。独立 mesh task 沿用原路径。

peer receipt 保留 ASTRA/AGENT_REPORT、原 sender、任务版本、message/operation ID 与信封哈希；其平台消息 ID 为 null。首次领取返回 `review_allowed=true`，`effects_allowed` 始终 false。同伴材料不产生人类授权，后续工作依据原任务书和人类授权决定。完成采用 `result.summary`（1–2800 字符），不会自动发群回复。过期任务归属、错误代次、人类暂停与不明队列送达均不能触发重复审阅或执行。

## 发件故障与历史覆盖

原 sender 按应用身份保持 FIFO，不同角色可独立进展。SDK 隐式重试关闭，明确的未发送拒绝按原 operation_id 退避；超时、分片证据不完整、缺消息 ID、进程中断和旧版未跟踪的 pending 进入 unknown hold。保留原行，核对实际平台证据后由原 owner reconcile；哈希本身不证明送达。

WebSocket connected 不证明 token 或发送可用。`21001` 是已有应用的访问控制拒绝；记录时间和平台请求 ID，交由原应用 owner/平台查明具体规则。不能用重建机器人、复制凭据或盲加 scope 替代修复。既有 Astra 代转须标明实际发送者与来源，并保留原 A 队列状态。

原驻留程序在启动、重连、相关事件拒收或持久写失败时进行有限历史审计，普通程序重试不调用模型。使用原应用的生成式 SDK `alist/aget` 接口，固定本轮上界，显式跟随页游标，重叠查询群历史并发现较早话题根、枚举可访问话题；不使用会吞错误的单页 helper。审计保存原页、请求、游标、正文哈希和错误。全部候选完成持久接收后才提交可见覆盖 checkpoint；拒绝访问、分页失败、时间/页数边界和修改冲突均保留 gap。`health.feishu_history` 单独暴露审计状态，发件旧错误不会掩盖它。

仍关联到本主会话的原真人消息会重新核对，包括已回复但后续工作可能仍在进行的消息。远端查询前，已知指令先写入持久核对门控；当前 scan 的完全一致证据只能解除自己的暂时门控。编辑、撤回、不可见或同 revision 正文冲突继续阻止旧指令执行。新一版实时真人输入仍需匹配当前核对证据，才可解除对应旧门控；不会自动恢复人类暂停，也不会回滚已经开始的副作用。

恢复出的历史正文保持待审资料。每轮新增需关注证据合成一个 `source_channel=feishu_history` 系统通知，使用原主线程的同一官方队列；不为每一条旧消息创建模型回合。原主首次领取只有 `review_allowed`，通过 `desktop_history_read`（同一认领参数文件，按 `next_offset` 分页）读取真实发送者、平台消息、revision、状态和原 API 正文，再用 `result.summary` 记录判断。不会自动执行历史命令或发群回复；先核对原操作与送达证据，避免重放旧指令或未知发送。

当前 SDK 回调不保证提供 header event_id；缺失保持 null。已删除、不可见或平台拒绝访问期间的内容不能声称全部找回。代码/离线测试通过与原应用 API 恢复是独立验收。真实验收须记录真人平台 message_id → 本主线程/代次 → 实际读取与结果 → 回复 message_id → 群内读回。

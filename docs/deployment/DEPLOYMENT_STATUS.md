# FPGA 三机多 Agent 部署状态

更新：2026-10-09。设计基线：`docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.6；仓库可见性按用户后续决定改为**公开**。

| 范围 | 当前证据 | 状态 |
| --- | --- | --- |
| 控制器、飞书适配、三节点协议、离线队列与分发包 | `python -m unittest discover -s tests -q`，191/191 通过；包含同伴 B 离线而 C 可继续、人类指令抢占、Git 快进认领、重启后暂停、编辑版本失效、签名健康探针、群发队列、新身份一条发信加同身份读回，以及相同接收时间下的编辑消息顺序测试 | **本地验证通过**，不是跨机/飞书线上验收 |
| Astra→DeepSeek 实际调用 | 2026-10-07 `python -m scripts.smoke_parent_child --key-file <本机密钥路径>` 返回 `CHILD_OK`；父 `gpt-6-astra/openai` 选择 `low`，子 `deepseek-flash/deepseek/max` | **A 机真实路由通过** |
| 推理深度显示 | 早前真实 Astra 同线程 `low`→`high` 且 app-server `thread/read.reasoningEffort` 对应 | **后端元数据通过**；本聊天右下角下拉框联动仍无可视证据 |
| A 机后台常驻 | 计划任务改为直接管理 Python 服务；重启后 `100.121.238.56:8787` 监听，签名健康接口返回 A，服务内 DeepSeek 派工返回 `DEPLOYED_OK`，待命数仍为 2 | **本机实测通过** |
| GitHub 仓库 | `https://github.com/carolwjade/CarlandFPGA.git` 公开；A 机已通过 GitHub Desktop 推送，并用 `git fetch origin` 与 `git ls-remote origin refs/heads/main` 回读确认本地/远端 `main` 同为 `86a7708`。后续提交仍须逐次回读；B/C 走 fork/PR | **A 机真实读写已通过**；该提交之后的版本以远端回读为准 |
| 队友分发包与接入 | 入口含逐身份发信及读回的上线门槛；发送回执写在被 Git 忽略的本机目录，读回失败不会重复发信。无凭据 B 机接入烟测已通过。分发包须由 `python -m fpga_mesh.distribution` 从干净、已提交的 Git 文件生成，再核对 CRC、逐文件 SHA-256 和 `MANIFEST.json` 的 revision | **入口本地验证通过**；本次更新版 ZIP 需在提交后重建，队友实机仍待验收 |
| 飞书六机器人 | A 机 `FPGA Astra A`（`cli_aa4c9f58dd385cc9`）及 `FPGA DeepSeek A`（`cli_aa4c9f8c59785cd1`）均已开通各自三项消息权限；DeepSeek 发布 `1.0.0`，Astra 添加 `im.message.receive_v1` 后发布 `1.0.1`，后台均显示“已发布/已启用”。Astra 的真实 SDK 长连接曾连通，后台“验证”返回“连接成功”。两身份对目标群的真实发信各返回 HTTP 400 / `230002`，没有发送成功，也没有读回。群 `FPGA/AI/DEV` 为外部群，其 Add Bot 页面仅列出 Custom Bot。开发者后台的“允许机器人被添加到外部群中使用”被禁用，提示当前账号须先完成个人实名认证 | **应用配置及发布完成；外部共享、入群、发信、读回、群事件接收未通过**。实名认证属于账号本人操作；完成后开启两应用外部共享、发布变更、逐一入群并执行自测 |
| 跨网 B/C 与 Tailscale | A 已安装并登录 Tailscale 1.102.4，取得 `100.121.238.56`；只允许 Tailscale 接口/地址、100.64.0.0/10 来源访问 TCP 8787 的防火墙规则已生效 | **A 机就绪**；B/C 尚未入网，无法验收真实跨机互通 |
| 板卡烧录及日志 | A 为唯一可烧录电脑，但未得到型号、工具链与实机接口 | **未实测**，`hardware_enabled=false` |
| 使用量、质量、耗时改善 | 子池动态扩缩、最高 `max`、零模型调用等待等单项行为已有测试；尚无三机代表任务对照 | **成效量化未验收**，不能声称已节省 GPT 套餐用量 |

飞书群 ID 已直接从群设置取得，群邀请链接不是应用机器人入群的必要条件。接入使用官方 `lark-channel-sdk` 长连接仅给 Astra；DeepSeek 应用不订阅群消息，但加入群后会由部署程序做一次性发送与读取自测。A 机配置保存了两个应用的非秘密 ID 和本机 Secret 路径，`feishu.enabled` 仍为 `false`，避免把尚未通过的机器人报成在线。当前不能把自定义 Webhook 机器人当作读取群内人类指令的替代品。管理员接手要点见 [飞书应用上线交接](FEISHU_APP_HANDOFF.md)。HTTP 同伴连接由各机直连，HMAC 认证且对来源/项目/接收者做检查；各机 SQLite 出站队列可在断线后补发。后台健康探针和配额读取都不调用模型，额度阈值 20%/10% 报告会持久排队。

队友入口 `deploy/Join-FPGAMesh.ps1` 与 `deploy/TEAMMATE_PROMPT.md` 不含 Secret。它能配置本地节点，但 ChatGPT 登录、飞书授权、Tailscale 加入同一 tailnet、GitHub fork 登录、跨机密钥交换以及 A 机板卡验收需要对应成员/平台参与。公开克隆不提供直接写权限。

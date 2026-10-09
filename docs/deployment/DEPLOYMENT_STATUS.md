# FPGA 三机多 Agent 部署状态

更新：2026-10-09。设计基线：`docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.6；仓库可见性按用户后续决定改为**公开**。

| 范围 | 当前证据 | 状态 |
| --- | --- | --- |
| 控制器、飞书适配、三节点协议、离线队列与分发包 | `python -m unittest discover -s tests -q`，192/192 通过；包含同伴 B 离线而 C 可继续、人类指令抢占、Git 快进认领、重启后暂停、编辑版本失效、签名健康探针、群发队列、新身份一条发信加同身份读回、相同接收时间下的编辑消息顺序，以及 SDK 后台线程把事件投递回控制器线程 | **本地验证通过**；A 机飞书线上验收另见下行 |
| Astra→DeepSeek 实际调用 | 2026-10-07 `python -m scripts.smoke_parent_child --key-file <本机密钥路径>` 返回 `CHILD_OK`；父 `gpt-6-astra/openai` 选择 `low`，子 `deepseek-flash/deepseek/max` | **A 机真实路由通过** |
| 推理深度显示 | 早前真实 Astra 同线程 `low`→`high` 且 app-server `thread/read.reasoningEffort` 对应 | **后端元数据通过**；本聊天右下角下拉框联动仍无可视证据 |
| A 机后台常驻 | 计划任务直接管理 Python 服务；启用飞书后发现并修复 SDK 导入时抓取运行中 event loop、回调跨线程访问 SQLite 两个问题。`FPGA-Mesh-Node-A` 运行中，真人群指令由常驻服务处理并回报，第二次入站零重试、无错误 | **本机与飞书真实联调通过**；B/C 仍待部署 |
| GitHub 仓库 | `https://github.com/carolwjade/CarlandFPGA.git` 公开；A 机通过 GitHub Desktop 推送，并用 `git ls-remote origin refs/heads/main` 回读确认本地与远端 `main` 一致。最新分发包的修订号见 `MANIFEST.json`；B/C 走 fork/PR | **A 机真实读写已通过**；每次提交后远端回读 |
| 队友分发包与接入 | 入口含逐身份发信及读回的上线门槛；发送回执写在被 Git 忽略的本机目录，读回失败不会重复发信。无凭据 B 机接入烟测已通过。分发包由 `python -m fpga_mesh.distribution` 从干净、已提交的 Git 文件生成，核对 CRC、逐文件 SHA-256 和 `MANIFEST.json` 的 revision | **入口本地验证通过**；本次更新版 ZIP 在提交后重建，队友实机仍待验收 |
| 飞书六机器人 | A 机 `FPGA Astra A`（`cli_aa4c9f58dd385cc9`）和 `FPGA DeepSeek A`（`cli_aa4c9f8c59785cd1`）的外部群版本 `1.0.2` 均已发布，两个机器人已加入 `FPGA/AI/DEV`。各自发信并同身份读回成功，群内可见原消息；Astra 长连接收到真人 `/fpga A` 指令并两次回复指定 ACK，常驻服务复测零重试、无错误 | **A 机两身份与真人群指令线上验收通过**；B/C 四身份尚未创建/入群 |
| 跨网 B/C 与 Tailscale | A 已安装并登录 Tailscale 1.102.4，取得 `100.121.238.56`；只允许 Tailscale 接口/地址、100.64.0.0/10 来源访问 TCP 8787 的防火墙规则已生效 | **A 机就绪**；B/C 尚未入网，无法验收真实跨机互通 |
| 板卡烧录及日志 | A 为唯一可烧录电脑，但未得到型号、工具链与实机接口 | **未实测**，`hardware_enabled=false` |
| 使用量、质量、耗时改善 | 子池动态扩缩、最高 `max`、零模型调用等待等单项行为已有测试；尚无三机代表任务对照 | **成效量化未验收**，不能声称已节省 GPT 套餐用量 |

飞书群 ID 已直接从群设置取得，群邀请链接不是应用机器人入群的必要条件。接入使用官方 `lark-channel-sdk` 长连接仅给 Astra；DeepSeek 应用不订阅群消息，只在入群自测时做一次性发送与读取。A 机配置保存了两个应用的非秘密 ID 和本机 Secret 路径，`feishu.enabled=true`；入群自测回执和 Secret 均只在 Git 忽略的本机目录。管理员接手要点见 [飞书应用上线交接](FEISHU_APP_HANDOFF.md)。HTTP 同伴连接由各机直连，HMAC 认证且对来源/项目/接收者做检查；各机 SQLite 出站队列可在断线后补发。后台健康探针和配额读取都不调用模型，额度阈值 20%/10% 报告会持久排队。

队友入口 `deploy/Join-FPGAMesh.ps1` 与 `deploy/TEAMMATE_PROMPT.md` 不含 Secret。它能配置本地节点，但 ChatGPT 登录、飞书授权、Tailscale 加入同一 tailnet、GitHub fork 登录、跨机密钥交换以及 A 机板卡验收需要对应成员/平台参与。公开克隆不提供直接写权限。

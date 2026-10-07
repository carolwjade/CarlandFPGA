# FPGA 三机多 Agent 部署状态

更新：2026-10-07。设计基线：`docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.6；仓库可见性按用户后续决定改为**公开**。

| 范围 | 当前证据 | 状态 |
| --- | --- | --- |
| 控制器、飞书适配、三节点协议、离线队列与分发包 | `python -m unittest discover -s tests -q`，170/170 通过；包含同伴 B 离线而 C 可继续、人类指令抢占、Git 快进认领、重启后暂停、编辑版本失效、签名健康探针、群发队列，以及新身份一条发信加同身份读回的本地测试 | **本地验证通过**，不是跨机/飞书线上验收 |
| Astra→DeepSeek 实际调用 | 2026-10-07 `python -m scripts.smoke_parent_child --key-file <本机密钥路径>` 返回 `CHILD_OK`；父 `gpt-6-astra/openai` 选择 `low`，子 `deepseek-flash/deepseek/max` | **A 机真实路由通过** |
| 推理深度显示 | 早前真实 Astra 同线程 `low`→`high` 且 app-server `thread/read.reasoningEffort` 对应 | **后端元数据通过**；本聊天右下角下拉框联动仍无可视证据 |
| A 机后台常驻 | 计划任务改为直接管理 Python 服务；重启后 `100.121.238.56:8787` 监听，签名健康接口返回 A，服务内 DeepSeek 派工返回 `DEPLOYED_OK`，待命数仍为 2 | **本机实测通过** |
| GitHub 仓库 | `https://github.com/carolwjade/CarlandFPGA.git` 公开；A 机具备 GitHub Desktop 推送路径，远端当前版本以 `git ls-remote origin refs/heads/main` 与分发包 `MANIFEST.json` 的 revision 对照验收 | **A 机既有推送路径通过**；本次版本是否同步以远端回读为准，B/C 走 fork/PR |
| 队友分发包与接入 | 入口增加逐身份发信及读回的上线门槛；发送回执写在被 Git 忽略的本机目录，读回失败不会重复发信。无凭据 B 机接入烟测已通过；新版 ZIP 的 CRC 与逐文件 SHA-256 已核验，解包副本 170/170 测试通过 | **新版 ZIP 本地验收通过**；队友实机仍待验收 |
| 飞书六机器人 | A 机已创建 `FPGA Astra A`（`cli_aa4c9f58dd385cc9`）及 `FPGA DeepSeek A`（`cli_aa4c9f8c59785cd1`），两者机器人能力已添加，Secret 仅保存在被 Git 忽略的本机目录。两应用目前待上线，权限列表为空；用各自凭据获取 tenant token 后实际发群消息均返回 HTTP 400 / `99991672`（缺少 API scope）。群 `FPGA/AI/DEV` 是外部群，Bots 列表仍为空 | **未上线、未入群、未发/读成功**；需开通并发布消息权限、外部共享、加入群，再运行逐身份自测 |
| 跨网 B/C 与 Tailscale | A 已安装并登录 Tailscale 1.102.4，取得 `100.121.238.56`；只允许 Tailscale 接口/地址、100.64.0.0/10 来源访问 TCP 8787 的防火墙规则已生效 | **A 机就绪**；B/C 尚未入网，无法验收真实跨机互通 |
| 板卡烧录及日志 | A 为唯一可烧录电脑，但未得到型号、工具链与实机接口 | **未实测**，`hardware_enabled=false` |
| 使用量、质量、耗时改善 | 子池动态扩缩、最高 `max`、零模型调用等待等单项行为已有测试；尚无三机代表任务对照 | **成效量化未验收**，不能声称已节省 GPT 套餐用量 |

飞书群 ID 已直接从群设置取得，群邀请链接不是应用机器人入群的必要条件。接入使用官方 `lark-channel-sdk` 长连接仅给 Astra；DeepSeek 应用不订阅群消息，但加入群后会由部署程序做一次性发送与读取自测。A 机配置保存了两个应用的非秘密 ID 和本机 Secret 路径，`feishu.enabled` 仍为 `false`，避免把尚未通过的机器人报成在线。管理员接手要点见 [飞书应用上线交接](FEISHU_APP_HANDOFF.md)。HTTP 同伴连接由各机直连，HMAC 认证且对来源/项目/接收者做检查；各机 SQLite 出站队列可在断线后补发。后台健康探针和配额读取都不调用模型，额度阈值 20%/10% 报告会持久排队。

队友入口 `deploy/Join-FPGAMesh.ps1` 与 `deploy/TEAMMATE_PROMPT.md` 不含 Secret。它能配置本地节点，但 ChatGPT 登录、飞书授权、Tailscale 加入同一 tailnet、GitHub fork 登录、跨机密钥交换以及 A 机板卡验收需要对应成员/平台参与。公开克隆不提供直接写权限。

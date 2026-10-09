# 飞书应用上线交接

目标群：`FPGA/AI/DEV`，Chat ID `oc_e0de73230fd64dd2da3e52fc781dffb1`。这是外部群，应用机器人需具备外部共享资格；自定义 Webhook 机器人不能接收人类群指令，不能替代 Astra。

| A 机身份 | 应用 ID | 应用身份权限 | 事件订阅 |
| --- | --- | --- | --- |
| FPGA Astra A | `cli_aa4c9f58dd385cc9` | `im:message:send_as_bot`、`im:message`、`im:message.group_msg` | `im.message.receive_v1`，长连接 |
| FPGA DeepSeek A | `cli_aa4c9f8c59785cd1` | `im:message:send_as_bot`、`im:message:readonly`、`im:message.group_msg` | 无 |

A 机两应用已建立、启用机器人能力并开通表中权限；DeepSeek 发布 `1.0.0`，Astra 添加 `im.message.receive_v1` 后发布 `1.0.1`，后台均显示“已发布/已启用”。密钥只在 `.local/deployment/node-a/feishu/`，未进入 Git 或分发包。Astra 已保存“长连接接收事件”，真实 SDK 连接后后台“验证”返回“连接成功”。群 `FPGA/AI/DEV` 是外部群；应用发布页的“允许机器人被添加到外部群中使用”开关被禁用，页面提示“根据平台安全合规要求，完成个人实名认证后即可开启该功能”。群的 Add Bot 页面因此只列出 Custom Bot，不列出两应用机器人。两身份实际发群消息均返回 HTTP 400 / `230002`，没有发送成功，更未读回。

账号本人完成飞书开发者个人实名认证后，在两个应用的“版本管理与发布”开启“允许机器人被添加到外部群中使用”，保存并发布变更；再到群设置 → Bots → Add Bot 逐一加入两机器人。Astra 的事件已配置并发布，入群后仍须用真实人类消息验证实际接收。B/C 各自在自己的账号创建对应两应用；若其外部共享开关同样被禁用，各账号本人也须完成实名认证。自定义 Webhook 机器人只有群消息推送能力，不能代替本方案的 Astra 群指令接收。

入群后、标记上线前，逐身份运行下列 A 机自测；B/C 由 `deploy/Join-FPGAMesh.ps1` 自动执行同样的检查。每个身份用自己的凭据只发送一条带标记的消息，再读回相同的消息 ID、群 ID 和文本。失败保持该身份关闭。发送成功但读回失败时，本机回执保留，重跑只补读。此操作没有模型调用；DeepSeek 不会订阅群消息或自主读群。

```powershell
.local\venv\Scripts\python.exe -m fpga_mesh.feishu_selftest --node A --role astra --app-id cli_aa4c9f58dd385cc9 --secret-file .local\deployment\node-a\feishu\astra-secret.txt --group-id oc_e0de73230fd64dd2da3e52fc781dffb1 --state-file .local\deployment\node-a\feishu\astra-selftest.json
.local\venv\Scripts\python.exe -m fpga_mesh.feishu_selftest --node A --role deepseek --app-id cli_aa4c9f8c59785cd1 --secret-file .local\deployment\node-a\feishu\deepseek-secret.txt --group-id oc_e0de73230fd64dd2da3e52fc781dffb1 --state-file .local\deployment\node-a\feishu\deepseek-selftest.json
```

只有两条命令都返回 `"status": "verified"` 且能在群内见到对应机器人消息，才将 A 机配置的 `feishu.enabled` 改为 `true` 并重新启动 `FPGA-Mesh-Node-A` 计划任务。随后应以真实人类群消息核验 Astra 的长连接接收，人类指令入口未验收前不能宣称三机实时协作已打通。API 必要条件与返回码见[飞书获取会话历史](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/list)。

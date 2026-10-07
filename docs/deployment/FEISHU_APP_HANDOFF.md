# 飞书应用上线交接

目标群：`FPGA/AI/DEV`，Chat ID `oc_e0de73230fd64dd2da3e52fc781dffb1`。这是外部群，应用机器人需具备外部共享资格；自定义 Webhook 机器人不能接收人类群指令，不能替代 Astra。

| A 机身份 | 应用 ID | 应用身份权限 | 事件订阅 |
| --- | --- | --- | --- |
| FPGA Astra A | `cli_aa4c9f58dd385cc9` | `im:message:send_as_bot`、`im:message`、`im:message.group_msg` | `im.message.receive_v1`，长连接 |
| FPGA DeepSeek A | `cli_aa4c9f8c59785cd1` | `im:message:send_as_bot`、`im:message:readonly`、`im:message.group_msg` | 无 |

A 机两应用已在飞书开发者后台建立并启用机器人能力，密钥只在 `.local/deployment/node-a/feishu/`，未进入 Git 或分发包。两者仍显示“待上线”；实际发信各返回 `99991672`，因此一条群消息也未发出。应用目前没有已开通权限。需要有飞书组织授权的人员在各自应用中开通表中的权限、发布并获准上线、开启外部共享，然后在群设置中加入两个机器人。Astra 的长连接事件订阅也须生效。B/C 各自在自己的组织/账号创建对应两应用，权限和事件模式相同。

入群后、标记上线前，逐身份运行下列 A 机自测；B/C 由 `deploy/Join-FPGAMesh.ps1` 自动执行同样的检查。每个身份用自己的凭据只发送一条带标记的消息，再读回相同的消息 ID、群 ID 和文本。失败保持该身份关闭。发送成功但读回失败时，本机回执保留，重跑只补读。此操作没有模型调用；DeepSeek 不会订阅群消息或自主读群。

```powershell
.local\venv\Scripts\python.exe -m fpga_mesh.feishu_selftest --node A --role astra --app-id cli_aa4c9f58dd385cc9 --secret-file .local\deployment\node-a\feishu\astra-secret.txt --group-id oc_e0de73230fd64dd2da3e52fc781dffb1 --state-file .local\deployment\node-a\feishu\astra-selftest.json
.local\venv\Scripts\python.exe -m fpga_mesh.feishu_selftest --node A --role deepseek --app-id cli_aa4c9f8c59785cd1 --secret-file .local\deployment\node-a\feishu\deepseek-secret.txt --group-id oc_e0de73230fd64dd2da3e52fc781dffb1 --state-file .local\deployment\node-a\feishu\deepseek-selftest.json
```

只有两条命令都返回 `"status": "verified"` 且能在群内见到对应机器人消息，才将 A 机配置的 `feishu.enabled` 改为 `true` 并重新启动 `FPGA-Mesh-Node-A` 计划任务。随后应以真实人类群消息核验 Astra 的长连接接收，人类指令入口未验收前不能宣称三机实时协作已打通。API 必要条件与返回码见[飞书获取会话历史](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/list)。

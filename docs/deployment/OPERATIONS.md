# FPGA Mesh 部署与运行

每台电脑运行一个本地控制器和一个用该成员 ChatGPT 订阅登录的 Astra 主实例。Astra 根据任务调用本机 DeepSeek V4.1 Flash 子池，默认两个待命，但没有数量上限规则；子实例只用 `deepseek-flash` / `deepseek` / `max`。等待飞书、同伴、子结果和硬件时由网络与本地事件唤醒，不进行模型轮询。

## 队友入网

将无凭据分发包交给 B/C 的 Codex 会话，附上 `deploy/TEAMMATE_PROMPT.md`。在各自 Windows 电脑上运行 `deploy/Join-FPGAMesh.ps1 -Node B` 或 `-Node C`。脚本从公开 GitHub 仓库克隆源码，创建被 Git 忽略的 `.local/venv`，安装飞书 SDK，生成该机配置，运行自检并注册登录后常驻任务。现有工作区只在干净时快进，不覆盖队友的修改。

完整参数示例（路径和值由各机填写，绝不要把密钥内容贴进命令行或 Git）：

```powershell
pwsh -NoProfile -File deploy\Join-FPGAMesh.ps1 -Node B `
  -DeepSeekKeyFile 'C:\secure\deepseek-key.txt' `
  -SharedSecretFile 'C:\secure\fpga-mesh-secret.txt' `
  -GroupId 'oc_e0de73230fd64dd2da3e52fc781dffb1' -RegisterApps `
  -PeerA 'http://100.x.x.a:8787' -PeerC 'http://100.x.x.c:8787' `
  -SetUpFork
```

`-RegisterApps` 对每机的 Astra 和 DeepSeek 形象使用飞书官方设备授权流程建两个应用；成员须在网页确认。Astra 应用订阅群消息，DeepSeek 应用仅有发送用途，不监听群。六个应用都要在飞书开发者后台核对实际生效的机器人能力、消息权限、事件订阅和可用范围，然后在群设置 → Bots → Add Bot 中加入 `FPGA/AI/DEV`；真实收发成功才算上线。群 ID 已从飞书桌面端「群设置 → 底部 Chat ID」核实为 `oc_e0de73230fd64dd2da3e52fc781dffb1`，脚本已将它设为默认值。群分享链接是给人类加入用的临时链接，机器人入群不依赖它。缺少 Astra 凭据时脚本保持飞书关闭；补齐后重跑脚本。A 机的本地路径为 `.local/deployment/node-a`，可使用相同配置生成器补入应用凭据，不在仓库提交本地配置。

未指明节点的新共享任务只在 `codex/coordination` 分支的追加认领记录快进推送成功后执行；其他节点读取胜出的负责人并跳过重复执行。公开仓库允许克隆却不授予推送权限，所以 B/C 在获得写入该协调分支的权限前不能独立认领新的共享任务。明确写 `/fpga B ...`、`/fpga C ...` 或 `Astra-B:`、`Astra-C:` 的指令无需认领分支。`/fpga pause`、`/fpga resume` 会发送到全部在线主节点；暂停状态跨服务重启保存。模型或网络错误按持久退避重试，不会每秒发起新模型请求。

三台电脑在不同网络，使用同一 Tailscale tailnet，三个节点都要有可互访的 100.x 地址。每机配置另两台的 URL，B/C 不经过 A 中转。HMAC 共享密钥文件必须由三位成员通过可信渠道放在本机；公开分发包没有这个文件。健康探针和持久发件箱在无模型调用的后台运行，某节点离线时其他节点仍可相互收发。Windows 防火墙和 tailnet 权限须允许节点的 8787 端口。

仓库为**公开**。队友可直接克隆；没有写权限时，用 `gh auth login` 登录自己的 GitHub，再运行带 `-SetUpFork` 的入口创建 fork，用 `codex/b/<task-id>` 或 `codex/c/<task-id>` 分支向 `carolwjade/CarlandFPGA` 提交 PR。代码、约束、日志和可公开的实验结果进入远端；密钥、令牌、SQLite、私有硬件标识不进入公开仓库。

## 运行与诊断

本机配置位于 `.local/deployment/node-<a|b|c>/node-<a|b|c>.toml`。计划任务 `FPGA-Mesh-Node-<A|B|C>` 在成员登录 Windows 后运行。检查：

```powershell
Get-ScheduledTask -TaskName 'FPGA-Mesh-Node-A' | Select-Object State
& .local\venv\Scripts\python.exe -m unittest discover -s tests -q
```

不经计划任务也可前台运行：

```powershell
$config = (Resolve-Path '.local\deployment\node-a\node-a.toml').Path
pwsh -NoProfile -File deploy\run-node.ps1 -Node A -Config $config -Python '.local\venv\Scripts\python.exe'
```

主 Astra 回合有五个 `fpga_child_*` 动态工具，以及 `fpga_group_report`、`fpga_peer_send`、`fpga_child_group_report`。子实例不能主动读取飞书群或发消息；父 Astra 显式发布一个当前、已完成的子任务结果时，使用本机共用的 DeepSeek 飞书形象。父实例对重要子结果独立验证。人类新指令会排在同伴报告之前，并中断当前较早回合；暂停/恢复命令立即改变分派状态。每个回合有故障看门狗，不会因等待无限占用模型。

A 机是唯一烧录者。当前 `hardware_enabled = false`，直到板卡型号、驱动、烧录命令、日志采集与操作授权完成实机联调；B/C 只能请求 A 实测。后台配额读取不发起模型回合，剩余 20% 和 10% 时在飞书队列生成预警。Astra 的工作回合推理档位由选择器按任务选择，子回合始终是 `max`。当前仅验证 app-server 线程实际档位变化；Codex Desktop 当前聊天窗口右下角下拉框的视觉联动仍未确认。

当前群在飞书客户端被标为**外部群**。Add Bot 页面明确限定只能添加自定义机器人或已开启 external sharing 的应用机器人。六个应用因此还需核对外部共享资格；自定义 Webhook 机器人只能主动推送，不能替代需接收群内新指令的 Astra 应用机器人。参见[飞书群机器人说明](https://www.feishu.cn/hc/zh-CN/articles/360024984973-%E5%9C%A8%E7%BE%A4%E7%BB%84%E4%B8%AD%E4%BD%BF%E7%94%A8%E6%9C%BA%E5%99%A8%E4%BA%BA)。

线上与本地验证的区别见 [部署状态](DEPLOYMENT_STATUS.md)。

# FPGA Mesh 运行说明

每台电脑运行一个本地控制器、一个用该成员 ChatGPT 登录的 Astra 主实例，以及由 Astra 按任务自主伸缩的 DeepSeek V4.1 Flash 子实例池。默认有两个**配置就绪但未发起模型请求**的子实例；Astra 可保留一个、增加到两个以上或暂不调用。所有子实例的实际回合固定 `deepseek-flash` / `deepseek` / `max`。

## 本机安装与登录后自启

在仓库根目录执行；A/B/C 各机选择自己的节点字母和密钥文件。`-Python` 必须指向能运行该工程的 Python 可执行文件，不能使用 Windows Store 占位别名。

```powershell
$python = 'C:\path\to\python.exe'
pwsh -NoProfile -File deploy\install.ps1 -Node A -DeepSeekKeyFile 'C:\path\to\DeepCodex.txt'
$config = (Resolve-Path '.local\deployment\node-a\node-a.toml').Path
pwsh -NoProfile -File deploy\register-autostart.ps1 -Node A -Config $config -Python $python -StartNow
Get-ScheduledTask -TaskName 'FPGA-Mesh-Node-A' | Select-Object State
```

`install.ps1` 默认安装到仓库内被 Git 忽略的 `.local/deployment`，配置只记录密钥文件路径。计划任务会复制启动脚本到本地安装目录，并保存工作区路径；重复注册会更新本工程自己的任务。移动仓库后须从新位置重新注册，否则计划任务会在 `runner-error.log` 记录找不到源代码。控制器停止后，SQLite 中的任务与结果仍在。计划任务强制停止可能暂留旧的 `child-control.json`；重启时会以新端口和令牌覆盖，停机期间的本地调用会失败并可重试。

若只需前台运行：

```powershell
pwsh -NoProfile -File deploy\run-node.ps1 -Node A -Config $config -Python $python
```

## 主从调用接口

Astra 线程注册五个原生动态工具：`fpga_child_status`、`fpga_child_scale`、`fpga_child_delegate`、`fpga_child_wait`、`fpga_child_cancel`。同样的本地控制接口可由 MCP 或 CLI 调用；各项结果按 `job_id`、`instance_id`、`task_id` 和 `task_version` 持久关联。Astra 自行决定何时派工、分给几个子实例以及如何采用结果。`wait` 等待异步事件，不在等待期间持续请求模型。新的人类任务版本会使旧版本结果标记为 stale，并阻止认领过程中的旧派工落地。父子工作回合另有默认一小时的故障看门狗，可通过本机配置 `turn_timeout_seconds` 调整；超时只使当前回合失败并请求中断，不停止整个控制器。

诊断后台服务可使用 CLI；实际派工由 Astra 的工具调用完成：

```powershell
$control = (Resolve-Path '.local\deployment\node-a\.local\node-a\child-control.json').Path
& $python -m fpga_mesh.child_cli --control-file $control status
& $python -m fpga_mesh.child_cli --control-file $control scale 3
& $python -m fpga_mesh.child_cli --control-file $control delegate --task-id check-1 --task-version 1 --text '分析时序报告'
& $python -m fpga_mesh.child_cli --control-file $control wait --job-id '<上一命令返回的 job_id>'
```

如需直接检查某个 Astra 线程的当前持久推理档位，可用 `scripts/check_thread_effort.py`。Astra 的选择回合只判断下一任务应使用 `low`、`medium`、`high`、`xhigh` 或 `max`；实际工作回合以该档位调用。选择器无法判断或超时则用 `max`。该控制作用于后台 Astra 线程；Codex Desktop 当前聊天窗口的右下角下拉框是否视觉同步仍需单独验收，不能从 `thread/read` 结果推断。

## 仍需提供的部署输入

| 输入 | 存放方式 |
| --- | --- |
| B/C 成员登录与 DeepSeek 密钥 | 各自电脑本地，不提交仓库 |
| 飞书群 ID、三位人类身份、六应用凭据与权限 | 各机本地凭据配置；子实例共用本机一个 DeepSeek 飞书身份 |
| 跨网地址与共享通信密钥 | 各机配置和环境变量；B/C 需能不经 A 互连 |
| GitHub 私有仓库 URL、权限和 Git 作者信息 | 本地 Git 配置 |
| A 的板卡型号、驱动、工具链及采集方式 | 仅 A 的硬件服务配置 |

真实飞书、B/C 跨网、GitHub、FPGA 烧录的验收状态以 [部署状态](DEPLOYMENT_STATUS.md) 为准。当前这些缺少输入的功能保持关闭；本地协议测试不代表线上服务已经连通。

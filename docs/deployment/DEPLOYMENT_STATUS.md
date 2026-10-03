# FPGA 三机多 Agent 部署状态

日期：2026-10-03。分支：`codex/fpga-multi-agent-deploy`。依据：`docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.6。

## 已验证

| 范围 | 实证 | 结果 |
| --- | --- | --- |
| 协议、控制器、主从调用及回归 | `python -m unittest discover -s tests -q` | 116/116 通过；包含并行派工、取消、恢复、任务版本、动态扩缩、JSON-RPC 异常与凭据隔离 |
| 三节点本地模拟 | `artifacts/verification/local_simulation_20261003.json` | A/B/C 本地替身处理消息；去重、离线补发、空闲零模型调用通过 |
| 本机 Codex 协议 | Desktop 随附 Codex `0.160.0` app-server；`.local/protocol-ts` 协议产物 | 支持 `thread/start.dynamicTools`、`turn/start.effort` 和 `thread/read.reasoningEffort` |
| 本机 Astra 身份与路由 | `codex login status`，真实 Astra 回合元数据 | 本机使用 ChatGPT 登录；父实例走 `openai` / `gpt-6-astra`，未继承 DeepSeek API key |
| 真实 Astra→DeepSeek 调用 | `python -m scripts.smoke_parent_child --key-file <本机密钥文件>` | Astra 原生调用 `fpga_child_delegate`、`fpga_child_wait`，子任务完成并回传 `CHILD_OK`；父回合选 `medium`，子实例固定 `max` |
| 真实 DeepSeek 路由 | app-server 回合、`scripts.smoke_installed_node`、计划任务后台派工 | `deepseek-flash` / `deepseek` / `max`；最终后台任务返回 `FINAL_RUNTIME_OK`，密钥仅供隔离子进程使用 |
| 动态子池 | `scripts.smoke_dynamic_pool` | 三个不同子实例并行完成 `CHILD_1/2/3`，由默认 2 个扩到 3 个再缩到 2 个，均为 `max` |
| Astra 自主选择推理深度 | `python -m scripts.smoke_effort_switch` | 同一个真实线程先后选择 `low` 与 `high`，每次 `thread/read.reasoningEffort` 与所选档位一致；无效选择退回 `max`，超时中断选择回合，无法确认中断时关闭会话并阻止后续主任务 |
| A 节点本机常驻 | Windows 计划任务 `FPGA-Mesh-Node-A`，工作区 `.local/deployment/node-a` | 已注册、运行、手动停止后重启；重启后 2 个待命子实例和已完成任务记录仍在，后台派工实测通过 |
| 飞书、同伴、Git、板卡的本地协议 | 对应测试及原先模拟结果 | 六个固定身份、Astra-only 订阅、HMAC 通信、追加认领、Git 检查点、独占烧录队列的程序行为通过；尚不是外部服务实测 |

计划任务的状态码 `267009` 表示任务正在运行。A 机运行目录在仓库的 `.local/deployment` 内，未跟踪进 Git；原先的 AppData 安装路径在该执行环境中无法被 Windows 计划任务读取，已不作为当前常驻入口。

## 尚未验收的条件

| 条件 | 当前状态 |
| --- | --- |
| Codex Desktop 右下角下拉框的可视同步 | **未获可视验收**。app-server 已实测每回合设置及线程元数据变化；当前工具不能读取或驱动 Codex Desktop 的该控件，也没有证据表明本聊天窗口会自动切换到后台 Astra 线程。不能把线程元数据验证写成 UI 验收。 |
| 协作带来的 GPT 套餐 usage 降低、质量保持与总耗时提升 | **未验证**。真实父子调用已通，但仍需有代表性的成组任务、质量基准、完整 GPT usage 与端到端时间对照。 |
| B/C 两台电脑及各自的 ChatGPT 登录 | **SKIPPED**。当前仅有 A 机；B/C 仍须在各自电脑安装和登录。 |
| 飞书六应用、群消息与人类指令 | **SKIPPED**。缺群 ID、三位成员身份、六应用凭据及权限；仅本地协议测试通过。 |
| 跨网 Tailscale 与 A 离线的 B/C 实测 | **SKIPPED**。缺另两台电脑及组网身份。 |
| GitHub 共用私有仓库及 LFS | **SKIPPED**。仓库尚未创建，缺 URL、成员权限和 LFS 配额；仅本地 Git 行为测试通过。 |
| FPGA 板卡和工具链 | **SKIPPED**。缺型号、驱动、烧录与采集接口；硬件执行开关保持关闭。 |

## 凭据与边界

本机安装配置仅保存 `DeepCodex.txt` 的绝对路径，不保存 API key 明文；Astra 进程环境不包含 `DEEPSEEK_API_KEY`，子实例不继承 OpenAI API key。`.local/`、`artifacts/`、日志和 SQLite 状态被 Git 忽略。没有把本地替身测试记为飞书、GitHub、跨机或板卡真实通过。

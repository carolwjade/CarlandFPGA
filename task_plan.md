# FPGA 三机多 Agent 部署计划

Goal: 按 `docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` 完成本机可执行部署、自动化验证和持久记录；缺少外部账号、凭据、三机网络、Tailscale 或 FPGA 板卡的项目保留明确占位，不伪造验收结果。

## Constraints

- 不修改或复制 `~/.codex/auth.json` 中的私密凭据。
- 不把密钥、Token、飞书凭据或机器私密配置写入 Git。
- 不把本地替身测试写成真实模型、飞书、GitHub 或板卡验收。
- 用户要求中途不审批；外部依赖不可用时跳过并记录。
- 完成后提交本分支、生成本地验收报告，并触发 Windows 关机。

## Phases

### Phase 0: 冻结协议

Status: complete

- 定义节点身份、消息信封、任务状态、委托、实验操作和认领记录。
- 明确去重、版本、持久化和恢复语义。
- 通过场景走查和单元测试。

### Phase 1: 单机控制器

Status: complete

- SQLite 事件、收件箱、发件箱、任务和恢复存储。
- 事件驱动等待，不轮询、不因空闲发送模型请求。
- 三节点本地替身、重复投递、重启恢复和离线继续场景。
- 完整单元测试和端到端验证脚本。

### Phase 2: Codex 与动态子实例池

Status: complete

- 生成隔离的 Codex 配置模板，固定 `deepseek-flash` 和 `max`。
- 默认两个待命、按需扩缩、回收后身份不复用、真实路由守卫。
- Codex app-server 协议版本固定和最小连接验证。
- 真实订阅/API 调用受外部凭据限制的项目留空。

### Phase 3: 飞书六角色适配层

Status: complete

- 六个固定身份、人类来源校验、Astra 委托和子实例共享身份。
- 去重、权限、历史补收、编辑/撤回和人工暂停状态。
- 真实飞书连接和凭据输入留空。

### Phase 4: 三节点通信与 GitHub

Status: complete

- 节点间持久收发、确认、重试、HMAC 校验和本地 HTTP 传输。
- 追加式任务认领、Git 检查点、LFS 清单和远程不可达恢复。
- Tailscale、三台真实电脑、私有仓库凭据留空。

### Phase 5: FPGA 板卡实验服务

Status: complete

- 独占实验队列、`operation_id` 幂等、状态不明待核对和安全停止。
- 结果归档绑定代码、工具、板卡身份、哈希和原始日志。
- 实机工具链与 FPGA 连接留空。

### Phase 6: 跨阶段验证与交付

Status: complete

- 运行全量测试和端到端验收脚本。
- 生成 `docs/deployment/DEPLOYMENT_STATUS.md`，逐项标记已验证、跳过和原因。
- 提交分支，检查工作区，生成最终验收摘要。
- 保存后安排 Windows 关机。

## Decisions

| 决策 | 原因 |
| --- | --- |
| 在当前专用仓库内使用 `codex/fpga-multi-agent-deploy` 分支 | 用户要求不中断，当前目录即部署目标且只有设计稿；额外 worktree 会引入审批和路径分叉 |
| Python 3.12 标准库实现控制器与测试 | workspace 已提供 Python，避免安装依赖，便于三机复制 |
| SQLite 作为本地持久层 | 支持事务、幂等、重启恢复和并发读，不依赖外部数据库 |
| 真实外部平台统一放在适配器后 | 无凭据时仍可验证确定性行为，避免替身冒充真实验收 |

## Errors Encountered

| Error | Attempt | Resolution |
| --- | --- | --- |
| OpenAI 官方页直连超时或 403 | 1 | 已尝试官方域名；后续使用本地 Codex CLI 协议产物，并在报告中标记网页核验受限 |
| `python` 命令指向 Windows Store 别名 | 1 | 使用 workspace 提供的 Python 3.12 绝对路径 |
| `git` 尚无初始提交 | 1 | 在新分支上先完成实现，再按阶段提交 |

## Next Step

提交部署分支并触发 Windows 关机。

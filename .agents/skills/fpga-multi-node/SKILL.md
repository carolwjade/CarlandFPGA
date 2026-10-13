---
name: fpga-multi-node
description: Use for CarlandFPGA multi-machine tasks on host A, including Astra coordination, controlled model delegation, peer communication, Git PR handoff, shared-board scheduling, and recovery of the existing mesh.
---

# 多机协作：主机 A

本包用于 A。先读 [角色声明](skill-role.json)，再用现有节点配置或控制器 `health` 核对本机身份；不要靠窗口标题或历史 IP 认定节点。B/C 使用共用客机包。A 负责统筹依赖、集成、最终验收和唯一物理板卡操作，各机仍独立接收人类指令、访问 GitHub、派工和两两通信。

## 每个项目会话

1. 先确认本轮人类需求、任务 ID/版本、负责人、允许操作与完成条件。纯进度询问只读账本和相应节点证据；不升级版本、抢占任务或唤醒模型。更改/暂停指令优先处理。沿用身份、凭据、配置、工作区、账本与常驻服务。
2. 读 [协作协议](references/protocol.md)。独立任务走 `fpga_session_open`，跟进复用 task_id；从实际允许目录安排下一回合模型/深度。决策、排障难点、优化和最终验收由质量主模型最高可用深度完成。执行按需交给 DeepSeek Flash/max；原生 GPT 仅用于明确特殊能力且持有有效租约。
3. 给 B/C 分配互不重叠的真实任务，说明 work_id、目录/分支归属、测试和证据。正式跨机派工用 `fpga_peer_send`；群公告只用于必要的人类沟通和发现，不将机器人消息当人类授权。
4. 按 [交接闭环](references/handoff.md) 实际获取 PR head，核对清单、提交与字节哈希，运行相应验证，在同一 PR 留反馈，取得客机读回回执。板卡请求由 A 独占执行；设计和工具细节读取 [单机技能](../pynq-z2-single-node/SKILL.md)，不因安装本技能启用硬件队列。
5. 只验收本轮批准范围。逐项区别 queued、传输 ACK、模型完成、独立验证与正式交接。已有可信证据可复用；不因验收展开额外故障注入或重复派工。结束有效模型回合，保留三机常驻监听；等待由普通程序完成，不调用模型。

## 群沟通

所有本机 GPT 主会话使用既有 Astra-A，所有 DeepSeek 执行实例共享既有 DeepSeek-A。人类 > 主 > 子；子实例不自主读群或发言，直属主会话仅为有效委托发布结果。人类未询问时，不主动群发本机/同伴上线、离线、重连、恢复及健康观测；内部探针和持久补发继续。明确任务阻塞只说明任务影响。此静默规则覆盖 A/B/C 和 DeepSeek，优先于旧项目书的上下线公告条目。

## 按需查阅

- [项目书需求对应](references/requirements.md)：三机职责、自治、额度、恢复和成果要求；工程目标与已验证结果分开。
- [协作协议](references/protocol.md)：身份、命令入口、会话、派工、持久通信和等待。
- [交接闭环](references/handoff.md)：A 接收与反馈、B/C 提交与读回、共享板卡实验。
- [已发生问题的处理](references/recovery.md)：遇到相同症状时定位并最小恢复。

版本与配置见 [安装/升级](INSTALL.md)。技能与包仅保存操作知识；历史报告不证明当前连接、权限或板测状态。运行时故障按相关条目处理，不把整套项目书和故障表预先塞入每次任务。

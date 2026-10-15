# 主会话权限与绑定恢复

2026-10-15 人类明确授权主会话自主开启、继续、终止和归档多个工作会话，
自选实际可用模型与推理深度，不再逐项询问。现行协议、A/B/C 技能入口、
运行时注入提示及模型路由检查均按此更新。保留官方目录支持性校验，移除
关键任务强制最高模型/深度、Flash 优先及原生特殊能力限制。

Desktop/native 的任务与独占文件记录即可安排执行；mesh 的租约只约束选择
该通道的 job。停止后必须确认真实终态再交出文件，归档不代替停止核验。
H01-H15、唯一当前主负责人、实板仅 A 操作及独立证据规则不变。

## 原地址暂未就绪

旧启动顺序先打开本地控制入口，再绑定 peer 地址。地址暂不存在时 Python
asyncio 会丢失 EADDRNOTAVAIL，抛出无 errno 的通用绑定异常；runtime 清理
全部入口后由 supervisor 反复重启，导致本地任务入口一起消失。

数值 IP 现显式绑定原地址与原端口后交给 asyncio。仅 EADDRNOTAVAIL/10049
进入 waiting，本地控制继续工作，由原 peer 重试循环等待；不新增控制器或
发送器、不切换到通配地址、不换端口。恢复成功进入 listening。
EADDRINUSE/10048、权限等错误保留为 failed；首次启动继续失败并清理，
延迟恢复中的永久错误停止绑定重试，原本地控制仍可诊断。

health 字段：peer_bind_state 为 disabled/waiting/listening/failed/stopped；
peer_bind_error 保存监听错误，peer_listen_port 在未监听时为 null。
传输 flush 成功不会清除绑定错误。健康变化仅保存在本地，不自动发群公告。

## Desktop 唯一所有者

会话数据库同目录可保存 external-task-owners.json：

```json
{
  "task-id": {
    "owner_kind": "desktop",
    "thread_id": "actual-desktop-thread-id"
  }
}
```

主会话仅在核实实际交接后记录声明。mesh open/prepare/route 每次读取并拒绝
该 task；不改旧 SQLite 关联，也不启动或接管 Desktop writer。其他 mesh
任务照常。文件损坏或不可读必须报错。该记录只阻止后台恢复，不代表获准
占有别人的工作。运行中的旧执行仍需先真实停止，不能只写声明强行夺取。

## 验证与部署

定向测试覆盖本地入口存活、地址恢复、端口和权限错误、等待中停止、真实
Server 注册 accept 后的取消清理、HMAC、去重、显式模型路由及外部所有者。
源码部署沿用现有节点；本轮原服务已退出，核实原 OS 租约均释放后，仅更新
已审查文件，再启动原 scheduled task。保存原失败和队列，不重新 Join，
不改凭据、地址、hardware_enabled 或旧任务绑定。

软件回归不证明 B/C 已升级；真实服务恢复以新 PID、原配置身份、本地控制
发现和原地址监听的本轮读回为准。

## 本轮实际恢复读回

源码 `6663173d4b0b1092501c304269fc80f36a6c505d` 已通过93项回归，独立复核另跑28项通过。原节点配置、凭据和任务终态原行保留。原定时任务第一次已到 listening，随后以0xC000013A终止，终止来源未确认；将同一任务入口由既有venv的python.exe改为pythonw.exe，参数和目录不变后，实际控制入口与原地址HMAC检查通过，新进程持续存活且重启0次。仅软件测试模拟了地址缺失/恢复，本轮没有主动中断Tailscale。

对应公开读回摘要见同名JSON；完整私有现场、旧任务XML与故障日志保留在原工作区。当前Desktop持久Goal已建立，未启用周期性模型轮询；永久零空闲token事件唤醒尚未验证。

# 代码、证据与共享板卡交接

## B/C 提交

1. 本轮负责人在独立任务目录和 `codex/b/<task-id>` 或 `codex/c/<task-id>` 分支工作。完成对应验证，保存命令、版本、退出码及原始日志字节。现有 Git 忽略 `artifacts/`、`logs/`、`*.log`；公开交接证据复制为任务目录内的 `.txt`，用 `git ls-files` 核对真实跟踪。凭据、SQLite、私人板卡标识不提交；大波形/bitstream 按现有 LFS 规则保留清单与哈希。
2. 先提交设计/测试源文件，记录完整源码 SHA；创建 `handoffs/<node>/<operation-id>/input.json`。字段见下文。代码与证据变化使用新操作和清单，保留原失败结果。
3. 用包内标准库工具创建和校验，不启动硬件服务：

```powershell
python -X utf8 .agents/skills/fpga-multi-node/scripts/handoff.py create --root . --input handoffs/<node>/<operation-id>/input.json --output handoffs/<node>/<operation-id>/manifest.json
python -X utf8 .agents/skills/fpga-multi-node/scripts/handoff.py verify --root . --manifest handoffs/<node>/<operation-id>/manifest.json
```

4. 提交清单，推送自己的现有 fork/节点分支，向现有上游 `carolwjade/CarlandFPGA:main` 建 PR。PR 正文写 operation_id、request_hash、源码完整 SHA、PR head、清单位置、复现命令和预期结果。正文使用 UTF-8 文件传 `gh --body-file`，避免 shell 转义或编码改变内容。
5. 以现有 Astra 的 `fpga_peer_send` 告知 A PR 与工作身份。网页打开、提交保存在本地、通知 queued 均不能报告正式交付完成。

`input.json` 包含 `request`、`artifacts`、`stages`。request 恰含 operation_id、task_id、task_version、requester（node-b/node-c）、code_commit（完整源码 SHA）、非空 test_steps 与 expected_result。artifacts 为根目录内相对路径；stage status 为 passed/failed/blocked/not_run，passed 必须有非空真实 log 路径。仿真、综合、实现、实板分别记录。SHA-256 证明字节，不证明日志判定。

## A 接收与反馈

收到请求先核对负责人、任务版本和本机权限；实际 fetch 对应 PR head 到隔离目录，不覆盖活动工作区。取得完整 head SHA，核对来源、源码提交、manifest/request_hash、全部文件与日志的字节哈希，运行 PR 的相关验证。

在**同一 PR**留下真实反馈：operation_id、request_hash、tested_commit（实际检出的完整 head）、阶段结论、命令/工具版本/退出码、日志与产物路径和哈希。失败说明复现条件；未执行阶段按本轮真实范围记录。PR 后续新提交使旧反馈只适用于旧 SHA，不能继承通过。B/C 实际读取匹配反馈后回执，完成交接闭环。测试 PR 可留证，合并/部署按项目权限和规则，验收反馈不自动授权合并。

## 共享 PYNQ-Z2

A 是唯一物理操作者，串行占用准备、上传/烧录、运行、采集、清理全过程。B/C 可以提交脚本、代码/产物哈希、复现步骤与预期结果，不直连板卡。A 使用现有 `pynq-z2-single-node` 与已授权板测入口，返回真实 stdout/stderr、退出码、板卡/镜像/工具及文件哈希；上传与 Python 烟测只证明该步骤，RTL 接口或性能要有对应实际加载与测量。

A 离线时 B/C 保留请求并继续独立任务。A 回来先核对当前指令/版本及板卡状态。查询回执丢失的原 operation_id；不确定是否已执行时先核对现场，禁止盲目重烧。安装技能不打开 `hardware_enabled`，不把设计中的硬件队列当作已运行适配器。

## Astra 附件

各自既有 Astra 的 `im:resource` 要由该应用所有者授权；更新包不授予云端 scope，DeepSeek 不增权。读回真实群/私聊消息与附件键，实际下载附件，再按原始字节核对 SHA-256。upload file_key 或群公告不等于实际下载；不同收件人/群不能互相代替收件证据。完整 Secret/HMAC 经已授权可信私聊/本机文件交接，不写群或公开证据。

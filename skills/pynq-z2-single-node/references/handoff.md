# 单机交接清单

当需要给 A 机板测或给其他开发者复现时，把源文件、约束、测试脚本、日志和报告放在同一根目录下，再使用技能脚本。单机独立开发也可用清单留存证据。`preflight.py` 仅报告 Vivado/ModelSim 的命令路径和 `board.status = not_checked`，不检测版本、连板或测试通过。

在根目录内写输入 JSON。示例中的字段名与现有 `fpga_mesh.hardware.HardwareRequest` 相同；示例状态仅说明结构，使用时填写本轮真实结果：

```json
{
  "request": {
    "operation_id": "experiment-001",
    "task_id": "single-node-001",
    "task_version": 1,
    "requester": "node-b",
    "code_commit": "<actual-git-commit>",
    "test_steps": ["run RTL regression", "inspect routed timing"],
    "expected_result": "<this-iteration-acceptance-criteria>"
  },
  "artifacts": ["rtl/top.sv", "constraints/top.xdc"],
  "stages": {
    "simulation": {"status": "passed", "log": "logs/simulation.log"},
    "implementation": {"status": "not_run"},
    "hardware": {"status": "blocked"}
  }
}
```

用实际存在的相对路径，统一 `/` 分隔；不得指向根目录外。`passed` 阶段必须指向非空的实际运行日志；失败阶段也尽量附日志。允许的状态为 `passed`、`failed`、`blocked`、`not_run`。缺 Vivado/板卡等前置条件记 `blocked`，本轮未安排的阶段记 `not_run`。`code_commit` 应是输入文件对应的提交；若工作树另有改动，将其另列为 artifact 并在交接说明中标明，不能误称提交可复现全部源文件。

```text
python <skill-dir>/scripts/handoff.py create --root <evidence-root> --input <evidence-root>/handoff-input.json --output <evidence-root>/manifest.json
python <skill-dir>/scripts/handoff.py verify --root <evidence-root> --manifest <evidence-root>/manifest.json
```

生成的 manifest 包含 `schema_version`、`request`、按现有 `HardwareRequest` 规则计算的 `request_hash`、`artifacts`、`stages`，以及每个源文件与日志的 `size` 和 SHA-256。`verify` 会复核字段、根目录范围、文件清单与哈希；失败时返回非零退出码。同一路径再次 create 只接受内容完全相同的清单；若证据或请求已变化，应新建操作号与清单路径，不能覆盖已发布记录。哈希只证明交接后字节未变化，不能证明日志确实满足测试判据；接收方仍需审阅日志和报告。B/C 传给 A 时只交代码提交、清单、复现步骤及测试建议；物理板卡操作由 A 安排，清单本身不会进入三机硬件队列。

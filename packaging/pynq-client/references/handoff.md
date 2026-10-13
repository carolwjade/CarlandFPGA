# 本机清单工具

多机分工、PR 提交、A 实测反馈与客机读回统一遵循项目根 `.agents/skills/fpga-multi-node/references/handoff.md`，不在单机包重复维护。B/C 需另装共用多机客机技能；本单机包不替代协作控制器。

本包的 `scripts/handoff.py` 是标准库工具，可独立 create/verify 请求与文件 SHA-256。字段为 request（operation_id、task_id、task_version、requester、code_commit、test_steps、expected_result）、artifacts、stages。路径必须在所选 root 内，统一 `/`；passed 必须引用非空真实日志。清单不可覆盖，内容变化使用新 operation_id。哈希只证明字节一致；A 板测还需真实板卡证据。

```powershell
python <skill-dir>/scripts/handoff.py create --root <仓库> --input <仓库内input.json> --output <仓库内manifest.json>
python <skill-dir>/scripts/handoff.py verify --root <仓库> --manifest <仓库内manifest.json>
```

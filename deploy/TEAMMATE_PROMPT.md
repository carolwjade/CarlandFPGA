# 给 B/C 本机 Codex 的部署任务

我是 CarlandFPGA 的节点 B 或 C。以本机既有 node_id 为准，沿用我的官方 Codex 登录、Astra/DeepSeek 应用、密钥文件引用、Git/fork、工作区和任务状态；身份不明时先核对，不新建身份。

请从 **B/C 共用多机客机技能包** 安装项目入口：

```powershell
python -X utf8 .agents/skills/fpga-multi-node/scripts/install.py --project-root <原项目> --node <B或C>
```

此后全部项目会话读取原项目根 `.agents/skills/fpga-multi-node/SKILL.md`。模型/派工、任务归属、PR/证据交接、A 实测反馈、恢复和静默在场只维护在那里，不再照旧提示重复执行。仅安装技能时不要运行部署、重载服务或增加云端权限。

**已接入节点更新运行源码：** 读取 `docs/deployment/IN_PLACE_UPDATE_2026-10-11.md`，用原 `deploy/Update-FPGAMesh.ps1` 先 CheckOnly；保留本地修改、配置、凭据、账本及原服务，按空闲栅栏更新。不要重新 Join，不用旧远端覆盖新代码。

**首次部署：** 读取运行包 `README.md`、`docs/deployment/OPERATIONS.md` 和 `deploy/HUMAN_STEPS.md`，从解压根目录运行 `pwsh -NoProfile -File deploy/Join-FPGAMesh.ps1 -Node <B或C>`。按实际需要填本人 DeepSeek/HMAC 密钥的文件路径及当前同伴地址，不能贴密钥内容。入口尝试工具安装、仓库/fork、本机依赖、两个应用、发信读回及常驻服务；每身份核对真实消息与实际 provider/model/effort 结果。云端权限和扫码由原账号完成，准确汇总缺项并继续独立步骤。

保存本机 `setup-status.json`、`NEXT_STEPS.md` 及原始证据。PYNQ 设计工具另用本机匹配的 board-free 单机技能，不装 A 的上传包。B/C 不直接上板；成果、清单、验证要求交 A，读取同一 PR 对应实际提交的反馈后回执。禁止主动群发上下线/重连/健康新闻；等待由常驻程序监听，不调用模型。

# PYNQ-Z2 单机开发入口

唯一当前入口是 [项目单机技能](../../.agents/skills/pynq-z2-single-node/SKILL.md)。设计、工具和实板知识只维护在技能中；协作、清单、PR与恢复只维护在多机技能。两者可使用本地工具独立工作，不要求启动三机服务。

A 读取主机版并独占物理板卡；B/C 共用客机版仅开发、仿真、构建和准备输入，通过仓库交 A 执行。两个技能均放项目 `.agents/skills`，新版安装与全局旧残留清理见 [统一说明](../../.agents/skills/fpga-multi-node/INSTALL.md)，在新会话生效。

```powershell
& .local/venv/Scripts/python.exe -X utf8 .agents/skills/pynq-z2-single-node/scripts/preflight.py
```

工具路径发现、实际启动、仿真、综合、实现、上传烟测和实板测量分层留证。历史连接实证见 [2026-10-09 板端运行](SINGLE_NODE_BOARD_LIVE_2026-10-09.md)，metadata/BRAM 经验见 [实板流程](../../.agents/skills/pynq-z2-single-node/references/board-verification.md)。历史命令和测量保留原字节，不能代替当前现场。

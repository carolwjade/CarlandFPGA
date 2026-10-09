# 单独安装 PYNQ-Z2 单机技能

这个 ZIP 只包含 `skills/pynq-z2-single-node/`，不配置三机控制器、飞书、GitHub 或 DeepSeek。解压后在 PowerShell 中运行：

```powershell
pwsh -NoProfile -File .\skills\pynq-z2-single-node\Install.ps1
```

脚本将技能复制到当前用户的 `$CODEX_HOME/skills/pynq-z2-single-node`；未设置 `CODEX_HOME` 时使用 `$HOME/.codex/skills`。已有不同版本会移入同目录的带随机后缀备份；同版本重跑不会重复安装。安装后在新的 Codex 会话中要求使用 `pynq-z2-single-node` 技能，先执行技能内的预检脚本，再按真实板卡和工具输出工作。B/C 仅能仿真与提交证据，实板由 A 操作。

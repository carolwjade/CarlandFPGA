# 项目内配置

两个技能作为一组安装，A 用主机包，B/C 用共用客机包。统一升级和旧残留清理见 [安装流程](../fpga-multi-node/INSTALL.md)。只写当前项目 `.agents/skills`，不再运行旧 Install.ps1 或安装到全局。新版在本项目的新会话中生效，当前运行回合保持原上下文。

A 首次实板引导才使用已有 Python 的 pyserial 与 Windows OpenSSH；按 `requirements-board.txt` 安装依赖，复用现有环境和密钥。串口须已登录 shell；多串口/网卡传实际 --serial、--ifindex。既有可信连接传 --host、--ifindex 可跳过串口引导。

```powershell
& .local/venv/Scripts/python.exe -X utf8 .agents/skills/pynq-z2-single-node/scripts/preflight.py
# 仅 A 在本轮授权和板卡独占成立时运行：
python -X utf8 .agents/skills/pynq-z2-single-node/scripts/board_run.py --script <已审阅文件> --output-dir <本轮证据目录>
```

B/C 包移除了物理脚本及其依赖，不执行 A 命令。安装不重新入网、不启动/重启服务、不修改硬件队列或云权限。

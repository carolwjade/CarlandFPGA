# 两技能项目安装与升级

版本 `2026.10.13.3`：项目只配置 fpga-multi-node 与 pynq-z2-single-node。A 主机包允许 A，B/C 共用包按本机既有 node_id 选择 B 或 C；不另建全局技能。解压到临时目录，从解压根使用实际 Python 3.12+：

```powershell
python -X utf8 .agents/skills/fpga-multi-node/scripts/install.py --project-root <现有项目绝对路径> --node A --cleanup-legacy
# 客机同一命令将 --node 改为 B 或 C，必须使用客机 ZIP。
```

安装器校验完整 MANIFEST revision、版本、文件集合/原始字节哈希、两个角色和正式节点配置后，互斥更新项目 `.agents/skills` 中这两个目录与根 AGENTS 入口。同版重装保持不变，旧内容存本项目 `.local/skill-backups` 的非发现备份；其他项目规则和不相关技能保留。既有配置、凭据、账本、任务、服务和人工暂停不修改。

`--cleanup-legacy` 清除确属本项目的旧全局同名技能与备份（既有 CODEX_HOME/skills、用户 .codex/skills、用户 .agents/skills），先保存项目内 ZIP 和清理记录。拒绝目录链接/越界路径；未知名称或身份不明的技能不删除。旧项目 `skills/pynq-z2-single-node` 由本轮迁移清除，保留历史 Git 与测量证据；旧桌面交付包先归档进项目再替换新版。不要把备份的 SKILL.md 目录放进任何技能发现根。

两个角色 ZIP 从干净、已提交、跟踪的源码构建：

```powershell
python -m fpga_mesh.distribution --profile project-skills-a --output artifacts/skills-2026.10.13.3-a.zip
python -m fpga_mesh.distribution --profile project-skills-bc --output artifacts/skills-2026.10.13.3-bc.zip
```

B/C 上线后读取新版本与 SHA-256，保存本地改动，在现有项目执行安装和旧残留清理，然后回报本机 node_id、revision、两个技能文件哈希、清理结果与新会话入口。只有发送/ACK 不能称已更新。使用既有持久通信，API 不可用按协作协议的替代链路处理。

新版在开启本项目的新会话后生效。根 AGENTS 要求全部会话读取统一协作入口，单机开发按任务读取 PYNQ 技能；当前生成回合不重载。安装只升级技能，不重新 Join，不重启控制器，不授予云 scope，不开启 hardware_enabled。

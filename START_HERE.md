# 给 B/C 队友

既有节点使用 B/C 共用双技能包 `project-skills-bc`。解压到临时目录，从该解压根运行：

```powershell
python -X utf8 .agents/skills/fpga-multi-node/scripts/install.py --project-root <原项目绝对路径> --node B --cleanup-legacy
```

C 改 --node C；必须匹配本机正式配置中的 node_id。一次安装项目内 fpga-multi-node 与 pynq-z2-single-node 两个技能，核对版本/清单哈希并清理已确认的旧全局与旧项目路径。保留本地身份、凭据、配置、账本、改动和服务。新版在本项目的新会话生效；单机技能已经在同包中，客机无实板入口。

运行控制器 ZIP 与技能包分开。仅升级技能不要 Join 或重启服务；需要更新已有控制器源码时使用原 Update 的 CheckOnly 与空闲栅栏。首次入网才读 [队友提示](deploy/TEAMMATE_PROMPT.md) 和 [人工步骤](deploy/HUMAN_STEPS.md)，完成 Join 后安装本机客机技能，再开始设计任务。

公开包没有 API key、飞书 Secret、HMAC、SSH 私钥或官方登录信息。成员沿用自己的认证；地址/权限看本轮真实读回，不使用历史 IP。飞书 API 受限可用既有 peer、GitHub 与已授权群直发补齐，分别记录发送、读回、下载哈希和本机安装完成。默认静默在场，等待由常驻程序完成。

仓库：[carolwjade/CarlandFPGA](https://github.com/carolwjade/CarlandFPGA)。公开克隆不等于写权限；B/C 使用现有 fork/PR。详细升级见 [.agents/skills/fpga-multi-node/INSTALL.md](.agents/skills/fpga-multi-node/INSTALL.md)。

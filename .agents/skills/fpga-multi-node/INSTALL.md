# 项目级技能安装

这是 A 主机包；B/C 使用共用客机包。技能只更新知识和本项目入口，依赖各机既有控制器，不安装/重启服务、不迁移凭据、不重新入网。

解压后使用已有 Python 3.12+，以实际项目路径与节点运行：

```powershell
python -X utf8 .agents/skills/fpga-multi-node/scripts/install.py --project-root <现有CarlandFPGA目录> --node A
```

B/C 同一命令将 `--node` 改为本机 B 或 C。安装器先校验 MANIFEST 的完整 revision 和文件哈希，再核对既有节点配置与允许角色。只复制 `.agents/skills/fpga-multi-node` 并在根 AGENTS 维护一个入口块，其他项目规则保留；原技能备份在本项目 `.local/skill-backups/`，同版重装不重复备份。配置、账本与服务不修改。

项目根及子目录的新会话自动发现统一技能；根 AGENTS 要求全部会话遵循它。已生成的回合保持原上下文，不要求为技能升级中断活动会话。只按需载入参考文档。

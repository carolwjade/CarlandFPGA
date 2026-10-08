# PYNQ-Z2 单机技能本地验收（2026-10-08）

此记录验证的是技能与本机工具链入口，不是随钻测井方案或 PYNQ-Z2 板卡的功能验收。源码提交为 f500fc2c7e31fea9edee2a70acaac2c4793135b8。

| 检查 | 观察结果 |
| --- | --- |
| 技能格式 | skill-creator quick_validate.py 输出 Skill is valid!；PyYAML 6.0.2 只安装在被忽略的临时校验目录 |
| 专项测试 | unittest discover -s tests -p test_pynq_z2_single_node.py -v：17 个通过 |
| 全仓回归 | unittest discover -s tests -q：187 个通过；现有依赖发出 deprecation 和 asyncio ResourceWarning，无失败 |
| Python 编译 | compileall -q skills/pynq-z2-single-node/scripts fpga_mesh：退出码 0 |
| 环境探测 | ModelSim 指向 C:\modeltech64_2020.4\win64\vsim.EXE；Vivado 未从 PATH/环境变量发现；board.status = not_checked |
| ModelSim 烟测 | 在纯 ASCII 临时目录用 vlib/vlog/vsim 编译运行 4 位计数器与 testbench；日志包含 PYNQ_SKILL_MODELSIM_SMOKE_PASS，Errors: 0，Warnings: 0 |
| 交接清单 | handoff.py create/verify 对烟测 RTL 与日志检查 4 个文件，verify 返回 valid=true；清单 SHA-256 为 319d744ed6d4d53343704f3fabbf745c161747575d56365be50259ae2d6dfdda |

烟测交接的 simulation 标记为 passed，synthesis、implementation、hardware 均为 not_run。它只说明本机 ModelSim 和清单流程可运行；没有做目标工程的综合实现、时序收敛或实板测试。后续目标方案确定并具备 Vivado/开发板后，按技能分层补齐真实证据。

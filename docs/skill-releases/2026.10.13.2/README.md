# 项目技能 2026.10.13.2

基准为项目设计稿 v0.8 与后续人类更新；两个项目技能、多机与单机各分 A 和共用 B/C 版本。唯一发现根 .agents/skills，单一清单工具，短入口按需读共同引用。metadata/BRAM 经验来自原板测，不在本轮重跑。

- 代码/包源提交：ec81863a086e8c2066fe4bcb2fc2a856d4b7d527。
- [代码 PR #12](https://github.com/carolwjade/CarlandFPGA/pull/12)，未合并；[角色包发行](https://github.com/carolwjade/CarlandFPGA/releases/tag/project-skills-2026.10.13.2) 为该源码的 prerelease。
- 334 项全量回归通过；最后模板重定向拒绝补项后 29 项分包/安装回归通过，无 skip。Windows junction、并发、双技能回滚、身份和旧清理边界均有真实本机回归。
- openai/gpt-6-astra/ultra 质量主会话 v1 给两处文档修复，v2 完成 REVIEW_PASS；最终由 A/root 核对安装与发布。
- A 的两个技能 22 个文件逐字节匹配包与 Git raw blob；旧全局同名与两备份、旧项目单机路径实际清除，项目内 ZIP 保留旧字节。配置、服务 PID 保持不变，第二次安装 unchanged，新会话生效。
- B/C 19 文件同一个无板卡包，已通过原 peer 各自投递更新请求；传输 ACK 不代表安装完成。群材料及客机回证在 closeout 独立记录。

package-verification.json 绑定两个 ZIP 的完整 SHA/CRC/源 blob/链接校验；A-install-verification.json 记录实际安装结果；quality-review.json 与 publication.json 记录完成主会话和实际远端资产 digest。private 配置、原备份和 UI 截图留项目本地，未公开。

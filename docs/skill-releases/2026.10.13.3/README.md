# 当前项目技能 2026.10.13.3

本版接续2版的统一设计和完整回证，修复B实际安装前读取既有CRCRLF配置失败；原失败发生写入前，保留原记录，不重写节点TOML。仅在内存采用与控制器一致的通用换行解析，原始config_bytes继续用于竞态与配置不变性校验。

先用真实字节结构复现旧实现：CRCRLF、单CR、含BOM的CRCRLF三种情形报TOMLDecodeError；CRLF已有支持。修复后30项相关回归通过，其中同一测试对四种结构均核对原字节不变及同版no-op。此前334项全量通过，文档最高质量主会话v2 REVIEW_PASS保留在2版回证；本修复由A/root主模型核对代码及真实测试。

包源111781bf9939ee15fced924c09eb680a101ff1ad；两个ZIP均CRC、逐文件SHA和Git raw blob一致，版本3角色匹配。A实际安装两技能22个文件，配置和服务PID不变，无确证旧残留，同版unchanged；新版新会话生效。BC19个文件无物理入口，正式安装和群文件回读单独见closeout。

[代码PR12](https://github.com/carolwjade/CarlandFPGA/pull/12)未合并；[当前角色包发行](https://github.com/carolwjade/CarlandFPGA/releases/tag/project-skills-2026.10.13.3)。2版已标superseded，原字节与失败回证作为历史保留，当前A及桌面交付已统一3版。

C 的 `SKILLS-20261013-UNIFIED-C/v2` 最终 Desktop 回执已替代旧等待状态：报告正式项目 19 文件安装校验通过、旧发现入口先归档后清理、同版 `unchanged`，配置、AGENTS 与服务不变。A 已独立复核本地发布 ZIP 的 CRC、MANIFEST 全部文件、角色及两个报告入口哈希；C 的安装现场和备份保留为客机报告证据，新会话加载尚未验证。原失败/中断操作保留，旧待处理请求仅可读回或同版 no-op，不得降级。具体消息 ID、版本及证据边界见 [closeout.json](closeout.json)。

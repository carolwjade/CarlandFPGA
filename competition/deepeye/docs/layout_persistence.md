# 私有布局保存与重开（G02 增量）

本增量将另存为接到已审查的 Windows 独占源句柄发布原语。它仍是待主会话
独立审查的候选；headless 软件结果不等于正式 G02、真实鼠标/DPI、H09、
完整双 H12 或29卡验收。合同 H01-H15 不变。

编辑或停止状态可保存/打开，运行、暂停或锁定状态仍禁止。保存使用明确的本地
绝对路径，只创建新文件，不覆盖目标。保存期间有独立提示，Save/Open 按钮
禁用；界面仍可绘制和响应，保存不修改几何、选择、撤销/重做、种子、运行、
链路或控制状态。超时后普通编辑可继续，未结束的保存仍占用唯一保存槽。

5000ms 等待截止时显示“保存结果未知，文件可能已写入；请检查目标文件，勿
自动重试”。这不表示失败或取消。文件、临时源或已创建的父目录都不会被调用方
删除，也不会重放请求。独立 helper 的6秒 watchdog 在普通调度下自退出124，
该值既可能在发布前出现，也可能在发布后出现。解释器启动、调度或内核停顿
不受严格 OS 截止保证；真正未结束的 worker 被保留，不 join、不重启、不重试。
同一路径的 unknown 结果在本进程继续隔离。重启不自动恢复或重放；后续明确的
另存为可选择新路径。迟到的结果单独记录/提示，不替换原 unknown，也不回放旧几何。

`LayoutStore.save_new_async` 供 shell await；兼容 `save_new` 也走同一安全 worker，
有限等待后返回。旧临时路径检查、FileAccess 写入和 Godot rename 发布/清理算法
已移除。目标文件只由 Windows leaf 的原始源 HANDLE 写入、flush、重读和单次
no-replace rename 发布。原语仅支持现有已审范围：普通固定本地 NTFS、直接
HarddiskVolume 盘符映射、支持的绝对路径/父目录。并发源与目标安全沿用独立审查
和原19项 NTFS 证据；本次不重跑旧原语测试。

UNC、设备路径、ADS、NUL、traversal 和显见非法/保留名称在 mkdir 前拒绝。
可信运行环境预检后，worker 可递归创建缺失父目录；这是独立、非原子的便利步骤，
可能先于 leaf 的不支持卷/祖先拒绝发生，失败也不删除父目录。它不能消除并发改链，
不等于整个保存事务原子。特权命名空间/驱动过滤/ACL/盘符改映射与断电持久性
仍不在该限定承诺内。

打开仍使用原有1MiB/UTF8有界读取与严格几何 codec，校验成功才一次替换文档。
成功打开会清空历史和选择、设置来源“文件布局”、种子未知；失败保持当前状态。
codec/文档/控制逻辑没有改变。JSON 仍只含 schema、不可变合同与 requirements
hash、m 单位、obstacles/gates 几何和 layout_hash；不含运行/链路/控制/模型/种子/
路线/真值。layout_hash 是规范几何内容一致性标识，不是签名或权限。

源项目请用 `simulator/native/run_viewer.py`，明确传入经过固定 SHA256 验证的
Godot 路径和独占 userdata/cache/TEMP 目录。启动器使用当前真实 Python 路径，
核对 interpreter/base/DLL/pyvenv.cfg 等小型身份清单；现有 CPython/stdlib 安装
是信任边界，不假称完整标准库闭包。仅子进程获得显式绑定和环境白名单，provider/
FPGA 凭据与 PATH/PYTHONPATH 不复制。无全局配置或服务变更。具体命令见
`simulator/native/README.md`。PCK 导出须另行安装真实文件侧车/runtime 与等价
固定 pins；本增量不建立或声称导出安装可用。

helper 只接收一帧不超过1MiB的严格 UTF8 opaque 几何；argv 不传目标或负载，
只含固定 bootstrap、bundle 路径和其 pin。校验 helper/leaf 原始字节后直接执行
那些已校验字节；不从布局 JSON 导入模块，不注册 AI/provider/control/service。
工作线程独占 pipe，不调用 SceneTree/文档/控制。主循环只查看锁保护状态，
Thread 不再 alive 才 join。精确原子进程退出>=0和独占未释放 map 条目均确认后，
只消费一次原 HANDLE cleanup；FAILED 不作停止证据或重试理由。Godot 不暴露
CloseHandle 返回值，所以这里只记录 cleanup 尝试与 map 读回，不声称内核句柄
关闭已验证。

worker 累积 blocking header/body 的所有 partial bytes；先观察原 helper 精确
退出，再逐字节有界 drain stdout/stderr。当前固定 helper/adapters 不创建子进程
或额外 writer，生产 stderr 不超过4096；仅在这些条件下，末次读取0作为本范围
drain 结束点。Godot 不暴露底层 Win32 read error，故不声称一般 EOF/逐错误码
证明。截断、超限或尾随 stdout 均为 unknown，不查询 pipe length 或压制日志。

新的聚焦脚本 `simulator/tests/test_layout_commit_bridge.gd` 在全新 staging /
userdata/cache/TEMP 路径运行，覆盖真实 helper 保存重开、Unicode/nonBMP、
codec hash、空/恰好1MiB/超限、已有哨兵、缺少/错误 runtime 零启动、同步兼容、
异步帧/提示/状态保持、唯一 worker 与第二请求拒绝、发布前后124、响应丢失、
迟到成功单独记录、尾随 stdout 拒绝及完成 worker 的回收。split-frame 测试还
实际观察 header/body partial read 并确认字节不丢失。故障仅来自分开固定哈希的
test-only adapters；无生产故障开关。不重跑旧618/696/384或 solver/板测。

仍需真实鼠标/选择/取消、200步真实操作与屏幕读回、1080p/1440p及125%/150%
缩放、正式资产/体积碰撞/完整穿门、隐藏布局与因果传感、PC AI 和双 H12 链路的
各自证据。本次不建立新的模型数据白名单，也不证明其他 OS 进程读不到用户选定
文件。G03/R03/all29 保持 `not_run`。

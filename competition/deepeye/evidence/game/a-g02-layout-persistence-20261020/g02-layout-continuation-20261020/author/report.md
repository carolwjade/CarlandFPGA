# G02 私有布局持久化：作者续接报告

- Work: `A-G02-LAYOUT-CONTINUE-20261020-v1`
- Task: `DEEPEYE-IMPLEMENTATION-20261014/v1`
- 结果：六文件候选实现完成；headless 聚焦测试和回归通过；等待主会话独立审查
- 正式状态：G02、H01-H15、formal29、native UI、双 H12 均为 `not_run`；不是产品验收

## 范围与来源核对

- 已读项目 `fpga-multi-node` skill、A 角色、当前 Desktop transfer、不可变 scope 的 MD/JSON。
- 从 `immutable_scope.json.requirements` 按 sort_keys/compact UTF-8 重算 SHA256：
  `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`，15 项 H01-H15 保持。
- 已核验设计 report/plan 的两枚给定 SHA256。
- 已读取 predecessor 失败终态、turn aborted 记录、takeover 与 35KB partial test snapshot；
  未擦除或重放旧 RED/失败证据。
- 任务开始时观察 HEAD：`889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1`。
- 工作期间主会话推进了 HEAD 到 `678e01dd097f326e5bf724dc9db9e6b3e388384d`
  （`feat: expire actor authority on stale inference progress`）。该提交没有修改本六文件、
  project.godot、viewer 或未修改的 editor test；本 child 未 commit/push。
- 最终审计修正了 `docs/layout_persistence.md` 的 Git blob SHA1：
  `adc8a2abaebd0d1ff283b05ab9b0a9931e2ceb23`。此前记录的 `931399…` 不是实际对象；
  文件 bytes/SHA256 未变。

## 交付

| 文件 | Bytes | SHA256 |
|---|---:|---|
| `competition/deepeye/simulator/editor/layout_codec.gd` | 14686 | `c3846c39426c7ae5042e300d02c1bb7a6705f7482318f5eb70bc095ee8ca4a72` |
| `competition/deepeye/simulator/editor/layout_store.gd` | 5754 | `6386a5d49fb2856bbcd46d1f07192842aef399220e097f92e64409e9211efe56` |
| `competition/deepeye/simulator/editor/scene_document.gd` | 30327 | `b603c7468b2f798f68601af23bf1c78051d217f086f806aa604962032dee1f5e` |
| `competition/deepeye/simulator/ui/shell.gd` | 31110 | `97e96a52eea2fe1c6d0c436d1a2526553fd8a6c0c72e2f930148d7bb2a3640fc` |
| `competition/deepeye/simulator/tests/test_layout_persistence.gd` | 37201 | `dfe81da4c6134865483e19776edf1a0f2ff79b279e694eb25a0fb1e64a0cd6b7` |
| `competition/deepeye/docs/layout_persistence.md` | 6228 | `2f796aef1b0f276bea66ca54741dcc1b1c6284d156f6d7301fc9595307897a5c` |

没有新增 `.uid` sidecar；引擎在该 headless 路径下未生成它们。

## 实际行为

- 现有左侧工具栏增加“保存布局…”/“打开布局…”按钮，打开显式场景内 `FileDialog`
  （`ACCESS_FILESYSTEM`，默认 viewer 私有 user-data `layouts/`）。
- `FileDialog.file_selected`/`canceled` 信号连接到真实 Shell handler；测试通过实际信号回调。
- 保存链路：SceneDocument 导出 -> 严格 codec -> 同目录临时文件 -> 有界重读 -> rename。
  顺序场景拒绝已有目标，失败保留旧目标/当前文档。
- 打开链路：有界字节/UTF-8 检查 -> 严格版本化 JSON -> 全量验证 -> 原 SceneDocument
  单次几何替换 -> 原 `layout_changed`/`gates_changed` 重建 viewer。成功清空历史/选择，
  设置“文件布局、种子未知”；失败保持文档、历史、选择、viewer、Run/链路状态。
- 文件只含 geometry 字段；严格拒绝额外 truth/model/control/runtime/seed/route/resource
  字段。没有 `ResourceLoader`、`eval` 或动态 `load` 执行文件内容。
- 临时名候选 0..16 全部占用时返回 `temp_unavailable`，不会在重试耗尽后截断已有临时文件。

## 验证结果

- 首次 PowerShell runner 因本机 5.1 不支持 `.ArgumentList` 而未启动 Godot；该失败和 effect 保留在
  `author/compile-run-01/runner-failure.txt`，随后按实际支持方式重新启动。
- 初始 partial-source compile/run 是真实失败：exit 1、11 failures，保留于
  `author/compile-run-01/`；失败原因包括缺 Shell handlers、store 把正常 EOF 当 I/O 错误、
  UTF-8 处理问题。
- 最终 `test_layout_persistence.gd`：`618 checks / 0 failures`，exit 0。
  - 覆盖真实文件 save/open、Shell 信号、原 SceneDocument、viewer meshes/gate
    transforms/orientation、seed provenance、history reset、取消、迟到状态变化、
    读写/发布失败、旧目标保留、严格 codec 和 temp exhaustion。
  - stderr 保留拒绝 NaN/无效 UTF-8/超大指数时 Godot 的解析警告；测试断言拒绝且 exit 0。
- 未修改的 `test_editor_document.gd`：`696 checks / 0 failures`，exit 0。
- 独立 staged scene-load smoke：`SCENE_SMOKE_PASS document=1 shell=1 file_dialog=1`，exit 0。
- 未重跑 actor composition/original24、G06、native OS 或其他无关回归；主会话并发提交的 actor progress 工作不属于本 child。
- 精确引擎：`4.7.2.stable.official.ed1daf0bf`；
  SHA256 `c8f0a6bc45a19b33541501e57f6f7cd972ab18453743266339d495cbbe846643`。
  所有运行使用 fresh stage 的 APPDATA/LOCALAPPDATA/TEMP/TMP/cache；PRODUCT 未运行引擎。

## 证据索引

- `byte-manifest-before.json` / `byte-manifest-after.json`：初始 HEAD 与当前六文件字节。
- `dependencies-before-after.json`：直接只读依赖与引擎；无外部依赖新增。
- `commands.json`、各 run 的 `arguments.txt`/`environment-and-engine.txt`/`stdout.log`/
  `stderr.log`/`exit_code.txt`：完整命令、环境、退出码和原始输出。
- `manifest.json`、`receipt.json`、`evidence-index.json`：六文件身份、结论与证据哈希。

## 已知限制

- 顺序 Save As 已拒绝已有目标；但 Godot 4.7.2 没有可用的独占创建原语。临时写、最终
  目标预检查与 `DirAccess.rename_absolute` 不是跨进程原子事务，不能声称并发
  no-overwrite 或原子发布。外部并发创建目标时平台可能 rename 失败或替换；该限制已写入
  `docs/layout_persistence.md` 并交主会话评估。
- 默认是场景内 FileDialog，不是 OS native dialog；没有真实鼠标/文件选择/缩放/截图证据。
- 本功能不证明 OS 隔离、物理碰撞、完整穿门、200 步 UI、PC AI、控制链路或双 H12。

## Git 与依赖

- branch：`codex/a/deepeye-implementation-20261014`
- 无 commit、push、服务修改、板卡操作、依赖安装、群消息或新线程。
- `project.godot`、`viewer/main.gd`、`main.tscn`、`test_editor_document.gd`、
  `docs/resource_contract.json` 对初始 HEAD 字节一致；没有新增外部依赖。
- 仓库工作区还包含主会话所有/并发改动；本报告只声明六文件 author 候选与只读证据，
  不声明整个 PRODUCT 工作区 clean。完整 raw status 见 `git-status-all.txt`。

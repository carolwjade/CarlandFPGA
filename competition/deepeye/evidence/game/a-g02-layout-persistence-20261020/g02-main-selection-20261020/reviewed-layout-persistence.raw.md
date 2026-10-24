# 私有布局保存与重开（G02 增量）

状态：作者候选实现，主会话独立审查前不构成验收。正式 G02、H01-H15 和
29 张任务书卡片仍为 `not_run`。本功能只处理编辑器几何的本地持久化，不证明
未来模型/进程隔离、产品物理、控制链路或正式 UI 验收。

## 用户流程

- 左侧现有工具栏新增“保存布局…”和“打开布局…”按钮。编辑状态为
  `editing` 或 `stopped` 时可用；`running`、`paused`、`locked` 时按钮禁用，
  且迟到的 `file_selected` 仍会在改变文档前再次检查状态。
- 两个按钮打开同一个显式 `FileDialog`（`ACCESS_FILESYSTEM`，本项目使用非原生
  场景内对话框）。默认目录为 Godot 查看器私有用户数据下的 `layouts/`；用户
  可明确选择其他本地路径。
- 保存只创建新文件；顺序执行时拒绝已存在的文件或目录，失败不改变当前文档，
  也不改变已有目标的内容。
- 打开先完成有界读取和全部严格校验，再一次性替换原始 `SceneDocument` 的几何。
  成功后清空撤销/重做和选择，设置来源为“文件布局”、种子未知，并通过现有
  `layout_changed` / `gates_changed` 信号重建原 viewer 网格和圈。
- 取消、读取失败、格式失败、状态变化或写入失败均保持当前几何、选择、历史、
  Run/链路状态不变；失败事件只用于可见反馈，不恢复文件中的任何运行字段。

## 文件和哈希

文件是普通 UTF-8 JSON，不是 Godot Resource。固定顶层字段：

```json
{
  "schema": 1,
  "contract": "DEEPEYE-HUMAN-LOCK-20261014/revision1",
  "requirements_sha256": "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804",
  "units": "m",
  "layout": {
    "obstacles": [],
    "gates": {
      "entry": {"face": "front", "u": 0.0, "v": 0.0},
      "exit": {"face": "back", "u": 0.0, "v": 0.0}
    }
  },
  "layout_hash": "<64 lowercase hex characters>"
}
```

`layout_hash` 沿用现有 `SceneDocument.commitment_hash()` 的规范化：对象键排序，
数组保持顺序，数值固定六位小数，字符串使用 JSON 转义，对 UTF-8 canonical JSON
取 SHA256。它只校验内容一致性，不是签名、权限或权威认可。

每个 obstacle 只允许 `object_id`、`kind`、`position`、`rotation_deg`、`size`、
`priority`。`kind` 必须是现有五种材料之一，`priority` 必须等于该材料的固定
优先级。`object_id` 必须是唯一正整数；Godot 4.7.2 将 JSON 数字解析为浮点数，
因此 codec 要求数值精确为整数且在安全整数范围内，不做字符串强转或小数截断。

## 严格边界

- 最大文件 1 MiB，最大 30 个 obstacle，JSON 嵌套最多 32 层；先检查大小和深度，
  再交给 JSON 解析器。
- 顶层、`layout`、obstacle、vector 和 gate 均拒绝缺失或额外字段。因此
  `run_state`、`control_bridge_connected`、`link_state`、随机种子、路线、
  BOOT、模型、传感器真值、资源路径和控制字段都不能进入或恢复。
- 所有坐标、尺寸、旋转和门参数必须是有限数值；bool、字符串、NaN/Infinity 和
  超大指数不能冒充数值。
- 位置中心须在 `[-15, 15]^3` 内；尺寸按现有 kind 范围；门面只能是六个合法面，
  `|u|`、`|v|` 不超过 14.85 m，同面两圈中心距不得小于 0.30 m。
- 文件字节必须是有效 UTF-8。实现不使用 `ResourceLoader`、`load()`、`eval()`，
  不执行文件中任何内容；只调用 JSON 数据解析。

## 保存发布的已知限制

当前 store 在同一目标目录写入唯一临时文件，重读校验后再调用
`DirAccess.rename_absolute` 发布；发布前后都检查目标不存在。Godot 4.7.2 的
`FileAccess` 没有向调用方提供独占创建原语，这段检查、临时文件写入和 rename
不是并发安全的原子事务。外部进程若在最终检查和 rename 之间创建目标，平台行为
可能是 rename 失败或替换；当前实现不能声称“并发 no-overwrite”或“跨进程原子
发布”。顺序场景的拒绝已有目标和失败保留旧目标由 headless 测试证明。

临时名重试最多 16 次；所有候选均被占用时返回 `temp_unavailable` 并失败关闭，
不会在重试耗尽后重新打开或截断已有临时文件。该检查也不能消除上述检查/打开之间
的并发竞态，因此本功能不能替代 OS 目录权限和隔离验收。

保存文件可能包含编辑器私有几何。默认位置是查看器私有用户数据，但用户可在
文件对话框中选择其他本地路径；此功能不建立 AI/模型输入白名单，也不证明它们
无法在操作系统层读取该路径。

## Headless 验证

作者在精确 `Godot 4.7.2.stable.official.ed1daf0bf` 上，于全新 staging
项目/userdata/cache/TEMP 中运行：

```text
godot --headless --path <staged-simulator> --script res://tests/test_layout_persistence.gd
godot --headless --path <staged-simulator> --script res://tests/test_editor_document.gd
godot --headless --path <staged-simulator> --script res://tests/smoke_layout_scene.gd
```

该 smoke 脚本只存在于作者 staging 证据目录，不属于 PRODUCT 六文件范围。

当前候选结果为 `test_layout_persistence` 618 checks / 0 failures、
`test_editor_document` 696 checks / 0 failures，显式 scene-load smoke 为
`SCENE_SMOKE_PASS`。拒绝 NaN、无效 UTF-8 和超大指数时引擎 stderr 会打印解析
警告，测试仍按预期拒绝且退出码为 0；这不是通过证据，也不是正式 UI 证据。

## 仍未完成的正式义务

- 真实鼠标点击保存/打开/取消、真实文件选择和中文失败反馈记录。
- 200 步真实 UI 操作、保存后修改再打开、屏幕哈希读回及人工核对。
- 1080p/1440p 和 125%/150% 缩放下的新按钮、对话框裁切检查。
- G02 所依赖的正式资产、物理碰撞、完整穿门、控制模式、隔离及性能证据。
- 双 H12 链路、正式 29 卡和 H01-H15 均保持未验收。

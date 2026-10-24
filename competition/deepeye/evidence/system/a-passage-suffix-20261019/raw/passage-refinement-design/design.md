# G06 下一小步：完整步长的严格出门尾段证明（待主线选择）

建议先实现**已证明全体退出红门后，逐片验证剩余尾段始终严格位于红面外**。保留完整原始 dt，沿用现有连续六面证书及全部 solid 检查；只扩大已有证据足够强的一类多切片成功，不先实现通用事件时刻求根或新的几何框架。

这是 `A-passage-refinement-design-20261019-v1` 的设计建议，不是实施或验收。原 A Desktop generation2 为唯一主线；H01–H15、`DEEPEYE-HUMAN-LOCK-20261014/revision1`、requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` 不变。主线选择后另派产品文件独占所有者。

## 1. 当前 UNKNOWN 的准确来源

已核验 repaired motion manifest `1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533`。`source_hashes.json` 保存本设计实际读取的源哈希。现有 reducer 在 `passage_phase.py:176–178` 发现 ARRIVED 且仍有 slice 时，立即返回原 state/UNKNOWN，后续工作区片还未检查。executor 因此在 solid 全步检查之前拒绝整个 prepare，未执行任何前缀。

六个纯数值诊断使用当前原样代码；无状态提交。中间 phase 是明确标注的数值种子，不证明此前实际蓝入红出。结果见 `observations.json` 和原始 stdout：

| 数值种子 | 当前结果 | 实际后片证据 |
| --- | --- | --- |
| EXIT_CROSSING，中心 z=-15.519，yaw=7000 | 2片；片0 ARRIVED 后立即 UNKNOWN | 片0出口 APERTURE；片1 SAFE，红面 STRICT_OUTSIDE_ACTIVE |
| EXIT_CROSSING，z=-15.5199，yaw=7000 | 同一早退 | 后片也有严格全体在红面外证书 |
| EXIT_CROSSING，z=-15.5184，yaw=7000 | 同一早退 | 后片虽 SAFE，但红面只有 APERTURE，严格外侧尾段尚未证得 |
| EXIT_CROSSING，z=-15.519，yaw=0 | 单片 SAFE | 原有单片到达已可用 |
| ENTRY_CROSSING，z=14.481，yaw=7000 | 2片 SAFE | 已有多片完整进入能力 |
| ENTRY_CROSSING，z=14.4815，yaw=7000 | 首片 ENTERED，第二片 UNKNOWN | 切到 exit 后蓝面为 ENVELOPE_NOT_CLEAR；按 entry 检查才有 APERTURE |

这些例子用 `h=.4/r=.12/Rb=.52`、v0=.25、FAST speed_code20、dt=10ms；yaw=7000 的真实 canonical 切片边界为 0 / 7,142,857 / 10,000,000ns。最后一个例子是另一项角色切换/包络保守性问题，不能靠删除 ARRIVED 早退修复。第一、二个例子证明本建议有真实而有限的用途。

## 2. 三个可选增量

| 方案 | 收益与代价 |
| --- | --- |
| **A：严格红面外尾段，建议本轮** | 只组合已存在的全区间证书。无新采样/积分/误差公式；可使上述两类早退变成全步可证明。弱尾段和蓝门切换继续 UNKNOWN。 |
| B：有界事件窗口细分 | 可定位跨门窗口、缩小部分证书的保守性；需先增加“同一原始 CanonicalPath 的任意子区间”认证。当前 plan 只从原始0开始，不能用重启子路径代替，否则加减速、速度舍入和累计误差可能改变。工作面更大。 |
| C：带不确定性的全刚体有向 support 单调性 | 可能支持仍需 APERTURE 的出门尾段及进入后的蓝面清场；须对整刚体、曲率/角误差/资产余量给出可复核新引理，不能仅把当前 monotone_at_gate 标志当已证明的全局跨角色不变量。建议后续独立数学任务。 |

不建议缩短提交步长到第一个成功前缀、跳过后片、把接触当通过或降低0.5mm旋转余量。它们均不满足当前全步验证和保守边界。

## 3. 方案 A 的有限证明义务

令原 canonical 全步划分为连续闭区间 I0…In-1，已有同一原命令/初态/误差来源，覆盖完整 dt。现有正常 reducer 在某片 Ij 上完成有序 ENTRY/ENTERED/EXIT 历史，并通过正确红门的完整体积证书，片末的 red Side.outside 为真。

对每个 k>j，继续调用**原有** `workspace_boundaries.check_slice(prepared,k,'exit')`，要求：

1. `status == SAFE`，且六面证书齐全；
2. 红面对应 FaceProof.method 为 `STRICT_OUTSIDE_ACTIVE`；
3. 其余五面保持原有严格 inside 全区间证据。

第二项的 lower 是端点固定轴包络下界减去完整 rho，严格大于现有 guard；根据既有包络定理，它覆盖整片的全部刚体体积。因此剩余每片都不再与红面相交，也不能经其它面离开。各片覆盖完整区间、端点共享；有限并集仍安全，无需推断未知的精确过门时刻或速度单调性。相切/guard边界不能通过严格条件。

这里没有削减任何 rho 项：至少 max(.0005,Rb*Theta)、K*L²/8、position、Rb*angle、additional margin；CP 原始加减速律、数值误差与 speed carry 不变。每片 solid scene 的 initial/full 检查仍由既有 executor 在完整 prepare 中执行。工作区成功不能抵消末片禁入/DRILLING_REQUIRED/UNKNOWN。

这是“完整 dt 的尾段也已证安全”语义：ARRIVED 仅在完整 prepare/final fence/CAS 后对外成为已提交状态；历史仍记录首次证明全体退出的片窗口。原计划不被截成事件前缀，也不另发余段授权。下一次 step 的 ARRIVED_FROZEN 行为保留。若主线另要求在未知精确穿门时刻立刻冻结，该要求需要独立调度/事件区间契约，不能悄悄用 safe-prefix 改当前 executor。

## 4. reducer 的最小状态与证据变化

- 正常进入、INSIDE、EXIT_CROSSING 分支和首次 ARRIVED 的判断不变。
- 首次 ARRIVED 后进入**本次 preview 局部尾段检查状态**。后片只追加其完整证书，不重复追加 ARRIVED/EXIT_WINDOW 事件，不把 phase 改回 INSIDE，也不开蓝红孔的并集。
- 任何后片非 SAFE，保留原来的 UNKNOWN/VIOLATION_PROVED 区分；后片 SAFE 但只有 APERTURE 时返回 UNKNOWN。候选保持本次调用前的原 state，局部新历史不对外提交。
- 只有所有剩余片满足上述严格条件，才从原 plan.end 形成全步候选：revision仍只+1，末端 pose/speed/error/时间不改为 Ij 末端。所有 suffix 证书进入 trace；可给新接受的尾段路径加一个私有 policy tag（如 strict-red-outside-suffix-v1），不改共享 wire/host schema 或 workspace 几何 VERSION。
- 仍先检查原 max_slices；完整工作预算不足就 UNKNOWN。没有新的重试或无限细分。
- 相对 anchor proof、已提交旧事件、实际最终 fence 映射和 TM-R1 materialization fail-stop 原样保留。整个后片工作发生在 prepare，final fence 后不增加几何、哈希或 I/O。

## 5. 建议独占文件归属

下一实施工作只需下列四个产品路径（均相对 `competition/deepeye/`）及自己的新证据目录：

1. `simulation/authority/motion/passage_phase.py`：只改变 preview 的本次终态尾段处理/私有 trace tag。
2. `tests/simulation/test_passage_phase.py`：全步/历史/角色及证据不足回归。
3. `tests/simulation/test_motion_executor.py`：真实 prepare/commit 接入回归；将旧 T12 的 z=-15.519 期待拆成新可证正例和 z=-15.5184 的保留 UNKNOWN 负例，原日志不改。
4. `docs/workspace_passage.md`：准确区分新支持的严格尾段、仍未知的 APERTURE 尾段及蓝门角色切换。

`motion_executor.py`、workspace/CP/gate/solid 数学、runtime/watchdog/wire、C broker、isolation、renderer和正式卡只读。若实施发现必须改这些文件，应先回主线确认新证明/归属，不扩写同一任务。

## 6. 有意义的实施验收测试

| 测试 | 应证明的行为 |
| --- | --- |
| 现有 z=-15.519 与 -15.5199 多片种子 | RED 当前早退；新实现收齐每片六面证明后 SAFE，末端等于原CP plan.end，仅一个ARRIVED，preview仍无grant/CAS。 |
| z=-15.5184 弱尾段 | 后片即使 APERTURE/SAFE，也继续 UNKNOWN；原状态/历史不变，executor无fence调用/位移。 |
| 原单片红门、已有多片蓝入 z14.481 | 行为和误差继承保持；不是必须所有多片进入都走新分支。 |
| 蓝入 z14.4815 角色切换 | 继续 UNKNOWN，明确记录这不是新尾段规则的覆盖范围。 |
| 全身对照 | 只钻尖入蓝/只中心出红/尾部未出均不得ENTERED/ARRIVED；phase种子标注数值fixture，不当真实历史。 |
| 六个面法向与同面双圈角色 | 用真实 canonical 轴向变换构造对称完整尾段；同面只能从正确红孔开始到达，蓝孔不能充当红孔。完整同面U路线与36对系统验证另列，不冒充已做。 |
| 错方向/错面/擦边/旋转尾擦 | 现有证书不得被终态分支跳过；精确fixture接触沿用VIOLATION_PROVED，外包络不足保留UNKNOWN。端点内而中途外的现有曲线反例保持不SAFE。 |
| 末片实体障碍 | 在有严格红面尾段的实际CP上布置仅后片进入的薄禁入实体，真实solid全片检查仍拒绝整个step；不得只提交到达前缀。普通硬岩仍DRILLING_REQUIRED。 |
| 预算/身份/历史 | max_slices不足零advance；无缺片/重片/重复ARRIVED；旧事件逐字段不变、相对proof不重标时间，完整原dt时间映射无TTL扩展。 |
| 真实executor数值接入 | 完整尾段正例只一次final callback/一次CAS；随后ARRIVED冻结；STOP/世界失效/原deadline/句柄复用/TM-R1仍否决。post-fence无重工作。 |

先锁定当前实际失败的正例与需要继续拒绝的近边界例，再改 reducer。跑有变更的 passage/executor 套件及原 workspace/solid/runtime 回归，独立复核完整新 trace 和末片障碍反例。此清单是未来测试要求，本轮只执行了六个诊断，不声称这些新增验收已通过。

## 7. 剩余依赖和正式边界

本建议直接改善一个可复现的 G06 局部依赖，无法解决蓝门角色切换附近的包络余量、通用 APERTURE 尾段、未验证模型包含、完整同面U路线、材料状态律或真实renderer连接。后续选择B/C前应先把这些 UNKNOWN 的证据缺口分别命名，避免从一个布尔早退变成隐式孔并集。

G06要求三拓扑合法权限、完整钻具、非指定面/擦边/尾部/薄层等至少1000用例及同trace的命令/观测/物理步/渲染证据；G07仍分别保留 HIL 与 PC_DIRECT 各30布局×3次的完整因果对照。方案A不修改这些门槛，也不认证源/BOOT/时钟/AI生命。所有29正式卡、真实两控制链路、游戏/UI/AI/板卡与最终验收仍 **not_run**。

设计自检：没有产品实现、缺省通过、未知碰撞标签或半步提交；每个新增可接受条件都有现有全区间证书支撑；较弱尾段与蓝门切换保守失败明确保留。主线审阅选择后另签实施任务，本设计不提交Git或派工。

# Authority 快速门孔净空证书

工作 `A-g06-fast-clearance-20261015-v1`；H01–H15 与
`DEEPEYE-HUMAN-LOCK-20261014/revision1` 不变，requirements pin：
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`。

`simulation/authority/motion/gate_clearance.py` 提供两个纯几何函数。
这是 authority 内部契约，尚未冻结为公共 ABI，不向控制算法提供世界真值或碰撞 oracle。
它使用 `gate_geometry` 的 private Decimal interval helpers；修改后者的精度、向外舍入、
轴规范化或 Gate 映射时必须连同本模块重新核验。此次基础源 SHA256：
`5e33a60927334cee4473d5f78afc248f04d3a5ef00db465b2bcdf14c1adc3839`。

## 输入与返回值

```python
errors = ErrorBounds(position_error_m, angle_error_rad, additional_margin_m)
instant = section_clearance(capsule, gate, direction=-1, errors=errors)
bounds = SliceBounds(end_position_m, arc_length_upper_m,
                     curvature_upper_per_m, rotation_upper_rad)
continuous = sweep_clearance(capsule, gate, direction=+1,
                             errors=errors, bounds=bounds)
```

三个误差参数全部必填，包括明确的零。位置误差是相对于门的位移范数上界；角误差是完整姿态
相对于名义姿态的转角上界；additional margin 是另外有依据的资产、坐标变换、引擎和其他长度
误差预算。调用者必须为这些上界提供来源并绑定实际版本。本模块验证数值域，不认证来源；
传入零不证明误差不存在。门仍是 SceneDocument 的固定六面/0.15 m 半径，不能借误差扩大门。

`ErrorBounds` 的位置和 additional 值限于 [0,10] m、角误差 [0,1] rad。
`SliceBounds` 的 L/κ 限于 [0,1000]（m、m⁻¹），Θ 限于 [0,1] rad；实际连续证书另要求
Θ≤π/3600（0.05°）。所有标量仅收有限 int/float，拒绝 bool、NaN、Infinity、字符串和负值。
端点坐标沿用 ±1000 m 域，并复制成 tuple。全路径弧长 L 用精确有理平方比较核对不小于端点
弦长，矛盾则抛 ValueError。这个检查无法认证 L 是真实路径长度上界，也无法认证 κ 或 Θ。
Θ 超过子步限制返回 UNKNOWN；边界无法证明也拒绝。所有输入/结果 dataclass 均冻结，方向只收
整数 −1（朝门内，蓝门）或 +1（朝门外，红门），不能用 abs 省略方向检查。

返回对象绑定完整 `CertificateInputs`（胶囊、门、方向、误差、可选 slice），列出假设与原因。
`motion_grant` 固定 False，结果没有 entered/arrived/碰撞世界状态。

|函数/状态|精确含义|
|---|---|
|瞬时 EMPTY|包含误差的完整胶囊与门平面严格分离；不是已进入、已退出或到达|
|瞬时 CLEAR_SECTION|完整有限胶囊截面已证明非空，方向角合格，且截面严格在孔内|
|瞬时 UNKNOWN|相切、角度不符、有限截面存在性不确定或充分上界不够紧；不放行|
|连续 SAFE_IF_INTERSECTING|在所有输入假设成立时，整个 slice 每次与门相交都只穿过孔内；不证明发生了穿越|
|连续 UNKNOWN|任何全 slice 角度/膨胀/径向充分证明不足；不放行|

`plane_separated` 是完整误差包络的严格分离信息；连续结果的 `nonempty_proved` 始终 False，
因为本函数不证明何时相交。无效输入抛异常；调用方必须使 UNKNOWN 和异常都无法产生运动许可。

## 瞬时包含证明

设 capsule 是 `segment(p−h a,p+h a) ⊕ Ball(r)`，a 是输入轴的精确数学单位化。
当前常用 h=.4/r=.12 候选总长 1.04 m，Rb=h+r=.52 m。它包含 0.80×0.24 m 的平端圆柱，
本模块不证明 B 最终网格、中心/pivot 或附件包含关系。灰盒已在单独 source `a7c2daf8` 修复，
其978个实际导出顶点经精确有理数复算位于此候选包络内，证据见 `greybox_drill_envelope.md`。
该特定灰盒结果不覆盖最终 B 资产或 Godot 后端的碰撞查询误差。

有限胶囊包含于同轴无限圆柱。以门中心 g、法向 n、P=I−nnᵀ，定义

```
s0 = n·(p−g), un = a·n
m = P(p−g) − (s0/un) P a
beta = position_error + (h+r)*angle_error + additional_margin
U = ||m|| + (r+beta)/|un|
```

无限圆柱与门平面的椭圆最大半轴是 `(r+beta)/|un|`；三角不等式给整个有限胶囊截面的径向上界 U。
`2 Rb sin(e_angle/2) ≤ Rb e_angle` 证明 beta 覆盖姿态偏移。un 区间含零时禁止除法，
不能替换成 epsilon；平行/近乎平行轴也会被独立方向角门拒绝。

名义 signed support 是 `s0 ± (h|un|+r)`。EMPTY 使用最小支持减 beta / 最大支持加 beta；
非空证明则要求最小支持的上界加 beta 严格为负，最大支持的下界减 beta 严格为正。
这里非空指本次输入的胶囊/其位姿误差族，不会从保守包络非空推断真实资产已经穿门。

方向角门严格证明 `direction*un > cos(5°−angle_error)`；因此真实倾角小于5°。
本算法对恰好5°或舍入不确定者可保守 UNKNOWN。截面拟合与方向是独立条件；即使球体可穿孔，
也不能借球对旋转不敏感免除钻头的方向要求。CLEAR_SECTION 另要求向外上界 U+guard<0.15 m。
无截面或相切不满足严格非空条件；相切孔边也不能通过。

上界不需要逼近真实最大半径到 10µm。偏心/有限端帽可能 UNKNOWN，而精细有限截面求解器能证明
通过；这是有证明的保守拒绝。例如 p=(.07,0,15.5)、轴+Z、h=.4/r=.12，有限端帽半径
`.07+sqrt(.12²−.1²)<.15`，快速无限圆柱上界 .19，所以本函数返回 UNKNOWN。
反过来，完整实体的正投影也不能替代门平面截面：约5°时 h*sin(angle)+r>.15，但实际中央截面
的 r/cos(angle)≈.12046，仍在孔内。

## 连续 slice 的包含证明

假设中心曲线按弧长 s∈[0,L_actual] 参数化，连续单位切向，曲率范数≤κ，L≥L_actual。
允许分段曲率变化；瞬移、切向跳变或未受这些上界覆盖的运动不能用本证书。
L 不得用弦长代替。线性弦插值 l(s) 的标准二阶导积分界给：

```
||p(s)−l(s)|| ≤ κ s(L_actual−s)/2 ≤ κ L²/8.
```

Θ 是整个 slice 相对起始姿态的旋转上界，可由角速度范数积分（总角变化）上界给出；
终点净四元数差可相消，不能充当 Θ。任何局部点 |x|≤Rb 的旋转偏移
`≤2 Rb sin(Θ/2)≤Rb Θ`。本实现用线性式避开 sin 的额外数值证明，计算：

```
rho = max(.0005, upper(Rb*Theta)) + upper(kappa*L²/8) + upper(beta)
U_slice = max(||m_start||, ||m_end||) + (r+rho)/|a_start·n|
```

因此真实整段运动体被“起始轴胶囊沿中心弦平移，再作半径 rho 的球膨胀”包含。
固定起始轴时，门平面轴交点 m 沿弦仿射；范数凸性使两个端点范数的较大者覆盖完整弦。
这两个端点计算的是已经证明包含整个连续运动的固定轴膨胀包络，绝非实际端点 overlap 检查。

全 slice 另独立证明 `起始有向倾角 + Θ + angle_error <5°`。
相同端点可以在中间绕回：4.99°→5.01°→4.99° 的两端合格、总角变化 .04° 也低于 .05°，
本函数仍因全段角度界拒绝。另一反例是 p=(.02995,0,15.3)，起始/结束轴+Z，中点倾斜
−.0004 rad，完整角变化 .0008 rad；两端截面可过，中点真实有限圆柱截面碰圈。
测试拒绝它。此反例验证通用几何上界，不宣称静止中心自转是已批准的积分器动作。

.5mm 是任务书旋转膨胀最低值，不吸收未知引擎误差。若 Rb 更大，Rb*Θ 可超过这个最低值；
不得只固定加 .5mm。当前 API 允许输入上界假设；将其绑定 `MotionStep` 的实际 slice、
积分器限制、全时间区间、命令截止点仍是下一阶段工作。调用者不能据数值已通过域校验声称
运动路径已认证。UNKNOWN 应中止该次执行尝试并交由 authority 记录原因，不可记作到达。

## 数值与缓存边界

沿用 gate_geometry 的 Decimal60 每操作 FLOOR/CEILING 区间、sqrt 相邻值包络及精确 copy_negate。
输入浮点值按其真实 binary64 值解释。π 由 Machin 恒等式与50项交错 arctan 的精确有理余项界
建立区间；小于.09 rad 的 cos 用9项、末项为正的交错多项式上界，每项仍向外计算。
Θ+角误差也使用向上加法，不先经普通 float 加法。最大子步角与 π/3600 的下界比较，近界不确定
可拒绝；数值判断没有从环境 Decimal context 取舍入或精度。

径向/支持判定另用 1e−12 m guard，导出浮点前加 1e−20 m padding 并 nextafter 向外。
这些保护只覆盖此数学计算路径；它们不是实际资产或 Godot 的≤0.1mm误差证明。
显式误差预算、引擎实测、包络相对实体的保守性和最终任务书容差必须另外核定。
几何上界可能较松，不能把保守外扩量叫作模型测量精度。

唯一缓存是最多128项 cos 阈值（键为精确向上角度预算 Decimal）。姿态、门、方向和证书没有缓存。
因此姿态变化/反向轴/扩大误差都重新计算。后续若引入证书缓存，必须绑定 run、scene版本、门、
完整slice、资产/pivot/scale、误差和积分器版本；授权/TTL仍独立校验，旧几何证书不能续租动作。

## 验证证据与性能范围

功能测试真实 RED 为28项缺失模块断言失败；实现后28项通过。第一次从错误工作目录执行导致
`competition` import error 的日志也保留，没有把环境错误当有效 RED。测试涵盖六面和正反方向、
球退化、有限端帽、近平行、严格接触、近零支持、误差扩张、角边界、整个slice反例、显式参数、
不受外部修改的 tuple、冻结结果、常量缓存及低精度 ambient Decimal context。

独立 private audit 使用 Decimal120，不调用产品 interval helpers 生成 oracle：

- 256 个有限胶囊截面闭式最大值，证明极值位于有限中央线段内；导出上界全部覆盖。
- 256 个球/有限端帽截面的独立闭式值。
- 256 个全时域圆弧解析 oracle：`M'=κ sec²(a)(−z+r sin(a))<0`，且整段 m>0、极值仍处在有限
  中央柱段，因此全时间最大值在起点。端点 float 误差独立测得≤8.876e−16 m，并包含在显式1e−12 m假设。
- 256 个独立高精度 cos 阈值检查。
- 9 个变异全部被断言检出：方向、误差、旋转最低量、RbΘ、弧弦偏差、终点、全slice角度、
  子步角上限、接触guard。变异只在内存复制模块执行，不改产品源。

一次本机 CPython 3.12.14 串行测量如下；原始每次耗时均保留，单位ms：

|路径|样本|Median|P95|Max|
|---|---:|---:|---:|---:|
|瞬时，已有冻结输入|2048|.1286|.1369|.3406|
|连续，已有冻结输入|2048|.2339|.2582|.6238|
|瞬时，包含构造输入|2048|.1553|.1691|.3327|
|连续，包含构造输入|2048|.2628|.2871|.8228|
|瞬时，冷cos阈值|256|.20945|.2347|.4377|
|连续，冷cos阈值|256|.3170|.3413|.6240|

瞬时样本包含1114 CLEAR_SECTION、648 UNKNOWN、286 EMPTY；连续1246 SAFE_IF_INTERSECTING、802 UNKNOWN。
这是本机有限分布，不是最坏耗时证明、并发运行承诺、完整100Hz执行器或G06通过证据。
既有精算的15–21ms限制继续保留；本函数不会暗中调用无期限精算来掩盖 UNKNOWN。

复现（工作目录产品根）：

```powershell
& ../venv/Scripts/python.exe -B -X utf8 -m unittest discover -s competition/deepeye/tests/simulation -p test_gate_clearance.py -v
```

独立 audit 与原始 RED/GREEN/变异/timing 在 A root 私有目录
`.planning/deepeye-implementation-a/g06-fast-clearance-20261015/`，运行入口 `audit_gate_clearance.py`；
不是可随产品分发的公共路径承诺。交接 receipt 记录精确命令、退出码及三文件哈希。

另一个独立会话复核了原52项组合测试、576个瞬时案例及144条曲线/4752个时刻，
未发现输入假设成立下的错误放行。采样是反例搜索证据，不是全域证明。它发现并建议补入的
“端点clear、中间曲线擦圈”案例现已加入公共回归：真实κ上界返回UNKNOWN，谎报κ=0则可返回
SAFE_IF_INTERSECTING。该案例明确要求下一层绑定真实积分路径，不能把数值域检查当来源认证。

实际 Godot 层仍要验证目标二进制/后端、初始重叠、薄层扫掠、旋转尾擦、缩放/轴映射、mask和查询
同步、contact guard有效性。官方 `cast_motion` 忽略初始已有重叠；
[PhysicsDirectSpaceState3D](https://docs.godotengine.org/en/stable/classes/class_physicsdirectspacestate3d.html)
因此不能单靠 cast。显式膨胀 CapsuleShape3D 时需同时设置 `radius=r+rho`、`height=2h+2(r+rho)`，
保持中央线段长度不变；官方 height 包含半球，见
[CapsuleShape3D](https://docs.godotengine.org/en/stable/classes/class_capsuleshape3d.html)。
这些文档约定不替代目标4.7.2实测。本轮没有服务、板卡、真实Godot cast、完整阶段机或资产验收。

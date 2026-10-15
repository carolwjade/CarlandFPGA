# A 权威域三维刚体运动积分

任务 `A-g06-kinematics-20261015-v1`，属于
`DEEPEYE-IMPLEMENTATION-20261014/v1` 的 G06 实施组成部分。当前主负责人仍是
Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`，generation 2。
本模块保留 `DEEPEYE-HUMAN-LOCK-20261014/revision1` 的全部 H01–H15，要求数组
SHA256 为 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`。
依据固定任务书 §7 的量化曲率和 §8.3 的三维运动要求实现；软件单测通过不关闭 G06。

## API 与坐标

```python
from competition.deepeye.simulation.authority.motion.kinematics import RigidState, advance

state = RigidState(
    position_m=(0.0, 0.0, 0.0),
    orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
    speed_m_s=0.0,
)
step = advance(state, "fast_9600", 10, 2000, 0, 10_000_000)
middle = step.sample_at_time_ns(5_000_000)
by_distance = step.sample_at_distance_m(step.distance_m / 2)
# 外层授权、连续完整体积扫掠全部成功后，才可以应用 step.end_state。
```

`position_m` 是刚体原点在世界中的位置，`orientation_xyzw` 是 body-to-world
单位四元数；不是 Euler 角。body `+Z` 向前、`+Y` 向上、`+X` 向右；正 yaw
绕 `+Y`，正 pitch 绕 `-X`。没有侧移或独立 roll 指令。先 yaw 再 pitch 等复合
操作仍产生正确的完整四元数，不把其中的 roll 分量删掉。刚体原点/pivot、真实
形状与包围半径由接入层绑定，积分器本身不假定钻头退化成点。

`RigidState`、返回的 `MotionStep` 和 `MotionSample` 都不可变。状态构造器允许
数值 tuple 或 list，但复制为固定长度 tuple，不保留可变容器。位置要求 3 项、
四元数要求 4 项；不接受 bool、非数、NaN、Inf、负速度或超过 0.25 m/s 的速度。
四元数范数离 1 超过 `1e-12` 即拒绝；此容差内只归一化浮点舍入误差，不接受
任意缩放的四元数。零距离、零速度变化的采样保持原不可变状态，避免无运动时
重复归一化改变姿态。Python 值对象并不构成防篡改或进程安全边界。

`advance(state, profile, speed_code, yaw_q, pitch_q, dt_ns)` 返回：

|字段/方法|语义|
|---|---|
|`start_state` / `end_state`|完整刚体起点/终点姿态与实际速度|
|`dt_ns`|严格整数物理步长，闭区间 1..10,000,000 ns|
|`distance_m`|实际积分路程，非起终点直线距离|
|`sample_at_time_ns(t)`|严格整数 `0 <= t <= dt_ns`，包含两端|
|`sample_at_distance_m(s)`|有限数值 `0 <= s <= distance_m`；严格拒绝域外值，不偷偷裁剪|
|采样返回值|`MotionSample(elapsed_ns, distance_m, state)`；距离反解可有小数 ns|

停止后的恒定距离平台取**最早到达该距离的时刻**。例如 0.001 m/s 以
0.25 m/s² 减速，在 4 ms 到达 0.000002 m 后停止；10 ms 步的最终距离反解为
4 ms，而时间采样 10 ms 仍返回 10 ms 和相同终点。完全静止步的距离 0 反解为
时间 0。时间反解仅将已在合法距离域内的浮点舍入限制到步域，不放宽输入边界。

## 量化与速度约束

直接复用 `integration/motion.py::validate`，包括 profile、整数码范围、禁止
bool，以及保守整数 ROM 的量化后合成曲率判定。FAST 每码 0.0125 m/s、最高
0.25 m/s；STRESS 每码 0.0001 m/s、最高 0.002 m/s。非法命令被拒绝，不能静默
clip 到合法码。当前实际速度若超过所选 profile 的上限，也拒绝推进；不能借
切换 profile 绕过速度上限。本模块没有 profile 会话历史，停止、新 session、
BOOT 和模式切换授权仍由外层验证。

非零目标速度时，量化校验后的曲率为：

```
kappa_yaw   = yaw_q   * pi / (180000 * v_target)
kappa_pitch = pitch_q * pi / (180000 * v_target)
||kappa|| <= 0.5 / m
body angular velocity = v_actual * (-kappa_pitch, kappa_yaw, 0)
```

目标速度为 0 仅允许两角速度码均为 0。此命令按直线减速，不保留上一条曲率，
也不在原地旋转。**失去授权后的硬 STOP 应由外层禁止推进**，不能调用减速
积分后把继续移动的制动距离当作已授权动作。

设步长为 `T`，目标速度与初速之差为 `delta`，加速度大小固定为 0.25 m/s²：

```
t_r = min(T, abs(delta) / 0.25)
a = sign(delta) * 0.25
v_r = v0 + a * t_r            # 达到目标的分支精确取 v_target
s(T) = (v0 + v_r) * t_r / 2 + v_r * (T - t_r)
```

先达到目标时将加减速段和匀速段分开，不能用末速乘整个步长。逆距离采样使用
有理化二次方程正根 `t = 2s / (v0 + sqrt(v0² + 2as))`，避免低距离时大数相减。

## 三维路径积分与后续扫掠

曲率在单条命令/单步内固定。令 `k=(-kappa_pitch,kappa_yaw,0)`、`K=||k||`、
`theta=K*s`、`sinc(x)=sin(x)/x`（只有 x 恰为 0 时取 1），沿程积分为：

```
q(s) = q0 * exp_quaternion(k*s)    # 右乘，轴在 body 坐标系
dx_body = kappa_yaw   * s²/2 * sinc(theta/2)²
dy_body = kappa_pitch * s²/2 * sinc(theta/2)²
dz_body = s * sinc(theta)
position(s) = position0 + rotate(q0, (dx_body,dy_body,dz_body))
```

横向系数利用半角恒等式，避免 `1-cos(theta)` 的消减误差；没有把“小于某个
角度”的合法转向清零。加减速的角速度由实际速度决定，路径依真实积分路程
推进。时间与距离采样都重新求解析曲线上相应完整刚体姿态，不在首末点间取
直线插值。

10 ms 是本 API 的最大步长，并不保证每一步已满足连续扫掠的 0.05° 旋转上限。
例如 FAST 上限和最大曲率可在 10 ms 旋转约 0.0716°。接入层可用
`0.5 * step.distance_m` 作为旋转弧度的保守上界，继续按距离或时间细分，且必须
保留真实 body/pivot 的旋转膨胀、平移弧线偏离界、数值容差、初始重叠检查和
完整体积扫掠。两个端点 overlap 或原点曲线无碰撞都不证明实体扫掠无碰撞。

本模块无场景真值输入、观测生成、权限授予、碰撞、蓝红圈完整穿越、进程隔离、
板卡 IO 或渲染能力；返回姿态仅供 A 权威域使用。不能把它输出到控制算法形成
隐藏布局/碰撞 oracle 旁路，也不能把本单元测试等同 G06、R03、板测或系统验收。

## 验证

从产品工作树根运行：

```powershell
& <原仓库>/.local/venv/Scripts/python.exe -B -X utf8 -m unittest `
  competition.deepeye.tests.simulation.test_kinematics `
  competition.deepeye.integration.test_motion -v
```

28 项新增用例覆盖解析直线/圆弧、正负双轴、非 identity 初始姿态的右乘、复合旋转、
加减速达到目标的精确分段、STRESS/FAST 量化边界、域外采样、静止平台最早时刻、
任意单位姿态零运动保持、1 ns 极小转向、时步划分一致性和 6000 步半圆轨迹/单位
四元数稳定性。四元数本身始终必须是单位范数。

初始 25 项真实 RED 已保留；新增零运动姿态回归也保存 RED/GREEN。首轮速度断言
存在 1 ulp 的期望容差误差，原失败日志保留，并将该断言容差从 `1e-17` 调整为
`2e-17`。10 类私有内存变异至少触发一个断言失败；覆盖整步末速、四元数乘法方向、
pitch 符号、微角清零、profile 上限、dt/距离边界、角码静默裁剪、非单位四元数和
停止平台选错时刻。变异从不覆盖产品源码。

完整命令、返回码、原始日志、源码和依赖哈希保存于主仓库的
`.planning/deepeye-implementation-a/g06-kinematics-20261015/receipt.json` 及同目录文件。
该证据交回当前主会话独立复核，未自行提交、发布、操作服务或实板。

主会话独立复核另外发现：合法的最小正 subnormal 距离可能令加速反解中
`v0² + 2as` 下溢，导致除零或错误地把极小时刻限制到整个步长。已保留真实
RED（4 个断言失败、1 个异常），加速分支改用
`hypot(v0, sqrt(2a) * sqrt(s))` 后再求有理化根；新增 Decimal 80 位独立预言机。
修复后本模块及量化测试共 35 项通过，独立复核的 144 条轨迹、612 个时间采样和
60 个极小加速输入均通过。制动边界探针最大时间差约 0.0373 ns，按全局最高速度
换算的保守空间差小于 `9.4e-12 m`；极端 subnormal 制动仍有相对精度限制。
这些是软件数值误差观察，不替代实际碰撞引擎误差预算或 G06 整体验收。

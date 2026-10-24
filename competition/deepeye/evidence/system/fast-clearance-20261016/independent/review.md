# G06 快速净空函数独立只读审查

任务 `DEEPEYE-IMPLEMENTATION-20261014/v1`；work_id `A-g06-fast-clearance-review-20261016-v1`；reviewer `/root/g06_geometry_design/gate_clearance_review`。

本次有限范围审查未发现输入假设成立时可复现的 false-clear 或其他阻断代码缺陷。此结论是给质量主会话的审查证据，不是合并决定、形式化全域正确性证明、MotionStep 接入通过或 G06 正式验收。未修改产品、提交或推送；未操作服务、板卡、ACL 或外部消息。

H01–H15 固定合同 `DEEPEYE-HUMAN-LOCK-20261014/revision1`，本次从 requirements 数组重新计算 canonical SHA256 为 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`。已读取不可变范围、当前协议和 transfer.json；唯一 director 仍为 Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`，generation 2。执行前 native validate 返回 execution_allowed=true，work/job/agent 匹配。

## 准确版本与范围

产品目录为 A root 的 `.local/deepeye-implementation-a/`。审查开始 HEAD `3b4736ff655b7fee35e79a5387f4118d1fff417c`；三项待交付文件尚未跟踪，本报告绑定文件字节而不是把 HEAD 当作含有改动的提交。

|文件（相对于产品根）|SHA256|
|---|---|
|competition/deepeye/simulation/authority/motion/gate_clearance.py|035d26e45419208bdcc30d8640df89fd444836d8ce7f0d32e22fc3c0cd6f9977|
|competition/deepeye/tests/simulation/test_gate_clearance.py|c3189e706e625eed0816b847b32d45cee6470fc64d1fd8a9b25d1f6c8781f6be|
|competition/deepeye/docs/authority_gate_clearance.md|373b53967453d55d7534256b43ccaccf34666b164261ae75c823118ae6a57fb8|
|competition/deepeye/simulation/authority/motion/gate_geometry.py（依赖，只读）|5e33a60927334cee4473d5f78afc248f04d3a5ef00db465b2bcdf14c1adc3839|

作者 receipt SHA256 `b79de177e9baa4a669bdecf062fe009f3fa70f52ab8fb31e340aa95d674e89eb` 已读回。其 1024 formula / 9 mutation / timing 数字是作者证据；本次没有把它们算入独立检查数量。四个源哈希在独立脚本结束时再次一致。

## 数学和实现核查

1. **瞬时包含方向正确**：`gate_clearance.py:138–143,153–157,190–195`。有限 capsule 位于同轴无限 cylinder 内；姿态和相对位置误差由 beta 的球膨胀覆盖。轴平面交点为 `p-g-(s0/un)a`（代码写成投影后的等价形式），椭圆半长轴 `(r+beta)/abs(un)`，加交点离心量给充分上界。该方法可拒绝合法有限端帽，不能反过来把保守上界当作真实截面的精确最大值。
2. **空/非空/严格接触分开**：`:176–196`。EMPTY 从外扩 support 严格分离获得；非空用反向收缩后的 support 跨过平面，不能仅因外包络非空推断真实资产发生穿越。径向 `upper+guard<R` 拒绝等号。1 pm guard 和 float 导出 padding 没有被拿来扩大孔径。
3. **方向与角度预算正确**：`:32–64,146–150,185–189,222–238`。Machin 公式用有理交错级数界，cos 的偶次末项多项式是正小角域内的上界。sign 仅在几何分母处取绝对值；angle predicate 比较有向 dot 下界。预算太大或分母可能含零时不执行不安全除法。Theta+angle_error 用显式向上加法，连续角门扣除整个 slice 的偏转界。
4. **连续包络前提清楚**：`:199–247`，说明文档 `:88–118`。对按弧长参数化、切向绝对连续且曲率有界的中心曲线（常见 C1、分段 C2 路径足够），Green 积分核的范数界给 `kappa*s*(L_actual-s)/2 <= kappa*L_upper^2/8`。每个实体点的旋转位移 `<=Rb*Theta`；与 beta 及最低旋转膨胀相加，覆盖起始固定轴沿弦平移的完整体。此后的 m(lambda) 仿射，范数凸性使端点范数最大值覆盖整个弦。没有用真实端点 overlap 冒充中途检查。
5. **数值路径未发现 ambient Decimal 运算遗漏**：依赖 `gate_geometry.py:20–145` 的逐操作 FLOOR/CEILING、sqrt 两侧邻值、copy_negate/copy_abs；新增代码中的算术均经 interval 或显式 Context。PI 的 Fraction 构造、整数构造和比较不受当前 Decimal 精度影响。独立低精度/trap/cold-reload 检查见下。

## 本 reviewer 实际运行的证据

- 产品根执行 `../venv/Scripts/python.exe -B -X utf8 -m unittest discover -s competition/deepeye/tests/simulation -p test_gate*.py -v`，exit 0，52/52，通过日志 `unit-gate-all.txt`。
- A root 执行 `.local/venv/Scripts/python.exe -B -X utf8 .planning/deepeye-implementation-a/g06-fast-clearance-independent-review-20261016/review_probe.py`，exit 0，日志 `probe-raw-1.txt`，结构化结果 `probe_results.json`。
- 私有 oracle 使用独立 Decimal110 运算、独立 pi 数字和 60 项三角函数级数，不调用产品 interval helpers 或作者 audit 脚本。它是高精度数值交叉检查，不是第二套经形式验证的区间证明。
- 576 个瞬时案例覆盖六面、正反方向、中心/有限帽/球/短体、偏心、显式误差、1e-300 和最小 subnormal 轴分量。结果为 EMPTY 241、UNKNOWN 216、CLEAR_SECTION 119；未发现 support、angle 或向外导出矛盾。导出值减独立充分上界的最小观测差约 1.4291e-17 m。
- 144 条二次中心曲线 `p(t)=p0+t*d+t*(1-t)*b`，独立使用 `L<=|d|+|b|`、`kappa<=2|b|/(|d|-|b|)^2`（|d|>|b|）建立假设。姿态在中途旋转再返回，角偏转为 `Theta*4t(1-t)`。144 个证书为 SAFE_IF_INTERSECTING 106、UNKNOWN 38；采样 4,752 个时刻，每次对有限 capsule 的球族截面作 25 点采样，没有发现 clear 证书的碰圈见证。**时间和截面采样只用于发现反例，不证明任意轨迹的全时域正确性**；一般数学前提仍依赖上面的解析包含论证。
- 低精度上下文 precision=1、ROUND_UP、Emax=2、Emin=-2，且 Inexact/Rounded traps 开启时，重新构造输入、清空 cos 缓存、cold reload 新模块后的 section/sweep 结果均一致。
- 另独立检查孔半径及其 nextafter 两侧、0.5 pm/2 pm 内缩边界：接触和 guard 内均 UNKNOWN，明确离开 guard 的案例可 CLEAR_SECTION。

## 非阻断补测建议与接入边界

**T1：建议把曲率导致的中途碰圈反例加入公共回归。** 当前 `test_gate_clearance.py:132–177` 检查膨胀算式、旋转中途反例和终点，但没有明确的弯曲中心线中途碰圈案例。作者私有 audit 不随公共测试运行。本次私有脚本 `adversarial_checks` 可复现：front gate，r=.12、h=.4、axis=+Z，`p0=(.0294,0,15.3)`、`p1=(.0294,0,15.32)`；中心路径 `p(t)=p0+t*(p1-p0)+(.004*t*(1-t),0,0)`。两端瞬时为 CLEAR_SECTION；中途存在半径至少 .1503976562 m 的有限截面点。用 L=.025、kappa=40、Theta=0 时连续结果为 UNKNOWN。此建议是回归覆盖改进，不是已发现的算法错误。

**I1：输入域校验不能认证运动。** 同一曲线若调用方谎报 kappa=0，本函数返回 SAFE_IF_INTERSECTING；这是违反明确前提的调用，不属于输入假设成立时的 false-clear。`gate_clearance.py:212–215` 仅能核对弦长不超过 L，`:217–234` 使用调用方上界；文档 `:24–35,116–118` 如实披露。下一阶段必须把实际中心路径、旋转、轴/pivot、误差来源、时间区间与这些值绑定。不能把浮点域合法当成来源已认证。

**I2：Theta 的精确定义应在 adapter 保留。** 当前 API 定义为整个 slice 相对起始姿态的最大转角界；总角变化是足够但更强的一种提供方式。此定义对几何包含有效，但本函数不证明总角变化本身也小于 .05°，不检查中心速度与钻轴一致、单调穿越、授权时效或 gate phase。若实际积分器还有更强动作约束，需要由 adapter/authority 单独验证，不能从 SAFE_IF_INTERSECTING 推断。

**I3：证据措辞。** 文档 `:144–152,175–177` 的“独立 private audit”指独立公式 oracle，由实现作者运行；不应把该段单独读作不同 reviewer 已完成。本文及其独立 receipt 才记录这次不同代理的只读审查。文档对 asset、Godot、100Hz 和 G06 的限制总体明确，没有发现借数值测试提升产品验收的断言。

保持未验证：真实资产/pivot/缩放包含、误差上界来源、实际 MotionStep slice 的完整绑定、Godot cast/初始 overlap/薄层/尾擦实测、阶段机及正确完整跨门、授权/控制链路、游戏/硬件/G06 最终验收。源码审查和有限数值测试不消除这些边界。

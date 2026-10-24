# Retained actor 独立软件审查

任务 A-actor-owner-independent-review-20261019-v1，job child-ed80d3358dba43b4b83dafef40a52b9b；2026-10-19。作者 actual completed/terminal=true 已读回。审查只写本目录；候选五文件及旧证据未改，不运行实际 native。

**发现一项正常公开生命周期路径可触发的新代可用性缺陷，以及两项假 native 依赖形状漂移的防御缺口。** 116项作者回归全部通过；冻结的精确8个独立方法为5通过、3失败方法，共6个失败断言/子例（跨代4种调用、类型边界各1）。候选是否接受及缺口优先级由主会话决定；建议先处理旧owner回调跨代影响，再进入真实actor接入。后两项不是“实际Win32已经返回错误类型”的证据。

## AOR-R1：旧owner公开调用可停止已经恢复的新BOOT（可用性，P2建议）

来源 `simulation/isolation/actor_owner.py:388`：`_close_internal`先调用`_revoke(reason)`，然后才检查`_cleanup_attempted`并返回旧结果。`actor_owner.py:251`的`_revoke`每次都会调用先前保存的`runtime.stop`、`executor.revoke`，即使旧owner已CLOSED；callbacks在`:372`保存，没有绑定代次的失效检查或一次性分离。

最小正常API序列：

1. actor1已绑定实际PcDirectRuntime／OwnedMotionExecutor与BOOT1。
2. `actor1.close('old retirement')`完成；同registry新建actor2。
3. 对同一runtime／executor激活新session8／generation2，绑定actor2，接好actor2.ai_lease，入新观测与命令。此时executor未stopped；作者现有恢复回归也证明这条新actor路径可以真正数值提交。
4. 再调用`actor1.close('repeat retired owner cleanup')`。

实际结果：旧actor仍CLOSED、新actor仍BOUND_ACTIVE，但新runtime `_latched=True`、新executor `stopped=True`。原生fake调用列表未增加，说明不是重复native cleanup，而是旧存留callback改变新一代的活动控制状态。强保留旧owner、重复teardown／迟到清理属于该API可达操作，不需要篡改候选私有字段或伪造alive。

复现：`independent_actor_tests.OwnerIndependent.test_repeat_old_close_does_not_revoke_fresh_replacement_boot`；原始close失败见`independent8_only.stderr.txt`、`repeat_old_close.witness.json`。按主会话要求，同一方法扩为4个子例而未增加方法数量：`old.close(...)`、`old.poll()`、`old.ai_lease(old_boot, now)`、参数错误的`old.ai_lease()`全部触发旧callbacks，新runtime/executor均被停止，native调用均未增加。后三者虽以ValueError拒绝旧调用，`_entry`的异常撤销仍影响新binding。最终日志`independent8_binding4.stderr.txt`，4份`old_binding_*.witness.json`。这是停止/可用性缺陷，不是已经证明的越权运动或碰撞。

最小后续修复范围建议由原作者新独占任务拥有 `actor_owner.py`、`test_actor_lifetime.py`、`docs/actor_lifetime.md`；callback派发必须只作用其原binding，可用BOOT/activation身份fence并在退休后分离。仅阻止重复close不足以覆盖poll、ai_lease和参数错误入口。不能只凭本地owner状态忽略部分激活失败所需的撤销；原binding首次异常仍应先停止两方，再诊断/cleanup。保留原异常传播、重入不恢复、一次native cleanup和未知副作用QUARANTINED资源所有权；旧binding迟到调用不得降低清理/隔离能力。回归应覆盖CLOSED及QUARANTINED旧owner在新代就绪后四类公开入口；不在本审查修代码。

## AOR-R2：cleanup将False当成WAIT_OBJECT_0（依赖形状漂移，P2防御建议）

来源为未改的依赖 `simulation/isolation/windows_cleanup.py:24`、`:35`、`:37`，由新owner在`actor_owner.py:402`进入：使用`state == 0`和`state in (0,258)`，没有严格int形状门。`actor_lifetime.py`的正样本路径已有严格int门，cleanup路径没有同等保护。

最小fake反例：正常launch后仅令FakeApi.Wait返回布尔`False`，调用`actor.close(...)`。实际actor报CLOSED，process reference被标terminal_confirmed，关闭process/job并删除profile，FakeApi.live仍True；没有合法整数终止观察。这违反“未知terminal保留恢复控制”的形状防御目标。

复现：`test_boolean_wait_cleanup_cannot_confirm_terminal`，失败与`boolean_wait_cleanup.witness.json`。**界限：当前冻结的Win32 Wait绑定restype是W.DWORD，正常Python结果为int；本例只证明注入seam/未来依赖漂移下的错误分类，未证明真实进程被提前关闭或原生Wait返回bool。** 该缺口在共享cleanup helper中，原五文件作者范围没有修改它；若主会话采纳，应另明确授予`windows_cleanup.py`及对应fake cleanup测试的ownership，不能让作者越界顺手改。

## AOR-R3：继承flags的bool回读被整数等值接受（依赖形状漂移，P2防御建议）

来源`actor_owner.py:314`：直接比较`[handle_flags(...)]`与`[1,1]／[0,0]`。最小fake反例只将既有FakeApi.handle_flags结果转bool；`True==1/False==0`使检查通过，actor被resume并返回RUNNING_UNBOUND。

复现：`test_boolean_flag_readback_is_not_an_integer_bitmask`及`boolean_flags.witness.json`。**界限：冻结原生helper的handle_flags正常返回DWORD.value整数；这是严格形状防御缺口，不是实际继承标志已经错误的证据。** 最小修复可留在原作者actor_owner/test_actor_owner/docs范围，先保存4个回读，再逐项要求严格整数及精确值；所有错误必须在resume前进入原cleanup。

## 已验证的保护与故意保留的接入缺口

精确作者116回归独立exit0、0skip；原失败日志37/41/46/52方法及最终116记录实读核对，未把各历史测试版本当成同一套最终用例重演。作者初始RED37、边界RED41（5fail/1error）、continuity RED46（5fail/1error）、private RED52（2fail）均保留。

新增四项保护测试通过：clock/native wait内caught diagnostics重入会停止实际runtime/executor；在wait中跨线程调用registry.launch只置pending veto且不提前close原HANDLE，随后同线程停止；Wait返回IntEnum(258)不能当严格int正样本；原始BaseException取消从实际runtime.step传播，actor先撤销、executor pending清空且pose_revision不变。其余已有原HANDLE连续性、clock回归/慢样本/固定deadline、替换reference、失败callback／sink、部分activation和真实数值final fence的证据复用116回归，不为计数重复扩大套件。

第五个“通过”的独立方法是**显式负向集成见证**，不是安全通过：把trusted provider.ai_lease从actor方法换成fixture静态provider后，让fake actor process死亡，实际runtime/executor仍能提交一个数值pose（revision1）。记录`provider_detached_integration_gap.witness.json`。这有意演示文档已声明的composition义务：新组件并不自动拦截任意直接runtime调用，也不验证/注册实际ai_lease routing；未来真实composition必须绑定并维护原actor provider、prepare/commit对象与双向撤销。此处没有将fixture verifier注册进Run，也不把它列作新增候选安全漏洞或实际AI运动证据。

20处actor API调用的参数形状与当前win32.py Python定义／ctypes绑定静态匹配，见helper_signatures.json；从未导入Win32 DLL模块或调用native。`create_profile`与`create_suspended`内部先登记成对资源、parent只继承两端点、AssignJob/inspect先于resume、持原process HANDLE调用Wait(handle,0)、资源sealed且一次cleanup的源流与同步prototype对照已读。此静态兼容性不等于OS token/ACL/mitigation/job/指针行为实际通过。

诊断输出还有明确边界：现有available_output helper最多读8192，actor的较小output_limit在helper返回后检查，未作为读取参数传入。它仍有8192硬上限并丢弃raw输出；若把文档“按output_limit有界”解读为严格native读字节上限，需要另澄清/接口调整。本审查未把该差异升级为泄漏或实际资源失控。

positive sample只证明原对象曾在该观察点nonsignaled，不能保证未来存活/AI响应/有效推断。sample-to-CAS death、CreateProcess-to-AssignJob窗口、owner hang／job最后持有者、实际BOOT/readiness认证、持续因果IPC、项目模型、全H12链路与Run注册仍是未执行依赖，作者文档已有正确限制；本审查不去实际启动native补这些门。

## 身份、测试及冻结

HEAD `3f702903f1e16fa72eae15f03ba431b78de24bd0`；作者manifest SHA256 `2bace7921cd89ff2cf7e9d1dd8b87dbd1be6f4d34abd1ac3cc3d37026dc39630`。五候选live／frozen／raw-Git-object／Git-clean-object完全一致。设计、作者report/receipt/native terminal已核验固定SHA；before.json保存34个候选/依赖/规则文件。after.json在冻结时复核，没有写产品、C-owned inherited dirty或旧证据。

原始命令argv／cwd／per-process PYTHONPATH/TEMP、exit0/1及stdout/stderr见各result.json。复现整个独立方法集：从ROOT运行 `.local/venv/Scripts/python.exe -B -X utf8 .planning/deepeye-resume-20261018/actor-owner-review/run_tests.py independent_repro`，新label避免覆盖旧日志。原`independent8`首轮因测试模块导入作者TestCase而被unittest一并发现32项，实际40方法/3fail，原日志保留；只改审查脚本为模块别名导入，`independent8_only`精确8方法/3fail，其当时脚本字节另存`independent_actor_tests.initial8.py.txt`。最终扩展同一方法的4种旧binding入口后，`independent8_binding4`为8方法/6失败断言或子例、仍仅3个失败方法；该版本即冻结的`independent_actor_tests.py`。没有改任何生产guard或作者fixture来制造失败。

审查完成不等于候选已获主验收。H01–H15合同`DEEPEYE-HUMAN-LOCK-20261014/revision1`及canonical SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`实算匹配。全部29正式卡、实际native actor、真实项目AI、游戏/板卡、两完整H12链路、产品Run均 **not_run**。

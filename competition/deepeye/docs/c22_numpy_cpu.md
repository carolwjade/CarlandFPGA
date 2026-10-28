# 固定 C22 模型的 NumPy CPU 后端

本目录现已收录固定 C22 FORCE 模型、预处理资料及 NumPy 推理后端。14 个源码/资产文件与原 owned09 私有阶段的输入逐字节一致；没有把外部 Python、NumPy 或系统 DLL 复制进仓库。

`ai_pc/cpu_package/numpy_model.py` 加载固定模型，`numpy_leaf.py` 执行完整的 8 层、4916 参数、float32 图；`numpy_stream_core.py` 保留因果窗口和会话状态，`numpy_process_endpoint.py` 提供串行请求/响应驱动。受控导入根为 `competition/deepeye`，外部 NumPy 版本为 2.5.4。线程环境必须在导入 NumPy 前设定；本后端自身检查原有五个线程环境值均为 1。

这里保留 C22 的严格 FORCE 输入语义、模型/预处理/源码 SHA 及相对资产路径。`force_cnn.py` 由 NumPy 后端读取原字节用于身份核对；NumPy 推理路径不调用该模块的 Torch 实现。训练来源路径仅为历史资料，不是运行时依赖。

## 已有实测证据

- 官方 CPU Torch 与 NumPy 的三份固定输入对照，最大概率差 `4.470348358154297e-8`、最大 logit 差 `4.76837158203125e-7`。
- 原 owned09 操作在原有隔离策略和 256 MiB actor 限制下完成 READY、OBSERVE、RESULT、END、ENDED；只有一次实际模型 forward，反馈窗口为 `39.8192 ms`。原进程退出与资源清理已核对。
- 本次源码迁移只核对字节、Python 语法、相对依赖和固定 SHA；没有重跑模型、endpoint 或板测。原始证据摘要见 `../evidence/system/a-c22-numpy-owned09-20261028/`。

## 接入边界

该源码可供下一步受控 PC 端进程部署和 broker 接入复用。当前产品工厂尚未切换为持续运行的 NumPy endpoint；不能直接用裸 CLI 的结果替代原 HANDLE、会话、时间和期限绑定。

FORCE Macro-F1 为 `0.1827348057438266`，质量门仍失败。FORCE 的 GR/RHOB/NPHI/RDEP 不得改名为数字孪生 EM/振动或由四路硬件值补零冒充；新传感域须使用独立合法 profile、校准、数据及模型。本次单次 CPU 反馈不是 ROCm 与 3D 并发 1000 次的 P95 验收，也不证明 ADC、G03、R03、完整 H12 或全部 29 卡通过。H01-H15 及原合同保持不变。

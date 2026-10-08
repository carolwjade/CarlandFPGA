# PYNQ-Z2 上位机与 FPGA 工具链部署记录（2026-10-08）

本记录区分“软件已装并运行”“安装资料已备齐”“受账号/实板条件阻断”。选题初稿尚未锁定上位机数据协议，因此此处部署可复用的开发、采集和观察环境，不把任一串口帧格式或性能指标写成最终方案。

## 本机已验证

| 项目 | 实际状态与路径 | 本次证据 |
| --- | --- | --- |
| Windows 主机 | Windows 11 Home 25H2，x64，build 26200 | `Get-CimInstance Win32_OperatingSystem` 与 CurrentVersion 注册表 |
| RTL 仿真/编译 | ModelSim SE-64 2020.4，`C:\modeltech64_2020.4\win64\` | 上一轮最小 RTL smoke 通过；本轮 preflight 发现 `vsim.exe`，见下方命令 |
| 编辑与 Python 调试 | VS Code 1.140.0，`C:\Users\CarlJade\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd` | `code.cmd --version`；Python、Pylance、debugpy 扩展清单核验 |
| 串口/SSH 终端 | PuTTY 0.85（含 Plink），WinGet 用户安装目录 | `PLINK.EXE -V` 输出 Release 0.85 |
| SD 镜像写入工具 | balenaEtcher 2.1.7，`C:\Users\CarlJade\AppData\Local\balena_etcher\balenaEtcher.exe`；Rufus 4.15，`C:\Users\CarlJade\AppData\Local\Microsoft\WinGet\Packages\Rufus.Rufus_Microsoft.Winget.Source_8wekyb3d8bbwe\rufus.exe` | 两者文件签名有效；尚未指定 SD 卡，均未执行写入 |
| 独立上位机 Python | `D:\PynqZ2\host-venv\Scripts\python.exe`，Python 3.12.10、pyserial 3.5、NumPy 2.5.3、Matplotlib 3.11.2 | `pip check` 无冲突；`loop://` 串口回环收发、无窗口 Agg 绘图均通过 |
| PYNQ-Z2 board files | `D:\PynqZ2\board_files\pynq-z2\A.0\` | 来源 commit 和 SHA-256 见 `D:\PynqZ2\board_files\SOURCE_MANIFEST.json`；3 个 XML 可解析 |
| PYNQ-Z2 v3.1.1 SD 镜像 | `D:\PynqZ2\downloads\pynq_z2_v3.1.1.zip`，1,926,017,023 bytes | SHA-256 `d7774bb6c56b79ea67e4dbfadca443c51ae6152b8c71799e79dd81e4782d6b03`；ZIP CRC 通过；完整清单见同目录 `SOURCE_MANIFEST.json` |

当前 `python -m serial.tools.list_ports` 返回 `no ports found`，表示本机没有发现已连接的板卡串口。上位机环回测试不是板卡通信测试。

本次更新后的全仓 `python -m unittest discover -s tests -q` 为 **190/190 通过**；`compileall` 与 `git diff --check` 退出码为 0。测试运行时已有 Feishu 验证链接输出和第三方 deprecation/asyncio 警告，本轮没有按该链接操作；它们不构成 FPGA 实板证据。

可复核的静态工具发现命令：

```powershell
& .local\venv\Scripts\python.exe skills\pynq-z2-single-node\scripts\preflight.py --modelsim-home C:\modeltech64_2020.4
```

本次返回 `modelsim.available=true` 且定位 `C:\modeltech64_2020.4\win64\vsim.exe`；`vivado.available=false`、`board.status=not_checked`。该脚本只检查可执行文件，不启动 Vivado 或 ModelSim。

## Vivado 安装门槛

PYNQ 3.1 的基础 Overlay 使用 Vivado 2024.1 构建。PYNQ-Z2 的 XC7Z020 在 Vivado ML Standard 的免费器件范围内。目标是安装官方 Vivado ML Standard 2024.1，并只选 Zynq-7000；不为尚未确定的 HLS、ARM 裸机或系统镜像重建预装 Vitis/PetaLinux。

已在 [AMD 2024.1 官方下载页](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2024-1.html) 点击 215.97 MB Windows Web Installer，实际跳转到 `login.amd.com` 的账号密码页面。本机没有已登录会话，因此安装器尚未取得，`vivado -version`、综合/实现、`.bit/.hwh` 均不能验收。AMD 官方 Web Installer 要求账号认证，安装过程还要阅读并接受许可条款。

本机是 Windows 11 Home 25H2；[Vivado 2024.1 的官方系统矩阵](https://docs.amd.com/r/2024.1-English/ug973-vivado-release-notes-install-license/Supported-Operating-Systems) 只列 Windows 10 Pro/Enterprise 22H2 和 Windows 11 22H2/23H2。该主机不在其列明配置中。若在本机安装，必须用实测验证启动、仿真/综合、实现和线缆连接；不能把“安装完成”当成官方兼容性证明。

账号步骤完成后，选择无空格的 D 盘安装目录；把已核验的 `pynq-z2` board files 放入 `data\boards\board_files`，然后运行 `vivado -version`、XSim/RTL 编译和真实 XC7Z020 最小工程。安装器和实际 Vivado 安装包不得混入 Git/分发 ZIP。AMD Ross Vivado MCP 仅在 Vivado 本体可用后再连接并做 Tcl 烟测。

## 开发板启动与下一阶段

官方 PYNQ-Z2 v3.1.1 镜像已下载并校验，ZIP 内是单个 `pynq_z2_v3.1.1.img`。已展开到 `D:\PynqZ2\downloads\pynq_z2_v3.1.1.img`，8,337,309,696 bytes，SHA-256 为 `4a6ac1cdbb413d768fcb059b7182e1f53aa7f728b898b7f5061cbb0b7cc93aab`。写卡前必须核对可移动盘设备，不能根据盘符猜测；当前没有明确 SD 卡目标，尚未写卡。板上 Jupyter 由镜像提供，主机浏览器通过以太网访问；USB 串口可用 PuTTY，官方设置为 115200/8N1、无流控。板卡接入后再保存端口枚举、镜像版本、启动日志和 Overlay 实测。

Rufus 启动验证触发 Windows 管理员授权提示，已中断启动；随后复查 `consent.exe` 已退出，没有授权或执行写卡。Raspberry Pi Imager 的安装因需要同类授权而取消；已安装的 Etcher/Rufus 已备好，待确认可移动 SD 卡后再验证实际写卡。

参考：[PYNQ-Z2 设置](https://pynq.readthedocs.io/en/v3.1/getting_started/pynq_z2_setup.html)、[PYNQ Overlay 文件要求](https://pynq.readthedocs.io/en/latest/overlay_design_methodology/overlay_design.html)、[PYNQ 3.1 镜像构建版本](https://pynq.readthedocs.io/en/v3.1/pynq_sd_card.html)、[AMD XUP PYNQ-Z2 board files](https://github.com/Xilinx/xup_embedded_system_design_flow/tree/main/board_files/pynq-z2/A.0)。

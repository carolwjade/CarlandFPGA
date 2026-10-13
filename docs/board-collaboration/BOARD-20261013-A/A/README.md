# BOARD-20261013-A: actual board feedback

Status: actual A-led shared-board execution and error feedback verified; B/C readback pending. Functional BRAM validation failed at metadata lookup, with zero comparisons. This is basic workchain acceptance, not a functional BRAM pass.

The human scope is to let B/C submit content to A, have A execute it through the actual connected PYNQ-Z2, and return results and errors to the same PR and group. A alone performs physical operations.

The initial real board runtime probe completed with exit 0 on 2026-10-13. It observed PYNQ 3.0.1, Python 3.10.4, ARMv7 and kernel 5.15.19-xilinx-v2022.1. Matching base Overlay files were present; that initial probe did not load the FPGA.

The exact B PR9 head bb0d302331785defb59fc8d47eeea5d27fb33e81 was executed once on the board. The installed base Overlay loaded successfully with matching bit/HWH hashes. The script then exited1 with metadata KeyError for iop_pmoda/mb_bram_ctrl; reset and BRAM test access were not reached. B's functional stage is failed. Original JSON/stdout/stderr and exact request bindings are in B-base-bram-v2-reset-origin-r1/.

The first accepted C PR8 request, head78f3c7b5b823184c8a4cbffffb24d4dfb98a63f4 and request1b06302e466b1de03513bc42f87c1ed111d026c40552e43a4878cbbdbc843070, produced the expected RuntimeError/exit1 on the actual board's CPython3.10.4/Linux. All10 raw Git blobs and canonical request hash were verified for the formal run. A first run using archive-converted newlines is retained separately and excluded from exact-byte acceptance. The probe has no overlay/peripheral access. C-error-feedback-v3/ preserves both runs without changing the original request.

PR10 subsequently advertised the same C operation ID with a different request hash. A did not execute that replacement under the original operation. The first accepted PR8 result remains immutable.

GPIO output readback was excluded because the on-board PYNQ output slice returns a software shadow and AXI GPIO output DATA reads zero. See [AMD PG144](https://docs.amd.com/r/en-US/pg144-axi-gpio/AXI-GPIO-Data-Register-GPIOx_DATA).

Each result records operation ID, request hash, source code commit, actual tested PR head, exact script/Overlay hashes, command, exit status and original output hashes. Host timestamps are authoritative: the board's internal clock reported2022, which is retained as observed and was not adjusted. No new custom RTL synthesis or implementation was run. Acknowledgements and same-PR feedback will be linked after readback.

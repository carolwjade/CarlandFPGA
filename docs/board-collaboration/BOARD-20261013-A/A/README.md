# BOARD-20261013-A: actual board feedback

Status: actual A-led shared-board execution, error feedback and B/C readback verified. Functional BRAM validation failed at metadata lookup, with zero comparisons. The required group summary remains pending delivery because Astra-A's existing tenant-token endpoint returns access-control code 21001. This is basic workchain evidence, not a functional BRAM pass or completed group notification.

The human scope is to let B/C submit content to A, have A execute it through the actual connected PYNQ-Z2, and return results and errors to the same PR and group. A alone performs physical operations.

The initial real board runtime probe completed with exit 0 on 2026-10-13. It observed PYNQ 3.0.1, Python 3.10.4, ARMv7 and kernel 5.15.19-xilinx-v2022.1. Matching base Overlay files were present; that initial probe did not load the FPGA.

The exact B PR9 head bb0d302331785defb59fc8d47eeea5d27fb33e81 was executed once on the board. The installed base Overlay loaded successfully with matching bit/HWH hashes. The script then exited1 with metadata KeyError for iop_pmoda/mb_bram_ctrl; reset and BRAM test access were not reached. B's functional stage is failed. Original JSON/stdout/stderr and exact request bindings are in B-base-bram-v2-reset-origin-r1/.

The first accepted C PR8 request, head78f3c7b5b823184c8a4cbffffb24d4dfb98a63f4 and request1b06302e466b1de03513bc42f87c1ed111d026c40552e43a4878cbbdbc843070, produced the expected RuntimeError/exit1 on the actual board's CPython3.10.4/Linux. All10 raw Git blobs and canonical request hash were verified for the formal run. A first run using archive-converted newlines is retained separately and excluded from exact-byte acceptance. The probe has no overlay/peripheral access. C-error-feedback-v3/ preserves both runs without changing the original request.

PR10 subsequently advertised the same C operation ID with a different request hash. A did not execute that replacement under the original operation. C withdrew the duplicate execution request and A closed PR10 without merging or deleting its evidence. The first accepted PR8 result remains immutable.

GPIO output readback was excluded because the on-board PYNQ output slice returns a software shadow and AXI GPIO output DATA reads zero. See [AMD PG144](https://docs.amd.com/r/en-US/pg144-axi-gpio/AXI-GPIO-Data-Register-GPIOx_DATA).

Each result records operation ID, request hash, source code commit, actual tested PR head, exact script/Overlay hashes, command, exit status and original output hashes. Host timestamps are authoritative: the board's internal clock reported2022, which is retained as observed and was not adjusted. No new custom RTL synthesis or implementation was run.

B independently matched the frozen request, tested commit and original log bytes in [its PR9 readback](https://github.com/carolwjade/CarlandFPGA/pull/9#issuecomment-6142007242). C independently matched the original PR8 binding, nonce and formal raw logs in [its PR8 readback](https://github.com/carolwjade/CarlandFPGA/pull/8#issuecomment-6142506646). A's physical results were returned to [PR9](https://github.com/carolwjade/CarlandFPGA/pull/9#issuecomment-6141929443) and [PR8](https://github.com/carolwjade/CarlandFPGA/pull/8#issuecomment-6141930072). A further native read-only audit matched all four committed raw stdout/stderr blobs to the saved physical-run files.

The existing A group report `BOARD-20261013-A:measured-board-feedback-v1` has no `sent_at` or platform message ID at the recovery checkpoint. The original app is enabled and published, its application IP allowlist is empty, and both the local API audit and original app's server logs show token rejection 21001. The current account has no tenant Admin Console entry. Credentials, scopes, original queues and identities were preserved. These observations do not establish the policy's root cause or prove recovery. C was separately authorized to relay the verified measured summary through its existing Astra-C identity; that relay requires its own send and readback evidence.

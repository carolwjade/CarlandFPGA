# BOARD-20261013-A: actual board feedback

Status: pending submitted B/C PRs and actual execution. This record does not establish completed multi-machine board acceptance.

The human scope is to let B/C submit content to A, have A execute it through the actual connected PYNQ-Z2, and return results and errors to the same PR and group. A alone performs physical operations.

The initial real board runtime probe completed with exit 0 on 2026-10-13. It observed PYNQ 3.0.1, Python 3.10.4, ARMv7 and kernel 5.15.19-xilinx-v2022.1. Matching base Overlay files were present; that initial probe did not load the FPGA.

The planned B v2 test validates physical PS-to-PL AXI BRAM reads/writes and restoration using the board image's installed base Overlay. It does not claim a new custom RTL synthesis or routed implementation. The planned C v3 payload intentionally raises a known exception to test actual board error feedback; that injected exception is not a board fault.

GPIO output readback was excluded because the on-board PYNQ output slice returns a software shadow and AXI GPIO output DATA reads zero. See [AMD PG144](https://docs.amd.com/r/en-US/pg144-axi-gpio/AXI-GPIO-Data-Register-GPIOx_DATA).

Each final result will record operation ID, HardwareRequest hash, source code commit, actual tested PR head, script and installed Overlay hashes, exact command, exit status and original output hashes. B/C acknowledgements will be linked after actual readback.

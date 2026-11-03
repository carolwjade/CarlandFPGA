# FPGA UART and MCU follow-up stage

The human accepted run995 and requested physical UART integration: A owns the
PYNQ FPGA and simulation; B owns the G3507 MCU and actuators. The reported wiring
is PMODA1/Y18 TX to PB7 RX, PMODA2/Y19 RX from PB6 TX, and PMODA5 common ground,
with the XDS UART driver isolated. USB-only power and MCU feedback health remain
separate observations.

The new optional `fpga/diagnostic/uart_joint50_a` helper adds a dedicated
AXI UARTLite at 50MHz/115200 8N1, keeping existing G05 and TRACE windows and the
internal E4/PWM observation paths. UART address comes from actual generated HWH.
Vivado's range hint retained a preferred64KiB aperture in attempt1012; the new
helper explicitly selects the same4KiB extent used for the original windows.
Original timing, DDR and PWM checks remain, with new five-port and actual vendor
XPM receiver boundary checks.

Attempt1019 was observed stopped without terminal supervisor reports; some
generated caches failed byte checks and were preserved. Attempt1026 starts from
verified source with a private new cache. Generated HWH metadata has passed the
new three-IP check. Final route/bitstream and physical UART remain separate
results and must not be inferred from that metadata check.

`live_display_mailbox.py` passes only the newest existing NativeClient snapshot
to a separate IO owner. It retains original timestamps, checks the selected
mode/epoch, isolates copies and drops pending positive-speed data on close.
The PC Follower shares the PC's QPC domain. A persistent SSH target-level adapter
connects to PS-local UART MMIO; individual MMIO bytes and PC absolute QPC are not
sent as cross-machine control calls.

B's exact product-service source at commit7f2ee9ee6540a1a29c45b460a60809426d4c420e
was read through Git and checked as SHA256
6404ce0b0be4b1d1f85615f083c63b6d1df9fef2bd55bbaea022a35032acab13.
The first real transfer will be DIAGNOSTIC_ONLY STOP/STATUS after the new actual
loaded identity and B's unique sequence/writer handoff. B currently reports
MCU running with FAULT4 and no fresh servo feedback. This does not authorize
ARM, pose or motor. Original29 and both final H12 acceptance paths remain open.

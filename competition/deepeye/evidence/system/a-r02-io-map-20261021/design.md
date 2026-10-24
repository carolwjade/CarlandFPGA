# A R02 revised future-overlay pin and electrical candidate — static only

This is a proposed allocation for a future TUL PYNQ-Z2 custom overlay, not a report of existing hardware or a formal R02 pass. It preserves DeepEye contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15, SHA-256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. The only active director is generation-2 `01a13d7e-dcf1-7272-a738-a637dd62ff9d`. Main review and integrated-top adoption remain separate decisions. All 29 overall gates remain open.

## Existing-map check and source boundary

The targeted `taskbook_final.md`, current `competition/deepeye/docs/interface.json`, A board-baseline record and B op19 tree evidence contain requirements and generic interface timing, but no selected cross-connector R02 pin map. The assignment's older `docs/competition/deepeye-2026/interface.json` path is absent; the current product copy is under `competition/deepeye/docs/`. The board's actual PCB revision and any purchased modules/cables were not inspected. Source URLs, bytes, hashes and page/table pins are in `source-pins.json`; this successor references the predecessor's sealed retained originals without modifying them. The downloaded schematic URL ends in `R12.pdf`, yet its title blocks say `PYNQ-Z2 R10`; verify the actual PCB revision against the selected netlist before wiring.

## Digital allocation

**Wiring hold:** J3 I2C SCL/SDA physical contact positions are unresolved. The package-only constraints below do not license a physical J3 cable assignment.

All listed pins are Zynq PL package pins with 3.3 V `LVCMOS33`; bank numbers are from the TUL schematic sheet 11 package pin names and the Xilinx/PYNQ 3.1.1 `base.xdc`. The TUL manual v1.1 Tables 14, 17 and 19 support the PMODB, J4 and SPI positions. Manual Table 16 and schematic sheet 4 conflict on J3 I2C contact numbers; those two positions remain unresolved. `candidate.xdc` maps only these 15 proposed top-level ports. Pmod B pins 5/11 are GND, 6/12 are 3.3 V; pins 4/10 remain spare. Pmod A is deliberately untouched because it shares Raspberry Pi header signals.

| Logical port | Header:position / board net | Package / bank | Direction / external connection |
|---|---|---|---|
| `yaw_pwm_o` | PMODB:1 JB1_P | W14 / 34 | output; jumper to PMODB:7 |
| `pitch_pwm_o` | PMODB:2 JB1_N | Y14 / 34 | output; jumper to PMODB:8 |
| `speed_pwm_o` | PMODB:3 JB2_P | T11 / 34 | output; jumper to PMODB:9 |
| `yaw_capture_i` | PMODB:7 JB3_P | V16 / 34 | input; physical jumper from :1 |
| `pitch_capture_i` | PMODB:8 JB3_N | W16 / 34 | input; physical jumper from :2 |
| `speed_capture_i` | PMODB:9 JB4_P | V12 / 34 | input; physical jumper from :3 |
| `pga_cs_n_o` | Arduino SPI:5 AR_SS | F16 / 35 | MCP6S21 CS |
| `pga_sck_o` | Arduino SPI:3 AR_SCK | H15 / 35 | MCP6S21 SCK |
| `pga_sdi_o` | Arduino SPI:4 AR_MOSI | T12 / 34 | MCP6S21 SI |
| `dac_scl_io` | Arduino J3: **unresolved** AR_SCL (manual:10; schematic:9) | P15 / 34 | open-drain I2C SCL |
| `dac_sda_io` | Arduino J3: **unresolved** AR_SDA (manual:9; schematic:10) | P16 / 34 | open-drain I2C SDA |
| `rs485_tx_o` | Arduino J4:5 AR4 | V15 / 34 | THVD1450 D |
| `rs485_rx_i` | Arduino J4:6 AR5 | T15 / 34 | THVD1450 R |
| `rs485_de_o` | Arduino J4:7 AR6 | R16 / 34 | THVD1450 DE, active high |
| `rs485_re_n_o` | Arduino J4:8 AR7 | U17 / 34 | THVD1450 /RE, active low |

Six distinct PMODB package pins and **three actual external jumper pairs** give independent output and capture paths. No internal register loopback is substituted. Arduino SPI MISO (header pin 1, W15) is unused because MCP6S21 has no SO. The TUL PDF text layer appears to merge `W16` with a page number as `W156`; the PYNQ XDC and schematic independently show W16.

## Four analog inputs and source circuit

Use Arduino J1 A0–A3 as **analog**, not their direct digital GPIO taps. TUL manual v1.1 pp. 22, 25 and Figure 1 says these header contacts accept 0–3.3 V referenced to board GND: a 2.32 kΩ / 1 kΩ divider scales the XADC input to approximately 0–0.994 V at 3.3 V; its figure also shows 140 Ω series on positive, 845 Ω on negative and 1 nF across the XADC pair. The TUL schematic sheet 4 shows the individual resistor networks (for A0, upper R71 2.32 kΩ, lower R105 1 kΩ, positive-series R72 140 Ω, negative-series R73 845 Ω, and C3 1 nF). This is **not** evidence of a 3.3 V-safe bare XADC pin or of a protective clamp; no clamp is identified in that analog network. TUL's separate V_P/V_N J5 pair is 0–1 V and is not used here. The Arduino digital taps before the divider remain unallocated. The board manual warns against 5 V shields and gives a 3.4 V powered recommended maximum for digital Arduino I/O.

| Header | J1 position | XADC channel | P / N package pins, bank 35 | Intended analog source |
|---|---:|---|---|---|
| A0 | 6 | VAUX1 | E17 / D18 | post-PGA VOUT |
| A1 | 5 | VAUX9 | E18 / E19 | DAC B / pressure stimulus |
| A2 | 4 | VAUX6 | K14 / J14 | DAC C / obstacle stimulus |
| A3 | 3 | VAUX15 | K16 / J16 | same source before PGA (CH0 reference) |

The XADC wizard/integrated top must enable the indicated auxiliary channels and scale results back to header volts using the board divider, with calibration if accuracy matters. `candidate.xdc` has no active VAUX lines because the integrated XADC connection and tool-generated constraints must be checked first. Do not copy the base overlay's analog `LVCMOS33` constraints blindly onto a new analog top. Before applying gain, limit stimulus so PGA VOUT stays in its valid output range and A0 stays below 3.3 V. Four ADC readings do not imply four independently varied DAC sources when A0 and A3 must share the same source before/after gain.

## External devices and electrical wiring

**PGA:** Proposed Microchip MCP6S21, 3.3 V supply, VSS/VREF at GND for unipolar tests, CH0 from DAC A, VOUT to A0, and a branch from DAC A to A3. Datasheet DS21117B p. 1 shows 8-pin MCP6S21 has CS/SCK/SI and no SO; pp. 19–20 gives SPI write command `010` to gain register and codes `000/001/010/100` for gain `1/2/4/8`. Capture gain by measured A0/A3 ratio in the linear range, not a nonexistent SPI readback. Add local decoupling and verify exact module pinout before power.

**DAC:** Proposed Microchip MCP4728, 3.3 V supply, four 12-bit outputs. Datasheet DS22187E pp. 1 and 50–51: each channel can select external VREF=VDD (nominal 0–3.3 V range here), but EEPROM configuration persists across power cycles; do not assume default output/reference. Both I2C lines must be open-drain via PL IOBUF. TUL schematic sheet 4 already depicts R49/R50, each 2.2 kΩ from AR_SCL/AR_SDA to VCC3V3; inspect actual fitted PCB and any DAC-module/adapter pull-ups before adding a resistor. If fitted, total bus pull-up is `R_eq = 1/(1/2200 + Σ_i 1/R_module_i)` Ω. For example, one additional 10 kΩ to the same 3.3 V rail would give approximately 1.803 kΩ, not 10 kΩ. Microchip DS22187E §7.1 (printed p. 51, PDF p. 51 (zero-based index 50)) describes a typical 1–10 kΩ range for standard/fast modes and Fig. 7-1 illustrates 5–10 kΩ for 100–400 kHz; choose against actual capacitance, rise time and sink current, not an unverified extra resistor set. J3 physical contact numbers are conflicting: manual v1.1 Table 16 assigns SCL=10/SDA=9, while downloaded TUL schematic sheet 4 assigns SCL=9/SDA=10. The P15 SCL/P16 SDA package-net assignments agree with the pinned Xilinx/PYNQ 3.1.1 XDC. Resolve the physical contacts from actual PCB revision or de-energized continuity before connecting a module; do not treat either document alone as proof of contact position. The 7-bit address is EEPROM-programmable and must be read/verified on the actual part. DAC A fans out to PGA CH0 and A3; B to A1, C to A2, D reserved for a controlled future stimulus. This is a proposed cable/module arrangement, not proof those parts are installed.

**RS485:** Proposed TI THVD1450 half-duplex transceiver powered at 3.3 V. Datasheet SLLSEY3E Rev E p. 5 gives R pin 1, /RE pin 2, DE pin 3, D pin 4, GND pin 5, differential A pin 6, B pin 7, VCC pin 8 for its 8-pin variants. PL connects only to D/R/DE//RE; A/B run as a differential pair to a separate PC-side RS485 adapter. DE=0 disables transmission; /RE=0 enables reception. Candidate 10 kΩ external pull-downs on DE and /RE hold receive mode during PL reset, subject to actual module circuit. Final cable design must specify a common reference, correct A/B polarity, termination only at bus endpoints, bias if needed and voltage/domain compatibility. UART framing and direction timing remain an integrated-top implementation task.

**Clock/reset:** TUL manual v1.1 p. 6 identifies a **50 MHz PS_CLK** and a separate **125 MHz PL reference on H16** driven by the Ethernet PHY, which can disappear when PHY reset is asserted. The candidate 100 MHz timing domain is the PS-generated `FCLK_CLK0`, configured in the Zynq processing-system block; it is not a 100 MHz board oscillator or a pin in this XDC. Use `FCLK_RESET0_N` through a reset synchronizer or `processor_system_reset` for the 100 MHz domain. Arduino J7 `AR_RST` is PS MIO12 per manual Table 18 and is not a spare PL reset pin. Verify generated clock period, reset polarity and timing in the future BD/HWH before any implementation.

## Integration gates and evidence

The predecessor's 44/44 static check remains historical evidence for the first draft; it did not detect the J3 primary-source conflict or the board pull-ups. The successor's `conflict-check.json` checks only the three changed issues and requires both J3 alternatives to remain unresolved. Neither check proves actual contact placement or electrical behavior. It does not prove PCB revision compatibility, actual jumper/module/adapter presence, analog level or slew, I2C address, SPI transaction, RS485 bus operation, bitstream/HWH, board capture, or R02/R03 acceptance. The future integrator must review the selected board revision and module datasheets, wire the three jumpers and analog/electrical modules, instantiate the BD/XADC controllers, then measure the signals and capture the operation/commit-bound evidence required by the taskbook. No board or toolchain action was taken here.

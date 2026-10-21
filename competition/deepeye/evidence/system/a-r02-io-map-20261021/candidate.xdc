# A R02 proposed package constraints only; names must match a future integrated top.
# PYNQ-Z2: TUL manual v1.1 and schematic, Xilinx/PYNQ 3.1.1 base.xdc.
# WARNING: J3 I2C physical positions CONFLICT: manual Table16 SCL=10/SDA=9,
# schematic sheet4 SCL=9/SDA=10. P15/P16 package nets remain XDC-supported;
# resolve actual PCB revision/net continuity before connecting any I2C cable.
# DO NOT concatenate with base.xdc for the same ports; use one allocation.
set_property -dict {PACKAGE_PIN W14 IOSTANDARD LVCMOS33} [get_ports {yaw_pwm_o}]  ;# PMODB pin 1 JB1_P
set_property -dict {PACKAGE_PIN Y14 IOSTANDARD LVCMOS33} [get_ports {pitch_pwm_o}]  ;# PMODB pin 2 JB1_N
set_property -dict {PACKAGE_PIN T11 IOSTANDARD LVCMOS33} [get_ports {speed_pwm_o}]  ;# PMODB pin 3 JB2_P
set_property -dict {PACKAGE_PIN V16 IOSTANDARD LVCMOS33} [get_ports {yaw_capture_i}]  ;# PMODB pin 7 JB3_P
set_property -dict {PACKAGE_PIN W16 IOSTANDARD LVCMOS33} [get_ports {pitch_capture_i}]  ;# PMODB pin 8 JB3_N
set_property -dict {PACKAGE_PIN V12 IOSTANDARD LVCMOS33} [get_ports {speed_capture_i}]  ;# PMODB pin 9 JB4_P
set_property -dict {PACKAGE_PIN F16 IOSTANDARD LVCMOS33} [get_ports {pga_cs_n_o}]  ;# ARDUINO_SPI pin 5 AR_SS
set_property -dict {PACKAGE_PIN H15 IOSTANDARD LVCMOS33} [get_ports {pga_sck_o}]  ;# ARDUINO_SPI pin 3 AR_SCK
set_property -dict {PACKAGE_PIN T12 IOSTANDARD LVCMOS33} [get_ports {pga_sdi_o}]  ;# ARDUINO_SPI pin 4 AR_MOSI
set_property -dict {PACKAGE_PIN P15 IOSTANDARD LVCMOS33} [get_ports {dac_scl_io}]  ;# AR_SCL, J3 physical contact UNRESOLVED (manual 10; schematic 9)
set_property -dict {PACKAGE_PIN P16 IOSTANDARD LVCMOS33} [get_ports {dac_sda_io}]  ;# AR_SDA, J3 physical contact UNRESOLVED (manual 9; schematic 10)
set_property -dict {PACKAGE_PIN V15 IOSTANDARD LVCMOS33} [get_ports {rs485_tx_o}]  ;# ARDUINO_J4 pin 5 AR4
set_property -dict {PACKAGE_PIN T15 IOSTANDARD LVCMOS33} [get_ports {rs485_rx_i}]  ;# ARDUINO_J4 pin 6 AR5
set_property -dict {PACKAGE_PIN R16 IOSTANDARD LVCMOS33} [get_ports {rs485_de_o}]  ;# ARDUINO_J4 pin 7 AR6
set_property -dict {PACKAGE_PIN U17 IOSTANDARD LVCMOS33} [get_ports {rs485_re_n_o}]  ;# ARDUINO_J4 pin 8 AR7

# VAUX1/9/6/15 analog pins are intentionally absent here: instantiate/configure XADC
# against A0-A3 with bank-35 VAUX P/N pairs; do not drive their Arduino digital taps.
# PS FCLK0 100 MHz and FCLK_RESET0_N are generated BD nets, not package pins.
# Add timing/reset constraints only after integrated BD/top and generated clocks are inspected.
# I2C requires IOBUF/open-drain RTL; schematic R49/R50 show 2.2k to 3.3 V.
# Verify actual board/module pullups and parallel value; do not add blindly.

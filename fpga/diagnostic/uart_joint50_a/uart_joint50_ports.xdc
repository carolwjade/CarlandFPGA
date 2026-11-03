# Opt-in new-image PMODA UART; original PMODB PWM XDC remains unchanged.
set_property PACKAGE_PIN Y18 [get_ports {mcu_uart_tx_o}]
set_property IOSTANDARD LVCMOS33 [get_ports {mcu_uart_tx_o}]
set_property PACKAGE_PIN Y19 [get_ports {mcu_uart_rx_i}]
set_property IOSTANDARD LVCMOS33 [get_ports {mcu_uart_rx_i}]
# No fabricated external IO delay or broad clock exception. The new pre-opt
# hook calls check_uart_rx_cdc(...,1) to identify/constrain the actual first D;
# its three following XPM synchronizer links remain timed and are checked.

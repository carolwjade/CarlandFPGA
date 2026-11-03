# Opt-in additive AXI UARTLite for the 50MHz G05/TRACE product. Source defines
# procedures only. Root calls integrate once in a NEW build, never old556.
namespace eval ::uart_joint50_a {}
proc ::uart_joint50_a::need {ok why} {if {!$ok} {error "UART_JOINT50: $why"}}
proc ::uart_joint50_a::one {items why} {need [expr {[llength $items]==1}] "expected one $why";return [lindex $items 0]}
proc ::uart_joint50_a::quote {s} {return "\"[string map [list \\ \\\\ \" \\\" \n \\n \r \\r \t \\t] $s]\""}
proc ::uart_joint50_a::write_new {path data} {
    need [expr {[file pathtype $path] eq "absolute" && ![file exists $path]}] "fresh absolute output required: $path"
    set f [open $path {WRONLY CREAT EXCL}];puts $f $data;close $f
}
proc ::uart_joint50_a::window {space name} {
    set seg [one [get_bd_addr_segs -of_objects $space -filter "NAME =~ *${name}*"] "mapped $name"]
    set base [expr {[get_property OFFSET $seg]}];set range [expr {[get_property RANGE $seg]}]
    need [expr {$range==4096 && $base%4096==0 && $base>=0 && $base+4095<=0xffffffff}] "aligned4KiB mapping required"
    return [dict create instance $name base $base range $range segment $seg]
}
proc ::uart_joint50_a::window_json {w vlnv} {
    return [format {{"instance":%s,"vlnv":%s,"base":"0x%08X","range":"0x%X","segment":%s}} [quote [dict get $w instance]] [quote $vlnv] [dict get $w base] [dict get $w range] [quote [dict get $w segment]]]
}
proc ::uart_joint50_a::integrate {cfg} {
    foreach key {uart_instance baud_rate mapping_output xdc_path} {need [dict exists $cfg $key] "missing config $key"}
    need [expr {[lsort [dict keys $cfg]] eq [lsort {uart_instance baud_rate mapping_output xdc_path}]}] "unselected config fields"
    set name [dict get $cfg uart_instance]
    need [expr {$name eq "mcu_uart" && [dict get $cfg baud_rate]==115200}] "selected B MTR4 profile is mcu_uart/115200/8N1"
    set xdc [file normalize [dict get $cfg xdc_path]]
    need [file isfile $xdc] "explicit UART XDC fragment missing"
    need [expr {![file exists [dict get $cfg mapping_output]]}] "mapping already exists; no replay"
    set ps [one [get_bd_cells -quiet ps7_0] PS7]
    set ic [one [get_bd_cells -quiet axi_gp0] interconnect]
    need [expr {[get_property CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $ps]==50}] "existing PS FCLK0 must be50MHz"
    need [expr {[get_property CONFIG.NUM_SI $ic]==1 && [get_property CONFIG.NUM_MI $ic]==2}] "expected original GP0/twoMI before additive call"
    need [expr {[llength [get_bd_cells -quiet $name]]==0}] "UART already instantiated; no repeat"
    set space [one [get_bd_addr_spaces ps7_0/Data] PSaddressspace]
    set before {};set nets {}
    foreach instance {g05_50_0 trace50_0} master {M00_AXI M01_AXI} {
        dict set before $instance [window $space $instance]
        dict set nets $master [one [get_bd_intf_nets -of_objects [get_bd_intf_pins axi_gp0/$master]] oldAXInet]
    }
    set clock [one [get_bd_pins ps7_0/FCLK_CLK0] FCLK0]
    set clocknet [one [get_bd_nets -of_objects $clock] FCLK0net]
    set reset [one [get_bd_pins rst_fclk0/peripheral_aresetn] peripheralreset]
    set resetnet [one [get_bd_nets -of_objects $reset] peripheralresetnet]
    set uart [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_uartlite:2.0 $name]
    # Installed2026.1 IP xgui uses _d in MHz, generated plain parameter in Hz.
    set_property -dict [list CONFIG.C_BAUDRATE 115200 CONFIG.C_DATA_BITS 8 CONFIG.C_USE_PARITY 0 CONFIG.C_ODD_PARITY 0 CONFIG.C_S_AXI_ACLK_FREQ_HZ_d 50.0] $uart
    set_property CONFIG.NUM_MI 3 $ic
    connect_bd_intf_net [get_bd_intf_pins axi_gp0/M02_AXI] [get_bd_intf_pins $name/S_AXI]
    connect_bd_net $clock [get_bd_pins axi_gp0/M02_ACLK] [get_bd_pins $name/s_axi_aclk]
    connect_bd_net $reset [get_bd_pins axi_gp0/M02_ARESETN] [get_bd_pins $name/s_axi_aresetn]
    set_property CONFIG.FREQ_HZ 50000000 [get_bd_pins $name/s_axi_aclk]
    foreach instance {g05_50_0 trace50_0} master {M00_AXI M01_AXI} {
        need [expr {[window $space $instance] eq [dict get $before $instance]}] "existing mapping changed"
        need [expr {[one [get_bd_intf_nets -of_objects [get_bd_intf_pins axi_gp0/$master]] oldAXInet] eq [dict get $nets $master]}] "existing AXI connection changed"
    }
    set target [one [get_bd_addr_segs $name/S_AXI/Reg] UARTmemorysegment]
    assign_bd_address -target_address_space $space -range 4K $target
    # Vivado may retain its preferred64KiB aperture despite the range hint.
    # Select the same explicit4KiB mapped extent as the original two windows.
    set uart_mapped [one [get_bd_addr_segs -of_objects $space -filter "NAME =~ *${name}*"] UARTmappedsegment]
    set_property range 4096 $uart_mapped
    set added [window $space $name]
    foreach instance {g05_50_0 trace50_0} {
        set w [window $space $instance]
        need [expr {$w eq [dict get $before $instance]}] "existing address moved after UART autoassignment"
        set a [dict get $added base];set b [dict get $w base]
        need [expr {$a+4095<$b || $b+4095<$a}] "UART address overlaps existing window"
    }
    need [expr {[llength [get_bd_addr_segs -of_objects $space]]==3}] "exactly3 GP0 windows required"
    foreach {port direction pin} {mcu_uart_tx_o O tx mcu_uart_rx_i I rx} {
        need [expr {[llength [get_bd_ports -quiet $port]]==0}] "UART top port exists"
        set external [create_bd_port -dir $direction $port]
        connect_bd_net $external [get_bd_pins $name/$pin]
    }
    need [expr {[one [get_bd_nets -of_objects [get_bd_pins $name/s_axi_aclk]] UARTclk] eq $clocknet}] "UART clock source changed"
    need [expr {[one [get_bd_nets -of_objects [get_bd_pins $name/s_axi_aresetn]] UARTrst] eq $resetnet}] "UART reset source changed"
    add_files -fileset constrs_1 -norecurse $xdc
    set bid [string tolower [get_property CONFIG.BUILD_ID [get_bd_cells trace50_0]]]
    regsub {^0x} $bid {} bid
    need [expr {[regexp {^[0-9a-f]{32}$} $bid] && $bid ne "dc4e89ccf3db18c4f9871575efc399ba"}] "new unique non-old TRACE buildID required"
    set windows [list [window_json [dict get $before g05_50_0] carlandfpga.local:diagnostic:deepeye_g05_axi_50:1.0] [window_json [dict get $before trace50_0] carlandfpga.local:diagnostic:deepeye_trace50_axi:1.0] [window_json $added xilinx.com:ip:axi_uartlite:2.0]]
    set data [format {{"schema":"DEEPEYE-UART-JOINT50-v1","bd":"functional50_diag","top":"functional50_diag_wrapper","master":"ps7_0/Data","build_id":"%s","clock_hz":50000000,"uart":{"instance":"mcu_uart","baud":115200,"data_bits":8,"parity":false},"windows":[%s],"preserved_first_two":true,"address_assignment":"Vivado auto; HWH discovered; no UART base assumption","physical_validation":"not_run"}} $bid [join $windows ,]]
    write_new [dict get $cfg mapping_output] $data
    return [dict create uart $uart mapping [dict get $cfg mapping_output] clock_hz 50000000 baud 115200]
}

proc ::uart_joint50_a::check_implemented_ports {report_path} {
    set actual {}
    foreach port [get_ports -quiet] {
        set name [get_property NAME $port]
        if {![regexp {^(DDR_|FIXED_IO_)} $name]} {lappend actual $name}
    }
    need [expr {[lsort $actual] eq [lsort {yaw_pwm_o pitch_pwm_o speed_pwm_o mcu_uart_tx_o mcu_uart_rx_i}]}] "exact5scalar PL port closure"
    set rows [list "port\tdirection\tpackage_pin\tiostandard\tactual_bank\tbonded"]
    foreach {name pin direction} {mcu_uart_tx_o Y18 OUT mcu_uart_rx_i Y19 IN} {
        set port [one [get_ports -quiet $name] UARTport]
        need [expr {[get_property DIRECTION $port] eq $direction && [get_property PACKAGE_PIN $port] eq $pin && [get_property IOSTANDARD $port] eq "LVCMOS33"}] "UART package/3.3V/direction mismatch"
        set package [one [get_package_pins $pin] packagepin]
        need [expr {[get_property IS_BONDED $package]==1}] "UART pin not bonded"
        set bank [get_property BANK $package]
        need [expr {$bank ne ""}] "actual UART bank absent"
        lappend rows "$name\t$direction\t$pin\tLVCMOS33\t$bank\t1"
    }
    write_new $report_path [join $rows \n]
}

# Call inside the generated NEW implementation pre-opt hook with apply=1,
# then again after route with apply=0. Only RXpad->firstCDC-D is excepted.
# Installed UARTLite2026.1 HDL uses xpm_cdc_single DEST_SYNC_FF=4.
proc ::uart_joint50_a::check_uart_rx_cdc {report_path {apply_exception 0}} {
    set rx [one [get_ports -quiet mcu_uart_rx_i] RXport]
    set d [one [all_fanout -flat -endpoints_only -from $rx] RXfirstendpoint]
    need [expr {[get_property REF_PIN_NAME $d] eq "D"}] "RX first endpoint must beFF D"
    if {$apply_exception} {set_false_path -from $rx -to $d}
    set rows [list "stage\tcell\td\tclock\tASYNC_REG\ttimed_from_previous"]
    set used {};set previous_q "";set common ""
    for {set i 0} {$i<4} {incr i} {
        set cell [one [get_cells -of_objects $d] CDCcell]
        need [expr {[string match -nocase {*mcu_uart*} $cell] && [string match -nocase {*INPUT_DOUBLE_REGS3*} $cell]}] "RX boundary must belong to vendorUART XPM"
        need [expr {[get_property REF_NAME $cell] eq "FDRE" && [string toupper [get_property ASYNC_REG $cell]] in {TRUE 1}}] "actual XPM synchronizer FF missing"
        set clk [one [get_clocks -of_objects [get_pins $cell/C]] CDCclock]
        need [expr {[get_property PERIOD $clk]==20.0}] "UART CDC must use actual20ns clock"
        if {$common eq ""} {set common $clk}
        need [expr {$clk eq $common}] "CDC suffix clock changed"
        if {$i>0} {
            foreach delay {max min} {need [expr {[llength [get_timing_paths -from $previous_q -to $d -delay_type $delay -max_paths 1]]==1}] "CDC followingstage is falsely untimed"}
        }
        lappend used $cell;lappend rows "$i\t$cell\t$d\t$clk\tTRUE\t[expr {$i>0}]"
        set previous_q [one [get_pins $cell/Q] CDCQ]
        if {$i<3} {
            set net [one [get_nets -of_objects $previous_q] CDCnet]
            set d [one [get_pins -of_objects $net -filter {DIRECTION == IN}] CDCnextD]
        }
    }
    need [expr {[llength [lsort -unique $used]]==4}] "four distinct UART CDC FFs required"
    write_new $report_path [join $rows \n]
}

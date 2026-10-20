set_param general.maxThreads 1
set top deepeye_pwm_applied_capture
set part xc7z020clg400-1
if {[catch {
    puts "DEEPEYE_OOC_TOOL [version -short]"
    puts "DEEPEYE_OOC_THREAD_LIMIT [get_param general.maxThreads]"
    read_verilog -sv sources/deepeye_atomic_pwm.sv
    read_verilog -sv sources/deepeye_pwm_coherent_capture.sv
    read_verilog -sv sources/deepeye_pwm_applied_capture.sv
    synth_design -top $top -part $part -mode out_of_context -flatten_hierarchy rebuilt
    set actual_top [get_property TOP [current_fileset]]
    set design_name [get_property NAME [current_design]]
    puts "DEEPEYE_OOC_IDENTITY design=$design_name top=$actual_top expected=$top"
    if {[get_property PART [current_design]] ne $part} {
        error "Unexpected synthesized part"
    }
    set blackboxes [get_cells -hier -quiet -filter {IS_BLACKBOX == 1}]
    set latches [get_cells -hier -quiet -filter {REF_NAME =~ LD*}]
    set clocks [get_clocks -quiet]
    report_utilization -hierarchical -file utilization.rpt
    report_drc -file synthesis_drc.rpt
    write_checkpoint -force synthesized.dcp
    write_verilog -force -mode funcsim synthesized.v
    set f [open synthesis-facts.txt w]
    puts $f "tool=[version -short]"
    puts $f "top=$actual_top"
    puts $f "design_object_name=$design_name"
    puts $f "part=[get_property PART [current_design]]"
    puts $f "threads=[get_param general.maxThreads]"
    puts $f "blackboxes=[llength $blackboxes]"
    puts $f "latches=[llength $latches]"
    puts $f "clocks=[llength $clocks]"
    puts $f "cells=[llength [get_cells -hier -quiet]]"
    puts $f "ports=[llength [get_ports -quiet]]"
    puts $f "count_w=32"
    puts $f "witness_w=64"
    puts $f "tag_w=32"
    close $f
    if {$actual_top ne $top} {
        error "Unexpected fileset top: $actual_top, expected $top"
    }
    if {[llength $blackboxes] != 0 || [llength $latches] != 0} {
        error "Unexpected blackboxes or latches"
    }
    puts "DEEPEYE_OOC_SYNTHESIS_PASS"
} message options]} {
    puts stderr "DEEPEYE_OOC_SYNTHESIS_FAIL $message"
    puts stderr [dict get $options -errorinfo]
    exit 1
}
exit 0

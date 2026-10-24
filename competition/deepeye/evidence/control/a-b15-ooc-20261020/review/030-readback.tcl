set_param general.maxThreads 1
set checkpoint C:/Users/CarlJade/AppData/Local/Temp/deepeye-a-b15-ooc-20261020-fix2/artifacts/synthesized.dcp
if {[catch {
    puts "B15_REVIEW_TOOL [version -short]"
    puts "B15_REVIEW_THREADS [get_param general.maxThreads]"
    open_checkpoint $checkpoint
    set top [get_property TOP [current_fileset]]
    set part [get_property PART [current_design]]
    set blackboxes [get_cells -hier -quiet -filter {IS_BLACKBOX == 1}]
    set latches [get_cells -hier -quiet -filter {REF_NAME =~ LD*}]
    set f [open readback-facts.txt w]
    puts $f "tool=[version -short]"
    puts $f "top=$top"
    puts $f "part=$part"
    puts $f "design_object_name=[get_property NAME [current_design]]"
    puts $f "threads=[get_param general.maxThreads]"
    puts $f "blackboxes=[llength $blackboxes]"
    puts $f "latches=[llength $latches]"
    puts $f "clocks=[llength [get_clocks -quiet]]"
    puts $f "cells=[llength [get_cells -hier -quiet]]"
    puts $f "bit_ports=[llength [get_ports -quiet]]"
    close $f
    set pfile [open readback-ports.txt w]
    foreach p [lsort [get_ports -quiet]] {
        puts $pfile [format {%s|%s} [get_property NAME $p] [get_property DIRECTION $p]]
    }
    close $pfile
    report_utilization -hierarchical -file readback-utilization.rpt
    if {$top ne "deepeye_pwm_applied_capture" || $part ne "xc7z020clg400-1"} {
        error "Unexpected checkpoint identity"
    }
    if {[llength $blackboxes] != 0 || [llength $latches] != 0} {
        error "Checkpoint has blackboxes or latches"
    }
    if {[get_param general.maxThreads] != 1 || [llength [get_ports -quiet]] != 798} {
        error "Unexpected thread limit or ports"
    }
    close_design
    puts "B15_CHECKPOINT_READBACK_PASS"
} message options]} {
    puts stderr "B15_CHECKPOINT_READBACK_FAIL $message"
    puts stderr [dict get $options -errorinfo]
    exit 1
}
exit 0

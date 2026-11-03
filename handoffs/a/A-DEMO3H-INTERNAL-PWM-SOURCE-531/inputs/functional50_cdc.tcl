# A519 explicit internal PWM feedback checker. Original external policy remains untouched.
source [file join [file dirname [info script]] original_external_cdc.tcl]
proc f519_internal_tap_check {root stage} {
    set all_d [get_pins -hierarchical -filter {REF_PIN_NAME == D}]
    set rows [list "channel\tstage\tD\tclock\tactual_driver"]
    set used {};set common {}
    foreach {idx out} {0 yaw_pwm_o 1 pitch_pwm_o 2 speed_pwm_o} {
        set pins {}
        foreach name {meta sync level} {
            set pattern [format {engine_i/capture_%s_q_reg\[%d\]/D$} $name $idx]
            set selected {}
            foreach p $all_d {if {[regexp $pattern [get_property NAME $p]]} {lappend selected $p}}
            f50_require {[llength $selected] == 1} "exact internal collector FF required: $name/$idx"
            set d [lindex $selected 0];set info [f50_ff $d]
            set clk [dict get $info clock]
            if {[llength $common] == 0} {set common $clk}
            f50_require {[f50_same_one $clk $common]} {all actual internal collector FFs must share 20ns clock}
            lappend used [get_property NAME $d];lappend pins $d
        }
        set first [lindex $pins 0]
        set port [get_ports -quiet $out]
        f50_require {[llength $port] == 1 && [get_property DIRECTION $port] eq "OUT"} "actual PWM output missing: $out"
        set pnet [get_nets -segments -of_objects $port]
        set drivers [get_pins -quiet -leaf -of_objects $pnet -filter {DIRECTION == OUT}]
        set inner $port
        foreach driver $drivers {
            set cell [get_cells -of_objects $driver]
            if {[get_property REF_NAME $cell] eq "OBUF"} {set inner [get_pins -of_objects $cell -filter {REF_PIN_NAME == I}]}
        }
        set expected [get_nets -segments -of_objects $inner]
        set actual [get_nets -segments -of_objects $first]
        set shared {}
        foreach n $actual {if {$n in $expected} {lappend shared $n}}
        f50_require {[llength $shared] > 0} "collector first D is not same actual internal PWM net: $out"
        lappend rows "$idx\tmeta\t[get_property NAME $first]\t[get_property NAME $common]\tactual_pwm_tap:$out"
        for {set n 1} {$n<3} {incr n} {
            set previous [get_cells -of_objects [lindex $pins [expr {$n-1}]]]
            set expected_q [get_pins -of_objects $previous -filter {REF_PIN_NAME == Q}]
            set target [lindex $pins $n]
            set actual_driver [get_pins -quiet -leaf -of_objects [get_nets -quiet -of_objects $target] -filter {DIRECTION == OUT}]
            f50_require {[f50_same_one $actual_driver $expected_q]} "internal 3FF direct Q/D link broken: $out stage$n"
            lappend rows "$idx\t$n\t[get_property NAME $target]\t[get_property NAME $common]\t[get_property NAME $expected_q]"
        }
    }
    f50_require {[llength [lsort -unique $used]] == 9} {nine distinct original internal collector FFs required}
    set f [open [file join $root reports internal_pwm_tap_${stage}.tsv] w];puts $f [join $rows \n];close $f
    return [get_property NAME $common]
}
proc f50_run_pre_opt_hook {context} {
    set root [dict get $context run_root]
    f519_internal_tap_check $root pre_opt
    report_exceptions -file [file join $root reports internal_pre_opt_exceptions.txt]
    write_checkpoint [file join $root artifacts functional50_diag_pre_opt.dcp]
    puts "A519_INTERNAL_TAP_PRE_OPT_VERIFIED"
}

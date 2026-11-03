# Self-contained in the original separate pre-opt hook as well as main session.
if {[llength [info procs require]] == 0} {proc require {condition message} {if {![uplevel 1 [list expr $condition]]} {error $message}}}
if {[llength [info procs one]] == 0} {proc one {objects description} {require {[llength $objects]==1} "expected exactly one $description";return [lindex $objects 0]}}
if {[llength [info procs putfile]] == 0} {proc putfile {path data} {set f [open $path {WRONLY CREAT EXCL}];puts $f $data;close $f}}
# INTERNAL_PWM_REGISTER_EQUIVALENCE_V2. No name-only or behavioral guesses.
proc f551_netsame {a b} {
 set aa [get_nets -segments -of_objects $a];set bb [get_nets -segments -of_objects $b]
 foreach n $aa {if {$n in $bb} {return 1}}
 return 0
}
proc f551_driver {p} {
 return [one [get_pins -quiet -leaf -of_objects [get_nets -segments -of_objects $p] -filter {DIRECTION == OUT}] {unique actual leaf driver}]
}
proc f551_input_equiv {a b pin} {
 if {[f551_netsame $a $b]} {return same_actual_net}
 require {$pin in {CE R}} {nonconstant FDRE input nets differ}
 set ad [f551_driver $a];set bd [f551_driver $b]
 set ac [one [get_cells -of_objects $ad] {constant source A}];set bc [one [get_cells -of_objects $bd] {constant source B}]
 set ar [get_property REF_NAME $ac];set br [get_property REF_NAME $bc]
 require {$ar eq $br && $ar in {VCC GND}} {different-net constants must be actual same-valued VCC/GND primitives}
 require {[get_property REF_PIN_NAME $ad] eq [get_property REF_PIN_NAME $bd]} {constant source pins differ}
 return actual_same_value_${ar}
}
proc f551_clone_equiv {meta out idx root} {
 set op [one [get_ports $out] {actual PWM output}]
 set obq [f551_driver $op];set ob [one [get_cells -of_objects $obq] {actual output buffer}]
 require {[get_property REF_NAME $ob] eq "OBUF"} {exact actual OBUF required}
 set obi [one [get_pins -of_objects $ob -filter {REF_PIN_NAME == I}] {OBUF actual I}]
 set q1 [f551_driver $meta];set q2 [f551_driver $obi]
 require {[get_property REF_PIN_NAME $q1] eq "Q" && [get_property REF_PIN_NAME $q2] eq "Q"} {PWM sources must be true register Q outputs}
 set a [one [get_cells -of_objects $q1] {original PWM generator FF}];set b [one [get_cells -of_objects $q2] {actual OBUF-input FF}]
 require {[get_property REF_NAME $a] eq "FDRE" && [get_property REF_NAME $b] eq "FDRE"} {both actual PWM drivers must be identical FDRE primitive kind}
 set an [get_property NAME $a];set expected [format {engine_i/u_pwm/pwm_q_reg[%d]} $idx]
 require {[string match "*/$expected" $an] || [string equal [string range $an end-[expr {[string length $expected]-1}] end] $expected]} {collector actual driver must be original channel PWM generator FF}
 set ia [get_property INIT $a];set ib [get_property INIT $b]
 require {$ia ne "" && $ia eq $ib} {FDRE INIT differs or absent}
 set rows [list "channel\tinput\tactual_original\tactual_output\tproof"]
 foreach pin {C CE D R} {
  set pa [one [get_pins -of_objects $a -filter "REF_PIN_NAME == $pin"] {original FDRE input}]
  set pb [one [get_pins -of_objects $b -filter "REF_PIN_NAME == $pin"] {output FDRE input}]
  set proof [f551_input_equiv $pa $pb $pin]
  lappend rows "$idx\t$pin\t[get_property NAME $pa]\t[get_property NAME $pb]\t$proof"
 }
 foreach pin {C CE D R Q} {
  set pa [one [get_pins -of_objects $a -filter "REF_PIN_NAME == $pin"] {original actual primitive pin}]
  set pb [one [get_pins -of_objects $b -filter "REF_PIN_NAME == $pin"] {output actual primitive pin}]
  set va [get_property IS_INVERTED $pa];set vb [get_property IS_INVERTED $pb]
  require {$va in {0 1} && $vb in {0 1} && $va eq $vb} {actual nonempty pin inversion equality required}
  lappend rows "$idx\t${pin}_IS_INVERTED\t$va\t$vb\tactual_nonempty_pin_property"
 }
 set ca [get_clocks -of_objects [get_pins -of_objects $a -filter {REF_PIN_NAME == C}]]
 set cb [get_clocks -of_objects [get_pins -of_objects $b -filter {REF_PIN_NAME == C}]]
 require {[llength $ca]==1 && [f50_same_one $ca $cb] && [get_property PERIOD $ca]==20.0} {same actual 20ns PWM clock required}
 lappend rows "$idx\tINIT\t$ia\t$ib\tidentical_FDRE_initial_state"
 lappend rows "$idx\tQ\t[get_property NAME $q1]\t[get_property NAME $q2]\tstrict_identical_FDRE_state_recurrence"
 putfile [file join $root reports clone_equivalence_${idx}.tsv] [join $rows \n]
}

proc f556_internal_tap_check {root stage} {
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
        if {[llength $shared] == 0} {f551_clone_equiv $first $out $idx $root}
        lappend rows "$idx\tmeta\t[get_property NAME $first]\t[get_property NAME $common]\tactual_pwm_register_equivalence:$out"
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

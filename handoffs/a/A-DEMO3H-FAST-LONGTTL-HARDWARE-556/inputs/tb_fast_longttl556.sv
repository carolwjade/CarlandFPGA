`timescale 1ns/1ps
module tb_fast_longttl556;
 import deepeye_g05_profile_50mhz::*;
 logic [7:0] profile_id=1,speed_code=14;
 logic signed [15:0] yaw_q=10,pitch_q=0;
 logic [15:0] ttl_ms=1;
 wire legal;wire [3:0] reject_bits;wire [31:0] period_ticks,high_yaw,high_pitch,high_speed;wire [63:0] ttl_ticks,curvature_sum,curvature_limit;
 deepeye_g05_command_map_50mhz dut(.*);
 integer cases=0;
 task check_ttl(input [7:0] p,input [15:0] t,input bit ok);
 begin profile_id=p;ttl_ms=t;#1;
  if (legal!==ok || reject_bits[2]!==!ok) $fatal(1,"TTL_BOUNDARY_FAIL p=%0d ttl=%0d legal=%0d reject=%h",p,t,legal,reject_bits);
  if(ok && (ttl_ticks!==64'(t)*64'd50000 || period_ticks!==1000000 || high_yaw!==125080 || high_pitch!==125000 || high_speed!==32000)) $fatal(1,"UNCHANGED_MAPPING_FAIL");
  cases=cases+1;$display("TTL_CASE p=%0d ttl=%0d accepted=%0d ticks=%0d",p,t,legal,ttl_ticks);
 end endtask
 initial begin
  if(TTL_MAX_PROFILE1_MS!==12000 || TTL_MAX_PROFILE2_MS!==12000 || CLOCK_HZ!==50000000 || TTL_TICKS_PER_MS!==50000) $fatal(1,"PROFILE_METADATA_FAIL");
  check_ttl(1,0,0);check_ttl(1,1,1);check_ttl(1,3000,1);check_ttl(1,3001,1);check_ttl(1,11999,1);check_ttl(1,12000,1);check_ttl(1,12001,0);
  check_ttl(2,0,0);check_ttl(2,1,1);check_ttl(2,3000,1);check_ttl(2,12000,1);check_ttl(2,12001,0);
  profile_id=3;ttl_ms=3000;#1;if(legal || !reject_bits[0])$fatal(1,"INVALID_PROFILE_GUARD_FAIL");
  profile_id=1;ttl_ms=12000;speed_code=21;#1;if(legal || !reject_bits[1])$fatal(1,"SPEED_GUARD_FAIL");
  speed_code=20;yaw_q=15000;#1;if(legal || !reject_bits[3])$fatal(1,"CURVATURE_GUARD_FAIL");
  yaw_q=15001;#1;if(legal || !reject_bits[1])$fatal(1,"YAW_GUARD_FAIL");
  speed_code=0;yaw_q=1;#1;if(legal || !reject_bits[1])$fatal(1,"STOP_YAW_GUARD_FAIL");
  $display("A556_FOCUSED_RTL_PASS ttl_cases=%0d guard_cases=5",cases);$finish;
 end
endmodule

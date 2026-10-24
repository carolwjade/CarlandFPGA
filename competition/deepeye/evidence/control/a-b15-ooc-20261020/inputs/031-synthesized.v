// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2026.1 (win64) Build 6511674 Tue Jun 16 11:02:23 MDT 2026
// Date        : Tue Oct 20 16:04:27 2026
// Host        : DESKTOP-FBHOHIO running 64-bit major release  (build 9200)
// Command     : write_verilog -force -mode funcsim artifacts/synthesized.v
// Design      : deepeye_pwm_applied_capture
// Purpose     : This verilog netlist is a functional simulation representation of the design and should not be modified
//               or synthesized. This netlist cannot be used for SDF annotated simulation.
// Device      : xc7z020clg400-1
// --------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

module deepeye_atomic_pwm
   (running_q_reg_0,
    accepted,
    rejected,
    applied_q_reg_0,
    frame_start,
    pending_q_reg_0,
    rst_0,
    stop_0,
    applied_q_reg_1,
    window_active_q_reg,
    window_active_q_reg_0,
    stop_1,
    applied_q_reg_2,
    Q,
    \active_high_yaw_q_reg[31]_0 ,
    \active_high_pitch_q_reg[31]_0 ,
    \active_high_speed_q_reg[31]_0 ,
    D,
    \active_high_pitch_q_reg[31]_1 ,
    \active_high_speed_q_reg[31]_1 ,
    \active_tag_q_reg[31]_0 ,
    active_tag,
    \active_period_q_reg[31]_0 ,
    capture_rearm,
    cfg_ready,
    pwm,
    clk,
    rst,
    failure_event_q_reg,
    raw_fault_events,
    failure_event_q_reg_0,
    stop,
    cfg_period,
    cfg_high_yaw,
    cfg_high_pitch,
    cfg_high_speed,
    cfg_valid,
    cfg_tag);
  output running_q_reg_0;
  output accepted;
  output rejected;
  output applied_q_reg_0;
  output frame_start;
  output pending_q_reg_0;
  output rst_0;
  output stop_0;
  output [0:0]applied_q_reg_1;
  output window_active_q_reg;
  output window_active_q_reg_0;
  output stop_1;
  output applied_q_reg_2;
  output [31:0]Q;
  output [31:0]\active_high_yaw_q_reg[31]_0 ;
  output [31:0]\active_high_pitch_q_reg[31]_0 ;
  output [31:0]\active_high_speed_q_reg[31]_0 ;
  output [31:0]D;
  output [31:0]\active_high_pitch_q_reg[31]_1 ;
  output [31:0]\active_high_speed_q_reg[31]_1 ;
  output [31:0]\active_tag_q_reg[31]_0 ;
  output [31:0]active_tag;
  output [31:0]\active_period_q_reg[31]_0 ;
  output capture_rearm;
  output cfg_ready;
  output [2:0]pwm;
  input clk;
  input rst;
  input failure_event_q_reg;
  input [0:0]raw_fault_events;
  input failure_event_q_reg_0;
  input stop;
  input [31:0]cfg_period;
  input [31:0]cfg_high_yaw;
  input [31:0]cfg_high_pitch;
  input [31:0]cfg_high_speed;
  input cfg_valid;
  input [31:0]cfg_tag;

  wire [31:0]D;
  wire [31:0]Q;
  wire accepted;
  wire accepted_q1;
  wire accepted_q_i_10_n_0;
  wire accepted_q_i_2_n_0;
  wire accepted_q_i_3_n_0;
  wire accepted_q_i_4_n_0;
  wire accepted_q_i_5_n_0;
  wire accepted_q_i_6_n_0;
  wire accepted_q_i_7_n_0;
  wire accepted_q_i_8_n_0;
  wire accepted_q_i_9_n_0;
  wire [31:0]\active_high_pitch_q_reg[31]_0 ;
  wire [31:0]\active_high_pitch_q_reg[31]_1 ;
  wire [31:0]\active_high_speed_q_reg[31]_0 ;
  wire [31:0]\active_high_speed_q_reg[31]_1 ;
  wire [31:0]\active_high_yaw_q_reg[31]_0 ;
  wire [31:0]\active_period_q_reg[31]_0 ;
  wire [31:0]active_tag;
  wire [31:0]\active_tag_q_reg[31]_0 ;
  wire applied_q_i_1_n_0;
  wire applied_q_reg_0;
  wire [0:0]applied_q_reg_1;
  wire applied_q_reg_2;
  wire apply_now;
  wire boundary_now0__10;
  wire boundary_now0_carry__0_i_1_n_0;
  wire boundary_now0_carry__0_i_2_n_0;
  wire boundary_now0_carry__0_i_3_n_0;
  wire boundary_now0_carry__0_i_4_n_0;
  wire boundary_now0_carry__0_i_5_n_0;
  wire boundary_now0_carry__0_i_5_n_1;
  wire boundary_now0_carry__0_i_5_n_2;
  wire boundary_now0_carry__0_i_5_n_3;
  wire boundary_now0_carry__0_i_5_n_4;
  wire boundary_now0_carry__0_i_5_n_5;
  wire boundary_now0_carry__0_i_5_n_6;
  wire boundary_now0_carry__0_i_5_n_7;
  wire boundary_now0_carry__0_i_6_n_0;
  wire boundary_now0_carry__0_i_6_n_1;
  wire boundary_now0_carry__0_i_6_n_2;
  wire boundary_now0_carry__0_i_6_n_3;
  wire boundary_now0_carry__0_i_6_n_4;
  wire boundary_now0_carry__0_i_6_n_5;
  wire boundary_now0_carry__0_i_6_n_6;
  wire boundary_now0_carry__0_i_6_n_7;
  wire boundary_now0_carry__0_i_7_n_0;
  wire boundary_now0_carry__0_i_7_n_1;
  wire boundary_now0_carry__0_i_7_n_2;
  wire boundary_now0_carry__0_i_7_n_3;
  wire boundary_now0_carry__0_i_7_n_4;
  wire boundary_now0_carry__0_i_7_n_5;
  wire boundary_now0_carry__0_i_7_n_6;
  wire boundary_now0_carry__0_i_7_n_7;
  wire boundary_now0_carry__0_n_0;
  wire boundary_now0_carry__0_n_1;
  wire boundary_now0_carry__0_n_2;
  wire boundary_now0_carry__0_n_3;
  wire boundary_now0_carry__1_i_1_n_0;
  wire boundary_now0_carry__1_i_2_n_0;
  wire boundary_now0_carry__1_i_3_n_0;
  wire boundary_now0_carry__1_i_4_n_2;
  wire boundary_now0_carry__1_i_4_n_3;
  wire boundary_now0_carry__1_i_4_n_5;
  wire boundary_now0_carry__1_i_4_n_6;
  wire boundary_now0_carry__1_i_4_n_7;
  wire boundary_now0_carry__1_i_5_n_0;
  wire boundary_now0_carry__1_i_5_n_1;
  wire boundary_now0_carry__1_i_5_n_2;
  wire boundary_now0_carry__1_i_5_n_3;
  wire boundary_now0_carry__1_i_5_n_4;
  wire boundary_now0_carry__1_i_5_n_5;
  wire boundary_now0_carry__1_i_5_n_6;
  wire boundary_now0_carry__1_i_5_n_7;
  wire boundary_now0_carry__1_n_2;
  wire boundary_now0_carry__1_n_3;
  wire boundary_now0_carry_i_1_n_0;
  wire boundary_now0_carry_i_2_n_0;
  wire boundary_now0_carry_i_3_n_0;
  wire boundary_now0_carry_i_4_n_0;
  wire boundary_now0_carry_i_5_n_0;
  wire boundary_now0_carry_i_5_n_1;
  wire boundary_now0_carry_i_5_n_2;
  wire boundary_now0_carry_i_5_n_3;
  wire boundary_now0_carry_i_5_n_4;
  wire boundary_now0_carry_i_5_n_5;
  wire boundary_now0_carry_i_5_n_6;
  wire boundary_now0_carry_i_5_n_7;
  wire boundary_now0_carry_i_6_n_0;
  wire boundary_now0_carry_i_6_n_1;
  wire boundary_now0_carry_i_6_n_2;
  wire boundary_now0_carry_i_6_n_3;
  wire boundary_now0_carry_i_6_n_4;
  wire boundary_now0_carry_i_6_n_5;
  wire boundary_now0_carry_i_6_n_6;
  wire boundary_now0_carry_i_6_n_7;
  wire boundary_now0_carry_i_7_n_0;
  wire boundary_now0_carry_i_7_n_1;
  wire boundary_now0_carry_i_7_n_2;
  wire boundary_now0_carry_i_7_n_3;
  wire boundary_now0_carry_i_7_n_4;
  wire boundary_now0_carry_i_7_n_5;
  wire boundary_now0_carry_i_7_n_6;
  wire boundary_now0_carry_i_7_n_7;
  wire boundary_now0_carry_n_0;
  wire boundary_now0_carry_n_1;
  wire boundary_now0_carry_n_2;
  wire boundary_now0_carry_n_3;
  wire capture_rearm;
  wire [31:0]cfg_high_pitch;
  wire [31:0]cfg_high_speed;
  wire [31:0]cfg_high_yaw;
  wire [31:0]cfg_period;
  wire cfg_ready;
  wire [31:0]cfg_tag;
  wire cfg_valid;
  wire clk;
  wire eligible_application0;
  wire eligible_application2;
  wire eligible_application4;
  wire failure_event_q_reg;
  wire failure_event_q_reg_0;
  wire frame_start;
  wire frame_start_q_i_1_n_0;
  wire i__carry__0_i_1_n_0;
  wire i__carry__0_i_2_n_0;
  wire i__carry__0_i_3_n_0;
  wire i__carry__0_i_4_n_0;
  wire i__carry__0_i_5_n_0;
  wire i__carry__0_i_6_n_0;
  wire i__carry__0_i_7_n_0;
  wire i__carry__0_i_8_n_0;
  wire i__carry__1_i_1_n_0;
  wire i__carry__1_i_2_n_0;
  wire i__carry__1_i_3_n_0;
  wire i__carry__1_i_4_n_0;
  wire i__carry__1_i_5_n_0;
  wire i__carry__1_i_6_n_0;
  wire i__carry__1_i_7_n_0;
  wire i__carry__1_i_8_n_0;
  wire i__carry__2_i_1_n_0;
  wire i__carry__2_i_2_n_0;
  wire i__carry__2_i_3_n_0;
  wire i__carry__2_i_4_n_0;
  wire i__carry__2_i_5_n_0;
  wire i__carry__2_i_6_n_0;
  wire i__carry__2_i_7_n_0;
  wire i__carry__2_i_8_n_0;
  wire i__carry_i_1__0_n_0;
  wire i__carry_i_1__1_n_0;
  wire i__carry_i_1__2_n_0;
  wire i__carry_i_1__3_n_0;
  wire i__carry_i_1_n_0;
  wire i__carry_i_2__0_n_0;
  wire i__carry_i_2__1_n_0;
  wire i__carry_i_2__2_n_0;
  wire i__carry_i_2__3_n_0;
  wire i__carry_i_2_n_0;
  wire i__carry_i_3__0_n_0;
  wire i__carry_i_3__1_n_0;
  wire i__carry_i_3__2_n_0;
  wire i__carry_i_3__3_n_0;
  wire i__carry_i_3_n_0;
  wire i__carry_i_4__0_n_0;
  wire i__carry_i_4__1_n_0;
  wire i__carry_i_4__2_n_0;
  wire i__carry_i_4__3_n_0;
  wire i__carry_i_4_n_0;
  wire i__carry_i_5__0_n_0;
  wire i__carry_i_5__1_n_0;
  wire i__carry_i_5__2_n_0;
  wire i__carry_i_5__3_n_0;
  wire i__carry_i_5_n_0;
  wire i__carry_i_6__0_n_0;
  wire i__carry_i_6__1_n_0;
  wire i__carry_i_6__2_n_0;
  wire i__carry_i_6__3_n_0;
  wire i__carry_i_6_n_0;
  wire i__carry_i_7__0_n_0;
  wire i__carry_i_7__1_n_0;
  wire i__carry_i_7__2_n_0;
  wire i__carry_i_7__3_n_0;
  wire i__carry_i_7_n_0;
  wire i__carry_i_8__0_n_0;
  wire i__carry_i_8__1_n_0;
  wire i__carry_i_8__2_n_0;
  wire i__carry_i_8__3_n_0;
  wire i__carry_i_8_n_0;
  wire [2:0]p_0_in;
  wire payload_legal0__15;
  wire payload_legal0_carry__0_i_1_n_0;
  wire payload_legal0_carry__0_i_2_n_0;
  wire payload_legal0_carry__0_i_3_n_0;
  wire payload_legal0_carry__0_i_4_n_0;
  wire payload_legal0_carry__0_i_5_n_0;
  wire payload_legal0_carry__0_i_6_n_0;
  wire payload_legal0_carry__0_i_7_n_0;
  wire payload_legal0_carry__0_i_8_n_0;
  wire payload_legal0_carry__0_n_0;
  wire payload_legal0_carry__0_n_1;
  wire payload_legal0_carry__0_n_2;
  wire payload_legal0_carry__0_n_3;
  wire payload_legal0_carry__1_i_1_n_0;
  wire payload_legal0_carry__1_i_2_n_0;
  wire payload_legal0_carry__1_i_3_n_0;
  wire payload_legal0_carry__1_i_4_n_0;
  wire payload_legal0_carry__1_i_5_n_0;
  wire payload_legal0_carry__1_i_6_n_0;
  wire payload_legal0_carry__1_i_7_n_0;
  wire payload_legal0_carry__1_i_8_n_0;
  wire payload_legal0_carry__1_n_0;
  wire payload_legal0_carry__1_n_1;
  wire payload_legal0_carry__1_n_2;
  wire payload_legal0_carry__1_n_3;
  wire payload_legal0_carry__2_i_1_n_0;
  wire payload_legal0_carry__2_i_2_n_0;
  wire payload_legal0_carry__2_i_3_n_0;
  wire payload_legal0_carry__2_i_4_n_0;
  wire payload_legal0_carry__2_i_5_n_0;
  wire payload_legal0_carry__2_i_6_n_0;
  wire payload_legal0_carry__2_i_7_n_0;
  wire payload_legal0_carry__2_i_8_n_0;
  wire payload_legal0_carry__2_n_1;
  wire payload_legal0_carry__2_n_2;
  wire payload_legal0_carry__2_n_3;
  wire payload_legal0_carry_i_1_n_0;
  wire payload_legal0_carry_i_2_n_0;
  wire payload_legal0_carry_i_3_n_0;
  wire payload_legal0_carry_i_4_n_0;
  wire payload_legal0_carry_i_5_n_0;
  wire payload_legal0_carry_i_6_n_0;
  wire payload_legal0_carry_i_7_n_0;
  wire payload_legal0_carry_i_8_n_0;
  wire payload_legal0_carry_n_0;
  wire payload_legal0_carry_n_1;
  wire payload_legal0_carry_n_2;
  wire payload_legal0_carry_n_3;
  wire payload_legal1__15;
  wire payload_legal1_carry__0_i_1_n_0;
  wire payload_legal1_carry__0_i_2_n_0;
  wire payload_legal1_carry__0_i_3_n_0;
  wire payload_legal1_carry__0_i_4_n_0;
  wire payload_legal1_carry__0_i_5_n_0;
  wire payload_legal1_carry__0_i_6_n_0;
  wire payload_legal1_carry__0_i_7_n_0;
  wire payload_legal1_carry__0_i_8_n_0;
  wire payload_legal1_carry__0_n_0;
  wire payload_legal1_carry__0_n_1;
  wire payload_legal1_carry__0_n_2;
  wire payload_legal1_carry__0_n_3;
  wire payload_legal1_carry__1_i_1_n_0;
  wire payload_legal1_carry__1_i_2_n_0;
  wire payload_legal1_carry__1_i_3_n_0;
  wire payload_legal1_carry__1_i_4_n_0;
  wire payload_legal1_carry__1_i_5_n_0;
  wire payload_legal1_carry__1_i_6_n_0;
  wire payload_legal1_carry__1_i_7_n_0;
  wire payload_legal1_carry__1_i_8_n_0;
  wire payload_legal1_carry__1_n_0;
  wire payload_legal1_carry__1_n_1;
  wire payload_legal1_carry__1_n_2;
  wire payload_legal1_carry__1_n_3;
  wire payload_legal1_carry__2_i_1_n_0;
  wire payload_legal1_carry__2_i_2_n_0;
  wire payload_legal1_carry__2_i_3_n_0;
  wire payload_legal1_carry__2_i_4_n_0;
  wire payload_legal1_carry__2_i_5_n_0;
  wire payload_legal1_carry__2_i_6_n_0;
  wire payload_legal1_carry__2_i_7_n_0;
  wire payload_legal1_carry__2_i_8_n_0;
  wire payload_legal1_carry__2_n_1;
  wire payload_legal1_carry__2_n_2;
  wire payload_legal1_carry__2_n_3;
  wire payload_legal1_carry_i_1_n_0;
  wire payload_legal1_carry_i_2_n_0;
  wire payload_legal1_carry_i_3_n_0;
  wire payload_legal1_carry_i_4_n_0;
  wire payload_legal1_carry_i_5_n_0;
  wire payload_legal1_carry_i_6_n_0;
  wire payload_legal1_carry_i_7_n_0;
  wire payload_legal1_carry_i_8_n_0;
  wire payload_legal1_carry_n_0;
  wire payload_legal1_carry_n_1;
  wire payload_legal1_carry_n_2;
  wire payload_legal1_carry_n_3;
  wire payload_legal2__15;
  wire payload_legal2_carry__0_i_1_n_0;
  wire payload_legal2_carry__0_i_2_n_0;
  wire payload_legal2_carry__0_i_3_n_0;
  wire payload_legal2_carry__0_i_4_n_0;
  wire payload_legal2_carry__0_i_5_n_0;
  wire payload_legal2_carry__0_i_6_n_0;
  wire payload_legal2_carry__0_i_7_n_0;
  wire payload_legal2_carry__0_i_8_n_0;
  wire payload_legal2_carry__0_n_0;
  wire payload_legal2_carry__0_n_1;
  wire payload_legal2_carry__0_n_2;
  wire payload_legal2_carry__0_n_3;
  wire payload_legal2_carry__1_i_1_n_0;
  wire payload_legal2_carry__1_i_2_n_0;
  wire payload_legal2_carry__1_i_3_n_0;
  wire payload_legal2_carry__1_i_4_n_0;
  wire payload_legal2_carry__1_i_5_n_0;
  wire payload_legal2_carry__1_i_6_n_0;
  wire payload_legal2_carry__1_i_7_n_0;
  wire payload_legal2_carry__1_i_8_n_0;
  wire payload_legal2_carry__1_n_0;
  wire payload_legal2_carry__1_n_1;
  wire payload_legal2_carry__1_n_2;
  wire payload_legal2_carry__1_n_3;
  wire payload_legal2_carry__2_i_1_n_0;
  wire payload_legal2_carry__2_i_2_n_0;
  wire payload_legal2_carry__2_i_3_n_0;
  wire payload_legal2_carry__2_i_4_n_0;
  wire payload_legal2_carry__2_i_5_n_0;
  wire payload_legal2_carry__2_i_6_n_0;
  wire payload_legal2_carry__2_i_7_n_0;
  wire payload_legal2_carry__2_i_8_n_0;
  wire payload_legal2_carry__2_n_1;
  wire payload_legal2_carry__2_n_2;
  wire payload_legal2_carry__2_n_3;
  wire payload_legal2_carry_i_1_n_0;
  wire payload_legal2_carry_i_2_n_0;
  wire payload_legal2_carry_i_3_n_0;
  wire payload_legal2_carry_i_4_n_0;
  wire payload_legal2_carry_i_5_n_0;
  wire payload_legal2_carry_i_6_n_0;
  wire payload_legal2_carry_i_7_n_0;
  wire payload_legal2_carry_i_8_n_0;
  wire payload_legal2_carry_n_0;
  wire payload_legal2_carry_n_1;
  wire payload_legal2_carry_n_2;
  wire payload_legal2_carry_n_3;
  wire [31:0]pending_high_pitch_q;
  wire [31:0]pending_high_speed_q;
  wire [31:0]pending_high_yaw_q;
  wire \pending_period_q_reg_n_0_[0] ;
  wire \pending_period_q_reg_n_0_[10] ;
  wire \pending_period_q_reg_n_0_[11] ;
  wire \pending_period_q_reg_n_0_[12] ;
  wire \pending_period_q_reg_n_0_[13] ;
  wire \pending_period_q_reg_n_0_[14] ;
  wire \pending_period_q_reg_n_0_[15] ;
  wire \pending_period_q_reg_n_0_[16] ;
  wire \pending_period_q_reg_n_0_[17] ;
  wire \pending_period_q_reg_n_0_[18] ;
  wire \pending_period_q_reg_n_0_[19] ;
  wire \pending_period_q_reg_n_0_[1] ;
  wire \pending_period_q_reg_n_0_[20] ;
  wire \pending_period_q_reg_n_0_[21] ;
  wire \pending_period_q_reg_n_0_[22] ;
  wire \pending_period_q_reg_n_0_[23] ;
  wire \pending_period_q_reg_n_0_[24] ;
  wire \pending_period_q_reg_n_0_[25] ;
  wire \pending_period_q_reg_n_0_[26] ;
  wire \pending_period_q_reg_n_0_[27] ;
  wire \pending_period_q_reg_n_0_[28] ;
  wire \pending_period_q_reg_n_0_[29] ;
  wire \pending_period_q_reg_n_0_[2] ;
  wire \pending_period_q_reg_n_0_[30] ;
  wire \pending_period_q_reg_n_0_[31] ;
  wire \pending_period_q_reg_n_0_[3] ;
  wire \pending_period_q_reg_n_0_[4] ;
  wire \pending_period_q_reg_n_0_[5] ;
  wire \pending_period_q_reg_n_0_[6] ;
  wire \pending_period_q_reg_n_0_[7] ;
  wire \pending_period_q_reg_n_0_[8] ;
  wire \pending_period_q_reg_n_0_[9] ;
  wire pending_q_i_1_n_0;
  wire pending_q_reg_0;
  wire [0:0]pending_tag_q;
  wire \pending_tag_q_reg_n_0_[0] ;
  wire \pending_tag_q_reg_n_0_[10] ;
  wire \pending_tag_q_reg_n_0_[11] ;
  wire \pending_tag_q_reg_n_0_[12] ;
  wire \pending_tag_q_reg_n_0_[13] ;
  wire \pending_tag_q_reg_n_0_[14] ;
  wire \pending_tag_q_reg_n_0_[15] ;
  wire \pending_tag_q_reg_n_0_[16] ;
  wire \pending_tag_q_reg_n_0_[17] ;
  wire \pending_tag_q_reg_n_0_[18] ;
  wire \pending_tag_q_reg_n_0_[19] ;
  wire \pending_tag_q_reg_n_0_[1] ;
  wire \pending_tag_q_reg_n_0_[20] ;
  wire \pending_tag_q_reg_n_0_[21] ;
  wire \pending_tag_q_reg_n_0_[22] ;
  wire \pending_tag_q_reg_n_0_[23] ;
  wire \pending_tag_q_reg_n_0_[24] ;
  wire \pending_tag_q_reg_n_0_[25] ;
  wire \pending_tag_q_reg_n_0_[26] ;
  wire \pending_tag_q_reg_n_0_[27] ;
  wire \pending_tag_q_reg_n_0_[28] ;
  wire \pending_tag_q_reg_n_0_[29] ;
  wire \pending_tag_q_reg_n_0_[2] ;
  wire \pending_tag_q_reg_n_0_[30] ;
  wire \pending_tag_q_reg_n_0_[31] ;
  wire \pending_tag_q_reg_n_0_[3] ;
  wire \pending_tag_q_reg_n_0_[4] ;
  wire \pending_tag_q_reg_n_0_[5] ;
  wire \pending_tag_q_reg_n_0_[6] ;
  wire \pending_tag_q_reg_n_0_[7] ;
  wire \pending_tag_q_reg_n_0_[8] ;
  wire \pending_tag_q_reg_n_0_[9] ;
  wire \phase_q[0]_i_1_n_0 ;
  wire \phase_q[0]_i_3_n_0 ;
  wire [31:0]phase_q_reg;
  wire \phase_q_reg[0]_i_2_n_0 ;
  wire \phase_q_reg[0]_i_2_n_1 ;
  wire \phase_q_reg[0]_i_2_n_2 ;
  wire \phase_q_reg[0]_i_2_n_3 ;
  wire \phase_q_reg[0]_i_2_n_4 ;
  wire \phase_q_reg[0]_i_2_n_5 ;
  wire \phase_q_reg[0]_i_2_n_6 ;
  wire \phase_q_reg[0]_i_2_n_7 ;
  wire \phase_q_reg[12]_i_1_n_0 ;
  wire \phase_q_reg[12]_i_1_n_1 ;
  wire \phase_q_reg[12]_i_1_n_2 ;
  wire \phase_q_reg[12]_i_1_n_3 ;
  wire \phase_q_reg[12]_i_1_n_4 ;
  wire \phase_q_reg[12]_i_1_n_5 ;
  wire \phase_q_reg[12]_i_1_n_6 ;
  wire \phase_q_reg[12]_i_1_n_7 ;
  wire \phase_q_reg[16]_i_1_n_0 ;
  wire \phase_q_reg[16]_i_1_n_1 ;
  wire \phase_q_reg[16]_i_1_n_2 ;
  wire \phase_q_reg[16]_i_1_n_3 ;
  wire \phase_q_reg[16]_i_1_n_4 ;
  wire \phase_q_reg[16]_i_1_n_5 ;
  wire \phase_q_reg[16]_i_1_n_6 ;
  wire \phase_q_reg[16]_i_1_n_7 ;
  wire \phase_q_reg[20]_i_1_n_0 ;
  wire \phase_q_reg[20]_i_1_n_1 ;
  wire \phase_q_reg[20]_i_1_n_2 ;
  wire \phase_q_reg[20]_i_1_n_3 ;
  wire \phase_q_reg[20]_i_1_n_4 ;
  wire \phase_q_reg[20]_i_1_n_5 ;
  wire \phase_q_reg[20]_i_1_n_6 ;
  wire \phase_q_reg[20]_i_1_n_7 ;
  wire \phase_q_reg[24]_i_1_n_0 ;
  wire \phase_q_reg[24]_i_1_n_1 ;
  wire \phase_q_reg[24]_i_1_n_2 ;
  wire \phase_q_reg[24]_i_1_n_3 ;
  wire \phase_q_reg[24]_i_1_n_4 ;
  wire \phase_q_reg[24]_i_1_n_5 ;
  wire \phase_q_reg[24]_i_1_n_6 ;
  wire \phase_q_reg[24]_i_1_n_7 ;
  wire \phase_q_reg[28]_i_1_n_1 ;
  wire \phase_q_reg[28]_i_1_n_2 ;
  wire \phase_q_reg[28]_i_1_n_3 ;
  wire \phase_q_reg[28]_i_1_n_4 ;
  wire \phase_q_reg[28]_i_1_n_5 ;
  wire \phase_q_reg[28]_i_1_n_6 ;
  wire \phase_q_reg[28]_i_1_n_7 ;
  wire \phase_q_reg[4]_i_1_n_0 ;
  wire \phase_q_reg[4]_i_1_n_1 ;
  wire \phase_q_reg[4]_i_1_n_2 ;
  wire \phase_q_reg[4]_i_1_n_3 ;
  wire \phase_q_reg[4]_i_1_n_4 ;
  wire \phase_q_reg[4]_i_1_n_5 ;
  wire \phase_q_reg[4]_i_1_n_6 ;
  wire \phase_q_reg[4]_i_1_n_7 ;
  wire \phase_q_reg[8]_i_1_n_0 ;
  wire \phase_q_reg[8]_i_1_n_1 ;
  wire \phase_q_reg[8]_i_1_n_2 ;
  wire \phase_q_reg[8]_i_1_n_3 ;
  wire \phase_q_reg[8]_i_1_n_4 ;
  wire \phase_q_reg[8]_i_1_n_5 ;
  wire \phase_q_reg[8]_i_1_n_6 ;
  wire \phase_q_reg[8]_i_1_n_7 ;
  wire [2:0]pwm;
  wire pwm_q0_carry__0_i_1_n_0;
  wire pwm_q0_carry__0_i_2_n_0;
  wire pwm_q0_carry__0_i_3_n_0;
  wire pwm_q0_carry__0_i_4_n_0;
  wire pwm_q0_carry__0_i_5_n_0;
  wire pwm_q0_carry__0_i_6_n_0;
  wire pwm_q0_carry__0_i_7_n_0;
  wire pwm_q0_carry__0_i_8_n_0;
  wire pwm_q0_carry__0_n_0;
  wire pwm_q0_carry__0_n_1;
  wire pwm_q0_carry__0_n_2;
  wire pwm_q0_carry__0_n_3;
  wire pwm_q0_carry__1_i_1_n_0;
  wire pwm_q0_carry__1_i_2_n_0;
  wire pwm_q0_carry__1_i_3_n_0;
  wire pwm_q0_carry__1_i_4_n_0;
  wire pwm_q0_carry__1_i_5_n_0;
  wire pwm_q0_carry__1_i_6_n_0;
  wire pwm_q0_carry__1_i_7_n_0;
  wire pwm_q0_carry__1_i_8_n_0;
  wire pwm_q0_carry__1_n_0;
  wire pwm_q0_carry__1_n_1;
  wire pwm_q0_carry__1_n_2;
  wire pwm_q0_carry__1_n_3;
  wire pwm_q0_carry__2_i_1_n_0;
  wire pwm_q0_carry__2_i_2_n_0;
  wire pwm_q0_carry__2_i_3_n_0;
  wire pwm_q0_carry__2_i_4_n_0;
  wire pwm_q0_carry__2_i_5_n_0;
  wire pwm_q0_carry__2_i_6_n_0;
  wire pwm_q0_carry__2_i_7_n_0;
  wire pwm_q0_carry__2_i_8_n_0;
  wire pwm_q0_carry__2_n_1;
  wire pwm_q0_carry__2_n_2;
  wire pwm_q0_carry__2_n_3;
  wire pwm_q0_carry_i_1_n_0;
  wire pwm_q0_carry_i_2_n_0;
  wire pwm_q0_carry_i_3_n_0;
  wire pwm_q0_carry_i_4_n_0;
  wire pwm_q0_carry_i_5_n_0;
  wire pwm_q0_carry_i_6_n_0;
  wire pwm_q0_carry_i_7_n_0;
  wire pwm_q0_carry_i_8_n_0;
  wire pwm_q0_carry_n_0;
  wire pwm_q0_carry_n_1;
  wire pwm_q0_carry_n_2;
  wire pwm_q0_carry_n_3;
  wire \pwm_q0_inferred__0/i__carry__0_n_0 ;
  wire \pwm_q0_inferred__0/i__carry__0_n_1 ;
  wire \pwm_q0_inferred__0/i__carry__0_n_2 ;
  wire \pwm_q0_inferred__0/i__carry__0_n_3 ;
  wire \pwm_q0_inferred__0/i__carry__1_n_0 ;
  wire \pwm_q0_inferred__0/i__carry__1_n_1 ;
  wire \pwm_q0_inferred__0/i__carry__1_n_2 ;
  wire \pwm_q0_inferred__0/i__carry__1_n_3 ;
  wire \pwm_q0_inferred__0/i__carry__2_n_1 ;
  wire \pwm_q0_inferred__0/i__carry__2_n_2 ;
  wire \pwm_q0_inferred__0/i__carry__2_n_3 ;
  wire \pwm_q0_inferred__0/i__carry_n_0 ;
  wire \pwm_q0_inferred__0/i__carry_n_1 ;
  wire \pwm_q0_inferred__0/i__carry_n_2 ;
  wire \pwm_q0_inferred__0/i__carry_n_3 ;
  wire \pwm_q0_inferred__1/i__carry__0_n_0 ;
  wire \pwm_q0_inferred__1/i__carry__0_n_1 ;
  wire \pwm_q0_inferred__1/i__carry__0_n_2 ;
  wire \pwm_q0_inferred__1/i__carry__0_n_3 ;
  wire \pwm_q0_inferred__1/i__carry__1_n_0 ;
  wire \pwm_q0_inferred__1/i__carry__1_n_1 ;
  wire \pwm_q0_inferred__1/i__carry__1_n_2 ;
  wire \pwm_q0_inferred__1/i__carry__1_n_3 ;
  wire \pwm_q0_inferred__1/i__carry__2_n_1 ;
  wire \pwm_q0_inferred__1/i__carry__2_n_2 ;
  wire \pwm_q0_inferred__1/i__carry__2_n_3 ;
  wire \pwm_q0_inferred__1/i__carry_n_0 ;
  wire \pwm_q0_inferred__1/i__carry_n_1 ;
  wire \pwm_q0_inferred__1/i__carry_n_2 ;
  wire \pwm_q0_inferred__1/i__carry_n_3 ;
  wire \pwm_q[0]_i_10_n_0 ;
  wire \pwm_q[0]_i_1_n_0 ;
  wire \pwm_q[0]_i_2_n_0 ;
  wire \pwm_q[0]_i_3_n_0 ;
  wire \pwm_q[0]_i_4_n_0 ;
  wire \pwm_q[0]_i_5_n_0 ;
  wire \pwm_q[0]_i_6_n_0 ;
  wire \pwm_q[0]_i_7_n_0 ;
  wire \pwm_q[0]_i_8_n_0 ;
  wire \pwm_q[0]_i_9_n_0 ;
  wire \pwm_q[1]_i_10_n_0 ;
  wire \pwm_q[1]_i_1_n_0 ;
  wire \pwm_q[1]_i_2_n_0 ;
  wire \pwm_q[1]_i_3_n_0 ;
  wire \pwm_q[1]_i_4_n_0 ;
  wire \pwm_q[1]_i_5_n_0 ;
  wire \pwm_q[1]_i_6_n_0 ;
  wire \pwm_q[1]_i_7_n_0 ;
  wire \pwm_q[1]_i_8_n_0 ;
  wire \pwm_q[1]_i_9_n_0 ;
  wire \pwm_q[2]_i_10_n_0 ;
  wire \pwm_q[2]_i_11_n_0 ;
  wire \pwm_q[2]_i_1_n_0 ;
  wire \pwm_q[2]_i_2_n_0 ;
  wire \pwm_q[2]_i_3_n_0 ;
  wire \pwm_q[2]_i_4_n_0 ;
  wire \pwm_q[2]_i_5_n_0 ;
  wire \pwm_q[2]_i_6_n_0 ;
  wire \pwm_q[2]_i_7_n_0 ;
  wire \pwm_q[2]_i_8_n_0 ;
  wire \pwm_q[2]_i_9_n_0 ;
  wire [0:0]raw_fault_events;
  wire rejected;
  wire rejected_q;
  wire rejected_q_i_1_n_0;
  wire rst;
  wire rst_0;
  wire running_q_reg_0;
  wire stop;
  wire stop_0;
  wire stop_1;
  wire window_active_q_i_100_n_0;
  wire window_active_q_i_101_n_0;
  wire window_active_q_i_102_n_0;
  wire window_active_q_i_103_n_0;
  wire window_active_q_i_104_n_0;
  wire window_active_q_i_105_n_0;
  wire window_active_q_i_106_n_0;
  wire window_active_q_i_107_n_0;
  wire window_active_q_i_109_n_0;
  wire window_active_q_i_10_n_0;
  wire window_active_q_i_110_n_0;
  wire window_active_q_i_111_n_0;
  wire window_active_q_i_112_n_0;
  wire window_active_q_i_113_n_0;
  wire window_active_q_i_114_n_0;
  wire window_active_q_i_115_n_0;
  wire window_active_q_i_116_n_0;
  wire window_active_q_i_118_n_0;
  wire window_active_q_i_119_n_0;
  wire window_active_q_i_120_n_0;
  wire window_active_q_i_121_n_0;
  wire window_active_q_i_122_n_0;
  wire window_active_q_i_123_n_0;
  wire window_active_q_i_124_n_0;
  wire window_active_q_i_125_n_0;
  wire window_active_q_i_126_n_0;
  wire window_active_q_i_127_n_0;
  wire window_active_q_i_128_n_0;
  wire window_active_q_i_129_n_0;
  wire window_active_q_i_130_n_0;
  wire window_active_q_i_131_n_0;
  wire window_active_q_i_132_n_0;
  wire window_active_q_i_133_n_0;
  wire window_active_q_i_134_n_0;
  wire window_active_q_i_135_n_0;
  wire window_active_q_i_136_n_0;
  wire window_active_q_i_137_n_0;
  wire window_active_q_i_138_n_0;
  wire window_active_q_i_139_n_0;
  wire window_active_q_i_140_n_0;
  wire window_active_q_i_141_n_0;
  wire window_active_q_i_142_n_0;
  wire window_active_q_i_143_n_0;
  wire window_active_q_i_144_n_0;
  wire window_active_q_i_145_n_0;
  wire window_active_q_i_146_n_0;
  wire window_active_q_i_147_n_0;
  wire window_active_q_i_148_n_0;
  wire window_active_q_i_149_n_0;
  wire window_active_q_i_15_n_0;
  wire window_active_q_i_16_n_0;
  wire window_active_q_i_17_n_0;
  wire window_active_q_i_18_n_0;
  wire window_active_q_i_19_n_0;
  wire window_active_q_i_20_n_0;
  wire window_active_q_i_21_n_0;
  wire window_active_q_i_22_n_0;
  wire window_active_q_i_23_n_0;
  wire window_active_q_i_24_n_0;
  wire window_active_q_i_25_n_0;
  wire window_active_q_i_26_n_0;
  wire window_active_q_i_27_n_0;
  wire window_active_q_i_28_n_0;
  wire window_active_q_i_29_n_0;
  wire window_active_q_i_30_n_0;
  wire window_active_q_i_31_n_0;
  wire window_active_q_i_33_n_0;
  wire window_active_q_i_34_n_0;
  wire window_active_q_i_35_n_0;
  wire window_active_q_i_36_n_0;
  wire window_active_q_i_37_n_0;
  wire window_active_q_i_38_n_0;
  wire window_active_q_i_39_n_0;
  wire window_active_q_i_40_n_0;
  wire window_active_q_i_42_n_0;
  wire window_active_q_i_43_n_0;
  wire window_active_q_i_44_n_0;
  wire window_active_q_i_45_n_0;
  wire window_active_q_i_46_n_0;
  wire window_active_q_i_47_n_0;
  wire window_active_q_i_48_n_0;
  wire window_active_q_i_49_n_0;
  wire window_active_q_i_51_n_0;
  wire window_active_q_i_52_n_0;
  wire window_active_q_i_53_n_0;
  wire window_active_q_i_54_n_0;
  wire window_active_q_i_55_n_0;
  wire window_active_q_i_56_n_0;
  wire window_active_q_i_57_n_0;
  wire window_active_q_i_58_n_0;
  wire window_active_q_i_59_n_0;
  wire window_active_q_i_5_n_0;
  wire window_active_q_i_60_n_0;
  wire window_active_q_i_61_n_0;
  wire window_active_q_i_62_n_0;
  wire window_active_q_i_63_n_0;
  wire window_active_q_i_64_n_0;
  wire window_active_q_i_65_n_0;
  wire window_active_q_i_66_n_0;
  wire window_active_q_i_67_n_0;
  wire window_active_q_i_68_n_0;
  wire window_active_q_i_69_n_0;
  wire window_active_q_i_6_n_0;
  wire window_active_q_i_70_n_0;
  wire window_active_q_i_71_n_0;
  wire window_active_q_i_73_n_0;
  wire window_active_q_i_74_n_0;
  wire window_active_q_i_75_n_0;
  wire window_active_q_i_76_n_0;
  wire window_active_q_i_77_n_0;
  wire window_active_q_i_78_n_0;
  wire window_active_q_i_79_n_0;
  wire window_active_q_i_7_n_0;
  wire window_active_q_i_80_n_0;
  wire window_active_q_i_82_n_0;
  wire window_active_q_i_83_n_0;
  wire window_active_q_i_84_n_0;
  wire window_active_q_i_85_n_0;
  wire window_active_q_i_86_n_0;
  wire window_active_q_i_87_n_0;
  wire window_active_q_i_88_n_0;
  wire window_active_q_i_89_n_0;
  wire window_active_q_i_8_n_0;
  wire window_active_q_i_91_n_0;
  wire window_active_q_i_92_n_0;
  wire window_active_q_i_93_n_0;
  wire window_active_q_i_94_n_0;
  wire window_active_q_i_95_n_0;
  wire window_active_q_i_96_n_0;
  wire window_active_q_i_97_n_0;
  wire window_active_q_i_98_n_0;
  wire window_active_q_i_9_n_0;
  wire window_active_q_reg;
  wire window_active_q_reg_0;
  wire window_active_q_reg_i_108_n_0;
  wire window_active_q_reg_i_108_n_1;
  wire window_active_q_reg_i_108_n_2;
  wire window_active_q_reg_i_108_n_3;
  wire window_active_q_reg_i_117_n_0;
  wire window_active_q_reg_i_117_n_1;
  wire window_active_q_reg_i_117_n_2;
  wire window_active_q_reg_i_117_n_3;
  wire window_active_q_reg_i_12_n_1;
  wire window_active_q_reg_i_12_n_2;
  wire window_active_q_reg_i_12_n_3;
  wire window_active_q_reg_i_13_n_1;
  wire window_active_q_reg_i_13_n_2;
  wire window_active_q_reg_i_13_n_3;
  wire window_active_q_reg_i_14_n_1;
  wire window_active_q_reg_i_14_n_2;
  wire window_active_q_reg_i_14_n_3;
  wire window_active_q_reg_i_32_n_0;
  wire window_active_q_reg_i_32_n_1;
  wire window_active_q_reg_i_32_n_2;
  wire window_active_q_reg_i_32_n_3;
  wire window_active_q_reg_i_41_n_0;
  wire window_active_q_reg_i_41_n_1;
  wire window_active_q_reg_i_41_n_2;
  wire window_active_q_reg_i_41_n_3;
  wire window_active_q_reg_i_50_n_0;
  wire window_active_q_reg_i_50_n_1;
  wire window_active_q_reg_i_50_n_2;
  wire window_active_q_reg_i_50_n_3;
  wire window_active_q_reg_i_72_n_0;
  wire window_active_q_reg_i_72_n_1;
  wire window_active_q_reg_i_72_n_2;
  wire window_active_q_reg_i_72_n_3;
  wire window_active_q_reg_i_81_n_0;
  wire window_active_q_reg_i_81_n_1;
  wire window_active_q_reg_i_81_n_2;
  wire window_active_q_reg_i_81_n_3;
  wire window_active_q_reg_i_90_n_0;
  wire window_active_q_reg_i_90_n_1;
  wire window_active_q_reg_i_90_n_2;
  wire window_active_q_reg_i_90_n_3;
  wire window_active_q_reg_i_99_n_0;
  wire window_active_q_reg_i_99_n_1;
  wire window_active_q_reg_i_99_n_2;
  wire window_active_q_reg_i_99_n_3;
  wire [3:0]NLW_boundary_now0_carry_O_UNCONNECTED;
  wire [3:0]NLW_boundary_now0_carry__0_O_UNCONNECTED;
  wire [3:3]NLW_boundary_now0_carry__1_CO_UNCONNECTED;
  wire [3:0]NLW_boundary_now0_carry__1_O_UNCONNECTED;
  wire [3:2]NLW_boundary_now0_carry__1_i_4_CO_UNCONNECTED;
  wire [3:3]NLW_boundary_now0_carry__1_i_4_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal0_carry_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal0_carry__0_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal0_carry__1_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal0_carry__2_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal1_carry_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal1_carry__0_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal1_carry__1_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal1_carry__2_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal2_carry_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal2_carry__0_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal2_carry__1_O_UNCONNECTED;
  wire [3:0]NLW_payload_legal2_carry__2_O_UNCONNECTED;
  wire [3:3]\NLW_phase_q_reg[28]_i_1_CO_UNCONNECTED ;
  wire [3:0]NLW_pwm_q0_carry_O_UNCONNECTED;
  wire [3:0]NLW_pwm_q0_carry__0_O_UNCONNECTED;
  wire [3:0]NLW_pwm_q0_carry__1_O_UNCONNECTED;
  wire [3:0]NLW_pwm_q0_carry__2_O_UNCONNECTED;
  wire [3:0]\NLW_pwm_q0_inferred__0/i__carry_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__0/i__carry__0_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__0/i__carry__1_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__0/i__carry__2_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__1/i__carry_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__1/i__carry__0_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__1/i__carry__1_O_UNCONNECTED ;
  wire [3:0]\NLW_pwm_q0_inferred__1/i__carry__2_O_UNCONNECTED ;
  wire [3:0]NLW_window_active_q_reg_i_108_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_117_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_12_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_13_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_14_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_32_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_41_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_50_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_72_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_81_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_90_O_UNCONNECTED;
  wire [3:0]NLW_window_active_q_reg_i_99_O_UNCONNECTED;

  LUT6 #(
    .INIT(64'hE000000000000000)) 
    accepted_q_i_1
       (.I0(accepted_q_i_2_n_0),
        .I1(accepted_q_i_3_n_0),
        .I2(payload_legal1__15),
        .I3(payload_legal0__15),
        .I4(payload_legal2__15),
        .I5(accepted_q_i_4_n_0),
        .O(rejected_q));
  LUT4 #(
    .INIT(16'hFFFE)) 
    accepted_q_i_10
       (.I0(cfg_period[22]),
        .I1(cfg_period[21]),
        .I2(cfg_period[23]),
        .I3(cfg_period[20]),
        .O(accepted_q_i_10_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    accepted_q_i_2
       (.I0(accepted_q_i_5_n_0),
        .I1(cfg_period[15]),
        .I2(cfg_period[14]),
        .I3(cfg_period[13]),
        .I4(cfg_period[12]),
        .I5(accepted_q_i_6_n_0),
        .O(accepted_q_i_2_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    accepted_q_i_3
       (.I0(accepted_q_i_7_n_0),
        .I1(cfg_period[26]),
        .I2(cfg_period[25]),
        .I3(cfg_period[27]),
        .I4(cfg_period[24]),
        .I5(accepted_q_i_8_n_0),
        .O(accepted_q_i_3_n_0));
  (* SOFT_HLUTNM = "soft_lutpair23" *) 
  LUT4 #(
    .INIT(16'h0010)) 
    accepted_q_i_4
       (.I0(stop),
        .I1(rst),
        .I2(cfg_valid),
        .I3(pending_q_reg_0),
        .O(accepted_q_i_4_n_0));
  LUT4 #(
    .INIT(16'hFFFE)) 
    accepted_q_i_5
       (.I0(cfg_period[9]),
        .I1(cfg_period[8]),
        .I2(cfg_period[11]),
        .I3(cfg_period[10]),
        .O(accepted_q_i_5_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    accepted_q_i_6
       (.I0(cfg_period[2]),
        .I1(cfg_period[3]),
        .I2(cfg_period[0]),
        .I3(cfg_period[1]),
        .I4(accepted_q_i_9_n_0),
        .O(accepted_q_i_6_n_0));
  LUT4 #(
    .INIT(16'hFFFE)) 
    accepted_q_i_7
       (.I0(cfg_period[29]),
        .I1(cfg_period[28]),
        .I2(cfg_period[31]),
        .I3(cfg_period[30]),
        .O(accepted_q_i_7_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    accepted_q_i_8
       (.I0(cfg_period[17]),
        .I1(cfg_period[18]),
        .I2(cfg_period[16]),
        .I3(cfg_period[19]),
        .I4(accepted_q_i_10_n_0),
        .O(accepted_q_i_8_n_0));
  LUT4 #(
    .INIT(16'hFFFE)) 
    accepted_q_i_9
       (.I0(cfg_period[5]),
        .I1(cfg_period[4]),
        .I2(cfg_period[7]),
        .I3(cfg_period[6]),
        .O(accepted_q_i_9_n_0));
  FDRE accepted_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(rejected_q),
        .Q(accepted),
        .R(1'b0));
  FDRE \active_high_pitch_q_reg[0] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[0]),
        .Q(\active_high_pitch_q_reg[31]_0 [0]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[10] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[10]),
        .Q(\active_high_pitch_q_reg[31]_0 [10]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[11] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[11]),
        .Q(\active_high_pitch_q_reg[31]_0 [11]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[12] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[12]),
        .Q(\active_high_pitch_q_reg[31]_0 [12]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[13] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[13]),
        .Q(\active_high_pitch_q_reg[31]_0 [13]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[14] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[14]),
        .Q(\active_high_pitch_q_reg[31]_0 [14]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[15] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[15]),
        .Q(\active_high_pitch_q_reg[31]_0 [15]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[16] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[16]),
        .Q(\active_high_pitch_q_reg[31]_0 [16]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[17] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[17]),
        .Q(\active_high_pitch_q_reg[31]_0 [17]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[18] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[18]),
        .Q(\active_high_pitch_q_reg[31]_0 [18]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[19] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[19]),
        .Q(\active_high_pitch_q_reg[31]_0 [19]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[1] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[1]),
        .Q(\active_high_pitch_q_reg[31]_0 [1]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[20] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[20]),
        .Q(\active_high_pitch_q_reg[31]_0 [20]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[21] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[21]),
        .Q(\active_high_pitch_q_reg[31]_0 [21]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[22] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[22]),
        .Q(\active_high_pitch_q_reg[31]_0 [22]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[23] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[23]),
        .Q(\active_high_pitch_q_reg[31]_0 [23]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[24] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[24]),
        .Q(\active_high_pitch_q_reg[31]_0 [24]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[25] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[25]),
        .Q(\active_high_pitch_q_reg[31]_0 [25]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[26] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[26]),
        .Q(\active_high_pitch_q_reg[31]_0 [26]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[27] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[27]),
        .Q(\active_high_pitch_q_reg[31]_0 [27]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[28] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[28]),
        .Q(\active_high_pitch_q_reg[31]_0 [28]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[29] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[29]),
        .Q(\active_high_pitch_q_reg[31]_0 [29]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[2] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[2]),
        .Q(\active_high_pitch_q_reg[31]_0 [2]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[30] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[30]),
        .Q(\active_high_pitch_q_reg[31]_0 [30]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[31] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[31]),
        .Q(\active_high_pitch_q_reg[31]_0 [31]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[3] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[3]),
        .Q(\active_high_pitch_q_reg[31]_0 [3]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[4] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[4]),
        .Q(\active_high_pitch_q_reg[31]_0 [4]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[5] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[5]),
        .Q(\active_high_pitch_q_reg[31]_0 [5]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[6] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[6]),
        .Q(\active_high_pitch_q_reg[31]_0 [6]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[7] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[7]),
        .Q(\active_high_pitch_q_reg[31]_0 [7]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[8] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[8]),
        .Q(\active_high_pitch_q_reg[31]_0 [8]),
        .R(accepted_q1));
  FDRE \active_high_pitch_q_reg[9] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_pitch_q[9]),
        .Q(\active_high_pitch_q_reg[31]_0 [9]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[0] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[0]),
        .Q(\active_high_speed_q_reg[31]_0 [0]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[10] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[10]),
        .Q(\active_high_speed_q_reg[31]_0 [10]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[11] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[11]),
        .Q(\active_high_speed_q_reg[31]_0 [11]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[12] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[12]),
        .Q(\active_high_speed_q_reg[31]_0 [12]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[13] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[13]),
        .Q(\active_high_speed_q_reg[31]_0 [13]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[14] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[14]),
        .Q(\active_high_speed_q_reg[31]_0 [14]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[15] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[15]),
        .Q(\active_high_speed_q_reg[31]_0 [15]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[16] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[16]),
        .Q(\active_high_speed_q_reg[31]_0 [16]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[17] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[17]),
        .Q(\active_high_speed_q_reg[31]_0 [17]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[18] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[18]),
        .Q(\active_high_speed_q_reg[31]_0 [18]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[19] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[19]),
        .Q(\active_high_speed_q_reg[31]_0 [19]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[1] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[1]),
        .Q(\active_high_speed_q_reg[31]_0 [1]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[20] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[20]),
        .Q(\active_high_speed_q_reg[31]_0 [20]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[21] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[21]),
        .Q(\active_high_speed_q_reg[31]_0 [21]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[22] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[22]),
        .Q(\active_high_speed_q_reg[31]_0 [22]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[23] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[23]),
        .Q(\active_high_speed_q_reg[31]_0 [23]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[24] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[24]),
        .Q(\active_high_speed_q_reg[31]_0 [24]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[25] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[25]),
        .Q(\active_high_speed_q_reg[31]_0 [25]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[26] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[26]),
        .Q(\active_high_speed_q_reg[31]_0 [26]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[27] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[27]),
        .Q(\active_high_speed_q_reg[31]_0 [27]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[28] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[28]),
        .Q(\active_high_speed_q_reg[31]_0 [28]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[29] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[29]),
        .Q(\active_high_speed_q_reg[31]_0 [29]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[2] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[2]),
        .Q(\active_high_speed_q_reg[31]_0 [2]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[30] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[30]),
        .Q(\active_high_speed_q_reg[31]_0 [30]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[31] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[31]),
        .Q(\active_high_speed_q_reg[31]_0 [31]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[3] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[3]),
        .Q(\active_high_speed_q_reg[31]_0 [3]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[4] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[4]),
        .Q(\active_high_speed_q_reg[31]_0 [4]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[5] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[5]),
        .Q(\active_high_speed_q_reg[31]_0 [5]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[6] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[6]),
        .Q(\active_high_speed_q_reg[31]_0 [6]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[7] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[7]),
        .Q(\active_high_speed_q_reg[31]_0 [7]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[8] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[8]),
        .Q(\active_high_speed_q_reg[31]_0 [8]),
        .R(accepted_q1));
  FDRE \active_high_speed_q_reg[9] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_speed_q[9]),
        .Q(\active_high_speed_q_reg[31]_0 [9]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[0] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[0]),
        .Q(\active_high_yaw_q_reg[31]_0 [0]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[10] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[10]),
        .Q(\active_high_yaw_q_reg[31]_0 [10]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[11] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[11]),
        .Q(\active_high_yaw_q_reg[31]_0 [11]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[12] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[12]),
        .Q(\active_high_yaw_q_reg[31]_0 [12]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[13] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[13]),
        .Q(\active_high_yaw_q_reg[31]_0 [13]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[14] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[14]),
        .Q(\active_high_yaw_q_reg[31]_0 [14]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[15] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[15]),
        .Q(\active_high_yaw_q_reg[31]_0 [15]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[16] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[16]),
        .Q(\active_high_yaw_q_reg[31]_0 [16]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[17] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[17]),
        .Q(\active_high_yaw_q_reg[31]_0 [17]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[18] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[18]),
        .Q(\active_high_yaw_q_reg[31]_0 [18]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[19] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[19]),
        .Q(\active_high_yaw_q_reg[31]_0 [19]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[1] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[1]),
        .Q(\active_high_yaw_q_reg[31]_0 [1]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[20] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[20]),
        .Q(\active_high_yaw_q_reg[31]_0 [20]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[21] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[21]),
        .Q(\active_high_yaw_q_reg[31]_0 [21]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[22] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[22]),
        .Q(\active_high_yaw_q_reg[31]_0 [22]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[23] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[23]),
        .Q(\active_high_yaw_q_reg[31]_0 [23]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[24] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[24]),
        .Q(\active_high_yaw_q_reg[31]_0 [24]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[25] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[25]),
        .Q(\active_high_yaw_q_reg[31]_0 [25]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[26] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[26]),
        .Q(\active_high_yaw_q_reg[31]_0 [26]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[27] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[27]),
        .Q(\active_high_yaw_q_reg[31]_0 [27]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[28] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[28]),
        .Q(\active_high_yaw_q_reg[31]_0 [28]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[29] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[29]),
        .Q(\active_high_yaw_q_reg[31]_0 [29]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[2] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[2]),
        .Q(\active_high_yaw_q_reg[31]_0 [2]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[30] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[30]),
        .Q(\active_high_yaw_q_reg[31]_0 [30]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[31] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[31]),
        .Q(\active_high_yaw_q_reg[31]_0 [31]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[3] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[3]),
        .Q(\active_high_yaw_q_reg[31]_0 [3]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[4] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[4]),
        .Q(\active_high_yaw_q_reg[31]_0 [4]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[5] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[5]),
        .Q(\active_high_yaw_q_reg[31]_0 [5]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[6] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[6]),
        .Q(\active_high_yaw_q_reg[31]_0 [6]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[7] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[7]),
        .Q(\active_high_yaw_q_reg[31]_0 [7]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[8] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[8]),
        .Q(\active_high_yaw_q_reg[31]_0 [8]),
        .R(accepted_q1));
  FDRE \active_high_yaw_q_reg[9] 
       (.C(clk),
        .CE(apply_now),
        .D(pending_high_yaw_q[9]),
        .Q(\active_high_yaw_q_reg[31]_0 [9]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[0] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[0] ),
        .Q(Q[0]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[10] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[10] ),
        .Q(Q[10]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[11] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[11] ),
        .Q(Q[11]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[12] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[12] ),
        .Q(Q[12]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[13] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[13] ),
        .Q(Q[13]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[14] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[14] ),
        .Q(Q[14]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[15] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[15] ),
        .Q(Q[15]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[16] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[16] ),
        .Q(Q[16]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[17] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[17] ),
        .Q(Q[17]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[18] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[18] ),
        .Q(Q[18]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[19] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[19] ),
        .Q(Q[19]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[1] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[1] ),
        .Q(Q[1]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[20] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[20] ),
        .Q(Q[20]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[21] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[21] ),
        .Q(Q[21]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[22] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[22] ),
        .Q(Q[22]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[23] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[23] ),
        .Q(Q[23]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[24] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[24] ),
        .Q(Q[24]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[25] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[25] ),
        .Q(Q[25]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[26] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[26] ),
        .Q(Q[26]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[27] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[27] ),
        .Q(Q[27]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[28] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[28] ),
        .Q(Q[28]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[29] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[29] ),
        .Q(Q[29]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[2] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[2] ),
        .Q(Q[2]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[30] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[30] ),
        .Q(Q[30]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[31] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[31] ),
        .Q(Q[31]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[3] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[3] ),
        .Q(Q[3]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[4] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[4] ),
        .Q(Q[4]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[5] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[5] ),
        .Q(Q[5]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[6] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[6] ),
        .Q(Q[6]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[7] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[7] ),
        .Q(Q[7]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[8] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[8] ),
        .Q(Q[8]),
        .R(accepted_q1));
  FDRE \active_period_q_reg[9] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_period_q_reg_n_0_[9] ),
        .Q(Q[9]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[0] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[0] ),
        .Q(active_tag[0]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[10] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[10] ),
        .Q(active_tag[10]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[11] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[11] ),
        .Q(active_tag[11]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[12] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[12] ),
        .Q(active_tag[12]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[13] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[13] ),
        .Q(active_tag[13]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[14] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[14] ),
        .Q(active_tag[14]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[15] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[15] ),
        .Q(active_tag[15]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[16] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[16] ),
        .Q(active_tag[16]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[17] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[17] ),
        .Q(active_tag[17]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[18] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[18] ),
        .Q(active_tag[18]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[19] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[19] ),
        .Q(active_tag[19]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[1] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[1] ),
        .Q(active_tag[1]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[20] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[20] ),
        .Q(active_tag[20]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[21] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[21] ),
        .Q(active_tag[21]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[22] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[22] ),
        .Q(active_tag[22]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[23] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[23] ),
        .Q(active_tag[23]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[24] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[24] ),
        .Q(active_tag[24]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[25] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[25] ),
        .Q(active_tag[25]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[26] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[26] ),
        .Q(active_tag[26]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[27] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[27] ),
        .Q(active_tag[27]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[28] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[28] ),
        .Q(active_tag[28]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[29] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[29] ),
        .Q(active_tag[29]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[2] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[2] ),
        .Q(active_tag[2]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[30] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[30] ),
        .Q(active_tag[30]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[31] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[31] ),
        .Q(active_tag[31]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[3] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[3] ),
        .Q(active_tag[3]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[4] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[4] ),
        .Q(active_tag[4]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[5] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[5] ),
        .Q(active_tag[5]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[6] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[6] ),
        .Q(active_tag[6]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[7] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[7] ),
        .Q(active_tag[7]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[8] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[8] ),
        .Q(active_tag[8]),
        .R(accepted_q1));
  FDRE \active_tag_q_reg[9] 
       (.C(clk),
        .CE(apply_now),
        .D(\pending_tag_q_reg_n_0_[9] ),
        .Q(active_tag[9]),
        .R(accepted_q1));
  (* SOFT_HLUTNM = "soft_lutpair24" *) 
  LUT3 #(
    .INIT(8'h10)) 
    applied_q_i_1
       (.I0(stop),
        .I1(rst),
        .I2(apply_now),
        .O(applied_q_i_1_n_0));
  FDRE applied_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(applied_q_i_1_n_0),
        .Q(applied_q_reg_0),
        .R(1'b0));
  CARRY4 boundary_now0_carry
       (.CI(1'b0),
        .CO({boundary_now0_carry_n_0,boundary_now0_carry_n_1,boundary_now0_carry_n_2,boundary_now0_carry_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_boundary_now0_carry_O_UNCONNECTED[3:0]),
        .S({boundary_now0_carry_i_1_n_0,boundary_now0_carry_i_2_n_0,boundary_now0_carry_i_3_n_0,boundary_now0_carry_i_4_n_0}));
  CARRY4 boundary_now0_carry__0
       (.CI(boundary_now0_carry_n_0),
        .CO({boundary_now0_carry__0_n_0,boundary_now0_carry__0_n_1,boundary_now0_carry__0_n_2,boundary_now0_carry__0_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_boundary_now0_carry__0_O_UNCONNECTED[3:0]),
        .S({boundary_now0_carry__0_i_1_n_0,boundary_now0_carry__0_i_2_n_0,boundary_now0_carry__0_i_3_n_0,boundary_now0_carry__0_i_4_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry__0_i_1
       (.I0(Q[23]),
        .I1(boundary_now0_carry__0_i_5_n_5),
        .I2(boundary_now0_carry__0_i_5_n_7),
        .I3(Q[21]),
        .I4(boundary_now0_carry__0_i_5_n_6),
        .I5(Q[22]),
        .O(boundary_now0_carry__0_i_1_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry__0_i_2
       (.I0(Q[20]),
        .I1(boundary_now0_carry__0_i_6_n_4),
        .I2(boundary_now0_carry__0_i_6_n_6),
        .I3(Q[18]),
        .I4(boundary_now0_carry__0_i_6_n_5),
        .I5(Q[19]),
        .O(boundary_now0_carry__0_i_2_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry__0_i_3
       (.I0(Q[17]),
        .I1(boundary_now0_carry__0_i_6_n_7),
        .I2(boundary_now0_carry__0_i_7_n_4),
        .I3(Q[16]),
        .I4(boundary_now0_carry__0_i_7_n_5),
        .I5(Q[15]),
        .O(boundary_now0_carry__0_i_3_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry__0_i_4
       (.I0(Q[14]),
        .I1(boundary_now0_carry__0_i_7_n_6),
        .I2(boundary_now0_carry_i_5_n_4),
        .I3(Q[12]),
        .I4(boundary_now0_carry__0_i_7_n_7),
        .I5(Q[13]),
        .O(boundary_now0_carry__0_i_4_n_0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry__0_i_5
       (.CI(boundary_now0_carry__0_i_6_n_0),
        .CO({boundary_now0_carry__0_i_5_n_0,boundary_now0_carry__0_i_5_n_1,boundary_now0_carry__0_i_5_n_2,boundary_now0_carry__0_i_5_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry__0_i_5_n_4,boundary_now0_carry__0_i_5_n_5,boundary_now0_carry__0_i_5_n_6,boundary_now0_carry__0_i_5_n_7}),
        .S(phase_q_reg[24:21]));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry__0_i_6
       (.CI(boundary_now0_carry__0_i_7_n_0),
        .CO({boundary_now0_carry__0_i_6_n_0,boundary_now0_carry__0_i_6_n_1,boundary_now0_carry__0_i_6_n_2,boundary_now0_carry__0_i_6_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry__0_i_6_n_4,boundary_now0_carry__0_i_6_n_5,boundary_now0_carry__0_i_6_n_6,boundary_now0_carry__0_i_6_n_7}),
        .S(phase_q_reg[20:17]));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry__0_i_7
       (.CI(boundary_now0_carry_i_5_n_0),
        .CO({boundary_now0_carry__0_i_7_n_0,boundary_now0_carry__0_i_7_n_1,boundary_now0_carry__0_i_7_n_2,boundary_now0_carry__0_i_7_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry__0_i_7_n_4,boundary_now0_carry__0_i_7_n_5,boundary_now0_carry__0_i_7_n_6,boundary_now0_carry__0_i_7_n_7}),
        .S(phase_q_reg[16:13]));
  CARRY4 boundary_now0_carry__1
       (.CI(boundary_now0_carry__0_n_0),
        .CO({NLW_boundary_now0_carry__1_CO_UNCONNECTED[3],boundary_now0__10,boundary_now0_carry__1_n_2,boundary_now0_carry__1_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_boundary_now0_carry__1_O_UNCONNECTED[3:0]),
        .S({1'b0,boundary_now0_carry__1_i_1_n_0,boundary_now0_carry__1_i_2_n_0,boundary_now0_carry__1_i_3_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    boundary_now0_carry__1_i_1
       (.I0(Q[31]),
        .I1(boundary_now0_carry__1_i_4_n_5),
        .I2(Q[30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(boundary_now0_carry__1_i_1_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry__1_i_2
       (.I0(Q[29]),
        .I1(boundary_now0_carry__1_i_4_n_7),
        .I2(boundary_now0_carry__1_i_5_n_5),
        .I3(Q[27]),
        .I4(boundary_now0_carry__1_i_5_n_4),
        .I5(Q[28]),
        .O(boundary_now0_carry__1_i_2_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry__1_i_3
       (.I0(Q[26]),
        .I1(boundary_now0_carry__1_i_5_n_6),
        .I2(boundary_now0_carry__0_i_5_n_4),
        .I3(Q[24]),
        .I4(boundary_now0_carry__1_i_5_n_7),
        .I5(Q[25]),
        .O(boundary_now0_carry__1_i_3_n_0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry__1_i_4
       (.CI(boundary_now0_carry__1_i_5_n_0),
        .CO({NLW_boundary_now0_carry__1_i_4_CO_UNCONNECTED[3:2],boundary_now0_carry__1_i_4_n_2,boundary_now0_carry__1_i_4_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({NLW_boundary_now0_carry__1_i_4_O_UNCONNECTED[3],boundary_now0_carry__1_i_4_n_5,boundary_now0_carry__1_i_4_n_6,boundary_now0_carry__1_i_4_n_7}),
        .S({1'b0,phase_q_reg[31:29]}));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry__1_i_5
       (.CI(boundary_now0_carry__0_i_5_n_0),
        .CO({boundary_now0_carry__1_i_5_n_0,boundary_now0_carry__1_i_5_n_1,boundary_now0_carry__1_i_5_n_2,boundary_now0_carry__1_i_5_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry__1_i_5_n_4,boundary_now0_carry__1_i_5_n_5,boundary_now0_carry__1_i_5_n_6,boundary_now0_carry__1_i_5_n_7}),
        .S(phase_q_reg[28:25]));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry_i_1
       (.I0(Q[11]),
        .I1(boundary_now0_carry_i_5_n_5),
        .I2(boundary_now0_carry_i_5_n_7),
        .I3(Q[9]),
        .I4(boundary_now0_carry_i_5_n_6),
        .I5(Q[10]),
        .O(boundary_now0_carry_i_1_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry_i_2
       (.I0(Q[8]),
        .I1(boundary_now0_carry_i_6_n_4),
        .I2(boundary_now0_carry_i_6_n_6),
        .I3(Q[6]),
        .I4(boundary_now0_carry_i_6_n_5),
        .I5(Q[7]),
        .O(boundary_now0_carry_i_2_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    boundary_now0_carry_i_3
       (.I0(Q[5]),
        .I1(boundary_now0_carry_i_6_n_7),
        .I2(boundary_now0_carry_i_7_n_5),
        .I3(Q[3]),
        .I4(boundary_now0_carry_i_7_n_4),
        .I5(Q[4]),
        .O(boundary_now0_carry_i_3_n_0));
  LUT6 #(
    .INIT(64'h6006000000006006)) 
    boundary_now0_carry_i_4
       (.I0(phase_q_reg[0]),
        .I1(Q[0]),
        .I2(boundary_now0_carry_i_7_n_6),
        .I3(Q[2]),
        .I4(boundary_now0_carry_i_7_n_7),
        .I5(Q[1]),
        .O(boundary_now0_carry_i_4_n_0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry_i_5
       (.CI(boundary_now0_carry_i_6_n_0),
        .CO({boundary_now0_carry_i_5_n_0,boundary_now0_carry_i_5_n_1,boundary_now0_carry_i_5_n_2,boundary_now0_carry_i_5_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry_i_5_n_4,boundary_now0_carry_i_5_n_5,boundary_now0_carry_i_5_n_6,boundary_now0_carry_i_5_n_7}),
        .S(phase_q_reg[12:9]));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry_i_6
       (.CI(boundary_now0_carry_i_7_n_0),
        .CO({boundary_now0_carry_i_6_n_0,boundary_now0_carry_i_6_n_1,boundary_now0_carry_i_6_n_2,boundary_now0_carry_i_6_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry_i_6_n_4,boundary_now0_carry_i_6_n_5,boundary_now0_carry_i_6_n_6,boundary_now0_carry_i_6_n_7}),
        .S(phase_q_reg[8:5]));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 boundary_now0_carry_i_7
       (.CI(1'b0),
        .CO({boundary_now0_carry_i_7_n_0,boundary_now0_carry_i_7_n_1,boundary_now0_carry_i_7_n_2,boundary_now0_carry_i_7_n_3}),
        .CYINIT(phase_q_reg[0]),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({boundary_now0_carry_i_7_n_4,boundary_now0_carry_i_7_n_5,boundary_now0_carry_i_7_n_6,boundary_now0_carry_i_7_n_7}),
        .S(phase_q_reg[4:1]));
  (* SOFT_HLUTNM = "soft_lutpair25" *) 
  LUT3 #(
    .INIT(8'h01)) 
    cfg_ready_INST_0
       (.I0(stop),
        .I1(rst),
        .I2(pending_q_reg_0),
        .O(cfg_ready));
  (* SOFT_HLUTNM = "soft_lutpair58" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[0]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [0]),
        .I1(applied_q_reg_1),
        .O(D[0]));
  (* SOFT_HLUTNM = "soft_lutpair53" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[10]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [10]),
        .I1(applied_q_reg_1),
        .O(D[10]));
  (* SOFT_HLUTNM = "soft_lutpair53" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[11]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [11]),
        .I1(applied_q_reg_1),
        .O(D[11]));
  (* SOFT_HLUTNM = "soft_lutpair52" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[12]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [12]),
        .I1(applied_q_reg_1),
        .O(D[12]));
  (* SOFT_HLUTNM = "soft_lutpair52" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[13]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [13]),
        .I1(applied_q_reg_1),
        .O(D[13]));
  (* SOFT_HLUTNM = "soft_lutpair51" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[14]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [14]),
        .I1(applied_q_reg_1),
        .O(D[14]));
  (* SOFT_HLUTNM = "soft_lutpair32" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[15]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [15]),
        .I1(applied_q_reg_1),
        .O(D[15]));
  (* SOFT_HLUTNM = "soft_lutpair31" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[16]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [16]),
        .I1(applied_q_reg_1),
        .O(D[16]));
  (* SOFT_HLUTNM = "soft_lutpair51" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[17]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [17]),
        .I1(applied_q_reg_1),
        .O(D[17]));
  (* SOFT_HLUTNM = "soft_lutpair50" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[18]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [18]),
        .I1(applied_q_reg_1),
        .O(D[18]));
  (* SOFT_HLUTNM = "soft_lutpair33" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[19]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [19]),
        .I1(applied_q_reg_1),
        .O(D[19]));
  (* SOFT_HLUTNM = "soft_lutpair58" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[1]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [1]),
        .I1(applied_q_reg_1),
        .O(D[1]));
  (* SOFT_HLUTNM = "soft_lutpair50" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[20]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [20]),
        .I1(applied_q_reg_1),
        .O(D[20]));
  (* SOFT_HLUTNM = "soft_lutpair34" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[21]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [21]),
        .I1(applied_q_reg_1),
        .O(D[21]));
  (* SOFT_HLUTNM = "soft_lutpair49" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[22]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [22]),
        .I1(applied_q_reg_1),
        .O(D[22]));
  (* SOFT_HLUTNM = "soft_lutpair49" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[23]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [23]),
        .I1(applied_q_reg_1),
        .O(D[23]));
  (* SOFT_HLUTNM = "soft_lutpair48" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[24]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [24]),
        .I1(applied_q_reg_1),
        .O(D[24]));
  (* SOFT_HLUTNM = "soft_lutpair48" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[25]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [25]),
        .I1(applied_q_reg_1),
        .O(D[25]));
  (* SOFT_HLUTNM = "soft_lutpair47" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[26]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [26]),
        .I1(applied_q_reg_1),
        .O(D[26]));
  (* SOFT_HLUTNM = "soft_lutpair47" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[27]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [27]),
        .I1(applied_q_reg_1),
        .O(D[27]));
  (* SOFT_HLUTNM = "soft_lutpair46" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[28]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [28]),
        .I1(applied_q_reg_1),
        .O(D[28]));
  (* SOFT_HLUTNM = "soft_lutpair46" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[29]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [29]),
        .I1(applied_q_reg_1),
        .O(D[29]));
  (* SOFT_HLUTNM = "soft_lutpair57" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[2]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [2]),
        .I1(applied_q_reg_1),
        .O(D[2]));
  (* SOFT_HLUTNM = "soft_lutpair45" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[30]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [30]),
        .I1(applied_q_reg_1),
        .O(D[30]));
  (* SOFT_HLUTNM = "soft_lutpair45" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[31]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [31]),
        .I1(applied_q_reg_1),
        .O(D[31]));
  (* SOFT_HLUTNM = "soft_lutpair57" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[3]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [3]),
        .I1(applied_q_reg_1),
        .O(D[3]));
  (* SOFT_HLUTNM = "soft_lutpair56" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[4]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [4]),
        .I1(applied_q_reg_1),
        .O(D[4]));
  (* SOFT_HLUTNM = "soft_lutpair56" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[5]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [5]),
        .I1(applied_q_reg_1),
        .O(D[5]));
  (* SOFT_HLUTNM = "soft_lutpair55" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[6]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [6]),
        .I1(applied_q_reg_1),
        .O(D[6]));
  (* SOFT_HLUTNM = "soft_lutpair55" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[7]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [7]),
        .I1(applied_q_reg_1),
        .O(D[7]));
  (* SOFT_HLUTNM = "soft_lutpair54" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[8]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [8]),
        .I1(applied_q_reg_1),
        .O(D[8]));
  (* SOFT_HLUTNM = "soft_lutpair54" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high0_q[9]_i_1 
       (.I0(\active_high_yaw_q_reg[31]_0 [9]),
        .I1(applied_q_reg_1),
        .O(D[9]));
  (* SOFT_HLUTNM = "soft_lutpair72" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[0]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [0]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [0]));
  (* SOFT_HLUTNM = "soft_lutpair68" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[10]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [10]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [10]));
  (* SOFT_HLUTNM = "soft_lutpair67" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[11]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [11]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [11]));
  (* SOFT_HLUTNM = "soft_lutpair67" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[12]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [12]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [12]));
  (* SOFT_HLUTNM = "soft_lutpair37" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[13]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [13]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [13]));
  (* SOFT_HLUTNM = "soft_lutpair66" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[14]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [14]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [14]));
  (* SOFT_HLUTNM = "soft_lutpair66" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[15]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [15]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [15]));
  (* SOFT_HLUTNM = "soft_lutpair65" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[16]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [16]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [16]));
  (* SOFT_HLUTNM = "soft_lutpair65" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[17]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [17]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [17]));
  (* SOFT_HLUTNM = "soft_lutpair64" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[18]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [18]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [18]));
  (* SOFT_HLUTNM = "soft_lutpair64" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[19]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [19]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [19]));
  (* SOFT_HLUTNM = "soft_lutpair72" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[1]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [1]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [1]));
  (* SOFT_HLUTNM = "soft_lutpair63" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[20]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [20]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [20]));
  (* SOFT_HLUTNM = "soft_lutpair63" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[21]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [21]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [21]));
  (* SOFT_HLUTNM = "soft_lutpair35" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[22]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [22]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [22]));
  (* SOFT_HLUTNM = "soft_lutpair62" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[23]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [23]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [23]));
  (* SOFT_HLUTNM = "soft_lutpair62" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[24]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [24]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [24]));
  (* SOFT_HLUTNM = "soft_lutpair61" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[25]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [25]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [25]));
  (* SOFT_HLUTNM = "soft_lutpair61" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[26]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [26]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [26]));
  (* SOFT_HLUTNM = "soft_lutpair36" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[27]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [27]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [27]));
  (* SOFT_HLUTNM = "soft_lutpair60" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[28]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [28]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [28]));
  (* SOFT_HLUTNM = "soft_lutpair60" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[29]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [29]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [29]));
  (* SOFT_HLUTNM = "soft_lutpair71" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[2]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [2]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [2]));
  (* SOFT_HLUTNM = "soft_lutpair59" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[30]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [30]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [30]));
  (* SOFT_HLUTNM = "soft_lutpair59" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[31]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [31]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [31]));
  (* SOFT_HLUTNM = "soft_lutpair71" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[3]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [3]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [3]));
  (* SOFT_HLUTNM = "soft_lutpair70" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[4]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [4]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [4]));
  (* SOFT_HLUTNM = "soft_lutpair70" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[5]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [5]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [5]));
  (* SOFT_HLUTNM = "soft_lutpair69" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[6]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [6]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [6]));
  (* SOFT_HLUTNM = "soft_lutpair38" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[7]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [7]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [7]));
  (* SOFT_HLUTNM = "soft_lutpair69" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[8]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [8]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [8]));
  (* SOFT_HLUTNM = "soft_lutpair68" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high1_q[9]_i_1 
       (.I0(\active_high_pitch_q_reg[31]_0 [9]),
        .I1(applied_q_reg_1),
        .O(\active_high_pitch_q_reg[31]_1 [9]));
  (* SOFT_HLUTNM = "soft_lutpair86" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[0]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [0]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [0]));
  (* SOFT_HLUTNM = "soft_lutpair82" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[10]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [10]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [10]));
  (* SOFT_HLUTNM = "soft_lutpair81" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[11]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [11]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [11]));
  (* SOFT_HLUTNM = "soft_lutpair81" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[12]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [12]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [12]));
  (* SOFT_HLUTNM = "soft_lutpair42" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[13]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [13]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [13]));
  (* SOFT_HLUTNM = "soft_lutpair80" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[14]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [14]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [14]));
  (* SOFT_HLUTNM = "soft_lutpair80" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[15]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [15]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [15]));
  (* SOFT_HLUTNM = "soft_lutpair79" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[16]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [16]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [16]));
  (* SOFT_HLUTNM = "soft_lutpair79" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[17]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [17]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [17]));
  (* SOFT_HLUTNM = "soft_lutpair78" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[18]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [18]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [18]));
  (* SOFT_HLUTNM = "soft_lutpair41" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[19]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [19]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [19]));
  (* SOFT_HLUTNM = "soft_lutpair86" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[1]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [1]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [1]));
  (* SOFT_HLUTNM = "soft_lutpair78" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[20]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [20]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [20]));
  (* SOFT_HLUTNM = "soft_lutpair77" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[21]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [21]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [21]));
  (* SOFT_HLUTNM = "soft_lutpair77" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[22]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [22]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [22]));
  (* SOFT_HLUTNM = "soft_lutpair76" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[23]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [23]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [23]));
  (* SOFT_HLUTNM = "soft_lutpair76" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[24]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [24]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [24]));
  (* SOFT_HLUTNM = "soft_lutpair75" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[25]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [25]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [25]));
  (* SOFT_HLUTNM = "soft_lutpair75" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[26]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [26]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [26]));
  (* SOFT_HLUTNM = "soft_lutpair40" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[27]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [27]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [27]));
  (* SOFT_HLUTNM = "soft_lutpair74" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[28]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [28]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [28]));
  (* SOFT_HLUTNM = "soft_lutpair74" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[29]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [29]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [29]));
  (* SOFT_HLUTNM = "soft_lutpair85" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[2]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [2]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [2]));
  (* SOFT_HLUTNM = "soft_lutpair73" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[30]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [30]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [30]));
  (* SOFT_HLUTNM = "soft_lutpair73" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[31]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [31]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [31]));
  (* SOFT_HLUTNM = "soft_lutpair85" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[3]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [3]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [3]));
  (* SOFT_HLUTNM = "soft_lutpair84" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[4]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [4]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [4]));
  (* SOFT_HLUTNM = "soft_lutpair43" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[5]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [5]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [5]));
  (* SOFT_HLUTNM = "soft_lutpair84" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[6]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [6]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [6]));
  (* SOFT_HLUTNM = "soft_lutpair83" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[7]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [7]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [7]));
  (* SOFT_HLUTNM = "soft_lutpair83" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[8]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [8]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [8]));
  (* SOFT_HLUTNM = "soft_lutpair82" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_high2_q[9]_i_1 
       (.I0(\active_high_speed_q_reg[31]_0 [9]),
        .I1(applied_q_reg_1),
        .O(\active_high_speed_q_reg[31]_1 [9]));
  (* SOFT_HLUTNM = "soft_lutpair111" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[0]_i_1 
       (.I0(Q[0]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [0]));
  (* SOFT_HLUTNM = "soft_lutpair107" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[10]_i_1 
       (.I0(Q[10]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [10]));
  (* SOFT_HLUTNM = "soft_lutpair115" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[11]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[11]),
        .O(\active_period_q_reg[31]_0 [11]));
  (* SOFT_HLUTNM = "soft_lutpair107" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[12]_i_1 
       (.I0(Q[12]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [12]));
  (* SOFT_HLUTNM = "soft_lutpair26" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[13]_i_1 
       (.I0(Q[13]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [13]));
  (* SOFT_HLUTNM = "soft_lutpair114" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[14]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[14]),
        .O(\active_period_q_reg[31]_0 [14]));
  (* SOFT_HLUTNM = "soft_lutpair106" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[15]_i_1 
       (.I0(Q[15]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [15]));
  (* SOFT_HLUTNM = "soft_lutpair106" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[16]_i_1 
       (.I0(Q[16]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [16]));
  (* SOFT_HLUTNM = "soft_lutpair114" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[17]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[17]),
        .O(\active_period_q_reg[31]_0 [17]));
  (* SOFT_HLUTNM = "soft_lutpair27" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[18]_i_1 
       (.I0(Q[18]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [18]));
  (* SOFT_HLUTNM = "soft_lutpair105" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[19]_i_1 
       (.I0(Q[19]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [19]));
  (* SOFT_HLUTNM = "soft_lutpair111" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[1]_i_1 
       (.I0(Q[1]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [1]));
  (* SOFT_HLUTNM = "soft_lutpair113" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[20]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[20]),
        .O(\active_period_q_reg[31]_0 [20]));
  (* SOFT_HLUTNM = "soft_lutpair105" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[21]_i_1 
       (.I0(Q[21]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [21]));
  (* SOFT_HLUTNM = "soft_lutpair29" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[22]_i_1 
       (.I0(Q[22]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [22]));
  (* SOFT_HLUTNM = "soft_lutpair113" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[23]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[23]),
        .O(\active_period_q_reg[31]_0 [23]));
  (* SOFT_HLUTNM = "soft_lutpair30" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[24]_i_1 
       (.I0(Q[24]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [24]));
  (* SOFT_HLUTNM = "soft_lutpair104" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[25]_i_1 
       (.I0(Q[25]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [25]));
  (* SOFT_HLUTNM = "soft_lutpair112" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[26]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[26]),
        .O(\active_period_q_reg[31]_0 [26]));
  (* SOFT_HLUTNM = "soft_lutpair104" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[27]_i_1 
       (.I0(Q[27]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [27]));
  (* SOFT_HLUTNM = "soft_lutpair28" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[28]_i_1 
       (.I0(Q[28]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [28]));
  (* SOFT_HLUTNM = "soft_lutpair112" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[29]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[29]),
        .O(\active_period_q_reg[31]_0 [29]));
  (* SOFT_HLUTNM = "soft_lutpair110" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[2]_i_1 
       (.I0(Q[2]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [2]));
  (* SOFT_HLUTNM = "soft_lutpair103" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[30]_i_1 
       (.I0(Q[30]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [30]));
  (* SOFT_HLUTNM = "soft_lutpair103" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[31]_i_1 
       (.I0(Q[31]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [31]));
  (* SOFT_HLUTNM = "soft_lutpair110" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[3]_i_1 
       (.I0(Q[3]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [3]));
  (* SOFT_HLUTNM = "soft_lutpair109" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[4]_i_1 
       (.I0(Q[4]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [4]));
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[5]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[5]),
        .O(\active_period_q_reg[31]_0 [5]));
  (* SOFT_HLUTNM = "soft_lutpair109" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[6]_i_1 
       (.I0(Q[6]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [6]));
  (* SOFT_HLUTNM = "soft_lutpair108" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[7]_i_1 
       (.I0(Q[7]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [7]));
  (* SOFT_HLUTNM = "soft_lutpair115" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[8]_i_1 
       (.I0(applied_q_reg_1),
        .I1(Q[8]),
        .O(\active_period_q_reg[31]_0 [8]));
  (* SOFT_HLUTNM = "soft_lutpair108" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_period_q[9]_i_1 
       (.I0(Q[9]),
        .I1(applied_q_reg_1),
        .O(\active_period_q_reg[31]_0 [9]));
  (* SOFT_HLUTNM = "soft_lutpair102" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[0]_i_1 
       (.I0(active_tag[0]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [0]));
  (* SOFT_HLUTNM = "soft_lutpair97" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[10]_i_1 
       (.I0(active_tag[10]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [10]));
  (* SOFT_HLUTNM = "soft_lutpair97" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[11]_i_1 
       (.I0(active_tag[11]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [11]));
  (* SOFT_HLUTNM = "soft_lutpair96" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[12]_i_1 
       (.I0(active_tag[12]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [12]));
  (* SOFT_HLUTNM = "soft_lutpair96" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[13]_i_1 
       (.I0(active_tag[13]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [13]));
  (* SOFT_HLUTNM = "soft_lutpair95" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[14]_i_1 
       (.I0(active_tag[14]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [14]));
  (* SOFT_HLUTNM = "soft_lutpair95" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[15]_i_1 
       (.I0(active_tag[15]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [15]));
  (* SOFT_HLUTNM = "soft_lutpair94" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[16]_i_1 
       (.I0(active_tag[16]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [16]));
  (* SOFT_HLUTNM = "soft_lutpair94" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[17]_i_1 
       (.I0(active_tag[17]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [17]));
  (* SOFT_HLUTNM = "soft_lutpair93" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[18]_i_1 
       (.I0(active_tag[18]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [18]));
  (* SOFT_HLUTNM = "soft_lutpair93" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[19]_i_1 
       (.I0(active_tag[19]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [19]));
  (* SOFT_HLUTNM = "soft_lutpair102" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[1]_i_1 
       (.I0(active_tag[1]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [1]));
  (* SOFT_HLUTNM = "soft_lutpair92" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[20]_i_1 
       (.I0(active_tag[20]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [20]));
  (* SOFT_HLUTNM = "soft_lutpair92" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[21]_i_1 
       (.I0(active_tag[21]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [21]));
  (* SOFT_HLUTNM = "soft_lutpair91" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[22]_i_1 
       (.I0(active_tag[22]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [22]));
  (* SOFT_HLUTNM = "soft_lutpair91" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[23]_i_1 
       (.I0(active_tag[23]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [23]));
  (* SOFT_HLUTNM = "soft_lutpair90" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[24]_i_1 
       (.I0(active_tag[24]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [24]));
  (* SOFT_HLUTNM = "soft_lutpair90" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[25]_i_1 
       (.I0(active_tag[25]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [25]));
  (* SOFT_HLUTNM = "soft_lutpair89" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[26]_i_1 
       (.I0(active_tag[26]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [26]));
  (* SOFT_HLUTNM = "soft_lutpair89" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[27]_i_1 
       (.I0(active_tag[27]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [27]));
  (* SOFT_HLUTNM = "soft_lutpair88" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[28]_i_1 
       (.I0(active_tag[28]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [28]));
  (* SOFT_HLUTNM = "soft_lutpair88" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[29]_i_1 
       (.I0(active_tag[29]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [29]));
  (* SOFT_HLUTNM = "soft_lutpair101" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[2]_i_1 
       (.I0(active_tag[2]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [2]));
  (* SOFT_HLUTNM = "soft_lutpair87" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[30]_i_1 
       (.I0(active_tag[30]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [30]));
  (* SOFT_HLUTNM = "soft_lutpair87" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[31]_i_1 
       (.I0(active_tag[31]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [31]));
  (* SOFT_HLUTNM = "soft_lutpair101" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[3]_i_1 
       (.I0(active_tag[3]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [3]));
  (* SOFT_HLUTNM = "soft_lutpair100" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[4]_i_1 
       (.I0(active_tag[4]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [4]));
  (* SOFT_HLUTNM = "soft_lutpair100" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[5]_i_1 
       (.I0(active_tag[5]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [5]));
  (* SOFT_HLUTNM = "soft_lutpair99" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[6]_i_1 
       (.I0(active_tag[6]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [6]));
  (* SOFT_HLUTNM = "soft_lutpair99" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[7]_i_1 
       (.I0(active_tag[7]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [7]));
  (* SOFT_HLUTNM = "soft_lutpair98" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[8]_i_1 
       (.I0(active_tag[8]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [8]));
  (* SOFT_HLUTNM = "soft_lutpair98" *) 
  LUT2 #(
    .INIT(4'h8)) 
    \expected_tag_q[9]_i_1 
       (.I0(active_tag[9]),
        .I1(applied_q_reg_1),
        .O(\active_tag_q_reg[31]_0 [9]));
  (* SOFT_HLUTNM = "soft_lutpair39" *) 
  LUT2 #(
    .INIT(4'h1)) 
    \failure_code_q[0]_i_2 
       (.I0(applied_q_reg_0),
        .I1(stop_0),
        .O(applied_q_reg_2));
  (* SOFT_HLUTNM = "soft_lutpair44" *) 
  LUT2 #(
    .INIT(4'hE)) 
    \failure_code_q[2]_i_4 
       (.I0(applied_q_reg_1),
        .I1(stop_0),
        .O(stop_1));
  LUT6 #(
    .INIT(64'h000000000000FAF8)) 
    failure_event_q_i_1
       (.I0(failure_event_q_reg),
        .I1(raw_fault_events),
        .I2(applied_q_reg_0),
        .I3(failure_event_q_reg_0),
        .I4(stop_0),
        .I5(applied_q_reg_1),
        .O(window_active_q_reg_0));
  (* SOFT_HLUTNM = "soft_lutpair24" *) 
  LUT5 #(
    .INIT(32'h11101010)) 
    frame_start_q_i_1
       (.I0(stop),
        .I1(rst),
        .I2(apply_now),
        .I3(boundary_now0__10),
        .I4(running_q_reg_0),
        .O(frame_start_q_i_1_n_0));
  FDRE frame_start_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(frame_start_q_i_1_n_0),
        .Q(frame_start),
        .R(1'b0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__0_i_1
       (.I0(boundary_now0_carry__0_i_7_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [15]),
        .I2(\active_high_pitch_q_reg[31]_0 [14]),
        .I3(boundary_now0_carry__0_i_7_n_6),
        .O(i__carry__0_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__0_i_2
       (.I0(boundary_now0_carry__0_i_7_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [13]),
        .I2(\active_high_pitch_q_reg[31]_0 [12]),
        .I3(boundary_now0_carry_i_5_n_4),
        .O(i__carry__0_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__0_i_3
       (.I0(boundary_now0_carry_i_5_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [11]),
        .I2(\active_high_pitch_q_reg[31]_0 [10]),
        .I3(boundary_now0_carry_i_5_n_6),
        .O(i__carry__0_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__0_i_4
       (.I0(boundary_now0_carry_i_5_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [9]),
        .I2(\active_high_pitch_q_reg[31]_0 [8]),
        .I3(boundary_now0_carry_i_6_n_4),
        .O(i__carry__0_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__0_i_5
       (.I0(\active_high_pitch_q_reg[31]_0 [15]),
        .I1(boundary_now0_carry__0_i_7_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [14]),
        .I3(boundary_now0_carry__0_i_7_n_6),
        .O(i__carry__0_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__0_i_6
       (.I0(\active_high_pitch_q_reg[31]_0 [13]),
        .I1(boundary_now0_carry__0_i_7_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [12]),
        .I3(boundary_now0_carry_i_5_n_4),
        .O(i__carry__0_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__0_i_7
       (.I0(\active_high_pitch_q_reg[31]_0 [11]),
        .I1(boundary_now0_carry_i_5_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [10]),
        .I3(boundary_now0_carry_i_5_n_6),
        .O(i__carry__0_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__0_i_8
       (.I0(\active_high_pitch_q_reg[31]_0 [9]),
        .I1(boundary_now0_carry_i_5_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [8]),
        .I3(boundary_now0_carry_i_6_n_4),
        .O(i__carry__0_i_8_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__1_i_1
       (.I0(boundary_now0_carry__0_i_5_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [23]),
        .I2(\active_high_pitch_q_reg[31]_0 [22]),
        .I3(boundary_now0_carry__0_i_5_n_6),
        .O(i__carry__1_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__1_i_2
       (.I0(boundary_now0_carry__0_i_5_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [21]),
        .I2(\active_high_pitch_q_reg[31]_0 [20]),
        .I3(boundary_now0_carry__0_i_6_n_4),
        .O(i__carry__1_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__1_i_3
       (.I0(boundary_now0_carry__0_i_6_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [19]),
        .I2(\active_high_pitch_q_reg[31]_0 [18]),
        .I3(boundary_now0_carry__0_i_6_n_6),
        .O(i__carry__1_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__1_i_4
       (.I0(boundary_now0_carry__0_i_6_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [17]),
        .I2(\active_high_pitch_q_reg[31]_0 [16]),
        .I3(boundary_now0_carry__0_i_7_n_4),
        .O(i__carry__1_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__1_i_5
       (.I0(\active_high_pitch_q_reg[31]_0 [23]),
        .I1(boundary_now0_carry__0_i_5_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [22]),
        .I3(boundary_now0_carry__0_i_5_n_6),
        .O(i__carry__1_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__1_i_6
       (.I0(\active_high_pitch_q_reg[31]_0 [21]),
        .I1(boundary_now0_carry__0_i_5_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [20]),
        .I3(boundary_now0_carry__0_i_6_n_4),
        .O(i__carry__1_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__1_i_7
       (.I0(\active_high_pitch_q_reg[31]_0 [19]),
        .I1(boundary_now0_carry__0_i_6_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [18]),
        .I3(boundary_now0_carry__0_i_6_n_6),
        .O(i__carry__1_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__1_i_8
       (.I0(\active_high_pitch_q_reg[31]_0 [17]),
        .I1(boundary_now0_carry__0_i_6_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [16]),
        .I3(boundary_now0_carry__0_i_7_n_4),
        .O(i__carry__1_i_8_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__2_i_1
       (.I0(boundary_now0_carry__1_i_4_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [31]),
        .I2(\active_high_pitch_q_reg[31]_0 [30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(i__carry__2_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__2_i_2
       (.I0(boundary_now0_carry__1_i_4_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [29]),
        .I2(\active_high_pitch_q_reg[31]_0 [28]),
        .I3(boundary_now0_carry__1_i_5_n_4),
        .O(i__carry__2_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__2_i_3
       (.I0(boundary_now0_carry__1_i_5_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [27]),
        .I2(\active_high_pitch_q_reg[31]_0 [26]),
        .I3(boundary_now0_carry__1_i_5_n_6),
        .O(i__carry__2_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry__2_i_4
       (.I0(boundary_now0_carry__1_i_5_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [25]),
        .I2(\active_high_pitch_q_reg[31]_0 [24]),
        .I3(boundary_now0_carry__0_i_5_n_4),
        .O(i__carry__2_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__2_i_5
       (.I0(\active_high_pitch_q_reg[31]_0 [31]),
        .I1(boundary_now0_carry__1_i_4_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(i__carry__2_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__2_i_6
       (.I0(\active_high_pitch_q_reg[31]_0 [29]),
        .I1(boundary_now0_carry__1_i_4_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [28]),
        .I3(boundary_now0_carry__1_i_5_n_4),
        .O(i__carry__2_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__2_i_7
       (.I0(\active_high_pitch_q_reg[31]_0 [27]),
        .I1(boundary_now0_carry__1_i_5_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [26]),
        .I3(boundary_now0_carry__1_i_5_n_6),
        .O(i__carry__2_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry__2_i_8
       (.I0(\active_high_pitch_q_reg[31]_0 [25]),
        .I1(boundary_now0_carry__1_i_5_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [24]),
        .I3(boundary_now0_carry__0_i_5_n_4),
        .O(i__carry__2_i_8_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_1
       (.I0(boundary_now0_carry_i_6_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [7]),
        .I2(\active_high_pitch_q_reg[31]_0 [6]),
        .I3(boundary_now0_carry_i_6_n_6),
        .O(i__carry_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_1__0
       (.I0(boundary_now0_carry_i_6_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [7]),
        .I2(\active_high_speed_q_reg[31]_0 [6]),
        .I3(boundary_now0_carry_i_6_n_6),
        .O(i__carry_i_1__0_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_1__1
       (.I0(boundary_now0_carry__0_i_7_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [15]),
        .I2(\active_high_speed_q_reg[31]_0 [14]),
        .I3(boundary_now0_carry__0_i_7_n_6),
        .O(i__carry_i_1__1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_1__2
       (.I0(boundary_now0_carry__0_i_5_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [23]),
        .I2(\active_high_speed_q_reg[31]_0 [22]),
        .I3(boundary_now0_carry__0_i_5_n_6),
        .O(i__carry_i_1__2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_1__3
       (.I0(boundary_now0_carry__1_i_4_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [31]),
        .I2(\active_high_speed_q_reg[31]_0 [30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(i__carry_i_1__3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_2
       (.I0(boundary_now0_carry_i_6_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [5]),
        .I2(\active_high_pitch_q_reg[31]_0 [4]),
        .I3(boundary_now0_carry_i_7_n_4),
        .O(i__carry_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_2__0
       (.I0(boundary_now0_carry_i_6_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [5]),
        .I2(\active_high_speed_q_reg[31]_0 [4]),
        .I3(boundary_now0_carry_i_7_n_4),
        .O(i__carry_i_2__0_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_2__1
       (.I0(boundary_now0_carry__0_i_7_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [13]),
        .I2(\active_high_speed_q_reg[31]_0 [12]),
        .I3(boundary_now0_carry_i_5_n_4),
        .O(i__carry_i_2__1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_2__2
       (.I0(boundary_now0_carry__0_i_5_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [21]),
        .I2(\active_high_speed_q_reg[31]_0 [20]),
        .I3(boundary_now0_carry__0_i_6_n_4),
        .O(i__carry_i_2__2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_2__3
       (.I0(boundary_now0_carry__1_i_4_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [29]),
        .I2(\active_high_speed_q_reg[31]_0 [28]),
        .I3(boundary_now0_carry__1_i_5_n_4),
        .O(i__carry_i_2__3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_3
       (.I0(boundary_now0_carry_i_7_n_5),
        .I1(\active_high_pitch_q_reg[31]_0 [3]),
        .I2(\active_high_pitch_q_reg[31]_0 [2]),
        .I3(boundary_now0_carry_i_7_n_6),
        .O(i__carry_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_3__0
       (.I0(boundary_now0_carry_i_7_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [3]),
        .I2(\active_high_speed_q_reg[31]_0 [2]),
        .I3(boundary_now0_carry_i_7_n_6),
        .O(i__carry_i_3__0_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_3__1
       (.I0(boundary_now0_carry_i_5_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [11]),
        .I2(\active_high_speed_q_reg[31]_0 [10]),
        .I3(boundary_now0_carry_i_5_n_6),
        .O(i__carry_i_3__1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_3__2
       (.I0(boundary_now0_carry__0_i_6_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [19]),
        .I2(\active_high_speed_q_reg[31]_0 [18]),
        .I3(boundary_now0_carry__0_i_6_n_6),
        .O(i__carry_i_3__2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_3__3
       (.I0(boundary_now0_carry__1_i_5_n_5),
        .I1(\active_high_speed_q_reg[31]_0 [27]),
        .I2(\active_high_speed_q_reg[31]_0 [26]),
        .I3(boundary_now0_carry__1_i_5_n_6),
        .O(i__carry_i_3__3_n_0));
  LUT4 #(
    .INIT(16'hD444)) 
    i__carry_i_4
       (.I0(boundary_now0_carry_i_7_n_7),
        .I1(\active_high_pitch_q_reg[31]_0 [1]),
        .I2(phase_q_reg[0]),
        .I3(\active_high_pitch_q_reg[31]_0 [0]),
        .O(i__carry_i_4_n_0));
  LUT4 #(
    .INIT(16'hD444)) 
    i__carry_i_4__0
       (.I0(boundary_now0_carry_i_7_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [1]),
        .I2(phase_q_reg[0]),
        .I3(\active_high_speed_q_reg[31]_0 [0]),
        .O(i__carry_i_4__0_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_4__1
       (.I0(boundary_now0_carry_i_5_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [9]),
        .I2(\active_high_speed_q_reg[31]_0 [8]),
        .I3(boundary_now0_carry_i_6_n_4),
        .O(i__carry_i_4__1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_4__2
       (.I0(boundary_now0_carry__0_i_6_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [17]),
        .I2(\active_high_speed_q_reg[31]_0 [16]),
        .I3(boundary_now0_carry__0_i_7_n_4),
        .O(i__carry_i_4__2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    i__carry_i_4__3
       (.I0(boundary_now0_carry__1_i_5_n_7),
        .I1(\active_high_speed_q_reg[31]_0 [25]),
        .I2(\active_high_speed_q_reg[31]_0 [24]),
        .I3(boundary_now0_carry__0_i_5_n_4),
        .O(i__carry_i_4__3_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_5
       (.I0(\active_high_pitch_q_reg[31]_0 [7]),
        .I1(boundary_now0_carry_i_6_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [6]),
        .I3(boundary_now0_carry_i_6_n_6),
        .O(i__carry_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_5__0
       (.I0(\active_high_speed_q_reg[31]_0 [7]),
        .I1(boundary_now0_carry_i_6_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [6]),
        .I3(boundary_now0_carry_i_6_n_6),
        .O(i__carry_i_5__0_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_5__1
       (.I0(\active_high_speed_q_reg[31]_0 [15]),
        .I1(boundary_now0_carry__0_i_7_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [14]),
        .I3(boundary_now0_carry__0_i_7_n_6),
        .O(i__carry_i_5__1_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_5__2
       (.I0(\active_high_speed_q_reg[31]_0 [23]),
        .I1(boundary_now0_carry__0_i_5_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [22]),
        .I3(boundary_now0_carry__0_i_5_n_6),
        .O(i__carry_i_5__2_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_5__3
       (.I0(\active_high_speed_q_reg[31]_0 [31]),
        .I1(boundary_now0_carry__1_i_4_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(i__carry_i_5__3_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_6
       (.I0(\active_high_pitch_q_reg[31]_0 [5]),
        .I1(boundary_now0_carry_i_6_n_7),
        .I2(\active_high_pitch_q_reg[31]_0 [4]),
        .I3(boundary_now0_carry_i_7_n_4),
        .O(i__carry_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_6__0
       (.I0(\active_high_speed_q_reg[31]_0 [5]),
        .I1(boundary_now0_carry_i_6_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [4]),
        .I3(boundary_now0_carry_i_7_n_4),
        .O(i__carry_i_6__0_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_6__1
       (.I0(\active_high_speed_q_reg[31]_0 [13]),
        .I1(boundary_now0_carry__0_i_7_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [12]),
        .I3(boundary_now0_carry_i_5_n_4),
        .O(i__carry_i_6__1_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_6__2
       (.I0(\active_high_speed_q_reg[31]_0 [21]),
        .I1(boundary_now0_carry__0_i_5_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [20]),
        .I3(boundary_now0_carry__0_i_6_n_4),
        .O(i__carry_i_6__2_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_6__3
       (.I0(\active_high_speed_q_reg[31]_0 [29]),
        .I1(boundary_now0_carry__1_i_4_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [28]),
        .I3(boundary_now0_carry__1_i_5_n_4),
        .O(i__carry_i_6__3_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_7
       (.I0(\active_high_pitch_q_reg[31]_0 [3]),
        .I1(boundary_now0_carry_i_7_n_5),
        .I2(\active_high_pitch_q_reg[31]_0 [2]),
        .I3(boundary_now0_carry_i_7_n_6),
        .O(i__carry_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_7__0
       (.I0(\active_high_speed_q_reg[31]_0 [3]),
        .I1(boundary_now0_carry_i_7_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [2]),
        .I3(boundary_now0_carry_i_7_n_6),
        .O(i__carry_i_7__0_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_7__1
       (.I0(\active_high_speed_q_reg[31]_0 [11]),
        .I1(boundary_now0_carry_i_5_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [10]),
        .I3(boundary_now0_carry_i_5_n_6),
        .O(i__carry_i_7__1_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_7__2
       (.I0(\active_high_speed_q_reg[31]_0 [19]),
        .I1(boundary_now0_carry__0_i_6_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [18]),
        .I3(boundary_now0_carry__0_i_6_n_6),
        .O(i__carry_i_7__2_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_7__3
       (.I0(\active_high_speed_q_reg[31]_0 [27]),
        .I1(boundary_now0_carry__1_i_5_n_5),
        .I2(\active_high_speed_q_reg[31]_0 [26]),
        .I3(boundary_now0_carry__1_i_5_n_6),
        .O(i__carry_i_7__3_n_0));
  LUT4 #(
    .INIT(16'h6006)) 
    i__carry_i_8
       (.I0(\active_high_pitch_q_reg[31]_0 [0]),
        .I1(phase_q_reg[0]),
        .I2(\active_high_pitch_q_reg[31]_0 [1]),
        .I3(boundary_now0_carry_i_7_n_7),
        .O(i__carry_i_8_n_0));
  LUT4 #(
    .INIT(16'h6006)) 
    i__carry_i_8__0
       (.I0(\active_high_speed_q_reg[31]_0 [0]),
        .I1(phase_q_reg[0]),
        .I2(\active_high_speed_q_reg[31]_0 [1]),
        .I3(boundary_now0_carry_i_7_n_7),
        .O(i__carry_i_8__0_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_8__1
       (.I0(\active_high_speed_q_reg[31]_0 [9]),
        .I1(boundary_now0_carry_i_5_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [8]),
        .I3(boundary_now0_carry_i_6_n_4),
        .O(i__carry_i_8__1_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_8__2
       (.I0(\active_high_speed_q_reg[31]_0 [17]),
        .I1(boundary_now0_carry__0_i_6_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [16]),
        .I3(boundary_now0_carry__0_i_7_n_4),
        .O(i__carry_i_8__2_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    i__carry_i_8__3
       (.I0(\active_high_speed_q_reg[31]_0 [25]),
        .I1(boundary_now0_carry__1_i_5_n_7),
        .I2(\active_high_speed_q_reg[31]_0 [24]),
        .I3(boundary_now0_carry__0_i_5_n_4),
        .O(i__carry_i_8__3_n_0));
  (* SOFT_HLUTNM = "soft_lutpair22" *) 
  LUT5 #(
    .INIT(32'hFFFFFFEF)) 
    out_valid_INST_0_i_3
       (.I0(rst),
        .I1(applied_q_reg_0),
        .I2(failure_event_q_reg),
        .I3(stop_0),
        .I4(applied_q_reg_1),
        .O(rst_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal0_carry
       (.CI(1'b0),
        .CO({payload_legal0_carry_n_0,payload_legal0_carry_n_1,payload_legal0_carry_n_2,payload_legal0_carry_n_3}),
        .CYINIT(1'b1),
        .DI({payload_legal0_carry_i_1_n_0,payload_legal0_carry_i_2_n_0,payload_legal0_carry_i_3_n_0,payload_legal0_carry_i_4_n_0}),
        .O(NLW_payload_legal0_carry_O_UNCONNECTED[3:0]),
        .S({payload_legal0_carry_i_5_n_0,payload_legal0_carry_i_6_n_0,payload_legal0_carry_i_7_n_0,payload_legal0_carry_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal0_carry__0
       (.CI(payload_legal0_carry_n_0),
        .CO({payload_legal0_carry__0_n_0,payload_legal0_carry__0_n_1,payload_legal0_carry__0_n_2,payload_legal0_carry__0_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal0_carry__0_i_1_n_0,payload_legal0_carry__0_i_2_n_0,payload_legal0_carry__0_i_3_n_0,payload_legal0_carry__0_i_4_n_0}),
        .O(NLW_payload_legal0_carry__0_O_UNCONNECTED[3:0]),
        .S({payload_legal0_carry__0_i_5_n_0,payload_legal0_carry__0_i_6_n_0,payload_legal0_carry__0_i_7_n_0,payload_legal0_carry__0_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__0_i_1
       (.I0(cfg_period[15]),
        .I1(cfg_high_speed[15]),
        .I2(cfg_period[14]),
        .I3(cfg_high_speed[14]),
        .O(payload_legal0_carry__0_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__0_i_2
       (.I0(cfg_period[13]),
        .I1(cfg_high_speed[13]),
        .I2(cfg_period[12]),
        .I3(cfg_high_speed[12]),
        .O(payload_legal0_carry__0_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__0_i_3
       (.I0(cfg_period[11]),
        .I1(cfg_high_speed[11]),
        .I2(cfg_period[10]),
        .I3(cfg_high_speed[10]),
        .O(payload_legal0_carry__0_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__0_i_4
       (.I0(cfg_period[9]),
        .I1(cfg_high_speed[9]),
        .I2(cfg_period[8]),
        .I3(cfg_high_speed[8]),
        .O(payload_legal0_carry__0_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__0_i_5
       (.I0(cfg_high_speed[15]),
        .I1(cfg_period[15]),
        .I2(cfg_high_speed[14]),
        .I3(cfg_period[14]),
        .O(payload_legal0_carry__0_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__0_i_6
       (.I0(cfg_high_speed[13]),
        .I1(cfg_period[13]),
        .I2(cfg_high_speed[12]),
        .I3(cfg_period[12]),
        .O(payload_legal0_carry__0_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__0_i_7
       (.I0(cfg_high_speed[11]),
        .I1(cfg_period[11]),
        .I2(cfg_high_speed[10]),
        .I3(cfg_period[10]),
        .O(payload_legal0_carry__0_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__0_i_8
       (.I0(cfg_high_speed[9]),
        .I1(cfg_period[9]),
        .I2(cfg_high_speed[8]),
        .I3(cfg_period[8]),
        .O(payload_legal0_carry__0_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal0_carry__1
       (.CI(payload_legal0_carry__0_n_0),
        .CO({payload_legal0_carry__1_n_0,payload_legal0_carry__1_n_1,payload_legal0_carry__1_n_2,payload_legal0_carry__1_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal0_carry__1_i_1_n_0,payload_legal0_carry__1_i_2_n_0,payload_legal0_carry__1_i_3_n_0,payload_legal0_carry__1_i_4_n_0}),
        .O(NLW_payload_legal0_carry__1_O_UNCONNECTED[3:0]),
        .S({payload_legal0_carry__1_i_5_n_0,payload_legal0_carry__1_i_6_n_0,payload_legal0_carry__1_i_7_n_0,payload_legal0_carry__1_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__1_i_1
       (.I0(cfg_period[23]),
        .I1(cfg_high_speed[23]),
        .I2(cfg_period[22]),
        .I3(cfg_high_speed[22]),
        .O(payload_legal0_carry__1_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__1_i_2
       (.I0(cfg_period[21]),
        .I1(cfg_high_speed[21]),
        .I2(cfg_period[20]),
        .I3(cfg_high_speed[20]),
        .O(payload_legal0_carry__1_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__1_i_3
       (.I0(cfg_period[19]),
        .I1(cfg_high_speed[19]),
        .I2(cfg_period[18]),
        .I3(cfg_high_speed[18]),
        .O(payload_legal0_carry__1_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__1_i_4
       (.I0(cfg_period[17]),
        .I1(cfg_high_speed[17]),
        .I2(cfg_period[16]),
        .I3(cfg_high_speed[16]),
        .O(payload_legal0_carry__1_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__1_i_5
       (.I0(cfg_high_speed[23]),
        .I1(cfg_period[23]),
        .I2(cfg_high_speed[22]),
        .I3(cfg_period[22]),
        .O(payload_legal0_carry__1_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__1_i_6
       (.I0(cfg_high_speed[21]),
        .I1(cfg_period[21]),
        .I2(cfg_high_speed[20]),
        .I3(cfg_period[20]),
        .O(payload_legal0_carry__1_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__1_i_7
       (.I0(cfg_high_speed[19]),
        .I1(cfg_period[19]),
        .I2(cfg_high_speed[18]),
        .I3(cfg_period[18]),
        .O(payload_legal0_carry__1_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__1_i_8
       (.I0(cfg_high_speed[17]),
        .I1(cfg_period[17]),
        .I2(cfg_high_speed[16]),
        .I3(cfg_period[16]),
        .O(payload_legal0_carry__1_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal0_carry__2
       (.CI(payload_legal0_carry__1_n_0),
        .CO({payload_legal0__15,payload_legal0_carry__2_n_1,payload_legal0_carry__2_n_2,payload_legal0_carry__2_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal0_carry__2_i_1_n_0,payload_legal0_carry__2_i_2_n_0,payload_legal0_carry__2_i_3_n_0,payload_legal0_carry__2_i_4_n_0}),
        .O(NLW_payload_legal0_carry__2_O_UNCONNECTED[3:0]),
        .S({payload_legal0_carry__2_i_5_n_0,payload_legal0_carry__2_i_6_n_0,payload_legal0_carry__2_i_7_n_0,payload_legal0_carry__2_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__2_i_1
       (.I0(cfg_period[31]),
        .I1(cfg_high_speed[31]),
        .I2(cfg_period[30]),
        .I3(cfg_high_speed[30]),
        .O(payload_legal0_carry__2_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__2_i_2
       (.I0(cfg_period[29]),
        .I1(cfg_high_speed[29]),
        .I2(cfg_period[28]),
        .I3(cfg_high_speed[28]),
        .O(payload_legal0_carry__2_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__2_i_3
       (.I0(cfg_period[27]),
        .I1(cfg_high_speed[27]),
        .I2(cfg_period[26]),
        .I3(cfg_high_speed[26]),
        .O(payload_legal0_carry__2_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry__2_i_4
       (.I0(cfg_period[25]),
        .I1(cfg_high_speed[25]),
        .I2(cfg_period[24]),
        .I3(cfg_high_speed[24]),
        .O(payload_legal0_carry__2_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__2_i_5
       (.I0(cfg_high_speed[31]),
        .I1(cfg_period[31]),
        .I2(cfg_high_speed[30]),
        .I3(cfg_period[30]),
        .O(payload_legal0_carry__2_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__2_i_6
       (.I0(cfg_high_speed[29]),
        .I1(cfg_period[29]),
        .I2(cfg_high_speed[28]),
        .I3(cfg_period[28]),
        .O(payload_legal0_carry__2_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__2_i_7
       (.I0(cfg_high_speed[27]),
        .I1(cfg_period[27]),
        .I2(cfg_high_speed[26]),
        .I3(cfg_period[26]),
        .O(payload_legal0_carry__2_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry__2_i_8
       (.I0(cfg_high_speed[25]),
        .I1(cfg_period[25]),
        .I2(cfg_high_speed[24]),
        .I3(cfg_period[24]),
        .O(payload_legal0_carry__2_i_8_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry_i_1
       (.I0(cfg_period[7]),
        .I1(cfg_high_speed[7]),
        .I2(cfg_period[6]),
        .I3(cfg_high_speed[6]),
        .O(payload_legal0_carry_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry_i_2
       (.I0(cfg_period[5]),
        .I1(cfg_high_speed[5]),
        .I2(cfg_period[4]),
        .I3(cfg_high_speed[4]),
        .O(payload_legal0_carry_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry_i_3
       (.I0(cfg_period[3]),
        .I1(cfg_high_speed[3]),
        .I2(cfg_period[2]),
        .I3(cfg_high_speed[2]),
        .O(payload_legal0_carry_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal0_carry_i_4
       (.I0(cfg_period[1]),
        .I1(cfg_high_speed[1]),
        .I2(cfg_period[0]),
        .I3(cfg_high_speed[0]),
        .O(payload_legal0_carry_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry_i_5
       (.I0(cfg_high_speed[7]),
        .I1(cfg_period[7]),
        .I2(cfg_high_speed[6]),
        .I3(cfg_period[6]),
        .O(payload_legal0_carry_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry_i_6
       (.I0(cfg_high_speed[5]),
        .I1(cfg_period[5]),
        .I2(cfg_high_speed[4]),
        .I3(cfg_period[4]),
        .O(payload_legal0_carry_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry_i_7
       (.I0(cfg_high_speed[3]),
        .I1(cfg_period[3]),
        .I2(cfg_high_speed[2]),
        .I3(cfg_period[2]),
        .O(payload_legal0_carry_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal0_carry_i_8
       (.I0(cfg_high_speed[1]),
        .I1(cfg_period[1]),
        .I2(cfg_high_speed[0]),
        .I3(cfg_period[0]),
        .O(payload_legal0_carry_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal1_carry
       (.CI(1'b0),
        .CO({payload_legal1_carry_n_0,payload_legal1_carry_n_1,payload_legal1_carry_n_2,payload_legal1_carry_n_3}),
        .CYINIT(1'b1),
        .DI({payload_legal1_carry_i_1_n_0,payload_legal1_carry_i_2_n_0,payload_legal1_carry_i_3_n_0,payload_legal1_carry_i_4_n_0}),
        .O(NLW_payload_legal1_carry_O_UNCONNECTED[3:0]),
        .S({payload_legal1_carry_i_5_n_0,payload_legal1_carry_i_6_n_0,payload_legal1_carry_i_7_n_0,payload_legal1_carry_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal1_carry__0
       (.CI(payload_legal1_carry_n_0),
        .CO({payload_legal1_carry__0_n_0,payload_legal1_carry__0_n_1,payload_legal1_carry__0_n_2,payload_legal1_carry__0_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal1_carry__0_i_1_n_0,payload_legal1_carry__0_i_2_n_0,payload_legal1_carry__0_i_3_n_0,payload_legal1_carry__0_i_4_n_0}),
        .O(NLW_payload_legal1_carry__0_O_UNCONNECTED[3:0]),
        .S({payload_legal1_carry__0_i_5_n_0,payload_legal1_carry__0_i_6_n_0,payload_legal1_carry__0_i_7_n_0,payload_legal1_carry__0_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__0_i_1
       (.I0(cfg_period[15]),
        .I1(cfg_high_pitch[15]),
        .I2(cfg_period[14]),
        .I3(cfg_high_pitch[14]),
        .O(payload_legal1_carry__0_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__0_i_2
       (.I0(cfg_period[13]),
        .I1(cfg_high_pitch[13]),
        .I2(cfg_period[12]),
        .I3(cfg_high_pitch[12]),
        .O(payload_legal1_carry__0_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__0_i_3
       (.I0(cfg_period[11]),
        .I1(cfg_high_pitch[11]),
        .I2(cfg_period[10]),
        .I3(cfg_high_pitch[10]),
        .O(payload_legal1_carry__0_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__0_i_4
       (.I0(cfg_period[9]),
        .I1(cfg_high_pitch[9]),
        .I2(cfg_period[8]),
        .I3(cfg_high_pitch[8]),
        .O(payload_legal1_carry__0_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__0_i_5
       (.I0(cfg_high_pitch[15]),
        .I1(cfg_period[15]),
        .I2(cfg_high_pitch[14]),
        .I3(cfg_period[14]),
        .O(payload_legal1_carry__0_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__0_i_6
       (.I0(cfg_high_pitch[13]),
        .I1(cfg_period[13]),
        .I2(cfg_high_pitch[12]),
        .I3(cfg_period[12]),
        .O(payload_legal1_carry__0_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__0_i_7
       (.I0(cfg_high_pitch[11]),
        .I1(cfg_period[11]),
        .I2(cfg_high_pitch[10]),
        .I3(cfg_period[10]),
        .O(payload_legal1_carry__0_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__0_i_8
       (.I0(cfg_high_pitch[9]),
        .I1(cfg_period[9]),
        .I2(cfg_high_pitch[8]),
        .I3(cfg_period[8]),
        .O(payload_legal1_carry__0_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal1_carry__1
       (.CI(payload_legal1_carry__0_n_0),
        .CO({payload_legal1_carry__1_n_0,payload_legal1_carry__1_n_1,payload_legal1_carry__1_n_2,payload_legal1_carry__1_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal1_carry__1_i_1_n_0,payload_legal1_carry__1_i_2_n_0,payload_legal1_carry__1_i_3_n_0,payload_legal1_carry__1_i_4_n_0}),
        .O(NLW_payload_legal1_carry__1_O_UNCONNECTED[3:0]),
        .S({payload_legal1_carry__1_i_5_n_0,payload_legal1_carry__1_i_6_n_0,payload_legal1_carry__1_i_7_n_0,payload_legal1_carry__1_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__1_i_1
       (.I0(cfg_period[23]),
        .I1(cfg_high_pitch[23]),
        .I2(cfg_period[22]),
        .I3(cfg_high_pitch[22]),
        .O(payload_legal1_carry__1_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__1_i_2
       (.I0(cfg_period[21]),
        .I1(cfg_high_pitch[21]),
        .I2(cfg_period[20]),
        .I3(cfg_high_pitch[20]),
        .O(payload_legal1_carry__1_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__1_i_3
       (.I0(cfg_period[19]),
        .I1(cfg_high_pitch[19]),
        .I2(cfg_period[18]),
        .I3(cfg_high_pitch[18]),
        .O(payload_legal1_carry__1_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__1_i_4
       (.I0(cfg_period[17]),
        .I1(cfg_high_pitch[17]),
        .I2(cfg_period[16]),
        .I3(cfg_high_pitch[16]),
        .O(payload_legal1_carry__1_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__1_i_5
       (.I0(cfg_high_pitch[23]),
        .I1(cfg_period[23]),
        .I2(cfg_high_pitch[22]),
        .I3(cfg_period[22]),
        .O(payload_legal1_carry__1_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__1_i_6
       (.I0(cfg_high_pitch[21]),
        .I1(cfg_period[21]),
        .I2(cfg_high_pitch[20]),
        .I3(cfg_period[20]),
        .O(payload_legal1_carry__1_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__1_i_7
       (.I0(cfg_high_pitch[19]),
        .I1(cfg_period[19]),
        .I2(cfg_high_pitch[18]),
        .I3(cfg_period[18]),
        .O(payload_legal1_carry__1_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__1_i_8
       (.I0(cfg_high_pitch[17]),
        .I1(cfg_period[17]),
        .I2(cfg_high_pitch[16]),
        .I3(cfg_period[16]),
        .O(payload_legal1_carry__1_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal1_carry__2
       (.CI(payload_legal1_carry__1_n_0),
        .CO({payload_legal1__15,payload_legal1_carry__2_n_1,payload_legal1_carry__2_n_2,payload_legal1_carry__2_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal1_carry__2_i_1_n_0,payload_legal1_carry__2_i_2_n_0,payload_legal1_carry__2_i_3_n_0,payload_legal1_carry__2_i_4_n_0}),
        .O(NLW_payload_legal1_carry__2_O_UNCONNECTED[3:0]),
        .S({payload_legal1_carry__2_i_5_n_0,payload_legal1_carry__2_i_6_n_0,payload_legal1_carry__2_i_7_n_0,payload_legal1_carry__2_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__2_i_1
       (.I0(cfg_period[31]),
        .I1(cfg_high_pitch[31]),
        .I2(cfg_period[30]),
        .I3(cfg_high_pitch[30]),
        .O(payload_legal1_carry__2_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__2_i_2
       (.I0(cfg_period[29]),
        .I1(cfg_high_pitch[29]),
        .I2(cfg_period[28]),
        .I3(cfg_high_pitch[28]),
        .O(payload_legal1_carry__2_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__2_i_3
       (.I0(cfg_period[27]),
        .I1(cfg_high_pitch[27]),
        .I2(cfg_period[26]),
        .I3(cfg_high_pitch[26]),
        .O(payload_legal1_carry__2_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry__2_i_4
       (.I0(cfg_period[25]),
        .I1(cfg_high_pitch[25]),
        .I2(cfg_period[24]),
        .I3(cfg_high_pitch[24]),
        .O(payload_legal1_carry__2_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__2_i_5
       (.I0(cfg_high_pitch[31]),
        .I1(cfg_period[31]),
        .I2(cfg_high_pitch[30]),
        .I3(cfg_period[30]),
        .O(payload_legal1_carry__2_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__2_i_6
       (.I0(cfg_high_pitch[29]),
        .I1(cfg_period[29]),
        .I2(cfg_high_pitch[28]),
        .I3(cfg_period[28]),
        .O(payload_legal1_carry__2_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__2_i_7
       (.I0(cfg_high_pitch[27]),
        .I1(cfg_period[27]),
        .I2(cfg_high_pitch[26]),
        .I3(cfg_period[26]),
        .O(payload_legal1_carry__2_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry__2_i_8
       (.I0(cfg_high_pitch[25]),
        .I1(cfg_period[25]),
        .I2(cfg_high_pitch[24]),
        .I3(cfg_period[24]),
        .O(payload_legal1_carry__2_i_8_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry_i_1
       (.I0(cfg_period[7]),
        .I1(cfg_high_pitch[7]),
        .I2(cfg_period[6]),
        .I3(cfg_high_pitch[6]),
        .O(payload_legal1_carry_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry_i_2
       (.I0(cfg_period[5]),
        .I1(cfg_high_pitch[5]),
        .I2(cfg_period[4]),
        .I3(cfg_high_pitch[4]),
        .O(payload_legal1_carry_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry_i_3
       (.I0(cfg_period[3]),
        .I1(cfg_high_pitch[3]),
        .I2(cfg_period[2]),
        .I3(cfg_high_pitch[2]),
        .O(payload_legal1_carry_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal1_carry_i_4
       (.I0(cfg_period[1]),
        .I1(cfg_high_pitch[1]),
        .I2(cfg_period[0]),
        .I3(cfg_high_pitch[0]),
        .O(payload_legal1_carry_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry_i_5
       (.I0(cfg_high_pitch[7]),
        .I1(cfg_period[7]),
        .I2(cfg_high_pitch[6]),
        .I3(cfg_period[6]),
        .O(payload_legal1_carry_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry_i_6
       (.I0(cfg_high_pitch[5]),
        .I1(cfg_period[5]),
        .I2(cfg_high_pitch[4]),
        .I3(cfg_period[4]),
        .O(payload_legal1_carry_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry_i_7
       (.I0(cfg_high_pitch[3]),
        .I1(cfg_period[3]),
        .I2(cfg_high_pitch[2]),
        .I3(cfg_period[2]),
        .O(payload_legal1_carry_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal1_carry_i_8
       (.I0(cfg_high_pitch[1]),
        .I1(cfg_period[1]),
        .I2(cfg_high_pitch[0]),
        .I3(cfg_period[0]),
        .O(payload_legal1_carry_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal2_carry
       (.CI(1'b0),
        .CO({payload_legal2_carry_n_0,payload_legal2_carry_n_1,payload_legal2_carry_n_2,payload_legal2_carry_n_3}),
        .CYINIT(1'b1),
        .DI({payload_legal2_carry_i_1_n_0,payload_legal2_carry_i_2_n_0,payload_legal2_carry_i_3_n_0,payload_legal2_carry_i_4_n_0}),
        .O(NLW_payload_legal2_carry_O_UNCONNECTED[3:0]),
        .S({payload_legal2_carry_i_5_n_0,payload_legal2_carry_i_6_n_0,payload_legal2_carry_i_7_n_0,payload_legal2_carry_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal2_carry__0
       (.CI(payload_legal2_carry_n_0),
        .CO({payload_legal2_carry__0_n_0,payload_legal2_carry__0_n_1,payload_legal2_carry__0_n_2,payload_legal2_carry__0_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal2_carry__0_i_1_n_0,payload_legal2_carry__0_i_2_n_0,payload_legal2_carry__0_i_3_n_0,payload_legal2_carry__0_i_4_n_0}),
        .O(NLW_payload_legal2_carry__0_O_UNCONNECTED[3:0]),
        .S({payload_legal2_carry__0_i_5_n_0,payload_legal2_carry__0_i_6_n_0,payload_legal2_carry__0_i_7_n_0,payload_legal2_carry__0_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__0_i_1
       (.I0(cfg_period[15]),
        .I1(cfg_high_yaw[15]),
        .I2(cfg_period[14]),
        .I3(cfg_high_yaw[14]),
        .O(payload_legal2_carry__0_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__0_i_2
       (.I0(cfg_period[13]),
        .I1(cfg_high_yaw[13]),
        .I2(cfg_period[12]),
        .I3(cfg_high_yaw[12]),
        .O(payload_legal2_carry__0_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__0_i_3
       (.I0(cfg_period[11]),
        .I1(cfg_high_yaw[11]),
        .I2(cfg_period[10]),
        .I3(cfg_high_yaw[10]),
        .O(payload_legal2_carry__0_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__0_i_4
       (.I0(cfg_period[9]),
        .I1(cfg_high_yaw[9]),
        .I2(cfg_period[8]),
        .I3(cfg_high_yaw[8]),
        .O(payload_legal2_carry__0_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__0_i_5
       (.I0(cfg_high_yaw[15]),
        .I1(cfg_period[15]),
        .I2(cfg_high_yaw[14]),
        .I3(cfg_period[14]),
        .O(payload_legal2_carry__0_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__0_i_6
       (.I0(cfg_high_yaw[13]),
        .I1(cfg_period[13]),
        .I2(cfg_high_yaw[12]),
        .I3(cfg_period[12]),
        .O(payload_legal2_carry__0_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__0_i_7
       (.I0(cfg_high_yaw[11]),
        .I1(cfg_period[11]),
        .I2(cfg_high_yaw[10]),
        .I3(cfg_period[10]),
        .O(payload_legal2_carry__0_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__0_i_8
       (.I0(cfg_high_yaw[9]),
        .I1(cfg_period[9]),
        .I2(cfg_high_yaw[8]),
        .I3(cfg_period[8]),
        .O(payload_legal2_carry__0_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal2_carry__1
       (.CI(payload_legal2_carry__0_n_0),
        .CO({payload_legal2_carry__1_n_0,payload_legal2_carry__1_n_1,payload_legal2_carry__1_n_2,payload_legal2_carry__1_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal2_carry__1_i_1_n_0,payload_legal2_carry__1_i_2_n_0,payload_legal2_carry__1_i_3_n_0,payload_legal2_carry__1_i_4_n_0}),
        .O(NLW_payload_legal2_carry__1_O_UNCONNECTED[3:0]),
        .S({payload_legal2_carry__1_i_5_n_0,payload_legal2_carry__1_i_6_n_0,payload_legal2_carry__1_i_7_n_0,payload_legal2_carry__1_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__1_i_1
       (.I0(cfg_period[23]),
        .I1(cfg_high_yaw[23]),
        .I2(cfg_period[22]),
        .I3(cfg_high_yaw[22]),
        .O(payload_legal2_carry__1_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__1_i_2
       (.I0(cfg_period[21]),
        .I1(cfg_high_yaw[21]),
        .I2(cfg_period[20]),
        .I3(cfg_high_yaw[20]),
        .O(payload_legal2_carry__1_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__1_i_3
       (.I0(cfg_period[19]),
        .I1(cfg_high_yaw[19]),
        .I2(cfg_period[18]),
        .I3(cfg_high_yaw[18]),
        .O(payload_legal2_carry__1_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__1_i_4
       (.I0(cfg_period[17]),
        .I1(cfg_high_yaw[17]),
        .I2(cfg_period[16]),
        .I3(cfg_high_yaw[16]),
        .O(payload_legal2_carry__1_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__1_i_5
       (.I0(cfg_high_yaw[23]),
        .I1(cfg_period[23]),
        .I2(cfg_high_yaw[22]),
        .I3(cfg_period[22]),
        .O(payload_legal2_carry__1_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__1_i_6
       (.I0(cfg_high_yaw[21]),
        .I1(cfg_period[21]),
        .I2(cfg_high_yaw[20]),
        .I3(cfg_period[20]),
        .O(payload_legal2_carry__1_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__1_i_7
       (.I0(cfg_high_yaw[19]),
        .I1(cfg_period[19]),
        .I2(cfg_high_yaw[18]),
        .I3(cfg_period[18]),
        .O(payload_legal2_carry__1_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__1_i_8
       (.I0(cfg_high_yaw[17]),
        .I1(cfg_period[17]),
        .I2(cfg_high_yaw[16]),
        .I3(cfg_period[16]),
        .O(payload_legal2_carry__1_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 payload_legal2_carry__2
       (.CI(payload_legal2_carry__1_n_0),
        .CO({payload_legal2__15,payload_legal2_carry__2_n_1,payload_legal2_carry__2_n_2,payload_legal2_carry__2_n_3}),
        .CYINIT(1'b0),
        .DI({payload_legal2_carry__2_i_1_n_0,payload_legal2_carry__2_i_2_n_0,payload_legal2_carry__2_i_3_n_0,payload_legal2_carry__2_i_4_n_0}),
        .O(NLW_payload_legal2_carry__2_O_UNCONNECTED[3:0]),
        .S({payload_legal2_carry__2_i_5_n_0,payload_legal2_carry__2_i_6_n_0,payload_legal2_carry__2_i_7_n_0,payload_legal2_carry__2_i_8_n_0}));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__2_i_1
       (.I0(cfg_period[31]),
        .I1(cfg_high_yaw[31]),
        .I2(cfg_period[30]),
        .I3(cfg_high_yaw[30]),
        .O(payload_legal2_carry__2_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__2_i_2
       (.I0(cfg_period[29]),
        .I1(cfg_high_yaw[29]),
        .I2(cfg_period[28]),
        .I3(cfg_high_yaw[28]),
        .O(payload_legal2_carry__2_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__2_i_3
       (.I0(cfg_period[27]),
        .I1(cfg_high_yaw[27]),
        .I2(cfg_period[26]),
        .I3(cfg_high_yaw[26]),
        .O(payload_legal2_carry__2_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry__2_i_4
       (.I0(cfg_period[25]),
        .I1(cfg_high_yaw[25]),
        .I2(cfg_period[24]),
        .I3(cfg_high_yaw[24]),
        .O(payload_legal2_carry__2_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__2_i_5
       (.I0(cfg_high_yaw[31]),
        .I1(cfg_period[31]),
        .I2(cfg_high_yaw[30]),
        .I3(cfg_period[30]),
        .O(payload_legal2_carry__2_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__2_i_6
       (.I0(cfg_high_yaw[29]),
        .I1(cfg_period[29]),
        .I2(cfg_high_yaw[28]),
        .I3(cfg_period[28]),
        .O(payload_legal2_carry__2_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__2_i_7
       (.I0(cfg_high_yaw[27]),
        .I1(cfg_period[27]),
        .I2(cfg_high_yaw[26]),
        .I3(cfg_period[26]),
        .O(payload_legal2_carry__2_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry__2_i_8
       (.I0(cfg_high_yaw[25]),
        .I1(cfg_period[25]),
        .I2(cfg_high_yaw[24]),
        .I3(cfg_period[24]),
        .O(payload_legal2_carry__2_i_8_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry_i_1
       (.I0(cfg_period[7]),
        .I1(cfg_high_yaw[7]),
        .I2(cfg_period[6]),
        .I3(cfg_high_yaw[6]),
        .O(payload_legal2_carry_i_1_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry_i_2
       (.I0(cfg_period[5]),
        .I1(cfg_high_yaw[5]),
        .I2(cfg_period[4]),
        .I3(cfg_high_yaw[4]),
        .O(payload_legal2_carry_i_2_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry_i_3
       (.I0(cfg_period[3]),
        .I1(cfg_high_yaw[3]),
        .I2(cfg_period[2]),
        .I3(cfg_high_yaw[2]),
        .O(payload_legal2_carry_i_3_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    payload_legal2_carry_i_4
       (.I0(cfg_period[1]),
        .I1(cfg_high_yaw[1]),
        .I2(cfg_period[0]),
        .I3(cfg_high_yaw[0]),
        .O(payload_legal2_carry_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry_i_5
       (.I0(cfg_high_yaw[7]),
        .I1(cfg_period[7]),
        .I2(cfg_high_yaw[6]),
        .I3(cfg_period[6]),
        .O(payload_legal2_carry_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry_i_6
       (.I0(cfg_high_yaw[5]),
        .I1(cfg_period[5]),
        .I2(cfg_high_yaw[4]),
        .I3(cfg_period[4]),
        .O(payload_legal2_carry_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry_i_7
       (.I0(cfg_high_yaw[3]),
        .I1(cfg_period[3]),
        .I2(cfg_high_yaw[2]),
        .I3(cfg_period[2]),
        .O(payload_legal2_carry_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    payload_legal2_carry_i_8
       (.I0(cfg_high_yaw[1]),
        .I1(cfg_period[1]),
        .I2(cfg_high_yaw[0]),
        .I3(cfg_period[0]),
        .O(payload_legal2_carry_i_8_n_0));
  FDRE \pending_high_pitch_q_reg[0] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[0]),
        .Q(pending_high_pitch_q[0]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[10] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[10]),
        .Q(pending_high_pitch_q[10]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[11] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[11]),
        .Q(pending_high_pitch_q[11]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[12] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[12]),
        .Q(pending_high_pitch_q[12]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[13] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[13]),
        .Q(pending_high_pitch_q[13]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[14] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[14]),
        .Q(pending_high_pitch_q[14]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[15] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[15]),
        .Q(pending_high_pitch_q[15]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[16] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[16]),
        .Q(pending_high_pitch_q[16]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[17] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[17]),
        .Q(pending_high_pitch_q[17]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[18] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[18]),
        .Q(pending_high_pitch_q[18]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[19] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[19]),
        .Q(pending_high_pitch_q[19]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[1] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[1]),
        .Q(pending_high_pitch_q[1]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[20] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[20]),
        .Q(pending_high_pitch_q[20]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[21] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[21]),
        .Q(pending_high_pitch_q[21]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[22] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[22]),
        .Q(pending_high_pitch_q[22]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[23] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[23]),
        .Q(pending_high_pitch_q[23]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[24] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[24]),
        .Q(pending_high_pitch_q[24]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[25] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[25]),
        .Q(pending_high_pitch_q[25]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[26] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[26]),
        .Q(pending_high_pitch_q[26]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[27] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[27]),
        .Q(pending_high_pitch_q[27]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[28] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[28]),
        .Q(pending_high_pitch_q[28]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[29] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[29]),
        .Q(pending_high_pitch_q[29]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[2] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[2]),
        .Q(pending_high_pitch_q[2]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[30] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[30]),
        .Q(pending_high_pitch_q[30]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[31] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[31]),
        .Q(pending_high_pitch_q[31]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[3] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[3]),
        .Q(pending_high_pitch_q[3]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[4] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[4]),
        .Q(pending_high_pitch_q[4]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[5] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[5]),
        .Q(pending_high_pitch_q[5]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[6] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[6]),
        .Q(pending_high_pitch_q[6]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[7] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[7]),
        .Q(pending_high_pitch_q[7]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[8] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[8]),
        .Q(pending_high_pitch_q[8]),
        .R(pending_tag_q));
  FDRE \pending_high_pitch_q_reg[9] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_pitch[9]),
        .Q(pending_high_pitch_q[9]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[0] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[0]),
        .Q(pending_high_speed_q[0]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[10] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[10]),
        .Q(pending_high_speed_q[10]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[11] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[11]),
        .Q(pending_high_speed_q[11]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[12] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[12]),
        .Q(pending_high_speed_q[12]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[13] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[13]),
        .Q(pending_high_speed_q[13]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[14] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[14]),
        .Q(pending_high_speed_q[14]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[15] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[15]),
        .Q(pending_high_speed_q[15]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[16] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[16]),
        .Q(pending_high_speed_q[16]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[17] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[17]),
        .Q(pending_high_speed_q[17]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[18] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[18]),
        .Q(pending_high_speed_q[18]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[19] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[19]),
        .Q(pending_high_speed_q[19]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[1] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[1]),
        .Q(pending_high_speed_q[1]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[20] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[20]),
        .Q(pending_high_speed_q[20]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[21] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[21]),
        .Q(pending_high_speed_q[21]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[22] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[22]),
        .Q(pending_high_speed_q[22]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[23] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[23]),
        .Q(pending_high_speed_q[23]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[24] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[24]),
        .Q(pending_high_speed_q[24]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[25] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[25]),
        .Q(pending_high_speed_q[25]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[26] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[26]),
        .Q(pending_high_speed_q[26]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[27] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[27]),
        .Q(pending_high_speed_q[27]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[28] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[28]),
        .Q(pending_high_speed_q[28]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[29] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[29]),
        .Q(pending_high_speed_q[29]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[2] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[2]),
        .Q(pending_high_speed_q[2]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[30] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[30]),
        .Q(pending_high_speed_q[30]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[31] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[31]),
        .Q(pending_high_speed_q[31]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[3] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[3]),
        .Q(pending_high_speed_q[3]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[4] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[4]),
        .Q(pending_high_speed_q[4]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[5] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[5]),
        .Q(pending_high_speed_q[5]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[6] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[6]),
        .Q(pending_high_speed_q[6]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[7] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[7]),
        .Q(pending_high_speed_q[7]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[8] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[8]),
        .Q(pending_high_speed_q[8]),
        .R(pending_tag_q));
  FDRE \pending_high_speed_q_reg[9] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_speed[9]),
        .Q(pending_high_speed_q[9]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[0] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[0]),
        .Q(pending_high_yaw_q[0]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[10] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[10]),
        .Q(pending_high_yaw_q[10]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[11] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[11]),
        .Q(pending_high_yaw_q[11]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[12] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[12]),
        .Q(pending_high_yaw_q[12]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[13] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[13]),
        .Q(pending_high_yaw_q[13]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[14] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[14]),
        .Q(pending_high_yaw_q[14]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[15] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[15]),
        .Q(pending_high_yaw_q[15]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[16] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[16]),
        .Q(pending_high_yaw_q[16]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[17] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[17]),
        .Q(pending_high_yaw_q[17]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[18] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[18]),
        .Q(pending_high_yaw_q[18]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[19] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[19]),
        .Q(pending_high_yaw_q[19]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[1] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[1]),
        .Q(pending_high_yaw_q[1]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[20] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[20]),
        .Q(pending_high_yaw_q[20]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[21] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[21]),
        .Q(pending_high_yaw_q[21]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[22] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[22]),
        .Q(pending_high_yaw_q[22]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[23] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[23]),
        .Q(pending_high_yaw_q[23]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[24] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[24]),
        .Q(pending_high_yaw_q[24]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[25] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[25]),
        .Q(pending_high_yaw_q[25]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[26] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[26]),
        .Q(pending_high_yaw_q[26]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[27] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[27]),
        .Q(pending_high_yaw_q[27]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[28] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[28]),
        .Q(pending_high_yaw_q[28]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[29] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[29]),
        .Q(pending_high_yaw_q[29]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[2] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[2]),
        .Q(pending_high_yaw_q[2]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[30] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[30]),
        .Q(pending_high_yaw_q[30]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[31] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[31]),
        .Q(pending_high_yaw_q[31]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[3] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[3]),
        .Q(pending_high_yaw_q[3]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[4] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[4]),
        .Q(pending_high_yaw_q[4]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[5] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[5]),
        .Q(pending_high_yaw_q[5]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[6] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[6]),
        .Q(pending_high_yaw_q[6]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[7] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[7]),
        .Q(pending_high_yaw_q[7]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[8] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[8]),
        .Q(pending_high_yaw_q[8]),
        .R(pending_tag_q));
  FDRE \pending_high_yaw_q_reg[9] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_high_yaw[9]),
        .Q(pending_high_yaw_q[9]),
        .R(pending_tag_q));
  LUT5 #(
    .INIT(32'hFEEEFEFE)) 
    \pending_period_q[31]_i_1 
       (.I0(stop),
        .I1(rst),
        .I2(pending_q_reg_0),
        .I3(boundary_now0__10),
        .I4(running_q_reg_0),
        .O(pending_tag_q));
  FDRE \pending_period_q_reg[0] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[0]),
        .Q(\pending_period_q_reg_n_0_[0] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[10] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[10]),
        .Q(\pending_period_q_reg_n_0_[10] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[11] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[11]),
        .Q(\pending_period_q_reg_n_0_[11] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[12] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[12]),
        .Q(\pending_period_q_reg_n_0_[12] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[13] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[13]),
        .Q(\pending_period_q_reg_n_0_[13] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[14] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[14]),
        .Q(\pending_period_q_reg_n_0_[14] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[15] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[15]),
        .Q(\pending_period_q_reg_n_0_[15] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[16] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[16]),
        .Q(\pending_period_q_reg_n_0_[16] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[17] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[17]),
        .Q(\pending_period_q_reg_n_0_[17] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[18] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[18]),
        .Q(\pending_period_q_reg_n_0_[18] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[19] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[19]),
        .Q(\pending_period_q_reg_n_0_[19] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[1] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[1]),
        .Q(\pending_period_q_reg_n_0_[1] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[20] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[20]),
        .Q(\pending_period_q_reg_n_0_[20] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[21] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[21]),
        .Q(\pending_period_q_reg_n_0_[21] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[22] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[22]),
        .Q(\pending_period_q_reg_n_0_[22] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[23] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[23]),
        .Q(\pending_period_q_reg_n_0_[23] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[24] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[24]),
        .Q(\pending_period_q_reg_n_0_[24] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[25] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[25]),
        .Q(\pending_period_q_reg_n_0_[25] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[26] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[26]),
        .Q(\pending_period_q_reg_n_0_[26] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[27] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[27]),
        .Q(\pending_period_q_reg_n_0_[27] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[28] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[28]),
        .Q(\pending_period_q_reg_n_0_[28] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[29] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[29]),
        .Q(\pending_period_q_reg_n_0_[29] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[2] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[2]),
        .Q(\pending_period_q_reg_n_0_[2] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[30] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[30]),
        .Q(\pending_period_q_reg_n_0_[30] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[31] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[31]),
        .Q(\pending_period_q_reg_n_0_[31] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[3] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[3]),
        .Q(\pending_period_q_reg_n_0_[3] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[4] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[4]),
        .Q(\pending_period_q_reg_n_0_[4] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[5] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[5]),
        .Q(\pending_period_q_reg_n_0_[5] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[6] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[6]),
        .Q(\pending_period_q_reg_n_0_[6] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[7] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[7]),
        .Q(\pending_period_q_reg_n_0_[7] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[8] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[8]),
        .Q(\pending_period_q_reg_n_0_[8] ),
        .R(pending_tag_q));
  FDRE \pending_period_q_reg[9] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_period[9]),
        .Q(\pending_period_q_reg_n_0_[9] ),
        .R(pending_tag_q));
  LUT6 #(
    .INIT(64'h0111010100100000)) 
    pending_q_i_1
       (.I0(stop),
        .I1(rst),
        .I2(pending_q_reg_0),
        .I3(boundary_now0__10),
        .I4(running_q_reg_0),
        .I5(rejected_q),
        .O(pending_q_i_1_n_0));
  FDRE pending_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(pending_q_i_1_n_0),
        .Q(pending_q_reg_0),
        .R(1'b0));
  FDRE \pending_tag_q_reg[0] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[0]),
        .Q(\pending_tag_q_reg_n_0_[0] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[10] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[10]),
        .Q(\pending_tag_q_reg_n_0_[10] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[11] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[11]),
        .Q(\pending_tag_q_reg_n_0_[11] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[12] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[12]),
        .Q(\pending_tag_q_reg_n_0_[12] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[13] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[13]),
        .Q(\pending_tag_q_reg_n_0_[13] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[14] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[14]),
        .Q(\pending_tag_q_reg_n_0_[14] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[15] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[15]),
        .Q(\pending_tag_q_reg_n_0_[15] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[16] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[16]),
        .Q(\pending_tag_q_reg_n_0_[16] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[17] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[17]),
        .Q(\pending_tag_q_reg_n_0_[17] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[18] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[18]),
        .Q(\pending_tag_q_reg_n_0_[18] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[19] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[19]),
        .Q(\pending_tag_q_reg_n_0_[19] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[1] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[1]),
        .Q(\pending_tag_q_reg_n_0_[1] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[20] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[20]),
        .Q(\pending_tag_q_reg_n_0_[20] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[21] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[21]),
        .Q(\pending_tag_q_reg_n_0_[21] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[22] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[22]),
        .Q(\pending_tag_q_reg_n_0_[22] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[23] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[23]),
        .Q(\pending_tag_q_reg_n_0_[23] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[24] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[24]),
        .Q(\pending_tag_q_reg_n_0_[24] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[25] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[25]),
        .Q(\pending_tag_q_reg_n_0_[25] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[26] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[26]),
        .Q(\pending_tag_q_reg_n_0_[26] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[27] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[27]),
        .Q(\pending_tag_q_reg_n_0_[27] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[28] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[28]),
        .Q(\pending_tag_q_reg_n_0_[28] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[29] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[29]),
        .Q(\pending_tag_q_reg_n_0_[29] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[2] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[2]),
        .Q(\pending_tag_q_reg_n_0_[2] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[30] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[30]),
        .Q(\pending_tag_q_reg_n_0_[30] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[31] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[31]),
        .Q(\pending_tag_q_reg_n_0_[31] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[3] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[3]),
        .Q(\pending_tag_q_reg_n_0_[3] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[4] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[4]),
        .Q(\pending_tag_q_reg_n_0_[4] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[5] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[5]),
        .Q(\pending_tag_q_reg_n_0_[5] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[6] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[6]),
        .Q(\pending_tag_q_reg_n_0_[6] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[7] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[7]),
        .Q(\pending_tag_q_reg_n_0_[7] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[8] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[8]),
        .Q(\pending_tag_q_reg_n_0_[8] ),
        .R(pending_tag_q));
  FDRE \pending_tag_q_reg[9] 
       (.C(clk),
        .CE(rejected_q),
        .D(cfg_tag[9]),
        .Q(\pending_tag_q_reg_n_0_[9] ),
        .R(pending_tag_q));
  LUT4 #(
    .INIT(16'hFFEF)) 
    \phase_q[0]_i_1 
       (.I0(stop),
        .I1(rst),
        .I2(running_q_reg_0),
        .I3(boundary_now0__10),
        .O(\phase_q[0]_i_1_n_0 ));
  LUT1 #(
    .INIT(2'h1)) 
    \phase_q[0]_i_3 
       (.I0(phase_q_reg[0]),
        .O(\phase_q[0]_i_3_n_0 ));
  FDRE \phase_q_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[0]_i_2_n_7 ),
        .Q(phase_q_reg[0]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[0]_i_2 
       (.CI(1'b0),
        .CO({\phase_q_reg[0]_i_2_n_0 ,\phase_q_reg[0]_i_2_n_1 ,\phase_q_reg[0]_i_2_n_2 ,\phase_q_reg[0]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b1}),
        .O({\phase_q_reg[0]_i_2_n_4 ,\phase_q_reg[0]_i_2_n_5 ,\phase_q_reg[0]_i_2_n_6 ,\phase_q_reg[0]_i_2_n_7 }),
        .S({phase_q_reg[3:1],\phase_q[0]_i_3_n_0 }));
  FDRE \phase_q_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[8]_i_1_n_5 ),
        .Q(phase_q_reg[10]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[8]_i_1_n_4 ),
        .Q(phase_q_reg[11]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[12]_i_1_n_7 ),
        .Q(phase_q_reg[12]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[12]_i_1 
       (.CI(\phase_q_reg[8]_i_1_n_0 ),
        .CO({\phase_q_reg[12]_i_1_n_0 ,\phase_q_reg[12]_i_1_n_1 ,\phase_q_reg[12]_i_1_n_2 ,\phase_q_reg[12]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[12]_i_1_n_4 ,\phase_q_reg[12]_i_1_n_5 ,\phase_q_reg[12]_i_1_n_6 ,\phase_q_reg[12]_i_1_n_7 }),
        .S(phase_q_reg[15:12]));
  FDRE \phase_q_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[12]_i_1_n_6 ),
        .Q(phase_q_reg[13]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[12]_i_1_n_5 ),
        .Q(phase_q_reg[14]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[12]_i_1_n_4 ),
        .Q(phase_q_reg[15]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[16]_i_1_n_7 ),
        .Q(phase_q_reg[16]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[16]_i_1 
       (.CI(\phase_q_reg[12]_i_1_n_0 ),
        .CO({\phase_q_reg[16]_i_1_n_0 ,\phase_q_reg[16]_i_1_n_1 ,\phase_q_reg[16]_i_1_n_2 ,\phase_q_reg[16]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[16]_i_1_n_4 ,\phase_q_reg[16]_i_1_n_5 ,\phase_q_reg[16]_i_1_n_6 ,\phase_q_reg[16]_i_1_n_7 }),
        .S(phase_q_reg[19:16]));
  FDRE \phase_q_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[16]_i_1_n_6 ),
        .Q(phase_q_reg[17]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[16]_i_1_n_5 ),
        .Q(phase_q_reg[18]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[16]_i_1_n_4 ),
        .Q(phase_q_reg[19]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[0]_i_2_n_6 ),
        .Q(phase_q_reg[1]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[20]_i_1_n_7 ),
        .Q(phase_q_reg[20]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[20]_i_1 
       (.CI(\phase_q_reg[16]_i_1_n_0 ),
        .CO({\phase_q_reg[20]_i_1_n_0 ,\phase_q_reg[20]_i_1_n_1 ,\phase_q_reg[20]_i_1_n_2 ,\phase_q_reg[20]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[20]_i_1_n_4 ,\phase_q_reg[20]_i_1_n_5 ,\phase_q_reg[20]_i_1_n_6 ,\phase_q_reg[20]_i_1_n_7 }),
        .S(phase_q_reg[23:20]));
  FDRE \phase_q_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[20]_i_1_n_6 ),
        .Q(phase_q_reg[21]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[20]_i_1_n_5 ),
        .Q(phase_q_reg[22]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[20]_i_1_n_4 ),
        .Q(phase_q_reg[23]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[24]_i_1_n_7 ),
        .Q(phase_q_reg[24]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[24]_i_1 
       (.CI(\phase_q_reg[20]_i_1_n_0 ),
        .CO({\phase_q_reg[24]_i_1_n_0 ,\phase_q_reg[24]_i_1_n_1 ,\phase_q_reg[24]_i_1_n_2 ,\phase_q_reg[24]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[24]_i_1_n_4 ,\phase_q_reg[24]_i_1_n_5 ,\phase_q_reg[24]_i_1_n_6 ,\phase_q_reg[24]_i_1_n_7 }),
        .S(phase_q_reg[27:24]));
  FDRE \phase_q_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[24]_i_1_n_6 ),
        .Q(phase_q_reg[25]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[24]_i_1_n_5 ),
        .Q(phase_q_reg[26]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[24]_i_1_n_4 ),
        .Q(phase_q_reg[27]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[28]_i_1_n_7 ),
        .Q(phase_q_reg[28]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[28]_i_1 
       (.CI(\phase_q_reg[24]_i_1_n_0 ),
        .CO({\NLW_phase_q_reg[28]_i_1_CO_UNCONNECTED [3],\phase_q_reg[28]_i_1_n_1 ,\phase_q_reg[28]_i_1_n_2 ,\phase_q_reg[28]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[28]_i_1_n_4 ,\phase_q_reg[28]_i_1_n_5 ,\phase_q_reg[28]_i_1_n_6 ,\phase_q_reg[28]_i_1_n_7 }),
        .S(phase_q_reg[31:28]));
  FDRE \phase_q_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[28]_i_1_n_6 ),
        .Q(phase_q_reg[29]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[0]_i_2_n_5 ),
        .Q(phase_q_reg[2]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[30] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[28]_i_1_n_5 ),
        .Q(phase_q_reg[30]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[31] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[28]_i_1_n_4 ),
        .Q(phase_q_reg[31]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[0]_i_2_n_4 ),
        .Q(phase_q_reg[3]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[4]_i_1_n_7 ),
        .Q(phase_q_reg[4]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[4]_i_1 
       (.CI(\phase_q_reg[0]_i_2_n_0 ),
        .CO({\phase_q_reg[4]_i_1_n_0 ,\phase_q_reg[4]_i_1_n_1 ,\phase_q_reg[4]_i_1_n_2 ,\phase_q_reg[4]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[4]_i_1_n_4 ,\phase_q_reg[4]_i_1_n_5 ,\phase_q_reg[4]_i_1_n_6 ,\phase_q_reg[4]_i_1_n_7 }),
        .S(phase_q_reg[7:4]));
  FDRE \phase_q_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[4]_i_1_n_6 ),
        .Q(phase_q_reg[5]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[4]_i_1_n_5 ),
        .Q(phase_q_reg[6]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[4]_i_1_n_4 ),
        .Q(phase_q_reg[7]),
        .R(\phase_q[0]_i_1_n_0 ));
  FDRE \phase_q_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[8]_i_1_n_7 ),
        .Q(phase_q_reg[8]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \phase_q_reg[8]_i_1 
       (.CI(\phase_q_reg[4]_i_1_n_0 ),
        .CO({\phase_q_reg[8]_i_1_n_0 ,\phase_q_reg[8]_i_1_n_1 ,\phase_q_reg[8]_i_1_n_2 ,\phase_q_reg[8]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\phase_q_reg[8]_i_1_n_4 ,\phase_q_reg[8]_i_1_n_5 ,\phase_q_reg[8]_i_1_n_6 ,\phase_q_reg[8]_i_1_n_7 }),
        .S(phase_q_reg[11:8]));
  FDRE \phase_q_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\phase_q_reg[8]_i_1_n_6 ),
        .Q(phase_q_reg[9]),
        .R(\phase_q[0]_i_1_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 pwm_q0_carry
       (.CI(1'b0),
        .CO({pwm_q0_carry_n_0,pwm_q0_carry_n_1,pwm_q0_carry_n_2,pwm_q0_carry_n_3}),
        .CYINIT(1'b0),
        .DI({pwm_q0_carry_i_1_n_0,pwm_q0_carry_i_2_n_0,pwm_q0_carry_i_3_n_0,pwm_q0_carry_i_4_n_0}),
        .O(NLW_pwm_q0_carry_O_UNCONNECTED[3:0]),
        .S({pwm_q0_carry_i_5_n_0,pwm_q0_carry_i_6_n_0,pwm_q0_carry_i_7_n_0,pwm_q0_carry_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 pwm_q0_carry__0
       (.CI(pwm_q0_carry_n_0),
        .CO({pwm_q0_carry__0_n_0,pwm_q0_carry__0_n_1,pwm_q0_carry__0_n_2,pwm_q0_carry__0_n_3}),
        .CYINIT(1'b0),
        .DI({pwm_q0_carry__0_i_1_n_0,pwm_q0_carry__0_i_2_n_0,pwm_q0_carry__0_i_3_n_0,pwm_q0_carry__0_i_4_n_0}),
        .O(NLW_pwm_q0_carry__0_O_UNCONNECTED[3:0]),
        .S({pwm_q0_carry__0_i_5_n_0,pwm_q0_carry__0_i_6_n_0,pwm_q0_carry__0_i_7_n_0,pwm_q0_carry__0_i_8_n_0}));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__0_i_1
       (.I0(boundary_now0_carry__0_i_7_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [15]),
        .I2(\active_high_yaw_q_reg[31]_0 [14]),
        .I3(boundary_now0_carry__0_i_7_n_6),
        .O(pwm_q0_carry__0_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__0_i_2
       (.I0(boundary_now0_carry__0_i_7_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [13]),
        .I2(\active_high_yaw_q_reg[31]_0 [12]),
        .I3(boundary_now0_carry_i_5_n_4),
        .O(pwm_q0_carry__0_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__0_i_3
       (.I0(boundary_now0_carry_i_5_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [11]),
        .I2(\active_high_yaw_q_reg[31]_0 [10]),
        .I3(boundary_now0_carry_i_5_n_6),
        .O(pwm_q0_carry__0_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__0_i_4
       (.I0(boundary_now0_carry_i_5_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [9]),
        .I2(\active_high_yaw_q_reg[31]_0 [8]),
        .I3(boundary_now0_carry_i_6_n_4),
        .O(pwm_q0_carry__0_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__0_i_5
       (.I0(\active_high_yaw_q_reg[31]_0 [15]),
        .I1(boundary_now0_carry__0_i_7_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [14]),
        .I3(boundary_now0_carry__0_i_7_n_6),
        .O(pwm_q0_carry__0_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__0_i_6
       (.I0(\active_high_yaw_q_reg[31]_0 [13]),
        .I1(boundary_now0_carry__0_i_7_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [12]),
        .I3(boundary_now0_carry_i_5_n_4),
        .O(pwm_q0_carry__0_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__0_i_7
       (.I0(\active_high_yaw_q_reg[31]_0 [11]),
        .I1(boundary_now0_carry_i_5_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [10]),
        .I3(boundary_now0_carry_i_5_n_6),
        .O(pwm_q0_carry__0_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__0_i_8
       (.I0(\active_high_yaw_q_reg[31]_0 [9]),
        .I1(boundary_now0_carry_i_5_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [8]),
        .I3(boundary_now0_carry_i_6_n_4),
        .O(pwm_q0_carry__0_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 pwm_q0_carry__1
       (.CI(pwm_q0_carry__0_n_0),
        .CO({pwm_q0_carry__1_n_0,pwm_q0_carry__1_n_1,pwm_q0_carry__1_n_2,pwm_q0_carry__1_n_3}),
        .CYINIT(1'b0),
        .DI({pwm_q0_carry__1_i_1_n_0,pwm_q0_carry__1_i_2_n_0,pwm_q0_carry__1_i_3_n_0,pwm_q0_carry__1_i_4_n_0}),
        .O(NLW_pwm_q0_carry__1_O_UNCONNECTED[3:0]),
        .S({pwm_q0_carry__1_i_5_n_0,pwm_q0_carry__1_i_6_n_0,pwm_q0_carry__1_i_7_n_0,pwm_q0_carry__1_i_8_n_0}));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__1_i_1
       (.I0(boundary_now0_carry__0_i_5_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [23]),
        .I2(\active_high_yaw_q_reg[31]_0 [22]),
        .I3(boundary_now0_carry__0_i_5_n_6),
        .O(pwm_q0_carry__1_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__1_i_2
       (.I0(boundary_now0_carry__0_i_5_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [21]),
        .I2(\active_high_yaw_q_reg[31]_0 [20]),
        .I3(boundary_now0_carry__0_i_6_n_4),
        .O(pwm_q0_carry__1_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__1_i_3
       (.I0(boundary_now0_carry__0_i_6_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [19]),
        .I2(\active_high_yaw_q_reg[31]_0 [18]),
        .I3(boundary_now0_carry__0_i_6_n_6),
        .O(pwm_q0_carry__1_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__1_i_4
       (.I0(boundary_now0_carry__0_i_6_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [17]),
        .I2(\active_high_yaw_q_reg[31]_0 [16]),
        .I3(boundary_now0_carry__0_i_7_n_4),
        .O(pwm_q0_carry__1_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__1_i_5
       (.I0(\active_high_yaw_q_reg[31]_0 [23]),
        .I1(boundary_now0_carry__0_i_5_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [22]),
        .I3(boundary_now0_carry__0_i_5_n_6),
        .O(pwm_q0_carry__1_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__1_i_6
       (.I0(\active_high_yaw_q_reg[31]_0 [21]),
        .I1(boundary_now0_carry__0_i_5_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [20]),
        .I3(boundary_now0_carry__0_i_6_n_4),
        .O(pwm_q0_carry__1_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__1_i_7
       (.I0(\active_high_yaw_q_reg[31]_0 [19]),
        .I1(boundary_now0_carry__0_i_6_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [18]),
        .I3(boundary_now0_carry__0_i_6_n_6),
        .O(pwm_q0_carry__1_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__1_i_8
       (.I0(\active_high_yaw_q_reg[31]_0 [17]),
        .I1(boundary_now0_carry__0_i_6_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [16]),
        .I3(boundary_now0_carry__0_i_7_n_4),
        .O(pwm_q0_carry__1_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 pwm_q0_carry__2
       (.CI(pwm_q0_carry__1_n_0),
        .CO({p_0_in[0],pwm_q0_carry__2_n_1,pwm_q0_carry__2_n_2,pwm_q0_carry__2_n_3}),
        .CYINIT(1'b0),
        .DI({pwm_q0_carry__2_i_1_n_0,pwm_q0_carry__2_i_2_n_0,pwm_q0_carry__2_i_3_n_0,pwm_q0_carry__2_i_4_n_0}),
        .O(NLW_pwm_q0_carry__2_O_UNCONNECTED[3:0]),
        .S({pwm_q0_carry__2_i_5_n_0,pwm_q0_carry__2_i_6_n_0,pwm_q0_carry__2_i_7_n_0,pwm_q0_carry__2_i_8_n_0}));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__2_i_1
       (.I0(boundary_now0_carry__1_i_4_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [31]),
        .I2(\active_high_yaw_q_reg[31]_0 [30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(pwm_q0_carry__2_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__2_i_2
       (.I0(boundary_now0_carry__1_i_4_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [29]),
        .I2(\active_high_yaw_q_reg[31]_0 [28]),
        .I3(boundary_now0_carry__1_i_5_n_4),
        .O(pwm_q0_carry__2_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__2_i_3
       (.I0(boundary_now0_carry__1_i_5_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [27]),
        .I2(\active_high_yaw_q_reg[31]_0 [26]),
        .I3(boundary_now0_carry__1_i_5_n_6),
        .O(pwm_q0_carry__2_i_3_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry__2_i_4
       (.I0(boundary_now0_carry__1_i_5_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [25]),
        .I2(\active_high_yaw_q_reg[31]_0 [24]),
        .I3(boundary_now0_carry__0_i_5_n_4),
        .O(pwm_q0_carry__2_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__2_i_5
       (.I0(\active_high_yaw_q_reg[31]_0 [31]),
        .I1(boundary_now0_carry__1_i_4_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [30]),
        .I3(boundary_now0_carry__1_i_4_n_6),
        .O(pwm_q0_carry__2_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__2_i_6
       (.I0(\active_high_yaw_q_reg[31]_0 [29]),
        .I1(boundary_now0_carry__1_i_4_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [28]),
        .I3(boundary_now0_carry__1_i_5_n_4),
        .O(pwm_q0_carry__2_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__2_i_7
       (.I0(\active_high_yaw_q_reg[31]_0 [27]),
        .I1(boundary_now0_carry__1_i_5_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [26]),
        .I3(boundary_now0_carry__1_i_5_n_6),
        .O(pwm_q0_carry__2_i_7_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry__2_i_8
       (.I0(\active_high_yaw_q_reg[31]_0 [25]),
        .I1(boundary_now0_carry__1_i_5_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [24]),
        .I3(boundary_now0_carry__0_i_5_n_4),
        .O(pwm_q0_carry__2_i_8_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry_i_1
       (.I0(boundary_now0_carry_i_6_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [7]),
        .I2(\active_high_yaw_q_reg[31]_0 [6]),
        .I3(boundary_now0_carry_i_6_n_6),
        .O(pwm_q0_carry_i_1_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry_i_2
       (.I0(boundary_now0_carry_i_6_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [5]),
        .I2(\active_high_yaw_q_reg[31]_0 [4]),
        .I3(boundary_now0_carry_i_7_n_4),
        .O(pwm_q0_carry_i_2_n_0));
  LUT4 #(
    .INIT(16'h44D4)) 
    pwm_q0_carry_i_3
       (.I0(boundary_now0_carry_i_7_n_5),
        .I1(\active_high_yaw_q_reg[31]_0 [3]),
        .I2(\active_high_yaw_q_reg[31]_0 [2]),
        .I3(boundary_now0_carry_i_7_n_6),
        .O(pwm_q0_carry_i_3_n_0));
  LUT4 #(
    .INIT(16'hD444)) 
    pwm_q0_carry_i_4
       (.I0(boundary_now0_carry_i_7_n_7),
        .I1(\active_high_yaw_q_reg[31]_0 [1]),
        .I2(\active_high_yaw_q_reg[31]_0 [0]),
        .I3(phase_q_reg[0]),
        .O(pwm_q0_carry_i_4_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry_i_5
       (.I0(\active_high_yaw_q_reg[31]_0 [7]),
        .I1(boundary_now0_carry_i_6_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [6]),
        .I3(boundary_now0_carry_i_6_n_6),
        .O(pwm_q0_carry_i_5_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry_i_6
       (.I0(\active_high_yaw_q_reg[31]_0 [5]),
        .I1(boundary_now0_carry_i_6_n_7),
        .I2(\active_high_yaw_q_reg[31]_0 [4]),
        .I3(boundary_now0_carry_i_7_n_4),
        .O(pwm_q0_carry_i_6_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    pwm_q0_carry_i_7
       (.I0(\active_high_yaw_q_reg[31]_0 [3]),
        .I1(boundary_now0_carry_i_7_n_5),
        .I2(\active_high_yaw_q_reg[31]_0 [2]),
        .I3(boundary_now0_carry_i_7_n_6),
        .O(pwm_q0_carry_i_7_n_0));
  LUT4 #(
    .INIT(16'h6006)) 
    pwm_q0_carry_i_8
       (.I0(phase_q_reg[0]),
        .I1(\active_high_yaw_q_reg[31]_0 [0]),
        .I2(\active_high_yaw_q_reg[31]_0 [1]),
        .I3(boundary_now0_carry_i_7_n_7),
        .O(pwm_q0_carry_i_8_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__0/i__carry 
       (.CI(1'b0),
        .CO({\pwm_q0_inferred__0/i__carry_n_0 ,\pwm_q0_inferred__0/i__carry_n_1 ,\pwm_q0_inferred__0/i__carry_n_2 ,\pwm_q0_inferred__0/i__carry_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry_i_1_n_0,i__carry_i_2_n_0,i__carry_i_3_n_0,i__carry_i_4_n_0}),
        .O(\NLW_pwm_q0_inferred__0/i__carry_O_UNCONNECTED [3:0]),
        .S({i__carry_i_5_n_0,i__carry_i_6_n_0,i__carry_i_7_n_0,i__carry_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__0/i__carry__0 
       (.CI(\pwm_q0_inferred__0/i__carry_n_0 ),
        .CO({\pwm_q0_inferred__0/i__carry__0_n_0 ,\pwm_q0_inferred__0/i__carry__0_n_1 ,\pwm_q0_inferred__0/i__carry__0_n_2 ,\pwm_q0_inferred__0/i__carry__0_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry__0_i_1_n_0,i__carry__0_i_2_n_0,i__carry__0_i_3_n_0,i__carry__0_i_4_n_0}),
        .O(\NLW_pwm_q0_inferred__0/i__carry__0_O_UNCONNECTED [3:0]),
        .S({i__carry__0_i_5_n_0,i__carry__0_i_6_n_0,i__carry__0_i_7_n_0,i__carry__0_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__0/i__carry__1 
       (.CI(\pwm_q0_inferred__0/i__carry__0_n_0 ),
        .CO({\pwm_q0_inferred__0/i__carry__1_n_0 ,\pwm_q0_inferred__0/i__carry__1_n_1 ,\pwm_q0_inferred__0/i__carry__1_n_2 ,\pwm_q0_inferred__0/i__carry__1_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry__1_i_1_n_0,i__carry__1_i_2_n_0,i__carry__1_i_3_n_0,i__carry__1_i_4_n_0}),
        .O(\NLW_pwm_q0_inferred__0/i__carry__1_O_UNCONNECTED [3:0]),
        .S({i__carry__1_i_5_n_0,i__carry__1_i_6_n_0,i__carry__1_i_7_n_0,i__carry__1_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__0/i__carry__2 
       (.CI(\pwm_q0_inferred__0/i__carry__1_n_0 ),
        .CO({p_0_in[1],\pwm_q0_inferred__0/i__carry__2_n_1 ,\pwm_q0_inferred__0/i__carry__2_n_2 ,\pwm_q0_inferred__0/i__carry__2_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry__2_i_1_n_0,i__carry__2_i_2_n_0,i__carry__2_i_3_n_0,i__carry__2_i_4_n_0}),
        .O(\NLW_pwm_q0_inferred__0/i__carry__2_O_UNCONNECTED [3:0]),
        .S({i__carry__2_i_5_n_0,i__carry__2_i_6_n_0,i__carry__2_i_7_n_0,i__carry__2_i_8_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__1/i__carry 
       (.CI(1'b0),
        .CO({\pwm_q0_inferred__1/i__carry_n_0 ,\pwm_q0_inferred__1/i__carry_n_1 ,\pwm_q0_inferred__1/i__carry_n_2 ,\pwm_q0_inferred__1/i__carry_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry_i_1__0_n_0,i__carry_i_2__0_n_0,i__carry_i_3__0_n_0,i__carry_i_4__0_n_0}),
        .O(\NLW_pwm_q0_inferred__1/i__carry_O_UNCONNECTED [3:0]),
        .S({i__carry_i_5__0_n_0,i__carry_i_6__0_n_0,i__carry_i_7__0_n_0,i__carry_i_8__0_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__1/i__carry__0 
       (.CI(\pwm_q0_inferred__1/i__carry_n_0 ),
        .CO({\pwm_q0_inferred__1/i__carry__0_n_0 ,\pwm_q0_inferred__1/i__carry__0_n_1 ,\pwm_q0_inferred__1/i__carry__0_n_2 ,\pwm_q0_inferred__1/i__carry__0_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry_i_1__1_n_0,i__carry_i_2__1_n_0,i__carry_i_3__1_n_0,i__carry_i_4__1_n_0}),
        .O(\NLW_pwm_q0_inferred__1/i__carry__0_O_UNCONNECTED [3:0]),
        .S({i__carry_i_5__1_n_0,i__carry_i_6__1_n_0,i__carry_i_7__1_n_0,i__carry_i_8__1_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__1/i__carry__1 
       (.CI(\pwm_q0_inferred__1/i__carry__0_n_0 ),
        .CO({\pwm_q0_inferred__1/i__carry__1_n_0 ,\pwm_q0_inferred__1/i__carry__1_n_1 ,\pwm_q0_inferred__1/i__carry__1_n_2 ,\pwm_q0_inferred__1/i__carry__1_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry_i_1__2_n_0,i__carry_i_2__2_n_0,i__carry_i_3__2_n_0,i__carry_i_4__2_n_0}),
        .O(\NLW_pwm_q0_inferred__1/i__carry__1_O_UNCONNECTED [3:0]),
        .S({i__carry_i_5__2_n_0,i__carry_i_6__2_n_0,i__carry_i_7__2_n_0,i__carry_i_8__2_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \pwm_q0_inferred__1/i__carry__2 
       (.CI(\pwm_q0_inferred__1/i__carry__1_n_0 ),
        .CO({p_0_in[2],\pwm_q0_inferred__1/i__carry__2_n_1 ,\pwm_q0_inferred__1/i__carry__2_n_2 ,\pwm_q0_inferred__1/i__carry__2_n_3 }),
        .CYINIT(1'b0),
        .DI({i__carry_i_1__3_n_0,i__carry_i_2__3_n_0,i__carry_i_3__3_n_0,i__carry_i_4__3_n_0}),
        .O(\NLW_pwm_q0_inferred__1/i__carry__2_O_UNCONNECTED [3:0]),
        .S({i__carry_i_5__3_n_0,i__carry_i_6__3_n_0,i__carry_i_7__3_n_0,i__carry_i_8__3_n_0}));
  LUT5 #(
    .INIT(32'h10101000)) 
    \pwm_q[0]_i_1 
       (.I0(stop),
        .I1(rst),
        .I2(\pwm_q[0]_i_2_n_0 ),
        .I3(running_q_reg_0),
        .I4(pending_q_reg_0),
        .O(\pwm_q[0]_i_1_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[0]_i_10 
       (.I0(pending_high_yaw_q[1]),
        .I1(pending_high_yaw_q[7]),
        .I2(pending_high_yaw_q[30]),
        .I3(pending_high_yaw_q[27]),
        .O(\pwm_q[0]_i_10_n_0 ));
  LUT6 #(
    .INIT(64'hB0B0BFBFBFB0BFB0)) 
    \pwm_q[0]_i_2 
       (.I0(\pwm_q[0]_i_3_n_0 ),
        .I1(\pwm_q[0]_i_4_n_0 ),
        .I2(apply_now),
        .I3(p_0_in[0]),
        .I4(window_active_q_i_7_n_0),
        .I5(\pwm_q[2]_i_5_n_0 ),
        .O(\pwm_q[0]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \pwm_q[0]_i_3 
       (.I0(\pwm_q[0]_i_5_n_0 ),
        .I1(pending_high_yaw_q[12]),
        .I2(pending_high_yaw_q[22]),
        .I3(pending_high_yaw_q[2]),
        .I4(pending_high_yaw_q[4]),
        .I5(\pwm_q[0]_i_6_n_0 ),
        .O(\pwm_q[0]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \pwm_q[0]_i_4 
       (.I0(\pwm_q[0]_i_7_n_0 ),
        .I1(pending_high_yaw_q[11]),
        .I2(pending_high_yaw_q[19]),
        .I3(pending_high_yaw_q[31]),
        .I4(pending_high_yaw_q[26]),
        .I5(\pwm_q[0]_i_8_n_0 ),
        .O(\pwm_q[0]_i_4_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[0]_i_5 
       (.I0(pending_high_yaw_q[15]),
        .I1(pending_high_yaw_q[21]),
        .I2(pending_high_yaw_q[0]),
        .I3(pending_high_yaw_q[6]),
        .O(\pwm_q[0]_i_5_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \pwm_q[0]_i_6 
       (.I0(pending_high_yaw_q[25]),
        .I1(pending_high_yaw_q[28]),
        .I2(pending_high_yaw_q[23]),
        .I3(pending_high_yaw_q[3]),
        .I4(\pwm_q[0]_i_9_n_0 ),
        .O(\pwm_q[0]_i_6_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[0]_i_7 
       (.I0(pending_high_yaw_q[5]),
        .I1(pending_high_yaw_q[18]),
        .I2(pending_high_yaw_q[29]),
        .I3(pending_high_yaw_q[24]),
        .O(\pwm_q[0]_i_7_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \pwm_q[0]_i_8 
       (.I0(pending_high_yaw_q[20]),
        .I1(pending_high_yaw_q[14]),
        .I2(pending_high_yaw_q[17]),
        .I3(pending_high_yaw_q[10]),
        .I4(\pwm_q[0]_i_10_n_0 ),
        .O(\pwm_q[0]_i_8_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[0]_i_9 
       (.I0(pending_high_yaw_q[8]),
        .I1(pending_high_yaw_q[16]),
        .I2(pending_high_yaw_q[13]),
        .I3(pending_high_yaw_q[9]),
        .O(\pwm_q[0]_i_9_n_0 ));
  LUT5 #(
    .INIT(32'h10101000)) 
    \pwm_q[1]_i_1 
       (.I0(stop),
        .I1(rst),
        .I2(\pwm_q[1]_i_2_n_0 ),
        .I3(running_q_reg_0),
        .I4(pending_q_reg_0),
        .O(\pwm_q[1]_i_1_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[1]_i_10 
       (.I0(pending_high_pitch_q[30]),
        .I1(pending_high_pitch_q[27]),
        .I2(pending_high_pitch_q[10]),
        .I3(pending_high_pitch_q[17]),
        .O(\pwm_q[1]_i_10_n_0 ));
  LUT6 #(
    .INIT(64'hEFE0EFEFEFE0E0E0)) 
    \pwm_q[1]_i_2 
       (.I0(\pwm_q[1]_i_3_n_0 ),
        .I1(\pwm_q[1]_i_4_n_0 ),
        .I2(apply_now),
        .I3(window_active_q_i_10_n_0),
        .I4(\pwm_q[2]_i_5_n_0 ),
        .I5(p_0_in[1]),
        .O(\pwm_q[1]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \pwm_q[1]_i_3 
       (.I0(\pwm_q[1]_i_5_n_0 ),
        .I1(pending_high_pitch_q[13]),
        .I2(pending_high_pitch_q[3]),
        .I3(pending_high_pitch_q[28]),
        .I4(pending_high_pitch_q[25]),
        .I5(\pwm_q[1]_i_6_n_0 ),
        .O(\pwm_q[1]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \pwm_q[1]_i_4 
       (.I0(\pwm_q[1]_i_7_n_0 ),
        .I1(pending_high_pitch_q[31]),
        .I2(pending_high_pitch_q[26]),
        .I3(pending_high_pitch_q[1]),
        .I4(pending_high_pitch_q[7]),
        .I5(\pwm_q[1]_i_8_n_0 ),
        .O(\pwm_q[1]_i_4_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[1]_i_5 
       (.I0(pending_high_pitch_q[2]),
        .I1(pending_high_pitch_q[4]),
        .I2(pending_high_pitch_q[9]),
        .I3(pending_high_pitch_q[23]),
        .O(\pwm_q[1]_i_5_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \pwm_q[1]_i_6 
       (.I0(pending_high_pitch_q[6]),
        .I1(pending_high_pitch_q[0]),
        .I2(pending_high_pitch_q[21]),
        .I3(pending_high_pitch_q[15]),
        .I4(\pwm_q[1]_i_9_n_0 ),
        .O(\pwm_q[1]_i_6_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[1]_i_7 
       (.I0(pending_high_pitch_q[8]),
        .I1(pending_high_pitch_q[16]),
        .I2(pending_high_pitch_q[11]),
        .I3(pending_high_pitch_q[19]),
        .O(\pwm_q[1]_i_7_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \pwm_q[1]_i_8 
       (.I0(pending_high_pitch_q[22]),
        .I1(pending_high_pitch_q[12]),
        .I2(pending_high_pitch_q[20]),
        .I3(pending_high_pitch_q[14]),
        .I4(\pwm_q[1]_i_10_n_0 ),
        .O(\pwm_q[1]_i_8_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[1]_i_9 
       (.I0(pending_high_pitch_q[5]),
        .I1(pending_high_pitch_q[18]),
        .I2(pending_high_pitch_q[29]),
        .I3(pending_high_pitch_q[24]),
        .O(\pwm_q[1]_i_9_n_0 ));
  LUT5 #(
    .INIT(32'h10101000)) 
    \pwm_q[2]_i_1 
       (.I0(stop),
        .I1(rst),
        .I2(\pwm_q[2]_i_2_n_0 ),
        .I3(running_q_reg_0),
        .I4(pending_q_reg_0),
        .O(\pwm_q[2]_i_1_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[2]_i_10 
       (.I0(pending_high_speed_q[1]),
        .I1(pending_high_speed_q[7]),
        .I2(pending_high_speed_q[30]),
        .I3(pending_high_speed_q[27]),
        .O(\pwm_q[2]_i_10_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[2]_i_11 
       (.I0(pending_high_speed_q[8]),
        .I1(pending_high_speed_q[16]),
        .I2(pending_high_speed_q[13]),
        .I3(pending_high_speed_q[9]),
        .O(\pwm_q[2]_i_11_n_0 ));
  LUT6 #(
    .INIT(64'hEFE0EFEFEFE0E0E0)) 
    \pwm_q[2]_i_2 
       (.I0(\pwm_q[2]_i_3_n_0 ),
        .I1(\pwm_q[2]_i_4_n_0 ),
        .I2(apply_now),
        .I3(window_active_q_i_6_n_0),
        .I4(\pwm_q[2]_i_5_n_0 ),
        .I5(p_0_in[2]),
        .O(\pwm_q[2]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \pwm_q[2]_i_3 
       (.I0(\pwm_q[2]_i_6_n_0 ),
        .I1(pending_high_speed_q[11]),
        .I2(pending_high_speed_q[19]),
        .I3(pending_high_speed_q[31]),
        .I4(pending_high_speed_q[26]),
        .I5(\pwm_q[2]_i_7_n_0 ),
        .O(\pwm_q[2]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \pwm_q[2]_i_4 
       (.I0(\pwm_q[2]_i_8_n_0 ),
        .I1(pending_high_speed_q[12]),
        .I2(pending_high_speed_q[22]),
        .I3(pending_high_speed_q[2]),
        .I4(pending_high_speed_q[4]),
        .I5(\pwm_q[2]_i_9_n_0 ),
        .O(\pwm_q[2]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h8)) 
    \pwm_q[2]_i_5 
       (.I0(boundary_now0__10),
        .I1(running_q_reg_0),
        .O(\pwm_q[2]_i_5_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[2]_i_6 
       (.I0(pending_high_speed_q[5]),
        .I1(pending_high_speed_q[18]),
        .I2(pending_high_speed_q[29]),
        .I3(pending_high_speed_q[24]),
        .O(\pwm_q[2]_i_6_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \pwm_q[2]_i_7 
       (.I0(pending_high_speed_q[20]),
        .I1(pending_high_speed_q[14]),
        .I2(pending_high_speed_q[17]),
        .I3(pending_high_speed_q[10]),
        .I4(\pwm_q[2]_i_10_n_0 ),
        .O(\pwm_q[2]_i_7_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \pwm_q[2]_i_8 
       (.I0(pending_high_speed_q[15]),
        .I1(pending_high_speed_q[21]),
        .I2(pending_high_speed_q[0]),
        .I3(pending_high_speed_q[6]),
        .O(\pwm_q[2]_i_8_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \pwm_q[2]_i_9 
       (.I0(pending_high_speed_q[25]),
        .I1(pending_high_speed_q[28]),
        .I2(pending_high_speed_q[23]),
        .I3(pending_high_speed_q[3]),
        .I4(\pwm_q[2]_i_11_n_0 ),
        .O(\pwm_q[2]_i_9_n_0 ));
  FDRE \pwm_q_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\pwm_q[0]_i_1_n_0 ),
        .Q(pwm[0]),
        .R(1'b0));
  FDRE \pwm_q_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\pwm_q[1]_i_1_n_0 ),
        .Q(pwm[1]),
        .R(1'b0));
  FDRE \pwm_q_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\pwm_q[2]_i_1_n_0 ),
        .Q(pwm[2]),
        .R(1'b0));
  (* SOFT_HLUTNM = "soft_lutpair25" *) 
  LUT5 #(
    .INIT(32'h00000100)) 
    rejected_q_i_1
       (.I0(stop),
        .I1(rst),
        .I2(pending_q_reg_0),
        .I3(cfg_valid),
        .I4(rejected_q),
        .O(rejected_q_i_1_n_0));
  FDRE rejected_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(rejected_q_i_1_n_0),
        .Q(rejected),
        .R(1'b0));
  LUT2 #(
    .INIT(4'hE)) 
    running_q_i_1
       (.I0(stop),
        .I1(rst),
        .O(accepted_q1));
  LUT5 #(
    .INIT(32'h11010000)) 
    running_q_i_2
       (.I0(stop),
        .I1(rst),
        .I2(running_q_reg_0),
        .I3(boundary_now0__10),
        .I4(pending_q_reg_0),
        .O(apply_now));
  FDRE running_q_reg
       (.C(clk),
        .CE(apply_now),
        .D(1'b1),
        .Q(running_q_reg_0),
        .R(accepted_q1));
  (* SOFT_HLUTNM = "soft_lutpair23" *) 
  LUT5 #(
    .INIT(32'hFFFFFEFF)) 
    window_active_q_i_1
       (.I0(stop),
        .I1(rst),
        .I2(pending_q_reg_0),
        .I3(running_q_reg_0),
        .I4(cfg_valid),
        .O(stop_0));
  LUT4 #(
    .INIT(16'hFEFF)) 
    window_active_q_i_10
       (.I0(window_active_q_i_28_n_0),
        .I1(window_active_q_i_29_n_0),
        .I2(window_active_q_i_30_n_0),
        .I3(window_active_q_i_31_n_0),
        .O(window_active_q_i_10_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_100
       (.I0(Q[15]),
        .I1(\active_high_pitch_q_reg[31]_0 [15]),
        .I2(Q[14]),
        .I3(\active_high_pitch_q_reg[31]_0 [14]),
        .O(window_active_q_i_100_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_101
       (.I0(Q[13]),
        .I1(\active_high_pitch_q_reg[31]_0 [13]),
        .I2(Q[12]),
        .I3(\active_high_pitch_q_reg[31]_0 [12]),
        .O(window_active_q_i_101_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_102
       (.I0(Q[11]),
        .I1(\active_high_pitch_q_reg[31]_0 [11]),
        .I2(Q[10]),
        .I3(\active_high_pitch_q_reg[31]_0 [10]),
        .O(window_active_q_i_102_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_103
       (.I0(Q[9]),
        .I1(\active_high_pitch_q_reg[31]_0 [9]),
        .I2(Q[8]),
        .I3(\active_high_pitch_q_reg[31]_0 [8]),
        .O(window_active_q_i_103_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_104
       (.I0(\active_high_pitch_q_reg[31]_0 [15]),
        .I1(Q[15]),
        .I2(\active_high_pitch_q_reg[31]_0 [14]),
        .I3(Q[14]),
        .O(window_active_q_i_104_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_105
       (.I0(\active_high_pitch_q_reg[31]_0 [13]),
        .I1(Q[13]),
        .I2(\active_high_pitch_q_reg[31]_0 [12]),
        .I3(Q[12]),
        .O(window_active_q_i_105_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_106
       (.I0(\active_high_pitch_q_reg[31]_0 [11]),
        .I1(Q[11]),
        .I2(\active_high_pitch_q_reg[31]_0 [10]),
        .I3(Q[10]),
        .O(window_active_q_i_106_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_107
       (.I0(\active_high_pitch_q_reg[31]_0 [9]),
        .I1(Q[9]),
        .I2(\active_high_pitch_q_reg[31]_0 [8]),
        .I3(Q[8]),
        .O(window_active_q_i_107_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_109
       (.I0(Q[15]),
        .I1(\active_high_yaw_q_reg[31]_0 [15]),
        .I2(Q[14]),
        .I3(\active_high_yaw_q_reg[31]_0 [14]),
        .O(window_active_q_i_109_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_110
       (.I0(Q[13]),
        .I1(\active_high_yaw_q_reg[31]_0 [13]),
        .I2(Q[12]),
        .I3(\active_high_yaw_q_reg[31]_0 [12]),
        .O(window_active_q_i_110_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_111
       (.I0(Q[11]),
        .I1(\active_high_yaw_q_reg[31]_0 [11]),
        .I2(Q[10]),
        .I3(\active_high_yaw_q_reg[31]_0 [10]),
        .O(window_active_q_i_111_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_112
       (.I0(Q[9]),
        .I1(\active_high_yaw_q_reg[31]_0 [9]),
        .I2(Q[8]),
        .I3(\active_high_yaw_q_reg[31]_0 [8]),
        .O(window_active_q_i_112_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_113
       (.I0(\active_high_yaw_q_reg[31]_0 [15]),
        .I1(Q[15]),
        .I2(\active_high_yaw_q_reg[31]_0 [14]),
        .I3(Q[14]),
        .O(window_active_q_i_113_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_114
       (.I0(\active_high_yaw_q_reg[31]_0 [13]),
        .I1(Q[13]),
        .I2(\active_high_yaw_q_reg[31]_0 [12]),
        .I3(Q[12]),
        .O(window_active_q_i_114_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_115
       (.I0(\active_high_yaw_q_reg[31]_0 [11]),
        .I1(Q[11]),
        .I2(\active_high_yaw_q_reg[31]_0 [10]),
        .I3(Q[10]),
        .O(window_active_q_i_115_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_116
       (.I0(\active_high_yaw_q_reg[31]_0 [9]),
        .I1(Q[9]),
        .I2(\active_high_yaw_q_reg[31]_0 [8]),
        .I3(Q[8]),
        .O(window_active_q_i_116_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_118
       (.I0(Q[15]),
        .I1(\active_high_speed_q_reg[31]_0 [15]),
        .I2(Q[14]),
        .I3(\active_high_speed_q_reg[31]_0 [14]),
        .O(window_active_q_i_118_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_119
       (.I0(Q[13]),
        .I1(\active_high_speed_q_reg[31]_0 [13]),
        .I2(Q[12]),
        .I3(\active_high_speed_q_reg[31]_0 [12]),
        .O(window_active_q_i_119_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_120
       (.I0(Q[11]),
        .I1(\active_high_speed_q_reg[31]_0 [11]),
        .I2(Q[10]),
        .I3(\active_high_speed_q_reg[31]_0 [10]),
        .O(window_active_q_i_120_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_121
       (.I0(Q[9]),
        .I1(\active_high_speed_q_reg[31]_0 [9]),
        .I2(Q[8]),
        .I3(\active_high_speed_q_reg[31]_0 [8]),
        .O(window_active_q_i_121_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_122
       (.I0(\active_high_speed_q_reg[31]_0 [15]),
        .I1(Q[15]),
        .I2(\active_high_speed_q_reg[31]_0 [14]),
        .I3(Q[14]),
        .O(window_active_q_i_122_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_123
       (.I0(\active_high_speed_q_reg[31]_0 [13]),
        .I1(Q[13]),
        .I2(\active_high_speed_q_reg[31]_0 [12]),
        .I3(Q[12]),
        .O(window_active_q_i_123_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_124
       (.I0(\active_high_speed_q_reg[31]_0 [11]),
        .I1(Q[11]),
        .I2(\active_high_speed_q_reg[31]_0 [10]),
        .I3(Q[10]),
        .O(window_active_q_i_124_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_125
       (.I0(\active_high_speed_q_reg[31]_0 [9]),
        .I1(Q[9]),
        .I2(\active_high_speed_q_reg[31]_0 [8]),
        .I3(Q[8]),
        .O(window_active_q_i_125_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_126
       (.I0(Q[7]),
        .I1(\active_high_pitch_q_reg[31]_0 [7]),
        .I2(Q[6]),
        .I3(\active_high_pitch_q_reg[31]_0 [6]),
        .O(window_active_q_i_126_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_127
       (.I0(Q[5]),
        .I1(\active_high_pitch_q_reg[31]_0 [5]),
        .I2(Q[4]),
        .I3(\active_high_pitch_q_reg[31]_0 [4]),
        .O(window_active_q_i_127_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_128
       (.I0(Q[3]),
        .I1(\active_high_pitch_q_reg[31]_0 [3]),
        .I2(Q[2]),
        .I3(\active_high_pitch_q_reg[31]_0 [2]),
        .O(window_active_q_i_128_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_129
       (.I0(Q[1]),
        .I1(\active_high_pitch_q_reg[31]_0 [1]),
        .I2(Q[0]),
        .I3(\active_high_pitch_q_reg[31]_0 [0]),
        .O(window_active_q_i_129_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_130
       (.I0(\active_high_pitch_q_reg[31]_0 [7]),
        .I1(Q[7]),
        .I2(\active_high_pitch_q_reg[31]_0 [6]),
        .I3(Q[6]),
        .O(window_active_q_i_130_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_131
       (.I0(\active_high_pitch_q_reg[31]_0 [5]),
        .I1(Q[5]),
        .I2(\active_high_pitch_q_reg[31]_0 [4]),
        .I3(Q[4]),
        .O(window_active_q_i_131_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_132
       (.I0(\active_high_pitch_q_reg[31]_0 [3]),
        .I1(Q[3]),
        .I2(\active_high_pitch_q_reg[31]_0 [2]),
        .I3(Q[2]),
        .O(window_active_q_i_132_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_133
       (.I0(\active_high_pitch_q_reg[31]_0 [1]),
        .I1(Q[1]),
        .I2(\active_high_pitch_q_reg[31]_0 [0]),
        .I3(Q[0]),
        .O(window_active_q_i_133_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_134
       (.I0(Q[7]),
        .I1(\active_high_yaw_q_reg[31]_0 [7]),
        .I2(Q[6]),
        .I3(\active_high_yaw_q_reg[31]_0 [6]),
        .O(window_active_q_i_134_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_135
       (.I0(Q[5]),
        .I1(\active_high_yaw_q_reg[31]_0 [5]),
        .I2(Q[4]),
        .I3(\active_high_yaw_q_reg[31]_0 [4]),
        .O(window_active_q_i_135_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_136
       (.I0(Q[3]),
        .I1(\active_high_yaw_q_reg[31]_0 [3]),
        .I2(Q[2]),
        .I3(\active_high_yaw_q_reg[31]_0 [2]),
        .O(window_active_q_i_136_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_137
       (.I0(Q[1]),
        .I1(\active_high_yaw_q_reg[31]_0 [1]),
        .I2(Q[0]),
        .I3(\active_high_yaw_q_reg[31]_0 [0]),
        .O(window_active_q_i_137_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_138
       (.I0(\active_high_yaw_q_reg[31]_0 [7]),
        .I1(Q[7]),
        .I2(\active_high_yaw_q_reg[31]_0 [6]),
        .I3(Q[6]),
        .O(window_active_q_i_138_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_139
       (.I0(\active_high_yaw_q_reg[31]_0 [5]),
        .I1(Q[5]),
        .I2(\active_high_yaw_q_reg[31]_0 [4]),
        .I3(Q[4]),
        .O(window_active_q_i_139_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_140
       (.I0(\active_high_yaw_q_reg[31]_0 [3]),
        .I1(Q[3]),
        .I2(\active_high_yaw_q_reg[31]_0 [2]),
        .I3(Q[2]),
        .O(window_active_q_i_140_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_141
       (.I0(\active_high_yaw_q_reg[31]_0 [1]),
        .I1(Q[1]),
        .I2(\active_high_yaw_q_reg[31]_0 [0]),
        .I3(Q[0]),
        .O(window_active_q_i_141_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_142
       (.I0(Q[7]),
        .I1(\active_high_speed_q_reg[31]_0 [7]),
        .I2(Q[6]),
        .I3(\active_high_speed_q_reg[31]_0 [6]),
        .O(window_active_q_i_142_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_143
       (.I0(Q[5]),
        .I1(\active_high_speed_q_reg[31]_0 [5]),
        .I2(Q[4]),
        .I3(\active_high_speed_q_reg[31]_0 [4]),
        .O(window_active_q_i_143_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_144
       (.I0(Q[3]),
        .I1(\active_high_speed_q_reg[31]_0 [3]),
        .I2(Q[2]),
        .I3(\active_high_speed_q_reg[31]_0 [2]),
        .O(window_active_q_i_144_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_145
       (.I0(Q[1]),
        .I1(\active_high_speed_q_reg[31]_0 [1]),
        .I2(Q[0]),
        .I3(\active_high_speed_q_reg[31]_0 [0]),
        .O(window_active_q_i_145_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_146
       (.I0(\active_high_speed_q_reg[31]_0 [7]),
        .I1(Q[7]),
        .I2(\active_high_speed_q_reg[31]_0 [6]),
        .I3(Q[6]),
        .O(window_active_q_i_146_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_147
       (.I0(\active_high_speed_q_reg[31]_0 [5]),
        .I1(Q[5]),
        .I2(\active_high_speed_q_reg[31]_0 [4]),
        .I3(Q[4]),
        .O(window_active_q_i_147_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_148
       (.I0(\active_high_speed_q_reg[31]_0 [3]),
        .I1(Q[3]),
        .I2(\active_high_speed_q_reg[31]_0 [2]),
        .I3(Q[2]),
        .O(window_active_q_i_148_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_149
       (.I0(\active_high_speed_q_reg[31]_0 [1]),
        .I1(Q[1]),
        .I2(\active_high_speed_q_reg[31]_0 [0]),
        .I3(Q[0]),
        .O(window_active_q_i_149_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_15
       (.I0(\active_high_speed_q_reg[31]_0 [9]),
        .I1(\active_high_speed_q_reg[31]_0 [10]),
        .I2(\active_high_speed_q_reg[31]_0 [8]),
        .I3(\active_high_speed_q_reg[31]_0 [11]),
        .I4(window_active_q_i_59_n_0),
        .O(window_active_q_i_15_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_16
       (.I0(\active_high_speed_q_reg[31]_0 [1]),
        .I1(\active_high_speed_q_reg[31]_0 [2]),
        .I2(\active_high_speed_q_reg[31]_0 [0]),
        .I3(\active_high_speed_q_reg[31]_0 [3]),
        .I4(window_active_q_i_60_n_0),
        .O(window_active_q_i_16_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_17
       (.I0(\active_high_speed_q_reg[31]_0 [30]),
        .I1(\active_high_speed_q_reg[31]_0 [31]),
        .I2(\active_high_speed_q_reg[31]_0 [28]),
        .I3(\active_high_speed_q_reg[31]_0 [29]),
        .I4(window_active_q_i_61_n_0),
        .O(window_active_q_i_17_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_18
       (.I0(\active_high_speed_q_reg[31]_0 [21]),
        .I1(\active_high_speed_q_reg[31]_0 [22]),
        .I2(\active_high_speed_q_reg[31]_0 [20]),
        .I3(\active_high_speed_q_reg[31]_0 [23]),
        .I4(window_active_q_i_62_n_0),
        .O(window_active_q_i_18_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_19
       (.I0(\active_high_yaw_q_reg[31]_0 [9]),
        .I1(\active_high_yaw_q_reg[31]_0 [10]),
        .I2(\active_high_yaw_q_reg[31]_0 [8]),
        .I3(\active_high_yaw_q_reg[31]_0 [11]),
        .I4(window_active_q_i_63_n_0),
        .O(window_active_q_i_19_n_0));
  LUT5 #(
    .INIT(32'h00000001)) 
    window_active_q_i_20
       (.I0(\active_high_yaw_q_reg[31]_0 [6]),
        .I1(\active_high_yaw_q_reg[31]_0 [30]),
        .I2(\active_high_yaw_q_reg[31]_0 [5]),
        .I3(\active_high_yaw_q_reg[31]_0 [7]),
        .I4(window_active_q_i_64_n_0),
        .O(window_active_q_i_20_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_21
       (.I0(\active_high_yaw_q_reg[31]_0 [12]),
        .I1(\active_high_yaw_q_reg[31]_0 [23]),
        .I2(\active_high_yaw_q_reg[31]_0 [24]),
        .I3(\active_high_yaw_q_reg[31]_0 [25]),
        .I4(window_active_q_i_65_n_0),
        .O(window_active_q_i_21_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_22
       (.I0(\active_high_yaw_q_reg[31]_0 [0]),
        .I1(\active_high_yaw_q_reg[31]_0 [27]),
        .I2(\active_high_yaw_q_reg[31]_0 [28]),
        .I3(\active_high_yaw_q_reg[31]_0 [29]),
        .I4(window_active_q_i_66_n_0),
        .O(window_active_q_i_22_n_0));
  (* SOFT_HLUTNM = "soft_lutpair27" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_23
       (.I0(Q[18]),
        .I1(Q[10]),
        .I2(Q[30]),
        .I3(Q[20]),
        .O(window_active_q_i_23_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_24
       (.I0(Q[19]),
        .I1(Q[29]),
        .I2(Q[9]),
        .I3(Q[12]),
        .I4(window_active_q_i_67_n_0),
        .O(window_active_q_i_24_n_0));
  (* SOFT_HLUTNM = "soft_lutpair29" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_25
       (.I0(Q[22]),
        .I1(Q[17]),
        .I2(Q[31]),
        .I3(Q[7]),
        .O(window_active_q_i_25_n_0));
  (* SOFT_HLUTNM = "soft_lutpair30" *) 
  LUT4 #(
    .INIT(16'h0001)) 
    window_active_q_i_26
       (.I0(Q[24]),
        .I1(Q[21]),
        .I2(Q[26]),
        .I3(Q[1]),
        .O(window_active_q_i_26_n_0));
  (* SOFT_HLUTNM = "soft_lutpair28" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_27
       (.I0(Q[28]),
        .I1(Q[16]),
        .I2(Q[15]),
        .I3(Q[2]),
        .O(window_active_q_i_27_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_28
       (.I0(\active_high_pitch_q_reg[31]_0 [8]),
        .I1(\active_high_pitch_q_reg[31]_0 [11]),
        .I2(\active_high_pitch_q_reg[31]_0 [9]),
        .I3(\active_high_pitch_q_reg[31]_0 [10]),
        .I4(window_active_q_i_68_n_0),
        .O(window_active_q_i_28_n_0));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_29
       (.I0(\active_high_pitch_q_reg[31]_0 [1]),
        .I1(\active_high_pitch_q_reg[31]_0 [2]),
        .I2(\active_high_pitch_q_reg[31]_0 [0]),
        .I3(\active_high_pitch_q_reg[31]_0 [3]),
        .I4(window_active_q_i_69_n_0),
        .O(window_active_q_i_29_n_0));
  LUT6 #(
    .INIT(64'h0400040400000000)) 
    window_active_q_i_3
       (.I0(window_active_q_i_5_n_0),
        .I1(window_active_q_i_6_n_0),
        .I2(window_active_q_i_7_n_0),
        .I3(window_active_q_i_8_n_0),
        .I4(window_active_q_i_9_n_0),
        .I5(window_active_q_i_10_n_0),
        .O(applied_q_reg_1));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    window_active_q_i_30
       (.I0(\active_high_pitch_q_reg[31]_0 [20]),
        .I1(\active_high_pitch_q_reg[31]_0 [30]),
        .I2(\active_high_pitch_q_reg[31]_0 [16]),
        .I3(\active_high_pitch_q_reg[31]_0 [19]),
        .I4(window_active_q_i_70_n_0),
        .O(window_active_q_i_30_n_0));
  LUT5 #(
    .INIT(32'h00000001)) 
    window_active_q_i_31
       (.I0(\active_high_pitch_q_reg[31]_0 [17]),
        .I1(\active_high_pitch_q_reg[31]_0 [31]),
        .I2(\active_high_pitch_q_reg[31]_0 [24]),
        .I3(\active_high_pitch_q_reg[31]_0 [25]),
        .I4(window_active_q_i_71_n_0),
        .O(window_active_q_i_31_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_33
       (.I0(Q[31]),
        .I1(\active_high_pitch_q_reg[31]_0 [31]),
        .I2(Q[30]),
        .I3(\active_high_pitch_q_reg[31]_0 [30]),
        .O(window_active_q_i_33_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_34
       (.I0(Q[29]),
        .I1(\active_high_pitch_q_reg[31]_0 [29]),
        .I2(Q[28]),
        .I3(\active_high_pitch_q_reg[31]_0 [28]),
        .O(window_active_q_i_34_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_35
       (.I0(Q[27]),
        .I1(\active_high_pitch_q_reg[31]_0 [27]),
        .I2(Q[26]),
        .I3(\active_high_pitch_q_reg[31]_0 [26]),
        .O(window_active_q_i_35_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_36
       (.I0(Q[25]),
        .I1(\active_high_pitch_q_reg[31]_0 [25]),
        .I2(Q[24]),
        .I3(\active_high_pitch_q_reg[31]_0 [24]),
        .O(window_active_q_i_36_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_37
       (.I0(\active_high_pitch_q_reg[31]_0 [31]),
        .I1(Q[31]),
        .I2(\active_high_pitch_q_reg[31]_0 [30]),
        .I3(Q[30]),
        .O(window_active_q_i_37_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_38
       (.I0(\active_high_pitch_q_reg[31]_0 [29]),
        .I1(Q[29]),
        .I2(\active_high_pitch_q_reg[31]_0 [28]),
        .I3(Q[28]),
        .O(window_active_q_i_38_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_39
       (.I0(\active_high_pitch_q_reg[31]_0 [27]),
        .I1(Q[27]),
        .I2(\active_high_pitch_q_reg[31]_0 [26]),
        .I3(Q[26]),
        .O(window_active_q_i_39_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_40
       (.I0(\active_high_pitch_q_reg[31]_0 [25]),
        .I1(Q[25]),
        .I2(\active_high_pitch_q_reg[31]_0 [24]),
        .I3(Q[24]),
        .O(window_active_q_i_40_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_42
       (.I0(Q[31]),
        .I1(\active_high_yaw_q_reg[31]_0 [31]),
        .I2(Q[30]),
        .I3(\active_high_yaw_q_reg[31]_0 [30]),
        .O(window_active_q_i_42_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_43
       (.I0(Q[29]),
        .I1(\active_high_yaw_q_reg[31]_0 [29]),
        .I2(Q[28]),
        .I3(\active_high_yaw_q_reg[31]_0 [28]),
        .O(window_active_q_i_43_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_44
       (.I0(Q[27]),
        .I1(\active_high_yaw_q_reg[31]_0 [27]),
        .I2(Q[26]),
        .I3(\active_high_yaw_q_reg[31]_0 [26]),
        .O(window_active_q_i_44_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_45
       (.I0(Q[25]),
        .I1(\active_high_yaw_q_reg[31]_0 [25]),
        .I2(Q[24]),
        .I3(\active_high_yaw_q_reg[31]_0 [24]),
        .O(window_active_q_i_45_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_46
       (.I0(\active_high_yaw_q_reg[31]_0 [31]),
        .I1(Q[31]),
        .I2(\active_high_yaw_q_reg[31]_0 [30]),
        .I3(Q[30]),
        .O(window_active_q_i_46_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_47
       (.I0(\active_high_yaw_q_reg[31]_0 [29]),
        .I1(Q[29]),
        .I2(\active_high_yaw_q_reg[31]_0 [28]),
        .I3(Q[28]),
        .O(window_active_q_i_47_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_48
       (.I0(\active_high_yaw_q_reg[31]_0 [27]),
        .I1(Q[27]),
        .I2(\active_high_yaw_q_reg[31]_0 [26]),
        .I3(Q[26]),
        .O(window_active_q_i_48_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_49
       (.I0(\active_high_yaw_q_reg[31]_0 [25]),
        .I1(Q[25]),
        .I2(\active_high_yaw_q_reg[31]_0 [24]),
        .I3(Q[24]),
        .O(window_active_q_i_49_n_0));
  (* SOFT_HLUTNM = "soft_lutpair39" *) 
  LUT4 #(
    .INIT(16'h7FFF)) 
    window_active_q_i_5
       (.I0(eligible_application2),
        .I1(eligible_application4),
        .I2(eligible_application0),
        .I3(applied_q_reg_0),
        .O(window_active_q_i_5_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_51
       (.I0(Q[31]),
        .I1(\active_high_speed_q_reg[31]_0 [31]),
        .I2(Q[30]),
        .I3(\active_high_speed_q_reg[31]_0 [30]),
        .O(window_active_q_i_51_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_52
       (.I0(Q[29]),
        .I1(\active_high_speed_q_reg[31]_0 [29]),
        .I2(Q[28]),
        .I3(\active_high_speed_q_reg[31]_0 [28]),
        .O(window_active_q_i_52_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_53
       (.I0(Q[27]),
        .I1(\active_high_speed_q_reg[31]_0 [27]),
        .I2(Q[26]),
        .I3(\active_high_speed_q_reg[31]_0 [26]),
        .O(window_active_q_i_53_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_54
       (.I0(Q[25]),
        .I1(\active_high_speed_q_reg[31]_0 [25]),
        .I2(Q[24]),
        .I3(\active_high_speed_q_reg[31]_0 [24]),
        .O(window_active_q_i_54_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_55
       (.I0(\active_high_speed_q_reg[31]_0 [31]),
        .I1(Q[31]),
        .I2(\active_high_speed_q_reg[31]_0 [30]),
        .I3(Q[30]),
        .O(window_active_q_i_55_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_56
       (.I0(\active_high_speed_q_reg[31]_0 [29]),
        .I1(Q[29]),
        .I2(\active_high_speed_q_reg[31]_0 [28]),
        .I3(Q[28]),
        .O(window_active_q_i_56_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_57
       (.I0(\active_high_speed_q_reg[31]_0 [27]),
        .I1(Q[27]),
        .I2(\active_high_speed_q_reg[31]_0 [26]),
        .I3(Q[26]),
        .O(window_active_q_i_57_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_58
       (.I0(\active_high_speed_q_reg[31]_0 [25]),
        .I1(Q[25]),
        .I2(\active_high_speed_q_reg[31]_0 [24]),
        .I3(Q[24]),
        .O(window_active_q_i_58_n_0));
  (* SOFT_HLUTNM = "soft_lutpair42" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_59
       (.I0(\active_high_speed_q_reg[31]_0 [13]),
        .I1(\active_high_speed_q_reg[31]_0 [12]),
        .I2(\active_high_speed_q_reg[31]_0 [15]),
        .I3(\active_high_speed_q_reg[31]_0 [14]),
        .O(window_active_q_i_59_n_0));
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_6
       (.I0(window_active_q_i_15_n_0),
        .I1(window_active_q_i_16_n_0),
        .I2(window_active_q_i_17_n_0),
        .I3(window_active_q_i_18_n_0),
        .O(window_active_q_i_6_n_0));
  (* SOFT_HLUTNM = "soft_lutpair43" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_60
       (.I0(\active_high_speed_q_reg[31]_0 [5]),
        .I1(\active_high_speed_q_reg[31]_0 [4]),
        .I2(\active_high_speed_q_reg[31]_0 [7]),
        .I3(\active_high_speed_q_reg[31]_0 [6]),
        .O(window_active_q_i_60_n_0));
  (* SOFT_HLUTNM = "soft_lutpair40" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_61
       (.I0(\active_high_speed_q_reg[31]_0 [27]),
        .I1(\active_high_speed_q_reg[31]_0 [24]),
        .I2(\active_high_speed_q_reg[31]_0 [26]),
        .I3(\active_high_speed_q_reg[31]_0 [25]),
        .O(window_active_q_i_61_n_0));
  (* SOFT_HLUTNM = "soft_lutpair41" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_62
       (.I0(\active_high_speed_q_reg[31]_0 [19]),
        .I1(\active_high_speed_q_reg[31]_0 [16]),
        .I2(\active_high_speed_q_reg[31]_0 [18]),
        .I3(\active_high_speed_q_reg[31]_0 [17]),
        .O(window_active_q_i_62_n_0));
  (* SOFT_HLUTNM = "soft_lutpair33" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_63
       (.I0(\active_high_yaw_q_reg[31]_0 [19]),
        .I1(\active_high_yaw_q_reg[31]_0 [18]),
        .I2(\active_high_yaw_q_reg[31]_0 [31]),
        .I3(\active_high_yaw_q_reg[31]_0 [4]),
        .O(window_active_q_i_63_n_0));
  (* SOFT_HLUTNM = "soft_lutpair34" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_64
       (.I0(\active_high_yaw_q_reg[31]_0 [21]),
        .I1(\active_high_yaw_q_reg[31]_0 [20]),
        .I2(\active_high_yaw_q_reg[31]_0 [22]),
        .I3(\active_high_yaw_q_reg[31]_0 [13]),
        .O(window_active_q_i_64_n_0));
  (* SOFT_HLUTNM = "soft_lutpair31" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_65
       (.I0(\active_high_yaw_q_reg[31]_0 [16]),
        .I1(\active_high_yaw_q_reg[31]_0 [3]),
        .I2(\active_high_yaw_q_reg[31]_0 [26]),
        .I3(\active_high_yaw_q_reg[31]_0 [1]),
        .O(window_active_q_i_65_n_0));
  (* SOFT_HLUTNM = "soft_lutpair32" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_66
       (.I0(\active_high_yaw_q_reg[31]_0 [15]),
        .I1(\active_high_yaw_q_reg[31]_0 [14]),
        .I2(\active_high_yaw_q_reg[31]_0 [17]),
        .I3(\active_high_yaw_q_reg[31]_0 [2]),
        .O(window_active_q_i_66_n_0));
  (* SOFT_HLUTNM = "soft_lutpair26" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_67
       (.I0(Q[13]),
        .I1(Q[11]),
        .I2(Q[14]),
        .I3(Q[8]),
        .O(window_active_q_i_67_n_0));
  (* SOFT_HLUTNM = "soft_lutpair37" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_68
       (.I0(\active_high_pitch_q_reg[31]_0 [13]),
        .I1(\active_high_pitch_q_reg[31]_0 [12]),
        .I2(\active_high_pitch_q_reg[31]_0 [15]),
        .I3(\active_high_pitch_q_reg[31]_0 [14]),
        .O(window_active_q_i_68_n_0));
  (* SOFT_HLUTNM = "soft_lutpair38" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_69
       (.I0(\active_high_pitch_q_reg[31]_0 [7]),
        .I1(\active_high_pitch_q_reg[31]_0 [4]),
        .I2(\active_high_pitch_q_reg[31]_0 [6]),
        .I3(\active_high_pitch_q_reg[31]_0 [5]),
        .O(window_active_q_i_69_n_0));
  LUT4 #(
    .INIT(16'h0004)) 
    window_active_q_i_7
       (.I0(window_active_q_i_19_n_0),
        .I1(window_active_q_i_20_n_0),
        .I2(window_active_q_i_21_n_0),
        .I3(window_active_q_i_22_n_0),
        .O(window_active_q_i_7_n_0));
  (* SOFT_HLUTNM = "soft_lutpair35" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_70
       (.I0(\active_high_pitch_q_reg[31]_0 [22]),
        .I1(\active_high_pitch_q_reg[31]_0 [21]),
        .I2(\active_high_pitch_q_reg[31]_0 [28]),
        .I3(\active_high_pitch_q_reg[31]_0 [18]),
        .O(window_active_q_i_70_n_0));
  (* SOFT_HLUTNM = "soft_lutpair36" *) 
  LUT4 #(
    .INIT(16'hFFFE)) 
    window_active_q_i_71
       (.I0(\active_high_pitch_q_reg[31]_0 [27]),
        .I1(\active_high_pitch_q_reg[31]_0 [26]),
        .I2(\active_high_pitch_q_reg[31]_0 [29]),
        .I3(\active_high_pitch_q_reg[31]_0 [23]),
        .O(window_active_q_i_71_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_73
       (.I0(Q[23]),
        .I1(\active_high_pitch_q_reg[31]_0 [23]),
        .I2(Q[22]),
        .I3(\active_high_pitch_q_reg[31]_0 [22]),
        .O(window_active_q_i_73_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_74
       (.I0(Q[21]),
        .I1(\active_high_pitch_q_reg[31]_0 [21]),
        .I2(Q[20]),
        .I3(\active_high_pitch_q_reg[31]_0 [20]),
        .O(window_active_q_i_74_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_75
       (.I0(Q[19]),
        .I1(\active_high_pitch_q_reg[31]_0 [19]),
        .I2(Q[18]),
        .I3(\active_high_pitch_q_reg[31]_0 [18]),
        .O(window_active_q_i_75_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_76
       (.I0(Q[17]),
        .I1(\active_high_pitch_q_reg[31]_0 [17]),
        .I2(Q[16]),
        .I3(\active_high_pitch_q_reg[31]_0 [16]),
        .O(window_active_q_i_76_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_77
       (.I0(\active_high_pitch_q_reg[31]_0 [23]),
        .I1(Q[23]),
        .I2(\active_high_pitch_q_reg[31]_0 [22]),
        .I3(Q[22]),
        .O(window_active_q_i_77_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_78
       (.I0(\active_high_pitch_q_reg[31]_0 [21]),
        .I1(Q[21]),
        .I2(\active_high_pitch_q_reg[31]_0 [20]),
        .I3(Q[20]),
        .O(window_active_q_i_78_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_79
       (.I0(\active_high_pitch_q_reg[31]_0 [19]),
        .I1(Q[19]),
        .I2(\active_high_pitch_q_reg[31]_0 [18]),
        .I3(Q[18]),
        .O(window_active_q_i_79_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    window_active_q_i_8
       (.I0(window_active_q_i_23_n_0),
        .I1(Q[27]),
        .I2(Q[5]),
        .I3(Q[25]),
        .I4(Q[23]),
        .I5(window_active_q_i_24_n_0),
        .O(window_active_q_i_8_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_80
       (.I0(\active_high_pitch_q_reg[31]_0 [17]),
        .I1(Q[17]),
        .I2(\active_high_pitch_q_reg[31]_0 [16]),
        .I3(Q[16]),
        .O(window_active_q_i_80_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_82
       (.I0(Q[23]),
        .I1(\active_high_yaw_q_reg[31]_0 [23]),
        .I2(Q[22]),
        .I3(\active_high_yaw_q_reg[31]_0 [22]),
        .O(window_active_q_i_82_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_83
       (.I0(Q[21]),
        .I1(\active_high_yaw_q_reg[31]_0 [21]),
        .I2(Q[20]),
        .I3(\active_high_yaw_q_reg[31]_0 [20]),
        .O(window_active_q_i_83_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_84
       (.I0(Q[19]),
        .I1(\active_high_yaw_q_reg[31]_0 [19]),
        .I2(Q[18]),
        .I3(\active_high_yaw_q_reg[31]_0 [18]),
        .O(window_active_q_i_84_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_85
       (.I0(Q[17]),
        .I1(\active_high_yaw_q_reg[31]_0 [17]),
        .I2(Q[16]),
        .I3(\active_high_yaw_q_reg[31]_0 [16]),
        .O(window_active_q_i_85_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_86
       (.I0(\active_high_yaw_q_reg[31]_0 [23]),
        .I1(Q[23]),
        .I2(\active_high_yaw_q_reg[31]_0 [22]),
        .I3(Q[22]),
        .O(window_active_q_i_86_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_87
       (.I0(\active_high_yaw_q_reg[31]_0 [21]),
        .I1(Q[21]),
        .I2(\active_high_yaw_q_reg[31]_0 [20]),
        .I3(Q[20]),
        .O(window_active_q_i_87_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_88
       (.I0(\active_high_yaw_q_reg[31]_0 [19]),
        .I1(Q[19]),
        .I2(\active_high_yaw_q_reg[31]_0 [18]),
        .I3(Q[18]),
        .O(window_active_q_i_88_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_89
       (.I0(\active_high_yaw_q_reg[31]_0 [17]),
        .I1(Q[17]),
        .I2(\active_high_yaw_q_reg[31]_0 [16]),
        .I3(Q[16]),
        .O(window_active_q_i_89_n_0));
  LUT6 #(
    .INIT(64'h0000000000000004)) 
    window_active_q_i_9
       (.I0(window_active_q_i_25_n_0),
        .I1(window_active_q_i_26_n_0),
        .I2(window_active_q_i_27_n_0),
        .I3(Q[3]),
        .I4(Q[6]),
        .I5(Q[4]),
        .O(window_active_q_i_9_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_91
       (.I0(Q[23]),
        .I1(\active_high_speed_q_reg[31]_0 [23]),
        .I2(Q[22]),
        .I3(\active_high_speed_q_reg[31]_0 [22]),
        .O(window_active_q_i_91_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_92
       (.I0(Q[21]),
        .I1(\active_high_speed_q_reg[31]_0 [21]),
        .I2(Q[20]),
        .I3(\active_high_speed_q_reg[31]_0 [20]),
        .O(window_active_q_i_92_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_93
       (.I0(Q[19]),
        .I1(\active_high_speed_q_reg[31]_0 [19]),
        .I2(Q[18]),
        .I3(\active_high_speed_q_reg[31]_0 [18]),
        .O(window_active_q_i_93_n_0));
  LUT4 #(
    .INIT(16'h22B2)) 
    window_active_q_i_94
       (.I0(Q[17]),
        .I1(\active_high_speed_q_reg[31]_0 [17]),
        .I2(Q[16]),
        .I3(\active_high_speed_q_reg[31]_0 [16]),
        .O(window_active_q_i_94_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_95
       (.I0(\active_high_speed_q_reg[31]_0 [23]),
        .I1(Q[23]),
        .I2(\active_high_speed_q_reg[31]_0 [22]),
        .I3(Q[22]),
        .O(window_active_q_i_95_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_96
       (.I0(\active_high_speed_q_reg[31]_0 [21]),
        .I1(Q[21]),
        .I2(\active_high_speed_q_reg[31]_0 [20]),
        .I3(Q[20]),
        .O(window_active_q_i_96_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_97
       (.I0(\active_high_speed_q_reg[31]_0 [19]),
        .I1(Q[19]),
        .I2(\active_high_speed_q_reg[31]_0 [18]),
        .I3(Q[18]),
        .O(window_active_q_i_97_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    window_active_q_i_98
       (.I0(\active_high_speed_q_reg[31]_0 [17]),
        .I1(Q[17]),
        .I2(\active_high_speed_q_reg[31]_0 [16]),
        .I3(Q[16]),
        .O(window_active_q_i_98_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_108
       (.CI(1'b0),
        .CO({window_active_q_reg_i_108_n_0,window_active_q_reg_i_108_n_1,window_active_q_reg_i_108_n_2,window_active_q_reg_i_108_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_134_n_0,window_active_q_i_135_n_0,window_active_q_i_136_n_0,window_active_q_i_137_n_0}),
        .O(NLW_window_active_q_reg_i_108_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_138_n_0,window_active_q_i_139_n_0,window_active_q_i_140_n_0,window_active_q_i_141_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_117
       (.CI(1'b0),
        .CO({window_active_q_reg_i_117_n_0,window_active_q_reg_i_117_n_1,window_active_q_reg_i_117_n_2,window_active_q_reg_i_117_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_142_n_0,window_active_q_i_143_n_0,window_active_q_i_144_n_0,window_active_q_i_145_n_0}),
        .O(NLW_window_active_q_reg_i_117_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_146_n_0,window_active_q_i_147_n_0,window_active_q_i_148_n_0,window_active_q_i_149_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_12
       (.CI(window_active_q_reg_i_32_n_0),
        .CO({eligible_application2,window_active_q_reg_i_12_n_1,window_active_q_reg_i_12_n_2,window_active_q_reg_i_12_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_33_n_0,window_active_q_i_34_n_0,window_active_q_i_35_n_0,window_active_q_i_36_n_0}),
        .O(NLW_window_active_q_reg_i_12_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_37_n_0,window_active_q_i_38_n_0,window_active_q_i_39_n_0,window_active_q_i_40_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_13
       (.CI(window_active_q_reg_i_41_n_0),
        .CO({eligible_application4,window_active_q_reg_i_13_n_1,window_active_q_reg_i_13_n_2,window_active_q_reg_i_13_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_42_n_0,window_active_q_i_43_n_0,window_active_q_i_44_n_0,window_active_q_i_45_n_0}),
        .O(NLW_window_active_q_reg_i_13_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_46_n_0,window_active_q_i_47_n_0,window_active_q_i_48_n_0,window_active_q_i_49_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_14
       (.CI(window_active_q_reg_i_50_n_0),
        .CO({eligible_application0,window_active_q_reg_i_14_n_1,window_active_q_reg_i_14_n_2,window_active_q_reg_i_14_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_51_n_0,window_active_q_i_52_n_0,window_active_q_i_53_n_0,window_active_q_i_54_n_0}),
        .O(NLW_window_active_q_reg_i_14_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_55_n_0,window_active_q_i_56_n_0,window_active_q_i_57_n_0,window_active_q_i_58_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_32
       (.CI(window_active_q_reg_i_72_n_0),
        .CO({window_active_q_reg_i_32_n_0,window_active_q_reg_i_32_n_1,window_active_q_reg_i_32_n_2,window_active_q_reg_i_32_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_73_n_0,window_active_q_i_74_n_0,window_active_q_i_75_n_0,window_active_q_i_76_n_0}),
        .O(NLW_window_active_q_reg_i_32_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_77_n_0,window_active_q_i_78_n_0,window_active_q_i_79_n_0,window_active_q_i_80_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_41
       (.CI(window_active_q_reg_i_81_n_0),
        .CO({window_active_q_reg_i_41_n_0,window_active_q_reg_i_41_n_1,window_active_q_reg_i_41_n_2,window_active_q_reg_i_41_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_82_n_0,window_active_q_i_83_n_0,window_active_q_i_84_n_0,window_active_q_i_85_n_0}),
        .O(NLW_window_active_q_reg_i_41_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_86_n_0,window_active_q_i_87_n_0,window_active_q_i_88_n_0,window_active_q_i_89_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_50
       (.CI(window_active_q_reg_i_90_n_0),
        .CO({window_active_q_reg_i_50_n_0,window_active_q_reg_i_50_n_1,window_active_q_reg_i_50_n_2,window_active_q_reg_i_50_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_91_n_0,window_active_q_i_92_n_0,window_active_q_i_93_n_0,window_active_q_i_94_n_0}),
        .O(NLW_window_active_q_reg_i_50_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_95_n_0,window_active_q_i_96_n_0,window_active_q_i_97_n_0,window_active_q_i_98_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_72
       (.CI(window_active_q_reg_i_99_n_0),
        .CO({window_active_q_reg_i_72_n_0,window_active_q_reg_i_72_n_1,window_active_q_reg_i_72_n_2,window_active_q_reg_i_72_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_100_n_0,window_active_q_i_101_n_0,window_active_q_i_102_n_0,window_active_q_i_103_n_0}),
        .O(NLW_window_active_q_reg_i_72_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_104_n_0,window_active_q_i_105_n_0,window_active_q_i_106_n_0,window_active_q_i_107_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_81
       (.CI(window_active_q_reg_i_108_n_0),
        .CO({window_active_q_reg_i_81_n_0,window_active_q_reg_i_81_n_1,window_active_q_reg_i_81_n_2,window_active_q_reg_i_81_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_109_n_0,window_active_q_i_110_n_0,window_active_q_i_111_n_0,window_active_q_i_112_n_0}),
        .O(NLW_window_active_q_reg_i_81_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_113_n_0,window_active_q_i_114_n_0,window_active_q_i_115_n_0,window_active_q_i_116_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_90
       (.CI(window_active_q_reg_i_117_n_0),
        .CO({window_active_q_reg_i_90_n_0,window_active_q_reg_i_90_n_1,window_active_q_reg_i_90_n_2,window_active_q_reg_i_90_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_118_n_0,window_active_q_i_119_n_0,window_active_q_i_120_n_0,window_active_q_i_121_n_0}),
        .O(NLW_window_active_q_reg_i_90_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_122_n_0,window_active_q_i_123_n_0,window_active_q_i_124_n_0,window_active_q_i_125_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 window_active_q_reg_i_99
       (.CI(1'b0),
        .CO({window_active_q_reg_i_99_n_0,window_active_q_reg_i_99_n_1,window_active_q_reg_i_99_n_2,window_active_q_reg_i_99_n_3}),
        .CYINIT(1'b0),
        .DI({window_active_q_i_126_n_0,window_active_q_i_127_n_0,window_active_q_i_128_n_0,window_active_q_i_129_n_0}),
        .O(NLW_window_active_q_reg_i_99_O_UNCONNECTED[3:0]),
        .S({window_active_q_i_130_n_0,window_active_q_i_131_n_0,window_active_q_i_132_n_0,window_active_q_i_133_n_0}));
  (* SOFT_HLUTNM = "soft_lutpair44" *) 
  LUT2 #(
    .INIT(4'h2)) 
    window_started_q_i_1
       (.I0(applied_q_reg_1),
        .I1(stop_0),
        .O(capture_rearm));
  (* SOFT_HLUTNM = "soft_lutpair22" *) 
  LUT5 #(
    .INIT(32'hFFFFDDCD)) 
    \window_tag_q[31]_i_1 
       (.I0(applied_q_reg_1),
        .I1(stop_0),
        .I2(failure_event_q_reg),
        .I3(applied_q_reg_0),
        .I4(rst),
        .O(window_active_q_reg));
endmodule

(* COUNT_AW = "32" *) (* COUNT_W = "32" *) (* COUNT_ZERO = "0" *) 
(* TAG_AW = "32" *) (* TAG_W = "32" *) (* TAG_ZERO = "0" *) 
(* WITNESS_AW = "64" *) (* WITNESS_W = "64" *) 
(* NotValidForBitStream *)
module deepeye_pwm_applied_capture
   (clk,
    rst,
    stop,
    cfg_valid,
    cfg_ready,
    cfg_period,
    cfg_high_yaw,
    cfg_high_pitch,
    cfg_high_speed,
    cfg_tag,
    sample_levels,
    out_ready,
    accepted,
    rejected,
    applied,
    frame_start,
    running,
    pending,
    pwm,
    active_period,
    active_high_yaw,
    active_high_pitch,
    active_high_speed,
    active_tag,
    window_active,
    window_started,
    capture_armed,
    out_valid,
    out_period,
    out_high0,
    out_high1,
    out_high2,
    out_start,
    out_end,
    out_tag,
    expected_period,
    expected_high0,
    expected_high1,
    expected_high2,
    expected_tag,
    raw_fault_events,
    failure_event,
    failure_code);
  input clk;
  input rst;
  input stop;
  input cfg_valid;
  output cfg_ready;
  input [31:0]cfg_period;
  input [31:0]cfg_high_yaw;
  input [31:0]cfg_high_pitch;
  input [31:0]cfg_high_speed;
  input [31:0]cfg_tag;
  input [2:0]sample_levels;
  input out_ready;
  output accepted;
  output rejected;
  output applied;
  output frame_start;
  output running;
  output pending;
  output [2:0]pwm;
  output [31:0]active_period;
  output [31:0]active_high_yaw;
  output [31:0]active_high_pitch;
  output [31:0]active_high_speed;
  output [31:0]active_tag;
  output window_active;
  output window_started;
  output capture_armed;
  output out_valid;
  output [31:0]out_period;
  output [31:0]out_high0;
  output [31:0]out_high1;
  output [31:0]out_high2;
  output [63:0]out_start;
  output [63:0]out_end;
  output [31:0]out_tag;
  output [31:0]expected_period;
  output [31:0]expected_high0;
  output [31:0]expected_high1;
  output [31:0]expected_high2;
  output [31:0]expected_tag;
  output [3:0]raw_fault_events;
  output failure_event;
  output [2:0]failure_code;

  wire accepted;
  wire [31:0]active_high_pitch;
  wire [31:0]active_high_speed;
  wire [31:0]active_high_yaw;
  wire [31:0]active_period;
  wire [31:0]active_tag;
  wire applied;
  wire capture_armed;
  wire capture_rearm;
  wire [31:0]cfg_high_pitch;
  wire [31:0]cfg_high_speed;
  wire [31:0]cfg_high_yaw;
  wire [31:0]cfg_period;
  wire cfg_ready;
  wire [31:0]cfg_tag;
  wire cfg_valid;
  wire clk;
  wire [31:0]expected_high0;
  wire [31:0]expected_high1;
  wire [31:0]expected_high2;
  wire [31:0]expected_period;
  wire [31:0]expected_tag;
  wire [2:0]failure_code;
  wire failure_event;
  wire failure_event_q2_out;
  wire frame_start;
  wire [63:0]out_end;
  wire [31:0]out_high0;
  wire [31:0]out_high1;
  wire [31:0]out_high2;
  wire [31:0]out_period;
  wire out_ready;
  wire [63:0]out_start;
  wire [31:0]out_tag;
  wire out_valid;
  wire [31:0]p_1_in__0;
  wire pending;
  wire [2:0]pwm;
  wire [3:0]raw_fault_events;
  wire rejected;
  wire rst;
  wire running;
  wire [2:0]sample_levels;
  wire stop;
  wire u_capture_n_169;
  wire u_capture_n_170;
  wire u_capture_n_5;
  wire u_capture_n_6;
  wire u_capture_n_7;
  wire u_generator_n_10;
  wire u_generator_n_11;
  wire u_generator_n_12;
  wire u_generator_n_173;
  wire u_generator_n_174;
  wire u_generator_n_175;
  wire u_generator_n_176;
  wire u_generator_n_177;
  wire u_generator_n_178;
  wire u_generator_n_179;
  wire u_generator_n_180;
  wire u_generator_n_181;
  wire u_generator_n_182;
  wire u_generator_n_183;
  wire u_generator_n_184;
  wire u_generator_n_185;
  wire u_generator_n_186;
  wire u_generator_n_187;
  wire u_generator_n_188;
  wire u_generator_n_189;
  wire u_generator_n_190;
  wire u_generator_n_191;
  wire u_generator_n_192;
  wire u_generator_n_193;
  wire u_generator_n_194;
  wire u_generator_n_195;
  wire u_generator_n_196;
  wire u_generator_n_197;
  wire u_generator_n_198;
  wire u_generator_n_199;
  wire u_generator_n_200;
  wire u_generator_n_201;
  wire u_generator_n_202;
  wire u_generator_n_203;
  wire u_generator_n_204;
  wire u_generator_n_205;
  wire u_generator_n_206;
  wire u_generator_n_207;
  wire u_generator_n_208;
  wire u_generator_n_209;
  wire u_generator_n_210;
  wire u_generator_n_211;
  wire u_generator_n_212;
  wire u_generator_n_213;
  wire u_generator_n_214;
  wire u_generator_n_215;
  wire u_generator_n_216;
  wire u_generator_n_217;
  wire u_generator_n_218;
  wire u_generator_n_219;
  wire u_generator_n_220;
  wire u_generator_n_221;
  wire u_generator_n_222;
  wire u_generator_n_223;
  wire u_generator_n_224;
  wire u_generator_n_225;
  wire u_generator_n_226;
  wire u_generator_n_227;
  wire u_generator_n_228;
  wire u_generator_n_229;
  wire u_generator_n_230;
  wire u_generator_n_231;
  wire u_generator_n_232;
  wire u_generator_n_233;
  wire u_generator_n_234;
  wire u_generator_n_235;
  wire u_generator_n_236;
  wire u_generator_n_237;
  wire u_generator_n_238;
  wire u_generator_n_239;
  wire u_generator_n_240;
  wire u_generator_n_241;
  wire u_generator_n_242;
  wire u_generator_n_243;
  wire u_generator_n_244;
  wire u_generator_n_245;
  wire u_generator_n_246;
  wire u_generator_n_247;
  wire u_generator_n_248;
  wire u_generator_n_249;
  wire u_generator_n_250;
  wire u_generator_n_251;
  wire u_generator_n_252;
  wire u_generator_n_253;
  wire u_generator_n_254;
  wire u_generator_n_255;
  wire u_generator_n_256;
  wire u_generator_n_257;
  wire u_generator_n_258;
  wire u_generator_n_259;
  wire u_generator_n_260;
  wire u_generator_n_261;
  wire u_generator_n_262;
  wire u_generator_n_263;
  wire u_generator_n_264;
  wire u_generator_n_265;
  wire u_generator_n_266;
  wire u_generator_n_267;
  wire u_generator_n_268;
  wire u_generator_n_301;
  wire u_generator_n_302;
  wire u_generator_n_303;
  wire u_generator_n_304;
  wire u_generator_n_305;
  wire u_generator_n_306;
  wire u_generator_n_307;
  wire u_generator_n_308;
  wire u_generator_n_309;
  wire u_generator_n_310;
  wire u_generator_n_311;
  wire u_generator_n_312;
  wire u_generator_n_313;
  wire u_generator_n_314;
  wire u_generator_n_315;
  wire u_generator_n_316;
  wire u_generator_n_317;
  wire u_generator_n_318;
  wire u_generator_n_319;
  wire u_generator_n_320;
  wire u_generator_n_321;
  wire u_generator_n_322;
  wire u_generator_n_323;
  wire u_generator_n_324;
  wire u_generator_n_325;
  wire u_generator_n_326;
  wire u_generator_n_327;
  wire u_generator_n_328;
  wire u_generator_n_329;
  wire u_generator_n_330;
  wire u_generator_n_331;
  wire u_generator_n_332;
  wire u_generator_n_6;
  wire u_generator_n_7;
  wire u_generator_n_9;
  wire window_active;
  wire window_started;

  FDRE \expected_high0_q_reg[0] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[0]),
        .Q(expected_high0[0]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[10] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[10]),
        .Q(expected_high0[10]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[11] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[11]),
        .Q(expected_high0[11]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[12] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[12]),
        .Q(expected_high0[12]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[13] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[13]),
        .Q(expected_high0[13]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[14] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[14]),
        .Q(expected_high0[14]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[15] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[15]),
        .Q(expected_high0[15]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[16] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[16]),
        .Q(expected_high0[16]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[17] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[17]),
        .Q(expected_high0[17]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[18] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[18]),
        .Q(expected_high0[18]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[19] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[19]),
        .Q(expected_high0[19]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[1] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[1]),
        .Q(expected_high0[1]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[20] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[20]),
        .Q(expected_high0[20]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[21] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[21]),
        .Q(expected_high0[21]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[22] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[22]),
        .Q(expected_high0[22]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[23] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[23]),
        .Q(expected_high0[23]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[24] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[24]),
        .Q(expected_high0[24]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[25] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[25]),
        .Q(expected_high0[25]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[26] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[26]),
        .Q(expected_high0[26]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[27] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[27]),
        .Q(expected_high0[27]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[28] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[28]),
        .Q(expected_high0[28]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[29] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[29]),
        .Q(expected_high0[29]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[2] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[2]),
        .Q(expected_high0[2]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[30] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[30]),
        .Q(expected_high0[30]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[31] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[31]),
        .Q(expected_high0[31]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[3] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[3]),
        .Q(expected_high0[3]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[4] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[4]),
        .Q(expected_high0[4]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[5] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[5]),
        .Q(expected_high0[5]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[6] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[6]),
        .Q(expected_high0[6]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[7] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[7]),
        .Q(expected_high0[7]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[8] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[8]),
        .Q(expected_high0[8]),
        .R(u_generator_n_7));
  FDRE \expected_high0_q_reg[9] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(p_1_in__0[9]),
        .Q(expected_high0[9]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[0] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_204),
        .Q(expected_high1[0]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[10] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_194),
        .Q(expected_high1[10]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[11] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_193),
        .Q(expected_high1[11]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[12] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_192),
        .Q(expected_high1[12]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[13] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_191),
        .Q(expected_high1[13]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[14] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_190),
        .Q(expected_high1[14]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[15] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_189),
        .Q(expected_high1[15]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[16] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_188),
        .Q(expected_high1[16]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[17] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_187),
        .Q(expected_high1[17]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[18] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_186),
        .Q(expected_high1[18]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[19] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_185),
        .Q(expected_high1[19]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[1] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_203),
        .Q(expected_high1[1]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[20] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_184),
        .Q(expected_high1[20]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[21] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_183),
        .Q(expected_high1[21]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[22] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_182),
        .Q(expected_high1[22]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[23] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_181),
        .Q(expected_high1[23]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[24] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_180),
        .Q(expected_high1[24]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[25] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_179),
        .Q(expected_high1[25]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[26] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_178),
        .Q(expected_high1[26]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[27] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_177),
        .Q(expected_high1[27]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[28] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_176),
        .Q(expected_high1[28]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[29] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_175),
        .Q(expected_high1[29]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[2] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_202),
        .Q(expected_high1[2]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[30] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_174),
        .Q(expected_high1[30]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[31] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_173),
        .Q(expected_high1[31]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[3] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_201),
        .Q(expected_high1[3]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[4] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_200),
        .Q(expected_high1[4]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[5] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_199),
        .Q(expected_high1[5]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[6] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_198),
        .Q(expected_high1[6]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[7] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_197),
        .Q(expected_high1[7]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[8] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_196),
        .Q(expected_high1[8]),
        .R(u_generator_n_7));
  FDRE \expected_high1_q_reg[9] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_195),
        .Q(expected_high1[9]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[0] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_236),
        .Q(expected_high2[0]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[10] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_226),
        .Q(expected_high2[10]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[11] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_225),
        .Q(expected_high2[11]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[12] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_224),
        .Q(expected_high2[12]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[13] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_223),
        .Q(expected_high2[13]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[14] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_222),
        .Q(expected_high2[14]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[15] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_221),
        .Q(expected_high2[15]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[16] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_220),
        .Q(expected_high2[16]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[17] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_219),
        .Q(expected_high2[17]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[18] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_218),
        .Q(expected_high2[18]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[19] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_217),
        .Q(expected_high2[19]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[1] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_235),
        .Q(expected_high2[1]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[20] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_216),
        .Q(expected_high2[20]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[21] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_215),
        .Q(expected_high2[21]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[22] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_214),
        .Q(expected_high2[22]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[23] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_213),
        .Q(expected_high2[23]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[24] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_212),
        .Q(expected_high2[24]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[25] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_211),
        .Q(expected_high2[25]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[26] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_210),
        .Q(expected_high2[26]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[27] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_209),
        .Q(expected_high2[27]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[28] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_208),
        .Q(expected_high2[28]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[29] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_207),
        .Q(expected_high2[29]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[2] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_234),
        .Q(expected_high2[2]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[30] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_206),
        .Q(expected_high2[30]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[31] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_205),
        .Q(expected_high2[31]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[3] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_233),
        .Q(expected_high2[3]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[4] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_232),
        .Q(expected_high2[4]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[5] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_231),
        .Q(expected_high2[5]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[6] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_230),
        .Q(expected_high2[6]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[7] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_229),
        .Q(expected_high2[7]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[8] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_228),
        .Q(expected_high2[8]),
        .R(u_generator_n_7));
  FDRE \expected_high2_q_reg[9] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_227),
        .Q(expected_high2[9]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[0] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_332),
        .Q(expected_period[0]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[10] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_322),
        .Q(expected_period[10]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[11] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_321),
        .Q(expected_period[11]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[12] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_320),
        .Q(expected_period[12]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[13] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_319),
        .Q(expected_period[13]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[14] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_318),
        .Q(expected_period[14]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[15] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_317),
        .Q(expected_period[15]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[16] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_316),
        .Q(expected_period[16]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[17] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_315),
        .Q(expected_period[17]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[18] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_314),
        .Q(expected_period[18]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[19] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_313),
        .Q(expected_period[19]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[1] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_331),
        .Q(expected_period[1]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[20] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_312),
        .Q(expected_period[20]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[21] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_311),
        .Q(expected_period[21]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[22] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_310),
        .Q(expected_period[22]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[23] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_309),
        .Q(expected_period[23]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[24] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_308),
        .Q(expected_period[24]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[25] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_307),
        .Q(expected_period[25]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[26] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_306),
        .Q(expected_period[26]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[27] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_305),
        .Q(expected_period[27]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[28] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_304),
        .Q(expected_period[28]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[29] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_303),
        .Q(expected_period[29]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[2] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_330),
        .Q(expected_period[2]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[30] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_302),
        .Q(expected_period[30]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[31] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_301),
        .Q(expected_period[31]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[3] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_329),
        .Q(expected_period[3]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[4] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_328),
        .Q(expected_period[4]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[5] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_327),
        .Q(expected_period[5]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[6] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_326),
        .Q(expected_period[6]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[7] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_325),
        .Q(expected_period[7]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[8] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_324),
        .Q(expected_period[8]),
        .R(u_generator_n_7));
  FDRE \expected_period_q_reg[9] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_323),
        .Q(expected_period[9]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[0] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_268),
        .Q(expected_tag[0]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[10] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_258),
        .Q(expected_tag[10]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[11] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_257),
        .Q(expected_tag[11]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[12] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_256),
        .Q(expected_tag[12]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[13] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_255),
        .Q(expected_tag[13]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[14] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_254),
        .Q(expected_tag[14]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[15] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_253),
        .Q(expected_tag[15]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[16] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_252),
        .Q(expected_tag[16]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[17] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_251),
        .Q(expected_tag[17]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[18] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_250),
        .Q(expected_tag[18]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[19] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_249),
        .Q(expected_tag[19]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[1] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_267),
        .Q(expected_tag[1]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[20] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_248),
        .Q(expected_tag[20]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[21] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_247),
        .Q(expected_tag[21]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[22] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_246),
        .Q(expected_tag[22]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[23] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_245),
        .Q(expected_tag[23]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[24] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_244),
        .Q(expected_tag[24]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[25] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_243),
        .Q(expected_tag[25]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[26] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_242),
        .Q(expected_tag[26]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[27] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_241),
        .Q(expected_tag[27]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[28] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_240),
        .Q(expected_tag[28]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[29] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_239),
        .Q(expected_tag[29]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[2] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_266),
        .Q(expected_tag[2]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[30] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_238),
        .Q(expected_tag[30]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[31] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_237),
        .Q(expected_tag[31]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[3] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_265),
        .Q(expected_tag[3]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[4] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_264),
        .Q(expected_tag[4]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[5] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_263),
        .Q(expected_tag[5]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[6] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_262),
        .Q(expected_tag[6]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[7] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_261),
        .Q(expected_tag[7]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[8] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_260),
        .Q(expected_tag[8]),
        .R(u_generator_n_7));
  FDRE \expected_tag_q_reg[9] 
       (.C(clk),
        .CE(u_capture_n_6),
        .D(u_generator_n_259),
        .Q(expected_tag[9]),
        .R(u_generator_n_7));
  FDRE \failure_code_q_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(u_capture_n_5),
        .Q(failure_code[0]),
        .R(1'b0));
  FDRE \failure_code_q_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(u_capture_n_169),
        .Q(failure_code[1]),
        .R(1'b0));
  FDRE \failure_code_q_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(u_capture_n_170),
        .Q(failure_code[2]),
        .R(1'b0));
  FDRE failure_event_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(u_generator_n_10),
        .Q(failure_event),
        .R(1'b0));
  deepeye_pwm_coherent_capture u_capture
       (.E(u_capture_n_6),
        .active_tag(active_tag),
        .armed_q_reg_0(capture_armed),
        .capture_rearm(capture_rearm),
        .clk(clk),
        .expected_high0(expected_high0),
        .expected_high1(expected_high1),
        .expected_high2(expected_high2),
        .expected_period(expected_period),
        .expected_tag(expected_tag),
        .failure_code(failure_code),
        .\failure_code_q_reg[0] (u_generator_n_12),
        .\failure_code_q_reg[1] (u_capture_n_169),
        .\failure_code_q_reg[1]_0 (window_active),
        .\failure_code_q_reg[1]_1 (u_generator_n_11),
        .\failure_code_q_reg[2] (u_capture_n_170),
        .\high2_q_reg[31]_0 (u_generator_n_6),
        .incoherent_event_q_reg_0(raw_fault_events[0]),
        .out_end(out_end),
        .out_high0(out_high0),
        .out_high1(out_high1),
        .out_high2(out_high2),
        .out_period(out_period),
        .out_ready(out_ready),
        .out_start(out_start),
        .out_tag(out_tag),
        .out_valid(out_valid),
        .out_valid_0(u_generator_n_7),
        .overrun_event_q_reg_0(raw_fault_events[3]),
        .overrun_event_q_reg_1(u_capture_n_7),
        .period_overflow_event_q_reg_0(raw_fault_events[1]),
        .period_overflow_event_q_reg_1(u_capture_n_5),
        .sample_levels(sample_levels),
        .window_active_q_reg(applied),
        .\window_tag_q_reg[0]_0 (failure_event_q2_out),
        .\window_tag_q_reg[31]_0 (u_generator_n_9),
        .witness_overflow_event_q_reg_0(raw_fault_events[2]));
  deepeye_atomic_pwm u_generator
       (.D(p_1_in__0),
        .Q(active_period),
        .accepted(accepted),
        .\active_high_pitch_q_reg[31]_0 (active_high_pitch),
        .\active_high_pitch_q_reg[31]_1 ({u_generator_n_173,u_generator_n_174,u_generator_n_175,u_generator_n_176,u_generator_n_177,u_generator_n_178,u_generator_n_179,u_generator_n_180,u_generator_n_181,u_generator_n_182,u_generator_n_183,u_generator_n_184,u_generator_n_185,u_generator_n_186,u_generator_n_187,u_generator_n_188,u_generator_n_189,u_generator_n_190,u_generator_n_191,u_generator_n_192,u_generator_n_193,u_generator_n_194,u_generator_n_195,u_generator_n_196,u_generator_n_197,u_generator_n_198,u_generator_n_199,u_generator_n_200,u_generator_n_201,u_generator_n_202,u_generator_n_203,u_generator_n_204}),
        .\active_high_speed_q_reg[31]_0 (active_high_speed),
        .\active_high_speed_q_reg[31]_1 ({u_generator_n_205,u_generator_n_206,u_generator_n_207,u_generator_n_208,u_generator_n_209,u_generator_n_210,u_generator_n_211,u_generator_n_212,u_generator_n_213,u_generator_n_214,u_generator_n_215,u_generator_n_216,u_generator_n_217,u_generator_n_218,u_generator_n_219,u_generator_n_220,u_generator_n_221,u_generator_n_222,u_generator_n_223,u_generator_n_224,u_generator_n_225,u_generator_n_226,u_generator_n_227,u_generator_n_228,u_generator_n_229,u_generator_n_230,u_generator_n_231,u_generator_n_232,u_generator_n_233,u_generator_n_234,u_generator_n_235,u_generator_n_236}),
        .\active_high_yaw_q_reg[31]_0 (active_high_yaw),
        .\active_period_q_reg[31]_0 ({u_generator_n_301,u_generator_n_302,u_generator_n_303,u_generator_n_304,u_generator_n_305,u_generator_n_306,u_generator_n_307,u_generator_n_308,u_generator_n_309,u_generator_n_310,u_generator_n_311,u_generator_n_312,u_generator_n_313,u_generator_n_314,u_generator_n_315,u_generator_n_316,u_generator_n_317,u_generator_n_318,u_generator_n_319,u_generator_n_320,u_generator_n_321,u_generator_n_322,u_generator_n_323,u_generator_n_324,u_generator_n_325,u_generator_n_326,u_generator_n_327,u_generator_n_328,u_generator_n_329,u_generator_n_330,u_generator_n_331,u_generator_n_332}),
        .active_tag(active_tag),
        .\active_tag_q_reg[31]_0 ({u_generator_n_237,u_generator_n_238,u_generator_n_239,u_generator_n_240,u_generator_n_241,u_generator_n_242,u_generator_n_243,u_generator_n_244,u_generator_n_245,u_generator_n_246,u_generator_n_247,u_generator_n_248,u_generator_n_249,u_generator_n_250,u_generator_n_251,u_generator_n_252,u_generator_n_253,u_generator_n_254,u_generator_n_255,u_generator_n_256,u_generator_n_257,u_generator_n_258,u_generator_n_259,u_generator_n_260,u_generator_n_261,u_generator_n_262,u_generator_n_263,u_generator_n_264,u_generator_n_265,u_generator_n_266,u_generator_n_267,u_generator_n_268}),
        .applied_q_reg_0(applied),
        .applied_q_reg_1(failure_event_q2_out),
        .applied_q_reg_2(u_generator_n_12),
        .capture_rearm(capture_rearm),
        .cfg_high_pitch(cfg_high_pitch),
        .cfg_high_speed(cfg_high_speed),
        .cfg_high_yaw(cfg_high_yaw),
        .cfg_period(cfg_period),
        .cfg_ready(cfg_ready),
        .cfg_tag(cfg_tag),
        .cfg_valid(cfg_valid),
        .clk(clk),
        .failure_event_q_reg(window_active),
        .failure_event_q_reg_0(u_capture_n_7),
        .frame_start(frame_start),
        .pending_q_reg_0(pending),
        .pwm(pwm),
        .raw_fault_events(raw_fault_events[2]),
        .rejected(rejected),
        .rst(rst),
        .rst_0(u_generator_n_6),
        .running_q_reg_0(running),
        .stop(stop),
        .stop_0(u_generator_n_7),
        .stop_1(u_generator_n_11),
        .window_active_q_reg(u_generator_n_9),
        .window_active_q_reg_0(u_generator_n_10));
  FDRE window_active_q_reg
       (.C(clk),
        .CE(u_capture_n_6),
        .D(failure_event_q2_out),
        .Q(window_active),
        .R(u_generator_n_7));
  FDRE window_started_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(capture_rearm),
        .Q(window_started),
        .R(1'b0));
endmodule

module deepeye_pwm_coherent_capture
   (armed_q_reg_0,
    incoherent_event_q_reg_0,
    period_overflow_event_q_reg_0,
    witness_overflow_event_q_reg_0,
    overrun_event_q_reg_0,
    period_overflow_event_q_reg_1,
    E,
    overrun_event_q_reg_1,
    out_valid,
    out_high0,
    out_high1,
    out_high2,
    out_tag,
    out_period,
    \failure_code_q_reg[1] ,
    \failure_code_q_reg[2] ,
    out_start,
    out_end,
    clk,
    \high2_q_reg[31]_0 ,
    sample_levels,
    \failure_code_q_reg[0] ,
    failure_code,
    window_active_q_reg,
    \failure_code_q_reg[1]_0 ,
    out_ready,
    out_valid_0,
    expected_high0,
    expected_high1,
    expected_high2,
    expected_tag,
    expected_period,
    \failure_code_q_reg[1]_1 ,
    capture_rearm,
    \window_tag_q_reg[31]_0 ,
    \window_tag_q_reg[0]_0 ,
    active_tag);
  output armed_q_reg_0;
  output incoherent_event_q_reg_0;
  output period_overflow_event_q_reg_0;
  output witness_overflow_event_q_reg_0;
  output overrun_event_q_reg_0;
  output period_overflow_event_q_reg_1;
  output [0:0]E;
  output overrun_event_q_reg_1;
  output out_valid;
  output [31:0]out_high0;
  output [31:0]out_high1;
  output [31:0]out_high2;
  output [31:0]out_tag;
  output [31:0]out_period;
  output \failure_code_q_reg[1] ;
  output \failure_code_q_reg[2] ;
  output [63:0]out_start;
  output [63:0]out_end;
  input clk;
  input \high2_q_reg[31]_0 ;
  input [2:0]sample_levels;
  input \failure_code_q_reg[0] ;
  input [2:0]failure_code;
  input window_active_q_reg;
  input \failure_code_q_reg[1]_0 ;
  input out_ready;
  input out_valid_0;
  input [31:0]expected_high0;
  input [31:0]expected_high1;
  input [31:0]expected_high2;
  input [31:0]expected_tag;
  input [31:0]expected_period;
  input \failure_code_q_reg[1]_1 ;
  input capture_rearm;
  input \window_tag_q_reg[31]_0 ;
  input [0:0]\window_tag_q_reg[0]_0 ;
  input [31:0]active_tag;

  wire [0:0]E;
  wire [31:0]active_tag;
  wire armed_q_i_10_n_0;
  wire armed_q_i_11_n_0;
  wire armed_q_i_12_n_0;
  wire armed_q_i_13_n_0;
  wire armed_q_i_14_n_0;
  wire armed_q_i_15_n_0;
  wire armed_q_i_16_n_0;
  wire armed_q_i_17_n_0;
  wire armed_q_i_18_n_0;
  wire armed_q_i_1_n_0;
  wire armed_q_i_2_n_0;
  wire armed_q_i_3_n_0;
  wire armed_q_i_4_n_0;
  wire armed_q_i_5_n_0;
  wire armed_q_i_6_n_0;
  wire armed_q_i_7_n_0;
  wire armed_q_i_8_n_0;
  wire armed_q_i_9_n_0;
  wire armed_q_reg_0;
  wire capture_out_ready;
  wire capture_rearm;
  wire clk;
  wire [31:0]expected_high0;
  wire [31:0]expected_high1;
  wire [31:0]expected_high2;
  wire [31:0]expected_period;
  wire [31:0]expected_tag;
  wire [2:0]failure_code;
  wire [2:1]failure_code_q;
  wire \failure_code_q[0]_i_3_n_0 ;
  wire \failure_code_q[2]_i_2_n_0 ;
  wire \failure_code_q[2]_i_5_n_0 ;
  wire \failure_code_q_reg[0] ;
  wire \failure_code_q_reg[1] ;
  wire \failure_code_q_reg[1]_0 ;
  wire \failure_code_q_reg[1]_1 ;
  wire \failure_code_q_reg[2] ;
  wire \fall_seen_q[0]_i_1_n_0 ;
  wire \fall_seen_q[0]_i_2_n_0 ;
  wire \fall_seen_q[1]_i_1_n_0 ;
  wire \fall_seen_q[1]_i_2_n_0 ;
  wire \fall_seen_q[2]_i_1_n_0 ;
  wire \fall_seen_q[2]_i_2_n_0 ;
  wire \fall_seen_q_reg_n_0_[0] ;
  wire \fall_seen_q_reg_n_0_[1] ;
  wire \high0_q[31]_i_1_n_0 ;
  wire \high0_q_reg_n_0_[0] ;
  wire \high0_q_reg_n_0_[10] ;
  wire \high0_q_reg_n_0_[11] ;
  wire \high0_q_reg_n_0_[12] ;
  wire \high0_q_reg_n_0_[13] ;
  wire \high0_q_reg_n_0_[14] ;
  wire \high0_q_reg_n_0_[15] ;
  wire \high0_q_reg_n_0_[16] ;
  wire \high0_q_reg_n_0_[17] ;
  wire \high0_q_reg_n_0_[18] ;
  wire \high0_q_reg_n_0_[19] ;
  wire \high0_q_reg_n_0_[1] ;
  wire \high0_q_reg_n_0_[20] ;
  wire \high0_q_reg_n_0_[21] ;
  wire \high0_q_reg_n_0_[22] ;
  wire \high0_q_reg_n_0_[23] ;
  wire \high0_q_reg_n_0_[24] ;
  wire \high0_q_reg_n_0_[25] ;
  wire \high0_q_reg_n_0_[26] ;
  wire \high0_q_reg_n_0_[27] ;
  wire \high0_q_reg_n_0_[28] ;
  wire \high0_q_reg_n_0_[29] ;
  wire \high0_q_reg_n_0_[2] ;
  wire \high0_q_reg_n_0_[30] ;
  wire \high0_q_reg_n_0_[31] ;
  wire \high0_q_reg_n_0_[3] ;
  wire \high0_q_reg_n_0_[4] ;
  wire \high0_q_reg_n_0_[5] ;
  wire \high0_q_reg_n_0_[6] ;
  wire \high0_q_reg_n_0_[7] ;
  wire \high0_q_reg_n_0_[8] ;
  wire \high0_q_reg_n_0_[9] ;
  wire \high1_q[31]_i_1_n_0 ;
  wire \high1_q_reg_n_0_[0] ;
  wire \high1_q_reg_n_0_[10] ;
  wire \high1_q_reg_n_0_[11] ;
  wire \high1_q_reg_n_0_[12] ;
  wire \high1_q_reg_n_0_[13] ;
  wire \high1_q_reg_n_0_[14] ;
  wire \high1_q_reg_n_0_[15] ;
  wire \high1_q_reg_n_0_[16] ;
  wire \high1_q_reg_n_0_[17] ;
  wire \high1_q_reg_n_0_[18] ;
  wire \high1_q_reg_n_0_[19] ;
  wire \high1_q_reg_n_0_[1] ;
  wire \high1_q_reg_n_0_[20] ;
  wire \high1_q_reg_n_0_[21] ;
  wire \high1_q_reg_n_0_[22] ;
  wire \high1_q_reg_n_0_[23] ;
  wire \high1_q_reg_n_0_[24] ;
  wire \high1_q_reg_n_0_[25] ;
  wire \high1_q_reg_n_0_[26] ;
  wire \high1_q_reg_n_0_[27] ;
  wire \high1_q_reg_n_0_[28] ;
  wire \high1_q_reg_n_0_[29] ;
  wire \high1_q_reg_n_0_[2] ;
  wire \high1_q_reg_n_0_[30] ;
  wire \high1_q_reg_n_0_[31] ;
  wire \high1_q_reg_n_0_[3] ;
  wire \high1_q_reg_n_0_[4] ;
  wire \high1_q_reg_n_0_[5] ;
  wire \high1_q_reg_n_0_[6] ;
  wire \high1_q_reg_n_0_[7] ;
  wire \high1_q_reg_n_0_[8] ;
  wire \high1_q_reg_n_0_[9] ;
  wire \high2_q[31]_i_1_n_0 ;
  wire \high2_q_reg[31]_0 ;
  wire \high2_q_reg_n_0_[0] ;
  wire \high2_q_reg_n_0_[10] ;
  wire \high2_q_reg_n_0_[11] ;
  wire \high2_q_reg_n_0_[12] ;
  wire \high2_q_reg_n_0_[13] ;
  wire \high2_q_reg_n_0_[14] ;
  wire \high2_q_reg_n_0_[15] ;
  wire \high2_q_reg_n_0_[16] ;
  wire \high2_q_reg_n_0_[17] ;
  wire \high2_q_reg_n_0_[18] ;
  wire \high2_q_reg_n_0_[19] ;
  wire \high2_q_reg_n_0_[1] ;
  wire \high2_q_reg_n_0_[20] ;
  wire \high2_q_reg_n_0_[21] ;
  wire \high2_q_reg_n_0_[22] ;
  wire \high2_q_reg_n_0_[23] ;
  wire \high2_q_reg_n_0_[24] ;
  wire \high2_q_reg_n_0_[25] ;
  wire \high2_q_reg_n_0_[26] ;
  wire \high2_q_reg_n_0_[27] ;
  wire \high2_q_reg_n_0_[28] ;
  wire \high2_q_reg_n_0_[29] ;
  wire \high2_q_reg_n_0_[2] ;
  wire \high2_q_reg_n_0_[30] ;
  wire \high2_q_reg_n_0_[31] ;
  wire \high2_q_reg_n_0_[3] ;
  wire \high2_q_reg_n_0_[4] ;
  wire \high2_q_reg_n_0_[5] ;
  wire \high2_q_reg_n_0_[6] ;
  wire \high2_q_reg_n_0_[7] ;
  wire \high2_q_reg_n_0_[8] ;
  wire \high2_q_reg_n_0_[9] ;
  wire incoherent_event_q2;
  wire incoherent_event_q4;
  wire incoherent_event_q6;
  wire incoherent_event_q_i_1_n_0;
  wire incoherent_event_q_i_2_n_0;
  wire incoherent_event_q_reg_0;
  wire [63:0]out_end;
  wire [31:0]out_high0;
  wire [31:0]out_high1;
  wire [31:0]out_high2;
  wire [31:0]out_period;
  wire out_ready;
  wire [63:0]out_start;
  wire [31:0]out_tag;
  wire out_valid;
  wire out_valid_0;
  wire out_valid_INST_0_i_10_n_0;
  wire out_valid_INST_0_i_10_n_1;
  wire out_valid_INST_0_i_10_n_2;
  wire out_valid_INST_0_i_10_n_3;
  wire out_valid_INST_0_i_11_n_0;
  wire out_valid_INST_0_i_12_n_0;
  wire out_valid_INST_0_i_13_n_0;
  wire out_valid_INST_0_i_14_n_0;
  wire out_valid_INST_0_i_14_n_1;
  wire out_valid_INST_0_i_14_n_2;
  wire out_valid_INST_0_i_14_n_3;
  wire out_valid_INST_0_i_15_n_0;
  wire out_valid_INST_0_i_16_n_0;
  wire out_valid_INST_0_i_17_n_0;
  wire out_valid_INST_0_i_18_n_0;
  wire out_valid_INST_0_i_18_n_1;
  wire out_valid_INST_0_i_18_n_2;
  wire out_valid_INST_0_i_18_n_3;
  wire out_valid_INST_0_i_19_n_0;
  wire out_valid_INST_0_i_1_n_0;
  wire out_valid_INST_0_i_20_n_0;
  wire out_valid_INST_0_i_21_n_0;
  wire out_valid_INST_0_i_22_n_0;
  wire out_valid_INST_0_i_22_n_1;
  wire out_valid_INST_0_i_22_n_2;
  wire out_valid_INST_0_i_22_n_3;
  wire out_valid_INST_0_i_23_n_0;
  wire out_valid_INST_0_i_24_n_0;
  wire out_valid_INST_0_i_25_n_0;
  wire out_valid_INST_0_i_26_n_0;
  wire out_valid_INST_0_i_26_n_1;
  wire out_valid_INST_0_i_26_n_2;
  wire out_valid_INST_0_i_26_n_3;
  wire out_valid_INST_0_i_27_n_0;
  wire out_valid_INST_0_i_28_n_0;
  wire out_valid_INST_0_i_29_n_0;
  wire out_valid_INST_0_i_2_n_0;
  wire out_valid_INST_0_i_30_n_0;
  wire out_valid_INST_0_i_30_n_1;
  wire out_valid_INST_0_i_30_n_2;
  wire out_valid_INST_0_i_30_n_3;
  wire out_valid_INST_0_i_31_n_0;
  wire out_valid_INST_0_i_32_n_0;
  wire out_valid_INST_0_i_33_n_0;
  wire out_valid_INST_0_i_34_n_0;
  wire out_valid_INST_0_i_35_n_0;
  wire out_valid_INST_0_i_35_n_1;
  wire out_valid_INST_0_i_35_n_2;
  wire out_valid_INST_0_i_35_n_3;
  wire out_valid_INST_0_i_36_n_0;
  wire out_valid_INST_0_i_37_n_0;
  wire out_valid_INST_0_i_38_n_0;
  wire out_valid_INST_0_i_39_n_0;
  wire out_valid_INST_0_i_40_n_0;
  wire out_valid_INST_0_i_40_n_1;
  wire out_valid_INST_0_i_40_n_2;
  wire out_valid_INST_0_i_40_n_3;
  wire out_valid_INST_0_i_41_n_0;
  wire out_valid_INST_0_i_42_n_0;
  wire out_valid_INST_0_i_43_n_0;
  wire out_valid_INST_0_i_44_n_0;
  wire out_valid_INST_0_i_45_n_0;
  wire out_valid_INST_0_i_45_n_1;
  wire out_valid_INST_0_i_45_n_2;
  wire out_valid_INST_0_i_45_n_3;
  wire out_valid_INST_0_i_46_n_0;
  wire out_valid_INST_0_i_47_n_0;
  wire out_valid_INST_0_i_48_n_0;
  wire out_valid_INST_0_i_49_n_0;
  wire out_valid_INST_0_i_4_n_0;
  wire out_valid_INST_0_i_50_n_0;
  wire out_valid_INST_0_i_50_n_1;
  wire out_valid_INST_0_i_50_n_2;
  wire out_valid_INST_0_i_50_n_3;
  wire out_valid_INST_0_i_51_n_0;
  wire out_valid_INST_0_i_52_n_0;
  wire out_valid_INST_0_i_53_n_0;
  wire out_valid_INST_0_i_54_n_0;
  wire out_valid_INST_0_i_55_n_0;
  wire out_valid_INST_0_i_56_n_0;
  wire out_valid_INST_0_i_57_n_0;
  wire out_valid_INST_0_i_58_n_0;
  wire out_valid_INST_0_i_59_n_0;
  wire out_valid_INST_0_i_5_n_2;
  wire out_valid_INST_0_i_5_n_3;
  wire out_valid_INST_0_i_60_n_0;
  wire out_valid_INST_0_i_61_n_0;
  wire out_valid_INST_0_i_62_n_0;
  wire out_valid_INST_0_i_63_n_0;
  wire out_valid_INST_0_i_64_n_0;
  wire out_valid_INST_0_i_65_n_0;
  wire out_valid_INST_0_i_66_n_0;
  wire out_valid_INST_0_i_67_n_0;
  wire out_valid_INST_0_i_68_n_0;
  wire out_valid_INST_0_i_69_n_0;
  wire out_valid_INST_0_i_6_n_2;
  wire out_valid_INST_0_i_6_n_3;
  wire out_valid_INST_0_i_70_n_0;
  wire out_valid_INST_0_i_71_n_0;
  wire out_valid_INST_0_i_72_n_0;
  wire out_valid_INST_0_i_73_n_0;
  wire out_valid_INST_0_i_74_n_0;
  wire out_valid_INST_0_i_7_n_2;
  wire out_valid_INST_0_i_7_n_3;
  wire out_valid_INST_0_i_8_n_2;
  wire out_valid_INST_0_i_8_n_3;
  wire out_valid_INST_0_i_9_n_2;
  wire out_valid_INST_0_i_9_n_3;
  wire overrun_event_q_i_10_n_0;
  wire overrun_event_q_i_11_n_0;
  wire overrun_event_q_i_1_n_0;
  wire overrun_event_q_i_2_n_0;
  wire overrun_event_q_i_3_n_0;
  wire overrun_event_q_i_4_n_0;
  wire overrun_event_q_i_5_n_0;
  wire overrun_event_q_i_6_n_0;
  wire overrun_event_q_i_7_n_0;
  wire overrun_event_q_i_8_n_0;
  wire overrun_event_q_i_9_n_0;
  wire overrun_event_q_reg_0;
  wire overrun_event_q_reg_1;
  wire p_0_in;
  wire [31:1]p_0_in__0;
  wire \partial_age_q[0]_i_1_n_0 ;
  wire \partial_age_q[31]_i_1_n_0 ;
  wire \partial_age_q[31]_i_3_n_0 ;
  wire \partial_age_q[31]_i_4_n_0 ;
  wire \partial_age_q_reg_n_0_[0] ;
  wire \partial_age_q_reg_n_0_[10] ;
  wire \partial_age_q_reg_n_0_[11] ;
  wire \partial_age_q_reg_n_0_[12] ;
  wire \partial_age_q_reg_n_0_[13] ;
  wire \partial_age_q_reg_n_0_[14] ;
  wire \partial_age_q_reg_n_0_[15] ;
  wire \partial_age_q_reg_n_0_[16] ;
  wire \partial_age_q_reg_n_0_[17] ;
  wire \partial_age_q_reg_n_0_[18] ;
  wire \partial_age_q_reg_n_0_[19] ;
  wire \partial_age_q_reg_n_0_[1] ;
  wire \partial_age_q_reg_n_0_[20] ;
  wire \partial_age_q_reg_n_0_[21] ;
  wire \partial_age_q_reg_n_0_[22] ;
  wire \partial_age_q_reg_n_0_[23] ;
  wire \partial_age_q_reg_n_0_[24] ;
  wire \partial_age_q_reg_n_0_[25] ;
  wire \partial_age_q_reg_n_0_[26] ;
  wire \partial_age_q_reg_n_0_[27] ;
  wire \partial_age_q_reg_n_0_[28] ;
  wire \partial_age_q_reg_n_0_[29] ;
  wire \partial_age_q_reg_n_0_[2] ;
  wire \partial_age_q_reg_n_0_[30] ;
  wire \partial_age_q_reg_n_0_[31] ;
  wire \partial_age_q_reg_n_0_[3] ;
  wire \partial_age_q_reg_n_0_[4] ;
  wire \partial_age_q_reg_n_0_[5] ;
  wire \partial_age_q_reg_n_0_[6] ;
  wire \partial_age_q_reg_n_0_[7] ;
  wire \partial_age_q_reg_n_0_[8] ;
  wire \partial_age_q_reg_n_0_[9] ;
  wire \partial_start_q[0]_i_1_n_0 ;
  wire \partial_start_q[63]_i_1_n_0 ;
  wire \partial_start_q_reg[12]_i_1_n_0 ;
  wire \partial_start_q_reg[12]_i_1_n_1 ;
  wire \partial_start_q_reg[12]_i_1_n_2 ;
  wire \partial_start_q_reg[12]_i_1_n_3 ;
  wire \partial_start_q_reg[12]_i_1_n_4 ;
  wire \partial_start_q_reg[12]_i_1_n_5 ;
  wire \partial_start_q_reg[12]_i_1_n_6 ;
  wire \partial_start_q_reg[12]_i_1_n_7 ;
  wire \partial_start_q_reg[16]_i_1_n_0 ;
  wire \partial_start_q_reg[16]_i_1_n_1 ;
  wire \partial_start_q_reg[16]_i_1_n_2 ;
  wire \partial_start_q_reg[16]_i_1_n_3 ;
  wire \partial_start_q_reg[16]_i_1_n_4 ;
  wire \partial_start_q_reg[16]_i_1_n_5 ;
  wire \partial_start_q_reg[16]_i_1_n_6 ;
  wire \partial_start_q_reg[16]_i_1_n_7 ;
  wire \partial_start_q_reg[20]_i_1_n_0 ;
  wire \partial_start_q_reg[20]_i_1_n_1 ;
  wire \partial_start_q_reg[20]_i_1_n_2 ;
  wire \partial_start_q_reg[20]_i_1_n_3 ;
  wire \partial_start_q_reg[20]_i_1_n_4 ;
  wire \partial_start_q_reg[20]_i_1_n_5 ;
  wire \partial_start_q_reg[20]_i_1_n_6 ;
  wire \partial_start_q_reg[20]_i_1_n_7 ;
  wire \partial_start_q_reg[24]_i_1_n_0 ;
  wire \partial_start_q_reg[24]_i_1_n_1 ;
  wire \partial_start_q_reg[24]_i_1_n_2 ;
  wire \partial_start_q_reg[24]_i_1_n_3 ;
  wire \partial_start_q_reg[24]_i_1_n_4 ;
  wire \partial_start_q_reg[24]_i_1_n_5 ;
  wire \partial_start_q_reg[24]_i_1_n_6 ;
  wire \partial_start_q_reg[24]_i_1_n_7 ;
  wire \partial_start_q_reg[28]_i_1_n_0 ;
  wire \partial_start_q_reg[28]_i_1_n_1 ;
  wire \partial_start_q_reg[28]_i_1_n_2 ;
  wire \partial_start_q_reg[28]_i_1_n_3 ;
  wire \partial_start_q_reg[28]_i_1_n_4 ;
  wire \partial_start_q_reg[28]_i_1_n_5 ;
  wire \partial_start_q_reg[28]_i_1_n_6 ;
  wire \partial_start_q_reg[28]_i_1_n_7 ;
  wire \partial_start_q_reg[32]_i_1_n_0 ;
  wire \partial_start_q_reg[32]_i_1_n_1 ;
  wire \partial_start_q_reg[32]_i_1_n_2 ;
  wire \partial_start_q_reg[32]_i_1_n_3 ;
  wire \partial_start_q_reg[32]_i_1_n_4 ;
  wire \partial_start_q_reg[32]_i_1_n_5 ;
  wire \partial_start_q_reg[32]_i_1_n_6 ;
  wire \partial_start_q_reg[32]_i_1_n_7 ;
  wire \partial_start_q_reg[36]_i_1_n_0 ;
  wire \partial_start_q_reg[36]_i_1_n_1 ;
  wire \partial_start_q_reg[36]_i_1_n_2 ;
  wire \partial_start_q_reg[36]_i_1_n_3 ;
  wire \partial_start_q_reg[36]_i_1_n_4 ;
  wire \partial_start_q_reg[36]_i_1_n_5 ;
  wire \partial_start_q_reg[36]_i_1_n_6 ;
  wire \partial_start_q_reg[36]_i_1_n_7 ;
  wire \partial_start_q_reg[40]_i_1_n_0 ;
  wire \partial_start_q_reg[40]_i_1_n_1 ;
  wire \partial_start_q_reg[40]_i_1_n_2 ;
  wire \partial_start_q_reg[40]_i_1_n_3 ;
  wire \partial_start_q_reg[40]_i_1_n_4 ;
  wire \partial_start_q_reg[40]_i_1_n_5 ;
  wire \partial_start_q_reg[40]_i_1_n_6 ;
  wire \partial_start_q_reg[40]_i_1_n_7 ;
  wire \partial_start_q_reg[44]_i_1_n_0 ;
  wire \partial_start_q_reg[44]_i_1_n_1 ;
  wire \partial_start_q_reg[44]_i_1_n_2 ;
  wire \partial_start_q_reg[44]_i_1_n_3 ;
  wire \partial_start_q_reg[44]_i_1_n_4 ;
  wire \partial_start_q_reg[44]_i_1_n_5 ;
  wire \partial_start_q_reg[44]_i_1_n_6 ;
  wire \partial_start_q_reg[44]_i_1_n_7 ;
  wire \partial_start_q_reg[48]_i_1_n_0 ;
  wire \partial_start_q_reg[48]_i_1_n_1 ;
  wire \partial_start_q_reg[48]_i_1_n_2 ;
  wire \partial_start_q_reg[48]_i_1_n_3 ;
  wire \partial_start_q_reg[48]_i_1_n_4 ;
  wire \partial_start_q_reg[48]_i_1_n_5 ;
  wire \partial_start_q_reg[48]_i_1_n_6 ;
  wire \partial_start_q_reg[48]_i_1_n_7 ;
  wire \partial_start_q_reg[4]_i_1_n_0 ;
  wire \partial_start_q_reg[4]_i_1_n_1 ;
  wire \partial_start_q_reg[4]_i_1_n_2 ;
  wire \partial_start_q_reg[4]_i_1_n_3 ;
  wire \partial_start_q_reg[4]_i_1_n_4 ;
  wire \partial_start_q_reg[4]_i_1_n_5 ;
  wire \partial_start_q_reg[4]_i_1_n_6 ;
  wire \partial_start_q_reg[4]_i_1_n_7 ;
  wire \partial_start_q_reg[52]_i_1_n_0 ;
  wire \partial_start_q_reg[52]_i_1_n_1 ;
  wire \partial_start_q_reg[52]_i_1_n_2 ;
  wire \partial_start_q_reg[52]_i_1_n_3 ;
  wire \partial_start_q_reg[52]_i_1_n_4 ;
  wire \partial_start_q_reg[52]_i_1_n_5 ;
  wire \partial_start_q_reg[52]_i_1_n_6 ;
  wire \partial_start_q_reg[52]_i_1_n_7 ;
  wire \partial_start_q_reg[56]_i_1_n_0 ;
  wire \partial_start_q_reg[56]_i_1_n_1 ;
  wire \partial_start_q_reg[56]_i_1_n_2 ;
  wire \partial_start_q_reg[56]_i_1_n_3 ;
  wire \partial_start_q_reg[56]_i_1_n_4 ;
  wire \partial_start_q_reg[56]_i_1_n_5 ;
  wire \partial_start_q_reg[56]_i_1_n_6 ;
  wire \partial_start_q_reg[56]_i_1_n_7 ;
  wire \partial_start_q_reg[60]_i_1_n_0 ;
  wire \partial_start_q_reg[60]_i_1_n_1 ;
  wire \partial_start_q_reg[60]_i_1_n_2 ;
  wire \partial_start_q_reg[60]_i_1_n_3 ;
  wire \partial_start_q_reg[60]_i_1_n_4 ;
  wire \partial_start_q_reg[60]_i_1_n_5 ;
  wire \partial_start_q_reg[60]_i_1_n_6 ;
  wire \partial_start_q_reg[60]_i_1_n_7 ;
  wire \partial_start_q_reg[63]_i_2_n_2 ;
  wire \partial_start_q_reg[63]_i_2_n_3 ;
  wire \partial_start_q_reg[63]_i_2_n_5 ;
  wire \partial_start_q_reg[63]_i_2_n_6 ;
  wire \partial_start_q_reg[63]_i_2_n_7 ;
  wire \partial_start_q_reg[8]_i_1_n_0 ;
  wire \partial_start_q_reg[8]_i_1_n_1 ;
  wire \partial_start_q_reg[8]_i_1_n_2 ;
  wire \partial_start_q_reg[8]_i_1_n_3 ;
  wire \partial_start_q_reg[8]_i_1_n_4 ;
  wire \partial_start_q_reg[8]_i_1_n_5 ;
  wire \partial_start_q_reg[8]_i_1_n_6 ;
  wire \partial_start_q_reg[8]_i_1_n_7 ;
  wire \partial_start_q_reg_n_0_[0] ;
  wire \partial_start_q_reg_n_0_[10] ;
  wire \partial_start_q_reg_n_0_[11] ;
  wire \partial_start_q_reg_n_0_[12] ;
  wire \partial_start_q_reg_n_0_[13] ;
  wire \partial_start_q_reg_n_0_[14] ;
  wire \partial_start_q_reg_n_0_[15] ;
  wire \partial_start_q_reg_n_0_[16] ;
  wire \partial_start_q_reg_n_0_[17] ;
  wire \partial_start_q_reg_n_0_[18] ;
  wire \partial_start_q_reg_n_0_[19] ;
  wire \partial_start_q_reg_n_0_[1] ;
  wire \partial_start_q_reg_n_0_[20] ;
  wire \partial_start_q_reg_n_0_[21] ;
  wire \partial_start_q_reg_n_0_[22] ;
  wire \partial_start_q_reg_n_0_[23] ;
  wire \partial_start_q_reg_n_0_[24] ;
  wire \partial_start_q_reg_n_0_[25] ;
  wire \partial_start_q_reg_n_0_[26] ;
  wire \partial_start_q_reg_n_0_[27] ;
  wire \partial_start_q_reg_n_0_[28] ;
  wire \partial_start_q_reg_n_0_[29] ;
  wire \partial_start_q_reg_n_0_[2] ;
  wire \partial_start_q_reg_n_0_[30] ;
  wire \partial_start_q_reg_n_0_[31] ;
  wire \partial_start_q_reg_n_0_[32] ;
  wire \partial_start_q_reg_n_0_[33] ;
  wire \partial_start_q_reg_n_0_[34] ;
  wire \partial_start_q_reg_n_0_[35] ;
  wire \partial_start_q_reg_n_0_[36] ;
  wire \partial_start_q_reg_n_0_[37] ;
  wire \partial_start_q_reg_n_0_[38] ;
  wire \partial_start_q_reg_n_0_[39] ;
  wire \partial_start_q_reg_n_0_[3] ;
  wire \partial_start_q_reg_n_0_[40] ;
  wire \partial_start_q_reg_n_0_[41] ;
  wire \partial_start_q_reg_n_0_[42] ;
  wire \partial_start_q_reg_n_0_[43] ;
  wire \partial_start_q_reg_n_0_[44] ;
  wire \partial_start_q_reg_n_0_[45] ;
  wire \partial_start_q_reg_n_0_[46] ;
  wire \partial_start_q_reg_n_0_[47] ;
  wire \partial_start_q_reg_n_0_[48] ;
  wire \partial_start_q_reg_n_0_[49] ;
  wire \partial_start_q_reg_n_0_[4] ;
  wire \partial_start_q_reg_n_0_[50] ;
  wire \partial_start_q_reg_n_0_[51] ;
  wire \partial_start_q_reg_n_0_[52] ;
  wire \partial_start_q_reg_n_0_[53] ;
  wire \partial_start_q_reg_n_0_[54] ;
  wire \partial_start_q_reg_n_0_[55] ;
  wire \partial_start_q_reg_n_0_[56] ;
  wire \partial_start_q_reg_n_0_[57] ;
  wire \partial_start_q_reg_n_0_[58] ;
  wire \partial_start_q_reg_n_0_[59] ;
  wire \partial_start_q_reg_n_0_[5] ;
  wire \partial_start_q_reg_n_0_[60] ;
  wire \partial_start_q_reg_n_0_[61] ;
  wire \partial_start_q_reg_n_0_[62] ;
  wire \partial_start_q_reg_n_0_[63] ;
  wire \partial_start_q_reg_n_0_[6] ;
  wire \partial_start_q_reg_n_0_[7] ;
  wire \partial_start_q_reg_n_0_[8] ;
  wire \partial_start_q_reg_n_0_[9] ;
  wire partial_valid_q_i_1_n_0;
  wire partial_valid_q_reg_n_0;
  wire period_overflow_event_q_i_10_n_0;
  wire period_overflow_event_q_i_1_n_0;
  wire period_overflow_event_q_i_2_n_0;
  wire period_overflow_event_q_i_3_n_0;
  wire period_overflow_event_q_i_4_n_0;
  wire period_overflow_event_q_i_5_n_0;
  wire period_overflow_event_q_i_6_n_0;
  wire period_overflow_event_q_i_7_n_0;
  wire period_overflow_event_q_i_8_n_0;
  wire period_overflow_event_q_i_9_n_0;
  wire period_overflow_event_q_reg_0;
  wire period_overflow_event_q_reg_1;
  wire \previous_q[0]_i_1_n_0 ;
  wire \previous_q[1]_i_1_n_0 ;
  wire \previous_q[2]_i_1_n_0 ;
  wire \previous_q_reg_n_0_[0] ;
  wire \previous_q_reg_n_0_[1] ;
  wire \previous_q_reg_n_0_[2] ;
  wire raw_equal0;
  wire raw_equal1;
  wire raw_equal2;
  wire raw_equal3;
  wire raw_equal30_out;
  wire [2:0]sample_levels;
  wire \slot_end_q[0]_i_1_n_0 ;
  wire \slot_end_q[10]_i_1_n_0 ;
  wire \slot_end_q[11]_i_1_n_0 ;
  wire \slot_end_q[12]_i_1_n_0 ;
  wire \slot_end_q[13]_i_1_n_0 ;
  wire \slot_end_q[14]_i_1_n_0 ;
  wire \slot_end_q[15]_i_1_n_0 ;
  wire \slot_end_q[16]_i_1_n_0 ;
  wire \slot_end_q[17]_i_1_n_0 ;
  wire \slot_end_q[18]_i_1_n_0 ;
  wire \slot_end_q[19]_i_1_n_0 ;
  wire \slot_end_q[1]_i_1_n_0 ;
  wire \slot_end_q[20]_i_1_n_0 ;
  wire \slot_end_q[21]_i_1_n_0 ;
  wire \slot_end_q[22]_i_1_n_0 ;
  wire \slot_end_q[23]_i_1_n_0 ;
  wire \slot_end_q[24]_i_1_n_0 ;
  wire \slot_end_q[25]_i_1_n_0 ;
  wire \slot_end_q[26]_i_1_n_0 ;
  wire \slot_end_q[27]_i_1_n_0 ;
  wire \slot_end_q[28]_i_1_n_0 ;
  wire \slot_end_q[29]_i_1_n_0 ;
  wire \slot_end_q[2]_i_1_n_0 ;
  wire \slot_end_q[30]_i_1_n_0 ;
  wire \slot_end_q[31]_i_1_n_0 ;
  wire \slot_end_q[32]_i_1_n_0 ;
  wire \slot_end_q[33]_i_1_n_0 ;
  wire \slot_end_q[34]_i_1_n_0 ;
  wire \slot_end_q[35]_i_1_n_0 ;
  wire \slot_end_q[36]_i_1_n_0 ;
  wire \slot_end_q[37]_i_1_n_0 ;
  wire \slot_end_q[38]_i_1_n_0 ;
  wire \slot_end_q[39]_i_1_n_0 ;
  wire \slot_end_q[3]_i_1_n_0 ;
  wire \slot_end_q[40]_i_1_n_0 ;
  wire \slot_end_q[41]_i_1_n_0 ;
  wire \slot_end_q[42]_i_1_n_0 ;
  wire \slot_end_q[43]_i_1_n_0 ;
  wire \slot_end_q[44]_i_1_n_0 ;
  wire \slot_end_q[45]_i_1_n_0 ;
  wire \slot_end_q[46]_i_1_n_0 ;
  wire \slot_end_q[47]_i_1_n_0 ;
  wire \slot_end_q[48]_i_1_n_0 ;
  wire \slot_end_q[49]_i_1_n_0 ;
  wire \slot_end_q[4]_i_1_n_0 ;
  wire \slot_end_q[50]_i_1_n_0 ;
  wire \slot_end_q[51]_i_1_n_0 ;
  wire \slot_end_q[52]_i_1_n_0 ;
  wire \slot_end_q[53]_i_1_n_0 ;
  wire \slot_end_q[54]_i_1_n_0 ;
  wire \slot_end_q[55]_i_1_n_0 ;
  wire \slot_end_q[56]_i_1_n_0 ;
  wire \slot_end_q[57]_i_1_n_0 ;
  wire \slot_end_q[58]_i_1_n_0 ;
  wire \slot_end_q[59]_i_1_n_0 ;
  wire \slot_end_q[5]_i_1_n_0 ;
  wire \slot_end_q[60]_i_1_n_0 ;
  wire \slot_end_q[61]_i_1_n_0 ;
  wire \slot_end_q[62]_i_1_n_0 ;
  wire \slot_end_q[63]_i_1_n_0 ;
  wire \slot_end_q[6]_i_1_n_0 ;
  wire \slot_end_q[7]_i_1_n_0 ;
  wire \slot_end_q[8]_i_1_n_0 ;
  wire \slot_end_q[9]_i_1_n_0 ;
  wire \slot_high0_q[0]_i_1_n_0 ;
  wire \slot_high0_q[10]_i_1_n_0 ;
  wire \slot_high0_q[11]_i_1_n_0 ;
  wire \slot_high0_q[12]_i_1_n_0 ;
  wire \slot_high0_q[13]_i_1_n_0 ;
  wire \slot_high0_q[14]_i_1_n_0 ;
  wire \slot_high0_q[15]_i_1_n_0 ;
  wire \slot_high0_q[16]_i_1_n_0 ;
  wire \slot_high0_q[17]_i_1_n_0 ;
  wire \slot_high0_q[18]_i_1_n_0 ;
  wire \slot_high0_q[19]_i_1_n_0 ;
  wire \slot_high0_q[1]_i_1_n_0 ;
  wire \slot_high0_q[20]_i_1_n_0 ;
  wire \slot_high0_q[21]_i_1_n_0 ;
  wire \slot_high0_q[22]_i_1_n_0 ;
  wire \slot_high0_q[23]_i_1_n_0 ;
  wire \slot_high0_q[24]_i_1_n_0 ;
  wire \slot_high0_q[25]_i_1_n_0 ;
  wire \slot_high0_q[26]_i_1_n_0 ;
  wire \slot_high0_q[27]_i_1_n_0 ;
  wire \slot_high0_q[28]_i_1_n_0 ;
  wire \slot_high0_q[29]_i_1_n_0 ;
  wire \slot_high0_q[2]_i_1_n_0 ;
  wire \slot_high0_q[30]_i_1_n_0 ;
  wire \slot_high0_q[31]_i_1_n_0 ;
  wire \slot_high0_q[3]_i_1_n_0 ;
  wire \slot_high0_q[4]_i_1_n_0 ;
  wire \slot_high0_q[5]_i_1_n_0 ;
  wire \slot_high0_q[6]_i_1_n_0 ;
  wire \slot_high0_q[7]_i_1_n_0 ;
  wire \slot_high0_q[8]_i_1_n_0 ;
  wire \slot_high0_q[9]_i_1_n_0 ;
  wire \slot_high1_q[0]_i_1_n_0 ;
  wire \slot_high1_q[10]_i_1_n_0 ;
  wire \slot_high1_q[11]_i_1_n_0 ;
  wire \slot_high1_q[12]_i_1_n_0 ;
  wire \slot_high1_q[13]_i_1_n_0 ;
  wire \slot_high1_q[14]_i_1_n_0 ;
  wire \slot_high1_q[15]_i_1_n_0 ;
  wire \slot_high1_q[16]_i_1_n_0 ;
  wire \slot_high1_q[17]_i_1_n_0 ;
  wire \slot_high1_q[18]_i_1_n_0 ;
  wire \slot_high1_q[19]_i_1_n_0 ;
  wire \slot_high1_q[1]_i_1_n_0 ;
  wire \slot_high1_q[20]_i_1_n_0 ;
  wire \slot_high1_q[21]_i_1_n_0 ;
  wire \slot_high1_q[22]_i_1_n_0 ;
  wire \slot_high1_q[23]_i_1_n_0 ;
  wire \slot_high1_q[24]_i_1_n_0 ;
  wire \slot_high1_q[25]_i_1_n_0 ;
  wire \slot_high1_q[26]_i_1_n_0 ;
  wire \slot_high1_q[27]_i_1_n_0 ;
  wire \slot_high1_q[28]_i_1_n_0 ;
  wire \slot_high1_q[29]_i_1_n_0 ;
  wire \slot_high1_q[2]_i_1_n_0 ;
  wire \slot_high1_q[30]_i_1_n_0 ;
  wire \slot_high1_q[31]_i_1_n_0 ;
  wire \slot_high1_q[3]_i_1_n_0 ;
  wire \slot_high1_q[4]_i_1_n_0 ;
  wire \slot_high1_q[5]_i_1_n_0 ;
  wire \slot_high1_q[6]_i_1_n_0 ;
  wire \slot_high1_q[7]_i_1_n_0 ;
  wire \slot_high1_q[8]_i_1_n_0 ;
  wire \slot_high1_q[9]_i_1_n_0 ;
  wire \slot_high2_q[0]_i_1_n_0 ;
  wire \slot_high2_q[10]_i_1_n_0 ;
  wire \slot_high2_q[11]_i_1_n_0 ;
  wire \slot_high2_q[12]_i_1_n_0 ;
  wire \slot_high2_q[13]_i_1_n_0 ;
  wire \slot_high2_q[14]_i_1_n_0 ;
  wire \slot_high2_q[15]_i_1_n_0 ;
  wire \slot_high2_q[16]_i_1_n_0 ;
  wire \slot_high2_q[17]_i_1_n_0 ;
  wire \slot_high2_q[18]_i_1_n_0 ;
  wire \slot_high2_q[19]_i_1_n_0 ;
  wire \slot_high2_q[1]_i_1_n_0 ;
  wire \slot_high2_q[20]_i_1_n_0 ;
  wire \slot_high2_q[21]_i_1_n_0 ;
  wire \slot_high2_q[22]_i_1_n_0 ;
  wire \slot_high2_q[23]_i_1_n_0 ;
  wire \slot_high2_q[24]_i_1_n_0 ;
  wire \slot_high2_q[25]_i_1_n_0 ;
  wire \slot_high2_q[26]_i_1_n_0 ;
  wire \slot_high2_q[27]_i_1_n_0 ;
  wire \slot_high2_q[28]_i_1_n_0 ;
  wire \slot_high2_q[29]_i_1_n_0 ;
  wire \slot_high2_q[2]_i_1_n_0 ;
  wire \slot_high2_q[30]_i_1_n_0 ;
  wire \slot_high2_q[31]_i_1_n_0 ;
  wire \slot_high2_q[3]_i_1_n_0 ;
  wire \slot_high2_q[4]_i_1_n_0 ;
  wire \slot_high2_q[5]_i_1_n_0 ;
  wire \slot_high2_q[6]_i_1_n_0 ;
  wire \slot_high2_q[7]_i_1_n_0 ;
  wire \slot_high2_q[8]_i_1_n_0 ;
  wire \slot_high2_q[9]_i_1_n_0 ;
  wire \slot_period_q[0]_i_1_n_0 ;
  wire \slot_period_q[10]_i_1_n_0 ;
  wire \slot_period_q[11]_i_1_n_0 ;
  wire \slot_period_q[12]_i_1_n_0 ;
  wire \slot_period_q[13]_i_1_n_0 ;
  wire \slot_period_q[14]_i_1_n_0 ;
  wire \slot_period_q[15]_i_1_n_0 ;
  wire \slot_period_q[16]_i_1_n_0 ;
  wire \slot_period_q[17]_i_1_n_0 ;
  wire \slot_period_q[18]_i_1_n_0 ;
  wire \slot_period_q[19]_i_1_n_0 ;
  wire \slot_period_q[1]_i_1_n_0 ;
  wire \slot_period_q[20]_i_1_n_0 ;
  wire \slot_period_q[21]_i_1_n_0 ;
  wire \slot_period_q[22]_i_1_n_0 ;
  wire \slot_period_q[23]_i_1_n_0 ;
  wire \slot_period_q[24]_i_1_n_0 ;
  wire \slot_period_q[25]_i_1_n_0 ;
  wire \slot_period_q[26]_i_1_n_0 ;
  wire \slot_period_q[27]_i_1_n_0 ;
  wire \slot_period_q[28]_i_1_n_0 ;
  wire \slot_period_q[29]_i_1_n_0 ;
  wire \slot_period_q[2]_i_1_n_0 ;
  wire \slot_period_q[30]_i_1_n_0 ;
  wire \slot_period_q[31]_i_100_n_0 ;
  wire \slot_period_q[31]_i_101_n_0 ;
  wire \slot_period_q[31]_i_102_n_0 ;
  wire \slot_period_q[31]_i_103_n_0 ;
  wire \slot_period_q[31]_i_105_n_0 ;
  wire \slot_period_q[31]_i_106_n_0 ;
  wire \slot_period_q[31]_i_107_n_0 ;
  wire \slot_period_q[31]_i_108_n_0 ;
  wire \slot_period_q[31]_i_109_n_0 ;
  wire \slot_period_q[31]_i_10_n_0 ;
  wire \slot_period_q[31]_i_110_n_0 ;
  wire \slot_period_q[31]_i_111_n_0 ;
  wire \slot_period_q[31]_i_112_n_0 ;
  wire \slot_period_q[31]_i_114_n_0 ;
  wire \slot_period_q[31]_i_115_n_0 ;
  wire \slot_period_q[31]_i_116_n_0 ;
  wire \slot_period_q[31]_i_117_n_0 ;
  wire \slot_period_q[31]_i_118_n_0 ;
  wire \slot_period_q[31]_i_119_n_0 ;
  wire \slot_period_q[31]_i_120_n_0 ;
  wire \slot_period_q[31]_i_121_n_0 ;
  wire \slot_period_q[31]_i_123_n_0 ;
  wire \slot_period_q[31]_i_124_n_0 ;
  wire \slot_period_q[31]_i_125_n_0 ;
  wire \slot_period_q[31]_i_126_n_0 ;
  wire \slot_period_q[31]_i_127_n_0 ;
  wire \slot_period_q[31]_i_128_n_0 ;
  wire \slot_period_q[31]_i_129_n_0 ;
  wire \slot_period_q[31]_i_12_n_0 ;
  wire \slot_period_q[31]_i_130_n_0 ;
  wire \slot_period_q[31]_i_131_n_0 ;
  wire \slot_period_q[31]_i_132_n_0 ;
  wire \slot_period_q[31]_i_133_n_0 ;
  wire \slot_period_q[31]_i_134_n_0 ;
  wire \slot_period_q[31]_i_135_n_0 ;
  wire \slot_period_q[31]_i_136_n_0 ;
  wire \slot_period_q[31]_i_137_n_0 ;
  wire \slot_period_q[31]_i_138_n_0 ;
  wire \slot_period_q[31]_i_139_n_0 ;
  wire \slot_period_q[31]_i_13_n_0 ;
  wire \slot_period_q[31]_i_140_n_0 ;
  wire \slot_period_q[31]_i_141_n_0 ;
  wire \slot_period_q[31]_i_142_n_0 ;
  wire \slot_period_q[31]_i_143_n_0 ;
  wire \slot_period_q[31]_i_144_n_0 ;
  wire \slot_period_q[31]_i_145_n_0 ;
  wire \slot_period_q[31]_i_146_n_0 ;
  wire \slot_period_q[31]_i_147_n_0 ;
  wire \slot_period_q[31]_i_148_n_0 ;
  wire \slot_period_q[31]_i_149_n_0 ;
  wire \slot_period_q[31]_i_14_n_0 ;
  wire \slot_period_q[31]_i_150_n_0 ;
  wire \slot_period_q[31]_i_151_n_0 ;
  wire \slot_period_q[31]_i_152_n_0 ;
  wire \slot_period_q[31]_i_153_n_0 ;
  wire \slot_period_q[31]_i_154_n_0 ;
  wire \slot_period_q[31]_i_15_n_0 ;
  wire \slot_period_q[31]_i_16_n_0 ;
  wire \slot_period_q[31]_i_17_n_0 ;
  wire \slot_period_q[31]_i_18_n_0 ;
  wire \slot_period_q[31]_i_19_n_0 ;
  wire \slot_period_q[31]_i_1_n_0 ;
  wire \slot_period_q[31]_i_20_n_0 ;
  wire \slot_period_q[31]_i_21_n_0 ;
  wire \slot_period_q[31]_i_22_n_0 ;
  wire \slot_period_q[31]_i_23_n_0 ;
  wire \slot_period_q[31]_i_24_n_0 ;
  wire \slot_period_q[31]_i_25_n_0 ;
  wire \slot_period_q[31]_i_26_n_0 ;
  wire \slot_period_q[31]_i_2_n_0 ;
  wire \slot_period_q[31]_i_30_n_0 ;
  wire \slot_period_q[31]_i_31_n_0 ;
  wire \slot_period_q[31]_i_32_n_0 ;
  wire \slot_period_q[31]_i_33_n_0 ;
  wire \slot_period_q[31]_i_34_n_0 ;
  wire \slot_period_q[31]_i_35_n_0 ;
  wire \slot_period_q[31]_i_36_n_0 ;
  wire \slot_period_q[31]_i_37_n_0 ;
  wire \slot_period_q[31]_i_38_n_0 ;
  wire \slot_period_q[31]_i_39_n_0 ;
  wire \slot_period_q[31]_i_40_n_0 ;
  wire \slot_period_q[31]_i_41_n_0 ;
  wire \slot_period_q[31]_i_43_n_0 ;
  wire \slot_period_q[31]_i_44_n_0 ;
  wire \slot_period_q[31]_i_45_n_0 ;
  wire \slot_period_q[31]_i_46_n_0 ;
  wire \slot_period_q[31]_i_47_n_0 ;
  wire \slot_period_q[31]_i_48_n_0 ;
  wire \slot_period_q[31]_i_49_n_0 ;
  wire \slot_period_q[31]_i_4_n_0 ;
  wire \slot_period_q[31]_i_50_n_0 ;
  wire \slot_period_q[31]_i_52_n_0 ;
  wire \slot_period_q[31]_i_53_n_0 ;
  wire \slot_period_q[31]_i_54_n_0 ;
  wire \slot_period_q[31]_i_55_n_0 ;
  wire \slot_period_q[31]_i_56_n_0 ;
  wire \slot_period_q[31]_i_57_n_0 ;
  wire \slot_period_q[31]_i_58_n_0 ;
  wire \slot_period_q[31]_i_59_n_0 ;
  wire \slot_period_q[31]_i_5_n_0 ;
  wire \slot_period_q[31]_i_61_n_0 ;
  wire \slot_period_q[31]_i_62_n_0 ;
  wire \slot_period_q[31]_i_63_n_0 ;
  wire \slot_period_q[31]_i_64_n_0 ;
  wire \slot_period_q[31]_i_65_n_0 ;
  wire \slot_period_q[31]_i_66_n_0 ;
  wire \slot_period_q[31]_i_67_n_0 ;
  wire \slot_period_q[31]_i_68_n_0 ;
  wire \slot_period_q[31]_i_69_n_0 ;
  wire \slot_period_q[31]_i_6_n_0 ;
  wire \slot_period_q[31]_i_70_n_0 ;
  wire \slot_period_q[31]_i_71_n_0 ;
  wire \slot_period_q[31]_i_72_n_0 ;
  wire \slot_period_q[31]_i_73_n_0 ;
  wire \slot_period_q[31]_i_74_n_0 ;
  wire \slot_period_q[31]_i_75_n_0 ;
  wire \slot_period_q[31]_i_76_n_0 ;
  wire \slot_period_q[31]_i_78_n_0 ;
  wire \slot_period_q[31]_i_79_n_0 ;
  wire \slot_period_q[31]_i_7_n_0 ;
  wire \slot_period_q[31]_i_80_n_0 ;
  wire \slot_period_q[31]_i_81_n_0 ;
  wire \slot_period_q[31]_i_82_n_0 ;
  wire \slot_period_q[31]_i_83_n_0 ;
  wire \slot_period_q[31]_i_84_n_0 ;
  wire \slot_period_q[31]_i_85_n_0 ;
  wire \slot_period_q[31]_i_87_n_0 ;
  wire \slot_period_q[31]_i_88_n_0 ;
  wire \slot_period_q[31]_i_89_n_0 ;
  wire \slot_period_q[31]_i_8_n_0 ;
  wire \slot_period_q[31]_i_90_n_0 ;
  wire \slot_period_q[31]_i_91_n_0 ;
  wire \slot_period_q[31]_i_92_n_0 ;
  wire \slot_period_q[31]_i_93_n_0 ;
  wire \slot_period_q[31]_i_94_n_0 ;
  wire \slot_period_q[31]_i_96_n_0 ;
  wire \slot_period_q[31]_i_97_n_0 ;
  wire \slot_period_q[31]_i_98_n_0 ;
  wire \slot_period_q[31]_i_99_n_0 ;
  wire \slot_period_q[31]_i_9_n_0 ;
  wire \slot_period_q[3]_i_1_n_0 ;
  wire \slot_period_q[4]_i_1_n_0 ;
  wire \slot_period_q[5]_i_1_n_0 ;
  wire \slot_period_q[6]_i_1_n_0 ;
  wire \slot_period_q[7]_i_1_n_0 ;
  wire \slot_period_q[8]_i_1_n_0 ;
  wire \slot_period_q[9]_i_1_n_0 ;
  wire \slot_period_q_reg[12]_i_2_n_0 ;
  wire \slot_period_q_reg[12]_i_2_n_1 ;
  wire \slot_period_q_reg[12]_i_2_n_2 ;
  wire \slot_period_q_reg[12]_i_2_n_3 ;
  wire \slot_period_q_reg[12]_i_2_n_4 ;
  wire \slot_period_q_reg[12]_i_2_n_5 ;
  wire \slot_period_q_reg[12]_i_2_n_6 ;
  wire \slot_period_q_reg[12]_i_2_n_7 ;
  wire \slot_period_q_reg[16]_i_2_n_0 ;
  wire \slot_period_q_reg[16]_i_2_n_1 ;
  wire \slot_period_q_reg[16]_i_2_n_2 ;
  wire \slot_period_q_reg[16]_i_2_n_3 ;
  wire \slot_period_q_reg[16]_i_2_n_4 ;
  wire \slot_period_q_reg[16]_i_2_n_5 ;
  wire \slot_period_q_reg[16]_i_2_n_6 ;
  wire \slot_period_q_reg[16]_i_2_n_7 ;
  wire \slot_period_q_reg[20]_i_2_n_0 ;
  wire \slot_period_q_reg[20]_i_2_n_1 ;
  wire \slot_period_q_reg[20]_i_2_n_2 ;
  wire \slot_period_q_reg[20]_i_2_n_3 ;
  wire \slot_period_q_reg[20]_i_2_n_4 ;
  wire \slot_period_q_reg[20]_i_2_n_5 ;
  wire \slot_period_q_reg[20]_i_2_n_6 ;
  wire \slot_period_q_reg[20]_i_2_n_7 ;
  wire \slot_period_q_reg[24]_i_2_n_0 ;
  wire \slot_period_q_reg[24]_i_2_n_1 ;
  wire \slot_period_q_reg[24]_i_2_n_2 ;
  wire \slot_period_q_reg[24]_i_2_n_3 ;
  wire \slot_period_q_reg[24]_i_2_n_4 ;
  wire \slot_period_q_reg[24]_i_2_n_5 ;
  wire \slot_period_q_reg[24]_i_2_n_6 ;
  wire \slot_period_q_reg[24]_i_2_n_7 ;
  wire \slot_period_q_reg[28]_i_2_n_0 ;
  wire \slot_period_q_reg[28]_i_2_n_1 ;
  wire \slot_period_q_reg[28]_i_2_n_2 ;
  wire \slot_period_q_reg[28]_i_2_n_3 ;
  wire \slot_period_q_reg[28]_i_2_n_4 ;
  wire \slot_period_q_reg[28]_i_2_n_5 ;
  wire \slot_period_q_reg[28]_i_2_n_6 ;
  wire \slot_period_q_reg[28]_i_2_n_7 ;
  wire \slot_period_q_reg[31]_i_104_n_0 ;
  wire \slot_period_q_reg[31]_i_104_n_1 ;
  wire \slot_period_q_reg[31]_i_104_n_2 ;
  wire \slot_period_q_reg[31]_i_104_n_3 ;
  wire \slot_period_q_reg[31]_i_113_n_0 ;
  wire \slot_period_q_reg[31]_i_113_n_1 ;
  wire \slot_period_q_reg[31]_i_113_n_2 ;
  wire \slot_period_q_reg[31]_i_113_n_3 ;
  wire \slot_period_q_reg[31]_i_11_n_2 ;
  wire \slot_period_q_reg[31]_i_11_n_3 ;
  wire \slot_period_q_reg[31]_i_11_n_5 ;
  wire \slot_period_q_reg[31]_i_11_n_6 ;
  wire \slot_period_q_reg[31]_i_11_n_7 ;
  wire \slot_period_q_reg[31]_i_122_n_0 ;
  wire \slot_period_q_reg[31]_i_122_n_1 ;
  wire \slot_period_q_reg[31]_i_122_n_2 ;
  wire \slot_period_q_reg[31]_i_122_n_3 ;
  wire \slot_period_q_reg[31]_i_27_n_1 ;
  wire \slot_period_q_reg[31]_i_27_n_2 ;
  wire \slot_period_q_reg[31]_i_27_n_3 ;
  wire \slot_period_q_reg[31]_i_28_n_1 ;
  wire \slot_period_q_reg[31]_i_28_n_2 ;
  wire \slot_period_q_reg[31]_i_28_n_3 ;
  wire \slot_period_q_reg[31]_i_29_n_1 ;
  wire \slot_period_q_reg[31]_i_29_n_2 ;
  wire \slot_period_q_reg[31]_i_29_n_3 ;
  wire \slot_period_q_reg[31]_i_42_n_0 ;
  wire \slot_period_q_reg[31]_i_42_n_1 ;
  wire \slot_period_q_reg[31]_i_42_n_2 ;
  wire \slot_period_q_reg[31]_i_42_n_3 ;
  wire \slot_period_q_reg[31]_i_51_n_0 ;
  wire \slot_period_q_reg[31]_i_51_n_1 ;
  wire \slot_period_q_reg[31]_i_51_n_2 ;
  wire \slot_period_q_reg[31]_i_51_n_3 ;
  wire \slot_period_q_reg[31]_i_60_n_0 ;
  wire \slot_period_q_reg[31]_i_60_n_1 ;
  wire \slot_period_q_reg[31]_i_60_n_2 ;
  wire \slot_period_q_reg[31]_i_60_n_3 ;
  wire \slot_period_q_reg[31]_i_77_n_0 ;
  wire \slot_period_q_reg[31]_i_77_n_1 ;
  wire \slot_period_q_reg[31]_i_77_n_2 ;
  wire \slot_period_q_reg[31]_i_77_n_3 ;
  wire \slot_period_q_reg[31]_i_86_n_0 ;
  wire \slot_period_q_reg[31]_i_86_n_1 ;
  wire \slot_period_q_reg[31]_i_86_n_2 ;
  wire \slot_period_q_reg[31]_i_86_n_3 ;
  wire \slot_period_q_reg[31]_i_95_n_0 ;
  wire \slot_period_q_reg[31]_i_95_n_1 ;
  wire \slot_period_q_reg[31]_i_95_n_2 ;
  wire \slot_period_q_reg[31]_i_95_n_3 ;
  wire \slot_period_q_reg[4]_i_2_n_0 ;
  wire \slot_period_q_reg[4]_i_2_n_1 ;
  wire \slot_period_q_reg[4]_i_2_n_2 ;
  wire \slot_period_q_reg[4]_i_2_n_3 ;
  wire \slot_period_q_reg[4]_i_2_n_4 ;
  wire \slot_period_q_reg[4]_i_2_n_5 ;
  wire \slot_period_q_reg[4]_i_2_n_6 ;
  wire \slot_period_q_reg[4]_i_2_n_7 ;
  wire \slot_period_q_reg[8]_i_2_n_0 ;
  wire \slot_period_q_reg[8]_i_2_n_1 ;
  wire \slot_period_q_reg[8]_i_2_n_2 ;
  wire \slot_period_q_reg[8]_i_2_n_3 ;
  wire \slot_period_q_reg[8]_i_2_n_4 ;
  wire \slot_period_q_reg[8]_i_2_n_5 ;
  wire \slot_period_q_reg[8]_i_2_n_6 ;
  wire \slot_period_q_reg[8]_i_2_n_7 ;
  wire \slot_start_q[0]_i_1_n_0 ;
  wire \slot_start_q[10]_i_1_n_0 ;
  wire \slot_start_q[11]_i_1_n_0 ;
  wire \slot_start_q[12]_i_1_n_0 ;
  wire \slot_start_q[13]_i_1_n_0 ;
  wire \slot_start_q[14]_i_1_n_0 ;
  wire \slot_start_q[15]_i_1_n_0 ;
  wire \slot_start_q[16]_i_1_n_0 ;
  wire \slot_start_q[17]_i_1_n_0 ;
  wire \slot_start_q[18]_i_1_n_0 ;
  wire \slot_start_q[19]_i_1_n_0 ;
  wire \slot_start_q[1]_i_1_n_0 ;
  wire \slot_start_q[20]_i_1_n_0 ;
  wire \slot_start_q[21]_i_1_n_0 ;
  wire \slot_start_q[22]_i_1_n_0 ;
  wire \slot_start_q[23]_i_1_n_0 ;
  wire \slot_start_q[24]_i_1_n_0 ;
  wire \slot_start_q[25]_i_1_n_0 ;
  wire \slot_start_q[26]_i_1_n_0 ;
  wire \slot_start_q[27]_i_1_n_0 ;
  wire \slot_start_q[28]_i_1_n_0 ;
  wire \slot_start_q[29]_i_1_n_0 ;
  wire \slot_start_q[2]_i_1_n_0 ;
  wire \slot_start_q[30]_i_1_n_0 ;
  wire \slot_start_q[31]_i_1_n_0 ;
  wire \slot_start_q[32]_i_1_n_0 ;
  wire \slot_start_q[33]_i_1_n_0 ;
  wire \slot_start_q[34]_i_1_n_0 ;
  wire \slot_start_q[35]_i_1_n_0 ;
  wire \slot_start_q[36]_i_1_n_0 ;
  wire \slot_start_q[37]_i_1_n_0 ;
  wire \slot_start_q[38]_i_1_n_0 ;
  wire \slot_start_q[39]_i_1_n_0 ;
  wire \slot_start_q[3]_i_1_n_0 ;
  wire \slot_start_q[40]_i_1_n_0 ;
  wire \slot_start_q[41]_i_1_n_0 ;
  wire \slot_start_q[42]_i_1_n_0 ;
  wire \slot_start_q[43]_i_1_n_0 ;
  wire \slot_start_q[44]_i_1_n_0 ;
  wire \slot_start_q[45]_i_1_n_0 ;
  wire \slot_start_q[46]_i_1_n_0 ;
  wire \slot_start_q[47]_i_1_n_0 ;
  wire \slot_start_q[48]_i_1_n_0 ;
  wire \slot_start_q[49]_i_1_n_0 ;
  wire \slot_start_q[4]_i_1_n_0 ;
  wire \slot_start_q[50]_i_1_n_0 ;
  wire \slot_start_q[51]_i_1_n_0 ;
  wire \slot_start_q[52]_i_1_n_0 ;
  wire \slot_start_q[53]_i_1_n_0 ;
  wire \slot_start_q[54]_i_1_n_0 ;
  wire \slot_start_q[55]_i_1_n_0 ;
  wire \slot_start_q[56]_i_1_n_0 ;
  wire \slot_start_q[57]_i_1_n_0 ;
  wire \slot_start_q[58]_i_1_n_0 ;
  wire \slot_start_q[59]_i_1_n_0 ;
  wire \slot_start_q[5]_i_1_n_0 ;
  wire \slot_start_q[60]_i_1_n_0 ;
  wire \slot_start_q[61]_i_1_n_0 ;
  wire \slot_start_q[62]_i_1_n_0 ;
  wire \slot_start_q[63]_i_1_n_0 ;
  wire \slot_start_q[63]_i_2_n_0 ;
  wire \slot_start_q[63]_i_3_n_0 ;
  wire \slot_start_q[6]_i_1_n_0 ;
  wire \slot_start_q[7]_i_1_n_0 ;
  wire \slot_start_q[8]_i_1_n_0 ;
  wire \slot_start_q[9]_i_1_n_0 ;
  wire \slot_tag_q[0]_i_1_n_0 ;
  wire \slot_tag_q[10]_i_1_n_0 ;
  wire \slot_tag_q[11]_i_1_n_0 ;
  wire \slot_tag_q[12]_i_1_n_0 ;
  wire \slot_tag_q[13]_i_1_n_0 ;
  wire \slot_tag_q[14]_i_1_n_0 ;
  wire \slot_tag_q[15]_i_1_n_0 ;
  wire \slot_tag_q[16]_i_1_n_0 ;
  wire \slot_tag_q[17]_i_1_n_0 ;
  wire \slot_tag_q[18]_i_1_n_0 ;
  wire \slot_tag_q[19]_i_1_n_0 ;
  wire \slot_tag_q[1]_i_1_n_0 ;
  wire \slot_tag_q[20]_i_1_n_0 ;
  wire \slot_tag_q[21]_i_1_n_0 ;
  wire \slot_tag_q[22]_i_1_n_0 ;
  wire \slot_tag_q[23]_i_1_n_0 ;
  wire \slot_tag_q[24]_i_1_n_0 ;
  wire \slot_tag_q[25]_i_1_n_0 ;
  wire \slot_tag_q[26]_i_1_n_0 ;
  wire \slot_tag_q[27]_i_1_n_0 ;
  wire \slot_tag_q[28]_i_1_n_0 ;
  wire \slot_tag_q[29]_i_1_n_0 ;
  wire \slot_tag_q[2]_i_1_n_0 ;
  wire \slot_tag_q[30]_i_1_n_0 ;
  wire \slot_tag_q[31]_i_1_n_0 ;
  wire \slot_tag_q[3]_i_1_n_0 ;
  wire \slot_tag_q[4]_i_1_n_0 ;
  wire \slot_tag_q[5]_i_1_n_0 ;
  wire \slot_tag_q[6]_i_1_n_0 ;
  wire \slot_tag_q[7]_i_1_n_0 ;
  wire \slot_tag_q[8]_i_1_n_0 ;
  wire \slot_tag_q[9]_i_1_n_0 ;
  wire slot_valid_q_i_1_n_0;
  wire slot_valid_q_reg_n_0;
  wire slot_valid_q_reg_rep_n_0;
  wire slot_valid_q_rep_i_1_n_0;
  wire \tick_q[0]_i_1_n_0 ;
  wire \tick_q[0]_i_3_n_0 ;
  wire [63:0]tick_q_reg;
  wire \tick_q_reg[0]_i_2_n_0 ;
  wire \tick_q_reg[0]_i_2_n_1 ;
  wire \tick_q_reg[0]_i_2_n_2 ;
  wire \tick_q_reg[0]_i_2_n_3 ;
  wire \tick_q_reg[0]_i_2_n_4 ;
  wire \tick_q_reg[0]_i_2_n_5 ;
  wire \tick_q_reg[0]_i_2_n_6 ;
  wire \tick_q_reg[0]_i_2_n_7 ;
  wire \tick_q_reg[12]_i_1_n_0 ;
  wire \tick_q_reg[12]_i_1_n_1 ;
  wire \tick_q_reg[12]_i_1_n_2 ;
  wire \tick_q_reg[12]_i_1_n_3 ;
  wire \tick_q_reg[12]_i_1_n_4 ;
  wire \tick_q_reg[12]_i_1_n_5 ;
  wire \tick_q_reg[12]_i_1_n_6 ;
  wire \tick_q_reg[12]_i_1_n_7 ;
  wire \tick_q_reg[16]_i_1_n_0 ;
  wire \tick_q_reg[16]_i_1_n_1 ;
  wire \tick_q_reg[16]_i_1_n_2 ;
  wire \tick_q_reg[16]_i_1_n_3 ;
  wire \tick_q_reg[16]_i_1_n_4 ;
  wire \tick_q_reg[16]_i_1_n_5 ;
  wire \tick_q_reg[16]_i_1_n_6 ;
  wire \tick_q_reg[16]_i_1_n_7 ;
  wire \tick_q_reg[20]_i_1_n_0 ;
  wire \tick_q_reg[20]_i_1_n_1 ;
  wire \tick_q_reg[20]_i_1_n_2 ;
  wire \tick_q_reg[20]_i_1_n_3 ;
  wire \tick_q_reg[20]_i_1_n_4 ;
  wire \tick_q_reg[20]_i_1_n_5 ;
  wire \tick_q_reg[20]_i_1_n_6 ;
  wire \tick_q_reg[20]_i_1_n_7 ;
  wire \tick_q_reg[24]_i_1_n_0 ;
  wire \tick_q_reg[24]_i_1_n_1 ;
  wire \tick_q_reg[24]_i_1_n_2 ;
  wire \tick_q_reg[24]_i_1_n_3 ;
  wire \tick_q_reg[24]_i_1_n_4 ;
  wire \tick_q_reg[24]_i_1_n_5 ;
  wire \tick_q_reg[24]_i_1_n_6 ;
  wire \tick_q_reg[24]_i_1_n_7 ;
  wire \tick_q_reg[28]_i_1_n_0 ;
  wire \tick_q_reg[28]_i_1_n_1 ;
  wire \tick_q_reg[28]_i_1_n_2 ;
  wire \tick_q_reg[28]_i_1_n_3 ;
  wire \tick_q_reg[28]_i_1_n_4 ;
  wire \tick_q_reg[28]_i_1_n_5 ;
  wire \tick_q_reg[28]_i_1_n_6 ;
  wire \tick_q_reg[28]_i_1_n_7 ;
  wire \tick_q_reg[32]_i_1_n_0 ;
  wire \tick_q_reg[32]_i_1_n_1 ;
  wire \tick_q_reg[32]_i_1_n_2 ;
  wire \tick_q_reg[32]_i_1_n_3 ;
  wire \tick_q_reg[32]_i_1_n_4 ;
  wire \tick_q_reg[32]_i_1_n_5 ;
  wire \tick_q_reg[32]_i_1_n_6 ;
  wire \tick_q_reg[32]_i_1_n_7 ;
  wire \tick_q_reg[36]_i_1_n_0 ;
  wire \tick_q_reg[36]_i_1_n_1 ;
  wire \tick_q_reg[36]_i_1_n_2 ;
  wire \tick_q_reg[36]_i_1_n_3 ;
  wire \tick_q_reg[36]_i_1_n_4 ;
  wire \tick_q_reg[36]_i_1_n_5 ;
  wire \tick_q_reg[36]_i_1_n_6 ;
  wire \tick_q_reg[36]_i_1_n_7 ;
  wire \tick_q_reg[40]_i_1_n_0 ;
  wire \tick_q_reg[40]_i_1_n_1 ;
  wire \tick_q_reg[40]_i_1_n_2 ;
  wire \tick_q_reg[40]_i_1_n_3 ;
  wire \tick_q_reg[40]_i_1_n_4 ;
  wire \tick_q_reg[40]_i_1_n_5 ;
  wire \tick_q_reg[40]_i_1_n_6 ;
  wire \tick_q_reg[40]_i_1_n_7 ;
  wire \tick_q_reg[44]_i_1_n_0 ;
  wire \tick_q_reg[44]_i_1_n_1 ;
  wire \tick_q_reg[44]_i_1_n_2 ;
  wire \tick_q_reg[44]_i_1_n_3 ;
  wire \tick_q_reg[44]_i_1_n_4 ;
  wire \tick_q_reg[44]_i_1_n_5 ;
  wire \tick_q_reg[44]_i_1_n_6 ;
  wire \tick_q_reg[44]_i_1_n_7 ;
  wire \tick_q_reg[48]_i_1_n_0 ;
  wire \tick_q_reg[48]_i_1_n_1 ;
  wire \tick_q_reg[48]_i_1_n_2 ;
  wire \tick_q_reg[48]_i_1_n_3 ;
  wire \tick_q_reg[48]_i_1_n_4 ;
  wire \tick_q_reg[48]_i_1_n_5 ;
  wire \tick_q_reg[48]_i_1_n_6 ;
  wire \tick_q_reg[48]_i_1_n_7 ;
  wire \tick_q_reg[4]_i_1_n_0 ;
  wire \tick_q_reg[4]_i_1_n_1 ;
  wire \tick_q_reg[4]_i_1_n_2 ;
  wire \tick_q_reg[4]_i_1_n_3 ;
  wire \tick_q_reg[4]_i_1_n_4 ;
  wire \tick_q_reg[4]_i_1_n_5 ;
  wire \tick_q_reg[4]_i_1_n_6 ;
  wire \tick_q_reg[4]_i_1_n_7 ;
  wire \tick_q_reg[52]_i_1_n_0 ;
  wire \tick_q_reg[52]_i_1_n_1 ;
  wire \tick_q_reg[52]_i_1_n_2 ;
  wire \tick_q_reg[52]_i_1_n_3 ;
  wire \tick_q_reg[52]_i_1_n_4 ;
  wire \tick_q_reg[52]_i_1_n_5 ;
  wire \tick_q_reg[52]_i_1_n_6 ;
  wire \tick_q_reg[52]_i_1_n_7 ;
  wire \tick_q_reg[56]_i_1_n_0 ;
  wire \tick_q_reg[56]_i_1_n_1 ;
  wire \tick_q_reg[56]_i_1_n_2 ;
  wire \tick_q_reg[56]_i_1_n_3 ;
  wire \tick_q_reg[56]_i_1_n_4 ;
  wire \tick_q_reg[56]_i_1_n_5 ;
  wire \tick_q_reg[56]_i_1_n_6 ;
  wire \tick_q_reg[56]_i_1_n_7 ;
  wire \tick_q_reg[60]_i_1_n_1 ;
  wire \tick_q_reg[60]_i_1_n_2 ;
  wire \tick_q_reg[60]_i_1_n_3 ;
  wire \tick_q_reg[60]_i_1_n_4 ;
  wire \tick_q_reg[60]_i_1_n_5 ;
  wire \tick_q_reg[60]_i_1_n_6 ;
  wire \tick_q_reg[60]_i_1_n_7 ;
  wire \tick_q_reg[8]_i_1_n_0 ;
  wire \tick_q_reg[8]_i_1_n_1 ;
  wire \tick_q_reg[8]_i_1_n_2 ;
  wire \tick_q_reg[8]_i_1_n_3 ;
  wire \tick_q_reg[8]_i_1_n_4 ;
  wire \tick_q_reg[8]_i_1_n_5 ;
  wire \tick_q_reg[8]_i_1_n_6 ;
  wire \tick_q_reg[8]_i_1_n_7 ;
  wire window_active_q_i_11_n_0;
  wire window_active_q_reg;
  wire [31:0]window_tag_q;
  wire [0:0]\window_tag_q_reg[0]_0 ;
  wire \window_tag_q_reg[31]_0 ;
  wire witness_overflow_event_q_i_1_n_0;
  wire witness_overflow_event_q_reg_0;
  wire [3:0]NLW_out_valid_INST_0_i_10_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_14_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_18_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_22_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_26_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_30_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_35_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_40_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_45_O_UNCONNECTED;
  wire [3:3]NLW_out_valid_INST_0_i_5_CO_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_5_O_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_50_O_UNCONNECTED;
  wire [3:3]NLW_out_valid_INST_0_i_6_CO_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_6_O_UNCONNECTED;
  wire [3:3]NLW_out_valid_INST_0_i_7_CO_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_7_O_UNCONNECTED;
  wire [3:3]NLW_out_valid_INST_0_i_8_CO_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_8_O_UNCONNECTED;
  wire [3:3]NLW_out_valid_INST_0_i_9_CO_UNCONNECTED;
  wire [3:0]NLW_out_valid_INST_0_i_9_O_UNCONNECTED;
  wire [3:2]\NLW_partial_start_q_reg[63]_i_2_CO_UNCONNECTED ;
  wire [3:3]\NLW_partial_start_q_reg[63]_i_2_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_104_O_UNCONNECTED ;
  wire [3:2]\NLW_slot_period_q_reg[31]_i_11_CO_UNCONNECTED ;
  wire [3:3]\NLW_slot_period_q_reg[31]_i_11_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_113_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_122_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_27_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_28_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_29_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_42_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_51_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_60_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_77_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_86_O_UNCONNECTED ;
  wire [3:0]\NLW_slot_period_q_reg[31]_i_95_O_UNCONNECTED ;
  wire [3:3]\NLW_tick_q_reg[60]_i_1_CO_UNCONNECTED ;

  LUT4 #(
    .INIT(16'h00F8)) 
    armed_q_i_1
       (.I0(armed_q_reg_0),
        .I1(armed_q_i_2_n_0),
        .I2(capture_rearm),
        .I3(\window_tag_q_reg[31]_0 ),
        .O(armed_q_i_1_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    armed_q_i_10
       (.I0(tick_q_reg[7]),
        .I1(tick_q_reg[56]),
        .I2(tick_q_reg[5]),
        .I3(tick_q_reg[10]),
        .I4(armed_q_i_16_n_0),
        .O(armed_q_i_10_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_11
       (.I0(tick_q_reg[50]),
        .I1(tick_q_reg[26]),
        .I2(tick_q_reg[52]),
        .I3(tick_q_reg[38]),
        .O(armed_q_i_11_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    armed_q_i_12
       (.I0(tick_q_reg[6]),
        .I1(tick_q_reg[17]),
        .I2(tick_q_reg[4]),
        .I3(tick_q_reg[8]),
        .I4(armed_q_i_17_n_0),
        .O(armed_q_i_12_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_13
       (.I0(tick_q_reg[62]),
        .I1(tick_q_reg[25]),
        .I2(tick_q_reg[51]),
        .I3(tick_q_reg[36]),
        .O(armed_q_i_13_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    armed_q_i_14
       (.I0(tick_q_reg[41]),
        .I1(tick_q_reg[55]),
        .I2(tick_q_reg[1]),
        .I3(tick_q_reg[12]),
        .I4(armed_q_i_18_n_0),
        .O(armed_q_i_14_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_15
       (.I0(tick_q_reg[47]),
        .I1(tick_q_reg[45]),
        .I2(tick_q_reg[16]),
        .I3(tick_q_reg[13]),
        .O(armed_q_i_15_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_16
       (.I0(tick_q_reg[46]),
        .I1(tick_q_reg[2]),
        .I2(tick_q_reg[54]),
        .I3(tick_q_reg[39]),
        .O(armed_q_i_16_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_17
       (.I0(tick_q_reg[43]),
        .I1(tick_q_reg[9]),
        .I2(tick_q_reg[30]),
        .I3(tick_q_reg[15]),
        .O(armed_q_i_17_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_18
       (.I0(tick_q_reg[44]),
        .I1(tick_q_reg[3]),
        .I2(tick_q_reg[40]),
        .I3(tick_q_reg[11]),
        .O(armed_q_i_18_n_0));
  LUT4 #(
    .INIT(16'hFFFE)) 
    armed_q_i_2
       (.I0(armed_q_i_3_n_0),
        .I1(armed_q_i_4_n_0),
        .I2(armed_q_i_5_n_0),
        .I3(armed_q_i_6_n_0),
        .O(armed_q_i_2_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFBFFFFFFF)) 
    armed_q_i_3
       (.I0(armed_q_i_7_n_0),
        .I1(tick_q_reg[34]),
        .I2(tick_q_reg[23]),
        .I3(tick_q_reg[61]),
        .I4(tick_q_reg[28]),
        .I5(armed_q_i_8_n_0),
        .O(armed_q_i_3_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFBFFFFFFF)) 
    armed_q_i_4
       (.I0(armed_q_i_9_n_0),
        .I1(tick_q_reg[35]),
        .I2(tick_q_reg[18]),
        .I3(tick_q_reg[33]),
        .I4(tick_q_reg[29]),
        .I5(armed_q_i_10_n_0),
        .O(armed_q_i_4_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFBFFFFFFF)) 
    armed_q_i_5
       (.I0(armed_q_i_11_n_0),
        .I1(tick_q_reg[21]),
        .I2(tick_q_reg[19]),
        .I3(tick_q_reg[48]),
        .I4(tick_q_reg[42]),
        .I5(armed_q_i_12_n_0),
        .O(armed_q_i_5_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFBFFFFFFF)) 
    armed_q_i_6
       (.I0(armed_q_i_13_n_0),
        .I1(tick_q_reg[22]),
        .I2(tick_q_reg[20]),
        .I3(tick_q_reg[63]),
        .I4(tick_q_reg[27]),
        .I5(armed_q_i_14_n_0),
        .O(armed_q_i_6_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_7
       (.I0(tick_q_reg[58]),
        .I1(tick_q_reg[24]),
        .I2(tick_q_reg[59]),
        .I3(tick_q_reg[53]),
        .O(armed_q_i_7_n_0));
  (* SOFT_HLUTNM = "soft_lutpair0" *) 
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    armed_q_i_8
       (.I0(tick_q_reg[0]),
        .I1(tick_q_reg[14]),
        .I2(tick_q_reg[31]),
        .I3(tick_q_reg[32]),
        .I4(armed_q_i_15_n_0),
        .O(armed_q_i_8_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    armed_q_i_9
       (.I0(tick_q_reg[60]),
        .I1(tick_q_reg[49]),
        .I2(tick_q_reg[57]),
        .I3(tick_q_reg[37]),
        .O(armed_q_i_9_n_0));
  FDRE armed_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(armed_q_i_1_n_0),
        .Q(armed_q_reg_0),
        .R(1'b0));
  LUT6 #(
    .INIT(64'h8088888880880000)) 
    \failure_code_q[0]_i_1 
       (.I0(\failure_code_q_reg[0] ),
        .I1(\failure_code_q[0]_i_3_n_0 ),
        .I2(period_overflow_event_q_reg_0),
        .I3(incoherent_event_q_reg_0),
        .I4(\failure_code_q[2]_i_2_n_0 ),
        .I5(failure_code[0]),
        .O(period_overflow_event_q_reg_1));
  (* SOFT_HLUTNM = "soft_lutpair6" *) 
  LUT2 #(
    .INIT(4'h7)) 
    \failure_code_q[0]_i_3 
       (.I0(\failure_code_q_reg[1]_0 ),
        .I1(witness_overflow_event_q_reg_0),
        .O(\failure_code_q[0]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'h00000000FFEA002A)) 
    \failure_code_q[1]_i_1 
       (.I0(failure_code[1]),
        .I1(\failure_code_q_reg[1]_0 ),
        .I2(witness_overflow_event_q_reg_0),
        .I3(\failure_code_q[2]_i_2_n_0 ),
        .I4(failure_code_q[1]),
        .I5(\failure_code_q_reg[1]_1 ),
        .O(\failure_code_q_reg[1] ));
  LUT6 #(
    .INIT(64'hFFFFFFFF00EE00EF)) 
    \failure_code_q[1]_i_2 
       (.I0(incoherent_event_q_reg_0),
        .I1(period_overflow_event_q_reg_0),
        .I2(armed_q_reg_0),
        .I3(witness_overflow_event_q_reg_0),
        .I4(overrun_event_q_reg_0),
        .I5(window_active_q_reg),
        .O(failure_code_q[1]));
  LUT6 #(
    .INIT(64'h00000000FFEA002A)) 
    \failure_code_q[2]_i_1 
       (.I0(failure_code[2]),
        .I1(\failure_code_q_reg[1]_0 ),
        .I2(witness_overflow_event_q_reg_0),
        .I3(\failure_code_q[2]_i_2_n_0 ),
        .I4(failure_code_q[2]),
        .I5(\failure_code_q_reg[1]_1 ),
        .O(\failure_code_q_reg[2] ));
  LUT6 #(
    .INIT(64'hEAEAEAEAEAEAEEEA)) 
    \failure_code_q[2]_i_2 
       (.I0(window_active_q_reg),
        .I1(\failure_code_q_reg[1]_0 ),
        .I2(\failure_code_q[2]_i_5_n_0 ),
        .I3(slot_valid_q_reg_rep_n_0),
        .I4(\high2_q_reg[31]_0 ),
        .I5(out_valid_INST_0_i_2_n_0),
        .O(\failure_code_q[2]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'hFFABFFAAFFABFFAB)) 
    \failure_code_q[2]_i_3 
       (.I0(window_active_q_reg),
        .I1(period_overflow_event_q_reg_0),
        .I2(incoherent_event_q_reg_0),
        .I3(witness_overflow_event_q_reg_0),
        .I4(overrun_event_q_reg_0),
        .I5(armed_q_reg_0),
        .O(failure_code_q[2]));
  (* SOFT_HLUTNM = "soft_lutpair7" *) 
  LUT4 #(
    .INIT(16'hFFEF)) 
    \failure_code_q[2]_i_5 
       (.I0(period_overflow_event_q_reg_0),
        .I1(incoherent_event_q_reg_0),
        .I2(armed_q_reg_0),
        .I3(overrun_event_q_reg_0),
        .O(\failure_code_q[2]_i_5_n_0 ));
  LUT6 #(
    .INIT(64'h00007FFF00000088)) 
    \fall_seen_q[0]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\fall_seen_q[0]_i_2_n_0 ),
        .I4(\high2_q_reg[31]_0 ),
        .I5(\fall_seen_q_reg_n_0_[0] ),
        .O(\fall_seen_q[0]_i_1_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair4" *) 
  LUT4 #(
    .INIT(16'hFFEF)) 
    \fall_seen_q[0]_i_2 
       (.I0(\partial_age_q[31]_i_4_n_0 ),
        .I1(\fall_seen_q_reg_n_0_[0] ),
        .I2(\previous_q_reg_n_0_[0] ),
        .I3(sample_levels[0]),
        .O(\fall_seen_q[0]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'h007F00FF00000088)) 
    \fall_seen_q[1]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\high2_q_reg[31]_0 ),
        .I4(\fall_seen_q[1]_i_2_n_0 ),
        .I5(\fall_seen_q_reg_n_0_[1] ),
        .O(\fall_seen_q[1]_i_1_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair3" *) 
  LUT4 #(
    .INIT(16'hFFEF)) 
    \fall_seen_q[1]_i_2 
       (.I0(\partial_age_q[31]_i_4_n_0 ),
        .I1(\fall_seen_q_reg_n_0_[1] ),
        .I2(\previous_q_reg_n_0_[1] ),
        .I3(sample_levels[1]),
        .O(\fall_seen_q[1]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'h007F00FF00000088)) 
    \fall_seen_q[2]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\high2_q_reg[31]_0 ),
        .I4(\fall_seen_q[2]_i_2_n_0 ),
        .I5(p_0_in),
        .O(\fall_seen_q[2]_i_1_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair2" *) 
  LUT4 #(
    .INIT(16'hFFEF)) 
    \fall_seen_q[2]_i_2 
       (.I0(\partial_age_q[31]_i_4_n_0 ),
        .I1(p_0_in),
        .I2(\previous_q_reg_n_0_[2] ),
        .I3(sample_levels[2]),
        .O(\fall_seen_q[2]_i_2_n_0 ));
  FDRE \fall_seen_q_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\fall_seen_q[0]_i_1_n_0 ),
        .Q(\fall_seen_q_reg_n_0_[0] ),
        .R(1'b0));
  FDRE \fall_seen_q_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\fall_seen_q[1]_i_1_n_0 ),
        .Q(\fall_seen_q_reg_n_0_[1] ),
        .R(1'b0));
  FDRE \fall_seen_q_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\fall_seen_q[2]_i_1_n_0 ),
        .Q(p_0_in),
        .R(1'b0));
  LUT4 #(
    .INIT(16'h8088)) 
    \high0_q[31]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\fall_seen_q[0]_i_2_n_0 ),
        .O(\high0_q[31]_i_1_n_0 ));
  FDRE \high0_q_reg[0] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(\partial_age_q[0]_i_1_n_0 ),
        .Q(\high0_q_reg_n_0_[0] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[10] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[10]),
        .Q(\high0_q_reg_n_0_[10] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[11] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[11]),
        .Q(\high0_q_reg_n_0_[11] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[12] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[12]),
        .Q(\high0_q_reg_n_0_[12] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[13] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[13]),
        .Q(\high0_q_reg_n_0_[13] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[14] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[14]),
        .Q(\high0_q_reg_n_0_[14] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[15] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[15]),
        .Q(\high0_q_reg_n_0_[15] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[16] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[16]),
        .Q(\high0_q_reg_n_0_[16] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[17] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[17]),
        .Q(\high0_q_reg_n_0_[17] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[18] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[18]),
        .Q(\high0_q_reg_n_0_[18] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[19] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[19]),
        .Q(\high0_q_reg_n_0_[19] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[1] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[1]),
        .Q(\high0_q_reg_n_0_[1] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[20] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[20]),
        .Q(\high0_q_reg_n_0_[20] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[21] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[21]),
        .Q(\high0_q_reg_n_0_[21] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[22] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[22]),
        .Q(\high0_q_reg_n_0_[22] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[23] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[23]),
        .Q(\high0_q_reg_n_0_[23] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[24] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[24]),
        .Q(\high0_q_reg_n_0_[24] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[25] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[25]),
        .Q(\high0_q_reg_n_0_[25] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[26] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[26]),
        .Q(\high0_q_reg_n_0_[26] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[27] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[27]),
        .Q(\high0_q_reg_n_0_[27] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[28] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[28]),
        .Q(\high0_q_reg_n_0_[28] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[29] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[29]),
        .Q(\high0_q_reg_n_0_[29] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[2] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[2]),
        .Q(\high0_q_reg_n_0_[2] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[30] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[30]),
        .Q(\high0_q_reg_n_0_[30] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[31] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[31]),
        .Q(\high0_q_reg_n_0_[31] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[3] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[3]),
        .Q(\high0_q_reg_n_0_[3] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[4] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[4]),
        .Q(\high0_q_reg_n_0_[4] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[5] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[5]),
        .Q(\high0_q_reg_n_0_[5] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[6] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[6]),
        .Q(\high0_q_reg_n_0_[6] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[7] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[7]),
        .Q(\high0_q_reg_n_0_[7] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[8] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[8]),
        .Q(\high0_q_reg_n_0_[8] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high0_q_reg[9] 
       (.C(clk),
        .CE(\high0_q[31]_i_1_n_0 ),
        .D(p_0_in__0[9]),
        .Q(\high0_q_reg_n_0_[9] ),
        .R(\high2_q_reg[31]_0 ));
  LUT4 #(
    .INIT(16'h8088)) 
    \high1_q[31]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\fall_seen_q[1]_i_2_n_0 ),
        .O(\high1_q[31]_i_1_n_0 ));
  FDRE \high1_q_reg[0] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(\partial_age_q[0]_i_1_n_0 ),
        .Q(\high1_q_reg_n_0_[0] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[10] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[10]),
        .Q(\high1_q_reg_n_0_[10] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[11] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[11]),
        .Q(\high1_q_reg_n_0_[11] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[12] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[12]),
        .Q(\high1_q_reg_n_0_[12] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[13] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[13]),
        .Q(\high1_q_reg_n_0_[13] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[14] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[14]),
        .Q(\high1_q_reg_n_0_[14] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[15] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[15]),
        .Q(\high1_q_reg_n_0_[15] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[16] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[16]),
        .Q(\high1_q_reg_n_0_[16] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[17] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[17]),
        .Q(\high1_q_reg_n_0_[17] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[18] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[18]),
        .Q(\high1_q_reg_n_0_[18] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[19] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[19]),
        .Q(\high1_q_reg_n_0_[19] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[1] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[1]),
        .Q(\high1_q_reg_n_0_[1] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[20] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[20]),
        .Q(\high1_q_reg_n_0_[20] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[21] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[21]),
        .Q(\high1_q_reg_n_0_[21] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[22] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[22]),
        .Q(\high1_q_reg_n_0_[22] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[23] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[23]),
        .Q(\high1_q_reg_n_0_[23] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[24] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[24]),
        .Q(\high1_q_reg_n_0_[24] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[25] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[25]),
        .Q(\high1_q_reg_n_0_[25] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[26] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[26]),
        .Q(\high1_q_reg_n_0_[26] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[27] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[27]),
        .Q(\high1_q_reg_n_0_[27] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[28] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[28]),
        .Q(\high1_q_reg_n_0_[28] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[29] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[29]),
        .Q(\high1_q_reg_n_0_[29] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[2] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[2]),
        .Q(\high1_q_reg_n_0_[2] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[30] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[30]),
        .Q(\high1_q_reg_n_0_[30] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[31] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[31]),
        .Q(\high1_q_reg_n_0_[31] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[3] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[3]),
        .Q(\high1_q_reg_n_0_[3] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[4] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[4]),
        .Q(\high1_q_reg_n_0_[4] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[5] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[5]),
        .Q(\high1_q_reg_n_0_[5] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[6] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[6]),
        .Q(\high1_q_reg_n_0_[6] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[7] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[7]),
        .Q(\high1_q_reg_n_0_[7] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[8] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[8]),
        .Q(\high1_q_reg_n_0_[8] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high1_q_reg[9] 
       (.C(clk),
        .CE(\high1_q[31]_i_1_n_0 ),
        .D(p_0_in__0[9]),
        .Q(\high1_q_reg_n_0_[9] ),
        .R(\high2_q_reg[31]_0 ));
  LUT4 #(
    .INIT(16'h8088)) 
    \high2_q[31]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\fall_seen_q[2]_i_2_n_0 ),
        .O(\high2_q[31]_i_1_n_0 ));
  FDRE \high2_q_reg[0] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(\partial_age_q[0]_i_1_n_0 ),
        .Q(\high2_q_reg_n_0_[0] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[10] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[10]),
        .Q(\high2_q_reg_n_0_[10] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[11] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[11]),
        .Q(\high2_q_reg_n_0_[11] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[12] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[12]),
        .Q(\high2_q_reg_n_0_[12] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[13] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[13]),
        .Q(\high2_q_reg_n_0_[13] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[14] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[14]),
        .Q(\high2_q_reg_n_0_[14] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[15] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[15]),
        .Q(\high2_q_reg_n_0_[15] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[16] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[16]),
        .Q(\high2_q_reg_n_0_[16] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[17] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[17]),
        .Q(\high2_q_reg_n_0_[17] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[18] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[18]),
        .Q(\high2_q_reg_n_0_[18] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[19] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[19]),
        .Q(\high2_q_reg_n_0_[19] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[1] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[1]),
        .Q(\high2_q_reg_n_0_[1] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[20] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[20]),
        .Q(\high2_q_reg_n_0_[20] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[21] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[21]),
        .Q(\high2_q_reg_n_0_[21] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[22] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[22]),
        .Q(\high2_q_reg_n_0_[22] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[23] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[23]),
        .Q(\high2_q_reg_n_0_[23] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[24] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[24]),
        .Q(\high2_q_reg_n_0_[24] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[25] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[25]),
        .Q(\high2_q_reg_n_0_[25] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[26] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[26]),
        .Q(\high2_q_reg_n_0_[26] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[27] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[27]),
        .Q(\high2_q_reg_n_0_[27] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[28] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[28]),
        .Q(\high2_q_reg_n_0_[28] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[29] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[29]),
        .Q(\high2_q_reg_n_0_[29] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[2] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[2]),
        .Q(\high2_q_reg_n_0_[2] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[30] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[30]),
        .Q(\high2_q_reg_n_0_[30] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[31] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[31]),
        .Q(\high2_q_reg_n_0_[31] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[3] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[3]),
        .Q(\high2_q_reg_n_0_[3] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[4] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[4]),
        .Q(\high2_q_reg_n_0_[4] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[5] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[5]),
        .Q(\high2_q_reg_n_0_[5] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[6] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[6]),
        .Q(\high2_q_reg_n_0_[6] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[7] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[7]),
        .Q(\high2_q_reg_n_0_[7] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[8] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[8]),
        .Q(\high2_q_reg_n_0_[8] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \high2_q_reg[9] 
       (.C(clk),
        .CE(\high2_q[31]_i_1_n_0 ),
        .D(p_0_in__0[9]),
        .Q(\high2_q_reg_n_0_[9] ),
        .R(\high2_q_reg[31]_0 ));
  LUT4 #(
    .INIT(16'h08AA)) 
    incoherent_event_q_i_1
       (.I0(incoherent_event_q_i_2_n_0),
        .I1(period_overflow_event_q_i_2_n_0),
        .I2(\slot_period_q[31]_i_7_n_0 ),
        .I3(partial_valid_q_reg_n_0),
        .O(incoherent_event_q_i_1_n_0));
  LUT6 #(
    .INIT(64'h0020002000000020)) 
    incoherent_event_q_i_2
       (.I0(armed_q_i_2_n_0),
        .I1(\slot_period_q[31]_i_6_n_0 ),
        .I2(armed_q_reg_0),
        .I3(\high2_q_reg[31]_0 ),
        .I4(\partial_age_q[31]_i_3_n_0 ),
        .I5(partial_valid_q_reg_n_0),
        .O(incoherent_event_q_i_2_n_0));
  FDRE incoherent_event_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(incoherent_event_q_i_1_n_0),
        .Q(incoherent_event_q_reg_0),
        .R(1'b0));
  LUT4 #(
    .INIT(16'h0080)) 
    out_valid_INST_0
       (.I0(out_valid_INST_0_i_1_n_0),
        .I1(out_valid_INST_0_i_2_n_0),
        .I2(slot_valid_q_reg_rep_n_0),
        .I3(\high2_q_reg[31]_0 ),
        .O(out_valid));
  LUT6 #(
    .INIT(64'h0000000000010000)) 
    out_valid_INST_0_i_1
       (.I0(out_valid_0),
        .I1(window_active_q_reg),
        .I2(period_overflow_event_q_reg_0),
        .I3(incoherent_event_q_reg_0),
        .I4(\failure_code_q_reg[1]_0 ),
        .I5(out_valid_INST_0_i_4_n_0),
        .O(out_valid_INST_0_i_1_n_0));
  CARRY4 out_valid_INST_0_i_10
       (.CI(out_valid_INST_0_i_30_n_0),
        .CO({out_valid_INST_0_i_10_n_0,out_valid_INST_0_i_10_n_1,out_valid_INST_0_i_10_n_2,out_valid_INST_0_i_10_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_10_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_31_n_0,out_valid_INST_0_i_32_n_0,out_valid_INST_0_i_33_n_0,out_valid_INST_0_i_34_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    out_valid_INST_0_i_11
       (.I0(expected_high1[31]),
        .I1(out_high1[31]),
        .I2(expected_high1[30]),
        .I3(out_high1[30]),
        .O(out_valid_INST_0_i_11_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_12
       (.I0(out_high1[28]),
        .I1(expected_high1[28]),
        .I2(out_high1[27]),
        .I3(expected_high1[27]),
        .I4(expected_high1[29]),
        .I5(out_high1[29]),
        .O(out_valid_INST_0_i_12_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_13
       (.I0(out_high1[24]),
        .I1(expected_high1[24]),
        .I2(out_high1[25]),
        .I3(expected_high1[25]),
        .I4(expected_high1[26]),
        .I5(out_high1[26]),
        .O(out_valid_INST_0_i_13_n_0));
  CARRY4 out_valid_INST_0_i_14
       (.CI(out_valid_INST_0_i_35_n_0),
        .CO({out_valid_INST_0_i_14_n_0,out_valid_INST_0_i_14_n_1,out_valid_INST_0_i_14_n_2,out_valid_INST_0_i_14_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_14_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_36_n_0,out_valid_INST_0_i_37_n_0,out_valid_INST_0_i_38_n_0,out_valid_INST_0_i_39_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    out_valid_INST_0_i_15
       (.I0(expected_high0[31]),
        .I1(out_high0[31]),
        .I2(expected_high0[30]),
        .I3(out_high0[30]),
        .O(out_valid_INST_0_i_15_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_16
       (.I0(out_high0[29]),
        .I1(expected_high0[29]),
        .I2(out_high0[27]),
        .I3(expected_high0[27]),
        .I4(expected_high0[28]),
        .I5(out_high0[28]),
        .O(out_valid_INST_0_i_16_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_17
       (.I0(out_high0[24]),
        .I1(expected_high0[24]),
        .I2(out_high0[25]),
        .I3(expected_high0[25]),
        .I4(expected_high0[26]),
        .I5(out_high0[26]),
        .O(out_valid_INST_0_i_17_n_0));
  CARRY4 out_valid_INST_0_i_18
       (.CI(out_valid_INST_0_i_40_n_0),
        .CO({out_valid_INST_0_i_18_n_0,out_valid_INST_0_i_18_n_1,out_valid_INST_0_i_18_n_2,out_valid_INST_0_i_18_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_18_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_41_n_0,out_valid_INST_0_i_42_n_0,out_valid_INST_0_i_43_n_0,out_valid_INST_0_i_44_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    out_valid_INST_0_i_19
       (.I0(expected_tag[31]),
        .I1(out_tag[31]),
        .I2(expected_tag[30]),
        .I3(out_tag[30]),
        .O(out_valid_INST_0_i_19_n_0));
  LUT5 #(
    .INIT(32'h80000000)) 
    out_valid_INST_0_i_2
       (.I0(raw_equal2),
        .I1(raw_equal3),
        .I2(raw_equal0),
        .I3(raw_equal30_out),
        .I4(raw_equal1),
        .O(out_valid_INST_0_i_2_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_20
       (.I0(out_tag[28]),
        .I1(expected_tag[28]),
        .I2(out_tag[27]),
        .I3(expected_tag[27]),
        .I4(expected_tag[29]),
        .I5(out_tag[29]),
        .O(out_valid_INST_0_i_20_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_21
       (.I0(out_tag[24]),
        .I1(expected_tag[24]),
        .I2(out_tag[25]),
        .I3(expected_tag[25]),
        .I4(expected_tag[26]),
        .I5(out_tag[26]),
        .O(out_valid_INST_0_i_21_n_0));
  CARRY4 out_valid_INST_0_i_22
       (.CI(out_valid_INST_0_i_45_n_0),
        .CO({out_valid_INST_0_i_22_n_0,out_valid_INST_0_i_22_n_1,out_valid_INST_0_i_22_n_2,out_valid_INST_0_i_22_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_22_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_46_n_0,out_valid_INST_0_i_47_n_0,out_valid_INST_0_i_48_n_0,out_valid_INST_0_i_49_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    out_valid_INST_0_i_23
       (.I0(expected_period[31]),
        .I1(out_period[31]),
        .I2(expected_period[30]),
        .I3(out_period[30]),
        .O(out_valid_INST_0_i_23_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_24
       (.I0(out_period[28]),
        .I1(expected_period[28]),
        .I2(out_period[27]),
        .I3(expected_period[27]),
        .I4(expected_period[29]),
        .I5(out_period[29]),
        .O(out_valid_INST_0_i_24_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_25
       (.I0(out_period[24]),
        .I1(expected_period[24]),
        .I2(out_period[25]),
        .I3(expected_period[25]),
        .I4(expected_period[26]),
        .I5(out_period[26]),
        .O(out_valid_INST_0_i_25_n_0));
  CARRY4 out_valid_INST_0_i_26
       (.CI(out_valid_INST_0_i_50_n_0),
        .CO({out_valid_INST_0_i_26_n_0,out_valid_INST_0_i_26_n_1,out_valid_INST_0_i_26_n_2,out_valid_INST_0_i_26_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_26_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_51_n_0,out_valid_INST_0_i_52_n_0,out_valid_INST_0_i_53_n_0,out_valid_INST_0_i_54_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    out_valid_INST_0_i_27
       (.I0(expected_high2[31]),
        .I1(out_high2[31]),
        .I2(expected_high2[30]),
        .I3(out_high2[30]),
        .O(out_valid_INST_0_i_27_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_28
       (.I0(out_high2[29]),
        .I1(expected_high2[29]),
        .I2(out_high2[27]),
        .I3(expected_high2[27]),
        .I4(expected_high2[28]),
        .I5(out_high2[28]),
        .O(out_valid_INST_0_i_28_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_29
       (.I0(out_high2[24]),
        .I1(expected_high2[24]),
        .I2(out_high2[25]),
        .I3(expected_high2[25]),
        .I4(expected_high2[26]),
        .I5(out_high2[26]),
        .O(out_valid_INST_0_i_29_n_0));
  CARRY4 out_valid_INST_0_i_30
       (.CI(1'b0),
        .CO({out_valid_INST_0_i_30_n_0,out_valid_INST_0_i_30_n_1,out_valid_INST_0_i_30_n_2,out_valid_INST_0_i_30_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_30_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_55_n_0,out_valid_INST_0_i_56_n_0,out_valid_INST_0_i_57_n_0,out_valid_INST_0_i_58_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_31
       (.I0(out_high1[21]),
        .I1(expected_high1[21]),
        .I2(out_high1[22]),
        .I3(expected_high1[22]),
        .I4(expected_high1[23]),
        .I5(out_high1[23]),
        .O(out_valid_INST_0_i_31_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_32
       (.I0(out_high1[18]),
        .I1(expected_high1[18]),
        .I2(out_high1[19]),
        .I3(expected_high1[19]),
        .I4(expected_high1[20]),
        .I5(out_high1[20]),
        .O(out_valid_INST_0_i_32_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_33
       (.I0(out_high1[15]),
        .I1(expected_high1[15]),
        .I2(out_high1[16]),
        .I3(expected_high1[16]),
        .I4(expected_high1[17]),
        .I5(out_high1[17]),
        .O(out_valid_INST_0_i_33_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_34
       (.I0(out_high1[13]),
        .I1(expected_high1[13]),
        .I2(out_high1[12]),
        .I3(expected_high1[12]),
        .I4(expected_high1[14]),
        .I5(out_high1[14]),
        .O(out_valid_INST_0_i_34_n_0));
  CARRY4 out_valid_INST_0_i_35
       (.CI(1'b0),
        .CO({out_valid_INST_0_i_35_n_0,out_valid_INST_0_i_35_n_1,out_valid_INST_0_i_35_n_2,out_valid_INST_0_i_35_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_35_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_59_n_0,out_valid_INST_0_i_60_n_0,out_valid_INST_0_i_61_n_0,out_valid_INST_0_i_62_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_36
       (.I0(out_high0[21]),
        .I1(expected_high0[21]),
        .I2(out_high0[22]),
        .I3(expected_high0[22]),
        .I4(expected_high0[23]),
        .I5(out_high0[23]),
        .O(out_valid_INST_0_i_36_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_37
       (.I0(out_high0[18]),
        .I1(expected_high0[18]),
        .I2(out_high0[19]),
        .I3(expected_high0[19]),
        .I4(expected_high0[20]),
        .I5(out_high0[20]),
        .O(out_valid_INST_0_i_37_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_38
       (.I0(out_high0[16]),
        .I1(expected_high0[16]),
        .I2(out_high0[15]),
        .I3(expected_high0[15]),
        .I4(expected_high0[17]),
        .I5(out_high0[17]),
        .O(out_valid_INST_0_i_38_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_39
       (.I0(out_high0[13]),
        .I1(expected_high0[13]),
        .I2(out_high0[12]),
        .I3(expected_high0[12]),
        .I4(expected_high0[14]),
        .I5(out_high0[14]),
        .O(out_valid_INST_0_i_39_n_0));
  LUT3 #(
    .INIT(8'hEF)) 
    out_valid_INST_0_i_4
       (.I0(witness_overflow_event_q_reg_0),
        .I1(overrun_event_q_reg_0),
        .I2(armed_q_reg_0),
        .O(out_valid_INST_0_i_4_n_0));
  CARRY4 out_valid_INST_0_i_40
       (.CI(1'b0),
        .CO({out_valid_INST_0_i_40_n_0,out_valid_INST_0_i_40_n_1,out_valid_INST_0_i_40_n_2,out_valid_INST_0_i_40_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_40_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_63_n_0,out_valid_INST_0_i_64_n_0,out_valid_INST_0_i_65_n_0,out_valid_INST_0_i_66_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_41
       (.I0(out_tag[21]),
        .I1(expected_tag[21]),
        .I2(out_tag[22]),
        .I3(expected_tag[22]),
        .I4(expected_tag[23]),
        .I5(out_tag[23]),
        .O(out_valid_INST_0_i_41_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_42
       (.I0(out_tag[18]),
        .I1(expected_tag[18]),
        .I2(out_tag[19]),
        .I3(expected_tag[19]),
        .I4(expected_tag[20]),
        .I5(out_tag[20]),
        .O(out_valid_INST_0_i_42_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_43
       (.I0(out_tag[16]),
        .I1(expected_tag[16]),
        .I2(out_tag[15]),
        .I3(expected_tag[15]),
        .I4(expected_tag[17]),
        .I5(out_tag[17]),
        .O(out_valid_INST_0_i_43_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_44
       (.I0(out_tag[13]),
        .I1(expected_tag[13]),
        .I2(out_tag[12]),
        .I3(expected_tag[12]),
        .I4(expected_tag[14]),
        .I5(out_tag[14]),
        .O(out_valid_INST_0_i_44_n_0));
  CARRY4 out_valid_INST_0_i_45
       (.CI(1'b0),
        .CO({out_valid_INST_0_i_45_n_0,out_valid_INST_0_i_45_n_1,out_valid_INST_0_i_45_n_2,out_valid_INST_0_i_45_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_45_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_67_n_0,out_valid_INST_0_i_68_n_0,out_valid_INST_0_i_69_n_0,out_valid_INST_0_i_70_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_46
       (.I0(out_period[21]),
        .I1(expected_period[21]),
        .I2(out_period[22]),
        .I3(expected_period[22]),
        .I4(expected_period[23]),
        .I5(out_period[23]),
        .O(out_valid_INST_0_i_46_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_47
       (.I0(out_period[20]),
        .I1(expected_period[20]),
        .I2(out_period[18]),
        .I3(expected_period[18]),
        .I4(expected_period[19]),
        .I5(out_period[19]),
        .O(out_valid_INST_0_i_47_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_48
       (.I0(out_period[15]),
        .I1(expected_period[15]),
        .I2(out_period[16]),
        .I3(expected_period[16]),
        .I4(expected_period[17]),
        .I5(out_period[17]),
        .O(out_valid_INST_0_i_48_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_49
       (.I0(out_period[13]),
        .I1(expected_period[13]),
        .I2(out_period[12]),
        .I3(expected_period[12]),
        .I4(expected_period[14]),
        .I5(out_period[14]),
        .O(out_valid_INST_0_i_49_n_0));
  CARRY4 out_valid_INST_0_i_5
       (.CI(out_valid_INST_0_i_10_n_0),
        .CO({NLW_out_valid_INST_0_i_5_CO_UNCONNECTED[3],raw_equal2,out_valid_INST_0_i_5_n_2,out_valid_INST_0_i_5_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_5_O_UNCONNECTED[3:0]),
        .S({1'b0,out_valid_INST_0_i_11_n_0,out_valid_INST_0_i_12_n_0,out_valid_INST_0_i_13_n_0}));
  CARRY4 out_valid_INST_0_i_50
       (.CI(1'b0),
        .CO({out_valid_INST_0_i_50_n_0,out_valid_INST_0_i_50_n_1,out_valid_INST_0_i_50_n_2,out_valid_INST_0_i_50_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_50_O_UNCONNECTED[3:0]),
        .S({out_valid_INST_0_i_71_n_0,out_valid_INST_0_i_72_n_0,out_valid_INST_0_i_73_n_0,out_valid_INST_0_i_74_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_51
       (.I0(out_high2[21]),
        .I1(expected_high2[21]),
        .I2(out_high2[22]),
        .I3(expected_high2[22]),
        .I4(expected_high2[23]),
        .I5(out_high2[23]),
        .O(out_valid_INST_0_i_51_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_52
       (.I0(out_high2[18]),
        .I1(expected_high2[18]),
        .I2(out_high2[19]),
        .I3(expected_high2[19]),
        .I4(expected_high2[20]),
        .I5(out_high2[20]),
        .O(out_valid_INST_0_i_52_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_53
       (.I0(out_high2[15]),
        .I1(expected_high2[15]),
        .I2(out_high2[16]),
        .I3(expected_high2[16]),
        .I4(expected_high2[17]),
        .I5(out_high2[17]),
        .O(out_valid_INST_0_i_53_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_54
       (.I0(out_high2[13]),
        .I1(expected_high2[13]),
        .I2(out_high2[12]),
        .I3(expected_high2[12]),
        .I4(expected_high2[14]),
        .I5(out_high2[14]),
        .O(out_valid_INST_0_i_54_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_55
       (.I0(out_high1[10]),
        .I1(expected_high1[10]),
        .I2(out_high1[9]),
        .I3(expected_high1[9]),
        .I4(expected_high1[11]),
        .I5(out_high1[11]),
        .O(out_valid_INST_0_i_55_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_56
       (.I0(out_high1[6]),
        .I1(expected_high1[6]),
        .I2(out_high1[7]),
        .I3(expected_high1[7]),
        .I4(expected_high1[8]),
        .I5(out_high1[8]),
        .O(out_valid_INST_0_i_56_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_57
       (.I0(out_high1[3]),
        .I1(expected_high1[3]),
        .I2(out_high1[4]),
        .I3(expected_high1[4]),
        .I4(expected_high1[5]),
        .I5(out_high1[5]),
        .O(out_valid_INST_0_i_57_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_58
       (.I0(out_high1[0]),
        .I1(expected_high1[0]),
        .I2(out_high1[1]),
        .I3(expected_high1[1]),
        .I4(expected_high1[2]),
        .I5(out_high1[2]),
        .O(out_valid_INST_0_i_58_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_59
       (.I0(out_high0[10]),
        .I1(expected_high0[10]),
        .I2(out_high0[9]),
        .I3(expected_high0[9]),
        .I4(expected_high0[11]),
        .I5(out_high0[11]),
        .O(out_valid_INST_0_i_59_n_0));
  CARRY4 out_valid_INST_0_i_6
       (.CI(out_valid_INST_0_i_14_n_0),
        .CO({NLW_out_valid_INST_0_i_6_CO_UNCONNECTED[3],raw_equal3,out_valid_INST_0_i_6_n_2,out_valid_INST_0_i_6_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_6_O_UNCONNECTED[3:0]),
        .S({1'b0,out_valid_INST_0_i_15_n_0,out_valid_INST_0_i_16_n_0,out_valid_INST_0_i_17_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_60
       (.I0(out_high0[6]),
        .I1(expected_high0[6]),
        .I2(out_high0[7]),
        .I3(expected_high0[7]),
        .I4(expected_high0[8]),
        .I5(out_high0[8]),
        .O(out_valid_INST_0_i_60_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_61
       (.I0(out_high0[3]),
        .I1(expected_high0[3]),
        .I2(out_high0[4]),
        .I3(expected_high0[4]),
        .I4(expected_high0[5]),
        .I5(out_high0[5]),
        .O(out_valid_INST_0_i_61_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_62
       (.I0(out_high0[0]),
        .I1(expected_high0[0]),
        .I2(out_high0[1]),
        .I3(expected_high0[1]),
        .I4(expected_high0[2]),
        .I5(out_high0[2]),
        .O(out_valid_INST_0_i_62_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_63
       (.I0(out_tag[10]),
        .I1(expected_tag[10]),
        .I2(out_tag[9]),
        .I3(expected_tag[9]),
        .I4(expected_tag[11]),
        .I5(out_tag[11]),
        .O(out_valid_INST_0_i_63_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_64
       (.I0(out_tag[6]),
        .I1(expected_tag[6]),
        .I2(out_tag[7]),
        .I3(expected_tag[7]),
        .I4(expected_tag[8]),
        .I5(out_tag[8]),
        .O(out_valid_INST_0_i_64_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_65
       (.I0(out_tag[3]),
        .I1(expected_tag[3]),
        .I2(out_tag[4]),
        .I3(expected_tag[4]),
        .I4(expected_tag[5]),
        .I5(out_tag[5]),
        .O(out_valid_INST_0_i_65_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_66
       (.I0(out_tag[0]),
        .I1(expected_tag[0]),
        .I2(out_tag[1]),
        .I3(expected_tag[1]),
        .I4(expected_tag[2]),
        .I5(out_tag[2]),
        .O(out_valid_INST_0_i_66_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_67
       (.I0(out_period[11]),
        .I1(expected_period[11]),
        .I2(out_period[9]),
        .I3(expected_period[9]),
        .I4(expected_period[10]),
        .I5(out_period[10]),
        .O(out_valid_INST_0_i_67_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_68
       (.I0(out_period[6]),
        .I1(expected_period[6]),
        .I2(out_period[7]),
        .I3(expected_period[7]),
        .I4(expected_period[8]),
        .I5(out_period[8]),
        .O(out_valid_INST_0_i_68_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_69
       (.I0(out_period[3]),
        .I1(expected_period[3]),
        .I2(out_period[4]),
        .I3(expected_period[4]),
        .I4(expected_period[5]),
        .I5(out_period[5]),
        .O(out_valid_INST_0_i_69_n_0));
  CARRY4 out_valid_INST_0_i_7
       (.CI(out_valid_INST_0_i_18_n_0),
        .CO({NLW_out_valid_INST_0_i_7_CO_UNCONNECTED[3],raw_equal0,out_valid_INST_0_i_7_n_2,out_valid_INST_0_i_7_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_7_O_UNCONNECTED[3:0]),
        .S({1'b0,out_valid_INST_0_i_19_n_0,out_valid_INST_0_i_20_n_0,out_valid_INST_0_i_21_n_0}));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_70
       (.I0(out_period[0]),
        .I1(expected_period[0]),
        .I2(out_period[1]),
        .I3(expected_period[1]),
        .I4(expected_period[2]),
        .I5(out_period[2]),
        .O(out_valid_INST_0_i_70_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_71
       (.I0(out_high2[10]),
        .I1(expected_high2[10]),
        .I2(out_high2[9]),
        .I3(expected_high2[9]),
        .I4(expected_high2[11]),
        .I5(out_high2[11]),
        .O(out_valid_INST_0_i_71_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_72
       (.I0(out_high2[6]),
        .I1(expected_high2[6]),
        .I2(out_high2[7]),
        .I3(expected_high2[7]),
        .I4(expected_high2[8]),
        .I5(out_high2[8]),
        .O(out_valid_INST_0_i_72_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_73
       (.I0(out_high2[4]),
        .I1(expected_high2[4]),
        .I2(out_high2[3]),
        .I3(expected_high2[3]),
        .I4(expected_high2[5]),
        .I5(out_high2[5]),
        .O(out_valid_INST_0_i_73_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    out_valid_INST_0_i_74
       (.I0(out_high2[0]),
        .I1(expected_high2[0]),
        .I2(out_high2[1]),
        .I3(expected_high2[1]),
        .I4(expected_high2[2]),
        .I5(out_high2[2]),
        .O(out_valid_INST_0_i_74_n_0));
  CARRY4 out_valid_INST_0_i_8
       (.CI(out_valid_INST_0_i_22_n_0),
        .CO({NLW_out_valid_INST_0_i_8_CO_UNCONNECTED[3],raw_equal30_out,out_valid_INST_0_i_8_n_2,out_valid_INST_0_i_8_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_8_O_UNCONNECTED[3:0]),
        .S({1'b0,out_valid_INST_0_i_23_n_0,out_valid_INST_0_i_24_n_0,out_valid_INST_0_i_25_n_0}));
  CARRY4 out_valid_INST_0_i_9
       (.CI(out_valid_INST_0_i_26_n_0),
        .CO({NLW_out_valid_INST_0_i_9_CO_UNCONNECTED[3],raw_equal1,out_valid_INST_0_i_9_n_2,out_valid_INST_0_i_9_n_3}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_out_valid_INST_0_i_9_O_UNCONNECTED[3:0]),
        .S({1'b0,out_valid_INST_0_i_27_n_0,out_valid_INST_0_i_28_n_0,out_valid_INST_0_i_29_n_0}));
  LUT3 #(
    .INIT(8'h02)) 
    overrun_event_q_i_1
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(overrun_event_q_i_2_n_0),
        .O(overrun_event_q_i_1_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    overrun_event_q_i_10
       (.I0(\partial_age_q_reg_n_0_[31] ),
        .I1(\partial_age_q_reg_n_0_[30] ),
        .I2(\partial_age_q_reg_n_0_[28] ),
        .I3(\partial_age_q_reg_n_0_[29] ),
        .O(overrun_event_q_i_10_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    overrun_event_q_i_11
       (.I0(\partial_age_q_reg_n_0_[18] ),
        .I1(\partial_age_q_reg_n_0_[19] ),
        .I2(\partial_age_q_reg_n_0_[16] ),
        .I3(\partial_age_q_reg_n_0_[17] ),
        .O(overrun_event_q_i_11_n_0));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFBFF)) 
    overrun_event_q_i_2
       (.I0(\slot_period_q[31]_i_9_n_0 ),
        .I1(armed_q_reg_0),
        .I2(\high2_q_reg[31]_0 ),
        .I3(\partial_age_q[31]_i_3_n_0 ),
        .I4(overrun_event_q_i_3_n_0),
        .I5(\slot_period_q[31]_i_4_n_0 ),
        .O(overrun_event_q_i_2_n_0));
  LUT4 #(
    .INIT(16'h0004)) 
    overrun_event_q_i_3
       (.I0(overrun_event_q_i_4_n_0),
        .I1(overrun_event_q_i_5_n_0),
        .I2(overrun_event_q_i_6_n_0),
        .I3(overrun_event_q_i_7_n_0),
        .O(overrun_event_q_i_3_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    overrun_event_q_i_4
       (.I0(\partial_age_q_reg_n_0_[0] ),
        .I1(\partial_age_q_reg_n_0_[1] ),
        .I2(\partial_age_q_reg_n_0_[3] ),
        .I3(\partial_age_q_reg_n_0_[2] ),
        .I4(overrun_event_q_i_8_n_0),
        .O(overrun_event_q_i_4_n_0));
  LUT5 #(
    .INIT(32'h00008000)) 
    overrun_event_q_i_5
       (.I0(\partial_age_q_reg_n_0_[9] ),
        .I1(\partial_age_q_reg_n_0_[8] ),
        .I2(\partial_age_q_reg_n_0_[11] ),
        .I3(\partial_age_q_reg_n_0_[10] ),
        .I4(overrun_event_q_i_9_n_0),
        .O(overrun_event_q_i_5_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    overrun_event_q_i_6
       (.I0(\partial_age_q_reg_n_0_[25] ),
        .I1(\partial_age_q_reg_n_0_[24] ),
        .I2(\partial_age_q_reg_n_0_[27] ),
        .I3(\partial_age_q_reg_n_0_[26] ),
        .I4(overrun_event_q_i_10_n_0),
        .O(overrun_event_q_i_6_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    overrun_event_q_i_7
       (.I0(\partial_age_q_reg_n_0_[21] ),
        .I1(\partial_age_q_reg_n_0_[20] ),
        .I2(\partial_age_q_reg_n_0_[23] ),
        .I3(\partial_age_q_reg_n_0_[22] ),
        .I4(overrun_event_q_i_11_n_0),
        .O(overrun_event_q_i_7_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    overrun_event_q_i_8
       (.I0(\partial_age_q_reg_n_0_[6] ),
        .I1(\partial_age_q_reg_n_0_[7] ),
        .I2(\partial_age_q_reg_n_0_[4] ),
        .I3(\partial_age_q_reg_n_0_[5] ),
        .O(overrun_event_q_i_8_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    overrun_event_q_i_9
       (.I0(\partial_age_q_reg_n_0_[14] ),
        .I1(\partial_age_q_reg_n_0_[15] ),
        .I2(\partial_age_q_reg_n_0_[12] ),
        .I3(\partial_age_q_reg_n_0_[13] ),
        .O(overrun_event_q_i_9_n_0));
  FDRE overrun_event_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(overrun_event_q_i_1_n_0),
        .Q(overrun_event_q_reg_0),
        .R(1'b0));
  (* SOFT_HLUTNM = "soft_lutpair5" *) 
  LUT2 #(
    .INIT(4'h1)) 
    \partial_age_q[0]_i_1 
       (.I0(\partial_age_q_reg_n_0_[0] ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(\partial_age_q[0]_i_1_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair11" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[10]_i_1 
       (.I0(\slot_period_q_reg[12]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[10]));
  (* SOFT_HLUTNM = "soft_lutpair11" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[11]_i_1 
       (.I0(\slot_period_q_reg[12]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[11]));
  (* SOFT_HLUTNM = "soft_lutpair12" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[12]_i_1 
       (.I0(\slot_period_q_reg[12]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[12]));
  (* SOFT_HLUTNM = "soft_lutpair12" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[13]_i_1 
       (.I0(\slot_period_q_reg[16]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[13]));
  (* SOFT_HLUTNM = "soft_lutpair13" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[14]_i_1 
       (.I0(\slot_period_q_reg[16]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[14]));
  (* SOFT_HLUTNM = "soft_lutpair13" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[15]_i_1 
       (.I0(\slot_period_q_reg[16]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[15]));
  (* SOFT_HLUTNM = "soft_lutpair14" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[16]_i_1 
       (.I0(\slot_period_q_reg[16]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[16]));
  (* SOFT_HLUTNM = "soft_lutpair14" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[17]_i_1 
       (.I0(\slot_period_q_reg[20]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[17]));
  (* SOFT_HLUTNM = "soft_lutpair15" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[18]_i_1 
       (.I0(\slot_period_q_reg[20]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[18]));
  (* SOFT_HLUTNM = "soft_lutpair15" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[19]_i_1 
       (.I0(\slot_period_q_reg[20]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[19]));
  (* SOFT_HLUTNM = "soft_lutpair2" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[1]_i_1 
       (.I0(\slot_period_q_reg[4]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[1]));
  (* SOFT_HLUTNM = "soft_lutpair16" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[20]_i_1 
       (.I0(\slot_period_q_reg[20]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[20]));
  (* SOFT_HLUTNM = "soft_lutpair16" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[21]_i_1 
       (.I0(\slot_period_q_reg[24]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[21]));
  (* SOFT_HLUTNM = "soft_lutpair17" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[22]_i_1 
       (.I0(\slot_period_q_reg[24]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[22]));
  (* SOFT_HLUTNM = "soft_lutpair17" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[23]_i_1 
       (.I0(\slot_period_q_reg[24]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[23]));
  (* SOFT_HLUTNM = "soft_lutpair18" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[24]_i_1 
       (.I0(\slot_period_q_reg[24]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[24]));
  (* SOFT_HLUTNM = "soft_lutpair18" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[25]_i_1 
       (.I0(\slot_period_q_reg[28]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[25]));
  (* SOFT_HLUTNM = "soft_lutpair19" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[26]_i_1 
       (.I0(\slot_period_q_reg[28]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[26]));
  (* SOFT_HLUTNM = "soft_lutpair19" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[27]_i_1 
       (.I0(\slot_period_q_reg[28]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[27]));
  (* SOFT_HLUTNM = "soft_lutpair20" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[28]_i_1 
       (.I0(\slot_period_q_reg[28]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[28]));
  (* SOFT_HLUTNM = "soft_lutpair20" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[29]_i_1 
       (.I0(\slot_period_q_reg[31]_i_11_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[29]));
  (* SOFT_HLUTNM = "soft_lutpair3" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[2]_i_1 
       (.I0(\slot_period_q_reg[4]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[2]));
  (* SOFT_HLUTNM = "soft_lutpair21" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[30]_i_1 
       (.I0(\slot_period_q_reg[31]_i_11_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[30]));
  LUT4 #(
    .INIT(16'h8088)) 
    \partial_age_q[31]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .I3(\partial_age_q[31]_i_4_n_0 ),
        .O(\partial_age_q[31]_i_1_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair21" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[31]_i_2 
       (.I0(\slot_period_q_reg[31]_i_11_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[31]));
  LUT6 #(
    .INIT(64'h0000020000000000)) 
    \partial_age_q[31]_i_3 
       (.I0(sample_levels[1]),
        .I1(\previous_q_reg_n_0_[1] ),
        .I2(\previous_q_reg_n_0_[0] ),
        .I3(sample_levels[0]),
        .I4(\previous_q_reg_n_0_[2] ),
        .I5(sample_levels[2]),
        .O(\partial_age_q[31]_i_3_n_0 ));
  LUT3 #(
    .INIT(8'hF7)) 
    \partial_age_q[31]_i_4 
       (.I0(\slot_period_q[31]_i_6_n_0 ),
        .I1(partial_valid_q_reg_n_0),
        .I2(overrun_event_q_i_3_n_0),
        .O(\partial_age_q[31]_i_4_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair4" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[3]_i_1 
       (.I0(\slot_period_q_reg[4]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[3]));
  (* SOFT_HLUTNM = "soft_lutpair8" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[4]_i_1 
       (.I0(\slot_period_q_reg[4]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[4]));
  (* SOFT_HLUTNM = "soft_lutpair8" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[5]_i_1 
       (.I0(\slot_period_q_reg[8]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[5]));
  (* SOFT_HLUTNM = "soft_lutpair9" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[6]_i_1 
       (.I0(\slot_period_q_reg[8]_i_2_n_6 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[6]));
  (* SOFT_HLUTNM = "soft_lutpair9" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[7]_i_1 
       (.I0(\slot_period_q_reg[8]_i_2_n_5 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[7]));
  (* SOFT_HLUTNM = "soft_lutpair10" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[8]_i_1 
       (.I0(\slot_period_q_reg[8]_i_2_n_4 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[8]));
  (* SOFT_HLUTNM = "soft_lutpair10" *) 
  LUT2 #(
    .INIT(4'h2)) 
    \partial_age_q[9]_i_1 
       (.I0(\slot_period_q_reg[12]_i_2_n_7 ),
        .I1(\partial_age_q[31]_i_4_n_0 ),
        .O(p_0_in__0[9]));
  FDRE \partial_age_q_reg[0] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(\partial_age_q[0]_i_1_n_0 ),
        .Q(\partial_age_q_reg_n_0_[0] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[10] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[10]),
        .Q(\partial_age_q_reg_n_0_[10] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[11] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[11]),
        .Q(\partial_age_q_reg_n_0_[11] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[12] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[12]),
        .Q(\partial_age_q_reg_n_0_[12] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[13] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[13]),
        .Q(\partial_age_q_reg_n_0_[13] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[14] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[14]),
        .Q(\partial_age_q_reg_n_0_[14] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[15] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[15]),
        .Q(\partial_age_q_reg_n_0_[15] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[16] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[16]),
        .Q(\partial_age_q_reg_n_0_[16] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[17] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[17]),
        .Q(\partial_age_q_reg_n_0_[17] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[18] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[18]),
        .Q(\partial_age_q_reg_n_0_[18] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[19] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[19]),
        .Q(\partial_age_q_reg_n_0_[19] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[1] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[1]),
        .Q(\partial_age_q_reg_n_0_[1] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[20] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[20]),
        .Q(\partial_age_q_reg_n_0_[20] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[21] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[21]),
        .Q(\partial_age_q_reg_n_0_[21] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[22] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[22]),
        .Q(\partial_age_q_reg_n_0_[22] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[23] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[23]),
        .Q(\partial_age_q_reg_n_0_[23] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[24] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[24]),
        .Q(\partial_age_q_reg_n_0_[24] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[25] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[25]),
        .Q(\partial_age_q_reg_n_0_[25] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[26] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[26]),
        .Q(\partial_age_q_reg_n_0_[26] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[27] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[27]),
        .Q(\partial_age_q_reg_n_0_[27] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[28] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[28]),
        .Q(\partial_age_q_reg_n_0_[28] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[29] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[29]),
        .Q(\partial_age_q_reg_n_0_[29] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[2] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[2]),
        .Q(\partial_age_q_reg_n_0_[2] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[30] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[30]),
        .Q(\partial_age_q_reg_n_0_[30] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[31] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[31]),
        .Q(\partial_age_q_reg_n_0_[31] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[3] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[3]),
        .Q(\partial_age_q_reg_n_0_[3] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[4] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[4]),
        .Q(\partial_age_q_reg_n_0_[4] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[5] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[5]),
        .Q(\partial_age_q_reg_n_0_[5] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[6] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[6]),
        .Q(\partial_age_q_reg_n_0_[6] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[7] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[7]),
        .Q(\partial_age_q_reg_n_0_[7] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[8] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[8]),
        .Q(\partial_age_q_reg_n_0_[8] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_age_q_reg[9] 
       (.C(clk),
        .CE(\partial_age_q[31]_i_1_n_0 ),
        .D(p_0_in__0[9]),
        .Q(\partial_age_q_reg_n_0_[9] ),
        .R(\high2_q_reg[31]_0 ));
  (* SOFT_HLUTNM = "soft_lutpair0" *) 
  LUT1 #(
    .INIT(2'h1)) 
    \partial_start_q[0]_i_1 
       (.I0(tick_q_reg[0]),
        .O(\partial_start_q[0]_i_1_n_0 ));
  LUT3 #(
    .INIT(8'h80)) 
    \partial_start_q[63]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\partial_age_q[31]_i_3_n_0 ),
        .O(\partial_start_q[63]_i_1_n_0 ));
  FDRE \partial_start_q_reg[0] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q[0]_i_1_n_0 ),
        .Q(\partial_start_q_reg_n_0_[0] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[10] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[12]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[10] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[11] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[12]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[11] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[12] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[12]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[12] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[12]_i_1 
       (.CI(\partial_start_q_reg[8]_i_1_n_0 ),
        .CO({\partial_start_q_reg[12]_i_1_n_0 ,\partial_start_q_reg[12]_i_1_n_1 ,\partial_start_q_reg[12]_i_1_n_2 ,\partial_start_q_reg[12]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[12]_i_1_n_4 ,\partial_start_q_reg[12]_i_1_n_5 ,\partial_start_q_reg[12]_i_1_n_6 ,\partial_start_q_reg[12]_i_1_n_7 }),
        .S(tick_q_reg[12:9]));
  FDRE \partial_start_q_reg[13] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[16]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[13] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[14] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[16]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[14] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[15] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[16]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[15] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[16] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[16]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[16] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[16]_i_1 
       (.CI(\partial_start_q_reg[12]_i_1_n_0 ),
        .CO({\partial_start_q_reg[16]_i_1_n_0 ,\partial_start_q_reg[16]_i_1_n_1 ,\partial_start_q_reg[16]_i_1_n_2 ,\partial_start_q_reg[16]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[16]_i_1_n_4 ,\partial_start_q_reg[16]_i_1_n_5 ,\partial_start_q_reg[16]_i_1_n_6 ,\partial_start_q_reg[16]_i_1_n_7 }),
        .S(tick_q_reg[16:13]));
  FDRE \partial_start_q_reg[17] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[20]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[17] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[18] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[20]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[18] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[19] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[20]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[19] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[1] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[4]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[1] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[20] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[20]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[20] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[20]_i_1 
       (.CI(\partial_start_q_reg[16]_i_1_n_0 ),
        .CO({\partial_start_q_reg[20]_i_1_n_0 ,\partial_start_q_reg[20]_i_1_n_1 ,\partial_start_q_reg[20]_i_1_n_2 ,\partial_start_q_reg[20]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[20]_i_1_n_4 ,\partial_start_q_reg[20]_i_1_n_5 ,\partial_start_q_reg[20]_i_1_n_6 ,\partial_start_q_reg[20]_i_1_n_7 }),
        .S(tick_q_reg[20:17]));
  FDRE \partial_start_q_reg[21] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[24]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[21] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[22] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[24]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[22] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[23] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[24]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[23] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[24] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[24]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[24] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[24]_i_1 
       (.CI(\partial_start_q_reg[20]_i_1_n_0 ),
        .CO({\partial_start_q_reg[24]_i_1_n_0 ,\partial_start_q_reg[24]_i_1_n_1 ,\partial_start_q_reg[24]_i_1_n_2 ,\partial_start_q_reg[24]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[24]_i_1_n_4 ,\partial_start_q_reg[24]_i_1_n_5 ,\partial_start_q_reg[24]_i_1_n_6 ,\partial_start_q_reg[24]_i_1_n_7 }),
        .S(tick_q_reg[24:21]));
  FDRE \partial_start_q_reg[25] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[28]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[25] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[26] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[28]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[26] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[27] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[28]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[27] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[28] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[28]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[28] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[28]_i_1 
       (.CI(\partial_start_q_reg[24]_i_1_n_0 ),
        .CO({\partial_start_q_reg[28]_i_1_n_0 ,\partial_start_q_reg[28]_i_1_n_1 ,\partial_start_q_reg[28]_i_1_n_2 ,\partial_start_q_reg[28]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[28]_i_1_n_4 ,\partial_start_q_reg[28]_i_1_n_5 ,\partial_start_q_reg[28]_i_1_n_6 ,\partial_start_q_reg[28]_i_1_n_7 }),
        .S(tick_q_reg[28:25]));
  FDRE \partial_start_q_reg[29] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[32]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[29] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[2] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[4]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[2] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[30] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[32]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[30] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[31] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[32]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[31] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[32] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[32]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[32] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[32]_i_1 
       (.CI(\partial_start_q_reg[28]_i_1_n_0 ),
        .CO({\partial_start_q_reg[32]_i_1_n_0 ,\partial_start_q_reg[32]_i_1_n_1 ,\partial_start_q_reg[32]_i_1_n_2 ,\partial_start_q_reg[32]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[32]_i_1_n_4 ,\partial_start_q_reg[32]_i_1_n_5 ,\partial_start_q_reg[32]_i_1_n_6 ,\partial_start_q_reg[32]_i_1_n_7 }),
        .S(tick_q_reg[32:29]));
  FDRE \partial_start_q_reg[33] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[36]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[33] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[34] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[36]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[34] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[35] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[36]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[35] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[36] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[36]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[36] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[36]_i_1 
       (.CI(\partial_start_q_reg[32]_i_1_n_0 ),
        .CO({\partial_start_q_reg[36]_i_1_n_0 ,\partial_start_q_reg[36]_i_1_n_1 ,\partial_start_q_reg[36]_i_1_n_2 ,\partial_start_q_reg[36]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[36]_i_1_n_4 ,\partial_start_q_reg[36]_i_1_n_5 ,\partial_start_q_reg[36]_i_1_n_6 ,\partial_start_q_reg[36]_i_1_n_7 }),
        .S(tick_q_reg[36:33]));
  FDRE \partial_start_q_reg[37] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[40]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[37] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[38] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[40]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[38] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[39] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[40]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[39] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[3] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[4]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[3] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[40] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[40]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[40] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[40]_i_1 
       (.CI(\partial_start_q_reg[36]_i_1_n_0 ),
        .CO({\partial_start_q_reg[40]_i_1_n_0 ,\partial_start_q_reg[40]_i_1_n_1 ,\partial_start_q_reg[40]_i_1_n_2 ,\partial_start_q_reg[40]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[40]_i_1_n_4 ,\partial_start_q_reg[40]_i_1_n_5 ,\partial_start_q_reg[40]_i_1_n_6 ,\partial_start_q_reg[40]_i_1_n_7 }),
        .S(tick_q_reg[40:37]));
  FDRE \partial_start_q_reg[41] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[44]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[41] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[42] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[44]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[42] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[43] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[44]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[43] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[44] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[44]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[44] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[44]_i_1 
       (.CI(\partial_start_q_reg[40]_i_1_n_0 ),
        .CO({\partial_start_q_reg[44]_i_1_n_0 ,\partial_start_q_reg[44]_i_1_n_1 ,\partial_start_q_reg[44]_i_1_n_2 ,\partial_start_q_reg[44]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[44]_i_1_n_4 ,\partial_start_q_reg[44]_i_1_n_5 ,\partial_start_q_reg[44]_i_1_n_6 ,\partial_start_q_reg[44]_i_1_n_7 }),
        .S(tick_q_reg[44:41]));
  FDRE \partial_start_q_reg[45] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[48]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[45] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[46] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[48]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[46] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[47] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[48]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[47] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[48] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[48]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[48] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[48]_i_1 
       (.CI(\partial_start_q_reg[44]_i_1_n_0 ),
        .CO({\partial_start_q_reg[48]_i_1_n_0 ,\partial_start_q_reg[48]_i_1_n_1 ,\partial_start_q_reg[48]_i_1_n_2 ,\partial_start_q_reg[48]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[48]_i_1_n_4 ,\partial_start_q_reg[48]_i_1_n_5 ,\partial_start_q_reg[48]_i_1_n_6 ,\partial_start_q_reg[48]_i_1_n_7 }),
        .S(tick_q_reg[48:45]));
  FDRE \partial_start_q_reg[49] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[52]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[49] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[4] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[4]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[4] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[4]_i_1 
       (.CI(1'b0),
        .CO({\partial_start_q_reg[4]_i_1_n_0 ,\partial_start_q_reg[4]_i_1_n_1 ,\partial_start_q_reg[4]_i_1_n_2 ,\partial_start_q_reg[4]_i_1_n_3 }),
        .CYINIT(tick_q_reg[0]),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[4]_i_1_n_4 ,\partial_start_q_reg[4]_i_1_n_5 ,\partial_start_q_reg[4]_i_1_n_6 ,\partial_start_q_reg[4]_i_1_n_7 }),
        .S(tick_q_reg[4:1]));
  FDRE \partial_start_q_reg[50] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[52]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[50] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[51] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[52]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[51] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[52] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[52]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[52] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[52]_i_1 
       (.CI(\partial_start_q_reg[48]_i_1_n_0 ),
        .CO({\partial_start_q_reg[52]_i_1_n_0 ,\partial_start_q_reg[52]_i_1_n_1 ,\partial_start_q_reg[52]_i_1_n_2 ,\partial_start_q_reg[52]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[52]_i_1_n_4 ,\partial_start_q_reg[52]_i_1_n_5 ,\partial_start_q_reg[52]_i_1_n_6 ,\partial_start_q_reg[52]_i_1_n_7 }),
        .S(tick_q_reg[52:49]));
  FDRE \partial_start_q_reg[53] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[56]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[53] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[54] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[56]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[54] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[55] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[56]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[55] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[56] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[56]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[56] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[56]_i_1 
       (.CI(\partial_start_q_reg[52]_i_1_n_0 ),
        .CO({\partial_start_q_reg[56]_i_1_n_0 ,\partial_start_q_reg[56]_i_1_n_1 ,\partial_start_q_reg[56]_i_1_n_2 ,\partial_start_q_reg[56]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[56]_i_1_n_4 ,\partial_start_q_reg[56]_i_1_n_5 ,\partial_start_q_reg[56]_i_1_n_6 ,\partial_start_q_reg[56]_i_1_n_7 }),
        .S(tick_q_reg[56:53]));
  FDRE \partial_start_q_reg[57] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[60]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[57] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[58] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[60]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[58] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[59] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[60]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[59] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[5] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[8]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[5] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[60] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[60]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[60] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[60]_i_1 
       (.CI(\partial_start_q_reg[56]_i_1_n_0 ),
        .CO({\partial_start_q_reg[60]_i_1_n_0 ,\partial_start_q_reg[60]_i_1_n_1 ,\partial_start_q_reg[60]_i_1_n_2 ,\partial_start_q_reg[60]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[60]_i_1_n_4 ,\partial_start_q_reg[60]_i_1_n_5 ,\partial_start_q_reg[60]_i_1_n_6 ,\partial_start_q_reg[60]_i_1_n_7 }),
        .S(tick_q_reg[60:57]));
  FDRE \partial_start_q_reg[61] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[63]_i_2_n_7 ),
        .Q(\partial_start_q_reg_n_0_[61] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[62] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[63]_i_2_n_6 ),
        .Q(\partial_start_q_reg_n_0_[62] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[63] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[63]_i_2_n_5 ),
        .Q(\partial_start_q_reg_n_0_[63] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[63]_i_2 
       (.CI(\partial_start_q_reg[60]_i_1_n_0 ),
        .CO({\NLW_partial_start_q_reg[63]_i_2_CO_UNCONNECTED [3:2],\partial_start_q_reg[63]_i_2_n_2 ,\partial_start_q_reg[63]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_partial_start_q_reg[63]_i_2_O_UNCONNECTED [3],\partial_start_q_reg[63]_i_2_n_5 ,\partial_start_q_reg[63]_i_2_n_6 ,\partial_start_q_reg[63]_i_2_n_7 }),
        .S({1'b0,tick_q_reg[63:61]}));
  FDRE \partial_start_q_reg[6] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[8]_i_1_n_6 ),
        .Q(\partial_start_q_reg_n_0_[6] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[7] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[8]_i_1_n_5 ),
        .Q(\partial_start_q_reg_n_0_[7] ),
        .R(\high2_q_reg[31]_0 ));
  FDRE \partial_start_q_reg[8] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[8]_i_1_n_4 ),
        .Q(\partial_start_q_reg_n_0_[8] ),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \partial_start_q_reg[8]_i_1 
       (.CI(\partial_start_q_reg[4]_i_1_n_0 ),
        .CO({\partial_start_q_reg[8]_i_1_n_0 ,\partial_start_q_reg[8]_i_1_n_1 ,\partial_start_q_reg[8]_i_1_n_2 ,\partial_start_q_reg[8]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\partial_start_q_reg[8]_i_1_n_4 ,\partial_start_q_reg[8]_i_1_n_5 ,\partial_start_q_reg[8]_i_1_n_6 ,\partial_start_q_reg[8]_i_1_n_7 }),
        .S(tick_q_reg[8:5]));
  FDRE \partial_start_q_reg[9] 
       (.C(clk),
        .CE(\partial_start_q[63]_i_1_n_0 ),
        .D(\partial_start_q_reg[12]_i_1_n_7 ),
        .Q(\partial_start_q_reg_n_0_[9] ),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h0D0D0800050D0000)) 
    partial_valid_q_i_1
       (.I0(armed_q_reg_0),
        .I1(armed_q_i_2_n_0),
        .I2(\high2_q_reg[31]_0 ),
        .I3(\partial_age_q[31]_i_4_n_0 ),
        .I4(partial_valid_q_reg_n_0),
        .I5(\partial_age_q[31]_i_3_n_0 ),
        .O(partial_valid_q_i_1_n_0));
  FDRE partial_valid_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(partial_valid_q_i_1_n_0),
        .Q(partial_valid_q_reg_n_0),
        .R(1'b0));
  (* SOFT_HLUTNM = "soft_lutpair1" *) 
  LUT4 #(
    .INIT(16'h0010)) 
    period_overflow_event_q_i_1
       (.I0(\slot_period_q[31]_i_4_n_0 ),
        .I1(\high2_q_reg[31]_0 ),
        .I2(armed_q_reg_0),
        .I3(period_overflow_event_q_i_2_n_0),
        .O(period_overflow_event_q_i_1_n_0));
  (* SOFT_HLUTNM = "soft_lutpair5" *) 
  LUT4 #(
    .INIT(16'h7FFF)) 
    period_overflow_event_q_i_10
       (.I0(\partial_age_q_reg_n_0_[9] ),
        .I1(\partial_age_q_reg_n_0_[0] ),
        .I2(\partial_age_q_reg_n_0_[25] ),
        .I3(\partial_age_q_reg_n_0_[17] ),
        .O(period_overflow_event_q_i_10_n_0));
  LUT4 #(
    .INIT(16'hFFFE)) 
    period_overflow_event_q_i_2
       (.I0(period_overflow_event_q_i_3_n_0),
        .I1(period_overflow_event_q_i_4_n_0),
        .I2(period_overflow_event_q_i_5_n_0),
        .I3(period_overflow_event_q_i_6_n_0),
        .O(period_overflow_event_q_i_2_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    period_overflow_event_q_i_3
       (.I0(\partial_age_q_reg_n_0_[22] ),
        .I1(\partial_age_q_reg_n_0_[31] ),
        .I2(\partial_age_q_reg_n_0_[14] ),
        .I3(\partial_age_q_reg_n_0_[2] ),
        .I4(period_overflow_event_q_i_7_n_0),
        .O(period_overflow_event_q_i_3_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    period_overflow_event_q_i_4
       (.I0(\partial_age_q_reg_n_0_[19] ),
        .I1(\partial_age_q_reg_n_0_[27] ),
        .I2(\partial_age_q_reg_n_0_[11] ),
        .I3(\partial_age_q_reg_n_0_[7] ),
        .I4(period_overflow_event_q_i_8_n_0),
        .O(period_overflow_event_q_i_4_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    period_overflow_event_q_i_5
       (.I0(\partial_age_q_reg_n_0_[16] ),
        .I1(\partial_age_q_reg_n_0_[24] ),
        .I2(\partial_age_q_reg_n_0_[8] ),
        .I3(\partial_age_q_reg_n_0_[4] ),
        .I4(period_overflow_event_q_i_9_n_0),
        .O(period_overflow_event_q_i_5_n_0));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    period_overflow_event_q_i_6
       (.I0(\partial_age_q_reg_n_0_[21] ),
        .I1(\partial_age_q_reg_n_0_[29] ),
        .I2(\partial_age_q_reg_n_0_[13] ),
        .I3(\partial_age_q_reg_n_0_[1] ),
        .I4(period_overflow_event_q_i_10_n_0),
        .O(period_overflow_event_q_i_6_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    period_overflow_event_q_i_7
       (.I0(\partial_age_q_reg_n_0_[6] ),
        .I1(\partial_age_q_reg_n_0_[10] ),
        .I2(\partial_age_q_reg_n_0_[26] ),
        .I3(\partial_age_q_reg_n_0_[18] ),
        .O(period_overflow_event_q_i_7_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    period_overflow_event_q_i_8
       (.I0(\partial_age_q_reg_n_0_[5] ),
        .I1(\partial_age_q_reg_n_0_[15] ),
        .I2(\partial_age_q_reg_n_0_[30] ),
        .I3(\partial_age_q_reg_n_0_[23] ),
        .O(period_overflow_event_q_i_8_n_0));
  LUT4 #(
    .INIT(16'h7FFF)) 
    period_overflow_event_q_i_9
       (.I0(\partial_age_q_reg_n_0_[3] ),
        .I1(\partial_age_q_reg_n_0_[12] ),
        .I2(\partial_age_q_reg_n_0_[28] ),
        .I3(\partial_age_q_reg_n_0_[20] ),
        .O(period_overflow_event_q_i_9_n_0));
  FDRE period_overflow_event_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(period_overflow_event_q_i_1_n_0),
        .Q(period_overflow_event_q_reg_0),
        .R(1'b0));
  LUT6 #(
    .INIT(64'h00000000FFF80070)) 
    \previous_q[0]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\previous_q_reg_n_0_[0] ),
        .I3(capture_rearm),
        .I4(sample_levels[0]),
        .I5(\window_tag_q_reg[31]_0 ),
        .O(\previous_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000FFF80070)) 
    \previous_q[1]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\previous_q_reg_n_0_[1] ),
        .I3(capture_rearm),
        .I4(sample_levels[1]),
        .I5(\window_tag_q_reg[31]_0 ),
        .O(\previous_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000FFF80070)) 
    \previous_q[2]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\previous_q_reg_n_0_[2] ),
        .I3(capture_rearm),
        .I4(sample_levels[2]),
        .I5(\window_tag_q_reg[31]_0 ),
        .O(\previous_q[2]_i_1_n_0 ));
  FDRE \previous_q_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\previous_q[0]_i_1_n_0 ),
        .Q(\previous_q_reg_n_0_[0] ),
        .R(1'b0));
  FDRE \previous_q_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\previous_q[1]_i_1_n_0 ),
        .Q(\previous_q_reg_n_0_[1] ),
        .R(1'b0));
  FDRE \previous_q_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\previous_q[2]_i_1_n_0 ),
        .Q(\previous_q_reg_n_0_[2] ),
        .R(1'b0));
  LUT6 #(
    .INIT(64'h000000000000000D)) 
    \slot_end_q[0]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(tick_q_reg[0]),
        .O(\slot_end_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[10]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[12]_i_1_n_6 ),
        .O(\slot_end_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[11]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[12]_i_1_n_5 ),
        .O(\slot_end_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[12]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[12]_i_1_n_4 ),
        .O(\slot_end_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[13]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[16]_i_1_n_7 ),
        .O(\slot_end_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[14]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[16]_i_1_n_6 ),
        .O(\slot_end_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[15]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[16]_i_1_n_5 ),
        .O(\slot_end_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[16]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[16]_i_1_n_4 ),
        .O(\slot_end_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[17]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[20]_i_1_n_7 ),
        .O(\slot_end_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[18]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[20]_i_1_n_6 ),
        .O(\slot_end_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[19]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[20]_i_1_n_5 ),
        .O(\slot_end_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[1]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[4]_i_1_n_7 ),
        .O(\slot_end_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[20]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[20]_i_1_n_4 ),
        .O(\slot_end_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[21]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[24]_i_1_n_7 ),
        .O(\slot_end_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[22]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[24]_i_1_n_6 ),
        .O(\slot_end_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[23]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[24]_i_1_n_5 ),
        .O(\slot_end_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[24]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[24]_i_1_n_4 ),
        .O(\slot_end_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[25]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[28]_i_1_n_7 ),
        .O(\slot_end_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[26]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[28]_i_1_n_6 ),
        .O(\slot_end_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[27]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[28]_i_1_n_5 ),
        .O(\slot_end_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[28]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[28]_i_1_n_4 ),
        .O(\slot_end_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[29]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[32]_i_1_n_7 ),
        .O(\slot_end_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[2]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[4]_i_1_n_6 ),
        .O(\slot_end_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[30]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[32]_i_1_n_6 ),
        .O(\slot_end_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[31]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[32]_i_1_n_5 ),
        .O(\slot_end_q[31]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[32]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[32]_i_1_n_4 ),
        .O(\slot_end_q[32]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[33]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[36]_i_1_n_7 ),
        .O(\slot_end_q[33]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[34]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[36]_i_1_n_6 ),
        .O(\slot_end_q[34]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[35]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[36]_i_1_n_5 ),
        .O(\slot_end_q[35]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[36]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[36]_i_1_n_4 ),
        .O(\slot_end_q[36]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[37]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[40]_i_1_n_7 ),
        .O(\slot_end_q[37]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[38]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[40]_i_1_n_6 ),
        .O(\slot_end_q[38]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[39]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[40]_i_1_n_5 ),
        .O(\slot_end_q[39]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[3]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[4]_i_1_n_5 ),
        .O(\slot_end_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[40]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[40]_i_1_n_4 ),
        .O(\slot_end_q[40]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[41]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[44]_i_1_n_7 ),
        .O(\slot_end_q[41]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[42]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[44]_i_1_n_6 ),
        .O(\slot_end_q[42]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[43]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[44]_i_1_n_5 ),
        .O(\slot_end_q[43]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[44]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[44]_i_1_n_4 ),
        .O(\slot_end_q[44]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[45]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[48]_i_1_n_7 ),
        .O(\slot_end_q[45]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[46]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[48]_i_1_n_6 ),
        .O(\slot_end_q[46]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[47]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[48]_i_1_n_5 ),
        .O(\slot_end_q[47]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[48]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[48]_i_1_n_4 ),
        .O(\slot_end_q[48]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[49]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[52]_i_1_n_7 ),
        .O(\slot_end_q[49]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[4]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[4]_i_1_n_4 ),
        .O(\slot_end_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[50]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[52]_i_1_n_6 ),
        .O(\slot_end_q[50]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[51]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[52]_i_1_n_5 ),
        .O(\slot_end_q[51]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[52]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[52]_i_1_n_4 ),
        .O(\slot_end_q[52]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[53]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[56]_i_1_n_7 ),
        .O(\slot_end_q[53]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[54]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[56]_i_1_n_6 ),
        .O(\slot_end_q[54]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[55]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[56]_i_1_n_5 ),
        .O(\slot_end_q[55]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[56]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[56]_i_1_n_4 ),
        .O(\slot_end_q[56]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[57]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[60]_i_1_n_7 ),
        .O(\slot_end_q[57]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[58]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[60]_i_1_n_6 ),
        .O(\slot_end_q[58]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[59]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[60]_i_1_n_5 ),
        .O(\slot_end_q[59]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[5]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[8]_i_1_n_7 ),
        .O(\slot_end_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[60]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[60]_i_1_n_4 ),
        .O(\slot_end_q[60]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[61]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[63]_i_2_n_7 ),
        .O(\slot_end_q[61]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[62]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[63]_i_2_n_6 ),
        .O(\slot_end_q[62]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[63]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[63]_i_2_n_5 ),
        .O(\slot_end_q[63]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[6]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[8]_i_1_n_6 ),
        .O(\slot_end_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[7]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[8]_i_1_n_5 ),
        .O(\slot_end_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[8]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[8]_i_1_n_4 ),
        .O(\slot_end_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_end_q[9]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg[12]_i_1_n_7 ),
        .O(\slot_end_q[9]_i_1_n_0 ));
  FDRE \slot_end_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[0]_i_1_n_0 ),
        .Q(out_end[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[10]_i_1_n_0 ),
        .Q(out_end[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[11]_i_1_n_0 ),
        .Q(out_end[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[12]_i_1_n_0 ),
        .Q(out_end[12]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[13]_i_1_n_0 ),
        .Q(out_end[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[14]_i_1_n_0 ),
        .Q(out_end[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[15]_i_1_n_0 ),
        .Q(out_end[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[16]_i_1_n_0 ),
        .Q(out_end[16]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[17]_i_1_n_0 ),
        .Q(out_end[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[18]_i_1_n_0 ),
        .Q(out_end[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[19]_i_1_n_0 ),
        .Q(out_end[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[1]_i_1_n_0 ),
        .Q(out_end[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[20]_i_1_n_0 ),
        .Q(out_end[20]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[21]_i_1_n_0 ),
        .Q(out_end[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[22]_i_1_n_0 ),
        .Q(out_end[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[23]_i_1_n_0 ),
        .Q(out_end[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[24]_i_1_n_0 ),
        .Q(out_end[24]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[25]_i_1_n_0 ),
        .Q(out_end[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[26]_i_1_n_0 ),
        .Q(out_end[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[27]_i_1_n_0 ),
        .Q(out_end[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[28]_i_1_n_0 ),
        .Q(out_end[28]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[29]_i_1_n_0 ),
        .Q(out_end[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[2]_i_1_n_0 ),
        .Q(out_end[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[30]_i_1_n_0 ),
        .Q(out_end[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[31]_i_1_n_0 ),
        .Q(out_end[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[32] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[32]_i_1_n_0 ),
        .Q(out_end[32]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[33] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[33]_i_1_n_0 ),
        .Q(out_end[33]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[34] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[34]_i_1_n_0 ),
        .Q(out_end[34]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[35] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[35]_i_1_n_0 ),
        .Q(out_end[35]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[36] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[36]_i_1_n_0 ),
        .Q(out_end[36]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[37] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[37]_i_1_n_0 ),
        .Q(out_end[37]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[38] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[38]_i_1_n_0 ),
        .Q(out_end[38]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[39] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[39]_i_1_n_0 ),
        .Q(out_end[39]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[3]_i_1_n_0 ),
        .Q(out_end[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[40] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[40]_i_1_n_0 ),
        .Q(out_end[40]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[41] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[41]_i_1_n_0 ),
        .Q(out_end[41]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[42] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[42]_i_1_n_0 ),
        .Q(out_end[42]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[43] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[43]_i_1_n_0 ),
        .Q(out_end[43]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[44] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[44]_i_1_n_0 ),
        .Q(out_end[44]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[45] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[45]_i_1_n_0 ),
        .Q(out_end[45]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[46] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[46]_i_1_n_0 ),
        .Q(out_end[46]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[47] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[47]_i_1_n_0 ),
        .Q(out_end[47]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[48] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[48]_i_1_n_0 ),
        .Q(out_end[48]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[49] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[49]_i_1_n_0 ),
        .Q(out_end[49]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[4]_i_1_n_0 ),
        .Q(out_end[4]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[50] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[50]_i_1_n_0 ),
        .Q(out_end[50]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[51] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[51]_i_1_n_0 ),
        .Q(out_end[51]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[52] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[52]_i_1_n_0 ),
        .Q(out_end[52]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[53] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[53]_i_1_n_0 ),
        .Q(out_end[53]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[54] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[54]_i_1_n_0 ),
        .Q(out_end[54]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[55] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[55]_i_1_n_0 ),
        .Q(out_end[55]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[56] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[56]_i_1_n_0 ),
        .Q(out_end[56]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[57] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[57]_i_1_n_0 ),
        .Q(out_end[57]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[58] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[58]_i_1_n_0 ),
        .Q(out_end[58]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[59] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[59]_i_1_n_0 ),
        .Q(out_end[59]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[5]_i_1_n_0 ),
        .Q(out_end[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[60] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[60]_i_1_n_0 ),
        .Q(out_end[60]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[61] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[61]_i_1_n_0 ),
        .Q(out_end[61]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[62] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[62]_i_1_n_0 ),
        .Q(out_end[62]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[63] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[63]_i_1_n_0 ),
        .Q(out_end[63]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[6]_i_1_n_0 ),
        .Q(out_end[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[7]_i_1_n_0 ),
        .Q(out_end[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[8]_i_1_n_0 ),
        .Q(out_end[8]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_end_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_end_q[9]_i_1_n_0 ),
        .Q(out_end[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[0]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[0] ),
        .O(\slot_high0_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[10]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[10] ),
        .O(\slot_high0_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[11]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[11] ),
        .O(\slot_high0_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[12]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[12] ),
        .O(\slot_high0_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[13]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[13] ),
        .O(\slot_high0_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[14]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[14] ),
        .O(\slot_high0_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[15]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[15] ),
        .O(\slot_high0_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[16]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[16] ),
        .O(\slot_high0_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[17]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[17] ),
        .O(\slot_high0_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[18]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[18] ),
        .O(\slot_high0_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[19]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[19] ),
        .O(\slot_high0_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[1]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[1] ),
        .O(\slot_high0_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[20]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[20] ),
        .O(\slot_high0_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[21]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[21] ),
        .O(\slot_high0_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[22]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[22] ),
        .O(\slot_high0_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[23]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[23] ),
        .O(\slot_high0_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[24]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[24] ),
        .O(\slot_high0_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[25]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[25] ),
        .O(\slot_high0_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[26]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[26] ),
        .O(\slot_high0_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[27]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[27] ),
        .O(\slot_high0_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[28]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[28] ),
        .O(\slot_high0_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[29]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[29] ),
        .O(\slot_high0_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[2]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[2] ),
        .O(\slot_high0_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[30]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[30] ),
        .O(\slot_high0_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[31]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[31] ),
        .O(\slot_high0_q[31]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[3]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[3] ),
        .O(\slot_high0_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[4]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[4] ),
        .O(\slot_high0_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[5]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[5] ),
        .O(\slot_high0_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[6]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[6] ),
        .O(\slot_high0_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[7]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[7] ),
        .O(\slot_high0_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[8]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[8] ),
        .O(\slot_high0_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high0_q[9]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high0_q_reg_n_0_[9] ),
        .O(\slot_high0_q[9]_i_1_n_0 ));
  FDRE \slot_high0_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[0]_i_1_n_0 ),
        .Q(out_high0[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[10]_i_1_n_0 ),
        .Q(out_high0[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[11]_i_1_n_0 ),
        .Q(out_high0[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[12]_i_1_n_0 ),
        .Q(out_high0[12]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[13]_i_1_n_0 ),
        .Q(out_high0[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[14]_i_1_n_0 ),
        .Q(out_high0[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[15]_i_1_n_0 ),
        .Q(out_high0[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[16]_i_1_n_0 ),
        .Q(out_high0[16]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[17]_i_1_n_0 ),
        .Q(out_high0[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[18]_i_1_n_0 ),
        .Q(out_high0[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[19]_i_1_n_0 ),
        .Q(out_high0[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[1]_i_1_n_0 ),
        .Q(out_high0[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[20]_i_1_n_0 ),
        .Q(out_high0[20]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[21]_i_1_n_0 ),
        .Q(out_high0[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[22]_i_1_n_0 ),
        .Q(out_high0[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[23]_i_1_n_0 ),
        .Q(out_high0[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[24]_i_1_n_0 ),
        .Q(out_high0[24]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[25]_i_1_n_0 ),
        .Q(out_high0[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[26]_i_1_n_0 ),
        .Q(out_high0[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[27]_i_1_n_0 ),
        .Q(out_high0[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[28]_i_1_n_0 ),
        .Q(out_high0[28]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[29]_i_1_n_0 ),
        .Q(out_high0[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[2]_i_1_n_0 ),
        .Q(out_high0[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[30]_i_1_n_0 ),
        .Q(out_high0[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[31]_i_1_n_0 ),
        .Q(out_high0[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[3]_i_1_n_0 ),
        .Q(out_high0[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[4]_i_1_n_0 ),
        .Q(out_high0[4]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[5]_i_1_n_0 ),
        .Q(out_high0[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[6]_i_1_n_0 ),
        .Q(out_high0[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[7]_i_1_n_0 ),
        .Q(out_high0[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[8]_i_1_n_0 ),
        .Q(out_high0[8]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high0_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high0_q[9]_i_1_n_0 ),
        .Q(out_high0[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[0]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[0] ),
        .O(\slot_high1_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[10]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[10] ),
        .O(\slot_high1_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[11]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[11] ),
        .O(\slot_high1_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[12]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[12] ),
        .O(\slot_high1_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[13]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[13] ),
        .O(\slot_high1_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[14]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[14] ),
        .O(\slot_high1_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[15]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[15] ),
        .O(\slot_high1_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[16]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[16] ),
        .O(\slot_high1_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[17]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[17] ),
        .O(\slot_high1_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[18]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[18] ),
        .O(\slot_high1_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[19]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[19] ),
        .O(\slot_high1_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[1]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[1] ),
        .O(\slot_high1_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[20]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[20] ),
        .O(\slot_high1_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[21]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[21] ),
        .O(\slot_high1_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[22]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[22] ),
        .O(\slot_high1_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[23]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[23] ),
        .O(\slot_high1_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[24]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[24] ),
        .O(\slot_high1_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[25]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[25] ),
        .O(\slot_high1_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[26]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[26] ),
        .O(\slot_high1_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[27]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[27] ),
        .O(\slot_high1_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[28]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[28] ),
        .O(\slot_high1_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[29]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[29] ),
        .O(\slot_high1_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[2]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[2] ),
        .O(\slot_high1_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[30]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[30] ),
        .O(\slot_high1_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[31]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[31] ),
        .O(\slot_high1_q[31]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[3]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[3] ),
        .O(\slot_high1_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[4]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[4] ),
        .O(\slot_high1_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[5]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[5] ),
        .O(\slot_high1_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[6]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[6] ),
        .O(\slot_high1_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[7]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[7] ),
        .O(\slot_high1_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[8]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[8] ),
        .O(\slot_high1_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high1_q[9]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high1_q_reg_n_0_[9] ),
        .O(\slot_high1_q[9]_i_1_n_0 ));
  FDRE \slot_high1_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[0]_i_1_n_0 ),
        .Q(out_high1[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[10]_i_1_n_0 ),
        .Q(out_high1[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[11]_i_1_n_0 ),
        .Q(out_high1[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[12]_i_1_n_0 ),
        .Q(out_high1[12]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[13]_i_1_n_0 ),
        .Q(out_high1[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[14]_i_1_n_0 ),
        .Q(out_high1[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[15]_i_1_n_0 ),
        .Q(out_high1[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[16]_i_1_n_0 ),
        .Q(out_high1[16]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[17]_i_1_n_0 ),
        .Q(out_high1[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[18]_i_1_n_0 ),
        .Q(out_high1[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[19]_i_1_n_0 ),
        .Q(out_high1[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[1]_i_1_n_0 ),
        .Q(out_high1[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[20]_i_1_n_0 ),
        .Q(out_high1[20]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[21]_i_1_n_0 ),
        .Q(out_high1[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[22]_i_1_n_0 ),
        .Q(out_high1[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[23]_i_1_n_0 ),
        .Q(out_high1[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[24]_i_1_n_0 ),
        .Q(out_high1[24]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[25]_i_1_n_0 ),
        .Q(out_high1[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[26]_i_1_n_0 ),
        .Q(out_high1[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[27]_i_1_n_0 ),
        .Q(out_high1[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[28]_i_1_n_0 ),
        .Q(out_high1[28]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[29]_i_1_n_0 ),
        .Q(out_high1[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[2]_i_1_n_0 ),
        .Q(out_high1[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[30]_i_1_n_0 ),
        .Q(out_high1[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[31]_i_1_n_0 ),
        .Q(out_high1[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[3]_i_1_n_0 ),
        .Q(out_high1[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[4]_i_1_n_0 ),
        .Q(out_high1[4]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[5]_i_1_n_0 ),
        .Q(out_high1[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[6]_i_1_n_0 ),
        .Q(out_high1[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[7]_i_1_n_0 ),
        .Q(out_high1[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[8]_i_1_n_0 ),
        .Q(out_high1[8]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high1_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high1_q[9]_i_1_n_0 ),
        .Q(out_high1[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[0]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[0] ),
        .O(\slot_high2_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[10]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[10] ),
        .O(\slot_high2_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[11]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[11] ),
        .O(\slot_high2_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[12]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[12] ),
        .O(\slot_high2_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[13]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[13] ),
        .O(\slot_high2_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[14]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[14] ),
        .O(\slot_high2_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[15]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[15] ),
        .O(\slot_high2_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[16]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[16] ),
        .O(\slot_high2_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[17]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[17] ),
        .O(\slot_high2_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[18]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[18] ),
        .O(\slot_high2_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[19]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[19] ),
        .O(\slot_high2_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[1]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[1] ),
        .O(\slot_high2_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[20]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[20] ),
        .O(\slot_high2_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[21]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[21] ),
        .O(\slot_high2_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[22]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[22] ),
        .O(\slot_high2_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[23]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[23] ),
        .O(\slot_high2_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[24]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[24] ),
        .O(\slot_high2_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[25]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[25] ),
        .O(\slot_high2_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[26]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[26] ),
        .O(\slot_high2_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[27]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[27] ),
        .O(\slot_high2_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[28]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[28] ),
        .O(\slot_high2_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[29]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[29] ),
        .O(\slot_high2_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[2]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[2] ),
        .O(\slot_high2_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[30]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[30] ),
        .O(\slot_high2_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[31]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[31] ),
        .O(\slot_high2_q[31]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[3]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[3] ),
        .O(\slot_high2_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[4]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[4] ),
        .O(\slot_high2_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[5]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[5] ),
        .O(\slot_high2_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[6]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[6] ),
        .O(\slot_high2_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[7]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[7] ),
        .O(\slot_high2_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[8]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[8] ),
        .O(\slot_high2_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_high2_q[9]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\high2_q_reg_n_0_[9] ),
        .O(\slot_high2_q[9]_i_1_n_0 ));
  FDRE \slot_high2_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[0]_i_1_n_0 ),
        .Q(out_high2[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[10]_i_1_n_0 ),
        .Q(out_high2[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[11]_i_1_n_0 ),
        .Q(out_high2[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[12]_i_1_n_0 ),
        .Q(out_high2[12]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[13]_i_1_n_0 ),
        .Q(out_high2[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[14]_i_1_n_0 ),
        .Q(out_high2[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[15]_i_1_n_0 ),
        .Q(out_high2[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[16]_i_1_n_0 ),
        .Q(out_high2[16]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[17]_i_1_n_0 ),
        .Q(out_high2[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[18]_i_1_n_0 ),
        .Q(out_high2[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[19]_i_1_n_0 ),
        .Q(out_high2[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[1]_i_1_n_0 ),
        .Q(out_high2[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[20]_i_1_n_0 ),
        .Q(out_high2[20]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[21]_i_1_n_0 ),
        .Q(out_high2[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[22]_i_1_n_0 ),
        .Q(out_high2[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[23]_i_1_n_0 ),
        .Q(out_high2[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[24]_i_1_n_0 ),
        .Q(out_high2[24]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[25]_i_1_n_0 ),
        .Q(out_high2[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[26]_i_1_n_0 ),
        .Q(out_high2[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[27]_i_1_n_0 ),
        .Q(out_high2[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[28]_i_1_n_0 ),
        .Q(out_high2[28]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[29]_i_1_n_0 ),
        .Q(out_high2[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[2]_i_1_n_0 ),
        .Q(out_high2[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[30]_i_1_n_0 ),
        .Q(out_high2[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[31]_i_1_n_0 ),
        .Q(out_high2[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[3]_i_1_n_0 ),
        .Q(out_high2[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[4]_i_1_n_0 ),
        .Q(out_high2[4]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[5]_i_1_n_0 ),
        .Q(out_high2[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[6]_i_1_n_0 ),
        .Q(out_high2[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[7]_i_1_n_0 ),
        .Q(out_high2[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[8]_i_1_n_0 ),
        .Q(out_high2[8]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_high2_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_high2_q[9]_i_1_n_0 ),
        .Q(out_high2[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h000000000000000D)) 
    \slot_period_q[0]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(\partial_age_q_reg_n_0_[0] ),
        .O(\slot_period_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[10]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[12]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[11]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[12]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[12]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[12]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[13]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[16]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[14]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[16]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[15]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[16]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[16]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[16]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[17]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[20]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[18]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[20]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[19]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[20]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[1]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[4]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[20]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[20]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[21]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[24]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[22]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[24]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[23]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[24]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[24]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[24]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[25]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[28]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[26]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[28]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[27]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[28]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[28]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[28]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[29]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[31]_i_11_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[2]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[4]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[30]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[31]_i_11_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'hAA00AA03AA00AA00)) 
    \slot_period_q[31]_i_1 
       (.I0(capture_out_ready),
        .I1(\slot_period_q[31]_i_4_n_0 ),
        .I2(\slot_period_q[31]_i_5_n_0 ),
        .I3(slot_valid_q_reg_n_0),
        .I4(\slot_period_q[31]_i_6_n_0 ),
        .I5(\slot_period_q[31]_i_7_n_0 ),
        .O(\slot_period_q[31]_i_1_n_0 ));
  LUT2 #(
    .INIT(4'h7)) 
    \slot_period_q[31]_i_10 
       (.I0(partial_valid_q_reg_n_0),
        .I1(armed_q_i_2_n_0),
        .O(\slot_period_q[31]_i_10_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_100 
       (.I0(\high2_q_reg_n_0_[23] ),
        .I1(\slot_period_q_reg[24]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[22] ),
        .I3(\slot_period_q_reg[24]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_100_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_101 
       (.I0(\high2_q_reg_n_0_[21] ),
        .I1(\slot_period_q_reg[24]_i_2_n_7 ),
        .I2(\high2_q_reg_n_0_[20] ),
        .I3(\slot_period_q_reg[20]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_101_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_102 
       (.I0(\high2_q_reg_n_0_[19] ),
        .I1(\slot_period_q_reg[20]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[18] ),
        .I3(\slot_period_q_reg[20]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_102_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_103 
       (.I0(\high2_q_reg_n_0_[17] ),
        .I1(\slot_period_q_reg[20]_i_2_n_7 ),
        .I2(\high2_q_reg_n_0_[16] ),
        .I3(\slot_period_q_reg[16]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_103_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_105 
       (.I0(\slot_period_q_reg[16]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[15] ),
        .I2(\slot_period_q_reg[16]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[14] ),
        .O(\slot_period_q[31]_i_105_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_106 
       (.I0(\slot_period_q_reg[16]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[13] ),
        .I2(\slot_period_q_reg[12]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[12] ),
        .O(\slot_period_q[31]_i_106_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_107 
       (.I0(\slot_period_q_reg[12]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[11] ),
        .I2(\slot_period_q_reg[12]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[10] ),
        .O(\slot_period_q[31]_i_107_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_108 
       (.I0(\slot_period_q_reg[12]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[9] ),
        .I2(\slot_period_q_reg[8]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[8] ),
        .O(\slot_period_q[31]_i_108_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_109 
       (.I0(\high1_q_reg_n_0_[15] ),
        .I1(\slot_period_q_reg[16]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[14] ),
        .I3(\slot_period_q_reg[16]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_109_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_110 
       (.I0(\high1_q_reg_n_0_[13] ),
        .I1(\slot_period_q_reg[16]_i_2_n_7 ),
        .I2(\high1_q_reg_n_0_[12] ),
        .I3(\slot_period_q_reg[12]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_110_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_111 
       (.I0(\high1_q_reg_n_0_[11] ),
        .I1(\slot_period_q_reg[12]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[10] ),
        .I3(\slot_period_q_reg[12]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_111_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_112 
       (.I0(\high1_q_reg_n_0_[9] ),
        .I1(\slot_period_q_reg[12]_i_2_n_7 ),
        .I2(\high1_q_reg_n_0_[8] ),
        .I3(\slot_period_q_reg[8]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_112_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_114 
       (.I0(\slot_period_q_reg[16]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[15] ),
        .I2(\slot_period_q_reg[16]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[14] ),
        .O(\slot_period_q[31]_i_114_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_115 
       (.I0(\slot_period_q_reg[16]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[13] ),
        .I2(\slot_period_q_reg[12]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[12] ),
        .O(\slot_period_q[31]_i_115_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_116 
       (.I0(\slot_period_q_reg[12]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[11] ),
        .I2(\slot_period_q_reg[12]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[10] ),
        .O(\slot_period_q[31]_i_116_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_117 
       (.I0(\slot_period_q_reg[12]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[9] ),
        .I2(\slot_period_q_reg[8]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[8] ),
        .O(\slot_period_q[31]_i_117_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_118 
       (.I0(\high0_q_reg_n_0_[15] ),
        .I1(\slot_period_q_reg[16]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[14] ),
        .I3(\slot_period_q_reg[16]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_118_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_119 
       (.I0(\high0_q_reg_n_0_[13] ),
        .I1(\slot_period_q_reg[16]_i_2_n_7 ),
        .I2(\high0_q_reg_n_0_[12] ),
        .I3(\slot_period_q_reg[12]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_119_n_0 ));
  LUT2 #(
    .INIT(4'hB)) 
    \slot_period_q[31]_i_12 
       (.I0(\slot_period_q[31]_i_5_n_0 ),
        .I1(\partial_age_q[31]_i_3_n_0 ),
        .O(\slot_period_q[31]_i_12_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_120 
       (.I0(\high0_q_reg_n_0_[11] ),
        .I1(\slot_period_q_reg[12]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[10] ),
        .I3(\slot_period_q_reg[12]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_120_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_121 
       (.I0(\high0_q_reg_n_0_[9] ),
        .I1(\slot_period_q_reg[12]_i_2_n_7 ),
        .I2(\high0_q_reg_n_0_[8] ),
        .I3(\slot_period_q_reg[8]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_121_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_123 
       (.I0(\slot_period_q_reg[16]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[15] ),
        .I2(\slot_period_q_reg[16]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[14] ),
        .O(\slot_period_q[31]_i_123_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_124 
       (.I0(\slot_period_q_reg[16]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[13] ),
        .I2(\slot_period_q_reg[12]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[12] ),
        .O(\slot_period_q[31]_i_124_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_125 
       (.I0(\slot_period_q_reg[12]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[11] ),
        .I2(\slot_period_q_reg[12]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[10] ),
        .O(\slot_period_q[31]_i_125_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_126 
       (.I0(\slot_period_q_reg[12]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[9] ),
        .I2(\slot_period_q_reg[8]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[8] ),
        .O(\slot_period_q[31]_i_126_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_127 
       (.I0(\high2_q_reg_n_0_[15] ),
        .I1(\slot_period_q_reg[16]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[14] ),
        .I3(\slot_period_q_reg[16]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_127_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_128 
       (.I0(\high2_q_reg_n_0_[13] ),
        .I1(\slot_period_q_reg[16]_i_2_n_7 ),
        .I2(\high2_q_reg_n_0_[12] ),
        .I3(\slot_period_q_reg[12]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_128_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_129 
       (.I0(\high2_q_reg_n_0_[11] ),
        .I1(\slot_period_q_reg[12]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[10] ),
        .I3(\slot_period_q_reg[12]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_129_n_0 ));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    \slot_period_q[31]_i_13 
       (.I0(\partial_age_q_reg_n_0_[7] ),
        .I1(\partial_age_q_reg_n_0_[4] ),
        .I2(\partial_age_q_reg_n_0_[2] ),
        .I3(\partial_age_q_reg_n_0_[1] ),
        .I4(\slot_period_q[31]_i_23_n_0 ),
        .O(\slot_period_q[31]_i_13_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_130 
       (.I0(\high2_q_reg_n_0_[9] ),
        .I1(\slot_period_q_reg[12]_i_2_n_7 ),
        .I2(\high2_q_reg_n_0_[8] ),
        .I3(\slot_period_q_reg[8]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_130_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_131 
       (.I0(\slot_period_q_reg[8]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[7] ),
        .I2(\slot_period_q_reg[8]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[6] ),
        .O(\slot_period_q[31]_i_131_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_132 
       (.I0(\slot_period_q_reg[8]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[5] ),
        .I2(\slot_period_q_reg[4]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[4] ),
        .O(\slot_period_q[31]_i_132_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_133 
       (.I0(\slot_period_q_reg[4]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[3] ),
        .I2(\slot_period_q_reg[4]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[2] ),
        .O(\slot_period_q[31]_i_133_n_0 ));
  LUT4 #(
    .INIT(16'h222B)) 
    \slot_period_q[31]_i_134 
       (.I0(\slot_period_q_reg[4]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[1] ),
        .I2(\partial_age_q_reg_n_0_[0] ),
        .I3(\high1_q_reg_n_0_[0] ),
        .O(\slot_period_q[31]_i_134_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_135 
       (.I0(\high1_q_reg_n_0_[7] ),
        .I1(\slot_period_q_reg[8]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[6] ),
        .I3(\slot_period_q_reg[8]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_135_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_136 
       (.I0(\high1_q_reg_n_0_[5] ),
        .I1(\slot_period_q_reg[8]_i_2_n_7 ),
        .I2(\high1_q_reg_n_0_[4] ),
        .I3(\slot_period_q_reg[4]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_136_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_137 
       (.I0(\high1_q_reg_n_0_[3] ),
        .I1(\slot_period_q_reg[4]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[2] ),
        .I3(\slot_period_q_reg[4]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_137_n_0 ));
  LUT4 #(
    .INIT(16'h6006)) 
    \slot_period_q[31]_i_138 
       (.I0(\high1_q_reg_n_0_[0] ),
        .I1(\partial_age_q_reg_n_0_[0] ),
        .I2(\high1_q_reg_n_0_[1] ),
        .I3(\slot_period_q_reg[4]_i_2_n_7 ),
        .O(\slot_period_q[31]_i_138_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_139 
       (.I0(\slot_period_q_reg[8]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[7] ),
        .I2(\slot_period_q_reg[8]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[6] ),
        .O(\slot_period_q[31]_i_139_n_0 ));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    \slot_period_q[31]_i_14 
       (.I0(\partial_age_q_reg_n_0_[31] ),
        .I1(\partial_age_q_reg_n_0_[29] ),
        .I2(\partial_age_q_reg_n_0_[27] ),
        .I3(\partial_age_q_reg_n_0_[24] ),
        .I4(\slot_period_q[31]_i_24_n_0 ),
        .O(\slot_period_q[31]_i_14_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_140 
       (.I0(\slot_period_q_reg[8]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[5] ),
        .I2(\slot_period_q_reg[4]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[4] ),
        .O(\slot_period_q[31]_i_140_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_141 
       (.I0(\slot_period_q_reg[4]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[3] ),
        .I2(\slot_period_q_reg[4]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[2] ),
        .O(\slot_period_q[31]_i_141_n_0 ));
  LUT4 #(
    .INIT(16'h222B)) 
    \slot_period_q[31]_i_142 
       (.I0(\slot_period_q_reg[4]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[1] ),
        .I2(\partial_age_q_reg_n_0_[0] ),
        .I3(\high0_q_reg_n_0_[0] ),
        .O(\slot_period_q[31]_i_142_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_143 
       (.I0(\high0_q_reg_n_0_[7] ),
        .I1(\slot_period_q_reg[8]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[6] ),
        .I3(\slot_period_q_reg[8]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_143_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_144 
       (.I0(\high0_q_reg_n_0_[5] ),
        .I1(\slot_period_q_reg[8]_i_2_n_7 ),
        .I2(\high0_q_reg_n_0_[4] ),
        .I3(\slot_period_q_reg[4]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_144_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_145 
       (.I0(\high0_q_reg_n_0_[3] ),
        .I1(\slot_period_q_reg[4]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[2] ),
        .I3(\slot_period_q_reg[4]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_145_n_0 ));
  LUT4 #(
    .INIT(16'h6006)) 
    \slot_period_q[31]_i_146 
       (.I0(\high0_q_reg_n_0_[0] ),
        .I1(\partial_age_q_reg_n_0_[0] ),
        .I2(\high0_q_reg_n_0_[1] ),
        .I3(\slot_period_q_reg[4]_i_2_n_7 ),
        .O(\slot_period_q[31]_i_146_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_147 
       (.I0(\slot_period_q_reg[8]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[7] ),
        .I2(\slot_period_q_reg[8]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[6] ),
        .O(\slot_period_q[31]_i_147_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_148 
       (.I0(\slot_period_q_reg[8]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[5] ),
        .I2(\slot_period_q_reg[4]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[4] ),
        .O(\slot_period_q[31]_i_148_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_149 
       (.I0(\slot_period_q_reg[4]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[3] ),
        .I2(\slot_period_q_reg[4]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[2] ),
        .O(\slot_period_q[31]_i_149_n_0 ));
  LUT5 #(
    .INIT(32'h00008000)) 
    \slot_period_q[31]_i_15 
       (.I0(\partial_age_q_reg_n_0_[6] ),
        .I1(\partial_age_q_reg_n_0_[5] ),
        .I2(\partial_age_q_reg_n_0_[0] ),
        .I3(\partial_age_q_reg_n_0_[3] ),
        .I4(\slot_period_q[31]_i_25_n_0 ),
        .O(\slot_period_q[31]_i_15_n_0 ));
  LUT4 #(
    .INIT(16'h222B)) 
    \slot_period_q[31]_i_150 
       (.I0(\slot_period_q_reg[4]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[1] ),
        .I2(\partial_age_q_reg_n_0_[0] ),
        .I3(\high2_q_reg_n_0_[0] ),
        .O(\slot_period_q[31]_i_150_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_151 
       (.I0(\high2_q_reg_n_0_[7] ),
        .I1(\slot_period_q_reg[8]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[6] ),
        .I3(\slot_period_q_reg[8]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_151_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_152 
       (.I0(\high2_q_reg_n_0_[5] ),
        .I1(\slot_period_q_reg[8]_i_2_n_7 ),
        .I2(\high2_q_reg_n_0_[4] ),
        .I3(\slot_period_q_reg[4]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_152_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_153 
       (.I0(\high2_q_reg_n_0_[3] ),
        .I1(\slot_period_q_reg[4]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[2] ),
        .I3(\slot_period_q_reg[4]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_153_n_0 ));
  LUT4 #(
    .INIT(16'h6006)) 
    \slot_period_q[31]_i_154 
       (.I0(\high2_q_reg_n_0_[0] ),
        .I1(\partial_age_q_reg_n_0_[0] ),
        .I2(\high2_q_reg_n_0_[1] ),
        .I3(\slot_period_q_reg[4]_i_2_n_7 ),
        .O(\slot_period_q[31]_i_154_n_0 ));
  LUT5 #(
    .INIT(32'hFFFF7FFF)) 
    \slot_period_q[31]_i_16 
       (.I0(\partial_age_q_reg_n_0_[30] ),
        .I1(\partial_age_q_reg_n_0_[28] ),
        .I2(\partial_age_q_reg_n_0_[26] ),
        .I3(\partial_age_q_reg_n_0_[25] ),
        .I4(\slot_period_q[31]_i_26_n_0 ),
        .O(\slot_period_q[31]_i_16_n_0 ));
  LUT6 #(
    .INIT(64'h7FFFFFFFFFFFFFFF)) 
    \slot_period_q[31]_i_17 
       (.I0(incoherent_event_q4),
        .I1(incoherent_event_q6),
        .I2(\fall_seen_q_reg_n_0_[0] ),
        .I3(incoherent_event_q2),
        .I4(\fall_seen_q_reg_n_0_[1] ),
        .I5(p_0_in),
        .O(\slot_period_q[31]_i_17_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \slot_period_q[31]_i_18 
       (.I0(\slot_period_q[31]_i_30_n_0 ),
        .I1(\high1_q_reg_n_0_[27] ),
        .I2(\high1_q_reg_n_0_[24] ),
        .I3(\high1_q_reg_n_0_[26] ),
        .I4(\high1_q_reg_n_0_[25] ),
        .I5(\slot_period_q[31]_i_31_n_0 ),
        .O(\slot_period_q[31]_i_18_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \slot_period_q[31]_i_19 
       (.I0(\slot_period_q[31]_i_32_n_0 ),
        .I1(\high1_q_reg_n_0_[15] ),
        .I2(\high1_q_reg_n_0_[12] ),
        .I3(\high1_q_reg_n_0_[14] ),
        .I4(\high1_q_reg_n_0_[13] ),
        .I5(\slot_period_q[31]_i_33_n_0 ),
        .O(\slot_period_q[31]_i_19_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[31]_i_2 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[31]_i_11_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[31]_i_2_n_0 ));
  LUT4 #(
    .INIT(16'h0004)) 
    \slot_period_q[31]_i_20 
       (.I0(\slot_period_q[31]_i_34_n_0 ),
        .I1(\slot_period_q[31]_i_35_n_0 ),
        .I2(\slot_period_q[31]_i_36_n_0 ),
        .I3(\slot_period_q[31]_i_37_n_0 ),
        .O(\slot_period_q[31]_i_20_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \slot_period_q[31]_i_21 
       (.I0(\slot_period_q[31]_i_38_n_0 ),
        .I1(\high2_q_reg_n_0_[22] ),
        .I2(\high2_q_reg_n_0_[21] ),
        .I3(\high2_q_reg_n_0_[23] ),
        .I4(\high2_q_reg_n_0_[20] ),
        .I5(\slot_period_q[31]_i_39_n_0 ),
        .O(\slot_period_q[31]_i_21_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \slot_period_q[31]_i_22 
       (.I0(\slot_period_q[31]_i_40_n_0 ),
        .I1(\high2_q_reg_n_0_[11] ),
        .I2(\high2_q_reg_n_0_[8] ),
        .I3(\high2_q_reg_n_0_[10] ),
        .I4(\high2_q_reg_n_0_[9] ),
        .I5(\slot_period_q[31]_i_41_n_0 ),
        .O(\slot_period_q[31]_i_22_n_0 ));
  LUT4 #(
    .INIT(16'h7FFF)) 
    \slot_period_q[31]_i_23 
       (.I0(\partial_age_q_reg_n_0_[8] ),
        .I1(\partial_age_q_reg_n_0_[11] ),
        .I2(\partial_age_q_reg_n_0_[13] ),
        .I3(\partial_age_q_reg_n_0_[14] ),
        .O(\slot_period_q[31]_i_23_n_0 ));
  LUT4 #(
    .INIT(16'h7FFF)) 
    \slot_period_q[31]_i_24 
       (.I0(\partial_age_q_reg_n_0_[21] ),
        .I1(\partial_age_q_reg_n_0_[22] ),
        .I2(\partial_age_q_reg_n_0_[16] ),
        .I3(\partial_age_q_reg_n_0_[19] ),
        .O(\slot_period_q[31]_i_24_n_0 ));
  LUT4 #(
    .INIT(16'h7FFF)) 
    \slot_period_q[31]_i_25 
       (.I0(\partial_age_q_reg_n_0_[9] ),
        .I1(\partial_age_q_reg_n_0_[10] ),
        .I2(\partial_age_q_reg_n_0_[12] ),
        .I3(\partial_age_q_reg_n_0_[15] ),
        .O(\slot_period_q[31]_i_25_n_0 ));
  LUT4 #(
    .INIT(16'h7FFF)) 
    \slot_period_q[31]_i_26 
       (.I0(\partial_age_q_reg_n_0_[20] ),
        .I1(\partial_age_q_reg_n_0_[23] ),
        .I2(\partial_age_q_reg_n_0_[17] ),
        .I3(\partial_age_q_reg_n_0_[18] ),
        .O(\slot_period_q[31]_i_26_n_0 ));
  LUT3 #(
    .INIT(8'h80)) 
    \slot_period_q[31]_i_3 
       (.I0(out_valid_INST_0_i_1_n_0),
        .I1(out_valid_INST_0_i_2_n_0),
        .I2(out_ready),
        .O(capture_out_ready));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_30 
       (.I0(\high1_q_reg_n_0_[29] ),
        .I1(\high1_q_reg_n_0_[28] ),
        .I2(\high1_q_reg_n_0_[31] ),
        .I3(\high1_q_reg_n_0_[30] ),
        .O(\slot_period_q[31]_i_30_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_31 
       (.I0(\high1_q_reg_n_0_[20] ),
        .I1(\high1_q_reg_n_0_[23] ),
        .I2(\high1_q_reg_n_0_[21] ),
        .I3(\high1_q_reg_n_0_[22] ),
        .I4(\slot_period_q[31]_i_69_n_0 ),
        .O(\slot_period_q[31]_i_31_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_32 
       (.I0(\high1_q_reg_n_0_[11] ),
        .I1(\high1_q_reg_n_0_[8] ),
        .I2(\high1_q_reg_n_0_[10] ),
        .I3(\high1_q_reg_n_0_[9] ),
        .O(\slot_period_q[31]_i_32_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_33 
       (.I0(\high1_q_reg_n_0_[1] ),
        .I1(\high1_q_reg_n_0_[2] ),
        .I2(\high1_q_reg_n_0_[0] ),
        .I3(\high1_q_reg_n_0_[3] ),
        .I4(\slot_period_q[31]_i_70_n_0 ),
        .O(\slot_period_q[31]_i_33_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_34 
       (.I0(\high0_q_reg_n_0_[13] ),
        .I1(\high0_q_reg_n_0_[14] ),
        .I2(\high0_q_reg_n_0_[5] ),
        .I3(\high0_q_reg_n_0_[6] ),
        .I4(\slot_period_q[31]_i_71_n_0 ),
        .O(\slot_period_q[31]_i_34_n_0 ));
  LUT5 #(
    .INIT(32'h00000001)) 
    \slot_period_q[31]_i_35 
       (.I0(\high0_q_reg_n_0_[29] ),
        .I1(\high0_q_reg_n_0_[30] ),
        .I2(\high0_q_reg_n_0_[28] ),
        .I3(\high0_q_reg_n_0_[31] ),
        .I4(\slot_period_q[31]_i_72_n_0 ),
        .O(\slot_period_q[31]_i_35_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_36 
       (.I0(\high0_q_reg_n_0_[25] ),
        .I1(\high0_q_reg_n_0_[26] ),
        .I2(\high0_q_reg_n_0_[24] ),
        .I3(\high0_q_reg_n_0_[27] ),
        .I4(\slot_period_q[31]_i_73_n_0 ),
        .O(\slot_period_q[31]_i_36_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_37 
       (.I0(\high0_q_reg_n_0_[4] ),
        .I1(\high0_q_reg_n_0_[7] ),
        .I2(\high0_q_reg_n_0_[0] ),
        .I3(\high0_q_reg_n_0_[3] ),
        .I4(\slot_period_q[31]_i_74_n_0 ),
        .O(\slot_period_q[31]_i_37_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_38 
       (.I0(\high2_q_reg_n_0_[27] ),
        .I1(\high2_q_reg_n_0_[24] ),
        .I2(\high2_q_reg_n_0_[31] ),
        .I3(\high2_q_reg_n_0_[28] ),
        .O(\slot_period_q[31]_i_38_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_39 
       (.I0(\high2_q_reg_n_0_[13] ),
        .I1(\high2_q_reg_n_0_[14] ),
        .I2(\high2_q_reg_n_0_[12] ),
        .I3(\high2_q_reg_n_0_[15] ),
        .I4(\slot_period_q[31]_i_75_n_0 ),
        .O(\slot_period_q[31]_i_39_n_0 ));
  LUT2 #(
    .INIT(4'h7)) 
    \slot_period_q[31]_i_4 
       (.I0(partial_valid_q_reg_n_0),
        .I1(armed_q_i_2_n_0),
        .O(\slot_period_q[31]_i_4_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_40 
       (.I0(\high2_q_reg_n_0_[2] ),
        .I1(\high2_q_reg_n_0_[1] ),
        .I2(\high2_q_reg_n_0_[6] ),
        .I3(\high2_q_reg_n_0_[5] ),
        .O(\slot_period_q[31]_i_40_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \slot_period_q[31]_i_41 
       (.I0(\high2_q_reg_n_0_[17] ),
        .I1(\high2_q_reg_n_0_[18] ),
        .I2(\high2_q_reg_n_0_[16] ),
        .I3(\high2_q_reg_n_0_[19] ),
        .I4(\slot_period_q[31]_i_76_n_0 ),
        .O(\slot_period_q[31]_i_41_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_43 
       (.I0(\slot_period_q_reg[31]_i_11_n_5 ),
        .I1(\high1_q_reg_n_0_[31] ),
        .I2(\slot_period_q_reg[31]_i_11_n_6 ),
        .I3(\high1_q_reg_n_0_[30] ),
        .O(\slot_period_q[31]_i_43_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_44 
       (.I0(\slot_period_q_reg[31]_i_11_n_7 ),
        .I1(\high1_q_reg_n_0_[29] ),
        .I2(\slot_period_q_reg[28]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[28] ),
        .O(\slot_period_q[31]_i_44_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_45 
       (.I0(\slot_period_q_reg[28]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[27] ),
        .I2(\slot_period_q_reg[28]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[26] ),
        .O(\slot_period_q[31]_i_45_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_46 
       (.I0(\slot_period_q_reg[28]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[25] ),
        .I2(\slot_period_q_reg[24]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[24] ),
        .O(\slot_period_q[31]_i_46_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_47 
       (.I0(\high1_q_reg_n_0_[31] ),
        .I1(\slot_period_q_reg[31]_i_11_n_5 ),
        .I2(\high1_q_reg_n_0_[30] ),
        .I3(\slot_period_q_reg[31]_i_11_n_6 ),
        .O(\slot_period_q[31]_i_47_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_48 
       (.I0(\high1_q_reg_n_0_[29] ),
        .I1(\slot_period_q_reg[31]_i_11_n_7 ),
        .I2(\high1_q_reg_n_0_[28] ),
        .I3(\slot_period_q_reg[28]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_48_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_49 
       (.I0(\high1_q_reg_n_0_[27] ),
        .I1(\slot_period_q_reg[28]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[26] ),
        .I3(\slot_period_q_reg[28]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_49_n_0 ));
  LUT5 #(
    .INIT(32'h0010FFFF)) 
    \slot_period_q[31]_i_5 
       (.I0(\slot_period_q[31]_i_13_n_0 ),
        .I1(\slot_period_q[31]_i_14_n_0 ),
        .I2(\slot_period_q[31]_i_15_n_0 ),
        .I3(\slot_period_q[31]_i_16_n_0 ),
        .I4(armed_q_reg_0),
        .O(\slot_period_q[31]_i_5_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_50 
       (.I0(\high1_q_reg_n_0_[25] ),
        .I1(\slot_period_q_reg[28]_i_2_n_7 ),
        .I2(\high1_q_reg_n_0_[24] ),
        .I3(\slot_period_q_reg[24]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_50_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_52 
       (.I0(\slot_period_q_reg[31]_i_11_n_5 ),
        .I1(\high0_q_reg_n_0_[31] ),
        .I2(\slot_period_q_reg[31]_i_11_n_6 ),
        .I3(\high0_q_reg_n_0_[30] ),
        .O(\slot_period_q[31]_i_52_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_53 
       (.I0(\slot_period_q_reg[31]_i_11_n_7 ),
        .I1(\high0_q_reg_n_0_[29] ),
        .I2(\slot_period_q_reg[28]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[28] ),
        .O(\slot_period_q[31]_i_53_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_54 
       (.I0(\slot_period_q_reg[28]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[27] ),
        .I2(\slot_period_q_reg[28]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[26] ),
        .O(\slot_period_q[31]_i_54_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_55 
       (.I0(\slot_period_q_reg[28]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[25] ),
        .I2(\slot_period_q_reg[24]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[24] ),
        .O(\slot_period_q[31]_i_55_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_56 
       (.I0(\high0_q_reg_n_0_[31] ),
        .I1(\slot_period_q_reg[31]_i_11_n_5 ),
        .I2(\high0_q_reg_n_0_[30] ),
        .I3(\slot_period_q_reg[31]_i_11_n_6 ),
        .O(\slot_period_q[31]_i_56_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_57 
       (.I0(\high0_q_reg_n_0_[29] ),
        .I1(\slot_period_q_reg[31]_i_11_n_7 ),
        .I2(\high0_q_reg_n_0_[28] ),
        .I3(\slot_period_q_reg[28]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_57_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_58 
       (.I0(\high0_q_reg_n_0_[27] ),
        .I1(\slot_period_q_reg[28]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[26] ),
        .I3(\slot_period_q_reg[28]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_58_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_59 
       (.I0(\high0_q_reg_n_0_[25] ),
        .I1(\slot_period_q_reg[28]_i_2_n_7 ),
        .I2(\high0_q_reg_n_0_[24] ),
        .I3(\slot_period_q_reg[24]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_59_n_0 ));
  LUT6 #(
    .INIT(64'hD0DD0000D0DDD0DD)) 
    \slot_period_q[31]_i_6 
       (.I0(sample_levels[1]),
        .I1(\previous_q_reg_n_0_[1] ),
        .I2(\previous_q_reg_n_0_[0] ),
        .I3(sample_levels[0]),
        .I4(\previous_q_reg_n_0_[2] ),
        .I5(sample_levels[2]),
        .O(\slot_period_q[31]_i_6_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_61 
       (.I0(\slot_period_q_reg[31]_i_11_n_5 ),
        .I1(\high2_q_reg_n_0_[31] ),
        .I2(\slot_period_q_reg[31]_i_11_n_6 ),
        .I3(\high2_q_reg_n_0_[30] ),
        .O(\slot_period_q[31]_i_61_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_62 
       (.I0(\slot_period_q_reg[31]_i_11_n_7 ),
        .I1(\high2_q_reg_n_0_[29] ),
        .I2(\slot_period_q_reg[28]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[28] ),
        .O(\slot_period_q[31]_i_62_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_63 
       (.I0(\slot_period_q_reg[28]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[27] ),
        .I2(\slot_period_q_reg[28]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[26] ),
        .O(\slot_period_q[31]_i_63_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_64 
       (.I0(\slot_period_q_reg[28]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[25] ),
        .I2(\slot_period_q_reg[24]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[24] ),
        .O(\slot_period_q[31]_i_64_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_65 
       (.I0(\high2_q_reg_n_0_[31] ),
        .I1(\slot_period_q_reg[31]_i_11_n_5 ),
        .I2(\high2_q_reg_n_0_[30] ),
        .I3(\slot_period_q_reg[31]_i_11_n_6 ),
        .O(\slot_period_q[31]_i_65_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_66 
       (.I0(\high2_q_reg_n_0_[29] ),
        .I1(\slot_period_q_reg[31]_i_11_n_7 ),
        .I2(\high2_q_reg_n_0_[28] ),
        .I3(\slot_period_q_reg[28]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_66_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_67 
       (.I0(\high2_q_reg_n_0_[27] ),
        .I1(\slot_period_q_reg[28]_i_2_n_5 ),
        .I2(\high2_q_reg_n_0_[26] ),
        .I3(\slot_period_q_reg[28]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_67_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_68 
       (.I0(\high2_q_reg_n_0_[25] ),
        .I1(\slot_period_q_reg[28]_i_2_n_7 ),
        .I2(\high2_q_reg_n_0_[24] ),
        .I3(\slot_period_q_reg[24]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_68_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_69 
       (.I0(\high1_q_reg_n_0_[19] ),
        .I1(\high1_q_reg_n_0_[16] ),
        .I2(\high1_q_reg_n_0_[18] ),
        .I3(\high1_q_reg_n_0_[17] ),
        .O(\slot_period_q[31]_i_69_n_0 ));
  LUT2 #(
    .INIT(4'h2)) 
    \slot_period_q[31]_i_7 
       (.I0(\partial_age_q[31]_i_3_n_0 ),
        .I1(\slot_period_q[31]_i_9_n_0 ),
        .O(\slot_period_q[31]_i_7_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_70 
       (.I0(\high1_q_reg_n_0_[5] ),
        .I1(\high1_q_reg_n_0_[4] ),
        .I2(\high1_q_reg_n_0_[7] ),
        .I3(\high1_q_reg_n_0_[6] ),
        .O(\slot_period_q[31]_i_70_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_71 
       (.I0(\high0_q_reg_n_0_[19] ),
        .I1(\high0_q_reg_n_0_[16] ),
        .I2(\high0_q_reg_n_0_[23] ),
        .I3(\high0_q_reg_n_0_[20] ),
        .O(\slot_period_q[31]_i_71_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_72 
       (.I0(\high0_q_reg_n_0_[2] ),
        .I1(\high0_q_reg_n_0_[1] ),
        .I2(\high0_q_reg_n_0_[15] ),
        .I3(\high0_q_reg_n_0_[12] ),
        .O(\slot_period_q[31]_i_72_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_73 
       (.I0(\high0_q_reg_n_0_[11] ),
        .I1(\high0_q_reg_n_0_[8] ),
        .I2(\high0_q_reg_n_0_[10] ),
        .I3(\high0_q_reg_n_0_[9] ),
        .O(\slot_period_q[31]_i_73_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_74 
       (.I0(\high0_q_reg_n_0_[18] ),
        .I1(\high0_q_reg_n_0_[17] ),
        .I2(\high0_q_reg_n_0_[22] ),
        .I3(\high0_q_reg_n_0_[21] ),
        .O(\slot_period_q[31]_i_74_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_75 
       (.I0(\high2_q_reg_n_0_[3] ),
        .I1(\high2_q_reg_n_0_[0] ),
        .I2(\high2_q_reg_n_0_[7] ),
        .I3(\high2_q_reg_n_0_[4] ),
        .O(\slot_period_q[31]_i_75_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \slot_period_q[31]_i_76 
       (.I0(\high2_q_reg_n_0_[26] ),
        .I1(\high2_q_reg_n_0_[25] ),
        .I2(\high2_q_reg_n_0_[30] ),
        .I3(\high2_q_reg_n_0_[29] ),
        .O(\slot_period_q[31]_i_76_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_78 
       (.I0(\slot_period_q_reg[24]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[23] ),
        .I2(\slot_period_q_reg[24]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[22] ),
        .O(\slot_period_q[31]_i_78_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_79 
       (.I0(\slot_period_q_reg[24]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[21] ),
        .I2(\slot_period_q_reg[20]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[20] ),
        .O(\slot_period_q[31]_i_79_n_0 ));
  LUT3 #(
    .INIT(8'h80)) 
    \slot_period_q[31]_i_8 
       (.I0(out_valid_INST_0_i_1_n_0),
        .I1(out_valid_INST_0_i_2_n_0),
        .I2(out_ready),
        .O(\slot_period_q[31]_i_8_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_80 
       (.I0(\slot_period_q_reg[20]_i_2_n_5 ),
        .I1(\high1_q_reg_n_0_[19] ),
        .I2(\slot_period_q_reg[20]_i_2_n_6 ),
        .I3(\high1_q_reg_n_0_[18] ),
        .O(\slot_period_q[31]_i_80_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_81 
       (.I0(\slot_period_q_reg[20]_i_2_n_7 ),
        .I1(\high1_q_reg_n_0_[17] ),
        .I2(\slot_period_q_reg[16]_i_2_n_4 ),
        .I3(\high1_q_reg_n_0_[16] ),
        .O(\slot_period_q[31]_i_81_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_82 
       (.I0(\high1_q_reg_n_0_[23] ),
        .I1(\slot_period_q_reg[24]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[22] ),
        .I3(\slot_period_q_reg[24]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_82_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_83 
       (.I0(\high1_q_reg_n_0_[21] ),
        .I1(\slot_period_q_reg[24]_i_2_n_7 ),
        .I2(\high1_q_reg_n_0_[20] ),
        .I3(\slot_period_q_reg[20]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_83_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_84 
       (.I0(\high1_q_reg_n_0_[19] ),
        .I1(\slot_period_q_reg[20]_i_2_n_5 ),
        .I2(\high1_q_reg_n_0_[18] ),
        .I3(\slot_period_q_reg[20]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_84_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_85 
       (.I0(\high1_q_reg_n_0_[17] ),
        .I1(\slot_period_q_reg[20]_i_2_n_7 ),
        .I2(\high1_q_reg_n_0_[16] ),
        .I3(\slot_period_q_reg[16]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_85_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_87 
       (.I0(\slot_period_q_reg[24]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[23] ),
        .I2(\slot_period_q_reg[24]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[22] ),
        .O(\slot_period_q[31]_i_87_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_88 
       (.I0(\slot_period_q_reg[24]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[21] ),
        .I2(\slot_period_q_reg[20]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[20] ),
        .O(\slot_period_q[31]_i_88_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_89 
       (.I0(\slot_period_q_reg[20]_i_2_n_5 ),
        .I1(\high0_q_reg_n_0_[19] ),
        .I2(\slot_period_q_reg[20]_i_2_n_6 ),
        .I3(\high0_q_reg_n_0_[18] ),
        .O(\slot_period_q[31]_i_89_n_0 ));
  LUT6 #(
    .INIT(64'hFFAEFFAEFFFFFFAE)) 
    \slot_period_q[31]_i_9 
       (.I0(\slot_period_q[31]_i_17_n_0 ),
        .I1(\slot_period_q[31]_i_18_n_0 ),
        .I2(\slot_period_q[31]_i_19_n_0 ),
        .I3(\slot_period_q[31]_i_20_n_0 ),
        .I4(\slot_period_q[31]_i_21_n_0 ),
        .I5(\slot_period_q[31]_i_22_n_0 ),
        .O(\slot_period_q[31]_i_9_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_90 
       (.I0(\slot_period_q_reg[20]_i_2_n_7 ),
        .I1(\high0_q_reg_n_0_[17] ),
        .I2(\slot_period_q_reg[16]_i_2_n_4 ),
        .I3(\high0_q_reg_n_0_[16] ),
        .O(\slot_period_q[31]_i_90_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_91 
       (.I0(\high0_q_reg_n_0_[23] ),
        .I1(\slot_period_q_reg[24]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[22] ),
        .I3(\slot_period_q_reg[24]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_91_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_92 
       (.I0(\high0_q_reg_n_0_[21] ),
        .I1(\slot_period_q_reg[24]_i_2_n_7 ),
        .I2(\high0_q_reg_n_0_[20] ),
        .I3(\slot_period_q_reg[20]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_92_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_93 
       (.I0(\high0_q_reg_n_0_[19] ),
        .I1(\slot_period_q_reg[20]_i_2_n_5 ),
        .I2(\high0_q_reg_n_0_[18] ),
        .I3(\slot_period_q_reg[20]_i_2_n_6 ),
        .O(\slot_period_q[31]_i_93_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \slot_period_q[31]_i_94 
       (.I0(\high0_q_reg_n_0_[17] ),
        .I1(\slot_period_q_reg[20]_i_2_n_7 ),
        .I2(\high0_q_reg_n_0_[16] ),
        .I3(\slot_period_q_reg[16]_i_2_n_4 ),
        .O(\slot_period_q[31]_i_94_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_96 
       (.I0(\slot_period_q_reg[24]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[23] ),
        .I2(\slot_period_q_reg[24]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[22] ),
        .O(\slot_period_q[31]_i_96_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_97 
       (.I0(\slot_period_q_reg[24]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[21] ),
        .I2(\slot_period_q_reg[20]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[20] ),
        .O(\slot_period_q[31]_i_97_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_98 
       (.I0(\slot_period_q_reg[20]_i_2_n_5 ),
        .I1(\high2_q_reg_n_0_[19] ),
        .I2(\slot_period_q_reg[20]_i_2_n_6 ),
        .I3(\high2_q_reg_n_0_[18] ),
        .O(\slot_period_q[31]_i_98_n_0 ));
  LUT4 #(
    .INIT(16'h22B2)) 
    \slot_period_q[31]_i_99 
       (.I0(\slot_period_q_reg[20]_i_2_n_7 ),
        .I1(\high2_q_reg_n_0_[17] ),
        .I2(\slot_period_q_reg[16]_i_2_n_4 ),
        .I3(\high2_q_reg_n_0_[16] ),
        .O(\slot_period_q[31]_i_99_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[3]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[4]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[4]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[4]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[5]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[8]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[6]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[8]_i_2_n_6 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[7]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[8]_i_2_n_5 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[8]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[8]_i_2_n_4 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h00000000000D0000)) 
    \slot_period_q[9]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_9_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q_reg[12]_i_2_n_7 ),
        .I5(\slot_period_q[31]_i_12_n_0 ),
        .O(\slot_period_q[9]_i_1_n_0 ));
  FDRE \slot_period_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[0]_i_1_n_0 ),
        .Q(out_period[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[10]_i_1_n_0 ),
        .Q(out_period[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[11]_i_1_n_0 ),
        .Q(out_period[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[12]_i_1_n_0 ),
        .Q(out_period[12]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[12]_i_2 
       (.CI(\slot_period_q_reg[8]_i_2_n_0 ),
        .CO({\slot_period_q_reg[12]_i_2_n_0 ,\slot_period_q_reg[12]_i_2_n_1 ,\slot_period_q_reg[12]_i_2_n_2 ,\slot_period_q_reg[12]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[12]_i_2_n_4 ,\slot_period_q_reg[12]_i_2_n_5 ,\slot_period_q_reg[12]_i_2_n_6 ,\slot_period_q_reg[12]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[12] ,\partial_age_q_reg_n_0_[11] ,\partial_age_q_reg_n_0_[10] ,\partial_age_q_reg_n_0_[9] }));
  FDRE \slot_period_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[13]_i_1_n_0 ),
        .Q(out_period[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[14]_i_1_n_0 ),
        .Q(out_period[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[15]_i_1_n_0 ),
        .Q(out_period[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[16]_i_1_n_0 ),
        .Q(out_period[16]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[16]_i_2 
       (.CI(\slot_period_q_reg[12]_i_2_n_0 ),
        .CO({\slot_period_q_reg[16]_i_2_n_0 ,\slot_period_q_reg[16]_i_2_n_1 ,\slot_period_q_reg[16]_i_2_n_2 ,\slot_period_q_reg[16]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[16]_i_2_n_4 ,\slot_period_q_reg[16]_i_2_n_5 ,\slot_period_q_reg[16]_i_2_n_6 ,\slot_period_q_reg[16]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[16] ,\partial_age_q_reg_n_0_[15] ,\partial_age_q_reg_n_0_[14] ,\partial_age_q_reg_n_0_[13] }));
  FDRE \slot_period_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[17]_i_1_n_0 ),
        .Q(out_period[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[18]_i_1_n_0 ),
        .Q(out_period[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[19]_i_1_n_0 ),
        .Q(out_period[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[1]_i_1_n_0 ),
        .Q(out_period[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[20]_i_1_n_0 ),
        .Q(out_period[20]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[20]_i_2 
       (.CI(\slot_period_q_reg[16]_i_2_n_0 ),
        .CO({\slot_period_q_reg[20]_i_2_n_0 ,\slot_period_q_reg[20]_i_2_n_1 ,\slot_period_q_reg[20]_i_2_n_2 ,\slot_period_q_reg[20]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[20]_i_2_n_4 ,\slot_period_q_reg[20]_i_2_n_5 ,\slot_period_q_reg[20]_i_2_n_6 ,\slot_period_q_reg[20]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[20] ,\partial_age_q_reg_n_0_[19] ,\partial_age_q_reg_n_0_[18] ,\partial_age_q_reg_n_0_[17] }));
  FDRE \slot_period_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[21]_i_1_n_0 ),
        .Q(out_period[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[22]_i_1_n_0 ),
        .Q(out_period[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[23]_i_1_n_0 ),
        .Q(out_period[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[24]_i_1_n_0 ),
        .Q(out_period[24]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[24]_i_2 
       (.CI(\slot_period_q_reg[20]_i_2_n_0 ),
        .CO({\slot_period_q_reg[24]_i_2_n_0 ,\slot_period_q_reg[24]_i_2_n_1 ,\slot_period_q_reg[24]_i_2_n_2 ,\slot_period_q_reg[24]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[24]_i_2_n_4 ,\slot_period_q_reg[24]_i_2_n_5 ,\slot_period_q_reg[24]_i_2_n_6 ,\slot_period_q_reg[24]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[24] ,\partial_age_q_reg_n_0_[23] ,\partial_age_q_reg_n_0_[22] ,\partial_age_q_reg_n_0_[21] }));
  FDRE \slot_period_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[25]_i_1_n_0 ),
        .Q(out_period[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[26]_i_1_n_0 ),
        .Q(out_period[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[27]_i_1_n_0 ),
        .Q(out_period[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[28]_i_1_n_0 ),
        .Q(out_period[28]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[28]_i_2 
       (.CI(\slot_period_q_reg[24]_i_2_n_0 ),
        .CO({\slot_period_q_reg[28]_i_2_n_0 ,\slot_period_q_reg[28]_i_2_n_1 ,\slot_period_q_reg[28]_i_2_n_2 ,\slot_period_q_reg[28]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[28]_i_2_n_4 ,\slot_period_q_reg[28]_i_2_n_5 ,\slot_period_q_reg[28]_i_2_n_6 ,\slot_period_q_reg[28]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[28] ,\partial_age_q_reg_n_0_[27] ,\partial_age_q_reg_n_0_[26] ,\partial_age_q_reg_n_0_[25] }));
  FDRE \slot_period_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[29]_i_1_n_0 ),
        .Q(out_period[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[2]_i_1_n_0 ),
        .Q(out_period[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[30]_i_1_n_0 ),
        .Q(out_period[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[31]_i_2_n_0 ),
        .Q(out_period[31]),
        .R(\high2_q_reg[31]_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_104 
       (.CI(1'b0),
        .CO({\slot_period_q_reg[31]_i_104_n_0 ,\slot_period_q_reg[31]_i_104_n_1 ,\slot_period_q_reg[31]_i_104_n_2 ,\slot_period_q_reg[31]_i_104_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_131_n_0 ,\slot_period_q[31]_i_132_n_0 ,\slot_period_q[31]_i_133_n_0 ,\slot_period_q[31]_i_134_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_104_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_135_n_0 ,\slot_period_q[31]_i_136_n_0 ,\slot_period_q[31]_i_137_n_0 ,\slot_period_q[31]_i_138_n_0 }));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[31]_i_11 
       (.CI(\slot_period_q_reg[28]_i_2_n_0 ),
        .CO({\NLW_slot_period_q_reg[31]_i_11_CO_UNCONNECTED [3:2],\slot_period_q_reg[31]_i_11_n_2 ,\slot_period_q_reg[31]_i_11_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_slot_period_q_reg[31]_i_11_O_UNCONNECTED [3],\slot_period_q_reg[31]_i_11_n_5 ,\slot_period_q_reg[31]_i_11_n_6 ,\slot_period_q_reg[31]_i_11_n_7 }),
        .S({1'b0,\partial_age_q_reg_n_0_[31] ,\partial_age_q_reg_n_0_[30] ,\partial_age_q_reg_n_0_[29] }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_113 
       (.CI(1'b0),
        .CO({\slot_period_q_reg[31]_i_113_n_0 ,\slot_period_q_reg[31]_i_113_n_1 ,\slot_period_q_reg[31]_i_113_n_2 ,\slot_period_q_reg[31]_i_113_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_139_n_0 ,\slot_period_q[31]_i_140_n_0 ,\slot_period_q[31]_i_141_n_0 ,\slot_period_q[31]_i_142_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_113_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_143_n_0 ,\slot_period_q[31]_i_144_n_0 ,\slot_period_q[31]_i_145_n_0 ,\slot_period_q[31]_i_146_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_122 
       (.CI(1'b0),
        .CO({\slot_period_q_reg[31]_i_122_n_0 ,\slot_period_q_reg[31]_i_122_n_1 ,\slot_period_q_reg[31]_i_122_n_2 ,\slot_period_q_reg[31]_i_122_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_147_n_0 ,\slot_period_q[31]_i_148_n_0 ,\slot_period_q[31]_i_149_n_0 ,\slot_period_q[31]_i_150_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_122_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_151_n_0 ,\slot_period_q[31]_i_152_n_0 ,\slot_period_q[31]_i_153_n_0 ,\slot_period_q[31]_i_154_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_27 
       (.CI(\slot_period_q_reg[31]_i_42_n_0 ),
        .CO({incoherent_event_q4,\slot_period_q_reg[31]_i_27_n_1 ,\slot_period_q_reg[31]_i_27_n_2 ,\slot_period_q_reg[31]_i_27_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_43_n_0 ,\slot_period_q[31]_i_44_n_0 ,\slot_period_q[31]_i_45_n_0 ,\slot_period_q[31]_i_46_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_27_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_47_n_0 ,\slot_period_q[31]_i_48_n_0 ,\slot_period_q[31]_i_49_n_0 ,\slot_period_q[31]_i_50_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_28 
       (.CI(\slot_period_q_reg[31]_i_51_n_0 ),
        .CO({incoherent_event_q6,\slot_period_q_reg[31]_i_28_n_1 ,\slot_period_q_reg[31]_i_28_n_2 ,\slot_period_q_reg[31]_i_28_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_52_n_0 ,\slot_period_q[31]_i_53_n_0 ,\slot_period_q[31]_i_54_n_0 ,\slot_period_q[31]_i_55_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_28_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_56_n_0 ,\slot_period_q[31]_i_57_n_0 ,\slot_period_q[31]_i_58_n_0 ,\slot_period_q[31]_i_59_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_29 
       (.CI(\slot_period_q_reg[31]_i_60_n_0 ),
        .CO({incoherent_event_q2,\slot_period_q_reg[31]_i_29_n_1 ,\slot_period_q_reg[31]_i_29_n_2 ,\slot_period_q_reg[31]_i_29_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_61_n_0 ,\slot_period_q[31]_i_62_n_0 ,\slot_period_q[31]_i_63_n_0 ,\slot_period_q[31]_i_64_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_29_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_65_n_0 ,\slot_period_q[31]_i_66_n_0 ,\slot_period_q[31]_i_67_n_0 ,\slot_period_q[31]_i_68_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_42 
       (.CI(\slot_period_q_reg[31]_i_77_n_0 ),
        .CO({\slot_period_q_reg[31]_i_42_n_0 ,\slot_period_q_reg[31]_i_42_n_1 ,\slot_period_q_reg[31]_i_42_n_2 ,\slot_period_q_reg[31]_i_42_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_78_n_0 ,\slot_period_q[31]_i_79_n_0 ,\slot_period_q[31]_i_80_n_0 ,\slot_period_q[31]_i_81_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_42_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_82_n_0 ,\slot_period_q[31]_i_83_n_0 ,\slot_period_q[31]_i_84_n_0 ,\slot_period_q[31]_i_85_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_51 
       (.CI(\slot_period_q_reg[31]_i_86_n_0 ),
        .CO({\slot_period_q_reg[31]_i_51_n_0 ,\slot_period_q_reg[31]_i_51_n_1 ,\slot_period_q_reg[31]_i_51_n_2 ,\slot_period_q_reg[31]_i_51_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_87_n_0 ,\slot_period_q[31]_i_88_n_0 ,\slot_period_q[31]_i_89_n_0 ,\slot_period_q[31]_i_90_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_51_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_91_n_0 ,\slot_period_q[31]_i_92_n_0 ,\slot_period_q[31]_i_93_n_0 ,\slot_period_q[31]_i_94_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_60 
       (.CI(\slot_period_q_reg[31]_i_95_n_0 ),
        .CO({\slot_period_q_reg[31]_i_60_n_0 ,\slot_period_q_reg[31]_i_60_n_1 ,\slot_period_q_reg[31]_i_60_n_2 ,\slot_period_q_reg[31]_i_60_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_96_n_0 ,\slot_period_q[31]_i_97_n_0 ,\slot_period_q[31]_i_98_n_0 ,\slot_period_q[31]_i_99_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_60_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_100_n_0 ,\slot_period_q[31]_i_101_n_0 ,\slot_period_q[31]_i_102_n_0 ,\slot_period_q[31]_i_103_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_77 
       (.CI(\slot_period_q_reg[31]_i_104_n_0 ),
        .CO({\slot_period_q_reg[31]_i_77_n_0 ,\slot_period_q_reg[31]_i_77_n_1 ,\slot_period_q_reg[31]_i_77_n_2 ,\slot_period_q_reg[31]_i_77_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_105_n_0 ,\slot_period_q[31]_i_106_n_0 ,\slot_period_q[31]_i_107_n_0 ,\slot_period_q[31]_i_108_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_77_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_109_n_0 ,\slot_period_q[31]_i_110_n_0 ,\slot_period_q[31]_i_111_n_0 ,\slot_period_q[31]_i_112_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_86 
       (.CI(\slot_period_q_reg[31]_i_113_n_0 ),
        .CO({\slot_period_q_reg[31]_i_86_n_0 ,\slot_period_q_reg[31]_i_86_n_1 ,\slot_period_q_reg[31]_i_86_n_2 ,\slot_period_q_reg[31]_i_86_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_114_n_0 ,\slot_period_q[31]_i_115_n_0 ,\slot_period_q[31]_i_116_n_0 ,\slot_period_q[31]_i_117_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_86_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_118_n_0 ,\slot_period_q[31]_i_119_n_0 ,\slot_period_q[31]_i_120_n_0 ,\slot_period_q[31]_i_121_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \slot_period_q_reg[31]_i_95 
       (.CI(\slot_period_q_reg[31]_i_122_n_0 ),
        .CO({\slot_period_q_reg[31]_i_95_n_0 ,\slot_period_q_reg[31]_i_95_n_1 ,\slot_period_q_reg[31]_i_95_n_2 ,\slot_period_q_reg[31]_i_95_n_3 }),
        .CYINIT(1'b0),
        .DI({\slot_period_q[31]_i_123_n_0 ,\slot_period_q[31]_i_124_n_0 ,\slot_period_q[31]_i_125_n_0 ,\slot_period_q[31]_i_126_n_0 }),
        .O(\NLW_slot_period_q_reg[31]_i_95_O_UNCONNECTED [3:0]),
        .S({\slot_period_q[31]_i_127_n_0 ,\slot_period_q[31]_i_128_n_0 ,\slot_period_q[31]_i_129_n_0 ,\slot_period_q[31]_i_130_n_0 }));
  FDRE \slot_period_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[3]_i_1_n_0 ),
        .Q(out_period[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[4]_i_1_n_0 ),
        .Q(out_period[4]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[4]_i_2 
       (.CI(1'b0),
        .CO({\slot_period_q_reg[4]_i_2_n_0 ,\slot_period_q_reg[4]_i_2_n_1 ,\slot_period_q_reg[4]_i_2_n_2 ,\slot_period_q_reg[4]_i_2_n_3 }),
        .CYINIT(\partial_age_q_reg_n_0_[0] ),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[4]_i_2_n_4 ,\slot_period_q_reg[4]_i_2_n_5 ,\slot_period_q_reg[4]_i_2_n_6 ,\slot_period_q_reg[4]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[4] ,\partial_age_q_reg_n_0_[3] ,\partial_age_q_reg_n_0_[2] ,\partial_age_q_reg_n_0_[1] }));
  FDRE \slot_period_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[5]_i_1_n_0 ),
        .Q(out_period[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[6]_i_1_n_0 ),
        .Q(out_period[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[7]_i_1_n_0 ),
        .Q(out_period[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_period_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[8]_i_1_n_0 ),
        .Q(out_period[8]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \slot_period_q_reg[8]_i_2 
       (.CI(\slot_period_q_reg[4]_i_2_n_0 ),
        .CO({\slot_period_q_reg[8]_i_2_n_0 ,\slot_period_q_reg[8]_i_2_n_1 ,\slot_period_q_reg[8]_i_2_n_2 ,\slot_period_q_reg[8]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\slot_period_q_reg[8]_i_2_n_4 ,\slot_period_q_reg[8]_i_2_n_5 ,\slot_period_q_reg[8]_i_2_n_6 ,\slot_period_q_reg[8]_i_2_n_7 }),
        .S({\partial_age_q_reg_n_0_[8] ,\partial_age_q_reg_n_0_[7] ,\partial_age_q_reg_n_0_[6] ,\partial_age_q_reg_n_0_[5] }));
  FDRE \slot_period_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_period_q[9]_i_1_n_0 ),
        .Q(out_period[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[0]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[0] ),
        .O(\slot_start_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[10]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[10] ),
        .O(\slot_start_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[11]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[11] ),
        .O(\slot_start_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[12]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[12] ),
        .O(\slot_start_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[13]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[13] ),
        .O(\slot_start_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[14]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[14] ),
        .O(\slot_start_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[15]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[15] ),
        .O(\slot_start_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[16]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[16] ),
        .O(\slot_start_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[17]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[17] ),
        .O(\slot_start_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[18]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[18] ),
        .O(\slot_start_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[19]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[19] ),
        .O(\slot_start_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[1]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[1] ),
        .O(\slot_start_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[20]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[20] ),
        .O(\slot_start_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[21]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[21] ),
        .O(\slot_start_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[22]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[22] ),
        .O(\slot_start_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[23]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[23] ),
        .O(\slot_start_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[24]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[24] ),
        .O(\slot_start_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[25]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[25] ),
        .O(\slot_start_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[26]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[26] ),
        .O(\slot_start_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[27]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[27] ),
        .O(\slot_start_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[28]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[28] ),
        .O(\slot_start_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[29]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[29] ),
        .O(\slot_start_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[2]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[2] ),
        .O(\slot_start_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[30]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[30] ),
        .O(\slot_start_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[31]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[31] ),
        .O(\slot_start_q[31]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[32]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[32] ),
        .O(\slot_start_q[32]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[33]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[33] ),
        .O(\slot_start_q[33]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[34]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[34] ),
        .O(\slot_start_q[34]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[35]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[35] ),
        .O(\slot_start_q[35]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[36]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[36] ),
        .O(\slot_start_q[36]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[37]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[37] ),
        .O(\slot_start_q[37]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[38]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[38] ),
        .O(\slot_start_q[38]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[39]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[39] ),
        .O(\slot_start_q[39]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[3]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[3] ),
        .O(\slot_start_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[40]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[40] ),
        .O(\slot_start_q[40]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[41]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[41] ),
        .O(\slot_start_q[41]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[42]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[42] ),
        .O(\slot_start_q[42]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[43]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[43] ),
        .O(\slot_start_q[43]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[44]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[44] ),
        .O(\slot_start_q[44]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[45]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[45] ),
        .O(\slot_start_q[45]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[46]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[46] ),
        .O(\slot_start_q[46]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[47]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[47] ),
        .O(\slot_start_q[47]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[48]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[48] ),
        .O(\slot_start_q[48]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[49]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[49] ),
        .O(\slot_start_q[49]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[4]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[4] ),
        .O(\slot_start_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[50]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[50] ),
        .O(\slot_start_q[50]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[51]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[51] ),
        .O(\slot_start_q[51]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[52]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[52] ),
        .O(\slot_start_q[52]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[53]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[53] ),
        .O(\slot_start_q[53]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[54]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[54] ),
        .O(\slot_start_q[54]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[55]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[55] ),
        .O(\slot_start_q[55]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[56]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[56] ),
        .O(\slot_start_q[56]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[57]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[57] ),
        .O(\slot_start_q[57]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[58]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[58] ),
        .O(\slot_start_q[58]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[59]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[59] ),
        .O(\slot_start_q[59]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[5]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[5] ),
        .O(\slot_start_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[60]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[60] ),
        .O(\slot_start_q[60]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[61]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[61] ),
        .O(\slot_start_q[61]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[62]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[62] ),
        .O(\slot_start_q[62]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[63]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[63] ),
        .O(\slot_start_q[63]_i_1_n_0 ));
  LUT2 #(
    .INIT(4'hB)) 
    \slot_start_q[63]_i_2 
       (.I0(\slot_period_q[31]_i_5_n_0 ),
        .I1(\partial_age_q[31]_i_3_n_0 ),
        .O(\slot_start_q[63]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'hFFAEFFAEFFFFFFAE)) 
    \slot_start_q[63]_i_3 
       (.I0(\slot_period_q[31]_i_17_n_0 ),
        .I1(\slot_period_q[31]_i_18_n_0 ),
        .I2(\slot_period_q[31]_i_19_n_0 ),
        .I3(\slot_period_q[31]_i_20_n_0 ),
        .I4(\slot_period_q[31]_i_21_n_0 ),
        .I5(\slot_period_q[31]_i_22_n_0 ),
        .O(\slot_start_q[63]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[6]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[6] ),
        .O(\slot_start_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[7]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[7] ),
        .O(\slot_start_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[8]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[8] ),
        .O(\slot_start_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_start_q[9]_i_1 
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(\slot_start_q[63]_i_2_n_0 ),
        .I3(\slot_period_q[31]_i_4_n_0 ),
        .I4(\slot_start_q[63]_i_3_n_0 ),
        .I5(\partial_start_q_reg_n_0_[9] ),
        .O(\slot_start_q[9]_i_1_n_0 ));
  FDRE \slot_start_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[0]_i_1_n_0 ),
        .Q(out_start[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[10]_i_1_n_0 ),
        .Q(out_start[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[11]_i_1_n_0 ),
        .Q(out_start[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[12]_i_1_n_0 ),
        .Q(out_start[12]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[13]_i_1_n_0 ),
        .Q(out_start[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[14]_i_1_n_0 ),
        .Q(out_start[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[15]_i_1_n_0 ),
        .Q(out_start[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[16]_i_1_n_0 ),
        .Q(out_start[16]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[17]_i_1_n_0 ),
        .Q(out_start[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[18]_i_1_n_0 ),
        .Q(out_start[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[19]_i_1_n_0 ),
        .Q(out_start[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[1]_i_1_n_0 ),
        .Q(out_start[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[20]_i_1_n_0 ),
        .Q(out_start[20]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[21]_i_1_n_0 ),
        .Q(out_start[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[22]_i_1_n_0 ),
        .Q(out_start[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[23]_i_1_n_0 ),
        .Q(out_start[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[24]_i_1_n_0 ),
        .Q(out_start[24]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[25]_i_1_n_0 ),
        .Q(out_start[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[26]_i_1_n_0 ),
        .Q(out_start[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[27]_i_1_n_0 ),
        .Q(out_start[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[28]_i_1_n_0 ),
        .Q(out_start[28]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[29]_i_1_n_0 ),
        .Q(out_start[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[2]_i_1_n_0 ),
        .Q(out_start[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[30]_i_1_n_0 ),
        .Q(out_start[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[31]_i_1_n_0 ),
        .Q(out_start[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[32] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[32]_i_1_n_0 ),
        .Q(out_start[32]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[33] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[33]_i_1_n_0 ),
        .Q(out_start[33]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[34] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[34]_i_1_n_0 ),
        .Q(out_start[34]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[35] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[35]_i_1_n_0 ),
        .Q(out_start[35]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[36] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[36]_i_1_n_0 ),
        .Q(out_start[36]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[37] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[37]_i_1_n_0 ),
        .Q(out_start[37]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[38] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[38]_i_1_n_0 ),
        .Q(out_start[38]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[39] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[39]_i_1_n_0 ),
        .Q(out_start[39]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[3]_i_1_n_0 ),
        .Q(out_start[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[40] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[40]_i_1_n_0 ),
        .Q(out_start[40]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[41] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[41]_i_1_n_0 ),
        .Q(out_start[41]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[42] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[42]_i_1_n_0 ),
        .Q(out_start[42]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[43] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[43]_i_1_n_0 ),
        .Q(out_start[43]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[44] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[44]_i_1_n_0 ),
        .Q(out_start[44]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[45] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[45]_i_1_n_0 ),
        .Q(out_start[45]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[46] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[46]_i_1_n_0 ),
        .Q(out_start[46]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[47] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[47]_i_1_n_0 ),
        .Q(out_start[47]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[48] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[48]_i_1_n_0 ),
        .Q(out_start[48]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[49] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[49]_i_1_n_0 ),
        .Q(out_start[49]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[4]_i_1_n_0 ),
        .Q(out_start[4]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[50] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[50]_i_1_n_0 ),
        .Q(out_start[50]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[51] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[51]_i_1_n_0 ),
        .Q(out_start[51]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[52] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[52]_i_1_n_0 ),
        .Q(out_start[52]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[53] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[53]_i_1_n_0 ),
        .Q(out_start[53]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[54] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[54]_i_1_n_0 ),
        .Q(out_start[54]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[55] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[55]_i_1_n_0 ),
        .Q(out_start[55]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[56] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[56]_i_1_n_0 ),
        .Q(out_start[56]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[57] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[57]_i_1_n_0 ),
        .Q(out_start[57]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[58] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[58]_i_1_n_0 ),
        .Q(out_start[58]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[59] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[59]_i_1_n_0 ),
        .Q(out_start[59]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[5]_i_1_n_0 ),
        .Q(out_start[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[60] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[60]_i_1_n_0 ),
        .Q(out_start[60]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[61] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[61]_i_1_n_0 ),
        .Q(out_start[61]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[62] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[62]_i_1_n_0 ),
        .Q(out_start[62]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[63] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[63]_i_1_n_0 ),
        .Q(out_start[63]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[6]_i_1_n_0 ),
        .Q(out_start[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[7]_i_1_n_0 ),
        .Q(out_start[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[8]_i_1_n_0 ),
        .Q(out_start[8]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_start_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_start_q[9]_i_1_n_0 ),
        .Q(out_start[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[0]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[0]),
        .O(\slot_tag_q[0]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[10]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[10]),
        .O(\slot_tag_q[10]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[11]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[11]),
        .O(\slot_tag_q[11]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[12]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[12]),
        .O(\slot_tag_q[12]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[13]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[13]),
        .O(\slot_tag_q[13]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[14]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[14]),
        .O(\slot_tag_q[14]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[15]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[15]),
        .O(\slot_tag_q[15]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[16]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[16]),
        .O(\slot_tag_q[16]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[17]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[17]),
        .O(\slot_tag_q[17]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[18]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[18]),
        .O(\slot_tag_q[18]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[19]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[19]),
        .O(\slot_tag_q[19]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[1]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[1]),
        .O(\slot_tag_q[1]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[20]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[20]),
        .O(\slot_tag_q[20]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[21]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[21]),
        .O(\slot_tag_q[21]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[22]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[22]),
        .O(\slot_tag_q[22]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[23]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[23]),
        .O(\slot_tag_q[23]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[24]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[24]),
        .O(\slot_tag_q[24]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[25]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[25]),
        .O(\slot_tag_q[25]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[26]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[26]),
        .O(\slot_tag_q[26]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[27]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[27]),
        .O(\slot_tag_q[27]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[28]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[28]),
        .O(\slot_tag_q[28]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[29]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[29]),
        .O(\slot_tag_q[29]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[2]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[2]),
        .O(\slot_tag_q[2]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[30]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[30]),
        .O(\slot_tag_q[30]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[31]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[31]),
        .O(\slot_tag_q[31]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[3]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[3]),
        .O(\slot_tag_q[3]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[4]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[4]),
        .O(\slot_tag_q[4]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[5]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[5]),
        .O(\slot_tag_q[5]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[6]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[6]),
        .O(\slot_tag_q[6]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[7]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[7]),
        .O(\slot_tag_q[7]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[8]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[8]),
        .O(\slot_tag_q[8]_i_1_n_0 ));
  LUT6 #(
    .INIT(64'h0000000D00000000)) 
    \slot_tag_q[9]_i_1 
       (.I0(slot_valid_q_reg_rep_n_0),
        .I1(\slot_period_q[31]_i_8_n_0 ),
        .I2(\slot_period_q[31]_i_12_n_0 ),
        .I3(\slot_period_q[31]_i_10_n_0 ),
        .I4(\slot_period_q[31]_i_9_n_0 ),
        .I5(window_tag_q[9]),
        .O(\slot_tag_q[9]_i_1_n_0 ));
  FDRE \slot_tag_q_reg[0] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[0]_i_1_n_0 ),
        .Q(out_tag[0]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[10] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[10]_i_1_n_0 ),
        .Q(out_tag[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[11] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[11]_i_1_n_0 ),
        .Q(out_tag[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[12] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[12]_i_1_n_0 ),
        .Q(out_tag[12]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[13] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[13]_i_1_n_0 ),
        .Q(out_tag[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[14] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[14]_i_1_n_0 ),
        .Q(out_tag[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[15] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[15]_i_1_n_0 ),
        .Q(out_tag[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[16] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[16]_i_1_n_0 ),
        .Q(out_tag[16]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[17] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[17]_i_1_n_0 ),
        .Q(out_tag[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[18] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[18]_i_1_n_0 ),
        .Q(out_tag[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[19] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[19]_i_1_n_0 ),
        .Q(out_tag[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[1] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[1]_i_1_n_0 ),
        .Q(out_tag[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[20] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[20]_i_1_n_0 ),
        .Q(out_tag[20]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[21] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[21]_i_1_n_0 ),
        .Q(out_tag[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[22] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[22]_i_1_n_0 ),
        .Q(out_tag[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[23] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[23]_i_1_n_0 ),
        .Q(out_tag[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[24] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[24]_i_1_n_0 ),
        .Q(out_tag[24]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[25] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[25]_i_1_n_0 ),
        .Q(out_tag[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[26] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[26]_i_1_n_0 ),
        .Q(out_tag[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[27] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[27]_i_1_n_0 ),
        .Q(out_tag[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[28] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[28]_i_1_n_0 ),
        .Q(out_tag[28]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[29] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[29]_i_1_n_0 ),
        .Q(out_tag[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[2] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[2]_i_1_n_0 ),
        .Q(out_tag[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[30] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[30]_i_1_n_0 ),
        .Q(out_tag[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[31] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[31]_i_1_n_0 ),
        .Q(out_tag[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[3] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[3]_i_1_n_0 ),
        .Q(out_tag[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[4] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[4]_i_1_n_0 ),
        .Q(out_tag[4]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[5] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[5]_i_1_n_0 ),
        .Q(out_tag[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[6] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[6]_i_1_n_0 ),
        .Q(out_tag[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[7] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[7]_i_1_n_0 ),
        .Q(out_tag[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[8] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[8]_i_1_n_0 ),
        .Q(out_tag[8]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \slot_tag_q_reg[9] 
       (.C(clk),
        .CE(\slot_period_q[31]_i_1_n_0 ),
        .D(\slot_tag_q[9]_i_1_n_0 ),
        .Q(out_tag[9]),
        .R(\high2_q_reg[31]_0 ));
  LUT5 #(
    .INIT(32'h0D0D0DAA)) 
    slot_valid_q_i_1
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(overrun_event_q_i_2_n_0),
        .I3(\slot_period_q[31]_i_1_n_0 ),
        .I4(\high2_q_reg[31]_0 ),
        .O(slot_valid_q_i_1_n_0));
  (* ORIG_CELL_NAME = "slot_valid_q_reg" *) 
  FDRE slot_valid_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(slot_valid_q_i_1_n_0),
        .Q(slot_valid_q_reg_n_0),
        .R(1'b0));
  (* ORIG_CELL_NAME = "slot_valid_q_reg" *) 
  FDRE slot_valid_q_reg_rep
       (.C(clk),
        .CE(1'b1),
        .D(slot_valid_q_rep_i_1_n_0),
        .Q(slot_valid_q_reg_rep_n_0),
        .R(1'b0));
  LUT5 #(
    .INIT(32'h0D0D0DAA)) 
    slot_valid_q_rep_i_1
       (.I0(slot_valid_q_reg_n_0),
        .I1(capture_out_ready),
        .I2(overrun_event_q_i_2_n_0),
        .I3(\slot_period_q[31]_i_1_n_0 ),
        .I4(\high2_q_reg[31]_0 ),
        .O(slot_valid_q_rep_i_1_n_0));
  LUT2 #(
    .INIT(4'h8)) 
    \tick_q[0]_i_1 
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .O(\tick_q[0]_i_1_n_0 ));
  LUT1 #(
    .INIT(2'h1)) 
    \tick_q[0]_i_3 
       (.I0(tick_q_reg[0]),
        .O(\tick_q[0]_i_3_n_0 ));
  FDRE \tick_q_reg[0] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[0]_i_2_n_7 ),
        .Q(tick_q_reg[0]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[0]_i_2 
       (.CI(1'b0),
        .CO({\tick_q_reg[0]_i_2_n_0 ,\tick_q_reg[0]_i_2_n_1 ,\tick_q_reg[0]_i_2_n_2 ,\tick_q_reg[0]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b1}),
        .O({\tick_q_reg[0]_i_2_n_4 ,\tick_q_reg[0]_i_2_n_5 ,\tick_q_reg[0]_i_2_n_6 ,\tick_q_reg[0]_i_2_n_7 }),
        .S({tick_q_reg[3:1],\tick_q[0]_i_3_n_0 }));
  FDRE \tick_q_reg[10] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[8]_i_1_n_5 ),
        .Q(tick_q_reg[10]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[11] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[8]_i_1_n_4 ),
        .Q(tick_q_reg[11]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[12] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[12]_i_1_n_7 ),
        .Q(tick_q_reg[12]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[12]_i_1 
       (.CI(\tick_q_reg[8]_i_1_n_0 ),
        .CO({\tick_q_reg[12]_i_1_n_0 ,\tick_q_reg[12]_i_1_n_1 ,\tick_q_reg[12]_i_1_n_2 ,\tick_q_reg[12]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[12]_i_1_n_4 ,\tick_q_reg[12]_i_1_n_5 ,\tick_q_reg[12]_i_1_n_6 ,\tick_q_reg[12]_i_1_n_7 }),
        .S(tick_q_reg[15:12]));
  FDRE \tick_q_reg[13] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[12]_i_1_n_6 ),
        .Q(tick_q_reg[13]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[14] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[12]_i_1_n_5 ),
        .Q(tick_q_reg[14]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[15] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[12]_i_1_n_4 ),
        .Q(tick_q_reg[15]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[16] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[16]_i_1_n_7 ),
        .Q(tick_q_reg[16]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[16]_i_1 
       (.CI(\tick_q_reg[12]_i_1_n_0 ),
        .CO({\tick_q_reg[16]_i_1_n_0 ,\tick_q_reg[16]_i_1_n_1 ,\tick_q_reg[16]_i_1_n_2 ,\tick_q_reg[16]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[16]_i_1_n_4 ,\tick_q_reg[16]_i_1_n_5 ,\tick_q_reg[16]_i_1_n_6 ,\tick_q_reg[16]_i_1_n_7 }),
        .S(tick_q_reg[19:16]));
  FDRE \tick_q_reg[17] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[16]_i_1_n_6 ),
        .Q(tick_q_reg[17]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[18] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[16]_i_1_n_5 ),
        .Q(tick_q_reg[18]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[19] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[16]_i_1_n_4 ),
        .Q(tick_q_reg[19]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[1] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[0]_i_2_n_6 ),
        .Q(tick_q_reg[1]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[20] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[20]_i_1_n_7 ),
        .Q(tick_q_reg[20]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[20]_i_1 
       (.CI(\tick_q_reg[16]_i_1_n_0 ),
        .CO({\tick_q_reg[20]_i_1_n_0 ,\tick_q_reg[20]_i_1_n_1 ,\tick_q_reg[20]_i_1_n_2 ,\tick_q_reg[20]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[20]_i_1_n_4 ,\tick_q_reg[20]_i_1_n_5 ,\tick_q_reg[20]_i_1_n_6 ,\tick_q_reg[20]_i_1_n_7 }),
        .S(tick_q_reg[23:20]));
  FDRE \tick_q_reg[21] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[20]_i_1_n_6 ),
        .Q(tick_q_reg[21]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[22] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[20]_i_1_n_5 ),
        .Q(tick_q_reg[22]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[23] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[20]_i_1_n_4 ),
        .Q(tick_q_reg[23]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[24] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[24]_i_1_n_7 ),
        .Q(tick_q_reg[24]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[24]_i_1 
       (.CI(\tick_q_reg[20]_i_1_n_0 ),
        .CO({\tick_q_reg[24]_i_1_n_0 ,\tick_q_reg[24]_i_1_n_1 ,\tick_q_reg[24]_i_1_n_2 ,\tick_q_reg[24]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[24]_i_1_n_4 ,\tick_q_reg[24]_i_1_n_5 ,\tick_q_reg[24]_i_1_n_6 ,\tick_q_reg[24]_i_1_n_7 }),
        .S(tick_q_reg[27:24]));
  FDRE \tick_q_reg[25] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[24]_i_1_n_6 ),
        .Q(tick_q_reg[25]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[26] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[24]_i_1_n_5 ),
        .Q(tick_q_reg[26]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[27] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[24]_i_1_n_4 ),
        .Q(tick_q_reg[27]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[28] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[28]_i_1_n_7 ),
        .Q(tick_q_reg[28]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[28]_i_1 
       (.CI(\tick_q_reg[24]_i_1_n_0 ),
        .CO({\tick_q_reg[28]_i_1_n_0 ,\tick_q_reg[28]_i_1_n_1 ,\tick_q_reg[28]_i_1_n_2 ,\tick_q_reg[28]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[28]_i_1_n_4 ,\tick_q_reg[28]_i_1_n_5 ,\tick_q_reg[28]_i_1_n_6 ,\tick_q_reg[28]_i_1_n_7 }),
        .S(tick_q_reg[31:28]));
  FDRE \tick_q_reg[29] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[28]_i_1_n_6 ),
        .Q(tick_q_reg[29]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[2] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[0]_i_2_n_5 ),
        .Q(tick_q_reg[2]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[30] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[28]_i_1_n_5 ),
        .Q(tick_q_reg[30]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[31] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[28]_i_1_n_4 ),
        .Q(tick_q_reg[31]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[32] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[32]_i_1_n_7 ),
        .Q(tick_q_reg[32]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[32]_i_1 
       (.CI(\tick_q_reg[28]_i_1_n_0 ),
        .CO({\tick_q_reg[32]_i_1_n_0 ,\tick_q_reg[32]_i_1_n_1 ,\tick_q_reg[32]_i_1_n_2 ,\tick_q_reg[32]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[32]_i_1_n_4 ,\tick_q_reg[32]_i_1_n_5 ,\tick_q_reg[32]_i_1_n_6 ,\tick_q_reg[32]_i_1_n_7 }),
        .S(tick_q_reg[35:32]));
  FDRE \tick_q_reg[33] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[32]_i_1_n_6 ),
        .Q(tick_q_reg[33]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[34] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[32]_i_1_n_5 ),
        .Q(tick_q_reg[34]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[35] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[32]_i_1_n_4 ),
        .Q(tick_q_reg[35]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[36] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[36]_i_1_n_7 ),
        .Q(tick_q_reg[36]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[36]_i_1 
       (.CI(\tick_q_reg[32]_i_1_n_0 ),
        .CO({\tick_q_reg[36]_i_1_n_0 ,\tick_q_reg[36]_i_1_n_1 ,\tick_q_reg[36]_i_1_n_2 ,\tick_q_reg[36]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[36]_i_1_n_4 ,\tick_q_reg[36]_i_1_n_5 ,\tick_q_reg[36]_i_1_n_6 ,\tick_q_reg[36]_i_1_n_7 }),
        .S(tick_q_reg[39:36]));
  FDRE \tick_q_reg[37] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[36]_i_1_n_6 ),
        .Q(tick_q_reg[37]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[38] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[36]_i_1_n_5 ),
        .Q(tick_q_reg[38]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[39] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[36]_i_1_n_4 ),
        .Q(tick_q_reg[39]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[3] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[0]_i_2_n_4 ),
        .Q(tick_q_reg[3]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[40] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[40]_i_1_n_7 ),
        .Q(tick_q_reg[40]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[40]_i_1 
       (.CI(\tick_q_reg[36]_i_1_n_0 ),
        .CO({\tick_q_reg[40]_i_1_n_0 ,\tick_q_reg[40]_i_1_n_1 ,\tick_q_reg[40]_i_1_n_2 ,\tick_q_reg[40]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[40]_i_1_n_4 ,\tick_q_reg[40]_i_1_n_5 ,\tick_q_reg[40]_i_1_n_6 ,\tick_q_reg[40]_i_1_n_7 }),
        .S(tick_q_reg[43:40]));
  FDRE \tick_q_reg[41] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[40]_i_1_n_6 ),
        .Q(tick_q_reg[41]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[42] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[40]_i_1_n_5 ),
        .Q(tick_q_reg[42]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[43] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[40]_i_1_n_4 ),
        .Q(tick_q_reg[43]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[44] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[44]_i_1_n_7 ),
        .Q(tick_q_reg[44]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[44]_i_1 
       (.CI(\tick_q_reg[40]_i_1_n_0 ),
        .CO({\tick_q_reg[44]_i_1_n_0 ,\tick_q_reg[44]_i_1_n_1 ,\tick_q_reg[44]_i_1_n_2 ,\tick_q_reg[44]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[44]_i_1_n_4 ,\tick_q_reg[44]_i_1_n_5 ,\tick_q_reg[44]_i_1_n_6 ,\tick_q_reg[44]_i_1_n_7 }),
        .S(tick_q_reg[47:44]));
  FDRE \tick_q_reg[45] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[44]_i_1_n_6 ),
        .Q(tick_q_reg[45]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[46] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[44]_i_1_n_5 ),
        .Q(tick_q_reg[46]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[47] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[44]_i_1_n_4 ),
        .Q(tick_q_reg[47]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[48] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[48]_i_1_n_7 ),
        .Q(tick_q_reg[48]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[48]_i_1 
       (.CI(\tick_q_reg[44]_i_1_n_0 ),
        .CO({\tick_q_reg[48]_i_1_n_0 ,\tick_q_reg[48]_i_1_n_1 ,\tick_q_reg[48]_i_1_n_2 ,\tick_q_reg[48]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[48]_i_1_n_4 ,\tick_q_reg[48]_i_1_n_5 ,\tick_q_reg[48]_i_1_n_6 ,\tick_q_reg[48]_i_1_n_7 }),
        .S(tick_q_reg[51:48]));
  FDRE \tick_q_reg[49] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[48]_i_1_n_6 ),
        .Q(tick_q_reg[49]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[4] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[4]_i_1_n_7 ),
        .Q(tick_q_reg[4]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[4]_i_1 
       (.CI(\tick_q_reg[0]_i_2_n_0 ),
        .CO({\tick_q_reg[4]_i_1_n_0 ,\tick_q_reg[4]_i_1_n_1 ,\tick_q_reg[4]_i_1_n_2 ,\tick_q_reg[4]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[4]_i_1_n_4 ,\tick_q_reg[4]_i_1_n_5 ,\tick_q_reg[4]_i_1_n_6 ,\tick_q_reg[4]_i_1_n_7 }),
        .S(tick_q_reg[7:4]));
  FDRE \tick_q_reg[50] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[48]_i_1_n_5 ),
        .Q(tick_q_reg[50]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[51] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[48]_i_1_n_4 ),
        .Q(tick_q_reg[51]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[52] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[52]_i_1_n_7 ),
        .Q(tick_q_reg[52]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[52]_i_1 
       (.CI(\tick_q_reg[48]_i_1_n_0 ),
        .CO({\tick_q_reg[52]_i_1_n_0 ,\tick_q_reg[52]_i_1_n_1 ,\tick_q_reg[52]_i_1_n_2 ,\tick_q_reg[52]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[52]_i_1_n_4 ,\tick_q_reg[52]_i_1_n_5 ,\tick_q_reg[52]_i_1_n_6 ,\tick_q_reg[52]_i_1_n_7 }),
        .S(tick_q_reg[55:52]));
  FDRE \tick_q_reg[53] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[52]_i_1_n_6 ),
        .Q(tick_q_reg[53]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[54] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[52]_i_1_n_5 ),
        .Q(tick_q_reg[54]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[55] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[52]_i_1_n_4 ),
        .Q(tick_q_reg[55]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[56] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[56]_i_1_n_7 ),
        .Q(tick_q_reg[56]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[56]_i_1 
       (.CI(\tick_q_reg[52]_i_1_n_0 ),
        .CO({\tick_q_reg[56]_i_1_n_0 ,\tick_q_reg[56]_i_1_n_1 ,\tick_q_reg[56]_i_1_n_2 ,\tick_q_reg[56]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[56]_i_1_n_4 ,\tick_q_reg[56]_i_1_n_5 ,\tick_q_reg[56]_i_1_n_6 ,\tick_q_reg[56]_i_1_n_7 }),
        .S(tick_q_reg[59:56]));
  FDRE \tick_q_reg[57] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[56]_i_1_n_6 ),
        .Q(tick_q_reg[57]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[58] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[56]_i_1_n_5 ),
        .Q(tick_q_reg[58]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[59] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[56]_i_1_n_4 ),
        .Q(tick_q_reg[59]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[5] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[4]_i_1_n_6 ),
        .Q(tick_q_reg[5]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[60] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[60]_i_1_n_7 ),
        .Q(tick_q_reg[60]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[60]_i_1 
       (.CI(\tick_q_reg[56]_i_1_n_0 ),
        .CO({\NLW_tick_q_reg[60]_i_1_CO_UNCONNECTED [3],\tick_q_reg[60]_i_1_n_1 ,\tick_q_reg[60]_i_1_n_2 ,\tick_q_reg[60]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[60]_i_1_n_4 ,\tick_q_reg[60]_i_1_n_5 ,\tick_q_reg[60]_i_1_n_6 ,\tick_q_reg[60]_i_1_n_7 }),
        .S(tick_q_reg[63:60]));
  FDRE \tick_q_reg[61] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[60]_i_1_n_6 ),
        .Q(tick_q_reg[61]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[62] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[60]_i_1_n_5 ),
        .Q(tick_q_reg[62]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[63] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[60]_i_1_n_4 ),
        .Q(tick_q_reg[63]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[6] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[4]_i_1_n_5 ),
        .Q(tick_q_reg[6]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[7] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[4]_i_1_n_4 ),
        .Q(tick_q_reg[7]),
        .R(\high2_q_reg[31]_0 ));
  FDRE \tick_q_reg[8] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[8]_i_1_n_7 ),
        .Q(tick_q_reg[8]),
        .R(\high2_q_reg[31]_0 ));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \tick_q_reg[8]_i_1 
       (.CI(\tick_q_reg[4]_i_1_n_0 ),
        .CO({\tick_q_reg[8]_i_1_n_0 ,\tick_q_reg[8]_i_1_n_1 ,\tick_q_reg[8]_i_1_n_2 ,\tick_q_reg[8]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\tick_q_reg[8]_i_1_n_4 ,\tick_q_reg[8]_i_1_n_5 ,\tick_q_reg[8]_i_1_n_6 ,\tick_q_reg[8]_i_1_n_7 }),
        .S(tick_q_reg[11:8]));
  FDRE \tick_q_reg[9] 
       (.C(clk),
        .CE(\tick_q[0]_i_1_n_0 ),
        .D(\tick_q_reg[8]_i_1_n_6 ),
        .Q(tick_q_reg[9]),
        .R(\high2_q_reg[31]_0 ));
  (* SOFT_HLUTNM = "soft_lutpair7" *) 
  LUT2 #(
    .INIT(4'hE)) 
    window_active_q_i_11
       (.I0(incoherent_event_q_reg_0),
        .I1(period_overflow_event_q_reg_0),
        .O(window_active_q_i_11_n_0));
  (* SOFT_HLUTNM = "soft_lutpair6" *) 
  LUT4 #(
    .INIT(16'hFFEF)) 
    window_active_q_i_2
       (.I0(overrun_event_q_reg_1),
        .I1(window_active_q_reg),
        .I2(\failure_code_q_reg[1]_0 ),
        .I3(witness_overflow_event_q_reg_0),
        .O(E));
  LUT6 #(
    .INIT(64'hFBFBFBFBFBFBFFFB)) 
    window_active_q_i_4
       (.I0(overrun_event_q_reg_0),
        .I1(armed_q_reg_0),
        .I2(window_active_q_i_11_n_0),
        .I3(slot_valid_q_reg_rep_n_0),
        .I4(\high2_q_reg[31]_0 ),
        .I5(out_valid_INST_0_i_2_n_0),
        .O(overrun_event_q_reg_1));
  FDRE \window_tag_q_reg[0] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[0]),
        .Q(window_tag_q[0]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[10] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[10]),
        .Q(window_tag_q[10]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[11] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[11]),
        .Q(window_tag_q[11]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[12] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[12]),
        .Q(window_tag_q[12]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[13] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[13]),
        .Q(window_tag_q[13]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[14] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[14]),
        .Q(window_tag_q[14]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[15] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[15]),
        .Q(window_tag_q[15]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[16] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[16]),
        .Q(window_tag_q[16]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[17] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[17]),
        .Q(window_tag_q[17]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[18] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[18]),
        .Q(window_tag_q[18]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[19] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[19]),
        .Q(window_tag_q[19]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[1] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[1]),
        .Q(window_tag_q[1]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[20] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[20]),
        .Q(window_tag_q[20]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[21] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[21]),
        .Q(window_tag_q[21]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[22] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[22]),
        .Q(window_tag_q[22]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[23] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[23]),
        .Q(window_tag_q[23]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[24] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[24]),
        .Q(window_tag_q[24]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[25] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[25]),
        .Q(window_tag_q[25]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[26] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[26]),
        .Q(window_tag_q[26]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[27] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[27]),
        .Q(window_tag_q[27]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[28] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[28]),
        .Q(window_tag_q[28]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[29] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[29]),
        .Q(window_tag_q[29]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[2] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[2]),
        .Q(window_tag_q[2]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[30] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[30]),
        .Q(window_tag_q[30]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[31] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[31]),
        .Q(window_tag_q[31]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[3] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[3]),
        .Q(window_tag_q[3]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[4] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[4]),
        .Q(window_tag_q[4]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[5] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[5]),
        .Q(window_tag_q[5]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[6] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[6]),
        .Q(window_tag_q[6]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[7] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[7]),
        .Q(window_tag_q[7]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[8] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[8]),
        .Q(window_tag_q[8]),
        .R(\window_tag_q_reg[31]_0 ));
  FDRE \window_tag_q_reg[9] 
       (.C(clk),
        .CE(\window_tag_q_reg[0]_0 ),
        .D(active_tag[9]),
        .Q(window_tag_q[9]),
        .R(\window_tag_q_reg[31]_0 ));
  (* SOFT_HLUTNM = "soft_lutpair1" *) 
  LUT3 #(
    .INIT(8'h04)) 
    witness_overflow_event_q_i_1
       (.I0(armed_q_i_2_n_0),
        .I1(armed_q_reg_0),
        .I2(\high2_q_reg[31]_0 ),
        .O(witness_overflow_event_q_i_1_n_0));
  FDRE witness_overflow_event_q_reg
       (.C(clk),
        .CE(1'b1),
        .D(witness_overflow_event_q_i_1_n_0),
        .Q(witness_overflow_event_q_reg_0),
        .R(1'b0));
endmodule
`ifndef GLBL
`define GLBL
`timescale  1 ps / 1 ps

module glbl ();

    parameter ROC_WIDTH = 100000;
    parameter TOC_WIDTH = 0;
    parameter GRES_WIDTH = 10000;
    parameter GRES_START = 10000;

//--------   STARTUP Globals --------------
    wire GSR;
    wire GTS;
    wire GWE;
    wire PRLD;
    wire GRESTORE;
    tri1 p_up_tmp;
    tri (weak1, strong0) PLL_LOCKG = p_up_tmp;

    wire PROGB_GLBL;
    wire CCLKO_GLBL;
    wire FCSBO_GLBL;
    wire [3:0] DO_GLBL;
    wire [3:0] DI_GLBL;
   
    reg GSR_int;
    reg GTS_int;
    reg PRLD_int;
    reg GRESTORE_int;

//--------   JTAG Globals --------------
    wire JTAG_TDO_GLBL;
    wire JTAG_TCK_GLBL;
    wire JTAG_TDI_GLBL;
    wire JTAG_TMS_GLBL;
    wire JTAG_TRST_GLBL;

    reg JTAG_CAPTURE_GLBL;
    reg JTAG_RESET_GLBL;
    reg JTAG_SHIFT_GLBL;
    reg JTAG_UPDATE_GLBL;
    reg JTAG_RUNTEST_GLBL;

    reg JTAG_SEL1_GLBL = 0;
    reg JTAG_SEL2_GLBL = 0 ;
    reg JTAG_SEL3_GLBL = 0;
    reg JTAG_SEL4_GLBL = 0;

    reg JTAG_USER_TDO1_GLBL = 1'bz;
    reg JTAG_USER_TDO2_GLBL = 1'bz;
    reg JTAG_USER_TDO3_GLBL = 1'bz;
    reg JTAG_USER_TDO4_GLBL = 1'bz;

    assign (strong1, weak0) GSR = GSR_int;
    assign (strong1, weak0) GTS = GTS_int;
    assign (weak1, weak0) PRLD = PRLD_int;
    assign (strong1, weak0) GRESTORE = GRESTORE_int;

    initial begin
	GSR_int = 1'b1;
	PRLD_int = 1'b1;
	#(ROC_WIDTH)
	GSR_int = 1'b0;
	PRLD_int = 1'b0;
    end

    initial begin
	GTS_int = 1'b1;
	#(TOC_WIDTH)
	GTS_int = 1'b0;
    end

    initial begin 
	GRESTORE_int = 1'b0;
	#(GRES_START);
	GRESTORE_int = 1'b1;
	#(GRES_WIDTH);
	GRESTORE_int = 1'b0;
    end

endmodule
`endif

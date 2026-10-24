`timescale 1ns/1ps
// Only widths are clamped in this top. The exact DUT emits its own diagnostic.
module guard_tb;
parameter integer COUNT_W=3,WITNESS_W=8,TAG_W=32;
localparam integer C=(COUNT_W<2)?2:((COUNT_W>32)?32:COUNT_W);
localparam integer W=(WITNESS_W<2)?2:((WITNESS_W>64)?64:WITNESS_W);
localparam integer T=(TAG_W<1)?1:((TAG_W>64)?64:TAG_W);
reg clk=0,rst=0,stop=0,rearm=0,out_ready=0;
reg [2:0] sample_levels=0;
reg [T-1:0] window_tag=0;
wire armed,out_valid;
wire [C-1:0] out_period,out_high0,out_high1,out_high2,fault_count;
wire [W-1:0] out_start,out_end;
wire [T-1:0] out_tag;
wire incoherent_event,period_overflow_event,witness_overflow_event,overrun_event;
wire incoherent_seen,period_overflow_seen,witness_overflow_seen,overrun_seen;
deepeye_pwm_coherent_capture #(.COUNT_W(COUNT_W),.WITNESS_W(WITNESS_W),.TAG_W(TAG_W)) dut(.*);
initial begin #10; $fatal(1,"GUARD_MISSING"); end
endmodule

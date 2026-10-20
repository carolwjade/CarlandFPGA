`timescale 1ns/1ps
module independent_tb;
parameter COUNT_W=4,WITNESS_W=8,TAG_W=8;
localparam CW=(COUNT_W<2)?2:((COUNT_W>32)?32:COUNT_W);
localparam WW=(WITNESS_W<2)?2:((WITNESS_W>64)?64:WITNESS_W);
localparam TW=(TAG_W<1)?1:((TAG_W>64)?64:TAG_W);
reg clk=0,rst=1,stop=0,cfg_valid=0,out_ready=0,loopback=0;
reg [CW-1:0] cfg_period=0,cfg_high_yaw=0,cfg_high_pitch=0,cfg_high_speed=0;
reg [TW-1:0] cfg_tag=0;
reg [2:0] drive_levels=0;
wire [2:0] sample_levels,pwm;
assign sample_levels=loopback?pwm:drive_levels;
wire cfg_ready,accepted,rejected,applied,frame_start,running,pending;
wire [CW-1:0] active_period,active_high_yaw,active_high_pitch,active_high_speed;
wire [TW-1:0] active_tag;
wire window_active,window_started,capture_armed,out_valid;
wire [CW-1:0] out_period,out_high0,out_high1,out_high2;
wire [WW-1:0] out_start,out_end;
wire [TW-1:0] out_tag;
wire [CW-1:0] expected_period,expected_high0,expected_high1,expected_high2;
wire [TW-1:0] expected_tag;
wire [3:0] raw_fault_events;
wire failure_event;wire [2:0] failure_code;
deepeye_pwm_applied_capture #(.COUNT_W(COUNT_W),.WITNESS_W(WITNESS_W),.TAG_W(TAG_W)) dut(.*);
always #5 clk=~clk;
integer fd,lg,i,n,sid,got,rows,k; reg [63:0] x[0:11];
string vec,tracefile;
task emit(input string kind);
begin
 $fwrite(lg,"%s %0d %0d",kind,i,sid);
 $fwrite(lg," %h",rst);
 $fwrite(lg," %h",stop);
 $fwrite(lg," %h",cfg_valid);
 $fwrite(lg," %h",cfg_period);
 $fwrite(lg," %h",cfg_high_yaw);
 $fwrite(lg," %h",cfg_high_pitch);
 $fwrite(lg," %h",cfg_high_speed);
 $fwrite(lg," %h",cfg_tag);
 $fwrite(lg," %h",drive_levels);
 $fwrite(lg," %h",loopback);
 $fwrite(lg," %h",out_ready);
 $fwrite(lg," %h",sample_levels);
 $fwrite(lg," %h",cfg_ready);
 $fwrite(lg," %h",accepted);
 $fwrite(lg," %h",rejected);
 $fwrite(lg," %h",applied);
 $fwrite(lg," %h",frame_start);
 $fwrite(lg," %h",running);
 $fwrite(lg," %h",pending);
 $fwrite(lg," %h",pwm);
 $fwrite(lg," %h",active_period);
 $fwrite(lg," %h",active_high_yaw);
 $fwrite(lg," %h",active_high_pitch);
 $fwrite(lg," %h",active_high_speed);
 $fwrite(lg," %h",active_tag);
 $fwrite(lg," %h",window_active);
 $fwrite(lg," %h",window_started);
 $fwrite(lg," %h",capture_armed);
 $fwrite(lg," %h",out_valid);
 $fwrite(lg," %h",out_period);
 $fwrite(lg," %h",out_high0);
 $fwrite(lg," %h",out_high1);
 $fwrite(lg," %h",out_high2);
 $fwrite(lg," %h",out_start);
 $fwrite(lg," %h",out_end);
 $fwrite(lg," %h",out_tag);
 $fwrite(lg," %h",expected_period);
 $fwrite(lg," %h",expected_high0);
 $fwrite(lg," %h",expected_high1);
 $fwrite(lg," %h",expected_high2);
 $fwrite(lg," %h",expected_tag);
 $fwrite(lg," %h",raw_fault_events);
 $fwrite(lg," %h",failure_event);
 $fwrite(lg," %h",failure_code);
 $fwrite(lg,"\n");
end
endtask
initial begin
 if(!$value$plusargs("VEC=%s",vec)||!$value$plusargs("LOG=%s",tracefile))$fatal(1,"MISSING_FILES");
 fd=$fopen(vec,"r");lg=$fopen(tracefile,"w");if(!fd||!lg)$fatal(1,"OPEN_FAILED");
 got=$fscanf(fd,"%d\n",rows);if(got!=1||rows<1)$fatal(1,"BAD_HEADER");
 for(i=0;i<rows;i=i+1)begin
  @(negedge clk);
  got=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h\n",x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10],x[11]);if(got!=12)$fatal(1,"BAD_VECTOR");
  sid=x[0];rst=x[1];stop=x[2];cfg_valid=x[3];cfg_period=x[4];cfg_high_yaw=x[5];cfg_high_pitch=x[6];cfg_high_speed=x[7];cfg_tag=x[8];drive_levels=x[9];loopback=x[10];out_ready=x[11];
  #1;emit("PRE");@(posedge clk);#1;emit("POST");
 end
 $fclose(fd);$fclose(lg);$display("INDEPENDENT_TRACE_DONE edges=%0d",rows);$finish;
end
endmodule

from pathlib import Path
import sys,json,math
D=Path(__file__).parent;R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发")
sys.path[:0]=[str(D/'candidate'),str(D.parent/'demo-motion500-781/python-source'),str(R/'.local/deepeye-host-deps')]
from certified_live_segment_v1 import LiveLaw,Target
from live_snapshot_pose_v1 import snapshot_from_native,with_field_result_time
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
state=RigidState((0.,0.,0.),(0.,0.,0.,1.),.025)
target=Target(1,0,0,2,12000)
law=LiveLaw.create('world784','segment1',1,state,target)
a=law.sample(490000000);b=law.sample(500000000);c=law.sample(510000000);d=law.sample(8000000000)
assert a.speed_m_s==b.speed_m_s==c.speed_m_s==d.speed_m_s==.025
assert a.position_m[2]<b.position_m[2]<c.position_m[2]<d.position_m[2] and d.position_m[2]>.199
passed=['last_actual_target_continues_across500ms_and8s_without_pause']
turn=LiveLaw.create('world784','segment2',2,c,Target(1,300,0,2,12000),parent_segment_id=law.segment_id)
assert turn.sample(0)==c
stop=LiveLaw.create('world784','pause3',3,turn.sample(100000000),Target(0,0,0,0,0),parent_segment_id=turn.segment_id)
assert stop.sample(0)==turn.sample(100000000)
assert 0<stop.sample(50000000).speed_m_s<.025 and stop.sample(200000000).speed_m_s==0
assert stop.sample(1000000000)==stop.sample(200000000)
passed.append('retarget_same_pose_quaternion_speed_and_pause_decelerates_without_jump')
ref=object();snap=snapshot_from_native(law,law_start_qpc_ns=1000000000,at_qpc_ns=1500000000,elapsed_ns=500000000,native_frame_seq=8,actual_pose=b,readback_ref=ref,read_begin_qpc_ns=1490000000,read_return_qpc_ns=1510000000,grant_deadline_qpc_ns=12000000000)
assert snap.at_qpc_ns==1500000000 and snap.original_readback is ref
later=with_field_result_time(snap,1700000000);assert later.at_qpc_ns==snap.at_qpc_ns and later.pose==snap.pose and later.field_return_qpc_ns==1700000000
try:snapshot_from_native(law,law_start_qpc_ns=1000000000,at_qpc_ns=13000000000,elapsed_ns=12000000000,native_frame_seq=9,actual_pose=d,readback_ref=ref,read_begin_qpc_ns=12900000000,read_return_qpc_ns=13100000000,grant_deadline_qpc_ns=12000000000)
except ValueError:pass
else:raise AssertionError('expired board grant snapshot accepted')
passed.append('source_time_not_rebased_to_return_and_expired_grant_rejected')
packet=law.native_packet(host_start_qpc_ns=1000000000,grant_deadline_qpc_ns=12000000000,clock_map_id='clock1');assert packet['hold_last_target'] is True and packet['formal_geometry_proof']=='not_run' and packet['runtime_volume_guard_required'] is True
r=dict(passed=True,controls=passed,model=False,PDE=False,native=False,board=False,UI=False,formal_geometry_proof='not_run',source_authority_minted=False)
(D/'MINIMAL_CONTROLS.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(json.dumps(r))

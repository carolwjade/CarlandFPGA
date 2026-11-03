"""Accepted native pose -> causal source snapshot contract, not authentication.

Root must first authenticate its original native readback and full-volume/portal
acceptance. This module retains that original object; parsed JSON cannot grant
motion/source authority. Sampling time is never moved to field-result time.
"""
from dataclasses import dataclass,replace
if __package__:
    from .certified_live_segment_v1 import LiveLaw,_uint
else:
    from certified_live_segment_v1 import LiveLaw,_uint
from competition.deepeye.simulation.authority.motion.kinematics import RigidState

@dataclass(frozen=True)
class SnapshotPose:
    segment:LiveLaw
    at_qpc_ns:int
    elapsed_ns:int
    native_frame_seq:int
    pose:RigidState
    read_begin_qpc_ns:int
    read_return_qpc_ns:int
    grant_deadline_qpc_ns:int
    original_readback:object
    field_return_qpc_ns:int|None=None
    source_authority:bool=False
    def public_pose(self):
        return dict(position_m=list(self.pose.position_m),orientation_xyzw=list(self.pose.orientation_xyzw))
    def diagnostic(self):
        return dict(world_epoch=self.segment.world_epoch,segment_id=self.segment.segment_id,
            control_seq=str(self.segment.control_seq),at_qpc_ns=str(self.at_qpc_ns),elapsed_ns=str(self.elapsed_ns),
            native_frame_seq=str(self.native_frame_seq),pose=self.public_pose(),speed_m_s=self.pose.speed_m_s,
            read_begin_qpc_ns=str(self.read_begin_qpc_ns),read_return_qpc_ns=str(self.read_return_qpc_ns),
            field_return_qpc_ns=None if self.field_return_qpc_ns is None else str(self.field_return_qpc_ns),
            source_authority=False,claim='mechanical binding only; Root owns actual native/source provenance')

def snapshot_from_native(segment,*,law_start_qpc_ns,at_qpc_ns,elapsed_ns,native_frame_seq,
                         actual_pose,readback_ref,read_begin_qpc_ns,read_return_qpc_ns,grant_deadline_qpc_ns):
    if type(segment) is not LiveLaw or type(actual_pose) is not RigidState:raise TypeError('same live law and canonical accepted pose required')
    for n in (law_start_qpc_ns,at_qpc_ns,elapsed_ns,native_frame_seq,read_begin_qpc_ns,read_return_qpc_ns,grant_deadline_qpc_ns):_uint(n)
    if not law_start_qpc_ns<=at_qpc_ns<=read_return_qpc_ns or at_qpc_ns>=grant_deadline_qpc_ns:raise ValueError('native sample future/expired actual grant')
    if at_qpc_ns-law_start_qpc_ns!=elapsed_ns or read_begin_qpc_ns>read_return_qpc_ns:raise ValueError('actual sample/law/bracket mismatch')
    if readback_ref is None:raise ValueError('retain original authenticated native readback reference')
    # Actual accepted pose is authoritative input from Root, not replaced by a
    # predicted endpoint or this law's future sample. Native collision STOP may
    # legitimately leave a different accepted pose; Root must mark/handle fault.
    return SnapshotPose(segment,at_qpc_ns,elapsed_ns,native_frame_seq,actual_pose,
        read_begin_qpc_ns,read_return_qpc_ns,grant_deadline_qpc_ns,readback_ref)

def with_field_result_time(snapshot,returned_qpc_ns):
    if type(snapshot) is not SnapshotPose:raise TypeError('retained snapshot required')
    _uint(returned_qpc_ns)
    if snapshot.field_return_qpc_ns is not None or returned_qpc_ns<snapshot.read_return_qpc_ns:raise ValueError('one original field result after snapshot receipt')
    return replace(snapshot,field_return_qpc_ns=returned_qpc_ns)

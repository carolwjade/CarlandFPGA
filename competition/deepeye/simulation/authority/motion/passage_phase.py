"""Ordered blue-entry/red-exit preview reducer. No pose application or CAS.

Typed/frozen chains are internal numerical provenance, not authentication of
the current owner, scene, clock, STOP, or previously executed movement.
"""
from dataclasses import dataclass, field
from fractions import Fraction

from . import certified_path as cp
from . import gate_geometry as g
from . import gate_clearance as gc
from . import workspace_boundaries as w
from .kinematics import RigidState, MAX_DT_NS


@dataclass(frozen=True)
class RunContext:
    run_id: str
    scene_revision: str
    epoch: int
    layout: w.Layout
    envelope: w.Envelope
    owner_reference: str

    def __post_init__(self):
        for value in (self.run_id,self.scene_revision,self.owner_reference):w._label(value)
        if type(self.epoch) is not int or self.epoch<0:raise ValueError('nonnegative epoch required')
        if type(self.layout) is not w.Layout or type(self.envelope) is not w.Envelope:
            raise TypeError('immutable layout and envelope required')


@dataclass(frozen=True)
class Event:
    kind: str
    start_ns: int
    end_ns: int
    pose_revision: int
    proof_binding: str


@dataclass(frozen=True,init=False)
class PassageState:
    context: RunContext
    pose: RigidState
    errors: gc.ErrorBounds
    speed_error_upper: Fraction
    error_budget_reference: str
    pose_revision: int
    monotonic_ns: int
    phase: str
    entered: bool
    history: tuple
    trace_hash: str
    seal: str = field(init=False)


def _state(**values):
    result=w._create(PassageState,**values)
    object.__setattr__(result,'seal',w.digest(result))
    return result


@dataclass(frozen=True)
class Initialization:
    status: str
    state: PassageState | None
    reason: str
    motion_grant: bool = field(default=False,init=False)


def initialize(context,pose,errors,*,pose_revision,monotonic_ns,error_budget_reference):
    if type(context) is not RunContext or type(pose) is not RigidState or type(errors) is not gc.ErrorBounds:
        raise TypeError('immutable context, current pose and explicit errors required')
    for value in (pose_revision,monotonic_ns):
        if type(value) is not int or value<0:raise ValueError('nonnegative revision/timestamp required')
    w._label(error_budget_reference)
    path=cp.CanonicalPath(pose,'fast_9600',0,0,0,1,inherited_errors=errors,error_budget_reference=error_budget_reference)
    sample=path.sample(0);sides=w.point_sides(sample,context.envelope)
    blue=context.layout.blue
    capsule=g.Capsule(pose.position_m,sample.axis,context.envelope.half_segment_m,context.envelope.radius_m)
    un=g._support_intervals(capsule,blue.plane)[3]
    outside=next(s for s in sides if s.face==blue.face).outside
    others=all(s.inside for s in sides if s.face!=blue.face)
    aligned=gc._angle_proved(un,-1,g._exact(sample.errors.angle_error_rad).hi)
    if not (outside and others and aligned):
        return Initialization('UNKNOWN',None,'initial complete outside/other-five-inside/inward witness missing')
    proof=w.digest((context,pose,sample.errors,sides,error_budget_reference))
    event=Event('INITIAL_OUTSIDE',monotonic_ns,monotonic_ns,pose_revision,proof)
    state=_state(context=context,pose=pose,errors=sample.errors,speed_error_upper=Fraction(0),
        error_budget_reference=error_budget_reference,pose_revision=pose_revision,monotonic_ns=monotonic_ns,
        phase='OUTSIDE_ENTRY',entered=False,history=(event,),trace_hash=proof)
    return Initialization('SAFE',state,'strict initial whole-body witness; no movement applied')


def _valid(state):
    if type(state) is not PassageState or state.seal!=w.digest(state):return False
    kinds=tuple(e.kind for e in state.history)
    if not kinds or kinds[0]!='INITIAL_OUTSIDE':return False
    expected={
        'OUTSIDE_ENTRY':('INITIAL_OUTSIDE',),
        'ENTRY_CROSSING':('INITIAL_OUTSIDE','ENTRY_WINDOW'),
        'INSIDE':('INITIAL_OUTSIDE','ENTRY_WINDOW','ENTERED'),
        'EXIT_CROSSING':('INITIAL_OUTSIDE','ENTRY_WINDOW','ENTERED','EXIT_WINDOW'),
        'ARRIVED':('INITIAL_OUTSIDE','ENTRY_WINDOW','ENTERED','EXIT_WINDOW','ARRIVED'),
    }
    if kinds!=expected.get(state.phase) or state.entered!=('ENTERED' in kinds):return False
    return (state.speed_error_upper>=0 and all(e.start_ns<=e.end_ns<=state.monotonic_ns and e.pose_revision<=state.pose_revision for e in state.history)
            and all(a.end_ns<=b.end_ns for a,b in zip(state.history,state.history[1:])))


def required_inherited_errors(state,dt_ns):
    if not _valid(state):raise ValueError('valid internal passage history required')
    if type(dt_ns) is not int or not 1<=dt_ns<=MAX_DT_NS:raise ValueError('canonical step duration required')
    # Speed law is 1-Lipschitz in v0. Difference in arc <= e_v*dt, pose <= K*e_v*dt.
    drift=state.speed_error_upper*Fraction(dt_ns,10**9)
    position=Fraction(state.errors.position_error_m)+drift
    angle=Fraction(state.errors.angle_error_rad)+drift/2  # canonical K<=.5
    return gc.ErrorBounds(cp._upper_float(cp._fraction_interval(position).hi),
        cp._upper_float(cp._fraction_interval(angle).hi),state.errors.additional_margin_m)


@dataclass(frozen=True)
class Preview:
    status: str
    candidate: PassageState
    proofs: tuple
    reason: str
    failure_candidate: bool = False
    motion_grant: bool = field(default=False,init=False)
    atomic_cas_completed: bool = field(default=False,init=False)


def preview(state,path,context,*,expected_pose_revision,start_monotonic_ns,deadline_monotonic_ns,hard_stop,max_slices=16):
    if type(path) is not cp.CanonicalPath or type(context) is not RunContext:
        raise TypeError('canonical path and owner-asserted immutable context required')
    if not _valid(state):raise ValueError('invalid internal history; no imported arbitrary phase')
    if type(max_slices) is not int or max_slices<0:raise ValueError('nonnegative slice work budget required')
    if (context!=state.context or expected_pose_revision!=state.pose_revision
            or path.provenance.start_state!=state.pose or start_monotonic_ns<state.monotonic_ns):
        return Preview('UNKNOWN',state,(),'run/scene/gates/epoch/pose/time mismatch')
    prepared=w.prepare(path,context.layout,context.envelope,start_monotonic_ns=start_monotonic_ns,
        deadline_monotonic_ns=deadline_monotonic_ns,hard_stop=hard_stop)
    plan=prepared.plan
    if not plan.covered_ns or state.phase=='ARRIVED':
        return Preview('HELD',state,(),plan.reason if not plan.covered_ns else 'ARRIVED_FROZEN')
    required=required_inherited_errors(state,path.provenance.requested_dt_ns)
    actual=path.provenance.inherited_errors
    if any(getattr(actual,name)<getattr(required,name) for name in ('position_error_m','angle_error_rad','additional_margin_m')):
        return Preview('UNKNOWN',state,(),'inherited pose/numeric/speed carry budget reset')
    if len(plan.slices)>max_slices:return Preview('UNKNOWN',state,(),'slice work budget exhausted before any advance')
    phase=state.phase;entered=state.entered;history=list(state.history);proofs=[]
    def event(kind,index,proof):
        record=plan.slices[index]
        history.append(Event(kind,start_monotonic_ns+record.start.elapsed_ns,
            start_monotonic_ns+record.end.elapsed_ns,state.pose_revision+1,proof.binding))
    for index,record in enumerate(plan.slices):
        role='entry' if phase in ('OUTSIDE_ENTRY','ENTRY_CROSSING') else 'exit'
        proof=w.check_slice(prepared,index,role);proofs.append(proof)
        if proof.status!='SAFE':
            return Preview(proof.status,state,tuple(proofs),proof.reason,proof.status=='VIOLATION_PROVED')
        active=context.layout.blue if role=='entry' else context.layout.red
        side=next(s for s in proof.end_sides if s.face==active.face)
        if role=='entry':
            if phase=='OUTSIDE_ENTRY' and not side.outside:
                event('ENTRY_WINDOW',index,proof);phase='ENTRY_CROSSING'
            if side.inside and all(s.inside for s in proof.end_sides):
                if phase=='OUTSIDE_ENTRY':event('ENTRY_WINDOW',index,proof)
                event('ENTERED',index,proof);phase='INSIDE';entered=True
        else:
            if not entered:return Preview('UNKNOWN',state,tuple(proofs),'missing ordered entered history')
            if phase=='INSIDE' and not side.inside:
                event('EXIT_WINDOW',index,proof);phase='EXIT_CROSSING'
            if side.outside:
                if phase=='INSIDE':event('EXIT_WINDOW',index,proof)
                event('ARRIVED',index,proof);phase='ARRIVED'
        # At most one role completion in this slice; role switches next slice.
        if phase=='ARRIVED' and index+1<len(plan.slices):
            return Preview('UNKNOWN',state,tuple(proofs),'arrival within multi-slice plan needs event-window refinement')
    trace=w.digest((state.trace_hash,prepared.binding,tuple(proofs),tuple(history)))
    end=plan.end
    next_state=_state(context=context,pose=end.state,errors=end.errors,
        speed_error_upper=state.speed_error_upper+Fraction(end.speed_export_error_m_s),
        error_budget_reference=path.provenance.error_budget_reference,pose_revision=state.pose_revision+1,
        monotonic_ns=start_monotonic_ns+plan.covered_ns,phase=phase,entered=entered,history=tuple(history),trace_hash=trace)
    return Preview('SAFE',next_state,tuple(proofs),'whole plan preview only; owner must recheck STOP/deadline and CAS')

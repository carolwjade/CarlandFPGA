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
    phase=state.phase;entered=state.entered;history=list(state.history);proofs=[];strict_suffix=False
    def event(kind,index,proof):
        record=plan.slices[index]
        history.append(Event(kind,start_monotonic_ns+record.start.elapsed_ns,
            start_monotonic_ns+record.end.elapsed_ns,state.pose_revision+1,proof.binding))
    for index,record in enumerate(plan.slices):
        role='entry' if phase in ('OUTSIDE_ENTRY','ENTRY_CROSSING') else 'exit'
        proof=w.check_slice(prepared,index,role);proofs.append(proof)
        if proof.status!='SAFE':
            return Preview(proof.status,state,tuple(proofs),proof.reason,proof.status=='VIOLATION_PROVED')
        if phase=='ARRIVED':
            # This preview's earlier slice proved full-body red exit. Every
            # remaining ORIGINAL slice still needs its complete exit-role proof:
            # red strictly outside throughout, other five strictly inside.
            if (len(proof.faces)!=len(w.FACES) or {face.face for face in proof.faces}!=set(w.FACES)
                    or proof.role!='exit' or any(face.method!=('STRICT_OUTSIDE_ACTIVE'
                    if face.face==context.layout.red.face else 'STRICT_INSIDE') for face in proof.faces)):
                return Preview('UNKNOWN',state,tuple(proofs),'strict red-outside suffix certificate missing')
            strict_suffix=True
            continue  # Retain ARRIVED, without another ARRIVED/EXIT_WINDOW event.
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
    if strict_suffix and plan.covered_ns!=path.provenance.requested_dt_ns:
        return Preview('UNKNOWN',state,tuple(proofs),'strict suffix requires the complete original duration')
    trace_values=(state.trace_hash,prepared.binding,tuple(proofs),tuple(history))
    trace=w.digest(('strict-red-outside-suffix-v1',trace_values) if strict_suffix else trace_values)
    end=plan.end
    next_state=_state(context=context,pose=end.state,errors=end.errors,
        speed_error_upper=state.speed_error_upper+Fraction(end.speed_export_error_m_s),
        error_budget_reference=path.provenance.error_budget_reference,pose_revision=state.pose_revision+1,
        monotonic_ns=start_monotonic_ns+plan.covered_ns,phase=phase,entered=entered,history=tuple(history),trace_hash=trace)
    return Preview('SAFE',next_state,tuple(proofs),'whole plan preview only; owner must recheck STOP/deadline and CAS')


@dataclass(frozen=True)
class RelativeTransition:
    """Private geometry anchor, never an authorization/freshness timestamp.

    The original absolute preview and its hashes remain intact. Only events
    appended by this transition are mapped to the separately committed fence.
    """
    previous: PassageState
    preview: Preview
    anchor_ns: int
    duration_ns: int


def prepare_relative_transition(state,path,context,*,max_slices=16):
    if not _valid(state) or type(path) is not cp.CanonicalPath:
        raise ValueError('valid owned history and canonical path required')
    duration=path.provenance.requested_dt_ns
    anchor=state.monotonic_ns
    # +1 belongs solely to the numerical anchor's strict D-1 convention.
    # It neither extends nor supplies a real command/AI/heartbeat deadline.
    result=preview(state,path,context,expected_pose_revision=state.pose_revision,
        start_monotonic_ns=anchor,deadline_monotonic_ns=anchor+duration+1,
        hard_stop=False,max_slices=max_slices)
    return RelativeTransition(state,result,anchor,duration)


def materialize_committed_transition(transition,*,start_ns,end_ns,binding):
    """Run outside the final fence, after the owner published its commit frame.

    This creates a new trace binding actual time to an unchanged relative proof;
    it never relabels that proof or moves previously committed events.
    """
    if type(transition) is not RelativeTransition or transition.preview.status!='SAFE':
        raise ValueError('successful internally prepared relative transition required')
    if (type(start_ns) is not int or type(end_ns) is not int
            or start_ns<transition.previous.monotonic_ns
            or end_ns-start_ns!=transition.duration_ns):
        raise ValueError('committed interval must cover the exact relative duration')
    w._label(binding)
    old=transition.previous;candidate=transition.preview.candidate
    if not _valid(old) or not _valid(candidate):raise ValueError('invalid internal phase chain')
    count=len(old.history)
    if candidate.history[:count]!=old.history:raise ValueError('previous events changed')
    delta=start_ns-transition.anchor_ns
    appended=tuple(Event(e.kind,e.start_ns+delta,e.end_ns+delta,e.pose_revision,e.proof_binding)
                   for e in candidate.history[count:])
    values={name:getattr(candidate,name) for name in candidate.__dataclass_fields__ if name!='seal'}
    values.update(monotonic_ns=end_ns,history=old.history+appended,
        trace_hash=w.digest(('relative-proof/actual-fence-v1',candidate.trace_hash,start_ns,end_ns,binding)))
    state=_state(**values)
    if not _valid(state):raise ValueError('actual interval violates phase chronology')
    return state

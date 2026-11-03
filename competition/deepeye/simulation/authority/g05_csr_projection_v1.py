"""Original G05/E4 source mapping to the bounded public demo AI view.

This is a new host verifier. It does not claim that E4 bytes are the older
private-PL capture format or that the original C36 projection was executed.
Only counts/quality from actual board-returned frames, public poses/gates and
actual executed actions leave this module; scene truth never enters the view.
"""
import copy
import math
from fractions import Fraction

from .g05_csr_channels_v1 import (_Mapping, _need, _raw, _sha, _uint,
                                 validate_raw4_observation)


def _nav_exit_goal(center,normal,half_segment,radius,numeric,asset,margin):
    """Public red-gate/body clearance target; never arrival or aperture proof."""
    _need(type(center) in (tuple,list) and len(center)==3 and
          type(normal) in (tuple,list) and len(normal)==3,'public gate geometry required')
    def exact(value):
        _need(type(value) in (int,float,Fraction) and
              (type(value) is not float or math.isfinite(value)),'finite public geometry bound')
        return Fraction(value)
    c=tuple(exact(x) for x in center);n=tuple(exact(x) for x in normal)
    _need(all(x in (-1,0,1) for x in n) and sum(abs(x) for x in n)==1,
          'public cube-face outward unit normal required')
    half,r,nb,ab=(exact(x) for x in (half_segment,radius,numeric,asset))
    _need(half>=0 and r>0 and nb>=0 and ab>=0 and
          type(margin) is float and margin==.05,'fixed declared public clearance bounds')
    offset=half+r+nb+ab+exact(margin)
    goal=[float(x) for x in c]
    for i,component in enumerate(n):
        if component:
            goal[i]=math.nextafter(float(c[i]+component*offset),
                                  math.inf if component>0 else -math.inf)
    _need(all(math.isfinite(x) and abs(x)<=1000 for x in goal),'existing public goal coordinate bound')
    return goal


def _original_mapping(mapping):
    from ...tools.diagnostic.functional50_chain_v2_client_a import OriginalPhaseReceipt
    from ...tools.diagnostic.original_source_trace_scan_a import _check_bundle
    _need(type(mapping) is _Mapping, 'original G05 mapping required')
    c=mapping.channels; c.checkpoint(); refs=mapping.refs; facts=mapping.facts
    _need(any(mapping is x for x in c._mappings) or mapping.current_read is None,
          'unretained original mapping')
    _need(any(event is mapping.event and saved['raw_response']==facts['raw_response']
              and original is refs for event,saved,original in c._events), 'original consumed TRACE event required')
    phase=refs['phase_receipt']
    _need(type(phase) is OriginalPhaseReceipt and phase.kind=='trace_scan'
          and phase.owner is c.refs.chain and any(phase is x for x in c.refs.chain.phase_receipts)
          and phase.response_raw==facts['raw_response'] and phase.status=='COMPLETE'
          and phase.unknown is False and phase.clock is c.refs.clock
          and phase.lower_qpc_ns==facts['lower_qpc_ns'] and phase.upper_qpc_ns==facts['upper_qpc_ns'],
          'actual original complete TRACE phase required')
    item=refs['admitted']; token=refs['token']; source=c.refs.source
    _need(any(item is x for x in c.refs.producer._scanner._admitted)
          and item['token'] is token and item['draft'] is refs['draft']
          and token._book is c.refs.book and token._draft is refs['draft'] and token._ended is True
          and any(token._draft is x for x in c.refs.book._samples), 'actual original selected source sample required')
    entry=source._retained_sample(refs['payload'])
    _need(entry['token'] is token and entry['raw']==refs['source_bytes']
          and item['payload_bytes']==refs['source_bytes'], 'source payload/token bytes changed')
    preparation=refs['preparation']; bundle=c.refs.chain.bundle; _check_bundle(bundle)
    _need(type(preparation) is bundle.adapter.Preparation and preparation.original.request is refs['request']
          and preparation.original.source is refs['source_bytes']
          and preparation.original.companions is refs['companions'], 'original B131 preparation bytes required')
    correlation=refs['client_result']['correlation']
    _need(type(correlation) is dict and correlation['status']=='FOUR_FRAME_CORRELATION_CONSISTENT'
          and correlation['retained']['original'].request==refs['request']
          and correlation['retained']['original'].source==refs['source_bytes']
          and correlation['retained']['original'].companions==refs['companions']
          and correlation['retained']['companions']==refs['companions'], 'actual selected four-frame correlation required')
    original=preparation.original
    verified=bundle.adapter.correlate_collected(preparation.plan,correlation['retained']['wire'],
                                               original.companions,correlation['result_rows'])
    _need(verified['status']=='FOUR_FRAME_CORRELATION_CONSISTENT'
          and verified['frames']==correlation['frames'], 'actual four raw E4 frames no longer correlate')
    return c,phase,item,token,verified


def _map_original_trace(channels,event,facts,refs):
    from ...integration.sensor_source import validate_record
    phase=refs['phase_receipt']; payload=refs['payload']; record=validate_record(payload)
    origin=channels.refs.source.source._origin; _uint(origin)
    adc=origin+record.adc_tick_ms*1_000_000
    em=None if record.em_tick_ms is None else origin+record.em_tick_ms*1_000_000
    lower=min(adc,em) if em is not None else adc
    candidate=dict(schema='g05_csr_source4_candidate_v1',kind='candidate_four_channel_input',
        channel_counts=[],quality=record.quality,
        source_time=dict(adc_qpc_ns=adc,em_qpc_ns=em,adc_tick_ms=record.adc_tick_ms,
            em_tick_ms=record.em_tick_ms,source_origin_qpc_ns=origin,
            time_basis='actual_original_nominal_source_grid_not_physical_ADC_timestamp'),
        observation_identity=dict(context=dict(channels.refs.c42_context),
            capture_sha256=_sha(facts['raw_response']),request_sha256=_sha(refs['request']),
            phase_index=phase.phase_index,source_admission_index=channels.refs.producer._scanner._admitted.index(refs['admitted'])),
        source_provenance=dict(source_mode=record.source_mode,profile_id=record.profile_id,
            profile_status=record.profile_status,profile_note=record.profile_note,
            transport='actual_board_E4_CSR_return',sensor_origin='simulation_causal_candidate',
            physical_sensor_authenticated=False,formal_H12='not_run',formal100ms='not_run'))
    m=_Mapping(channels,event,facts,refs,candidate,b'',lower,phase)
    c,actual,item,token,correlation=_original_mapping(m)
    frames=correlation['frames']; counts=[]
    _need(len(frames)==4, 'four actual returned channels required')
    for i,frame in enumerate(frames):
        point=frame['point']; lane=frame['original_lane']
        valid=bool(record.quality & (1<<i))
        expected_source=(em if i<3 else adc) if valid else None
        _need(frame['channel']==i and frame['crc_consistent'] is True
              and lane['acquisition_qpc_ns']==adc and lane['source_qpc_ns']==expected_source,
              'actual ADC/EM grid and frame association changed')
        _need(point['valid'] is valid, 'returned channel validity changed')
        counts.append(point['value'] if valid else None)
    # Returned counts are the only values exposed to AI. Original input counts
    # are used by the unchanged B131 correlator, never as a fallback here.
    candidate['channel_counts']=counts
    now=c.refs.clock(); _need(lower<=actual.lower_qpc_ns<=actual.upper_qpc_ns<=now,
                              'original source/host receive order required')
    draft=refs['draft']; adc_call=draft.get('adc')
    _need(type(adc_call) is dict and type(adc_call.get('end_qpc_ns')) is int,
          'actual completed source ADC call required')
    adc_upper=adc_call['end_qpc_ns']; _need(adc<=adc_upper<=actual.lower_qpc_ns,
                                           'ADC call not before actual board injection')
    doc=dict(schema_version=1,kind='g05_raw4_observation_v1',context=dict(c.refs.legacy_context),
        observed_seq=actual.phase_index,adc_interval_ns=dict(lower_ns=adc,upper_ns=adc_upper),
        native_em_interval_ns=None if em is None else dict(lower_ns=em,upper_ns=em),
        receipt_interval_ns=dict(lower_ns=actual.lower_qpc_ns,upper_ns=actual.upper_qpc_ns),
        capture_sha256=_sha(facts['raw_response']),quality=record.quality,channel_counts=counts,
        wire_format='ABI3_E4_PAYLOAD_REV2',wire_hex=correlation['retained']['wire'].hex(),
        target100ms_met=(now-adc<=100_000_000 and em is not None and now-em<=100_000_000))
    m.raw=_raw(doc); validate_raw4_observation(m.raw,context=c.refs.legacy_context,now_ns=now)
    return m


def _public_observation(mapping):
    c,phase,item,token,_=_original_mapping(mapping)
    draft=token._draft; record=mapping.candidate
    reads=draft.get('pose_reads'); _need(type(reads) is dict, 'original sensor pose reads required')
    adc_read=reads.get('adc'); _need(type(adc_read) is dict and adc_read.get('postcheck_complete') is True,
                                   'actual complete ADC pose read required')
    adc_pose=adc_read.get('pose'); _need(type(adc_pose) is dict, 'actual ADC pose required')
    quality=record['quality']; times=record['source_time']; em_pose=None
    if quality & 7:
        if times['adc_qpc_ns']==times['em_qpc_ns']:
            em_read=reads.get('em')
        else:
            held=draft.get('held_em_association')
            _need(type(held) is dict and type(held.get('original_em')) is dict,
                  'actual held EM origin required')
            em_read=held['original_em'].get('pose_read')
        _need(type(em_read) is dict and em_read.get('postcheck_complete') is True,
              'actual complete EM pose read required')
        em_pose=em_read.get('pose'); _need(type(em_pose) is dict, 'actual EM pose required')
    return dict(sample_id=record['observation_identity']['capture_sha256'],
        counts=list(record['channel_counts']),quality=quality,
        adc_qpc_ns=times['adc_qpc_ns'],em_qpc_ns=times['em_qpc_ns'],
        adc_pose=copy.deepcopy(adc_pose),em_pose=copy.deepcopy(em_pose))


def project_original_g05(association, *, max_source_age_ns):
    """Project only an association retained inside the actual actor transaction."""
    from .owned_invocation_v1.adapter import _Association, _root_guard
    from ...tools.run_causal_functional_chain import _RegistryView, _RegistryHold
    _uint(max_source_age_ns,1,30_000_000_000)
    _need(type(association) is _Association and type(association.g05_mapping) is _Mapping,
          'original typed observation association required')
    a=association; m=a.g05_mapping; c=m.channels; o=c.owner
    _need(a.owner is o and a.mapping_receipt is m and a.event in c._observation_events
          and a.record.raw==m.raw and a.source is c and a.clock is c.refs.clock
          and a.session is c.refs.projection and m.used and _raw(m.candidate)==m.retained_bytes,
          'active original source association changed')
    _root_guard(o,a); c.binding.check_source_config(); _original_mapping(m)
    current=m.current_read; view=m.registry_ref; hold=m.registry_hold
    _need(a.current_read is current and a.registry_ref is view and type(view) is _RegistryView
          and type(hold) is _RegistryHold and hold.view is view
          and any(x is current and y is view and z is hold for x,y,z in c.refs.source._registry_observations),
          'actual original getter/registry hold required')
    _need(any(x is current for x in c.refs.projection._current)
          and any(x is view and y is hold for x,y,_ in c.refs.projection._registries),
          'original C42 getter/registry attachments lost')
    _need(type(current) is dict and type(current.get('pose')) is dict
          and type(current.get('pose_read')) is dict and current.get('valid_span') is not None,
          'actual current public pose and validity span required')
    now=_uint(current['at_qpc_ns']); actual_now=c.refs.clock()
    _need(hold.lower_qpc_ns<=current['pose_read']['begin_qpc_ns']<=now<=hold.upper_qpc_ns<=actual_now,
          'actual getter/hold interval mismatch')
    _need(current['pose_revision']==c.refs.link.executor._root.pose_revision,
          'public getter is not current original Root')
    _need(view._refs[3] is o and view._refs[6] is o._boot
          and view._refs[9] is c.refs.book._root is c.refs.link.executor._root,
          'original Root changed after the actual getter/registry hold')
    selected=[x for x in c._mappings if x is not m]+[m]
    transitions=tuple(t for t in c.refs.book._actor_custody.transitions
                      if t.kind=='STEP' and t.closed)
    from . import navigation_session_profile as navigation
    navigation_profile=c.refs.source.source._navigation_profile
    navigation.validate_profile(navigation_profile)
    if navigation_profile is not None:
        selected,transitions=navigation.rolling_refs(navigation_profile,
            tuple((x.sample_lower_ns,x) for x in selected),
            tuple((t.record['completion_observed_qpc_ns'],t) for t in transitions),m)
        selected=[x for x in selected if x is not m]+[m]
    observations=[_public_observation(x) for x in selected]
    observation=observations[-1]
    _need(actual_now-m.sample_lower_ns<max_source_age_ns, 'actual demo source age expired')
    values=c.refs.world.binding.world_values
    goal=list(values.layout.red.center_m)
    if navigation_profile is not None:
        declared=values.budget_derivation
        _need(declared.numeric_m>=declared.policy_guard_m+declared.getter_endpoint_cap_m
              and declared.asset_m>=declared.policy_guard_m+declared.full_drill_containment_upper_m,
              'declared public numeric/getter/drill-asset coverage required')
        # Own executed gate history, not a candidate preview or obstacle query.
        # The current getter/registry hold above must still bind this exact Root.
        executor=c.refs.link.executor; root=executor._root
        passage=executor.passage_state()
        _need(executor._root is root is c.refs.book._root
              and current['pose_revision']==root.pose_revision
              and passage.pose_revision==root.pose_revision and passage.pose==root.pose
              and passage.context.layout==values.layout
              and passage.context.envelope==values.envelope
              and not root.world_invalid and not root.trial_failed,
              'same closed public getter and executed portal history required')
        _need(type(passage.entered) is bool
              and passage.entered==any(e.kind=='ENTERED' for e in passage.history)
              and passage.phase in ('OUTSIDE_ENTRY','ENTRY_CROSSING','INSIDE','EXIT_CROSSING','ARRIVED'),
              'original executed whole-entry history required')
        _need((passage.phase in ('INSIDE','EXIT_CROSSING','ARRIVED'))==passage.entered,
              'executed portal stage mismatch')
        # Never steer back to blue after its committed ENTERED event, even
        # for same-face gates or after the bounded public action window rolls.
        gate=values.layout.red if passage.entered else values.layout.blue
        normal=gate.normal if passage.entered else tuple(-x for x in gate.normal)
        goal=_nav_exit_goal(gate.center_m,normal,
            values.envelope.half_segment_m,values.envelope.radius_m,
            declared.numeric_m,declared.asset_m,navigation_profile.exit_clearance_margin_m)
    actions=[]
    for transition in transitions:
        before=transition.before; after=c.refs.book._root
        slots=[s for s in c.refs.world.owner._commits if s.book_transition is transition and s.committed]
        _need(len(slots)==1 and slots[0].post_root is not None, 'actual executed action receipt missing')
        after=slots[0].post_root
        def pose(value):return dict(position_m=[float(x) for x in value.position_m],
                                    orientation_xyzw=[float(x) for x in value.orientation_xyzw])
        actions.append(dict(action_id=c.refs.projection.bind_observed(slots[0]),
                            from_pose=pose(before.pose),to_pose=pose(after.pose)))
    public_limit=32 if navigation_profile is None else navigation_profile.max_public_items
    _need(len(observations)+len(actions)<=public_limit, 'finite public evidence history exceeded')
    public=dict(schema_version=1,projection_id='g05_csr_c28_demo_view_v1',enabled=True,
                now_qpc_ns=actual_now,pose=copy.deepcopy(current['pose']),goal_m=goal,
                observation=observation,history=observations[:-1],executed_actions=actions)
    # New selected verifier validates the bounded public schema before IPC.
    c.policy.demo_ai_profile.verifier.validate_public(public)
    target100=(actual_now-observation['adc_qpc_ns']<=100_000_000
               and observation['em_qpc_ns'] is not None
               and actual_now-observation['em_qpc_ns']<=100_000_000)
    return dict(input_status='PROJECTED',core_ran=False,authorization='none',public_input=public,
                evidence_scope='g05_csr_original_v1',target100ms_met=target100)

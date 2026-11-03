"""Explicit live PC_DIRECT admission; no board output/old Book credentials.

Root authenticates the actual INIT/SSH/native route. This adapter correlates its
original snapshot, causal source and genuine four E4 frames before host motion.
The inherited BOARD client is an exact822 copy; its schema is never relaxed.
"""
import binascii
import copy
import hashlib
import math
import struct
import time

from .continuous_native_client import (NativeClient, NativeRejected, canonical,
                                       hex64, need, tick, uint)
from .motion import validate

COMMAND_ABI = 'DEEPEYE-LIVE-PC-DIRECT-COMMAND-884-v1'
SOURCE_AGE_NS = 1_500_000_000
TTL_MAX_MS = 3000
NATIVE_ADMISSION_MARGIN_NS = 100_000_000
EXTRA_STATE = frozenset(('admission_mode', 'action_source', 'world_epoch',
    'source_witness', 'board_observation_seq', 'board_observation_sha256',
    'source_record_sha256', 'observation_native_tick_usec', 'pc_command_seq',
    'pc_command_sha256'))


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _label(value):
    need(type(value) is str and 0 < len(value) <= 128 and value.isascii() and
         all(32 < ord(c) < 127 for c in value), 'ASCII_IDENTITY')
    return value


def _native_uint(value):
    need(type(value) in (int, float) and math.isfinite(value) and
         value == int(value), 'NATIVE_INTEGER')
    return uint(int(value), 0, (1 << 53)-1)


def advice_applicable(advice, current, epoch, now):
    """Original acquisition, .25m/15degree and actual current-read guard."""
    try:
        need(type(advice) is dict and advice['world_epoch'] == epoch and
             advice['status'] in ('ADVISE', 'STOP'), 'ACTUAL_ADVICE')
        acquired = tick(advice['source_acquisition_qpc_ns'])
        need(0 <= now-acquired < SOURCE_AGE_NS, 'FAST_SOURCE_EXPIRED')
        completed = tick(advice['inference_completed_qpc_ns'])
        need(acquired <= completed <= now, 'ACTUAL_AI_COMPLETION')
        n = current['native']; at = current['host']['accepted_tick_qpc_interval_ns'][0]
        need(n['ready'] is True and not n['fault'] and 0 <= now-at <= 250_000_000,
             'CURRENT_NATIVE_READ_EXPIRED')
        need(math.dist(advice['source_pose']['position_m'], n['position_m']) <= .25,
             'SOURCE_POSE_DISTANCE')
        def forward(q):
            x,y,z,w = q
            return (2*(x*z+y*w), 2*(y*z-x*w), 1-2*(x*x+y*y))
        a = forward(advice['source_pose']['orientation_xyzw'])
        b = forward(n['orientation_xyzw'])
        need(sum(x*y for x,y in zip(a,b)) >= math.cos(math.radians(15)),
             'SOURCE_POSE_ORIENTATION')
        need(advice['quality'] == 7 and advice['c3_observed'] is False,
             'FRESH_FINITE_EM3_REQUIRED')
        return True
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def verify_e4(source, actual, *, binding, source_seq):
    """Independently decode original E4/CRC; no numerical source execution."""
    from ..golden.codec import trace_candidate
    r = actual['response']; result = r['result']
    need(r.get('abi') == 'DEEPEYE-LIVE-BOARD-791-v1' and r.get('op') == 'sense'
         and r.get('status') == 'COMPLETE' and r.get('unknown') is False and
         all(r.get(k) == v for k,v in binding.items()), 'BOUND_REAL_SENSE')
    need(digest(r) == actual['response_sha256'], 'ORIGINAL_SENSE_DIGEST')
    uint(r['request_seq'], 1, 0xffffffff); uint(source_seq, 1, 65535//4)
    need(result['source_seq'] == source_seq and result['source_digest'] == digest(source)
         and result['quality'] == source['quality'] == 7 and
         result['correlation'] == 'FOUR_FRAME_CRC_SOURCE_CONSISTENT', 'SOURCE_IDENTITY_QUALITY')
    counts = source['channel_counts']; rows = result['result_rows']; ds = result['decoded']
    need(type(counts) is list and len(counts) == len(rows) == len(ds) == 4 and
         counts[3] is None and all(type(v) is int and 0 <= v <= 4095 for v in counts[:3]),
         'GENUINE_EM3_NULL_C3')
    wire = bytes.fromhex(result['wire_hex']); need(0 < len(wire) <= 252, 'E4_BYTES')
    cursor = 0; session = None; previous = None
    for lane, (declared,row) in enumerate(zip(ds,rows)):
        size = uint(row['bytes'], 14, 63); frame = wire[cursor:cursor+size]; cursor += size
        need(len(frame) == size, 'FRAME_SIZE')
        magic,version,kind,length,view,seq,stamp = struct.unpack_from('<2sBBBBHI', frame)
        need(magic == b'\xa5\x5a' and version == 3 and kind == 0xe4 and view == 1
             and len(frame) == length+14 and seq == 4*(source_seq-1)+lane+1
             and stamp == result['adc_tick_ms']*1000, 'E4_HEADER')
        need(struct.unpack_from('<H',frame,len(frame)-2)[0] ==
             binascii.crc_hqx(frame[2:-2],0xffff), 'E4_CRC')
        payload = frame[12:-2]; need(payload[0] == 2, 'E4_REVISION')
        frame_session = struct.unpack_from('<I',payload,5)[0]
        need(session is None or session == frame_session, 'FOUR_FRAME_SESSION'); session = frame_session
        decoded = trace_candidate.decode_payload(bytes([1])+payload[1:],
                      dict(session=session,config_epoch=1,e=0))
        point = decoded['points'][0]
        need(decoded == declared and decoded['channel'] == lane and decoded['count'] == 1
             and point['index'] == source_seq and point['value'] == counts[lane]
             and point['tick_ms'] == stamp and point['source_tick_ms'] ==
             (result['em_tick_ms']*1000 if counts[lane] is not None else None), 'RAW_E4_SOURCE')
        need(point['valid'] == (counts[lane] is not None) and not point['saturated']
             and not point['held'] and not point['source_fault'], 'E4_FRESH_QUALITY')
        need(row['error'] == row['refusal'] == 0 and row['rx_end'] == row['rx_before']+size
             and (previous is None or (row['id'] == previous['id']+1 and
                                      row['rx_before'] == previous['rx_end'])), 'E4_ROW_CONTINUITY')
        previous = row
    need(cursor == len(wire), 'EXACT_FOUR_FRAMES')
    return dict(board_sense_seq=r['request_seq'], board_receipt_sha256=digest(r),
        board_frame_sha256=hashlib.sha256(wire).hexdigest(), source_record_sha256=digest(source))


class PcDirectClient(NativeClient):
    """Explicit PC-only schema; never manufactures an APPLY/PWM response."""
    def __init__(self, connected_socket, token, *, world_epoch, **kwargs):
        self.world_epoch = _label(world_epoch)
        self.observation = None; self.observations = {}; self.pc_seq = 0; self.last_pc_command = None
        self.last_accepted_pc_command = None
        self.last_pc_rejection = None
        super().__init__(connected_socket, token, **kwargs)

    def _validate_state(self, state):
        need(type(state) is dict and EXTRA_STATE <= state.keys(), 'PC_STATE_EXTENSION')
        NativeClient._validate_state({k:v for k,v in state.items() if k not in EXTRA_STATE})
        need(state['admission_mode'] == 'PC_DIRECT' and state['action_source'] == 'pc_direct_host'
             and state['world_epoch'] == self.world_epoch, 'IMMUTABLE_PC_MODE_EPOCH')
        witness = state['source_witness']
        need(type(witness) is str and len(witness) == 32 and
             all(c in '0123456789abcdef' for c in witness), 'NATIVE_SOURCE_WITNESS')
        need(_native_uint(state['board_request_seq']) == 0 and
             state['board_receipt_sha256'] == '', 'DIRECT_IS_NOT_BOARD_OUTPUT')
        obs = _native_uint(state['board_observation_seq']); pc = _native_uint(state['pc_command_seq'])
        tick(state['observation_native_tick_usec'])
        for key in ('board_observation_sha256','source_record_sha256'):
            if obs: hex64(state[key])
            else: need(state[key] == '', 'UNOBSERVED_STATE_HASH')
        if pc: hex64(state['pc_command_sha256'])
        else: need(state['pc_command_sha256'] == '', 'UNCOMMANDED_STATE_HASH')

    def observe_pc(self, snapshot, source_payload, actual_sense, *, source_seq):
        need(self.board_binding is not None, 'REAL_INIT_BINDING_REQUIRED')
        self._validate_state(snapshot['native'])
        source = copy.deepcopy(source_payload); original = snapshot['native']
        at = tick(source['at_qpc_ns']); now = self.clock()
        need(original['ready'] is True and not original['fault'] and
             source['world_epoch'] == self.world_epoch and
             source['segment_id'] == 'native-'+original['revision'] and
             at == snapshot['host']['accepted_tick_qpc_interval_ns'][0] and
             source['position_m'] == original['position_m'] and
             source['orientation_xyzw'] == original['orientation_xyzw'] and
             source['speed_m_s'] == original['speed_m_s'], 'ORIGINAL_NATIVE_SOURCE_SNAPSHOT')
        need(at <= tick(source['completed_qpc_ns']) <= actual_sense['host_before_ns'] <=
             actual_sense['host_returned_ns'] <= now and now-at < SOURCE_AGE_NS,
             'ORIGINAL_ACQUISITION_FAST_AGE')
        refs = verify_e4(source, actual_sense, binding=self.board_binding, source_seq=source_seq)
        need(self.observation is None or refs['board_sense_seq'] > self.observation['board_sense_seq'],
             'INCREASING_BOARD_SENSE')
        fields = dict(world_epoch=self.world_epoch,source_witness=original['source_witness'],
            **refs,source_acquisition_qpc_ns=source['at_qpc_ns'],source_segment_id=source['segment_id'],
            source_position_m=source['position_m'],source_orientation_xyzw=source['orientation_xyzw'],
            board_binding=dict(self.board_binding))
        response = self._exchange('observe_pc', **fields); state = response['state']
        try:
            need(_native_uint(state['board_observation_seq']) == refs['board_sense_seq'] and
                 state['board_observation_sha256'] == refs['board_receipt_sha256'] and
                 state['source_record_sha256'] == refs['source_record_sha256'] and
                 state['observation_native_tick_usec'] == original['tick_usec'], 'OBSERVATION_NATIVE_CORRELATION')
        except BaseException: self.broken = True; raise
        self.observation = dict(refs,source=source,native_tick_usec=original['tick_usec'])
        self.observations = {seq:item for seq,item in self.observations.items()
            if now-tick(item['source']['at_qpc_ns']) < SOURCE_AGE_NS}
        self.observations[refs['board_sense_seq']] = self.observation
        return response

    def _admission_headroom(self, native_deadline_usec, now):
        """Conservative native-now upper bound plus the last actual RPC RTT.

        RTT is scheduling headroom, not a guarantee about the next request.
        Native still independently refuses a late request without applying it.
        """
        bracket = self.bracket
        uint(now, bracket.receive_qpc_ns)
        rtt = bracket.receive_qpc_ns-bracket.send_qpc_ns
        future = now+rtt
        native_upper_ns = (future+bracket.offset_max_ns+
                           bracket._drift(future-bracket.send_qpc_ns))
        return native_deadline_usec*1000 > native_upper_ns+NATIVE_ADMISSION_MARGIN_NS

    def _accepted_unchanged_and_active(self, state):
        accepted = self.last_accepted_pc_command
        need(accepted is not None, 'ORIGINAL_ACCEPTED_PC_COMMAND_REQUIRED')
        self._validate_state(state)
        target = accepted['target']
        need(_native_uint(state['pc_command_seq']) == accepted['command']['command_seq'] and
             state['pc_command_sha256'] == accepted['command_sha256'] and
             state['deadline_usec'] == accepted['native_deadline_usec'] and
             state['target_speed_m_s'] == target['speed_m_s'] and
             state['yaw_curvature_per_m'] == target['yaw_curvature_per_m'] and
             state['pitch_curvature_per_m'] == target['pitch_curvature_per_m'] and
             state['ready'] is True and state['running'] is True and not state['fault'] and
             tick(state['read_now_usec']) < tick(state['deadline_usec']),
             'ORIGINAL_ACCEPTED_PC_COMMAND_NOT_LIVE_UNCHANGED')

    def apply_advice(self, advice, current, command, *, ttl_ms=3000, paused=False,
                     operator_cap_m_s=.25, attempt_callback=None):
        need(type(paused) is bool and self.observation is not None and self.bracket is not None,
             'ADMITTED_REAL_OBSERVATION_REQUIRED')
        ttl_ms = uint(ttl_ms, 1, TTL_MAX_MS); now = self.clock()
        self._validate_state(current['native'])
        need(advice_applicable(advice,current,self.world_epoch,now), 'ORIGINAL_ADVICE_INAPPLICABLE')
        matches = [item for item in self.observations.values()
            if item['source']['at_qpc_ns'] == advice['source_acquisition_qpc_ns'] and
               item['source_record_sha256'] == advice['source_record_sha256'] and
               item['board_frame_sha256'] == advice['board_frame_sha256']]
        need(len(matches) == 1, 'ORIGINAL_REGISTERED_AI_OBSERVATION')
        obs = matches[0]; source = obs['source']
        need(advice['source_acquisition_qpc_ns'] == source['at_qpc_ns'] and
             advice['segment_id'] == source['segment_id'] and
             advice['board_frame_sha256'] == obs['board_frame_sha256'] and
             advice['source_record_sha256'] == obs['source_record_sha256'] and
             advice['source_pose'] == {k:source[k] for k in
                                     ('position_m','orientation_xyzw','speed_m_s')}, 'AI_REAL_SOURCE_BINDING')
        speed = uint(command['speed_code'], 0, 20)
        yaw,pitch = command['yaw_q'],command['pitch_q']
        mapped = validate('fast_9600',speed,yaw,pitch)
        need(type(operator_cap_m_s) in (int,float) and math.isfinite(operator_cap_m_s)
             and 0 <= operator_cap_m_s <= .25 and mapped.target_speed_m_s <= operator_cap_m_s,
             'TARGET_WITHIN_LATCHED_INITIAL_OR_MODE_CAP')
        need(not paused or speed == yaw == pitch == 0, 'PAUSE_ZERO_HOST_TARGET')
        if speed:
            need(advice['status'] == 'ADVISE' and mapped.target_speed_m_s <= advice['speed_limit_m_s'],
                 'TARGET_WITHIN_ACTUAL_AI_LIMIT')
        need(attempt_callback is None or callable(attempt_callback), 'ATTEMPT_CALLBACK')
        next_seq = uint(self.pc_seq+1,1,(1 << 53)-1)
        deadline = min(now+ttl_ms*1_000_000,tick(source['at_qpc_ns'])+SOURCE_AGE_NS)
        try:
            native_end = self.bracket.conservative_native_deadline_usec(deadline)
        except ValueError as error:
            if str(error) != 'NO_CONSERVATIVE_GRANT_REMAINS': raise
            return dict(deferred=True,reason='pc_preflight_headroom',state=copy.deepcopy(current['native']))
        if not self._admission_headroom(native_end,self.clock()):
            return dict(deferred=True,reason='pc_preflight_headroom',state=copy.deepcopy(current['native']))
        doc = dict(abi=COMMAND_ABI,mode='PC_DIRECT',world_epoch=self.world_epoch,profile='fast_9600',
            command_seq=next_seq,first_send_qpc_ns=str(now),source_acquisition_qpc_ns=source['at_qpc_ns'],
            **{k:obs[k] for k in ('board_sense_seq','board_receipt_sha256','board_frame_sha256','source_record_sha256')},
            ai_result_sha256=digest(advice),speed_code=speed,yaw_q=yaw,pitch_q=pitch,
            ttl_ms=ttl_ms,native_deadline_usec=str(native_end))
        command_bytes = canonical(doc); need(command_bytes.isascii(), 'CANONICAL_ASCII_COMMAND')
        attempt = dict(command=doc,command_json=command_bytes.decode('ascii'),
            command_sha256=hashlib.sha256(command_bytes).hexdigest(),host_deadline_qpc_ns=deadline)
        if attempt_callback is not None: attempt_callback(copy.deepcopy(attempt))
        # A slow intent logger cannot consume a sequence or create a late send.
        if not self._admission_headroom(native_end,self.clock()):
            return dict(deferred=True,reason='pc_preflight_headroom',state=copy.deepcopy(current['native']))
        self.pc_seq = next_seq
        self.last_pc_command = attempt
        self.last_pc_rejection = None
        try:
            response = self._exchange('pause_pc_direct' if paused else 'apply_pc_direct',
                command_json=attempt['command_json'],command_sha256=attempt['command_sha256'])
        except NativeRejected as error:
            self.last_pc_rejection = copy.deepcopy(error.response)
            if (error.response.get('reason') != 'pc_admission_headroom' or
                    error.response.get('admission_applied') is not False or
                    self.last_accepted_pc_command is None): raise
            self._accepted_unchanged_and_active(error.response.get('state'))
            return dict(deferred=True,reason='pc_admission_headroom',
                        state=copy.deepcopy(error.response['state']))
        s = response['state']
        try:
            need(_native_uint(s['pc_command_seq']) == self.pc_seq and
                 s['pc_command_sha256'] == self.last_pc_command['command_sha256'] and
                 tick(s['deadline_usec']) <= native_end and tick(s['deadline_usec']) > tick(s['read_now_usec']) and
                 s['target_speed_m_s'] == mapped.target_speed_m_s and
                 abs(s['yaw_curvature_per_m']-mapped.curvature_yaw_per_m) < 1e-12 and
                 abs(s['pitch_curvature_per_m']-mapped.curvature_pitch_per_m) < 1e-12,
                 'EXECUTABLE_PC_RECEIPT_CORRELATION')
        except BaseException: self.broken = True; raise
        self.last_accepted_pc_command = copy.deepcopy(attempt)
        self.last_accepted_pc_command.update(native_deadline_usec=s['deadline_usec'],target=dict(
            speed_m_s=s['target_speed_m_s'],yaw_curvature_per_m=s['yaw_curvature_per_m'],
            pitch_curvature_per_m=s['pitch_curvature_per_m']))
        return response

    def apply_pwm(self, *args, **kwargs):
        raise ValueError('PC_DIRECT_NEVER_BOARD_APPLY')

    def pause(self, *args, **kwargs):
        raise ValueError('PC_DIRECT_REQUIRES_REAL_HOST_ZERO_COMMAND')

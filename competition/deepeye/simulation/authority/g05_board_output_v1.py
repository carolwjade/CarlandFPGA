"""Explicit G05 50 MHz measured-output mode; pure parsing grants no authority.

Layout source: deepeye_g05_axi_50mhz_candidate.sv SHA256
99cdb09399466966458343351d0d941191f34cc9af6f9808c5fb3cc58086ea5a.
Words 3..5 are submitted echoes. Only captured PWM highs 15..17 supply
yaw/pitch/speed. The original channel must separately admit the actual APPLY.
Legacy topology 2 is a host-envelope compatibility encoding in this mode;
it does not claim PC_DIRECT or UART HIL hardware evidence.
"""
from dataclasses import dataclass

MODE = 'G05_CSR_BOARD_OUTPUT'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class G05BoardOutputPolicyV1:
    consume_window_ns: int

    def check(self):
        _need(type(self) is G05BoardOutputPolicyV1 and
              type(self.consume_window_ns) is int and
              1 <= self.consume_window_ns <= 5_000_000_000,
              'strict bounded G05 board-output consume window required')


def check_mode_selection(board_policy, pc_direct_policy, csr_policy):
    if board_policy is not None:
        _need(type(board_policy) is G05BoardOutputPolicyV1,
              'exact board-output policy required')
        board_policy.check()
        _need(pc_direct_policy is None and csr_policy is not None,
              'board output requires G05 CSR and excludes PC_DIRECT policy')


def decode_board_output(words, command_words, *, session, build_id=None):
    """Decode actual measured PWM; reject wrong/torn/echo-only captures.

    This is a consistency parser, never evidence that hardware ran. All local
    start/end witnesses are relative counters, never host or board timestamps.
    """
    from ...tools.diagnostic.functional50_g05_a import _command
    _need(type(words) is list and len(words) == 32 and
          all(type(v) is int and 0 <= v <= 0xffffffff for v in words),
          'complete unsigned 32-word G05 output capture required')
    _command(command_words, 0, None, build_id=build_id)
    yaw, pitch, profile, speed, ttl, seq, tag = command_words
    _need(type(session) is int and 1 <= session <= 0xffffffff and
          words[0] > 0 and words[1:3] == [seq, tag] and
          words[30:] == [session, 0x47303550],
          'actual output command/session identity mismatch')
    _need(words[3:6] == [(speed << 8) | profile, (pitch << 16) | yaw, ttl],
          'submitted echo does not match original APPLY request')
    u64 = lambda at: words[at] | (words[at + 1] << 32)
    applied, deadline, result = u64(6), u64(8), u64(10)
    _need(applied < result < deadline and deadline - applied == ttl * 50000,
          'actual 50 MHz output lifetime mismatch')
    starts, ends = [u64(18 + 2*i) for i in range(3)], [u64(24 + 2*i) for i in range(3)]
    for lane, (period, high, start, end) in enumerate(zip(words[12:15], words[15:18], starts, ends)):
        _need(abs(period - 1000000) <= 1 and 0 < high < period and
              0 < start < end <= 0xffffffff and end - start == period,
              'actual PWM period/local capture witness mismatch')
    _need(max(starts) - min(starts) <= 1 and max(ends) - min(ends) <= 1,
          'actual three-lane output capture is incoherent')
    decoded = []
    for measured, origin, step in zip(words[15:18], (125000,125000,25000), (8,8,500)):
        code = (measured - origin + step // 2) // step
        _need(abs(measured - (origin + step * code)) <= 1,
              'measured PWM output is outside one-tick encoding tolerance')
        decoded.append(code)
    y, p, s = decoded
    signed = lambda v: v if v < 0x8000 else v - 0x10000
    _need((y,p,s) == (signed(yaw),signed(pitch),speed) and s > 0,
          'measured output differs from original command or is STOP')
    return dict(action=1,yaw_q=y,pitch_q=p,speed_code=s,duration_ms=ttl)

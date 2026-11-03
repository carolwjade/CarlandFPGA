"""Joint-build per-command TTL syntax capability; import is inert.

This proves only reviewed12000ms command support, with no mission duration/count
quota. It grants no device access, UART ownership, motor release or acceptance.
The original G05 helper and measured-output decoder remain byte-identical.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading

REQUIREMENTS_SHA256 = '2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
REVIEW1039_SHA256 = 'beb8c519ec26998d03a6393a358e9dbe253d86d640de1cc2babf1ff3ee7fedf9'
_KEY = object()
_ROM = ((0,128234,512938,1154111,2051753,3205865,4616446,6283496,8207015,10387004,12823462,15516389,18465785,21671651,25133986,28852790,32828063,37059806,41548017,46292698,51293849),
        (0,8,32,73,131,205,295,402,525,664,820,993,1181,1386,1608,1846,2100,2371,2659,2962,3282))
RTL_PINS = {
    'fpga/diagnostic/g05_capture/additive50_source_candidate/rtl/deepeye_g05_command_map_50mhz.sv': '18639b1a2c0d6e5d3a4dafaf4a597f52347b5730b86c4fd368f5b896584b2c35',
    'fpga/diagnostic/g05_capture/additive50_source_candidate/rtl/deepeye_g05_profile_50mhz.sv': '34cbb7cbd214d75964f133a65c792552ac22a9838b40efe4dd6537667422f845',
    'fpga/diagnostic/g05_capture/additive50_source_candidate/rtl/deepeye_g05_curvature_rom_50mhz.svh': 'd462859e6893cd90fb33ad9ddd481aaa7ee46937ba3d197431f81b602357a83c',
}


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def _json(blob):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(blob, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def _hex(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'SHA256 required')
    return value


def _safe_path(value):
    path = Path(value)
    _need(path.is_absolute() and '..' not in path.parts, 'absolute non-link path required')
    for part in (path, *path.parents):
        _need(not part.is_symlink(), 'symlink path refused')
    return path


def _fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def read_pinned(path, expected, limit=1024 * 1024):
    path = _safe_path(path)
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
              0 < before.st_size <= limit, 'bounded single-link regular input required')
        blob = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    _need(len(blob) == before.st_size and
          _fingerprint(before) == _fingerprint(after) == _fingerprint(path.lstat()), 'input changed')
    _need(_sha(blob) == _hex(expected), 'input SHA256 mismatch ' + str(path))
    return blob, (str(path), _fingerprint(after))


@dataclass(frozen=True)
class _PerCommandCapability:
    _key: object
    binding: tuple
    proof: tuple
    watches: tuple
    owner: tuple


def issue_from_review(*, load_plan_path, load_plan_sha256, review_path, review_sha256,
                      build_plan_path, source_closure_path, rtl_root):
    """Read-only proof minting; actual device/run authority remains with Root."""
    _need(review_sha256 == REVIEW1039_SHA256, 'exact adopted actual1039 review required')
    watches = []
    def pinned(path, expected, limit=1024 * 1024):
        blob, identity = read_pinned(path, expected, limit)
        watches.append(identity)
        return blob
    review = _json(pinned(review_path, review_sha256))
    _need(review['schema'] == 'DEEPEYE-A-JOINT-BUILD-REVIEW-1039-v1' and
          review['status'] == 'same_run_build_ready_for_A_load_review' and
          review['requirements_sha256'] == REQUIREMENTS_SHA256 and
          review['original_RTL_sources_verified'] == 20 and review['uart_sources_verified'] == 3,
          'actual reviewed unchanged20 RTL proof required')
    plan = _json(pinned(load_plan_path, load_plan_sha256, 131072))
    from_plan_keys = {'operation_id','request_sha256','build_id','source_commit','boot_id',
                      'bit_path','hwh_path','mapping_path','bit_sha256','hwh_sha256',
                      'mapping_sha256','operation_parent','baseline_hwh_path','baseline_hwh_sha256'}
    _need(type(plan) is dict and set(plan) == from_plan_keys, 'exact14-key physical load plan required')
    body = dict(plan)
    request = body.pop('request_sha256')
    _need(_sha(_canonical(body)) == _hex(request), 'actual load request mismatch')
    _need(plan['build_id'] == review['build_id'] == review['hwh']['build_id'], 'actual reviewed build mismatch')
    for name in ('bit', 'hwh'):
        expected = review['artifacts']['functional50_diag.' + name]['sha256']
        _need(plan[name + '_sha256'] == expected, 'actual reviewed artifact mismatch ' + name)
        pinned(plan[name + '_path'], expected, 16 * 1024 * 1024)
    _need(plan['mapping_sha256'] == review['mapping_sha256'], 'actual reviewed mapping mismatch')
    pinned(plan['mapping_path'], plan['mapping_sha256'], 131072)
    build_plan = _json(pinned(build_plan_path, review['build_plan_sha256']))
    closure_blob = pinned(source_closure_path, build_plan['source_closure_sha256'])
    closure = _json(closure_blob)
    _need(build_plan['build_id'] == closure['build_id_hex128'] == plan['build_id'] and
          build_plan['original_20_RTL_unchanged'] is True and closure['prior_RTL_unmodified'] is True and
          closure['requirements_sha256'] == REQUIREMENTS_SHA256 and closure['clock_hz'] == 50000000,
          'same-build original20 source closure required')
    sources = closure['sources']
    _need(type(sources) is dict and len(sources) == 20, 'exact20 original RTL sources required')
    rtl_root = _safe_path(rtl_root)
    for name, expected in sources.items():
        relative = Path(name)
        _need(not relative.is_absolute() and '..' not in relative.parts, 'bounded RTL relative path required')
        _need(build_plan['frozen_inputs']['inputs/readonly_sources/' + name] == expected,
              'reviewed build plan/source closure mismatch')
        pinned(rtl_root / relative, expected, 2 * 1024 * 1024)
    for name, expected in RTL_PINS.items():
        _need(sources.get(name) == expected, 'reviewed12000ms mapper/profile/ROM pin required')
    binding = tuple(plan[key] for key in ('operation_id','request_sha256','boot_id','build_id',
                                         'bit_sha256','hwh_sha256','mapping_sha256')) + (review_sha256,)
    return _PerCommandCapability(_KEY, binding,
                                 (review['build_plan_sha256'], _sha(closure_blob), _sha(_canonical(sources))),
                                 tuple(watches), (os.getpid(), threading.get_ident()))


def validate_capability(capability, build_id):
    _need(type(capability) is _PerCommandCapability and capability._key is _KEY,
          'exact issued joint per-command capability required')
    _need(capability.owner == (os.getpid(), threading.get_ident()) and
          len(capability.binding) == 8 and capability.binding[3] == build_id and
          capability.binding[7] == REVIEW1039_SHA256 and len(capability.proof) == 3 and
          capability.watches, 'same-owner actual reviewed build capability required')
    for value in capability.proof:
        _hex(value)
    for name, identity in capability.watches:
        path = _safe_path(name)
        _need(_fingerprint(path.lstat()) == identity, 'reviewed capability input changed')
    return capability


def command_check(words, last_cmd, locked_profile, *, build_id=None, capability=None):
    """Original seven-word command guards; only long-TTL authority is replaced."""
    validate_capability(capability, build_id)
    _need(type(words) is tuple and len(words) == 7 and
          all(type(v) is int and 0 <= v <= 0xffffffff for v in words),
          'seven exact unsigned command words')
    y, p, profile, speed, ttl, seq, tag = words
    _need(y <= 0xffff and p <= 0xffff and profile in (1, 2) and speed <= 20 and
          1 <= ttl <= 12000, 'G05 encoding and profile')
    y = y if y < 0x8000 else y - 65536
    p = p if p < 0x8000 else p - 65536
    _need(-15000 <= y <= 15000 and -15000 <= p <= 15000 and
          (speed != 0 or (y == 0 and p == 0)), 'G05 target bounds')
    _need(y*y + p*p <= _ROM[profile-1][speed] and seq > last_cmd and
          (locked_profile is None or locked_profile == profile),
          'G05 curvature, sequence or locked profile')
    return words


def decode_board_output(words, command_words, *, session, build_id=None, capability=None):
    """Original measured PWM decoder, with the same explicit command capability."""
    _need(type(words) is list and len(words) == 32 and
          all(type(v) is int and 0 <= v <= 0xffffffff for v in words),
          'complete unsigned 32-word G05 output capture required')
    command_check(command_words, 0, None, build_id=build_id, capability=capability)
    yaw, pitch, profile, speed, ttl, seq, tag = command_words
    _need(type(session) is int and 1 <= session <= 0xffffffff and
          words[0] > 0 and words[1:3] == [seq, tag] and
          words[30:] == [session, 0x47303550], 'actual output command/session identity mismatch')
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
    return dict(action=1, yaw_q=y, pitch_q=p, speed_code=s, duration_ms=ttl)


def validate_identity13(words):
    _need(type(words) is tuple and len(words) == 13 and
          all(type(v) is int and 0 <= v <= 0xffffffff for v in words),
          '13 unsigned identity words required')
    _need(any(words[:8]) and any(words[8:12]) and words[12] != 0,
          'nonzero original run/nonce/session')
    return words

"""Root's explicitly flagged one-load CLI. Import is inert.

Load-only preparation: no G05 initialization, UART access, MCU frame, profile,
transfer grant, cleanup, reset or retry. The adopted loader alone changes PL and
FCLK0. Its operation records remain the source for the later independent reader.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import uuid
import xml.etree.ElementTree as ET

REQUIREMENTS_SHA256 = '2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
LOADER_SHA256 = '478ee99fa753f2050812c7aec5655ba286004b8262565a5304dad7c2dc8705c7'
VERIFIER_SHA256 = 'd8a96c5e6c277b8608b89e22bba49fae7425e331af79dfa2d9c14be437550a24'
HELPER_SHA256 = '865a857c2455a9cc0254db54eb7b8c71cb16f5416bb299b2711cd9151649268d'
BASELINE_SHA256 = '73a64f2d19e8d13c70af0150eef71bc3092825f95a8481ba0fb4e71ae55c2e5b'
PLAN_KEYS = {'operation_id', 'request_sha256', 'build_id', 'source_commit', 'boot_id',
             'bit_path', 'hwh_path', 'mapping_path', 'bit_sha256', 'hwh_sha256',
             'mapping_sha256', 'operation_parent', 'baseline_hwh_path', 'baseline_hwh_sha256'}
IP_NAMES = ('g05_50_0', 'trace50_0', 'mcu_uart')
TRACE_IDENTITIES = ((0x00, 0x54353046), (0x04, 1), (0x08, 4),
                    (0x0c, 50000000), (0x10, 1000000), (0x14, 4096))
G05_IDENTITIES = ((0x00, 0x47303550), (0x04, 2), (0x08, 0), (0x10, 0))


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
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None,
          'SHA256 required')
    return value


def _safe_path(value):
    _need(type(value) in (str, type(Path('.'))), 'path required')
    path = Path(value)
    _need(path.is_absolute() and '..' not in path.parts, 'absolute non-link path required')
    for part in (path, *path.parents):
        _need(not part.is_symlink(), 'symlink path refused')
    return path


def _fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _read_regular(value, limit):
    path = _safe_path(value)
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
              0 < before.st_size <= limit, 'bounded single-link regular file required')
        blob = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    _need(len(blob) == before.st_size and
          _fingerprint(before) == _fingerprint(after) == _fingerprint(path.lstat()),
          'file changed during read')
    return blob


def _pinned(value, limit, expected):
    blob = _read_regular(value, limit)
    _need(_sha(blob) == _hex(expected), 'pinned file hash mismatch ' + str(value))
    return blob


def _validate_plan(plan):
    """Pure exact14-key identity validation; no board access or authority grant."""
    _need(type(plan) is dict and set(plan) == PLAN_KEYS, 'exact14-key loader plan required')
    body = dict(plan)
    request = body.pop('request_sha256')
    _need(_sha(_canonical(body)) == _hex(request), 'approved request hash mismatch')
    _need(type(plan['operation_id']) is str and
          re.fullmatch('[A-Za-z0-9_-]{1,80}', plan['operation_id']) is not None, 'operation ID')
    _need(type(plan['build_id']) is str and re.fullmatch('[0-9a-f]{32}', plan['build_id']) is not None
          and int(plan['build_id'], 16) > 0, 'BUILD_ID')
    _need(type(plan['source_commit']) is str and
          re.fullmatch('[0-9a-f]{40}', plan['source_commit']) is not None, 'source commit')
    _need(type(plan['boot_id']) is str and str(uuid.UUID(plan['boot_id'])) == plan['boot_id'], 'BOOT UUID')
    for name in ('bit', 'hwh', 'mapping', 'baseline_hwh'):
        _safe_path(plan[name + '_path'])
        _hex(plan[name + '_sha256'])
    _need(plan['baseline_hwh_sha256'] == BASELINE_SHA256, 'baseline HWH pin required')
    parent = _safe_path(plan['operation_parent'])
    bit, hwh = Path(plan['bit_path']), Path(plan['hwh_path'])
    _need(bit.suffix == '.bit' and hwh.suffix == '.hwh' and
          bit.parent == hwh.parent and bit.stem == hwh.stem, 'same-name BIT/HWH required')
    return parent / plan['operation_id']


def _dependencies(stage):
    """Import only the pinned fresh staged loader/helper/verifier dependency set."""
    stage = _safe_path(stage)
    snapshot = stage / 'snapshot'
    helper_path = snapshot / 'competition/deepeye/tools/diagnostic/functional50_board_a.py'
    required = (
        ('load_once_joint50_1024', stage / 'load_once_joint50_1024.py', LOADER_SHA256),
        ('verify_uart_joint50_hwh', stage / 'verify_uart_joint50_hwh.py', VERIFIER_SHA256),
        ('competition.deepeye.tools.diagnostic.functional50_board_a', helper_path, HELPER_SHA256),
    )
    for name, path, expected in required:
        _pinned(path, 1024 * 1024, expected)
        prior = sys.modules.get(name)
        if prior is not None:
            _need(Path(prior.__file__) == path, 'preloaded dependency path mismatch ' + name)
    for count in range(1, 5):
        parts = ('competition', 'deepeye', 'tools', 'diagnostic')[:count]
        directory = snapshot.joinpath(*parts)
        _need(directory.is_dir() and not (directory / '__init__.py').exists(),
              'fresh snapshot namespace packages required')
        prior = sys.modules.get('.'.join(parts))
        if prior is not None:
            _need(list(prior.__path__) == [str(directory)], 'preloaded snapshot namespace mismatch')
    sys.path[:0] = [str(stage), str(snapshot)]
    modules = {}
    for name, path, expected in required:
        module = importlib.import_module(name)
        _need(Path(module.__file__) == path, 'fresh staged imported source path required ' + name)
        _pinned(module.__file__, 1024 * 1024, expected)
        modules[name] = module
    return modules[required[0][0]], modules[required[2][0]]


def _clock(value):
    _need(type(value) is dict and set(value) == {'source', 'pll_fdiv', 'div0', 'div1', 'other'},
          'exact PS clock fields required')
    names = ('source', 'pll_fdiv', 'div0', 'div1')
    _need(all(type(value[key]) is int for key in names) and
          [value[key] for key in names] == [0, 20, 10, 2], 'actual PS 50MHz clock mismatch')
    _need(type(value['other']) in (tuple, list) and len(value['other']) == 3 and
          all(type(item) is int and 0 <= item <= 0xffffffff for item in value['other']),
          'three bounded other PS clocks required')
    return {**{key: value[key] for key in names}, 'other': list(value['other'])}


def _csr_read(mmio, offsets):
    result = {}
    for offset in offsets:
        value = int(mmio.read(offset))
        _need(0 <= value <= 0xffffffff, 'CSR word outside uint32')
        result['0x%02x' % offset] = value
    return result


def _validate_csr(trace, g05, build_id):
    """Pure validation of the bounded measured raw CSR dictionaries."""
    trace_keys = {'0x%02x' % offset for offset, _ in TRACE_IDENTITIES} | {
        '0x%02x' % (0x60 + 4 * index) for index in range(4)}
    g05_keys = {'0x%02x' % offset for offset, _ in G05_IDENTITIES}
    _need(type(trace) is dict and set(trace) == trace_keys and
          type(g05) is dict and set(g05) == g05_keys, 'exact bounded raw CSR fields required')
    _need(all(type(value) is int and 0 <= value <= 0xffffffff
              for value in (*trace.values(), *g05.values())), 'plain uint32 CSR values required')
    for offset, wanted in TRACE_IDENTITIES:
        _need(trace['0x%02x' % offset] == wanted, 'actual TRACE identity mismatch')
    for offset, wanted in G05_IDENTITIES:
        _need(g05['0x%02x' % offset] == wanted, 'fresh G05 identity/OFF/status/fault mismatch')
    actual_build = ''.join('%08x' % trace['0x%02x' % (0x60 + 4 * index)] for index in reversed(range(4)))
    _need(actual_build == build_id, 'actual TRACE BUILD_ID mismatch')
    return actual_build


def _hwh_context(blob, helper):
    _need(type(blob) is bytes and 0 < len(blob) <= 8 * 1024 * 1024 and b'\x00' not in blob and
          not re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', blob, re.I), 'bounded plain HWH required')
    root = ET.fromstring(blob)
    def module(name):
        return helper._one((item for item in root.findall('./MODULES/MODULE')
                            if item.get('INSTANCE') == name), name)
    def port(obj, name):
        return helper._one((item for item in obj.findall('./PORTS/PORT')
                            if item.get('NAME') == name), name)
    g05, trace, uart = (module(name) for name in IP_NAMES)
    clock_net = port(g05, 's_axi_aclk').get('SIGNAME')
    reset_net = port(g05, 's_axi_aresetn').get('SIGNAME')
    _need(clock_net and reset_net, 'actual product clock/reset nets required')
    for obj in (g05, trace, uart):
        clock, reset = port(obj, 's_axi_aclk'), port(obj, 's_axi_aresetn')
        _need(clock.get('SIGNAME') == clock_net and reset.get('SIGNAME') == reset_net and
              reset.get('POLARITY') == 'ACTIVE_LOW', 'actual shared50MHz/active-low reset required')
    params = helper._params(uart)
    _need(helper._integer(params['C_S_AXI_ACLK_FREQ_HZ']) ==
          helper._integer(port(uart, 's_axi_aclk').get('CLKFREQUENCY')) == 50000000 and
          helper._integer(params['C_BAUDRATE']) == 115200 and
          helper._integer(params['C_DATA_BITS']) == 8 and
          helper._integer(params['C_USE_PARITY']) == 0 and
          helper._integer(params['C_ODD_PARITY']) == 0, 'actual UART50MHz1152008N1 mismatch')
    return dict(product_clock_net=clock_net, product_reset_net=reset_net,
                uart=dict(clock_hz=50000000, baud=115200, data_bits=8, parity=False,
                          stop_bits=1, clock_net=clock_net, reset_net=reset_net))


def run_load(*, allow_board_load=False, plan_path, plan_sha256):
    _need(allow_board_load is True, 'explicit --allow-board-load is required')
    _need(os.name == 'posix' and os.geteuid() == 0 and os.uname().machine == 'armv7l',
          'actual root armv7l PS required')
    plan_path = _safe_path(plan_path)
    plan_blob = _pinned(plan_path, 131072, plan_sha256)
    plan = _json(plan_blob)
    operation = _validate_plan(plan)
    _need(not operation.exists(), 'operation exists; never replay a started or uncertain load')
    _need(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == plan['boot_id'], 'current BOOT mismatch')
    stage = _safe_path(Path(__file__).parent)
    entry_blob = _read_regular(Path(__file__), 1024 * 1024)
    loader, helper = _dependencies(stage)
    mapping = _json(_pinned(plan['mapping_path'], 131072, plan['mapping_sha256']))
    _pinned(plan['bit_path'], 16 * 1024 * 1024, plan['bit_sha256'])
    _pinned(plan['hwh_path'], 8 * 1024 * 1024, plan['hwh_sha256'])
    _pinned(plan['baseline_hwh_path'], 8 * 1024 * 1024, BASELINE_SHA256)
    before_descriptors = loader.validated_joint_descriptors(
        plan['hwh_path'], mapping, plan['build_id'], plan['baseline_hwh_path'])
    _need(_pinned(plan_path, 131072, plan_sha256) == plan_blob, 'approved plan changed before load')
    load_attempted = False
    try:
        load_attempted = True
        returned = loader.open_stream_from_plan(plan_path)
        _need(type(returned) is tuple and len(returned) == 3, 'original loader three-tuple required')
        trace_mmio, g05_mmio, returned_plan = returned
        _need(type(returned_plan) is dict and _canonical(returned_plan) == _canonical(plan),
              'loader returned different approved plan')
        from pynq import Clocks, Device
        _need(Clocks._instance._slcr_mmio.device is Device.active_device, 'actual PS clock device mismatch')
        current_boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        _need(current_boot == plan['boot_id'], 'postload current BOOT mismatch')
        clock_record = _clock(_json(_read_regular(operation / 'clock-readback.json', 131072)))
        actual_clock = _clock(helper._ps(Clocks))
        _need(actual_clock == clock_record, 'actual postload PS clocks differ from loader record')
        write_record = _json(_read_regular(operation / 'clock-write-started.json', 131072))
        _need(type(write_record) is dict and set(write_record) == {'fclk', 'div0', 'div1', 'before'} and
              [write_record[key] for key in ('fclk', 'div0', 'div1')] == [0, 10, 2] and
              type(write_record['before']) is dict and
              actual_clock['other'] == write_record['before']['other'], 'other PS clocks changed')
        load_returned = _json(_read_regular(operation / 'load-returned.json', 131072))
        _need(type(load_returned) is dict and set(load_returned) == {'monotonic_ns'} and
              type(load_returned['monotonic_ns']) is int and load_returned['monotonic_ns'] > 0,
              'actual load-returned record required')
        stem = 'functional50_' + plan['request_sha256'][:24]
        operation_hwh = operation / (stem + '.hwh')
        hwh_blob = _pinned(operation_hwh, 8 * 1024 * 1024, plan['hwh_sha256'])
        _pinned(operation / (stem + '.bit'), 16 * 1024 * 1024, plan['bit_sha256'])
        _need(_pinned(plan_path, 131072, plan_sha256) == plan_blob, 'approved plan changed after load')
        actual_descriptors = loader.validated_joint_descriptors(
            operation_hwh, mapping, plan['build_id'], plan['baseline_hwh_path'])
        _need(actual_descriptors == before_descriptors and
              actual_descriptors['hwh_sha256'] == plan['hwh_sha256'] and
              tuple(item['instance'] for item in actual_descriptors['windows']) == IP_NAMES,
              'actual operation HWH three-IP descriptor mismatch')
        context = _hwh_context(hwh_blob, helper)
        trace_raw = _csr_read(trace_mmio, [offset for offset, _ in TRACE_IDENTITIES] +
                              [0x60 + 4 * index for index in range(4)])
        g05_raw = _csr_read(g05_mmio, [offset for offset, _ in G05_IDENTITIES])
        actual_build = _validate_csr(trace_raw, g05_raw, plan['build_id'])
        _need(_clock(helper._ps(Clocks)) == actual_clock and
              Path('/proc/sys/kernel/random/boot_id').read_text().strip() == current_boot,
              'BOOT/PS changed during bounded readback')
        _need(_read_regular(Path(__file__), 1024 * 1024) == entry_blob, 'entry source changed during load')
        snapshot = dict(
            schema='DEEPEYE-ACTUAL-LOADED-SNAPSHOT-1037-v1',
            evidence_kind='measured_load_snapshot_only',
            contract='DEEPEYE-HUMAN-LOCK-20261014/revision2', requirements_sha256=REQUIREMENTS_SHA256,
            operation_id=plan['operation_id'], request_sha256=plan['request_sha256'],
            approved_plan_sha256=plan_sha256, source_commit=plan['source_commit'],
            boot_id=current_boot, build_id=actual_build, operation_directory=str(operation),
            bit_sha256=plan['bit_sha256'], hwh_sha256=_sha(hwh_blob),
            mapping_sha256=plan['mapping_sha256'], baseline_hwh_sha256=BASELINE_SHA256,
            operation_hwh_path=str(operation_hwh), actual_ps_clock=actual_clock,
            fclk_hz=50000000 * actual_clock['pll_fdiv'] // (actual_clock['div0'] * actual_clock['div1']),
            raw_csr=dict(trace=trace_raw, g05=g05_raw),
            ips=[dict(item) for item in actual_descriptors['windows']], **context,
            load_returned_monotonic_ns=load_returned['monotonic_ns'],
            measured_monotonic_ns=time.monotonic_ns(), pid=os.getpid(),
            loader_sha256=LOADER_SHA256, verifier_sha256=VERIFIER_SHA256,
            entry_sha256=_sha(entry_blob),
            G05_off=True, UART_accessed=False, MCU_frame_sent=False,
            self_grants_profile=False, grants_B_transfer=False,
            G03='not_run', R03='not_run', all29='not_run')
        _need(len(_canonical(snapshot)) <= 65536, 'bounded actual snapshot required')
        helper._record(operation, 'actual_loaded_snapshot.json', snapshot)
        return snapshot
    except BaseException as error:
        if load_attempted and operation.is_dir():
            try:
                helper._record(operation, 'actual-load-snapshot-failed.json', dict(
                    operation_id=plan['operation_id'], request_sha256=plan['request_sha256'],
                    error_type=type(error).__name__, message=str(error)[:2048],
                    load_may_have_happened=True, automatic_retry=False,
                    cleanup_performed=False, monotonic_ns=time.monotonic_ns()))
            except BaseException:
                pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-board-load', action='store_true')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args(argv)
    if not args.allow_board_load:
        parser.error('--allow-board-load is required; no load was attempted')
    try:
        snapshot = run_load(allow_board_load=args.allow_board_load, plan_path=args.plan,
                            plan_sha256=args.plan_sha256)
    except Exception as error:
        print(json.dumps(dict(status='load_or_snapshot_failed_do_not_replay',
                              error_type=type(error).__name__, message=str(error)[:2048],
                              automatic_retry=False), sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(snapshot, sort_keys=True, separators=(',', ':'), allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

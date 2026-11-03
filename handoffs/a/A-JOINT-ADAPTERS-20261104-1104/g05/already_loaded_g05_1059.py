"""Explicit Root-only G05/TRACE stream on an already-loaded joint product.

Import has no effects. The unchanged791 LiveBoard owns control/capture and the
original stream ABI. This entry never calls its loading main, any loader, UART,
Overlay, clock setter or recovery/reset path. A terminal run is not reopened.
"""
import argparse
from contextlib import redirect_stdout
from dataclasses import asdict
import importlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time

REQUIREMENTS_SHA256 = '2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
SOURCE_PINS = {
    'diagnostic_stdio1041.py': 'f459d18bda342267dd9d239067af52bf2665c16e6df9a11f8ac31681c66ee676',
    'remote_live_board_a.py': 'afd0bbafc36b4a51dddc417d6af5a53610e46e63138d6cbf0a3f7090d258e7b0',
    'root_loaded_product1031.py': 'd3be22472808418cc9fef164fe8ca3021987b84ecde1cef9261568155e6da57b',
    'snapshot/competition/deepeye/golden/codec/trace_candidate.py': 'a489ac34b49976532803b34f006f8bc24103548f34ddd55cc2ecaedc529a9642',
    'snapshot/competition/deepeye/tools/diagnostic/functional50_g05_a.py': 'c599b70f5870feee2fdd2964ff2d1a172457fb285865d14a5c1a3e89639aa4e4',
    'snapshot/competition/deepeye/simulation/authority/g05_board_output_v1.py': 'e2f44030ab996819c1516f4a568b4b53febcb1b28bf8338f05961ff80b087805',
}
CONFIG_KEYS = {'schema','requirements_sha256','approved_plan_path','approved_plan_sha256',
               'operation_directory','build_review_path','build_review_sha256','build_plan_path',
               'source_closure_path','rtl_root','identity_path','identity_sha256','run_id',
               'world_epoch','source_pins'}
NEW_SOURCES = {'already_loaded_g05_1059.py', 'joint_command_ttl1059.py'}


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _validate_config(config):
    _need(type(config) is dict and set(config) == CONFIG_KEYS, 'exact Root run config fields required')
    _need(config['schema'] == 'DEEPEYE-ALREADY-LOADED-G05-RUN-1059-v1' and
          config['requirements_sha256'] == REQUIREMENTS_SHA256, 'revision2 run config required')
    _need(type(config['run_id']) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}', config['run_id']) is not None,
          'fresh bounded G05 run ID required')
    _need(type(config['world_epoch']) is int and 1 <= config['world_epoch'] <= 0xffffffff,
          'actual positive world epoch required')
    _need(type(config['source_pins']) is dict and set(config['source_pins']) == NEW_SOURCES,
          'exact Root-reviewed new source pins required')
    return config


def _bootstrap(stage):
    """Pin before importing the already-adopted read-only API bootstrap."""
    import hashlib
    import importlib.util
    import stat
    for relative, expected in SOURCE_PINS.items():
        path = stage / relative
        _need(path.is_absolute() and '..' not in path.parts, 'absolute fresh stage required')
        for part in (path, *path.parents):
            _need(not part.is_symlink(), 'stage symlink refused')
        with path.open('rb') as stream:
            before = os.fstat(stream.fileno())
            _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
                  0 < before.st_size <= 2 * 1024 * 1024, 'bounded staged source required')
            blob = stream.read(2 * 1024 * 1024 + 1)
            after = os.fstat(stream.fileno())
        fields = lambda value: (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns,value.st_mode,value.st_nlink)
        _need(fields(before) == fields(after) == fields(path.lstat()) and len(blob) == before.st_size and
              hashlib.sha256(blob).hexdigest() == expected, 'staged source pin mismatch ' + relative)
    spec = importlib.util.spec_from_file_location('g05_root_bootstrap1041', stage / 'diagnostic_stdio1041.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _IdentityJournal:
    """Keep original events intact while attaching immutable physical/run IDs."""
    def __init__(self, journal, context):
        self.journal, self.context = journal, context
        self.stop_unknown = False

    def record(self, event, durable=False):
        _need(type(event) is dict and 'joint_run' not in event, 'original journal event required')
        if event.get('event') in ('terminal-stop-unknown', 'terminal-stop-not-attempted-identity-unknown'):
            self.stop_unknown = True
        self.journal.record(dict(event, joint_run=self.context), durable)


def _run_loaded(config, stage, protocol_in, protocol_out, config_watch):
    bootstrap = _bootstrap(stage)
    for relative, expected in config['source_pins'].items():
        bootstrap._read_pinned(stage / relative, expected, 2 * 1024 * 1024)
    sys.path[:0] = [str(stage), str(stage / 'snapshot')]
    joint = importlib.import_module('joint_command_ttl1059')
    live = importlib.import_module('remote_live_board_a')
    for module, name in ((joint, 'joint_command_ttl1059.py'), (live, 'remote_live_board_a.py')):
        _need(Path(module.__file__) == stage / name, 'fresh staged live module required')
    # Only this adopted bootstrap's imports/readonly factory are used. No UART
    # authorization, service attach, original791 main or loader is invoked.
    service_api, unused_stdio_api, reader_api = bootstrap._load_apis(stage)
    root = reader_api.build_actual_reader(
        service_api, approved_plan_path=Path(config['approved_plan_path']),
        approved_plan_sha256=config['approved_plan_sha256'],
        actual_operation_directory=Path(config['operation_directory']),
        transfer_review_path=Path(config['build_review_path']),
        transfer_review_sha256=config['build_review_sha256'])
    actual = root.read_current()
    _need(root.simulation is False and root._authorized is None and root._uart_mmio is None,
          'read-only actual physical parent required')
    _need(root._trace.device is root._device and root._g05.device is root._device and
          root._clocks._instance._slcr_mmio.device is root._device,
          'one actual parent Device for G05/TRACE required')
    capability = joint.issue_from_review(
        load_plan_path=config['approved_plan_path'], load_plan_sha256=config['approved_plan_sha256'],
        review_path=config['build_review_path'], review_sha256=config['build_review_sha256'],
        build_plan_path=config['build_plan_path'], source_closure_path=config['source_closure_path'],
        rtl_root=config['rtl_root'])
    expected_binding = tuple(getattr(actual, key) for key in
                             ('operation_id','request_hash','boot_id','build_id','bit_sha256','hwh_sha256','mapping_sha256'))
    _need(capability.binding[:7] == expected_binding, 'actual parent/capability binding mismatch')
    identity_raw = bootstrap._read_pinned(config['identity_path'], config['identity_sha256'], 4096)
    identity_doc = bootstrap._json(identity_raw)
    _need(type(identity_doc) is list, 'Root-pinned identity13 JSON list required')
    identity = joint.validate_identity13(tuple(identity_doc))
    codec = importlib.import_module('competition.deepeye.golden.codec.trace_candidate')
    _need(Path(codec.__file__) == stage / 'snapshot/competition/deepeye/golden/codec/trace_candidate.py',
          'fresh staged codec source required')
    lines = live.BoundedLines(protocol_in)
    raw = lines.read(time.monotonic_ns() + 30_000_000_000)
    _need(raw is not None and len(raw) <= live.MAX_LINE and raw.endswith(b'\n'), 'bounded original INIT required')
    init = live.strict_json(raw)
    _need(init == dict(abi=live.ABI, op='init', request_seq=0, boot_id=actual.boot_id,
                       build_id=actual.build_id, request_hash=actual.request_hash), 'actual parent INIT binding required')
    operation = bootstrap._safe_path(config['operation_directory'])
    root._assert_owner()
    _need(root.read_current() == actual, 'physical parent changed before G05 claim')
    fresh_status, fresh_fault = int(root._g05.read(8)), int(root._g05.read(0x10))
    _need(fresh_status == 0 and fresh_fault == 0,
          'G05 is not fresh OFF; explicit supported recovery required, never reinitialize')
    context = dict(run_id=config['run_id'], world_epoch=config['world_epoch'], identity13=list(identity),
                   identity_sha256=config['identity_sha256'], physical_parent=asdict(actual),
                   approved_plan_sha256=config['approved_plan_sha256'],
                   build_review_sha256=config['build_review_sha256'],
                   initial_g05_status=fresh_status, initial_g05_fault=fresh_fault,
                   per_command_ttl_max_ms=12000, mission_limits=None,
                   pid=os.getpid(), thread=threading.get_ident())
    # One persistent claim per physical load: no deletion/reclaim/reinitialize.
    from competition.deepeye.tools.diagnostic.functional50_board_a import _record
    _record(operation, 'g05-live-owner-claim.json', context)
    parent = operation / 'g05-live-runs'
    if not parent.exists():
        parent.mkdir(mode=0o700)
    bootstrap._safe_path(parent)
    run = parent / config['run_id']
    run.mkdir(mode=0o700)
    _record(run, 'run-started.json', context)
    sd_journal = live.SDJournal(run / 'stream.jsonl')
    journal = _IdentityJournal(sd_journal, context)
    worker = None
    initialized = False

    def guard():
        bootstrap._read_pinned(config_watch[0], config_watch[1], 131072)
        bootstrap._read_pinned(config['identity_path'], config['identity_sha256'], 4096)
        joint.validate_capability(capability, actual.build_id)
        _need(root.read_current() == actual and root._authorized is None and root._uart_mmio is None,
              'original actual parent identity required; no UART authority')

    def check_command(*args, **kwargs):
        guard()
        return joint.command_check(*args, capability=capability, **kwargs)

    def decode_output(*args, **kwargs):
        guard()
        return joint.decode_board_output(*args, capability=capability, **kwargs)

    class GuardedLiveBoard(live.LiveBoard):
        def live(self):
            guard()
            return super().live()

        def safety_tail(self):
            try:
                guard()
            except BaseException as error:
                journal.record(dict(event='terminal-stop-not-attempted-identity-unknown',
                                    error_type=type(error).__name__, message=str(error)[:512]), True)
                self.poisoned = True
                self.closed = True
                return
            return super().safety_tail()

    try:
        guard()
        worker = GuardedLiveBoard(root._trace, root._g05, boot_id=actual.boot_id,
                                  build_id=actual.build_id, request_hash=actual.request_hash,
                                  identity=identity, codec=codec, command_check=check_command,
                                  output_decode=decode_output, journal=journal)
        journal.record(dict(event='initialize-intent', monotonic_ns=time.monotonic_ns()), True)
        worker.initialize()
        initialized = True
        journal.record(dict(event='initialize-returned', monotonic_ns=time.monotonic_ns()), True)
        live.write_response(protocol_out, dict(abi=live.ABI, op='init', status='COMPLETE',
                                              scope_sha256=REQUIREMENTS_SHA256,
                                              boot_id=actual.boot_id, build_id=actual.build_id,
                                              request_hash=actual.request_hash, initial_speed_code=2,
                                              speed_applied=False, formal_acceptance='not_run',
                                              g05_run_id=config['run_id'], world_epoch=config['world_epoch']))
        live.serve(worker, protocol_in, protocol_out, lines)
        return 2 if worker.poisoned or journal.stop_unknown else 0
    except BaseException as error:
        journal.record(dict(event='run-failed', error_type=type(error).__name__,
                            message=str(error)[:512], automatic_retry=False), True)
        raise
    finally:
        if worker is not None and not worker.closed:
            if initialized or worker.effect or worker.arm_owned:
                worker.safety_tail()
            else:
                journal.record(dict(event='terminal-no-owned-effect-no-stop',
                                    automatic_reinitialize=False), True)
                worker.closed = True
        journal.record(dict(event='run-terminal', closed=worker.closed if worker is not None else False,
                            poisoned=worker.poisoned if worker is not None else True,
                            stop_unknown=journal.stop_unknown, physical_zero_capture_proven=False,
                            automatic_reload=False, automatic_reinitialize=False), True)
        sd_journal.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-g05-run', action='store_true')
    parser.add_argument('--config', required=True)
    parser.add_argument('--config-sha256', required=True)
    args = parser.parse_args(argv)
    if not args.allow_g05_run:
        parser.error('--allow-g05-run is required before any physical read/initialization')
    _need(os.name == 'posix' and os.geteuid() == 0 and os.uname().machine == 'armv7l',
          'actual root armv7l PS required')
    stage = Path(__file__).parent
    bootstrap = _bootstrap(stage)
    raw = bootstrap._read_pinned(args.config, args.config_sha256, 131072)
    config = _validate_config(bootstrap._json(raw))
    # Separate protocol fd before native metadata imports; stdout remains JSON.
    sys.stdout.flush()
    sys.stderr.flush()
    fd = os.dup(sys.stdout.fileno())
    protocol_out = os.fdopen(fd, 'wb', buffering=0)
    try:
        os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
        with redirect_stdout(sys.stderr):
            return _run_loaded(config, stage, sys.stdin.buffer, protocol_out,
                               (args.config, args.config_sha256))
    except Exception as error:
        print(json.dumps(dict(event='g05_attach_failed', error_type=type(error).__name__,
                              message=str(error)[:512], retry=False), sort_keys=True), file=sys.stderr, flush=True)
        return 2
    finally:
        protocol_out.close()


if __name__ == '__main__':
    raise SystemExit(main())

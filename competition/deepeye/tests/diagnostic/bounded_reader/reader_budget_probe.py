"""New focused Reader filesystem proof. Root alone releases either actual run."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

PREFIX = 'DEEYE_READER_BUDGET_PROBE '
ORDER = ('small_file_read_budget', 'limit_boundary_success', 'oversize_rejected_before_read',
         'total_limit_rejected_before_read', 'growth_rejected', 'truncation_rejected',
         'duplicate_identity_rejected', 'hardlink_rejected')
FIXTURES = {'small_file_read_budget': b'alpha', 'limit_boundary_success': b'0123456789abcdef',
            'oversize_rejected_before_read': b'0123456789abcdef!',
            'total_limit_rejected_before_read': b'total', 'growth_rejected': b'grow',
            'truncation_rejected': b'truncate', 'duplicate_identity_rejected': b'dupe',
            'hardlink_rejected': b'link'}
ORIGINAL_OPEN = Path.open
LINE_MAX = 65536
STDOUT_MAX = 1048576


def require(value, message):
    if not value:
        raise ValueError(message)


def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        return actual.keys() == expected.keys() and all(exact(actual[k], expected[k]) for k in actual)
    if type(actual) is list:
        return len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
    return actual == expected


class ReadSpy:
    """Records the actual requested n; caps only the real forwarding allocation."""
    def __init__(self, real, path, initial_size, requests, forwarded, mutation):
        self.real = real
        self.path = path
        self.initial_size = initial_size
        self.requests = requests
        self.forwarded = forwarded
        self.mutation = mutation

    def __enter__(self):
        self.real.__enter__()
        return self

    def __exit__(self, kind, value, traceback):
        return self.real.__exit__(kind, value, traceback)

    def fileno(self):
        return self.real.fileno()

    def __getattr__(self, name):
        return getattr(self.real, name)

    def read(self, n=-1):
        self.requests.append(n)  # Actual call argument, BEFORE the forwarding cap.
        require(type(n) is int and n >= 0, 'unexpected Reader read argument')
        count = min(n, self.initial_size + 1)
        self.forwarded.append(count)
        if self.mutation == 'truncate':
            with ORIGINAL_OPEN(self.path, 'r+b') as writer:
                writer.truncate(3)  # Real shrink after Reader's fstat, before actual read.
                writer.flush()
                os.fsync(writer.fileno())
        data = self.real.read(count)
        if self.mutation == 'grow':
            with ORIGINAL_OPEN(self.path, 'ab') as writer:
                writer.write(b'!')  # Real append after actual read, before Reader's next fstat.
                writer.flush()
                os.fsync(writer.fileno())
        return data


def case(module, root, name):
    directory = root / name
    directory.mkdir(exist_ok=False)
    path = directory / 'input.bin'
    with ORIGINAL_OPEN(path, 'xb') as output:
        output.write(FIXTURES[name])
    if name == 'hardlink_rejected':
        os.link(path, directory / 'alias.bin')  # Only a fresh owned test file is linked.
    initial_size = len(FIXTURES[name])
    reader = module.Reader(directory / 'unused-output')
    if name == 'total_limit_rejected_before_read':
        reader.total = module.MAX_SELECTED_TOTAL - 4
    requests, forwarded = [], []
    mutation = 'grow' if name == 'growth_rejected' else ('truncate' if name == 'truncation_rejected' else '')

    def open_spy(open_path, mode='r', *args, **kwargs):
        real = ORIGINAL_OPEN(open_path, mode, *args, **kwargs)
        if Path(open_path) == path and mode == 'rb':
            return ReadSpy(real, path, initial_size, requests, forwarded, mutation)
        return real

    data = None
    error_type = error_message = None
    with patch.object(Path, 'open', new=open_spy):
        try:
            if name in ('limit_boundary_success', 'oversize_rejected_before_read'):
                data = reader.read(path, limit=16)
            else:
                data = reader.read(path)
            if name == 'duplicate_identity_rejected':
                reader.read(path)  # The second actual open/fstat must reject the real identity.
        except BaseException as error:
            error_type, error_message = type(error).__name__, str(error)
    with ORIGINAL_OPEN(path, 'rb') as source:
        final = source.read()
    return {'data_hex': None if data is None else data.hex(),
            'data_sha256': None if data is None else hashlib.sha256(data).hexdigest(),
            'read_requests': requests, 'forwarded_limits': forwarded, 'read_call_count': len(requests),
            'exception_type': error_type, 'exception_message': error_message,
            'reader_total': reader.total, 'reader_identity_count': len(reader.identities),
            'file_hex': final.hex(), 'file_sha256': hashlib.sha256(final).hexdigest(),
            'file_bytes': len(final), 'file_links': path.stat().st_nlink, 'fixture_error': None}


def no_existing_links(path):
    for part in (path,) + tuple(path.parents):
        if part.exists() or part.is_symlink():
            value = part.lstat()
            require(not part.is_symlink() and not (getattr(value, 'st_file_attributes', 0) & 0x400),
                    'symlink/reparse proof path refused')


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--collector', type=Path, required=True)
    parser.add_argument('--phase', choices=('baseline', 'corrected'), required=True)
    parser.add_argument('--cases', type=Path, required=True)
    args = parser.parse_args()
    require(args.collector.is_absolute() and args.cases.is_absolute(), 'explicit absolute source/case roots required')
    collector, cases = args.collector.absolute(), args.cases.absolute()
    no_existing_links(collector)
    no_existing_links(cases)
    require(not cases.exists(), 'exclusive new case root required; never overwrite or clean old cases')
    expectations = json.loads(Path(__file__).with_name('expectations.json').read_text('utf-8'))
    raw = collector.read_bytes()
    actual_pin = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    require(exact(actual_pin, expectations['collector_pins'][args.phase]), 'source hash differs from released exact candidate')
    require('pynq' not in sys.modules, 'PYNQ already imported in proof process')
    name = 'deepeye_reader_proof_' + actual_pin['sha256'][:16] + '_' + args.phase
    spec = importlib.util.spec_from_file_location(name, collector)
    require(spec is not None and spec.loader is not None, 'collector module specification unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # Required for future-annotation/dataclass lookup.
    try:
        spec.loader.exec_module(module)  # Not __main__; no PYNQ/runtime constructor is invoked.
        require(module.__name__ != '__main__' and 'pynq' not in sys.modules, 'non-main import-only boundary failed')
        cases.mkdir(parents=True, exist_ok=False)
        records = []
        failures = 0
        for case_name in ORDER:
            try:
                observed = case(module, cases, case_name)
            except BaseException as error:
                observed = {'fixture_error': {'type': type(error).__name__, 'message': str(error)}}
            safe = dict(expectations['corrected'][case_name])
            compared = dict(observed)
            if case_name != 'small_file_read_budget':
                # These are filesystem/data controls, not allocation-budget assertions.
                safe.pop('read_requests')
                compared.pop('read_requests', None)
            passed = exact(compared, safe)
            failures += int(not passed)
            records.append({'schema': 1, 'case': case_name, 'passed': passed, 'observed': observed})
        exit_code = 0 if failures == 0 else 1
        records.append({'schema': 1, 'case': 'complete', 'passed': exit_code == 0,
                        'observed': {'checks': 8, 'failures': failures, 'exit_code': exit_code,
                                     'phase': args.phase, 'source': {**actual_pin, 'path': collector.as_posix()},
                                     'cases_root': cases.as_posix(), 'pynq_imported': 'pynq' in sys.modules,
                                     'target_module_not_main': module.__name__ != '__main__',
                                     'case_folders_preserved': all((cases / n).is_dir() for n in ORDER),
                                     'component_only': True, 'board_runtime': False}})
        lines = [PREFIX + json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False)
                 for record in records]
        require(all(len((line + '\n').encode('utf-8')) <= LINE_MAX for line in lines) and
                sum(len((line + '\n').encode('utf-8')) for line in lines) <= STDOUT_MAX, 'bounded proof output exceeded')
        for line in lines:
            print(line)
        return exit_code
    finally:
        sys.modules.pop(name, None)


if __name__ == '__main__':
    raise SystemExit(main())

"""Independent literal oracle: verifies saved output, never imports the collector/probe."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

PREFIX = 'DEEYE_READER_BUDGET_PROBE '
ORDER = ('small_file_read_budget', 'limit_boundary_success', 'oversize_rejected_before_read',
         'total_limit_rejected_before_read', 'growth_rejected', 'truncation_rejected',
         'duplicate_identity_rejected', 'hardlink_rejected')
PINS = {'baseline': {'bytes': 29706, 'sha256': '0b5fbdb9016eca5858cb1945068bd356d4d84ab7a032c8f5e567131414364384'},
        'corrected': {'bytes': 29713, 'sha256': '391ed05c23f3f8e19b25877b897fe0361d073327ec4e4d62898db9c499f1f501'}}


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


def literal_observations(phase):
    # Fixed input/output bytes and expected calls; no candidate-derived expectations.
    fixtures = (b'alpha', b'0123456789abcdef', b'0123456789abcdef!', b'total',
                b'grow', b'truncate', b'dupe', b'link')
    final = fixtures[:4] + (b'grow!', b'tru', b'dupe', b'link')
    data = (b'alpha', b'0123456789abcdef', None, None, None, None, b'dupe', None)
    requests = ([268435457], [17], [], [], [268435457], [268435457], [268435457], []) if phase == 'baseline' else (
                [6], [17], [], [], [5], [9], [5], [])
    forwards = ([6], [17], [], [], [5], [9], [5], [])
    totals = (5, 16, 0, 536870908, 0, 0, 4, 0)
    identities = (1, 1, 0, 0, 0, 0, 1, 0)
    messages = (None, None, 'input size limit', 'input size limit',
                'input changed during snapshot', 'input changed during snapshot',
                'input path/hardlink alias', 'input path/hardlink alias')
    result = {}
    for index, name in enumerate(ORDER):
        value = data[index]
        result[name] = {'data_hex': None if value is None else value.hex(),
                        'data_sha256': None if value is None else hashlib.sha256(value).hexdigest(),
                        'read_requests': requests[index], 'forwarded_limits': forwards[index],
                        'read_call_count': len(requests[index]),
                        'exception_type': None if messages[index] is None else 'Rejected',
                        'exception_message': messages[index], 'reader_total': totals[index],
                        'reader_identity_count': identities[index], 'file_hex': final[index].hex(),
                        'file_sha256': hashlib.sha256(final[index]).hexdigest(),
                        'file_bytes': len(final[index]), 'file_links': 2 if index == 7 else 1,
                        'fixture_error': None}
    return result


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, 'duplicate JSON key')
        obj[key] = value
    return obj


def reject_constant(value):
    raise ValueError('nonfinite JSON value')


def loads(value):
    return json.loads(value, object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def main():
    require(len(sys.argv) == 3 and sys.argv[2] in PINS, 'usage: verify_output.py STDOUT baseline|corrected')
    phase = sys.argv[2]
    raw = Path(sys.argv[1]).read_bytes()
    require(0 < len(raw) <= 1048576, 'output length')
    lines = raw.decode('utf-8').splitlines()
    require(len(lines) == 9 and all(len(line.encode('utf-8')) <= 65536 and line.startswith(PREFIX)
                                 for line in lines), 'exactly nine bounded typed prefix records required')
    records = [loads(line[len(PREFIX):]) for line in lines]
    released = loads(Path(__file__).with_name('expectations.json').read_text('utf-8'))
    model = {'schema': 1, 'collector_pins': PINS,
             'baseline': literal_observations('baseline'), 'corrected': literal_observations('corrected')}
    require(exact(released, model), 'released expectations do not match independent literal oracle')
    expected = literal_observations(phase)
    expected_failures = ['small_file_read_budget'] if phase == 'baseline' else []
    actual_failures = []
    for record, name in zip(records[:8], ORDER):
        passed = name not in expected_failures
        require(exact(record, {'schema': 1, 'case': name, 'passed': passed, 'observed': expected[name]}),
                'case record mismatch: ' + name)
        if not record['passed']:
            actual_failures.append(name)
    require(actual_failures == expected_failures, 'failure set mismatch')
    complete = records[8]
    require(type(complete) is dict and set(complete) == {'schema', 'case', 'passed', 'observed'}, 'complete fields')
    observed = complete['observed']
    require(type(observed) is dict and type(observed.get('source')) is dict, 'complete observation/source type')
    source_path = observed['source'].get('path')
    case_path = observed.get('cases_root')
    require(type(source_path) is str and type(case_path) is str and
            (PurePosixPath(source_path).is_absolute() or (len(source_path) > 3 and source_path[1:3] == ':/')) and
            (PurePosixPath(case_path).is_absolute() or (len(case_path) > 3 and case_path[1:3] == ':/')),
            'absolute recorded paths required')
    failure_count = len(expected_failures)
    status = 1 if failure_count else 0
    expected_complete = {'schema': 1, 'case': 'complete', 'passed': status == 0,
                         'observed': {'checks': 8, 'failures': failure_count, 'exit_code': status,
                                      'phase': phase, 'source': {**PINS[phase], 'path': source_path},
                                      'cases_root': case_path, 'pynq_imported': False,
                                      'target_module_not_main': True, 'case_folders_preserved': True,
                                      'component_only': True, 'board_runtime': False}}
    require(exact(complete, expected_complete), 'complete record mismatch')
    print(json.dumps({'oracle': 'verified', 'phase': phase, 'checks': 8,
                      'expected_failures': expected_failures, 'probe_exit_code': status,
                      'stdout_sha256': hashlib.sha256(raw).hexdigest(), 'board_runtime': False}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

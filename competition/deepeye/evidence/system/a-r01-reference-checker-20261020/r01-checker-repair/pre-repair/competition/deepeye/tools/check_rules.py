"""Validate frozen R01 source/trace artifacts; never grant product acceptance.

No network, registration, model, hardware or file-write operations are performed.
An exit zero requires --reference-only and verifies the declared bounded scope.
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import sys

PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
CONTRACT = 'DEEPEYE-HUMAN-LOCK-20261014/revision1'
SOURCE = 'amd_guide_20260831.pdf'
SOURCE_SHA = 'c6ad82acd4f7bdcd13bd412e232ed85d05f2a87dd5e2cdd04f9d219f88b569fc'
LIMIT = 1_048_576
PRODUCT = Path(__file__).resolve().parents[1]
REPO = PRODUCT.parents[1]
STATES = {'not_run', 'passed', 'blocked'}
COLUMNS = ['requirement_id', 'source', 'source_page', 'owner_cards', 'status']
# Reviewed mapping of the pinned 28-page original, using one-based PDF file pages.
# This table cannot validate new rules/source versions; those require a new review.
POLICY = {
    'official_3_2_platform': ([13, 14, 15], ['R01', 'R02']),
    'official_3_2_real_task': ([13], ['R01', 'R04', 'A05']),
    'official_3_2_logic': ([13, 14, 16], ['B01', 'B02', 'B03', 'B04', 'B05', 'B06']),
    'official_3_2_rocm': ([15], ['R02', 'C03']),
    'official_3_2_ai': ([14, 20], ['C02', 'C03', 'C04', 'G04']),
    'official_3_2_cooperation': ([14, 16, 20], ['R03', 'B04', 'C05', 'G05', 'G06']),
    'official_core_success': ([16], ['A02', 'A05', 'G07']),
    'official_core_latency': ([16, 17], ['A05', 'G05', 'G07']),
    'official_core_ai': ([17], ['C02', 'C03']),
    'official_core_fpga': ([17], ['B06', 'A03']),
    'official_core_link': ([17], ['B04', 'G05']),
    'official_special_resources': ([17], ['B06']),
    'official_special_reliability': ([17], ['A03', 'G07']),
    'official_evidence': ([17, 18], ['A04', 'G08']),
    'official_deliverable': ([17, 18, 19], ['A04', 'G08']),
}
SPECIALS = {'FPGA resources/timing', 'system reliability'}


def require(condition, message):
    if not condition: raise ValueError(message)


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('nonfinite JSON constant')


def _finite_float(value):
    number = float(value)
    require(math.isfinite(number), 'nonfinite JSON number')
    return number


def parse_json(raw):
    require(type(raw) is bytes and len(raw) <= LIMIT, 'metadata exceeds byte bound')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                       parse_constant=_constant, parse_float=_finite_float)
    require(type(value) is dict, 'JSON document must be an object')
    return value


def read_bounded(path, limit=LIMIT):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'input exceeds byte bound')
    return raw


def parse_trace(raw):
    require(type(raw) is bytes and len(raw) <= LIMIT, 'trace exceeds byte bound')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), strict=True)
    require(reader.fieldnames == COLUMNS, 'trace header differs from fixed schema')
    rows = list(reader)
    require(len(rows) == 30, 'trace must cover all fifteen human and fifteen official requirements')
    require(all(set(row) == set(COLUMNS) and all(type(value) is str for value in row.values())
                for row in rows), 'trace row has missing or extra columns')
    return rows


def _same_members(actual, expected, label):
    require(type(actual) is list and len(actual) == len(expected), label)
    require(all(type(item) is str for item in actual), label)
    require(set(actual) == set(expected), label)


def _state(value):
    require(type(value) is str and value in STATES, 'invalid declared acceptance status')


def validate_metadata(rules, rows, scope):
    require(type(rules) is dict and type(scope) is dict and type(rows) is list, 'invalid metadata roots')
    actual = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    require(actual == PIN and scope['requirements_sha256'] == PIN, 'immutable human scope hash mismatch')
    require(scope['contract_id'] == 'DEEPEYE-HUMAN-LOCK-20261014' and
            type(scope['revision']) is int and scope['revision'] == 1, 'human contract identity mismatch')
    require(rules['immutable_scope_id'] == CONTRACT and rules['immutable_scope_sha256'] == PIN,
            'rules are not bound to the immutable human scope')
    for key, expected in (('schema', 1), ('implementation_task_version', 1), ('core_metrics_count', 5)):
        require(type(rules[key]) is int and rules[key] == expected, 'invalid ' + key)
    require(rules['implementation_task_id'] == 'DEEPEYE-IMPLEMENTATION-20261014', 'wrong implementation task')
    source = rules['source']
    require(type(source) is dict and source['filename'] == SOURCE and source['sha256'] == SOURCE_SHA,
            'wrong frozen source identity or nonportable filename')
    require(type(source['pdf_pages']) is int and source['pdf_pages'] == 28, 'wrong original page count')
    require(source['page_numbering'] == '1-based PDF file page; printed page is file page minus 3 for section 3.2',
            'source page numbering differs from the reviewed mapping')
    require(type(rules['requirements']) is list and len(rules['requirements']) == len(POLICY), 'incomplete official coverage')
    official = {}
    for row in rules['requirements']:
        require(type(row) is dict and set(row) == {'id', 'pdf_pages', 'requirement', 'owner_cards', 'product_status'},
                'official requirement shape mismatch')
        name = row['id']
        require(type(name) is str and name in POLICY and name not in official, 'unknown or duplicate official requirement')
        pages, owners = POLICY[name]
        require(type(row['pdf_pages']) is list and all(type(page) is int for page in row['pdf_pages']) and
                row['pdf_pages'] == pages, 'official page mapping differs from reviewed source')
        _same_members(row['owner_cards'], owners, 'official owner mapping differs from reviewed taskbook')
        require(type(row['requirement']) is str and bool(row['requirement'].strip()), 'missing requirement description')
        _state(row['product_status'])
        official[name] = row
    _same_members(rules['selected_special_metrics'], SPECIALS, 'specialist metrics must cover both selected distinct categories')
    gates = rules['gates']
    require(type(gates) is dict, 'missing separately declared gates')
    for name in ('rocm_project_C03', 'physical_gain_rules_recognition', 'physical_gain_engineering_A05', 'R01'):
        _state(gates[name])
    human = {row['id']: row for row in scope['requirements']}
    require(set(human) == {'H%02d' % i for i in range(1, 16)}, 'human requirement IDs differ')
    require(len(rows) == 30, 'missing or extra trace rows')
    found = set()
    for row in rows:
        require(type(row) is dict and set(row) == set(COLUMNS) and
                all(type(value) is str for value in row.values()), 'trace shape mismatch')
        name = row['requirement_id']
        require(name not in found and name in (set(human) | set(official)), 'duplicate or unknown trace row')
        found.add(name); _state(row['status'])
        owners = row['owner_cards'].split(';')
        if name in human:
            require(row['source'] == CONTRACT and row['source_page'] == '', 'human source association differs')
            _same_members(owners, human[name]['acceptance_cards'], 'human owner mapping differs from immutable scope')
        else:
            mapped = official[name]
            require(row['source'] == SOURCE and row['source_page'] == ';'.join(map(str, mapped['pdf_pages'])),
                    'official trace source/page mismatch')
            _same_members(owners, mapped['owner_cards'], 'official trace owner mismatch')
            require(row['status'] == mapped['product_status'], 'official trace status mismatch')
    return dict(human_requirements=len(human), official_requirements=len(official),
                core_metrics=sum(name.startswith('official_core_') for name in official),
                special_metrics=len(SPECIALS), requirements_sha256=actual)


def verify_source(path):
    path = Path(path)
    try:
        raw = read_bounded(path, 32 * LIMIT)
    except FileNotFoundError:
        return dict(status='blocked', path=str(path.resolve()), reason='pinned original PDF is absent')
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == SOURCE_SHA, 'actual original PDF bytes do not match frozen source hash')
    return dict(status='passed', path=str(path.resolve()), bytes=len(raw), sha256=digest,
                scope='exact frozen source identity; no fresh online retrieval or semantic re-interpretation')


def make_result(coverage, source, rules, reference_only):
    good = source['status'] == 'passed'
    code = 0 if good and reference_only else 2
    result = dict(status='reference_checks_passed' if code == 0 else 'blocked',
        scope='reference_only' if reference_only else 'full_R01', R01='not_run',
        formal_acceptance=False, hardware_enable_eligible=False, coverage=coverage,
        source=source, declared_gates=rules['gates'], registration_claim=rules['registration'],
        remaining_gates=['independent registration/qualification evidence',
                         'organizer rule recognition of the proposed real physical task',
                         'actual ROCm project and physical engineering evidence owned by their cards',
                         'separately reviewed formal acceptance integration'],
        note='Metadata status fields are claims; this read-only checker cannot accept measured or human qualification gates.')
    return result, code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-only', action='store_true')
    parser.add_argument('--source-pdf', type=Path, help='Explicit read-only original; no fallback search or download')
    args = parser.parse_args(argv)
    paths = [PRODUCT / 'docs/rules.json', PRODUCT / 'docs/requirements_trace.csv',
             REPO / 'docs/competition/deepeye-2026/immutable_scope.json']
    try:
        raw = [read_bounded(path) for path in paths]
        rules, rows, scope = parse_json(raw[0]), parse_trace(raw[1]), parse_json(raw[2])
        coverage = validate_metadata(rules, rows, scope)
        source_path = args.source_pdf or REPO / 'docs/competition/deepeye-2026/sources' / SOURCE
        source = verify_source(source_path)
        result, code = make_result(coverage, source, rules, args.reference_only)
        result['artifact_sha256'] = {str(path.resolve()): hashlib.sha256(data).hexdigest() for path, data in zip(paths, raw)}
        result['source_inside_checkout'] = source_path.resolve().is_relative_to(REPO.resolve())
    except (ValueError, KeyError, TypeError, OSError, RecursionError, csv.Error) as error:
        result, code = dict(status='failed', R01='not_run', formal_acceptance=False,
                            hardware_enable_eligible=False, error=str(error)), 1
    result['checked_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__': sys.exit(main())

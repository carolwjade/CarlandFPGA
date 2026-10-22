"""Offline R02 calibration arithmetic; never accesses devices or accepts R02.

See hardware/calibration_format.md. All acquisition metadata is a declaration.
Only the raw input hash and arithmetic are checked here, not physical provenance.
"""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

MAX_INPUT_BYTES = 4 * 1024 * 1024
REQUIREMENTS_SHA256 = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'


class InvalidRecord(ValueError):
    pass


def require(condition, path, message):
    if not condition:
        raise InvalidRecord(f'{path}: {message}')


def fields(value, names, path):
    require(type(value) is dict and set(value) == set(names.split()), path,
            'missing or unexpected fields')


def label(value, path):
    require(type(value) is str and 0 < len(value) <= 256 and value.strip() == value
            and all(ord(c) >= 32 for c in value), path, 'nonempty label of at most 256 characters required')


def number(value, path):
    require(type(value) in (int, float), path, 'finite number required')
    try:
        result = float(value)
    except OverflowError as exc:
        raise InvalidRecord(f'{path}: finite number required') from exc
    require(math.isfinite(result), path, 'finite number required')
    return result


def decode(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, key, 'duplicate JSON key')
            obj[key] = value
        return obj

    def nonfinite(value):
        raise InvalidRecord('nonfinite JSON value: ' + value)

    def finite_float(value):
        return number(float(value), 'JSON number')

    require(type(raw) is bytes and len(raw) <= MAX_INPUT_BYTES, 'input', 'maximum size is 4 MiB')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
                          parse_constant=nonfinite, parse_float=finite_float)
    except (UnicodeError, RecursionError) as exc:
        raise InvalidRecord('invalid UTF-8 or JSON nesting') from exc


def linear_fit(points):
    """Equal weight per independent level, y volts against mean decoded code."""
    xs = [p['mean_code'] for p in points]
    ys = [p['reference_v'] for p in points]
    xm, ym = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
    scale = max(abs(x - xm) for x in xs)
    require(scale > 64 * sys.float_info.epsilon * max(1.0, abs(xm)),
            'fit', 'ADC spread is zero or numerically unresolved')
    zs = [(x - xm) / scale for x in xs]
    gain = math.fsum(z * (y - ym) for z, y in zip(zs, ys)) / math.fsum(z*z for z in zs) / scale
    offset = ym - gain * xm
    residuals = [y - (offset + gain*x) for x, y in zip(xs, ys)]
    require(gain > 0 and all(math.isfinite(v) for v in [gain, offset, *residuals]),
            'fit', 'positive finite calibration slope required')
    return dict(offset_v=offset, volts_per_code=gain,
                residual_v=residuals, max_abs_residual_v=max(map(abs, residuals)),
                rms_residual_v=math.sqrt(math.fsum(v*v for v in residuals) / len(residuals)))


def channel_report(c, source_mode, minimum, sample_ids):
    fields(c, 'channel_id signal_chain_id gain nominal_adc_bits container_bits packing range_v '
           'reference_instrument levels', 'channel')
    cid = c['channel_id']
    require(type(cid) is str and cid in ('A0', 'A1', 'A2', 'A3'), 'channel_id', 'A0-A3 required')
    for key in ('signal_chain_id', 'reference_instrument'):
        label(c[key], cid + '.' + key)
    require(type(c['gain']) is int and c['gain'] in (1, 2, 4, 8), cid, 'fixed gain must be 1, 2, 4 or 8')
    require(cid == 'A0' or c['gain'] == 1, cid, 'only A0 is on the documented PGA output')
    require(type(c['nominal_adc_bits']) is int and c['nominal_adc_bits'] == 12,
            cid, 'nominal ADC resolution must be explicitly 12 bits')
    require(type(c['container_bits']) is int and c['container_bits'] == 16,
            cid, 'container width must be explicitly 16 bits')
    require(c['packing'] in ('right_aligned', 'left_aligned'), cid, 'explicit supported packing required')
    require(type(c['range_v']) is list and len(c['range_v']) == 2, cid, 'two header-voltage bounds required')
    low, high = [number(v, cid + '.range_v') for v in c['range_v']]
    require(0 <= low < high <= 3.3, cid, 'declared header-voltage range must lie within 0-3.3 V')
    require(type(c['levels']) is list and len(c['levels']) <= 256, cid, 'at most 256 levels required')
    result = dict(channel_id=cid, signal_chain_id=c['signal_chain_id'], gain=c['gain'],
                  nominal_adc_bits=12, container_bits=16, packing=c['packing'], range_v=[low, high],
                  reference_instrument=c['reference_instrument'], level_count=len(c['levels']),
                  sample_count=0, status='incomplete', fit=None, levels=[], issues=[])

    def issue(path, code):
        result['issues'].append(dict(path=path, code=code))

    ids = set()
    for index, point in enumerate(c['levels']):
        path = f'{cid}.levels[{index}]'
        fields(point, 'level_id target_v reference_kind reference_v reference_uncertainty_v samples', path)
        label(point['level_id'], path + '.level_id')
        require(point['level_id'] not in ids, path, 'duplicate level_id')
        ids.add(point['level_id'])
        expected = 'software_fixture' if source_mode == 'software_fixture' else 'independent_measurement'
        require(point['reference_kind'] == expected, path,
                'independent reference required; DAC setpoint is not a measurement')
        target, ref, unc = [number(point[k], path + '.' + k)
                            for k in ('target_v', 'reference_v', 'reference_uncertainty_v')]
        require(0 <= unc <= 3.3, path, 'nonnegative reference uncertainty up to 3.3 V required')
        if not low <= target <= high:
            issue(path, 'target_out_of_range')
        if ref - unc < low or ref + unc > high:
            issue(path, 'reference_out_of_range')
        samples = point['samples']
        require(type(samples) is list and 1 <= len(samples) <= 4096, path, '1-4096 samples per level required')
        codes = []
        for j, s in enumerate(samples):
            sp = f'{path}.samples[{j}]'
            fields(s, 'sample_id raw_word analog_saturation', sp)
            label(s['sample_id'], sp + '.sample_id')
            require(s['sample_id'] not in sample_ids, sp, 'duplicate sample_id in dataset')
            sample_ids.add(s['sample_id'])
            word = s['raw_word']
            require(type(word) is int and 0 <= word <= 65535, sp, 'raw_word must be a uint16 integer')
            if c['packing'] == 'left_aligned':
                require(word & 15 == 0, sp, 'nonzero padding in left-aligned 12-bit word')
                code = word >> 4
            else:
                require(word <= 4095, sp, 'nonzero padding in right-aligned 12-bit word')
                code = word
            flag = s['analog_saturation']
            require(flag is None or type(flag) is bool, sp, 'analog_saturation must be true, false or null')
            if code in (0, 4095):
                issue(sp, 'adc_low_rail' if code == 0 else 'adc_high_rail')
            if flag is True:
                issue(sp, 'declared_analog_saturation')
            elif flag is None:
                issue(sp, 'analog_saturation_unknown')
            codes.append(code)
        result['sample_count'] += len(codes)
        result['levels'].append(dict(level_id=point['level_id'], target_v=target,
                                     reference_v=ref, reference_uncertainty_v=unc,
                                     sample_count=len(codes), mean_code=math.fsum(codes)/len(codes)))
    if result['level_count'] < minimum:
        issue(cid, 'insufficient_independent_levels')
    resolution = 64 * sys.float_info.epsilon * max(1.0, abs(low), abs(high))
    targets = sorted(p['target_v'] for p in result['levels'])
    if any(b - a <= resolution for a, b in zip(targets, targets[1:])):
        issue(cid, 'repeated_or_unresolved_target_levels')
    references = sorted(result['levels'], key=lambda p: p['reference_v'])
    if any(b['reference_v'] - b['reference_uncertainty_v']
           - (a['reference_v'] + a['reference_uncertainty_v']) <= resolution
           for a, b in zip(references, references[1:])):
        issue(cid, 'overlapping_or_unresolved_reference_levels')
    if not result['issues']:
        try:
            result['fit'] = linear_fit(result['levels'])
            result['status'] = 'computed'
        except InvalidRecord as exc:
            issue(cid, str(exc))
    return result


def analyze(raw, levels=8):
    """Return deterministic offline evidence. Physical acceptance is never set."""
    result = dict(schema=1, status='not_run', input_sha256=None, source_mode=None,
                  declared_provenance={}, evidence_level='none', minimum_levels=levels,
                  physical_verification='not_run', r02_acceptance='not_run', r03_acceptance='not_run',
                  requirements_sha256=REQUIREMENTS_SHA256,
                  enob=dict(status='not_run', reason='DC calibration does not measure ENOB'),
                  channels=[], errors=[])
    try:
        require(type(levels) is int and 8 <= levels <= 256, 'levels', '8-256 independent levels required')
        if raw is None:
            result['errors'].append('input_missing: no measurements supplied')
            return result
        require(type(raw) is bytes, 'input', 'bytes required')
        # The CLI reads at most limit+1 bytes. An oversized prefix is not the file.
        require(len(raw) <= MAX_INPUT_BYTES, 'input', 'maximum size is 4 MiB; full input not hashed')
        result['input_sha256'] = hashlib.sha256(raw).hexdigest()
        doc = decode(raw)
        fields(doc, 'schema source_mode operation_id request_hash tested_commit captured_at_utc channels', 'input')
        require(type(doc['schema']) is int and doc['schema'] == 1, 'schema', 'version 1 required')
        mode = doc['source_mode']
        require(mode in ('sensor_live', 'twin_fixture', 'software_fixture'), 'source_mode', 'ADC-compatible mode required')
        label(doc['operation_id'], 'operation_id')
        for key, digits in [('request_hash', 64), ('tested_commit', 40)]:
            require(type(doc[key]) is str and re.fullmatch('[0-9a-f]{' + str(digits) + '}', doc[key]) is not None,
                    key, f'full lowercase {digits}-digit hexadecimal identity required')
        stamp = doc['captured_at_utc']
        require(type(stamp) is str and len(stamp) <= 40, 'captured_at_utc', 'UTC ISO timestamp required')
        dt = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        require(dt.utcoffset() is not None and dt.utcoffset().total_seconds() == 0,
                'captured_at_utc', 'explicit UTC required')
        require(type(doc['channels']) is list and len(doc['channels']) == 4, 'channels', 'exactly four channels required')
        result['source_mode'] = mode
        result['evidence_level'] = ('software_fixture' if mode == 'software_fixture'
                                    else 'offline_computation_on_declared_measurements')
        result['declared_provenance'] = {k: doc[k] for k in ('operation_id', 'request_hash', 'tested_commit', 'captured_at_utc')}
        seen = set()
        channels = [channel_report(c, mode, levels, seen) for c in doc['channels']]
        require({c['channel_id'] for c in channels} == {'A0', 'A1', 'A2', 'A3'}, 'channels', 'duplicate or missing channel')
        result['channels'] = sorted(channels, key=lambda c: c['channel_id'])
        result['status'] = 'computed' if all(c['status'] == 'computed' for c in channels) else 'incomplete'
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        result['status'] = 'invalid'
        result['channels'] = []
        result['errors'].append(str(exc))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--levels', type=int, default=8)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, help='create a new report; existing files are never overwritten')
    args = parser.parse_args(argv)
    result = None
    try:
        raw = None
        if args.input is not None:
            if not args.input.is_file():
                raise OSError('input must be an existing regular file')
            with args.input.open('rb') as stream:
                raw = stream.read(MAX_INPUT_BYTES + 1)
        result = analyze(raw, args.levels)
        if args.output is not None:
            payload = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
            with args.output.open('xb') as stream:
                stream.write(payload)
    except OSError as exc:
        if result is None:
            result = analyze(None, args.levels)
            result['errors'] = []
        result['status'] = 'invalid'
        result['errors'].append('file_error: ' + str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result['status'] == 'computed' else 2 if result['status'] == 'invalid' else 3


if __name__ == '__main__':
    raise SystemExit(main())

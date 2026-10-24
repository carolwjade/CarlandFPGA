import datetime
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
WORK = HERE / 'work' / 'counterexamples'
CHECKER = PRODUCT / 'competition/deepeye/tools/check_rules.py'
RULES = PRODUCT / 'competition/deepeye/docs/rules.json'
TRACE = PRODUCT / 'competition/deepeye/docs/requirements_trace.csv'
SCOPE = PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed(label):
    case = WORK / label
    if case.exists():
        raise SystemExit('refusing to overwrite case: ' + str(case))
    (case / 'competition/deepeye/tools').mkdir(parents=True)
    (case / 'competition/deepeye/docs').mkdir(parents=True)
    (case / 'docs/competition/deepeye-2026').mkdir(parents=True)
    shutil.copyfile(CHECKER, case / 'competition/deepeye/tools/check_rules.py')
    shutil.copyfile(TRACE, case / 'competition/deepeye/docs/requirements_trace.csv')
    shutil.copyfile(SCOPE, case / 'docs/competition/deepeye-2026/immutable_scope.json')
    return case


def write_rules(case, rules):
    path = case / 'competition/deepeye/docs/rules.json'
    path.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def write_raw_rules(case, raw):
    path = case / 'competition/deepeye/docs/rules.json'
    path.write_bytes(raw)
    return path


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    original_rules = json.loads(RULES.read_bytes())
    cases = {}

    case = seed('weights-tamper')
    rules = json.loads(json.dumps(original_rules))
    rules['assessment_weights']['fpga_quality'] = 30
    rules['assessment_weights']['engineering_innovation'] = 10
    path = write_rules(case, rules)
    cases['weights-tamper'] = {
        'mutation': 'substitute a different 100-point weight distribution',
        'rules_sha256': sha256(path),
    }

    case = seed('weights-missing')
    rules = json.loads(json.dumps(original_rules))
    del rules['assessment_weights']
    path = write_rules(case, rules)
    cases['weights-missing'] = {
        'mutation': 'remove assessment_weights entirely',
        'rules_sha256': sha256(path),
    }

    case = seed('deep-json')
    raw = RULES.read_bytes().rstrip()
    assert raw.endswith(b'}')
    deep_value = b'[' * 4000 + b'0' + b']' * 4000
    path = write_raw_rules(case, raw[:-1] + b',adversarial_depth:' + deep_value + b'}\n')
    cases['deep-json'] = {
        'mutation': 'append a 4000-level array under an unused key',
        'rules_bytes': path.stat().st_size,
        'rules_sha256': sha256(path),
    }

    case = seed('duplicate-key')
    raw = RULES.read_bytes().rstrip()
    assert raw.startswith(b'{')
    path = write_raw_rules(case, b'{schema:1,' + raw[1:] + b'\n')
    cases['duplicate-key'] = {
        'mutation': 'add a duplicate top-level schema key',
        'rules_sha256': sha256(path),
    }

    case = seed('joint-drift')
    rules = json.loads(json.dumps(original_rules))
    row = next(item for item in rules['requirements'] if item['id'] == 'official_3_2_rocm')
    row['pdf_pages'] = [3]
    row['owner_cards'] = ['R01']
    rules_path = write_rules(case, rules)
    trace_path = case / 'competition/deepeye/docs/requirements_trace.csv'
    text = trace_path.read_text(encoding='utf-8')
    old = 'official_3_2_rocm,amd_guide_20260831.pdf,15,R02;C03,not_run'
    new = 'official_3_2_rocm,amd_guide_20260831.pdf,3,R01,not_run'
    if text.count(old) != 1:
        raise SystemExit('unexpected trace row for joint-drift case')
    trace_path.write_text(text.replace(old, new), encoding='utf-8')
    cases['joint-drift'] = {
        'mutation': 'move ROCm rule and trace row jointly to page 3 and owner R01',
        'rules_sha256': sha256(rules_path),
        'trace_sha256': sha256(trace_path),
    }

    manifest = {
        'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'product_sources': {
            str(CHECKER): sha256(CHECKER),
            str(RULES): sha256(RULES),
            str(TRACE): sha256(TRACE),
            str(SCOPE): sha256(SCOPE),
        },
        'cases': cases,
    }
    (WORK / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

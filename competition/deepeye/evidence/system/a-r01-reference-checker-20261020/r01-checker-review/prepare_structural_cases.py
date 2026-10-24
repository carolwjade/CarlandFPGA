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
QUOTE = bytes([34])


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


def key(name):
    return QUOTE + name.encode('utf-8') + QUOTE


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    cases = {}

    case = seed('deep-json-v2')
    path = case / 'competition/deepeye/docs/rules.json'
    raw = b'{' + key('adversarial_depth') + b':' + b'[' * 4000 + b'0' + b']' * 4000 + b'}\n'
    path.write_bytes(raw)
    cases['deep-json-v2'] = {
        'mutation': 'minimal JSON object containing a 4000-level array',
        'rules_bytes': path.stat().st_size,
        'rules_sha256': sha256(path),
    }

    case = seed('duplicate-key-v2')
    path = case / 'competition/deepeye/docs/rules.json'
    raw = b'{' + key('schema') + b':1,' + key('schema') + b':1}\n'
    path.write_bytes(raw)
    cases['duplicate-key-v2'] = {
        'mutation': 'minimal JSON object with a duplicate schema key',
        'rules_sha256': sha256(path),
    }

    report = {
        'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'product_sources': {
            str(CHECKER): sha256(CHECKER),
            str(RULES): sha256(RULES),
            str(TRACE): sha256(TRACE),
            str(SCOPE): sha256(SCOPE),
        },
        'cases': cases,
    }
    (WORK / 'structural-manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

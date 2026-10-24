import datetime
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
TEST_PATH = PRODUCT / 'competition/deepeye/tests/test_check_rules.py'
CHECKER_PATH = PRODUCT / 'competition/deepeye/tools/check_rules.py'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('review_origin_test_check_rules', TEST_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit('cannot load test module')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checker = module.checker
    methods = sorted(
        name for name, value in inspect.getmembers(module.RuleCheckerTests, inspect.isfunction)
        if name.startswith('test_')
    )
    report = {
        'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'python_executable': sys.executable,
        'python_version': sys.version,
        'test_module': {
            'path': str(TEST_PATH),
            'sha256': sha256(TEST_PATH),
            'loaded_file': str(Path(module.__file__).resolve()),
        },
        'checker_module': {
            'path': str(CHECKER_PATH),
            'sha256': sha256(CHECKER_PATH),
            'loaded_file': str(Path(checker.__file__).resolve()),
            'cached': checker.__cached__,
            'product': str(checker.PRODUCT.resolve()),
            'repo': str(checker.REPO.resolve()),
        },
        'test_method_count': len(methods),
        'test_methods': methods,
        'origin_matches': Path(module.__file__).resolve() == TEST_PATH.resolve()
            and Path(checker.__file__).resolve() == CHECKER_PATH.resolve(),
    }
    if not report['origin_matches'] or len(methods) != 17:
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))
    output = HERE / 'provenance-check.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'output': str(output),
        'origin_matches': True,
        'checker_sha256': report['checker_module']['sha256'],
        'test_sha256': report['test_module']['sha256'],
        'test_method_count': len(methods),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()

import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT_SCOPE = ROOT / '.local/deepeye-implementation-a/docs/competition/deepeye-2026/immutable_scope.json'
ROOT_SCOPE = ROOT / 'docs/competition/deepeye-2026/immutable_scope.json'
PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'


def main():
    product_raw = PRODUCT_SCOPE.read_bytes()
    root_raw = ROOT_SCOPE.read_bytes()
    scope = json.loads(root_raw)
    canonical = json.dumps(
        scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    actual = hashlib.sha256(canonical).hexdigest()
    ids = [row['id'] for row in scope['requirements']]
    report = {
        'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'contract_id': scope.get('contract_id'),
        'revision': scope.get('revision'),
        'requirements_count': len(scope['requirements']),
        'requirement_ids': ids,
        'expected_ids': ['H%02d' % number for number in range(1, 16)],
        'scope_file_sha256': {
            'product': hashlib.sha256(product_raw).hexdigest(),
            'root': hashlib.sha256(root_raw).hexdigest(),
        },
        'scope_files_identical': product_raw == root_raw,
        'declared_requirements_sha256': scope.get('requirements_sha256'),
        'canonical_requirements_sha256': actual,
        'expected_requirements_sha256': PIN,
        'matches': actual == scope.get('requirements_sha256') == PIN,
    }
    if not (report['matches'] and product_raw == root_raw and ids == report['expected_ids']):
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))
    output = HERE / 'requirements-check.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'output': str(output),
        'canonical_requirements_sha256': actual,
        'match': report['matches'],
        'requirements_count': report['requirements_count'],
        'scope_files_identical': report['scope_files_identical'],
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()

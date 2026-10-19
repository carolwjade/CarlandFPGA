import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(data):
    return {item['relative_path']: item['sha256'] for item in data['sources']}


def evidence_hashes(data):
    return {item['relative_path']: item['sha256'] for item in data['evidence_files']}


def canonical_input_hashes(data):
    return {
        name: sorted(item['sha256'] for item in records)
        for name, records in data['canonical_inputs'].items()
    }


before_path = HERE / 'inventory-before.json'
after_path = HERE / 'inventory-after.json'
before = json.loads(before_path.read_text(encoding='utf-8'))
after = json.loads(after_path.read_text(encoding='utf-8'))
comparison = {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'before_inventory_sha256': sha256(before_path),
    'after_inventory_sha256': sha256(after_path),
    'candidate_manifest_sha256': {
        'before': before['candidate_manifest']['sha256'],
        'after': after['candidate_manifest']['sha256'],
        'pin_match': after['candidate_manifest']['matches'],
    },
    'product_head': {
        'base': before['candidate_base_head'],
        'before': before['product_head']['stdout'].strip(),
        'after': after['product_head']['stdout'].strip(),
        'changed_by_unrelated_concurrent_work': before['product_head']['stdout'].strip() != after['product_head']['stdout'].strip(),
    },
    'source_files': {
        'before': source_hashes(before),
        'after': source_hashes(after),
    },
    'input_files': {
        'before': canonical_input_hashes(before),
        'after': canonical_input_hashes(after),
    },
    'evidence_files': {
        'before': evidence_hashes(before),
        'after': evidence_hashes(after),
    },
}
comparison['source_files']['unchanged'] = comparison['source_files']['before'] == comparison['source_files']['after']
comparison['input_files']['unchanged'] = comparison['input_files']['before'] == comparison['input_files']['after']
comparison['evidence_files']['unchanged'] = comparison['evidence_files']['before'] == comparison['evidence_files']['after']
comparison['all_pinned_bytes_unchanged'] = all((
    comparison['source_files']['unchanged'],
    comparison['input_files']['unchanged'],
    comparison['evidence_files']['unchanged'],
    comparison['candidate_manifest_sha256']['pin_match'],
))
output = HERE / 'pin-comparison.json'
output.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'all_pinned_bytes_unchanged': comparison['all_pinned_bytes_unchanged'],
    'product_head_before': comparison['product_head']['before'],
    'product_head_after': comparison['product_head']['after'],
}, ensure_ascii=False))

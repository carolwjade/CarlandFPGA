import json
from pathlib import Path

root = Path.cwd()
review = root / '.planning' / 'deepeye-resume-20261018' / 'g02-layout-persistence-review'
paths = set(review.glob('*.json'))
paths.update((review / 'evidence').rglob('*.json'))
paths.update((review / 'runs').rglob('*.json'))
files = sorted(paths, key=lambda p: str(p).lower())
bad = []
encodings = {}

def decode(data):
    if data.startswith(b'\xff\xfe'):
        return data.decode('utf-16'), 'utf-16-le-bom'
    if data.startswith(b'\xfe\xff'):
        return data.decode('utf-16'), 'utf-16-be-bom'
    if data.startswith(b'\xef\xbb\xbf'):
        return data.decode('utf-8-sig'), 'utf-8-bom'
    return data.decode('utf-8'), 'utf-8'

for path in files:
    try:
        text, enc = decode(path.read_bytes())
        encodings[enc] = encodings.get(enc, 0) + 1
        json.loads(text)
    except Exception as exc:
        bad.append((path.relative_to(review).as_posix(), type(exc).__name__, str(exc)))

print(f'ROOT={review.as_posix()}')
print(f'SCOPE=review-root *.json + evidence/**/*.json + runs/**/*.json')
print(f'FILES={len(files)}')
print('ENCODINGS=' + ','.join(f'{k}:{v}' for k, v in sorted(encodings.items())))
print(f'BAD={len(bad)}')
for rel, kind, message in bad:
    print(f'BAD_FILE={rel} TYPE={kind} MESSAGE={message}')
print('RESULT=' + ('PASS' if not bad else 'FAIL'))
raise SystemExit(0 if not bad else 1)
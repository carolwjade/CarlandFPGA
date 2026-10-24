import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
base = Path(sys.base_prefix)
assert sys.version_info[:2] == (3, 12)
files = [base / name for name in ('python.exe', 'python3.dll', 'python312.dll',
                                'vcruntime140.dll', 'vcruntime140_1.dll')]
files += [base / 'DLLs' / name for name in ('_ctypes.pyd', 'libffi-8.dll')]
def entry(path):
    assert path.is_file() and not path.is_symlink() and not path.is_junction()
    data = path.read_bytes()
    return {'path': str(path), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
for path in (HERE, *HERE.parents):
    assert not path.is_symlink() and not path.is_junction()
module = ROOT / '.local/deepeye-implementation-a/competition/deepeye/simulation/isolation'
result = {'python': sys.version, 'base_prefix': str(base),
          'runtime_files': [entry(path) for path in files],
          'isolation_module_files': [entry(path) for path in sorted(module.glob('*.py'))],
          'native_executed': False, 'original_files_acl_changed': False}
with (HERE / 'runtime-preflight.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps({'python': sys.version.split()[0], 'runtime_files': len(files),
                  'isolation_module_files': len(result['isolation_module_files']),
                  'native_executed': False}))

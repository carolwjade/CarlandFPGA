"""Record the exact staged import origins used by the rereview."""
import hashlib
import importlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
STAGE = ROOT / 'stage-01' / 'product'


def digest(path):
    data = Path(path).read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


sys.path.insert(0, str(STAGE))
module = importlib.import_module('competition.deepeye.tests.test_check_rules')
result = {
    'python_executable': sys.executable,
    'python_version': sys.version,
    'sys_path_0': sys.path[0],
    'stage_root': str(STAGE),
    'test_module_file': str(Path(module.__file__).resolve()),
    'test_module_cached': module.__cached__,
    'test_product_constant': str(module.PRODUCT.resolve()),
    'test_repo_constant': str(module.REPO.resolve()),
    'test_path_constant': str(module.PATH.resolve()),
    'checker_module_file': str(Path(module.checker.__file__).resolve()),
    'checker_cached': module.checker.__cached__,
    'test_method_count': len([name for name in dir(module.RuleCheckerTests) if name.startswith('test_')]),
    'test_sha256': digest(module.__file__),
    'checker_sha256': digest(module.checker.__file__),
    'import_origins_match_stage': (
        Path(module.__file__).resolve().is_relative_to(STAGE.resolve()) and
        Path(module.checker.__file__).resolve().is_relative_to(STAGE.resolve()) and
        Path(module.PATH).resolve() == (STAGE / 'competition/deepeye/tools/check_rules.py').resolve()
    ),
}
(ROOT / 'provenance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))

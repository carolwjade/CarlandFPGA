import hashlib, importlib.util, json, pathlib, sys
root = pathlib.Path(r'C:\\Users\\CarlJade\\Documents\\ChatGPT\\FPGA多机协作开发\\.planning\\deepeye-resume-20261018\\b-pr30-operations10-11-20261020\\source')
model = root / 'competition/deepeye/golden/control/register_transaction_reference.py'
test = root / 'competition/deepeye/tests/control/test_register_transaction.py'
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
ref = load('register_transaction_reference', model)
test_mod = load('test_register_transaction', test)
def rec(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'module_file': str(getattr(sys.modules.get(path.stem), '__file__', ''))}
print(json.dumps({'python': sys.executable, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'model': rec(model), 'test_module': str(getattr(test_mod, '__file__', '')), 'reference_module': str(getattr(ref, '__file__', '')), 'reference_sha256': hashlib.sha256(pathlib.Path(ref.__file__).read_bytes()).hexdigest(), 'sys_path': list(sys.path), 'sys_version': sys.version}, sort_keys=True))
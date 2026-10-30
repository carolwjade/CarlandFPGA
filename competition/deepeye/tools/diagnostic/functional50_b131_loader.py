"""Fixed B131 byte loader, with no host transport or hardware imports."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_PINS={'dependencies128.py':'304f1552ce4126b9e6d15503273e7cfe0da4c3c1a7f5ef2db0deea0ecd9f2ba3',
       'adapter128.py':'12d975c2841edb65ef427121d098cd6ed27f600edd922f1a63fc5d6b5908ea41',
       'reducer128.py':'590f004fb7ae9a743c4ac56d65663248dcf0223d218c02b93a78ce324f9aaf2d'}
_DEPS={'competition/deepeye/tools/diagnostic/functional50_input113/input113.py':'95b46940767d3be4dbe3d885a4852119161ea5e4567ab3bda51798c39109ea49',
       'competition/deepeye/golden/codec/trace_candidate.py':'a489ac34b49976532803b34f006f8bc24103548f34ddd55cc2ecaedc529a9642'}

def _need(ok, message):
    if not ok: raise ValueError(message)

def _sha(path):
    _need(path.is_file() and not path.is_symlink(),'pinned file required: '+str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_selected(snapshot_root):
    """Load the unchanged B131 from a Root-assembled exact hierarchy once."""
    root=Path(snapshot_root)
    _need(root.is_absolute() and root.is_dir() and not root.is_symlink(),'snapshot root required')
    base=root/'competition/deepeye/tools/diagnostic/functional50_adapter128'
    for name,sha in _PINS.items():_need(_sha(base/name)==sha,'B131 pin mismatch: '+name)
    for name,sha in _DEPS.items():_need(_sha(root/name)==sha,'B131 dependency mismatch: '+name)
    _need(not any(x in sys.modules for x in ('dependencies128','adapter128','reducer128','_adapter128_input113','_adapter128_trace_codec')),'fixed module name already occupied')
    loaded=[]
    try:
        for name in ('dependencies128','adapter128','reducer128'):
            spec=importlib.util.spec_from_file_location(name,base/(name+'.py'))
            _need(spec is not None and spec.loader is not None,'fixed loader absent')
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module;loaded.append(name);spec.loader.exec_module(module)
        return _Bundle(_KEY,sys.modules['adapter128'],sys.modules['reducer128'])
    except BaseException:
        for name in reversed(loaded):sys.modules.pop(name,None)
        for name in ('_adapter128_input113','_adapter128_trace_codec'):sys.modules.pop(name,None)
        raise

_KEY=object()
class _Bundle:
    def __init__(self,key,adapter,reducer):
        _need(key is _KEY,'fixed loader required');self.adapter=adapter;self.reducer=reducer

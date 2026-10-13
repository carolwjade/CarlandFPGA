"""A-owned metadata diagnostic: no Overlay download, MMIO or GPIO writes."""
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import platform
import xml.etree.ElementTree as ET
import pynq
import pynq.metadata.mem_dict_view as mem_view

bit = Path('/usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/overlays/base/base.bit')
hwh = bit.with_suffix('.hwh')
expected = {'bit': 'ecabdcb5d483c75335ab6f043824a2386971c7b0ffd6e3315f24860bf5088eb6', 'hwh': 'cbd90c84f3a46d1eba95dff7ba7d0079812f7e46641a08e2318c9928cd36ce8f'}
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
hashes = {'bit': digest(bit), 'hwh': digest(hwh)}
assert hashes == expected, 'Base assets changed; stop diagnostic'
before = {'bitfile_name': pynq.PL.bitfile_name, 'timestamp': pynq.PL.timestamp}
overlay = pynq.Overlay(str(bit), download=False, gen_cache=False)
after = {'bitfile_name': pynq.PL.bitfile_name, 'timestamp': pynq.PL.timestamp}
assert before == after, 'PL identity changed during read-only diagnostic'
target = 'iop_pmoda/mb_bram_ctrl'
tree = ET.parse(hwh)
modules = [m for m in tree.iter('MODULE') if m.get('FULLNAME', '').strip('/') == target]
ranges = [dict(m.attrib) for m in tree.iter('MEMRANGE') if m.get('INSTANCE', '') in (target, '/'+target, 'mb_bram_ctrl')]
report = {
    'task_id': 'BOARD-20261013-A', 'phase': 'metadata-v3-readonly-preflight',
    'board_utc': datetime.now(timezone.utc).isoformat(), 'runtime': {'python': platform.python_version(), 'pynq': pynq.__version__, 'machine': platform.machine()},
    'hashes': hashes, 'pre_PL': before, 'post_PL': after,
    'overlay_download': False, 'mmio_created': False, 'gpio_writes': False,
    'parser': type(overlay.parser).__module__ + '.' + type(overlay.parser).__name__,
    'target': target, 'ip_dict_target': overlay.ip_dict.get(target),
    'mem_dict_target': overlay.mem_dict.get(target),
    'reset_gpio': overlay.gpio_dict.get('mb_iop_pmoda_reset'),
    'hwh_target_modules': [dict(m.attrib) for m in modules], 'hwh_target_memranges': ranges,
    'mem_dict_view_source': {'path': inspect.getsourcefile(mem_view), 'sha256': digest(inspect.getsourcefile(mem_view))},
    'overlay_source': {'path': inspect.getsourcefile(pynq.Overlay), 'sha256': digest(inspect.getsourcefile(pynq.Overlay))},
}
print(json.dumps(report, indent=2, default=str))

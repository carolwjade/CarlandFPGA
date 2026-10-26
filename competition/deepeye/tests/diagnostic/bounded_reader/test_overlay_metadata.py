"""Focused host controls for the observed PYNQ outer dictionary subclass.

The subclass fixture reproduces the observed container relationship; it is not
the PYNQ implementation or a hardware/runtime substitute. Root retains raw
board metadata, process exits and exact source pins separately.
"""
import argparse
from collections import UserDict
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


class ObservedContainerSurrogate(dict):
    pass


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--collector', type=Path, required=True)
    args = parser.parse_args()
    assert args.collector.is_absolute()
    raw = args.collector.read_bytes()
    name = 'deepeye_overlay_metadata_component_only'
    spec = importlib.util.spec_from_file_location(name, args.collector)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    assert 'pynq' not in sys.modules
    entry = {'fullpath': 'private_diag_0',
             'type': 'carlandfpga.local:diagnostic:deepeye_private_axi_diag:1.0',
             'phys_addr': 0x43C00000, 'addr_range': 4096}
    valid = {'private_diag_0': entry}
    cases = [('plain_dict_accepts', deepcopy(valid), True),
             ('observed_dict_subclass_accepts', ObservedContainerSurrogate(deepcopy(valid)), True),
             ('unrelated_mapping_rejected', UserDict(deepcopy(valid)), False),
             ('missing_target_rejected', {}, False)]
    duplicate = deepcopy(valid)
    duplicate['alias'] = deepcopy(entry)
    cases.append(('duplicate_target_rejected', duplicate, False))
    for label, key, value in [('fullpath', 'fullpath', 'another_module'),
                              ('vlnv', 'type', 'unrelated:ip:wrong:1.0'),
                              ('base', 'phys_addr', 0x43C01000),
                              ('range', 'addr_range', 8192)]:
        candidate = ObservedContainerSurrogate(deepcopy(valid))
        candidate['private_diag_0'][key] = value
        cases.append(('wrong_' + label + '_rejected', candidate, False))
    failed = []
    for label, ips, should_accept in cases:
        error = None
        accepted = False
        try:
            module.check_overlay(SimpleNamespace(ip_dict=ips),
                                 SimpleNamespace(base=0x43C00000, span=4096))
            accepted = True
        except module.Rejected as failure:
            error = {'type': type(failure).__name__, 'message': str(failure)}
        passed = accepted == should_accept
        if not passed:
            failed.append(label)
        print('DEEYE_OVERLAY_METADATA ' + json.dumps(
            {'case': label, 'passed': passed, 'accepted': accepted,
             'expected_accept': should_accept, 'error': error}, sort_keys=True))
    code = 1 if failed else 0
    print('DEEYE_OVERLAY_METADATA ' + json.dumps(
        {'case': 'complete', 'checks': len(cases), 'failed': failed, 'exit_code': code,
         'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_bytes': len(raw),
         'pynq_imported': 'pynq' in sys.modules, 'component_only': True,
         'real_container_replaced_by_host_surrogate': True}, sort_keys=True))
    sys.modules.pop(name)
    return code


if __name__ == '__main__':
    raise SystemExit(main())

"""Explicit derived demo profile; original C36/C37/C44/C28 defaults stay fixed."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from . import projection, verifier

PROFILE_ID = 'demo30h_ai_profile_v1'
MAX_SOURCE_AGE_NS = 5_000_000_000

@dataclass(frozen=True, slots=True)
class DemoAIProfile:
    profile_id: str
    manifest_sha256: str
    files: object
    model_sha256: str
    projection: object
    verifier: object
    max_source_age_ns: int
    package_root: str
    manifest_path: str
    age_normalization_ms: int
    original_quality_age_ns: int
    prospective_command_max_ns: int = 1_000_000_000  # New typed demo policy only; not a core action change.

def selected_profile(max_source_age_ns):
    if type(max_source_age_ns) is not int or not 0 < max_source_age_ns <= MAX_SOURCE_AGE_NS:
        raise ValueError('DEMO_AGE_LIMIT')
    root = Path(__file__).resolve().parents[3]/'ai_pc'/'demo30h_owned_package_v1'
    manifest_path = root/'package-manifest.json'
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != verifier.PACKAGE_MANIFEST_SHA256:
        raise ValueError('fixed new demo package manifest changed')
    manifest = json.loads(raw)
    names = {'c37_entry.py','c37_package.py','frozen_c28.py'}
    if type(manifest) is not dict or set(manifest)!={'schema_version','files'} or manifest['schema_version']!=1 or type(manifest['files']) is not dict or set(manifest['files'])!=names:
        raise ValueError('fixed new demo package shape changed')
    files = dict(manifest['files'])
    for name,pin in files.items():
        path = root/name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=pin:
            raise ValueError('fixed new demo package bytes changed: '+name)
    if files['frozen_c28.py'] != verifier.CORE_SHA256:
        raise ValueError('new demo model pin mismatch')
    files['package-manifest.json']=digest
    return DemoAIProfile(PROFILE_ID,digest,MappingProxyType(files),verifier.CORE_SHA256,
        projection,verifier.selected_verifier(max_source_age_ns),max_source_age_ns,
        str(root),str(manifest_path),verifier.AGE_NORMALIZATION_MS,verifier.ORIGINAL_QUALITY_AGE_NS)

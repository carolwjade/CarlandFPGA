"""Explicit derived demo profile; original C36/C37/C44/C28 defaults stay fixed."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from . import projection, verifier

PROFILE_ID = 'demo30h_ai_em3_profile_v2'
MAX_SOURCE_AGE_NS = 5_000_000_000
ENTRY_C0_MAX_SOURCE_AGE_NS = 8_000_000_000
STRICT_ENGINEERING_PROFILE = {'profile_id': 'DEEPEYE-EM3-STRICT-V2', 'sha256': '1f730ddb7739353485db554be39d8cfcb528c97eeb1917b8b0dc1fb18c1d0905'}
NAV_ENGINEERING_PROFILE = {'profile_id': 'DEEPEYE-EM3-NAV-FAST-V1', 'sha256': '11ff1d2895c46ab7135e18835e06afa5b4251665341f215eda1ede6e4969e861'}
ENTRY_C0_ENGINEERING_PROFILE = {'profile_id':'DEEPEYE-EM3-NAV-ENTRY-C0-DEMO8S-V1','sha256':'678386c5ba8fec15dd9c6f0bb19daa18e3d86af55b8b3789991b3a99be98c47f'}

ENTRY_C0_12_ENGINEERING_PROFILE = {'profile_id': 'DEEPEYE-EM3-NAV-ENTRY-C0-DEMO12S-V3', 'sha256': 'a69f7a8330ddeb3bc07278be28f6eea9b1f692c4b5076e4ea70c28664d3406dd'}
ENTRY_C0_12_MAX_SOURCE_AGE_NS = 12_000_000_000

LONG_TTL_ENGINEERING_PROFILE = {'profile_id': 'DEEPEYE-EM3-NAV-ENTRY-LONG-TTL-DEMO30S-V4', 'sha256': '5ee6930f22e29f49bb70fc4239bf58105567d2d899790f61d3d5924fcec93e36'}
LONG_TTL_MAX_SOURCE_AGE_NS = 30_000_000_000

@dataclass(frozen=True, slots=True)
class EM3NavigationProfile:
    profile_id: str
    sha256: str

NAV_FAST_V1=EM3NavigationProfile(NAV_ENGINEERING_PROFILE['profile_id'],NAV_ENGINEERING_PROFILE['sha256'])
NAV_ENTRY_C0_V1=EM3NavigationProfile(ENTRY_C0_ENGINEERING_PROFILE['profile_id'],ENTRY_C0_ENGINEERING_PROFILE['sha256'])
NAV_ENTRY_C0_12S_V3=EM3NavigationProfile(ENTRY_C0_12_ENGINEERING_PROFILE['profile_id'],ENTRY_C0_12_ENGINEERING_PROFILE['sha256'])
NAV_ENTRY_LONG_TTL_V4=EM3NavigationProfile(LONG_TTL_ENGINEERING_PROFILE['profile_id'],LONG_TTL_ENGINEERING_PROFILE['sha256'])

@dataclass(frozen=True, slots=True)
class DemoEM3AIProfile:
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
    navigation_profile: object = None
    engineering_profile: object = None
    prospective_command_max_ns: int = 1_000_000_000  # New typed demo policy only; not a core action change.

def selected_profile(max_source_age_ns, *, navigation_profile=None):
    if navigation_profile is not None and (type(navigation_profile) is not EM3NavigationProfile or navigation_profile not in (NAV_FAST_V1,NAV_ENTRY_C0_V1,NAV_ENTRY_C0_12S_V3,NAV_ENTRY_LONG_TTL_V4)):
        raise ValueError('FIXED_EM3_NAV_PROFILE')
    longttl=navigation_profile==NAV_ENTRY_LONG_TTL_V4
    entry12=navigation_profile==NAV_ENTRY_C0_12S_V3
    entry_c0=navigation_profile==NAV_ENTRY_C0_V1
    cap=LONG_TTL_MAX_SOURCE_AGE_NS if longttl else ENTRY_C0_12_MAX_SOURCE_AGE_NS if entry12 else ENTRY_C0_MAX_SOURCE_AGE_NS if entry_c0 else MAX_SOURCE_AGE_NS
    if type(max_source_age_ns) is not int or not 0 < max_source_age_ns <= cap:
        raise ValueError('DEMO_AGE_LIMIT')
    if longttl:
        from . import verifier_longttl_demo_v7 as selected_verifier
    elif entry12:
        from . import verifier_c0_demo_v5 as selected_verifier
    elif entry_c0:
        from . import verifier_c0_demo_v3 as selected_verifier
    else:
        selected_verifier=verifier
    engineering=LONG_TTL_ENGINEERING_PROFILE if longttl else ENTRY_C0_12_ENGINEERING_PROFILE if entry12 else ENTRY_C0_ENGINEERING_PROFILE if entry_c0 else NAV_ENGINEERING_PROFILE if navigation_profile is not None else STRICT_ENGINEERING_PROFILE
    root = Path(__file__).resolve().parents[3]/'ai_pc'/('demo30h_owned_em3_package_v7' if longttl else 'demo30h_owned_em3_package_v5' if entry12 else 'demo30h_owned_em3_package_v3' if entry_c0 else 'demo30h_owned_em3_package_v2')
    manifest_path = root/'package-manifest.json'
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != selected_verifier.PACKAGE_MANIFEST_SHA256:
        raise ValueError('fixed new demo package manifest changed')
    manifest = json.loads(raw)
    names = {'c37_entry.py','c37_package.py','em3_core.py'}
    if type(manifest) is not dict or set(manifest)!={'schema_version','files'} or manifest['schema_version']!=1 or type(manifest['files']) is not dict or set(manifest['files'])!=names:
        raise ValueError('fixed new demo package shape changed')
    files = dict(manifest['files'])
    for name,pin in files.items():
        path = root/name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=pin:
            raise ValueError('fixed new demo package bytes changed: '+name)
    if files['em3_core.py'] != selected_verifier.CORE_SHA256:
        raise ValueError('new demo model pin mismatch')
    files['package-manifest.json']=digest
    return DemoEM3AIProfile(PROFILE_ID,digest,MappingProxyType(files),selected_verifier.CORE_SHA256,
        projection,selected_verifier.selected_verifier(max_source_age_ns,engineering_profile=engineering),max_source_age_ns,
        str(root),str(manifest_path),selected_verifier.AGE_NORMALIZATION_MS,selected_verifier.ORIGINAL_QUALITY_AGE_NS,navigation_profile=navigation_profile,engineering_profile=MappingProxyType(dict(engineering)),prospective_command_max_ns=12_000_000_000 if longttl else 3_000_000_000 if navigation_profile is not None else 1_000_000_000)

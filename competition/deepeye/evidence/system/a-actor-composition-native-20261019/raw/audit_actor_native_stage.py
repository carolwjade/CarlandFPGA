"""Independent main audit of copied runtime bytes; no imports or native effects."""
import hashlib,json,sys,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a';HERE=OUT/'actor-native-main'
def sha(b):return hashlib.sha256(b).hexdigest()
case=sys.argv[1];assert case in ('retained-natural-exit','fixed-unbound-expiry','persistence-after-acquisition')
index=json.loads((HERE/(case+'.stage.json')).read_bytes());attempt=Path(index['attempt_directory']);stage=attempt/'source-stage'
assert attempt.parent==HERE and not (attempt/'stage-main-audit.json').exists()
proposal_raw=(attempt/'allow-proposal.json').read_bytes();assert sha(proposal_raw)==index['proposal_sha256']
proposal=json.loads(proposal_raw);assert proposal['native_execution'] is False and proposal['approved_by'] is None
for name,digest in proposal['sources'].items():assert sha((PRODUCT/name).read_bytes())==digest,name
for name,digest in proposal['staged_files'].items():assert sha((stage/name).read_bytes())==digest,name
assert {p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}==set(proposal['staged_files'])
for p in (stage,*stage.rglob('*')):
    assert not p.is_symlink() and not p.is_junction() and not(getattr(p.stat(),'st_file_attributes',0)&0x400)
    if p.is_file():assert p.stat().st_nlink==1
origin=json.loads((attempt/'origin-stage-manifest.json').read_bytes())['entries'];origin_sources=0;zip_members={}
for row in origin:
    if 'source' in row:
        raw=Path(row['source']).read_bytes();assert sha(raw)==row['sha256'] and len(raw)==row['size'];origin_sources+=1
        if 'zip_member' in row:zip_members[row['zip_member']]=row
        elif row['stage']!='fixture.py':assert (stage/row['stage']).read_bytes()==raw
    elif row['stage'] in ('python312.zip','python312._pth'):
        raw=(stage/row['stage']).read_bytes();assert sha(raw)==row['sha256'] and len(raw)==row['size']
with zipfile.ZipFile(stage/'python312.zip') as z:
    assert z.testzip() is None and set(z.namelist())==set(zip_members) and len(z.namelist())==len(zip_members)
    for name,row in zip_members.items():
        raw=z.read(name);assert sha(raw)==row['sha256'] and len(raw)==row['size']
# The pinned Windows stage_runtime uses write_text(newline=None), hence CRLF.
assert (stage/'python312._pth').read_bytes()==b'python312.zip\r\nDLLs\r\n.\r\n'
assert sha((stage/'fixture.py').read_bytes())==proposal['sources']['competition/deepeye/simulation/isolation/actor_fixture.py']=='47946ba137eb61aa9d4d2357487c28210314bd4642ad7b1b4d781d052abab3b6'
result={'case_prepared':case,'attempt_directory':str(attempt),'proposal_sha256':index['proposal_sha256'],'source_files_verified':len(proposal['sources']),'final_stage_files_verified':len(proposal['staged_files']),'origin_source_files_verified':origin_sources,'zip_members_verified':len(zip_members),'zip_crc':'passed','superseded_original_fixture':'historical origin only; final staged fixture verified against approved source','stage_bytes':index['stage_bytes'],'native_execution':False,'enabled_allow_written':False,'all29':'not_run'}
with (attempt/'stage-main-audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))

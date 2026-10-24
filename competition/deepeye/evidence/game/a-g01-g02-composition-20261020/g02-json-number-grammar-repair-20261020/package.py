from pathlib import Path
import json,hashlib,shutil,difflib
H=Path(__file__).resolve().parent;A=H.parent/'g02-gate-numeric-policy-repair-20261020'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((A/'candidate-pins.json').read_bytes())
assert not (H/'candidate').exists()
for rel in old['files']:
 p=H/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/'stage'/rel,p)
 if rel!='editor/gate_json_numbers.gd':assert sha(p)==old['files'][rel]
rel='editor/gate_json_numbers.gd';target='competition/deepeye/simulator/'+rel
before=(H/'baseline'/rel).read_text(encoding='utf8');after=(H/'candidate'/rel).read_text(encoding='utf8')
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+target,'b/'+target))
assert patch
(H/'candidate-additive.patch').write_text(patch,encoding='utf8',newline='\n')
pins={'adoption_root':'competition/deepeye/simulator','base_patch_sha256':old['patch_sha256'],'files':{k:sha(H/'candidate'/k) for k in old['files']},'additive_patch_sha256':sha(H/'candidate-additive.patch'),'additive_base_files':old['files'],'changed_files':[rel]}
(H/'candidate-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps(pins))

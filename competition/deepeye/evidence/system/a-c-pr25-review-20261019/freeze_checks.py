import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
CROOT=Path('C:/Users/CarlJade/.codex/worktrees/deepeye-c-pr25-review/FPGA多机协作开发')
HEAD='942fa309ffc8f1d32c816cfa643b009b031d7d0a';OLD='31267d6c4ae284b8788ebb457f49c4ae5a49c60c'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(CROOT),*a])
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain=v1')
checks={}
for rel,row in before['files'].items():
 current=(CROOT/rel).read_bytes();export=(OUT/'exact-git-blobs'/rel).read_bytes()
 assert sha(current)==row['checkout_sha256'] and sha(export)==row['sha256'],rel
 checks[rel]={'checkout_sha256':sha(current),'exact_blob_sha256':sha(export),'unchanged':True}
json_checks={}
for name in ('source_inventory','force_wells','splits','split_policy','label_schema','preprocessing'):
 rel='competition/deepeye/data/'+name+'.json';a=git('show',OLD+':'+rel);b=git('show',HEAD+':'+rel)
 assert a==b;json_checks[rel]=sha(b)
historical={}
for name in ('force_inventory.py','force_preprocess.py'):
 old='competition/deepeye/data/'+name;now='competition/deepeye/data/provenance/force_2020_v1/'+name
 a=git('show',OLD+':'+old);b=git('show',HEAD+':'+now);assert a==b;historical[now]={'sha256':sha(b),'matches_old_head_path':old,'historical_executed':False}
delta=git('diff','--name-only','cdbb6b4daef1ae1df324accd4d5086b48d005c6b',HEAD).decode().splitlines()
assert all(p.startswith(('competition/deepeye/evidence/ai/trace_candidate_decode/','handoffs/c/C-DEEPEYE-TRACE-CANDIDATE-DECODE-20261018-14/')) for p in delta)
save('after.json',{'head':HEAD,'clean':True,'frozen_files_unchanged':len(checks),'files':checks,'six_original_json_unchanged_from_prior_head':json_checks,'historical_snapshot_source':historical,'op14_delta_from_op12_final':delta,'op14_existing_source_test_unchanged':True,'python':sys.version,'checked_utc':datetime.now(timezone.utc).isoformat()})
logs={}
for path in sorted(OUT.glob('*.log')):
 data=path.read_bytes();logs[path.name]={'bytes':len(data),'sha256':sha(data)}
save('raw-log-hashes.json',logs)
print(json.dumps({'clean':True,'files_unchanged':len(checks),'original_json_unchanged':6,'op14_delta_files':len(delta),'historical_snapshot_hashes':historical},ensure_ascii=False))

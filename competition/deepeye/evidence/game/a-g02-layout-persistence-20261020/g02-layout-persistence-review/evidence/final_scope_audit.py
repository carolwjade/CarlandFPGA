import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path.cwd()
REVIEW = ROOT / '.planning/deepeye-resume-20261018/g02-layout-persistence-review'
PRODUCT = ROOT / '.local/deepeye-implementation-a'
GIT = Path(r'C:\Users\CarlJade\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe')
EXPECTED_HEAD = '678e01dd097f326e5bf724dc9db9e6b3e388384d'
SIX = [
    'competition/deepeye/simulator/editor/layout_codec.gd',
    'competition/deepeye/simulator/editor/layout_store.gd',
    'competition/deepeye/simulator/editor/scene_document.gd',
    'competition/deepeye/simulator/ui/shell.gd',
    'competition/deepeye/simulator/tests/test_layout_persistence.gd',
    'competition/deepeye/docs/layout_persistence.md',
]
DEPS = [
    'competition/deepeye/simulator/project.godot',
    'competition/deepeye/simulator/viewer/main.gd',
    'competition/deepeye/simulator/viewer/main.tscn',
    'competition/deepeye/simulator/tests/test_editor_document.gd',
    'competition/deepeye/docs/resource_contract.json',
]
EXPECTED_SHA = {
    SIX[0]: 'c3846c39426c7ae5042e300d02c1bb7a6705f7482318f5eb70bc095ee8ca4a72',
    SIX[1]: '6386a5d49fb2856bbcd46d1f07192842aef399220e097f92e64409e9211efe56',
    SIX[2]: 'b603c7468b2f798f68601af23bf1c78051d217f086f806aa604962032dee1f5e',
    SIX[3]: '97e96a52eea2fe1c6d0c436d1a2526553fd8a6c0c72e2f930148d7bb2a3640fc',
    SIX[4]: 'dfe81da4c6134865483e19776edf1a0f2ff79b279e694eb25a0fb1e64a0cd6b7',
    SIX[5]: '2f796aef1b0f276bea66ca54741dcc1b1c6284d156f6d7301fc9595307897a5c',
}
EXPECTED_DEP_SHA = {
    DEPS[0]: 'be6e37bfb9873eb5557aba170f3de4d4593833daf134ccde8593b9f7e3624161',
    DEPS[1]: '9d04c654aa0d64643654d2378eed631135ee9927059b8fc8a5c7d26127644083',
    DEPS[2]: 'b770eedd64ea5dea3205c324b0501d483dbb2c6d52cadbb9c24aa428b15314db',
    DEPS[3]: '3b1e79c8cde2b29122c9e0a36819eef63bdd329862ed299f84d6ce1cf1b5b430',
    DEPS[4]: '852a686a0ee261773dbc233350a6ab1d540edae0b2c3889d928caefdfc629ff4',
}
EXPECTED_STATUS = sorted([
    ' M ' + SIX[2],
    ' M ' + SIX[3],
    '?? ' + SIX[0],
    '?? ' + SIX[1],
    '?? ' + SIX[4],
    '?? ' + SIX[5],
])

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def decode_json_bytes(data):
    if data.startswith(b'\xff\xfe'):
        return data.decode('utf-16')
    if data.startswith(b'\xfe\xff'):
        return data.decode('utf-16')
    if data.startswith(b'\xef\xbb\xbf'):
        return data.decode('utf-8-sig')
    return data.decode('utf-8')

def load_pin(name):
    p = REVIEW / 'evidence' / name
    data = p.read_bytes()
    return { 'path': str(p.relative_to(ROOT)).replace('\\','/'), 'bytes': len(data), 'sha256': sha_bytes(data), 'json': json.loads(decode_json_bytes(data)) }

def git(args):
    cp = subprocess.run([str(GIT), '-C', str(PRODUCT), *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {'argv': [str(GIT), '-C', str(PRODUCT), *args], 'exit_code': cp.returncode, 'stdout': cp.stdout.decode('utf-8', 'replace'), 'stderr': cp.stderr.decode('utf-8', 'replace')}

checks = []
def check(name, ok, detail=None):
    checks.append({'name': name, 'ok': bool(ok), 'detail': detail})

before = load_pin('pins-before.stdout.json')
after = load_pin('pins-after.stdout.json')
strict = load_pin('pins-final-strict-02.stdout.json')
for label, pin in [('before',before),('after',after)]:
    check(label + '_status_passed', pin['json'].get('status') == 'passed', pin['json'].get('status'))
check('strict_status_failed_only_for_head', strict['json'].get('status') == 'failed' and strict['json'].get('failures', [{}])[0].get('name') == 'product_head', {'status':strict['json'].get('status'),'failures':strict['json'].get('failures')})
for label in ['six_files','dependencies','evidence']:
    check('before_after_' + label + '_identical', before['json'].get(label) == after['json'].get(label))
    check('after_final_' + label + '_identical', after['json'].get(label) == strict['json'].get(label))

strict_failures = strict['json'].get('failures', [])
check('strict_74_checks', len(strict['json'].get('checks', [])) == 74, len(strict['json'].get('checks', [])))
check('strict_exactly_one_head_failure', len(strict_failures) == 1 and strict_failures[0].get('name') == 'product_head', strict_failures)
non_head = [c for c in strict['json'].get('checks', []) if c.get('name') != 'product_head']
check('strict_73_nonhead_checks_pass', len(non_head) == 73 and all(c.get('ok') for c in non_head), {'count':len(non_head),'failed':[c['name'] for c in non_head if not c.get('ok')]})

head = git(['rev-parse','HEAD'])
final_head = head['stdout'].strip()
check('head_command_exit', head['exit_code'] == 0, head)
check('expected_head_preserved', EXPECTED_HEAD == strict['json'].get('expected', {}).get('product_head'), strict['json'].get('expected', {}).get('product_head'))
check('head_advanced_unrelated', final_head != EXPECTED_HEAD, {'review_start':EXPECTED_HEAD,'final':final_head})

ancestor = git(['merge-base','--is-ancestor',EXPECTED_HEAD,final_head])
check('review_start_head_is_ancestor', ancestor['exit_code'] == 0, ancestor)
head_range = git(['diff','--name-only',EXPECTED_HEAD + '..' + final_head, '--', *SIX, *DEPS])
changed_paths = [x for x in head_range['stdout'].splitlines() if x]
touched_reviewed = sorted(set(changed_paths) & set(SIX + DEPS))
check('reviewed_scope_diff_exit', head_range['exit_code'] == 0, head_range)
check('reviewed_scope_has_no_allowlisted_changes', not touched_reviewed, touched_reviewed)

status = git(['status','--porcelain=v1','--',*SIX])
status_lines = sorted(status['stdout'].splitlines())
check('candidate_status_exact', status['exit_code'] == 0 and status_lines == EXPECTED_STATUS, {'exit':status['exit_code'],'lines':status_lines})
diff_check = git(['diff','--check','--',*SIX])
check('scoped_diff_check', diff_check['exit_code'] == 0, diff_check)

source_records = []
for rel in SIX:
    p = PRODUCT / rel
    data = p.read_bytes()
    rec = {'path':rel,'bytes':len(data),'sha256':sha_bytes(data),'expected_sha256':EXPECTED_SHA[rel]}
    rec['ok'] = rec['sha256'] == rec['expected_sha256']
    source_records.append(rec)
    check('source_sha256:'+rel, rec['ok'], rec)
strict_six_by_path = {r['path']:r for r in strict['json'].get('six_files', [])}
for rec in source_records:
    check('source_matches_strict_pin:'+rec['path'], rec['sha256'] == strict_six_by_path.get(rec['path'],{}).get('sha256_actual'), {'actual':rec['sha256'],'strict_pin':strict_six_by_path.get(rec['path'],{}).get('sha256_actual')})

dep_records=[]
for rel in DEPS:
    p=PRODUCT/rel; data=p.read_bytes()
    rec={'path':rel,'bytes':len(data),'sha256':sha_bytes(data),'expected_sha256':EXPECTED_DEP_SHA[rel]}
    rec['ok']=rec['sha256']==rec['expected_sha256']
    dep_records.append(rec)
    check('dependency_sha256:'+rel, rec['ok'], rec)

strict_dep_by_path = {r['path']:r for r in strict['json'].get('dependencies', [])}
for rec in dep_records:
    check('dependency_matches_strict_pin:'+rec['path'], rec['sha256'] == strict_dep_by_path.get(rec['path'],{}).get('sha256_actual'), {'actual':rec['sha256'],'strict_pin':strict_dep_by_path.get(rec['path'],{}).get('sha256_actual')})

godot=PRODUCT/'competition/deepeye/simulator/.godot'
if godot.exists():
    files=[p for p in godot.rglob('*') if p.is_file()]
    newest=max(files, key=lambda p:p.stat().st_mtime) if files else None
    gstat=godot.stat()
    godot_record={'path':str(godot.relative_to(ROOT)).replace('\\','/'),'exists':True,'creation_time_utc':__import__('datetime').datetime.fromtimestamp(gstat.st_ctime, __import__('datetime').timezone.utc).isoformat(),'last_write_utc':__import__('datetime').datetime.fromtimestamp(gstat.st_mtime, __import__('datetime').timezone.utc).isoformat(),'file_count':len(files),'newest_file':str(newest.relative_to(ROOT)).replace('\\','/') if newest else None,'newest_write_utc':__import__('datetime').datetime.fromtimestamp(newest.stat().st_mtime, __import__('datetime').timezone.utc).isoformat() if newest else None}
else:
    godot_record={'path':str(godot.relative_to(ROOT)).replace('\\','/'),'exists':False}
check('product_godot_dir_exists_and_predates_review', godot_record['exists'] and godot_record['newest_write_utc'] < '2026-10-19T17:01:23', godot_record)

git_item=GIT.stat(); git_hash=sha_bytes(GIT.read_bytes())
git_version=subprocess.run([str(GIT),'--version'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
git_record={'path':str(GIT),'bytes':git_item.st_size,'sha256':git_hash,'version':git_version.stdout.decode('utf-8','replace').strip(),'version_exit_code':git_version.returncode}

failed=[c for c in checks if not c['ok']]
out={
    'schema':1,
    'scope':'read-only final reviewed-source/dependency/evidence and product-state audit',
    'review_start_head':EXPECTED_HEAD,
    'final_head':final_head,
    'head_advanced_during_review':final_head != EXPECTED_HEAD,
    'head_advance_note':'External main commit after the earlier 74/74 pin audits; only unrelated control-evidence paths are listed in the recorded range.',
    'reviewed_scope_changed_paths':changed_paths,
    'reviewed_scope_touched_reviewed_paths':touched_reviewed,
    'head_commit_metadata':git(['show','-s','--format=%H%n%P%n%cI','HEAD']),
    'git':git_record,
    'git_commands':[head,ancestor,head_range,status,diff_check],
    'candidate_status':status_lines,
    'sources':source_records,
    'dependencies':dep_records,
    'godot_directory':godot_record,
    'pin_files':{'before':{k:before[k] for k in ['path','bytes','sha256']},'after':{k:after[k] for k in ['path','bytes','sha256']},'strict_final':{k:strict[k] for k in ['path','bytes','sha256']}},
    'strict_final_summary':{'checks':len(strict['json'].get('checks',[])),'failures':strict_failures,'nonhead_checks_pass':len(non_head)==73 and all(c.get('ok') for c in non_head)},
    'checks':checks,
    'failures':failed,
    'status':'passed_reviewed_scope_unrelated_main_head_advance' if not failed else 'failed',
}
print(json.dumps(out,indent=2,ensure_ascii=False))
raise SystemExit(0 if not failed else 1)

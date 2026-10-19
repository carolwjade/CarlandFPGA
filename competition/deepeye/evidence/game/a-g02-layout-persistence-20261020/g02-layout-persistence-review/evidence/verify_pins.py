import hashlib, json, pathlib, subprocess, sys
ROOT = pathlib.Path.cwd()
PRODUCT = ROOT / '.local/deepeye-implementation-a'
AUTHOR_REL = pathlib.Path('.planning/deepeye-resume-20261018/g02-layout-continuation-20261020/author')
AUTHOR = ROOT / AUTHOR_REL
GIT = r'C:\Users\CarlJade\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe'
EXPECTED = {
    'manifest': 'd6149d0c55c063af52d90d2ab41b927f3f81afdf024acf3e9d61208175ddf586',
    'report': 'b5db84b2d57f398330f52908cf79308da8afba3435800002a4ce2cb5870a6b7e',
    'receipt': '4ce04cd29f6f26a4f475ca1e7ae16d07f5b79af7812238bfa890f4e608667cd1',
    'index': '1beeb40486c79dcda72c2314994c9699efe9f76ed4e7168dbc509413562a5b45',
    'design_report': '9ba018f712213c8151e07bc63eae57bdae031f7f6817ec2696e1847b129a8d1b',
    'design_plan': '945502bf23e340dc4899fb689016f9ee04858ca214ae081d1c5d12f7d6617495',
    'engine': 'c8f0a6bc45a19b33541501e57f6f7cd972ab18453743266339d495cbbe846643',
    'product_head': '678e01dd097f326e5bf724dc9db9e6b3e388384d',
    'initial_product_head': '889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()

def git(*args):
    return subprocess.check_output([GIT, '-C', str(PRODUCT), *args])

def file_record(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)).replace('\\','/'), 'bytes': len(data), 'sha256': sha(data)}

out = {'schema': 1, 'expected': EXPECTED, 'checks': [], 'failures': []}

def check(name, ok, detail=None):
    out['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail})
    if not ok:
        out['failures'].append({'name': name, 'detail': detail})

for key, filename in [('manifest','manifest.json'), ('report','report.md'), ('receipt','receipt.json'), ('index','evidence-index.json')]:
    rec = file_record(AUTHOR / filename)
    check('author_' + key + '_sha256', rec['sha256'] == EXPECTED[key], rec)

for key, rel in [('design_report','.planning/deepeye-resume-20261018/game-integration-next/report.md'), ('design_plan','.planning/deepeye-resume-20261018/game-integration-next/plan.md')]:
    rec = file_record(ROOT / rel)
    check(key + '_sha256', rec['sha256'] == EXPECTED[key], rec)

head = git('rev-parse','HEAD').decode().strip()
check('product_head', head == EXPECTED['product_head'], head)
manifest = json.loads((AUTHOR/'manifest.json').read_text(encoding='utf-8-sig'))
check('manifest_task', manifest.get('task_id') == 'DEEPEYE-IMPLEMENTATION-20261014' and manifest.get('task_version') == 1, {'task_id':manifest.get('task_id'),'task_version':manifest.get('task_version')})
check('manifest_initial_head', manifest.get('initial_head_observed_at_task_start') == EXPECTED['initial_product_head'], manifest.get('initial_head_observed_at_task_start'))
check('manifest_current_head', manifest.get('current_head_at_manifest_time') == EXPECTED['product_head'], manifest.get('current_head_at_manifest_time'))
check('manifest_head_advance_unrelated', manifest.get('head_advanced_by_main_not_this_child') is True and manifest.get('head_advance_affects_layout_six') is False, {'by_main':manifest.get('head_advanced_by_main_not_this_child'),'affects_six':manifest.get('head_advance_affects_layout_six')})

six_results=[]
for item in manifest.get('six_file_manifest', []):
    rel = item['path']
    p = PRODUCT / rel
    data = p.read_bytes()
    rec = {'path':rel, 'bytes':len(data), 'sha256_actual':sha(data), 'sha256_manifest':item.get('sha256'),
           'bytes_manifest':item.get('bytes'), 'lines_actual':data.count(b'\n'), 'lines_manifest':item.get('lines'),
           'raw_git_blob_sha1':git_blob(data), 'git_blob_sha1_manifest':item.get('git_blob_sha1'),
           'ends_with_lf':data.endswith(b'\n'), 'crlf_count':data.count(b'\r\n')}
    check('six_sha256:'+rel, rec['sha256_actual']==item.get('sha256'), rec)
    check('six_bytes:'+rel, len(data)==item.get('bytes'), rec)
    check('six_lines:'+rel, data.count(b'\n')==item.get('lines'), rec)
    check('six_ends_lf:'+rel, data.endswith(b'\n') and item.get('ends_with_lf') is True, rec)
    if rel.endswith('layout_persistence.md'):
        lf = data.replace(b'\r\n',b'\n')
        rec['lf_git_blob_sha1'] = git_blob(lf)
        rec['raw_sha256'] = sha(data)
        rec['lf_sha256'] = sha(lf)
        rec['classification'] = 'documented Git clean/text normalization; manifest pins clean LF blob while actual bytes are CRLF'
        check('doc_actual_raw_sha256_matches', sha(data)==item.get('sha256'), rec)
        check('doc_clean_lf_blob_matches_manifest', git_blob(lf)==item.get('git_blob_sha1'), rec)
        check('doc_actual_bytes_are_crlf', b'\r\n' in data, rec)
    else:
        check('six_raw_git_blob:'+rel, git_blob(data)==item.get('git_blob_sha1'), rec)
    six_results.append(rec)
out['six_files'] = six_results
check('six_file_count', len(six_results)==6, len(six_results))

dep_results=[]
for item in manifest.get('dependencies_before_after', []):
    rel=item['path']; p=PRODUCT/rel; data=p.read_bytes()
    base_data=git('show',EXPECTED['initial_product_head']+':'+rel)
    rec={'path':rel,'sha256_actual':sha(data),'before':item.get('before_sha256'),'after':item.get('after_sha256'),
         'base_sha256':sha(base_data),'raw_git_blob_sha1':git_blob(data),'manifest_blob':item.get('current_git_blob_sha1')}
    check('dependency_actual_after:'+rel, rec['sha256_actual']==item.get('after_sha256'), rec)
    check('dependency_before_after_equal:'+rel, item.get('before_sha256')==item.get('after_sha256'), rec)
    check('dependency_equal_initial_head:'+rel, rec['sha256_actual']==rec['base_sha256'], rec)
    check('dependency_git_blob:'+rel, rec['raw_git_blob_sha1']==item.get('current_git_blob_sha1'), rec)
    dep_results.append(rec)
out['dependencies'] = dep_results
check('dependency_count', len(dep_results)==5, len(dep_results))

engine_p = ROOT / manifest['engine']['path']
engine_data = engine_p.read_bytes()
engine_rec=file_record(engine_p)
check('engine_sha256', engine_rec['sha256']==EXPECTED['engine'], engine_rec)

index = json.loads((AUTHOR/'evidence-index.json').read_text(encoding='utf-8-sig'))
ev_results=[]
for item in index.get('files',[]):
    p=ROOT/item['path']
    if not p.is_file():
        ev_results.append({'path':item['path'],'exists':False}); out['failures'].append({'name':'evidence_missing','detail':item['path']}); continue
    data=p.read_bytes(); rec={'path':item['path'],'exists':True,'bytes':len(data),'bytes_expected':item.get('bytes'),'sha256':sha(data),'sha256_expected':item.get('sha256')}
    ok=rec['bytes']==item.get('bytes') and rec['sha256']==item.get('sha256')
    rec['ok']=ok
    if not ok: out['failures'].append({'name':'evidence_hash','detail':rec})
    ev_results.append(rec)
out['evidence'] = ev_results
check('evidence_file_count', len(ev_results)==48, len(ev_results))
check('evidence_all_match', all(x.get('ok') for x in ev_results), sum(1 for x in ev_results if x.get('ok')))

audit_p = ROOT/'.planning/deepeye-resume-20261018/g02-layout-author-handoff-audit.json'
audit_data = audit_p.read_bytes()
audit = json.loads(audit_data.decode('utf-8-sig'))
out['audit'] = {'path':str(audit_p.relative_to(ROOT)).replace('\\','/'),'bytes':len(audit_data),'sha256':sha(audit_data),
                'original_job':audit.get('original_job'),'terminal':audit.get('terminal'),'source_files':audit.get('source_files'),
                'dependencies':audit.get('dependencies'),'evidence_files':audit.get('evidence_files')}
check('audit_original_job', audit.get('original_job')=='child-9d0281a0ffd54a8c99db1ad653d1d39c', out['audit'])
check('audit_terminal_and_counts', audit.get('terminal') is True and audit.get('source_files')==6 and audit.get('dependencies')==5 and audit.get('evidence_files')==48, out['audit'])
check('audit_manifest_pin', audit.get('manifest_sha256')==EXPECTED['manifest'], audit.get('manifest_sha256'))
check('audit_report_pin', audit.get('report_sha256')==EXPECTED['report'], audit.get('report_sha256'))
check('audit_receipt_pin', audit.get('receipt_sha256')==EXPECTED['receipt'], audit.get('receipt_sha256'))
check('audit_index_pin', audit.get('index_sha256')==EXPECTED['index'], audit.get('index_sha256'))

out['status']='passed' if not out['failures'] else 'failed'
print(json.dumps(out, indent=2, ensure_ascii=False))
sys.exit(0 if out['status']=='passed' else 1)


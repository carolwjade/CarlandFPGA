from pathlib import Path
import hashlib,json,os,re,subprocess
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';A=O.parent/'passage-suffix-implementation'
def sha(data):return hashlib.sha256(data).hexdigest()
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
before=json.loads((O/'before.json').read_bytes());after=json.loads((O/'after.json').read_bytes());env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
git_checks=[]
def git(args,data=None):
    cmd=['git','-C',str(P),*args];run=subprocess.run(cmd,input=data,capture_output=True,env=env)
    git_checks.append({'command':cmd,'exit_code':run.returncode,'stderr':run.stderr.decode('utf8','replace')})
    assert run.returncode==0
    return run.stdout
for name,want in after['sources'].items():
    base=git(['show',before['head']+':'+name]);old=(A/'before'/name).read_bytes();assert base==old,name
    raw=(P/name).read_bytes();assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
    raw_blob=git(['hash-object','--stdin'],raw).decode().strip();clean=git(['hash-object','--path='+name,'--stdin'],raw).decode().strip()
    assert raw_blob==clean
    git_checks[-1].update(raw_blob=raw_blob,clean_blob=clean,base_matches_before_raw=True)
save('base-and-clean-byte-checks.json',git_checks)
provenance={}
for name in ('red','red-corrected','red-duration','green-release'):
    metadata=json.loads((A/(name+'.json')).read_bytes());raw=(A/(name+'.stderr.bin')).read_bytes()
    text=raw.decode('utf8','replace');last=re.search(r'Ran (\d+) tests?[^\n]*',text)
    status=re.findall(r'(?:FAILED \([^\n]+\)|OK(?: \([^\n]+\))?)',text)
    provenance[name]={'exit_code':metadata['exit_code'],'tests':int(last.group(1)) if last else None,
        'final_status':status[-1] if status else None,'stderr_sha256':sha(raw),
        'jsonschema_setup_error':'ModuleNotFoundError' in text and 'jsonschema' in text}
assert provenance['red']['jsonschema_setup_error'] is True
assert provenance['red-corrected']['tests']==43 and provenance['red-corrected']['exit_code']==1
assert provenance['red-duration']['tests']==45 and provenance['red-duration']['exit_code']==1
assert provenance['green-release']['tests']==253 and provenance['green-release']['exit_code']==0
save('author-red-green-provenance.json',provenance)
for label,count in (('253',253),('independent',7)):
    metadata=json.loads((O/(label+'.command.json')).read_bytes());assert metadata['exit_code']==0
    raw=(O/(label+'.stderr.bin')).read_bytes()
    assert ('Ran '+str(count)+' tests').encode() in raw
    # A test name itself contains "rejected_not_skipped"; only the final unittest
    # summary establishes the skip count, not a substring scan of all names.
    assert raw.decode('utf8').strip().splitlines()[-1].strip()=='OK'
receipt={'work_id':'A-passage-suffix-independent-review-20261019-v1','job_id':'child-b64d7ef1c5ec4940bef803aceb15f586',
    'reviewer':'/root/r03_review_20261018','result':'no blocking finding in exact frozen numerical candidate; main acceptance retained',
    'head_before':before['head'],'head_after':after['head'],'candidate_manifest_sha256':'c4b5b656e78a084e36e8bfcedfdb2f65144226d8af7b336f4588cc4352df6657',
    'sources':after['sources'],'dependencies_unchanged':len(after['dependencies']),'design_evidence_unchanged':len(after['old_design_evidence']),
    'author_evidence_files_unchanged':len(before['author_evidence']),'regressions':{'tests':253,'exit_code':0,'skips':0},
    'independent':{'methods':7,'exit_code':0,'three_slice_ramp':True,'certificate_corruption_explicitly_labeled':True,
                   'real_compound_cylinder_tail_rejection':True,'actual_runtime_final_fence_and_single_publication':True},
    'base_before_raw_equal':True,'owned_utf8_lf_raw_equals_git_clean':True,'source_read_only':True,
    'formal_acceptance':'all29 cards and both actual H12 chains not_run',
    'requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804',
    'design_sha256':'2e0b5eaa18f6e1197befc5fd1e76513f3e54b0199823827e2fb6994777800596'}
save('receipt.json',receipt)
print(json.dumps({'receipt_sha256':sha((O/'receipt.json').read_bytes()),'regressions':253,'independent':7,'result':'PASS numerical scope'},indent=2))

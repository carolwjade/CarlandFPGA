import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'


def digest(path):
    data=path.read_bytes()
    return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def save(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


baseline=json.loads((HERE/'baseline.json').read_text(encoding='utf-8'))
green=json.loads((HERE/'green-release.json').read_text(encoding='utf-8'))
assert green['exit_code']==0
assert b'Ran 253 tests' in (HERE/'green-release.stderr.bin').read_bytes()
unchanged={}
for relative,expected in baseline['files'].items():
    if relative not in baseline['owned']:
        assert digest(PRODUCT/relative)==expected,relative
        unchanged[relative]=expected
for relative,expected in baseline['old_evidence'].items():
    assert digest(ROOT/relative)==expected,relative
manifest,clean,diff={},[],[]
env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0'
for relative in baseline['owned']:
    source=PRODUCT/relative
    raw=source.read_bytes();raw.decode('utf-8')
    assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf'),relative
    value=digest(source)
    assert value==green['sources'][relative],relative
    destination=HERE/'frozen'/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    assert digest(destination)==value
    manifest[relative]=value
    commands=[['git','-C',str(PRODUCT),'hash-object','--no-filters',relative],
              ['git','-C',str(PRODUCT),'hash-object','--path='+relative,relative]]
    outputs=[]
    for command in commands:
        result=subprocess.run(command,env=env,capture_output=True)
        assert result.returncode==0,result.stderr
        outputs.append(result.stdout.decode('ascii').strip())
    assert outputs[0]==outputs[1],relative
    clean.append({'path':relative,'utf8_lf':True,'raw_blob_oid':outputs[0],
                  'clean_blob_oid':outputs[1],'equal':True,'commands':commands})
    before=(HERE/'before'/relative).read_text(encoding='utf-8').splitlines(keepends=True)
    diff.extend(difflib.unified_diff(before,raw.decode('utf-8').splitlines(keepends=True),
        fromfile='before/'+relative,tofile='after/'+relative))
save('source-manifest.json',manifest)
save('git-clean-verification.json',clean)
save('dependencies-after.json',{'unchanged':unchanged,'old_design_evidence_unchanged':baseline['old_evidence']})
(HERE/'source.diff').write_text(''.join(diff),encoding='utf-8',newline='\n')
# Original subprocess bytes stay untouched in .bin; these readable companions
# explicitly normalize CRLF to LF and are not labeled raw evidence.
for path in HERE.glob('*.bin'):
    text=path.read_bytes().decode('utf-8').replace('\r\n','\n').replace('\r','\n')
    path.with_suffix('.log').write_text(text,encoding='utf-8',newline='\n')
head=subprocess.check_output(['git','-C',str(PRODUCT),'rev-parse','HEAD'],env=env,text=True).strip()
save('freeze-status.json',{'head':head,'source_files':len(manifest),'unowned_dependencies_unchanged':len(unchanged),
    'old_design_evidence_files_unchanged':len(baseline['old_evidence']),'raw_equals_git_clean':True,
    'utf8_lf':True,'tests':253,'test_exit':0,'formal_acceptance':'not_run'})
print(json.dumps(json.loads((HERE/'freeze-status.json').read_text(encoding='utf-8')),indent=2))

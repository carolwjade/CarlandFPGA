from pathlib import Path
import hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'.local/deepeye-implementation-a'
OWN=['competition/deepeye/'+n for n in ('simulation/authority/motion/workspace_boundaries.py','simulation/authority/motion/passage_phase.py','tests/simulation/test_workspace_boundaries.py','tests/simulation/test_passage_phase.py','docs/workspace_passage.md')]
def sha(b):return hashlib.sha256(b).hexdigest()
def command(name,args,input=None):
    r=subprocess.run(args,cwd=P,input=input,capture_output=True)
    (O/(name+'.stdout.log')).write_bytes(r.stdout);(O/(name+'.stderr.log')).write_bytes(r.stderr)
    (O/(name+'.command.json')).write_text(json.dumps({'argv':args,'cwd':str(P),'exit_code':r.returncode},indent=2)+'\n',encoding='utf-8')
    assert r.returncode==0,(name,r.returncode,r.stderr)
    return r.stdout
before=json.loads((O/'before.json').read_text('utf-8'))
prior=json.loads((O.parent/'entry-role-refinement/dependencies-final.json').read_text('utf-8'))
for n,record in before.items():assert record['sha256']==prior['files'][n]['raw_sha256'],n
unaffected={}
for n in before:
    if n not in OWN:
        raw=(P/n).read_bytes();assert sha(raw)==before[n]['sha256'],n
        unaffected[n]={'sha256':sha(raw),'bytes':len(raw)}
for label,expected in [('red1',1),('focused1',0),('focused2',0),('regression1',0)]:
    data=json.loads((O/(label+'.command.json')).read_text('utf-8'));assert data['exit_code']==expected
    assert data['before']==data['after'],label+' changed sources during test'
regression=json.loads((O/'regression1.command.json').read_text('utf-8'))
candidate={}
for n in OWN:
    raw=(P/n).read_bytes();assert sha(raw)==regression['before'][n]['sha256'],n
    dest=O/'candidate'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    raw_blob=command('raw-'+Path(n).stem,['git','hash-object','--stdin'],raw).decode().strip()
    clean_blob=command('clean-'+Path(n).stem,['git','hash-object','--path='+n,'--stdin'],raw).decode().strip()
    assert raw_blob==clean_blob,'candidate normalization drift '+n
    candidate[n]={'sha256':sha(raw),'bytes':len(raw),'raw_git_blob':raw_blob,'git_clean_blob':clean_blob}
command('owned-diff',['git','diff','--no-ext-diff','--',*OWN])
command('diff-check',['git','diff','--check','--',*OWN])
manifest={'work_id':'A-entry-bridge-implementation-20261019-v1','job_id':'child-a69ad47a35414c86870f4e9c36ae24a7',
 'owner':'/root/r03_review_20261018','base_head':'3f702903f1e16fa72eae15f03ba431b78de24bd0',
 'requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804',
 'candidate':candidate,'unaffected':unaffected,'candidate_raw_equals_git_clean':True,
 'formal_cards':'all29 not_run','design_selection_sha256':sha((O.parent/'bridge-and-actor-main-selection.json').read_bytes())}
(O/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
sys.path.insert(0,str(P));sys.path.insert(1,str(ROOT/'.local/deepeye-host-deps'))
from competition.deepeye.tests.simulation import test_passage_phase as fx
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
fixture=fx.PassagePhaseTests();fixture.setUp();state=fixture.numerical_seed('ENTRY_CROSSING',(0,0,14.4815))
result=fixture.step(state,path=fixture.path(state,yaw=7000))
assert result.status=='SAFE' and len(result.bridges)==1
(O/'nominal-witness.json').write_text(json.dumps(w._canonical(result),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_manifest_sha256':sha((O/'source-manifest.json').read_bytes()),'five_candidate_files':candidate,'unchanged_dependencies':len(unaffected)}))

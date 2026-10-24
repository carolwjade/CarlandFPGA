from pathlib import Path
import hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'.local/deepeye-implementation-a'
OWN=['competition/deepeye/'+n for n in ('simulation/authority/motion/workspace_boundaries.py','simulation/authority/motion/passage_phase.py','tests/simulation/test_workspace_boundaries.py','tests/simulation/test_passage_phase.py','docs/workspace_passage.md')]
def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot():
    old=json.loads((O.parent/'entry-role-refinement/dependencies-final.json').read_text('utf-8'))
    deps={n:{'sha256':sha((P/n).read_bytes()),'bytes':(P/n).stat().st_size} for n in old['files']}
    scope=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text('utf-8'))
    assert sha(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    return deps
label=sys.argv[1]
if label=='before':
    data=snapshot();(O/'before.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    for n in OWN:
        target=O/'baseline'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((P/n).read_bytes())
    print('baseline saved');raise SystemExit()
assert not (O/(label+'.command.json')).exists(),'do not overwrite run'
if label.startswith('red'):
    modules=['competition.deepeye.tests.simulation.test_passage_phase.PassagePhaseTests.test_bridge_preserves_entered_window_and_full_original_step']
elif label.startswith('focused'):
    modules=['competition.deepeye.tests.simulation.test_'+s for s in ('workspace_boundaries','passage_phase')]
else:
    modules=json.loads((O.parent/'passage-suffix-review/253.command.json').read_text('utf-8'))['command'][6:]
env=os.environ.copy();env['PYTHONPATH']=str(P)+';'+str(ROOT/'.local/deepeye-host-deps');temp=O/'temp';temp.mkdir(exist_ok=True)
env['TMP']=env['TEMP']=str(temp)
cmd=[sys.executable,'-B','-X','utf8','-m','unittest','-v',*modules]
before=snapshot();result=subprocess.run(cmd,cwd=P,env=env,capture_output=True)
(O/(label+'.stdout.log')).write_bytes(result.stdout);(O/(label+'.stderr.log')).write_bytes(result.stderr)
(O/(label+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(P),'exit_code':result.returncode,'PYTHONPATH':env['PYTHONPATH'],'TEMP':str(temp),'before':before,'after':snapshot()},indent=2)+'\n',encoding='utf-8')
print(result.stderr.decode('utf-8'));raise SystemExit(result.returncode)

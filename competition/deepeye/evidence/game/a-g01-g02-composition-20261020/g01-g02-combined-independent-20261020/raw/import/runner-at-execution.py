from pathlib import Path
import datetime, difflib, hashlib, importlib.util, json, math, os, re, shutil, struct, subprocess, sys, time
from fractions import Fraction
E=Path(__file__).resolve().parent
R=E.parents[2]; B=E.parent
C=B/'g01-g02-combined-headless-20261020'; S=E/'stage'
G=B/'g02-json-number-grammar-repair-20261020'
F=B/'g01-asset-adapter-repair-independent-20261020'
P=R/'.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE=R/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def dump(name,x):
 p=E/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def files(p,cache=False):
 return {q.relative_to(p).as_posix():dict(bytes=q.stat().st_size,sha256=sha(q)) for q in sorted(p.rglob('*')) if q.is_file() and (cache or '.godot' not in q.parts) and '__pycache__' not in q.parts and q.name!='lease.private.json'}
def diff(a,b): return {k:dict(before=a.get(k),after=b.get(k)) for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)}
def protected():
 return {str(p.relative_to(R)):files(p) for p in [P,C,G,F,B/'layout-path-nul-main-20261020',B/'headless-font-nul-diagnosis-20261020',B/'g01-asset-adapter-independent-20261020',B/'g01-asset-adapter-implementation-20261020']}
def prepare():
 scope=read(R/'docs/competition/deepeye-2026/immutable_scope.json')
 assert hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==CONTRACT
 assert [x['id'] for x in scope['requirements']]==['H%02d'%i for i in range(1,16)]
 transfer=read(R/'.planning/deepeye-desktop-handoff-20261015/transfer.json')
 assert transfer['status']=='active' and transfer['director_generation']==2 and transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
 assert sha(ENGINE)==PIN
 assert files(C/'candidate/simulator')==read(C/'candidate-source-pins.json')
 before=protected();dump('source-before.json',dict(protected=before,requirements_sha256=CONTRACT,engine_sha256=PIN,node_id='A',project_id='fpga-main',transfer_sha256=sha(R/'.planning/deepeye-desktop-handoff-20261015/transfer.json')))
 if not S.exists():shutil.copytree(C/'candidate/simulator',S)
 # Unchanged original input/oracle corpus; never regenerate the observations.
 for name in ['test_gate_numeric.gd','test_gate_reader.gd','numeric_cases.json','reader_cases.json']:
  shutil.copyfile(G/'stage/tests'/name,S/'tests'/name)
 old=E/'old-store-stage'
 if not old.exists():shutil.copytree(C/'candidate/simulator',old)
 shutil.copyfile(B/'layout-path-nul-main-20261020/baseline/layout_store.gd',old/'editor/layout_store.gd')
 assert sha(old/'editor/layout_store.gd')=='6386a5d49fb2856bbcd46d1f07192842aef399220e097f92e64409e9211efe56'
 assert diff(files(C/'candidate/simulator'),files(old)).keys()=={'editor/layout_store.gd'}
 oldstore=(old/'editor/layout_store.gd').read_text(encoding='utf8');newstore=(S/'editor/layout_store.gd').read_text(encoding='utf8')
 assert oldstore.replace('path.find("\\u0000") != -1','path.to_utf8_buffer().has(0)')==newstore
 (E/'unicode-path.diff').write_text(''.join(difflib.unified_diff(oldstore.splitlines(True),newstore.splitlines(True),fromfile='old/layout_store.gd',tofile='candidate/layout_store.gd')),encoding='utf8')
 oldgrammar=(G/'baseline/editor/gate_json_numbers.gd').read_text(encoding='utf8');newgrammar=(S/'editor/gate_json_numbers.gd').read_text(encoding='utf8')
 (E/'grammar.diff').write_text(''.join(difflib.unified_diff(oldgrammar.splitlines(True),newgrammar.splitlines(True),fromfile='base/gate_json_numbers.gd',tofile='candidate/gate_json_numbers.gd')),encoding='utf8')
 for mode in ['bad-license','signature','empty-visual','null']:
  dest=E/('fixture-'+mode);shutil.copytree(C/'candidate/simulator',dest)
  src=F/('fixture-'+mode)
  for rel in ['tests/test_failure_review.gd','review-mode.txt','world/asset_library.gd']:shutil.copyfile(src/rel,dest/rel)
  assert sha(dest/'tests/test_failure_review.gd')==sha(B/'g01-asset-adapter-independent-20261020/test_failure_review.gd')
 dump('stage-initial-manifest.json',files(S));dump('preparation.json',dict(candidate_exact=True,source_files=len(read(C/'candidate-source-pins.json')),original_unicode_test_sha256=sha(S/'tests/test_layout_unicode_path.gd'),numeric_inputs={n:sha(S/'tests'/n) for n in ['test_gate_numeric.gd','test_gate_reader.gd','numeric_cases.json','reader_cases.json']}))
 print('Prepared exact candidate and private old-store/failure clones; contract verified.')
def run(label,stage,script,expected='',code=0):
 stage=E/stage;out=E/'raw'/label;out.mkdir(parents=True,exist_ok=False)
 argv=[str(ENGINE),'--headless','--path',str(stage)]+(['--editor','--import'] if script=='import' else ['--script',script])
 assert sha(ENGINE)==PIN and stage.is_relative_to(E)
 env=os.environ.copy();overrides={'PYTHONDONTWRITEBYTECODE':'1'}
 for k in ['APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']:
  d=E/'private-env'/label/k;d.mkdir(parents=True,exist_ok=True);overrides[k]=str(d)
 env.update(overrides)
 rec=dict(argv=argv,cwd=str(stage),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment_overrides=overrides,creationflags=subprocess.CREATE_NO_WINDOW,timeout_seconds=55,executable_sha256=PIN,harness_sha256=sha(Path(__file__)),source_before=files(stage),cache_before=files(stage,True),expected_summary=expected,expected_exit=code)
 def save(): dump('raw/'+label+'/result.json',rec)
 save();start=time.monotonic()
 with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
  proc=subprocess.Popen(argv,cwd=stage,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);rec['pid']=proc.pid;save()
  try:rec.update(exit_code=proc.wait(timeout=55),timed_out=False)
  except subprocess.TimeoutExpired:proc.kill();rec.update(exit_code=proc.wait(timeout=5),timed_out=True)
 rec.update(terminal=proc.poll() is not None,elapsed_seconds=time.monotonic()-start,source_after=files(stage),cache_after=files(stage,True),stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'))
 rec['source_delta']=diff(rec['source_before'],rec['source_after']);rec['generated_cache_delta']=diff(rec['cache_before'],rec['cache_after'])
 text=(out/'stdout.txt').read_text(encoding='utf8',errors='replace')+(out/'stderr.txt').read_text(encoding='utf8',errors='replace')
 rec['script_errors']=any(s in text for s in ['SCRIPT ERROR','Parse Error','Compile Error'])
 rec['nul_diagnostics']=text.count('NUL');rec['error_lines']=[s for s in text.splitlines() if 'ERROR:' in s or 'Unicode parsing error' in s or 'WARNING:' in s]
 rec['eligible']=rec['terminal'] and not rec['timed_out'] and not rec['script_errors'] and rec['exit_code']==int(code) and expected in text
 for name in ['numeric_observations.json']:
  if label=='numeric' and (stage/'tests'/name).exists():shutil.copyfile(stage/'tests'/name,out/name)
 save();print(json.dumps({k:rec[k] for k in ['pid','exit_code','terminal','timed_out','eligible','nul_diagnostics','error_lines']}));print(text[-1700:])
 assert rec['eligible'],label
def evidence(label,receipt,out,err,deps,stage):
 d=read(receipt);assert d['terminal'] and d['exit_code']==0 and not d.get('timed_out',d.get('timeout',False))
 assert d.get('executable_sha256',d.get('engine_sha256'))==PIN
 assert sha(out)==d['stdout_sha256'] and sha(err)==d['stderr_sha256']
 before=d.get('source_before',d.get('source_manifest_before',d.get('source_manifest')));after=d.get('source_after',d.get('source_manifest_after',d.get('source_manifest')))
 def norm(m):return {x['path']:x['sha256'] for x in m} if isinstance(m,list) else {k:(v['sha256'] if isinstance(v,dict) else v) for k,v in m.items()}
 before=norm(before);after=norm(after)
 for rel in deps:assert sha(S/rel)==sha(stage/rel)==before[rel]==after[rel],(label,rel)
 text=out.read_text(encoding='utf8')+err.read_text(encoding='utf8');assert 'SCRIPT ERROR' not in text and 'Parse Error' not in text and 'failures=0' in text
 return dict(label=label,receipt=str(receipt.relative_to(R)),receipt_sha256=sha(receipt),stdout_sha256=sha(out),stderr_sha256=sha(err),verified_dependencies=deps,terminal=True,exit_code=0,diagnostics=[x for x in text.splitlines() if 'ERROR:' in x or 'Unicode parsing error' in x],argv=d['argv'],pid=d['pid'])
def reuse():
 deps=['editor/gate_json_numbers.gd','editor/gate_numeric.gd','editor/layout_codec.gd','editor/scene_document.gd']
 result=evidence('grammar176',G/'raw/grammar-state-final/result.json',G/'raw/grammar-state-final/stdout.txt',G/'raw/grammar-state-final/stderr.txt',deps,G/'stage')
 d=read(G/'raw/grammar-state-final/result.json')
 more=['tests/grammar_probe.gd','tests/grammar_cases.json']+['grammar-fixtures/'+p.name for p in (G/'stage/grammar-fixtures').iterdir()]
 for rel in more:assert sha(G/'stage'/rel)==d['source_before'][rel]==d['source_after'][rel]
 assert 'GRAMMAR checks=176 failures=0' in (G/'raw/grammar-state-final/stdout.txt').read_text(encoding='utf8')
 result['exact_harness_dependencies']={p:sha(G/'stage'/p) for p in more}
 # Verify source fixture oracle and all 85 row oracles independently with CPython.
 rows=read(G/'stage/tests/grammar_cases.json')
 for row in rows:
  try:json.loads(row['text']);want=True
  except json.JSONDecodeError:want=False
  assert want==row['want']
 ob=read(G/'raw/grammar-state-final/grammar_observations.json');assert ob['checks']==176 and ob['failures']==0
 for item in ob['observations']:
  assert item['accepted']==item['want']
  if item['kind']=='obstacle':
   try:json.loads(item['text']);want=True
   except json.JSONDecodeError:want=False
   assert want==item['accepted']
 result['grammar_observations_sha256']=sha(G/'raw/grammar-state-final/grammar_observations.json')
 bfolder=B/'g01-asset-adapter-implementation-20261020';d=read(bfolder/'final-assets.json')
 deps=next(x['verified_dependencies'] for x in read(F/'exact-evidence-reuse.json') if x['label']=='final-assets')
 b=evidence('B622',bfolder/'final-assets.json',bfolder/'final-assets.stdout.txt',bfolder/'final-assets.stderr.txt',deps,Path(d['cwd']))
 assert 'checks=622 failures=0' in (bfolder/'final-assets.stdout.txt').read_text(encoding='utf8')
 assert len(b['diagnostics'])==1 and "unknown obstacle kind 'bogus_kind'" in b['diagnostics'][0]
 dump('exact-evidence-reuse.json',[result,b]);print('Verified reusable grammar176 and B622 exact transitive dependencies, original oracles/logs/terminals. F1-F4 dependencies changed; targeted harnesses run fresh.')
def analyze():
 authority=R/'.local/deepeye-implementation-a/competition/deepeye/simulation/authority/motion/gate_geometry.py'
 assert sha(authority)==sha(G/'oracle/gate_geometry.py')
 spec=importlib.util.spec_from_file_location('current_gate',authority);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 cases=read(S/'tests/numeric_cases.json');obs=read(E/'raw/numeric/numeric_observations.json');assert len(cases)==len(obs)==2100
 legal=0
 for row,ob in zip(cases,obs):
  vals=struct.unpack('<4d',bytes.fromhex(row['hex']))
  good=all(math.isfinite(v) and abs(v)<=14.85 for v in vals) and (row['entry_face']!=row['exit_face'] or sum((Fraction(vals[j])-Fraction(vals[j+2]))**2 for j in [0,1])>=Fraction(.3)**2)
  try:module.validate_gate_pair(module.Gate(row['entry_face'],*vals[:2]),module.Gate(row['exit_face'],*vals[2:]));actual=True
  except (TypeError,ValueError):actual=False
  assert good==actual==row['want']==ob['valid']==ob['encoded']==ob['decoded']
  if good:
   legal+=1;assert ob['reopened_hex']==row['hex'];gates=json.loads(ob['wire'])['layout']['gates'];assert struct.pack('<4d',gates['entry']['u'],gates['entry']['v'],gates['exit']['u'],gates['exit']['v']).hex()==row['hex']
 assert legal==1116
 dump('numeric-oracle-verification.json',dict(rows=2100,legal_exact_roundtrips=legal,oracle_disagreements=0,authority_sha256=sha(authority),fraction_rule='exact rational same-face distance against binary64 .3 squared',corpus_sha256=sha(S/'tests/numeric_cases.json'),observations_sha256=sha(E/'raw/numeric/numeric_observations.json')))
 print('Independently verified 2100 original cases, 1116 legal exact binary64 roundtrips; Fraction/current Gate oracle disagreements=0.')
if __name__=='__main__':
 action=sys.argv[1]
 if action=='prepare':prepare()
 elif action=='run':run(*sys.argv[2:])
 elif action=='reuse':reuse()
 elif action=='analyze':analyze()

from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess, sys, time
import review as v
E=v.E; R=v.R; S=v.S; G=v.G
def bounded_audit(action,label):
 out=E/'raw'/label;out.mkdir(parents=True,exist_ok=False)
 argv=[sys.executable,'-B','-X','utf8',str(E/'review.py'),action]
 env=os.environ.copy();overrides={'PYTHONDONTWRITEBYTECODE':'1'}
 for key in ['APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']:
  p=E/'private-env'/label/key;p.mkdir(parents=True,exist_ok=True);overrides[key]=str(p)
 env.update(overrides);before=v.files(S)
 rec=dict(argv=argv,cwd=str(E),environment_overrides=overrides,creationflags=subprocess.CREATE_NO_WINDOW,timeout_seconds=55,executable_sha256=v.sha(Path(sys.executable)),script_sha256=v.sha(E/'review.py'),source_before=before,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 def save():v.dump('raw/'+label+'/result.json',rec)
 save();start=time.monotonic()
 with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
  p=subprocess.Popen(argv,cwd=E,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);rec['pid']=p.pid;save()
  try:rec.update(exit_code=p.wait(timeout=55),timed_out=False)
  except subprocess.TimeoutExpired:p.kill();rec.update(exit_code=p.wait(timeout=5),timed_out=True)
 rec.update(terminal=p.poll() is not None,elapsed_seconds=time.monotonic()-start,source_after=v.files(S),stdout_sha256=v.sha(out/'stdout.txt'),stderr_sha256=v.sha(out/'stderr.txt'))
 rec['source_unchanged']=rec['source_before']==rec['source_after'];save()
 print((out/'stdout.txt').read_text(encoding='utf8'));print((out/'stderr.txt').read_text(encoding='utf8'))
 assert rec['exit_code']==0 and rec['terminal'] and not rec['timed_out'] and rec['source_unchanged']
def publication():
 names=['test_gate_numeric.gd','numeric_cases.json','test_gate_reader.gd','reader_cases.json','grammar_probe.gd','grammar_cases.json']
 dest=E/'reproduction-inputs';(dest/'tests').mkdir(parents=True,exist_ok=False)
 origins={}
 for name in names:
  src=(G/'stage/tests'/name) if name.startswith('grammar') else S/'tests'/name
  shutil.copyfile(src,dest/'tests'/name);origins['tests/'+name]=dict(source=str(src.relative_to(R)),sha256=v.sha(src),unchanged=True)
 shutil.copytree(G/'stage/grammar-fixtures',dest/'grammar-fixtures')
 for p in (dest/'grammar-fixtures').iterdir():origins['grammar-fixtures/'+p.name]=dict(source=str((G/'stage/grammar-fixtures'/p.name).relative_to(R)),sha256=v.sha(p),unchanged=True)
 v.dump('publication-inputs.json',dict(files=origins,assertions_changed=False,can_live_unchanged_under_simulator_tests=True,required_resource_paths={'numeric':['res://tests/numeric_cases.json'],'reader':['res://tests/reader_cases.json'],'grammar':['res://tests/grammar_cases.json','res://grammar-fixtures/leading-zero.json','res://grammar-fixtures/missing-fraction.json','res://grammar-fixtures/missing-fraction-with-exponent.json','res://grammar-fixtures/valid-exponent.json']},generated_outputs=['res://tests/numeric_observations.json','res://tests/grammar_observations.json'],read_dependencies=['res://editor/scene_document.gd','res://editor/layout_codec.gd','res://editor/gate_numeric.gd','res://editor/gate_json_numbers.gd'],environment='Godot 4.7.2 pinned executable, --headless --path <simulator> --script res://tests/<name>.gd; write permission for generated observations. Private APPDATA/LOCALAPPDATA/TEMP/TMP/XDG roots used by review; no external input/network required.',grammar_evidence='176 assertions reused only after exact dependency, original harness/input, log, terminal and oracle verification; no new grammar execution claimed',oracle_analysis='review.py analyze uses Python standard library Fraction/struct and current simulation/authority/motion/gate_geometry.py; no corpus regeneration'))
def finish():
 before=v.read(E/'source-before.json');current=v.protected();assert current==before['protected']
 assert v.sha(v.ENGINE)==v.PIN
 rows=[]
 for label in ['import','editor','persistence','ui','integration','unicode','numeric','unicode-red','reader','failure-bad-license','failure-signature','failure-empty-visual','failure-null','oracle-analysis','reuse-audit']:
  base=E/'raw'/label;d=v.read(base/'result.json');assert d['terminal'] and not d['timed_out'] and d['exit_code']==(1 if label=='unicode-red' else 0)
  for stream in ['stdout','stderr']:assert v.sha(base/(stream+'.txt'))==d[stream+'_sha256']
  if label not in ['oracle-analysis','reuse-audit']:
   assert d['eligible'] and not d['script_errors']
   for rel,pin in v.read(v.C/'candidate-source-pins.json').items():
    if label=='unicode-red' and rel=='editor/layout_store.gd':continue
    if label.startswith('failure-') and rel=='world/asset_library.gd':continue
    assert d['source_before'][rel]==d['source_after'][rel]==pin,(label,rel)
   if label not in ['unicode-red','persistence','reader']:assert d['error_lines']==[],label
   assert d['nul_diagnostics']==(3 if label=='unicode-red' else 0)
   if label=='persistence':assert len(d['error_lines'])==5 and sum('Exponent too high' in x for x in d['error_lines'])==3 and sum('Invalid UTF-8 leading byte (ff)' in x for x in d['error_lines'])==2
   if label=='reader':assert d['error_lines']==['WARNING: Exponent too high']*2
  rows.append({k:d[k] for k in ['argv','pid','terminal','timed_out','exit_code','elapsed_seconds','executable_sha256','stdout_sha256','stderr_sha256']})
 process=v.read(E/'terminal-process-readback.json');assert process['matching_process_count']==0
 after=v.files(S);original=v.read(v.C/'candidate-source-pins.json')
 assert all(after[n]==row for n,row in original.items())
 additions={k:x for k,x in after.items() if k not in original}
 v.dump('source-after.json',dict(protected=current,protected_unchanged=True,stage_source=after,generated_or_harness_additions=additions,engine_cache=v.files(S/'.godot',True),requirements_sha256=v.CONTRACT))
 v.dump('receipt.json',dict(schema=1,job_id='child-5c32d7c217d34ebd9c4ff58c4449fa0f',agent_id='/root/g01_g02_combined_independent_20261020',task='DEEPEYE-IMPLEMENTATION-20261014/v1',contract='DEEPEYE-HUMAN-LOCK-20261014/revision1',requirements_sha256=v.CONTRACT,candidate_manifest_sha256=v.sha(v.C/'candidate-source-pins.json'),source_before_sha256=v.sha(E/'source-before.json'),source_after_sha256=v.sha(E/'source-after.json'),fresh_runs=rows,exact_reuse_sha256=v.sha(E/'exact-evidence-reuse.json'),numeric_oracle_sha256=v.sha(E/'numeric-oracle-verification.json'),publication_inputs_sha256=v.sha(E/'publication-inputs.json'),candidate_exact=True,protected_sources_unchanged=True,new_actionable_findings=[],unicode_red_green='same unchanged six real file-I/O assertions: old-store 6/3 exit1, candidate6/0 exit0',embedded_nul_string_tested=False,ordinary_import_and_tests_nul_diagnostics=0,processes_remaining=0,display='strictly headless CREATE_NO_WINDOW; no GUI/input/capture/display changes',formal_cards='all29 not_run',native_ui='not_run',GPU='not_run',board='not_run',PC_AI='not_run',control_chains='not_run',adoption_owner='sole A main',native_completion_pending=True))
 print('Verified all fresh terminal/log/source records, exact candidate, protected sources unchanged and zero remaining owned processes.')
def seal():
 rows=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=v.sha(p)) for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ['lease.private.json','non-secret-artifact-manifest.json'] and '.godot' not in p.parts]
 v.dump('non-secret-artifact-manifest.json',dict(files=rows,excludes=['lease.private.json','self','generated .godot cache']))
 for row in rows:assert v.sha(E/row['path'])==row['sha256']
 print('Sealed and read back '+str(len(rows))+' nonsecret artifacts.')
if __name__=='__main__':
 action=sys.argv[1]
 if action=='audit':bounded_audit('analyze','oracle-analysis');bounded_audit('reuse','reuse-audit')
 elif action=='publication':publication()
 elif action=='finish':finish()
 elif action=='seal':seal()

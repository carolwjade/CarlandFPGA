import datetime, difflib, importlib.util, json, pathlib, re
spec = importlib.util.spec_from_file_location('evidence', pathlib.Path(__file__).with_name('evidence_runner.py'))
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
D = evidence.EVIDENCE
record = json.loads((D/'assignment-record.json').read_text(encoding='utf-8'))
prefix = '.local/deepeye-implementation-a/competition/deepeye/simulator/'
owned = {p[len(prefix):] for p in record['ownership'] if p.startswith(prefix)}
before = {row['path']:row for row in json.loads((D/'source-before-manifest.json').read_text(encoding='utf-8'))}
after = {row['path']:row for row in evidence.manifest(evidence.SOURCE)}
changed = [p for p in sorted(before.keys()|after.keys()) if before.get(p) != after.get(p)]
assert set(changed) <= owned, ('Unowned source drift', set(changed)-owned)
diffs = []
for p in changed:
    previous = (D/'source-before'/p).read_text(encoding='utf-8').splitlines(True) if p in before else []
    current = (evidence.SOURCE/p).read_text(encoding='utf-8').splitlines(True)
    diffs.extend(difflib.unified_diff(previous,current,fromfile='before/'+p,tofile='candidate/'+p))
(D/'candidate.diff').write_text(''.join(diffs),encoding='utf-8')
labels = ['red-integration-actual','final-import','final-integration-actual','final-assets','final-editor','final-persistence','final-ui-fit','baseline-editor','negative-missing-actual','negative-null-final','negative-collider-final']
results = []
for label in labels:
    metadata = json.loads((D/(label+'.json')).read_text(encoding='utf-8'))
    stdout = (D/(label+'.stdout.txt')).read_text(encoding='utf-8',errors='replace')
    stderr = (D/(label+'.stderr.txt')).read_text(encoding='utf-8',errors='replace')
    results.append({'label':label, 'exit_code':metadata['exit_code'],'terminal':metadata['terminal'],
                    'timeout':metadata['timeout'], 'seconds':metadata['seconds'],
                    'summary':[line for line in stdout.splitlines() if re.search(r'checks=|RESULT|ASSET_FAILURE',line)],
                    'script_errors':stderr.count('SCRIPT ERROR:'),'unicode_nul_diagnostics':stderr.count('Unexpected NUL character'),
                    'receipt_sha256':evidence.digest(D/(label+'.json')), 'stdout_sha256':evidence.digest(D/(label+'.stdout.txt')),
                    'stderr_sha256':evidence.digest(D/(label+'.stderr.txt'))})
assert all(r['terminal'] and not r['timeout'] for r in results)
assert all(r['exit_code']==0 and r['script_errors']==0 for r in results if r['label']!='red-integration-actual')
assert json.loads((D/'terminal-process-readback.json').read_text(encoding='utf-8-sig')) == []
cpu = next(line.removeprefix('CPU_PRESENTATION ') for line in (D/'final-integration-actual.stdout.txt').read_text(encoding='utf-8').splitlines() if line.startswith('CPU_PRESENTATION '))
receipt = {'schema':1,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'job_id':record['job_id'],'work_id':record['work_id'],'agent':record['agent'],
           'contract':'DEEPEYE-HUMAN-LOCK-20261014/revision1',
           'requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804',
           'engine_sha256':evidence.PIN, 'changed_owned_files':[after[p] for p in changed],
           'unowned_source_changes':[], 'B_sources_unchanged':15,
           'candidate_manifest_sha256':evidence.digest(D/'source-after-manifest.json'),
           'candidate_diff_sha256':evidence.digest(D/'candidate.diff'),'results':results,'cpu_sample':json.loads(cpu),
           'result_state':'bounded_implementation_and_assertion_checks_complete_pending_main_review',
           'engine_clean_gate':'not_satisfied_inherited_Unicode_NUL_diagnostics',
           'baseline_diagnostic_evidence':'baseline-editor exit0 checks696 failures0 emits same3 Unicode NUL diagnostics as candidate editor',
           'known_expected_stderr':['B bogus_kind negative control','persistence exponent/invalid-UTF8/NUL rejection fixtures'],
           'preserved_failed_attempts':['red-integration.json: test parser inference error before genuine RED',
                                       'candidate01-import.json: main.gd inference error corrected before GREEN',
                                       'candidate01-integration.json: camera float32 exact comparison test corrected',
                                       'negative-missing/null/collider.json: fixture parser inference error',
                                       'negative-null-actual.json: fixture expected text instead of dictionary; own PID24256 verified then stopped',
                                       'negative-collider-actual.json: fixture assumed wrong JSON schema; own PID43516 verified then stopped',
                                       'final-integration.json: added test helper inference error corrected; actual final run passes'],
           'processes_remaining':0,'native_ui':'not_run_by_child','GPU_FPS':'not_run',
           'physics_authority_crossing_sensors_AI_both_control_modes_board_system':'not_run',
           'formal_cards':{'count':29,'state':'not_run'},'acceptance_owner':'sole A main; no child acceptance'}
evidence.write('implementation-receipt.json',receipt)
print(json.dumps({'changed_files':len(changed),'unowned_changes':0,'manifest_sha256':receipt['candidate_manifest_sha256'],
                  'diff_sha256':receipt['candidate_diff_sha256'],'receipt_sha256':evidence.digest(D/'implementation-receipt.json')},indent=2))

import datetime,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];P=ROOT/'.local/deepeye-implementation-a';R=OUT/'g02-layout-persistence-review';E=OUT/'g02-main-selection-20261020'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
job=read(OUT/'g02-persistence-review-20261020-terminal.json')['result'][0]
assert job['job_id']=='child-ffab680842604466bbb1ead6549b1c11' and job['status']=='completed' and job['terminal'] and not job['stale'] and job['error'] is None
expected={'findings.md':'995a004cb894290e0f6b5983b4b7eb2928053d9f2667d15378d696347ee526a7','inspection_manifest.json':'edccbaebef095a051d6c74805432f923ca56fe8516a1c804e93645b7e93ab3ea','receipt.json':'95739fb966ea0537d1da337957b3e7e8711c137438c58040c1eb86b75d9138c9'}
for name,digest in expected.items():assert sha(R/name)==digest and digest in job['result']['text']
m=read(R/'inspection_manifest.json');checks={};source={}
for row in m['candidate_sources']:
    p=ROOT/row['product_path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    source[p.relative_to(P).as_posix()]=row['sha256']
for row in m['dependencies']:
    assert sha(ROOT/row['product_path'])==row['actual_sha256']==row['before_sha256']==row['after_sha256']
for section in ['author_metadata','author_evidence','prior_red','review_evidence','review_run_files','review_special_sources']:
    for row in m[section]:
        p=(ROOT/row['path']).resolve();assert p.is_relative_to(ROOT.resolve())
        if row.get('exists') is False:assert not p.exists();continue
        assert sha(p)==row['sha256'],(section,row['path'])
        assert p.stat().st_size==row['bytes']
    checks[section]=len(m[section])
tests={t['label']:t for t in m['independent_tests']}
for label in ['persistence-01','editor-01','smoke-01','flow-counterexample-01','rename-probe-01','import-origin-01']:
    t=tests[label];actual=read(R/'runs'/label/'result.json')
    assert t['result_exit_code']==actual['exit_code']==0 and not actual['timed_out'] and actual['process_started']
    for stream in ['stdout','stderr']:assert sha(ROOT/t[stream])==t[stream+'_sha256']
assert (tests['persistence-01']['checks'],tests['persistence-01']['failures'])==(618,0)
assert (tests['editor-01']['checks'],tests['editor-01']['failures'])==(696,0)
assert (tests['flow-counterexample-01']['checks'],tests['flow-counterexample-01']['failures'])==(11,0)
rename=(R/'runs/rename-probe-01/stdout.log').read_text(encoding='utf-8')
assert 'TARGET_AFTER_HEX=4e45575c6e' in rename
scope=read(ROOT/'docs/competition/deepeye-2026/immutable_scope.json')
assert hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
native=read(OUT/'g02-native-ui-main/main-result.json');assert native['exact_source_files_unchanged']==17 and native['original_gui_and_wrapper_absent']
assert not E.exists();E.mkdir()
doc=P/'competition/deepeye/docs/layout_persistence.md';raw=doc.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='2f796aef1b0f276bea66ca54741dcc1b1c6284d156f6d7301fc9595307897a5c'
normalized=raw.replace(b'\r\n',b'\n')
assert hashlib.sha256(normalized).hexdigest()=='1a4f3bd49cf675aaa4c30bb71b6dca4d4e92c2dfcd655f2a363688183ceba93d'
with (E/'reviewed-layout-persistence.raw.md').open('xb') as f:f.write(raw)
decision=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),work_id='A-G02-PERSISTENCE-MAIN-SELECTION-20261020-v1',original_review_job=job['job_id'],terminal=True,
    reviewed_artifacts=expected,reviewed_source_files=source,dependencies_checked=5,pins_checked=checks,
    independent_checks=dict(persistence=618,editor=696,dialog_flow=11,scene_smoke=True,import_origin=True),
    native_ui='save/cancel/reopen observed on initial empty layout; three UI readbacks only, not full G02 matrix',
    native_exit='900s watchdog exit1 retained; original PIDs absent',
    concurrent_save='Pinned Windows rename replaces existing destination. No concurrent no-overwrite guarantee. Known unimplemented limit preserved.',
    head_audit='74/74 before/after passed. Later strict audit retained one product_head mismatch after main publications, other73 and all scoped sources/dependencies unchanged. Not relabeled all-green.',
    documentation_normalization=dict(original_sha256=hashlib.sha256(raw).hexdigest(),published_sha256=hashlib.sha256(normalized).hexdigest(),operation='CRLF to LF only; original bytes preserved; no prose/source behavior change'),
    main_decision='adopt exact five reviewed GDScript files and text-equivalent normalized documentation as bounded persistence increment; no product Run or formal approval',formal_G02='not_run',all29_formal_cards='not_run')
with (E/'decision-before-normalization.json').open('x',encoding='utf-8') as f:json.dump(decision,f,indent=2);f.write('\n')
doc.write_bytes(normalized)
decision['published_source_files']={name:sha(P/name) for name in source}
assert all(decision['published_source_files'][n]==h for n,h in source.items() if n!='competition/deepeye/docs/layout_persistence.md')
with (E/'decision.json').open('x',encoding='utf-8') as f:json.dump(decision,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in decision.items() if k not in ['reviewed_source_files','published_source_files']}))

from review import *
import ast, difflib, re

prior=audit_prior()
assert prior==read(HERE/'prior-integrity-before.json')
dump(HERE/'prior-integrity-after.json',prior)
original=read(HERE/'source-manifest.json')
assert sources(PSIM)==original['product_before']
for p,h in EXPECTED.items(): assert sha(PSIM/p)==h==sha(SIM/p)
for p,h in FACEPINS.items():
    staged=SIM/'tests'/p if p.endswith('.gd') else STAGE/'competition/deepeye/tests/simulation'/p
    assert sha(staged)==h
for rel in ['ui/shell.gd','tests/test_g02_ui_fit.gd']:
    delta=''.join(difflib.unified_diff((UI/'baseline'/rel).read_text(encoding='utf-8').splitlines(True),(PSIM/rel).read_text(encoding='utf-8').splitlines(True),fromfile='baseline/'+rel,tofile='candidate/'+rel))
    assert delta==(UI/(Path(rel).name+'.diff')).read_text(encoding='utf-8')
    (HERE/(Path(rel).name+'.diff')).write_text(delta,encoding='utf-8')
oldtree=ast.parse((HERE.parent/'g02-face-matrix-continuation-20261020/candidate/test_gate_face_matrix.py').read_text(encoding='utf-8'))
newtree=ast.parse((FACE/'candidate/test_gate_face_matrix.py').read_text(encoding='utf-8'))
removed=0
for node in newtree.body:
    if isinstance(node,ast.ClassDef) and node.name=='GateFaceMatrixTests':
        before=len(node.body)
        node.body=[x for x in node.body if not isinstance(x,ast.FunctionDef) or x.name!='test_strict_numeric_policy_difference_for_all_six_faces']
        removed=before-len(node.body)
assert removed==1 and ast.dump(newtree)==ast.dump(oldtree)

def stream(label,name='stdout.txt'): return (HERE/'raw'/label/name).read_text(encoding='utf-8',errors='replace')
assert 'UI_FIT checks=266 failures=0' in stream('focused266')
assert 'TESTS checks=1977 failures=0' in stream('combinedface1977')
assert 'BOUNDARY_RESULT checks=15 failures=0' in stream('untouchedprobe15')
assert 'Ran 1 test' in stream('python-new-policy','stderr.txt') and '\nOK\n' in stream('python-new-policy','stderr.txt')
faces=stream('combinedface1977').splitlines()
assert len([x for x in faces if x.startswith('PAIR_ROW ')])==36
assert len([x for x in faces if x.startswith('UI_PAIR_ROW ')])==36
editor=[json.loads(x.split(' ',1)[1]) for x in faces if x.startswith('EDITOR_POLICY_ROW ')]
python=[json.loads(x.split(' ',1)[1]) for x in stream('python-new-policy').splitlines() if x.startswith('PY_POLICY_ROW ')]
assert len(editor)==len(python)==6
assert all(x['separation_0.2999999995'] and x['coordinate_14.8500000005'] for x in editor)
assert all(not x['observations']['separation_0.2999999995'] and not x['observations']['coordinate_14.8500000005'] for x in python)
dump(HERE/'numeric-policy-observations.json',{'editor':editor,'python':python,'common_near_boundary_semantics':False,'policy_changed':False,'formal_G02_closure':'separate main followup required'})
origins=json.loads(next(x.split(' ',1)[1] for x in stream('python-new-policy').splitlines() if x.startswith('IMPORT_ORIGINS ')))
assert all(Path(p).resolve().is_relative_to(STAGE.resolve()) for p in origins.values())

processes=[]
for out in sorted((HERE/'raw').iterdir()):
    r=read(out/'result.json')
    assert r['terminated'] and not r['timed_out'] and r['product_unchanged']
    assert r['product_before']==original['product_before']==r['product_after']
    assert sha(out/'stdout.txt')==r['stdout_sha256'] and sha(out/'stderr.txt')==r['stderr_sha256']
    processes.append({k:r[k] for k in ['pid','exit_code','timed_out','terminated','source_unchanged','product_unchanged','added_stage_files','changed_stage_files']}|{'label':out.name})
dump(HERE/'process-termination.json',processes)
assert len(processes)==8
assert read(HERE/'raw/extra-boundary/result.json')['exit_code']==1
assert 'EXTRA_RESULT checks=23 failures=1' in stream('extra-boundary')
assert 'Cannot infer the type' in stream('escape-diagnosis','stderr.txt')
assert read(HERE/'raw/escape-diagnosis/result.json')['exit_code']==1
assert read(HERE/'raw/escape-diagnosis-v2/result.json')['exit_code']==0
decodes=read(HERE/'independent-escape-decode.json')
assert len(decodes)==7 and all(x['json_decoder_roundtrip'] and x['raw_exact'] and x['hard_wrap_rejoins_exact_escaped'] for x in decodes)

# Preserve relevant old failures without modifying or upgrading their claims.
preserved=[]
for base,rel,label in [
    (UI,'logs/independent-red/stdout.bin','ui-M1-original'),
    (UI,'logs/import-candidate/result.json','ui-import-source-unchanged-false'),
    (UI,'preserved-execution-notes.md','ui-wrapper-failure-notes'),
    (FACE,'preserved/review/raw/current-ui-overlay/stdout.txt','face-stale-assertion-red'),
    (HERE.parent/'g02-face-matrix-20261020','raw/godot/stderr.txt','face-original-script-error'),
    (HERE.parent/'g02-face-matrix-20261020','raw/godot/stdout.txt','face-original-invalid-PASS'),
    (HERE.parent/'g02-face-matrix-continuation-20261020','raw/python-inherited/stderr.txt','face-original-43-failures')]:
    src=base/rel; dst=HERE/'preserved'/label/Path(rel).name
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    assert sha(src)==sha(dst)
    preserved.append({'origin':str(src),'copy':str(dst.relative_to(HERE)),'sha256':sha(src)})
dump(HERE/'preserved/inputs.json',preserved)
assert 'SCRIPT ERROR' in (HERE/'preserved/face-original-script-error/stderr.txt').read_text(encoding='utf-8')
assert 'failures=43' in (HERE/'preserved/face-original-43-failures/stderr.txt').read_text(encoding='utf-8')
assert read(HERE/'preserved/ui-import-source-unchanged-false/result.json')['source_unchanged'] is False
summary={'outcome':'no bounded source blocker established; main disposition and native visual probe pending','fresh':{'focused':{'checks':266,'failures':0},'combinedface':{'checks':1977,'failures':0,'document_rows':36,'shell_rows':36},'untouchedprobe':{'checks':15,'failures':0},'python_policy':{'methods':1,'faces':6,'import_origins':origins}},'extra_probe':{'checks':23,'reported_failures':1,'adjudication':'one Godot c_unescape oracle mismatch; independently decoded all 7 cases exactly; other 22 checks pass','popup':'478x392 contained at 1280x720','raw_status_and_file_result':'exact'},'reused_broad':[696,618],'prior_artifacts_verified':[201,87],'python_existing_ast_unchanged':True,'formal_cards':'all 29 not_run','known_numeric_policy_gap':True,'product_unchanged':True,'final_source_pins':EXPECTED,'face_pins':FACEPINS,'all_processes_terminated':True}
dump(HERE/'verification-summary.json',summary)
dump(HERE/'source-after.json',{'product_after':sources(PSIM),'stage_after':sources(STAGE),'product_unchanged':True,'independent_probe_sha256':sha(SIM/'tests/review_boundary.gd')})

findings='''# Independent final combined G02 evidence review

No bounded source blocker was established for the final UI status-height repair plus the adapted face candidates. This is evidence for the sole A main's disposition and a native visual probe, not formal source/product acceptance. All 29 formal cards remain not_run.

## Current evidence

The exact final PRODUCT shell/project/UI-test bytes match the assignment pins. The private face candidates also match both assigned pins. All 17 PRODUCT simulator files were freshly copied into a private stage; the pinned adapted simulation dependencies match the corresponding available PRODUCT bytes. Read-only source inspection and exact baseline/candidate diff comparisons confirm the repair changes only bounded visible status and tooltip formatting. No Git operation was used, so the parent-supplied HEAD 6c51b2d5304dc3bf9735a304931e8001b22e7541 is context only; this review binds actual source SHA256, not an assertion that a commit contains these dirty bytes.

Fresh direct Godot runs on these combined sources pass focused UI 266/0, adapted face 1977/0 (36 document rows and 36 real shell-signal rows), and exact untouched independent probe 15/0. The probe retains SHA256 964ad14344b9c111eb1a2ac2c00a7f5aafc6b362dd00d1f7e53f6159fa797623. Fresh Python runs its one new six-face numeric-policy method successfully, with actual gate_geometry and gate_clearance import origins inside this private stage. Existing Python AST is independently unchanged after removing only that method. The old broad 696/0 and 618/0 results were reused only after their exact runtime source-before/after and PRODUCT-before/after pins matched all 17 final PRODUCT files, with exit 0, normal termination and unchanged source. They were not rerun.

ActionStatus is 24 pixels high, retains one visible line with the 15-pixel body font, clips/ellipsizes visible text and retains full accepted raw Label.text and last_file_result. Central area remains 60.897377 percent at 1920x1080 and 70.203993 percent at 2560x1440; 1280x720 has positive 43.727431 percent, with no 60 percent claim. The real engine PopupPanel for the 512-CJK diagnostic is 736x254 and contained at all three client sizes. Permanent help, disabled authority buttons, geometry and stale-tooltip clearing pass. The unchanged independent probe also checks isolated band-gutter wheel/right input and already-open dialog resizing.

An extra probe checks 512 characters combining literal backslash-n, actual newlines, tabs and backslashes, plus pointer events specifically targeted at ActionStatus. The actual engine tooltip is 478x392 and contained at 1280x720. The remaining 22 checks verify complete raw reason/status, 15px font, visible 24px line, stable bottom height, actual hovered ActionStatus, isolated wheel/right/middle/left gestures, unchanged camera/document/help and cleared tooltip. No product Run is called.

## L1: Narrow the c_unescape roundtrip claim

The extra probe reports 23 checks / 1 failure / exit 1 because it uses the same Godot c_unescape decoding assumption as the author test. A separate seven-case diagnostic shows that literal backslash-n/backslash-t and Windows-style C:\\new\\test strings fail that decoder, while their raw status remains exact. The first diagnostic script had a type-inference parse error; its failed script and raw result remain unchanged, and a separate v2 adds only an explicit String type.

Independent Python JSON decoding of the actual tooltip after removing only inserted formatting line breaks reconstructs all seven original statuses exactly, including the 512-character mixed case. Those rejoined tooltip bytes also equal the engine's escaped input in all seven cases. This identifies a limitation of Godot c_unescape as the test oracle, not established product data loss or a broken reversible encoding. Preserve the original extra-probe RED and narrow the author's blanket assertion that c_unescape reconstructs all backslash-containing statuses. Do not use that assertion as a general escape proof. A broader supported-control-character guarantee was not established. Main decides any followup to the test/wording; no production or validator change was made here.

## Separate existing numeric-policy gap

Fresh evidence reproduces the editor's 1e-9m tolerance accepting separation 0.2999999995 and coordinate 14.8500000005 on all six faces; Python strict coordinate/exact-rational overlap rejects both. Both accept tested tangent/edge and reject clear interior/overrun. Adapted assertions explicitly preserve that difference; they do not approve common policy. Godot ABI fields are clearly expected fixture labels; actual Gate.abi_face observations remain Python evidence. The main-identified taskbook G02 policy followup remains required before formal closure. Neither production validator was edited.

## Integrity, failures and limits

All 201 UI and 87 face manifest artifacts, sizes and hashes verify before/after. Both author terminal completions contain exact persisted final results. Original M1 RED, original face stale-help RED, original script-error/PASS and 43-failure Python evidence are preserved/copied with origin hashes. The old script-error/PASS remains invalid. The UI author's original import wrapper failures and source_unchanged=false UID additions remain unchanged; no pristine-import provenance is claimed. This review's fresh import also records source_unchanged=false because nine missing .gd.uid files were generated. No existing stage source changed during import. All subsequent tests have unchanged stage/PRODUCT maps. Diagnostic scripts were added as separate files between runs and have exact execution-time pins.

Eight headless processes (including the extra oracle RED and initial diagnostic parse failure) terminated normally without timeout or forced termination. Engine stdout/stderr, argv, PID, executable/source hashes, exits and environment are recorded under raw/. Startup Unexpected NUL warnings remain unresolved and retained; clean stderr is not claimed. Reused persistence rejection-fixture diagnostics remain the original evidence.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1 and H01-H15 canonical hash c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 are verified independently for root and PRODUCT; active generation-2 transfer and node-A role/config were read. All writes stay in this assigned evidence directory. No GUI, OS mouse/DPI/scaling, ordinary file-failure reachability, game rendering, product Run, board, services/drivers/config/providers/credentials, Git operation, messages or children occurred. Headless evidence does not close replay, containment, world-authority, continuous full-volume crossing/CCD, runtime/route, causal sensing, PC AI/H12 chains or any formal card. Acceptance remains with the main.
'''
(HERE/'findings.md').write_text(findings,encoding='utf-8')
final='''Independent final combined review complete; no bounded source blocker established. Main disposition/native visual probe pending. All 29 formal cards remain not_run.
Fresh final UI 266/0, combined face 1977/0 with 36 document + 36 signal rows, untouched probe 15/0, focused Python policy method PASS on six faces with private import origins. Reused exact-pinned 696/0 and 618/0. All 201 UI + 87 face artifacts verified unchanged. PRODUCT source unchanged throughout.
L1 evidence correction: extra mixed-escape probe 23/1 is a Godot c_unescape oracle mismatch; separate diagnostic plus independent decoding reconstruct all 7 statuses exactly. Its other 22 checks pass, including 15px/24px visible status, contained 478x392 tooltip at 720p, actual ActionStatus pointer isolation, unchanged camera/document/help and clearing. Preserve RED and narrow blanket c_unescape claim; no product data-loss blocker established.
Existing editor 1e-9m versus Python strict/exact boundary gap remains separate and requires main followup before formal G02 closure; validators unchanged. Original import UID/source_unchanged=false wrapper failures and old test failures preserved. Eight headless processes terminated; two diagnostic/oracle failures retained. NUL warnings unresolved. No native GUI/DPI/ordinary-error reachability/Run/board/Git/services/messages/children.
Source SHA256 shell=bf61c548fec75793773606e9203666efa0acdf497ecce67535ca9d7d1255bbcc; UI-test=2c95090dceb98518c331dbb803f1bd1bb4e9d438439b58173e2bee78aa857db4; project=f713d8279b16a9710cc9a2a892a54c620a64dbeb36179fa4ac4cd3c7651d26f2; face-GD=62233b3304d6378ccafd5ff76268322d7735fdab87ba4e84632852d1b355d49e; face-PY=e34e8ed095e97d192dfd7c27c87c3473249b7d09a2bdd560350138eb5073e0fa.
Contract DEEPEYE-HUMAN-LOCK-20261014/revision1 H01-H15 canonical c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 unchanged. Details findings.md, verification-summary.json, source-manifest.json, source-after.json, process-termination.json and raw/.
'''
(HERE/'final-result.txt').write_text(final,encoding='utf-8')
artifacts=[]
for p in sorted(HERE.rglob('*')):
    if not p.is_file() or p.name in ['lease.private.json','manifest.json','receipt.json','native-complete-response.json']: continue
    if '.godot' in p.parts or '__pycache__' in p.parts or 'tmp' in p.relative_to(HERE).parts: continue
    artifacts.append({'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
dump(HERE/'manifest.json',{'schema':1,'files':artifacts,'exclusions':['private lease','generated .godot cache','temporary runtime data','receipt/completion self-reference']})
receipt={'job_id':'child-c26eaab1000c4e7c92e78e9f4f9026cc','agent_id':'/root/g02_final_combined_review_20261020','status':'bounded evidence review complete; main disposition pending','manifest_sha256':sha(HERE/'manifest.json'),'findings_sha256':sha(HERE/'findings.md'),'verification_summary_sha256':sha(HERE/'verification-summary.json'),'final_result_sha256':sha(HERE/'final-result.txt'),'formal_cards':'all 29 not_run','product_writes':False}
dump(HERE/'receipt.json',receipt)
print(json.dumps(receipt,indent=2))

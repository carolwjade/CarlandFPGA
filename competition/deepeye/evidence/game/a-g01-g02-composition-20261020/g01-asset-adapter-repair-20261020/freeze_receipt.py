import datetime,difflib,json,re
from repair_runner import E,ROOT,SOURCE,REVIEW,ENGINE,PIN,OWNED,sha,dump,manifest,contract
before=json.loads((E/'source-before.json').read_text(encoding='utf-8'))
current=manifest(SOURCE)
old={r['path']:r for r in before['source_manifest']}; new={r['path']:r for r in current}
changed=[p for p in sorted(old.keys()|new.keys()) if old.get(p)!=new.get(p)]
assert sorted(changed)==sorted(OWNED),changed
for row in current:
    assert sha(E/'frozen-stage'/row['path'])==row['sha256'],row['path']
dump('source-after.json',dict(requirements_sha256=contract(),engine_sha256=sha(ENGINE),source_manifest=current,changed_owned_files=[new[p] for p in OWNED],unowned_files_unchanged=True))
diff=''.join(''.join(difflib.unified_diff((E/'original-stage'/p).read_text(encoding='utf-8').splitlines(True),(SOURCE/p).read_text(encoding='utf-8').splitlines(True),fromfile='before/'+p,tofile='candidate/'+p)) for p in OWNED)
(E/'repair.diff').write_text(diff,encoding='utf-8')
oracles=json.loads((E/'unchanged-oracles.json').read_text(encoding='utf-8'))
for row in oracles:
    assert sha(E/row['path'])==row['sha256']==sha(REVIEW/row['path'])
labels={'frozen-import':None,'frozen-integration':'VIEWER_ASSET_INTEGRATION checks=136 failures=0','frozen-independent':'INDEPENDENT checks=54 failures=0','frozen-persistence':'TESTS checks=628 failures=0','frozen-editor':'TESTS checks=696 failures=0','frozen-g02-ui-fit':'UI_FIT checks=266 failures=0',**{'frozen-negative-'+m:'FAILURE_REVIEW mode='+m+' checks='+str(n)+' failures=0' for m,n in [('bad-license',14),('signature',10),('empty-visual',14),('null',16)]}}
results=[]
for label,summary in labels.items():
    r=json.loads((E/(label+'.json')).read_text(encoding='utf-8'))
    out=E/(label+'.stdout.txt'); err=E/(label+'.stderr.txt')
    assert r['terminal'] and not r['timeout'] and r['exit_code']==0 and r['executable_sha256']==PIN
    assert sha(out)==r['stdout_sha256'] and sha(err)==r['stderr_sha256']
    text=out.read_text(encoding='utf-8'); errors=err.read_text(encoding='utf-8')
    assert 'SCRIPT ERROR' not in errors and not re.search(r'^ERROR:',errors,re.M)
    if summary: assert summary in text
    executed={row['path']:row['sha256'] for row in r['source_manifest_before']}
    for p in OWNED: assert executed[p]==sha(SOURCE/p),(label,p)
    for p in ['test_failure_review.gd'] if 'negative' in label else ['test_independent.gd'] if label=='frozen-independent' else []:
        assert executed['tests/'+p]==sha(REVIEW/p)
    results.append(dict(label=label,summary=summary,pid=r['pid'],exit_code=0,timeout=False,terminal=True,receipt_sha256=sha(E/(label+'.json')),stdout_sha256=sha(out),stderr_sha256=sha(err),script_errors=0,unicode_nul_diagnostics=errors.count('Unexpected NUL character'),warnings=errors.count('WARNING:'),source_pins_match=True))
# Preserve and validate the exact final integration harness's RED result.
red=json.loads((E/'frozen-harness-red.json').read_text(encoding='utf-8'))
assert red['terminal'] and not red['timeout'] and red['exit_code']==1
assert 'VIEWER_ASSET_INTEGRATION checks=136 failures=11' in (E/'frozen-harness-red.stdout.txt').read_text(encoding='utf-8')
assert sha(E/'frozen-harness-red-stage/tests/test_viewer_asset_integration.gd')==sha(SOURCE/'tests/test_viewer_asset_integration.gd')
# Only the B-only 622 check run is reused. Its complete transitive code/config
# and asset inputs match; changed A scripts and unrelated test scripts are not
# loaded by that harness.
author=E.parent/'g01-asset-adapter-implementation-20261020'
r=json.loads((author/'final-assets.json').read_text(encoding='utf-8'))
assert r['terminal'] and not r['timeout'] and r['exit_code']==0 and r['engine_sha256']==PIN
assert r['argv'][-2:]==['--script','res://tests/test_asset_contract.gd']
for ext in ['stdout','stderr']: assert sha(author/('final-assets.'+ext+'.txt'))==r[ext+'_sha256']
assert 'RESULT checks=622 failures=0' in (author/'final-assets.stdout.txt').read_text(encoding='utf-8')
assert 'SCRIPT ERROR' not in (author/'final-assets.stderr.txt').read_text(encoding='utf-8')
mapping={row['path']:row for row in r['source_manifest']}
deps=[row for row in current if row['path'].startswith(('world/','assets/')) or row['path'] in ['project.godot','tests/test_asset_contract.gd']]
assert all(mapping[row['path']]['sha256']==row['sha256'] for row in deps)
reuse=dict(summary='RESULT checks=622 failures=0',eligible=True,receipt_sha256=sha(author/'final-assets.json'),argv=r['argv'],cwd=r['cwd'],terminal=True,exit_code=0,timeout=False,engine_sha256=PIN,stdout_sha256=r['stdout_sha256'],stderr_sha256=r['stderr_sha256'],exact_dependency_pins=deps,justification='Executing harness only preloads world/asset_library.gd, which preloads the other three world geometry scripts. Harness, all world/assets inputs and project.godot match the executing receipt. A viewer/presenter and other tests are not loaded. Does not prove native UI or acceptance.')
dump('B622-exact-reuse.json',reuse)
process=json.loads((E/'terminal-process-readback.json').read_text(encoding='utf-8-sig'))
assert process['matching_process_count']==0
value=dict(schema=1,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),job_id='child-d9f9c52cb946453183722e1957978fe0',agent='/root/g01_asset_adapter_repair_20261020',task='DEEPEYE-IMPLEMENTATION-20261014/v1',contract='DEEPEYE-HUMAN-LOCK-20261014/revision1',requirements_sha256=before['requirements_sha256'],engine_sha256=PIN,changed_owned_files=[new[p] for p in OWNED],unowned_product_files_unchanged=True,source_before_sha256=sha(E/'source-before.json'),source_after_sha256=sha(E/'source-after.json'),repair_diff_sha256=sha(E/'repair.diff'),final_stage_manifest_sha256=sha(E/'frozen-stage-manifest.json'),unchanged_oracles=oracles,original_red_reuse_sha256=sha(E/'original-red-reuse.json'),final_harness_red=dict(checks=136,failures=11,terminal=True,exit_code=1,receipt_sha256=sha(E/'frozen-harness-red.json')),fresh_runs=results,reused_B622_sha256=sha(E/'B622-exact-reuse.json'),fixed_findings=['F1','F2','F3','F4'],processes_remaining=0,native_ui='not_run',engine_clean='not_satisfied_inherited_Unicode_NUL',formal_cards=dict(count=29,state='not_run'),acceptance_owner='sole A main; repair evidence only; independent re-review pending')
dump('repair-receipt.json',value)
print(json.dumps(dict(changed=changed,verified_frozen_runs=len(results),unowned_product_files_unchanged=True,receipt_sha256=sha(E/'repair-receipt.json'),source_after_sha256=sha(E/'source-after.json'),repair_diff_sha256=sha(E/'repair.diff'))))

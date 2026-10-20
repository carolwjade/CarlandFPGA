import datetime,json,re
from review_runner import E,AUTHOR,sha,dump,PIN
before=json.loads((E/'source-before.json').read_text(encoding='utf-8'))
after=json.loads((E/'source-after.json').read_text(encoding='utf-8'))
assert before['source_manifest']==after['source_manifest']
assert after['candidate_manifest_sha256']=='4e174b26b9c52ccd76458dab1910cd59b8a17092a400a441a3b74377b29c4dc2'
assert sha(AUTHOR/'candidate.diff')=='44f2e8a9c39c9fa20db2c2ae8f112eb76ef3343e331e8f4879e243dfd0a6d51e'
results=[]
labels=['fresh-import','fresh-integration','independent-adversarial','independent-adversarial-corrected','negative-missing','negative-parser','negative-null','negative-collider','negative-empty-visual','negative-bad-license','negative-signature']
for label in labels:
    r=json.loads((E/(label+'.json')).read_text(encoding='utf-8'))
    out=E/(label+'.stdout.txt'); err=E/(label+'.stderr.txt')
    assert sha(out)==r['stdout_sha256'] and sha(err)==r['stderr_sha256'] and r['terminal'] and not r['timeout']
    text=out.read_text(encoding='utf-8'); error=err.read_text(encoding='utf-8')
    results.append(dict(label=label,pid=r['pid'],exit_code=r['exit_code'],terminal=r['terminal'],timeout=r['timeout'],receipt_sha256=sha(E/(label+'.json')),stdout_sha256=sha(out),stderr_sha256=sha(err),summaries=[line for line in text.splitlines() if re.search(r'(VIEWER_ASSET_INTEGRATION|INDEPENDENT checks=|FAILURE_REVIEW mode=)',line)],script_errors=error.count('SCRIPT ERROR'),unicode_nul_diagnostics=error.count('Unexpected NUL character'),eligible_as_clean_assertion_run=label not in ['independent-adversarial','negative-parser','negative-bad-license','negative-signature'] and r['exit_code']==0 and 'SCRIPT ERROR' not in error))
validate=json.loads((E/'native-validate-response.json').read_text(encoding='utf-8'))
process=json.loads((E/'terminal-process-readback.json').read_text(encoding='utf-8-sig'))
assert process['matching_process_count']==0
value=dict(schema=1,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),agent='/root/g01_asset_adapter_independent_20261020',job_id='child-52e445a08a2e44c4b584fcedeee59530',work_id=validate.get('work_id'),contract='DEEPEYE-HUMAN-LOCK-20261014/revision1',requirements_sha256=after['requirements_sha256'],engine_sha256=PIN,author_terminal_verified=after['author_terminal'],candidate_manifest_sha256=after['candidate_manifest_sha256'],candidate_diff_sha256=sha(AUTHOR/'candidate.diff'),candidate_source_pins=after['candidate'],B_source_pins=after['B'],full_product_manifest_unchanged=True,product_writes=0,findings=[dict(id='F1',severity='P2',path='viewer/asset_presenter.gd',lines=[80,64,73],issue='wrong license metadata type fails open and adopts invalid asset with ready report',reproducer='negative-bad-license'),dict(id='F2',severity='P2',path='viewer/asset_presenter.gd',lines=[35,42,61,224],issue='wrong static factory arity escapes diagnostic; greybox with ready report',reproducer='negative-signature'),dict(id='F3',severity='P2',path='viewer/asset_presenter.gd',lines=[78,96],issue='empty Visual with stale metadata silently accepted as ready',reproducer='negative-empty-visual'),dict(id='F4',severity='P2',path='viewer/main.gd',lines=[339,343,639,649],issue='fallback label and world-ray picking ignore parent transform; identity scene unaffected',reproducer='negative-null')],fresh_runs=results,reused_evidence='exact-evidence-reuse.json',preserved_invalid_own_attempt='independent-adversarial emitted runtime error after 49/0; corrected harness 54/0 is the eligible run',processes_remaining=0,native_ui='not_run',GPU_FPS='not_run',engine_clean='not_satisfied_inherited_Unicode_NUL',formal_cards=dict(count=29,state='not_run'),acceptance_owner='sole A main; review evidence only')
dump('independent-review-receipt.json',value)
pins=[]
for p in sorted(E.iterdir()):
    if p.is_file() and p.name not in ['lease.private.json','non-secret-artifact-manifest.json']:
        pins.append(dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)))
dump('non-secret-artifact-manifest.json',pins)
print(json.dumps(dict(work_id=value['work_id'],findings=4,full_product_manifest_unchanged=True,receipt_sha256=sha(E/'independent-review-receipt.json'),findings_sha256=sha(E/'findings.md'),non_secret_manifest_sha256=sha(E/'non-secret-artifact-manifest.json'))))

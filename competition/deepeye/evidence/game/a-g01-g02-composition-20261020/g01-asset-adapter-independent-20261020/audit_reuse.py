import difflib,json,pathlib
from review_runner import AUTHOR,E,SOURCE,ENGINE,sha,dump
current={r['path']:r for r in json.loads((E/'frozen-stage-manifest.json').read_text(encoding='utf-8'))}
items=[]
for label,script,summary in [('final-assets','test_asset_contract.gd','RESULT checks=622 failures=0'),('final-editor','test_editor_document.gd','TESTS checks=696 failures=0'),('final-persistence','test_layout_persistence.gd','TESTS checks=628 failures=0'),('final-ui-fit','test_g02_ui_fit.gd','UI_FIT checks=266 failures=0')]:
    receipt=json.loads((AUTHOR/(label+'.json')).read_text(encoding='utf-8'))
    mapping={r['path']:r for r in receipt['source_manifest']}
    differences=[dict(path=k,current=v['sha256'],recorded=mapping.get(k,{}).get('sha256')) for k,v in current.items() if mapping.get(k,{}).get('sha256')!=v['sha256']]
    out=AUTHOR/(label+'.stdout.txt'); err=AUTHOR/(label+'.stderr.txt')
    argv=receipt['argv']; expected_script='res://tests/'+script
    ok=(receipt['terminal'] and not receipt['timeout'] and receipt['exit_code']==0 and receipt['engine_sha256']==sha(ENGINE) and argv[-2:]==['--script',expected_script] and sha(out)==receipt['stdout_sha256'] and sha(err)==receipt['stderr_sha256'] and summary in out.read_text(encoding='utf-8') and 'SCRIPT ERROR' not in err.read_text(encoding='utf-8'))
    # These harnesses do not preload/load the newly added integration harness.
    allowed={'tests/test_viewer_asset_integration.gd'}
    ok=ok and all(d['path'] in allowed for d in differences)
    row=dict(label=label,reuse_eligible=ok,receipt_sha256=sha(AUTHOR/(label+'.json')),stdout_sha256=sha(out),stderr_sha256=sha(err),argv=argv,recorded_terminal=receipt['terminal'],recorded_exit=receipt['exit_code'],summary=summary,source_differences=differences,justification='All runtime/project/assets/editor/viewer/UI and executing harness bytes match frozen candidate. Only a nonexecuted integration test may differ; none of these four harnesses loads it. Exact binary and actual argv/cwd/stdout/stderr/terminal receipt are checked. Reuse does not prove native UI, physics or acceptance.')
    assert ok,row
    items.append(row)
dump('exact-evidence-reuse.json',items)
diff=(AUTHOR/'candidate.diff').read_text(encoding='utf-8')
block=diff.split('+++ candidate/tests/test_viewer_asset_integration.gd\n',1)[1].split('--- before/tests/test_viewer_asset_integration.gd.uid',1)[0]
reconstructed='\n'.join(line[1:] for line in block.splitlines() if line.startswith('+'))+'\n'
actual=(SOURCE/'tests/test_viewer_asset_integration.gd').read_text(encoding='utf-8')
delta=''.join(difflib.unified_diff(reconstructed.splitlines(True),actual.splitlines(True),fromfile='candidate.diff reconstruction',tofile='actual pinned source'))
(E/'candidate-diff-staleness.txt').write_text(delta,encoding='utf-8')
print(json.dumps(dict(reused=[i['summary'] for i in items],diff_stale=bool(delta))))

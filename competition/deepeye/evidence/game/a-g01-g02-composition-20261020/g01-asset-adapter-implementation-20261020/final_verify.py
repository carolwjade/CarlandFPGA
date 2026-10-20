import contextlib, importlib.util, io, pathlib, re
spec = importlib.util.spec_from_file_location('evidence', pathlib.Path(__file__).with_name('evidence_runner.py'))
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
runs = [('final-stage','final-assets','test_asset_contract'),
        ('final-stage','final-editor','test_editor_document'),
        ('final-stage','final-persistence','test_layout_persistence'),
        ('final-stage','final-ui-fit','test_g02_ui_fit'),
        ('source-before','baseline-editor','test_editor_document')]
for stage,label,script in runs:
    with contextlib.redirect_stdout(io.StringIO()):
        code = evidence.run(stage,label,script)
    out = (evidence.EVIDENCE/(label+'.stdout.txt')).read_text(encoding='utf-8',errors='replace')
    err = (evidence.EVIDENCE/(label+'.stderr.txt')).read_text(encoding='utf-8',errors='replace')
    print(label, 'exit='+str(code), '|', ' | '.join(line for line in out.splitlines() if re.search(r'checks=|RESULT', line)))
    print('  stderr: script_errors='+str(err.count('SCRIPT ERROR:'))+', Unicode NUL='+str(err.count('Unexpected NUL character')))

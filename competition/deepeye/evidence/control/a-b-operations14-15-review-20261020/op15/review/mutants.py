import importlib.util,json,re,shutil,traceback
from pathlib import Path
OWN=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_review',OWN/'review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PRIOR=m.D;m.D=OWN/'mutant-runs';m.D.mkdir();m.R={'commands':[],'mutants':[]}
D=m.D;R=m.R;command=m.command
(D/'temp').mkdir();(D/'build').mkdir();(D/'build/run.do').write_text('onerror {quit -code 1}\nrun -all\nquit -code 0\n',encoding='ascii');(D/'snapshot').mkdir()
for p in (PRIOR/'snapshot').iterdir():shutil.copyfile(p,D/'snapshot'/p.name)
shutil.copyfile(PRIOR/'positive-4-8-8.vec',D/'test.vec')
rows=[[int(x,16)for x in line.split()]for line in (D/'test.vec').read_text().splitlines()[1:]]
scenarios=json.loads((PRIOR/'positive-4-8-8.scenarios.json').read_bytes())
original=(D/'snapshot/deepeye_pwm_applied_capture.sv').read_text()
mutants=[('delayed-transfer',[('rst || stop || transfer_now || g_pending || !g_running','rst || stop || g_pending || !g_running')]),
('same-tag-retained',[('rst || stop || transfer_now || g_pending || !g_running','rst || stop || (transfer_now && (cfg_tag != expected_tag_q)) || (g_pending && (cfg_tag != expected_tag_q)) || !g_running'),('assign capture_rearm = capture_arm;','assign capture_rearm = capture_arm && (cfg_tag != expected_tag_q);')]),
('mismatch-admitted',[('assign out_valid = transport_window && c_armed && !raw_fault &&\n                       c_out_valid && raw_equal;','assign out_valid = transport_window && c_armed && !raw_fault &&\n                       c_out_valid;')])]
drive=None
try:
    code,text,err=command('subst-before',['subst'],D);used={line[:2].upper()for line in text.splitlines()};drive=next(x+':'for x in 'RSTUVWXYZQ'if x+':'not in used and not Path(x+':/').exists());a=drive+'/'
    command('subst-create',['subst',drive,str(D)],D)
    for name,replacements in mutants:
        text=original
        for old,new in replacements:assert text.count(old)==1;text=text.replace(old,new)
        (D/'snapshot'/(name+'.sv')).write_text(text,encoding='utf8');m.save(D/(name+'.mutation.json'),{'original_sha256':m.sha(D/'snapshot/deepeye_pwm_applied_capture.sv'),'mutant_sha256':m.sha(D/'snapshot'/(name+'.sv')),'replacements':replacements})
        code,tx,er=command(name+'-vlib',[m.TOOL/'vlib.exe',name],a+'build');assert code==0
        code,tx,er=command(name+'-vlog',[m.TOOL/'vlog.exe','-sv','-work',name,a+'snapshot/deepeye_atomic_pwm.sv',a+'snapshot/deepeye_pwm_coherent_capture.sv',a+'snapshot/'+name+'.sv',a+'snapshot/independent_tb.sv'],a+'build');assert code==0 and 'Errors: 0'in tx
        code,tx,er=command(name+'-vsim',[m.TOOL/'vsim.exe','-batch','-syncio',name+'.independent_tb','-gCOUNT_W=4','-gWITNESS_W=8','-gTAG_W=8','+VEC='+a+'test.vec','+LOG='+a+name+'.trace','-l',a+name+'.transcript','-wlf',a+name+'.wlf','-do','run.do'],a+'build');assert code==0 and 'INDEPENDENT_TRACE_DONE edges=2376'in tx and not re.search(r'\*\*\s+(?:Fatal|Error):',tx+er)
        result=m.check(D/(name+'.trace'),rows,scenarios,4,8,8);result.update(name=name,compiled=True,simulator_completed=True,process_exit=code,trace_sha256=m.sha(D/(name+'.trace')));m.save(D/(name+'.check.json'),result);R['mutants'].append(result);m.save(D/'receipt.json',R)
        assert result['error_count']>0,name
finally:
    if drive:
        command('subst-remove',['subst',drive,'/d'],D);code,tx,er=command('subst-after',['subst'],D);R['mapping_removed']=not any(line.startswith(drive+'\\')for line in tx.splitlines());m.save(D/'receipt.json',R)
print(json.dumps([{'name':r['name'],'errors':r['error_count'],'first':r['errors'][:3]}for r in R['mutants']]))

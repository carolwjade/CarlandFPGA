import importlib.util,json,re,shutil
from pathlib import Path
OWN=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('own',OWN/'review.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.D=OWN/'same-tag-probe';D=m.D;D.mkdir();(D/'temp').mkdir();(D/'build').mkdir();(D/'snapshot').mkdir();m.R={'commands':[]}
for p in (OWN/'attempt03/snapshot').iterdir():shutil.copyfile(p,D/'snapshot'/p.name)
shutil.copyfile(OWN/'attempt03/positive-4-8-8.vec',D/'test.vec')
(D/'build/run.do').write_text('onerror {quit -code 1}\nrun -all\nquit -code 0\n',encoding='ascii')
text=(D/'snapshot/deepeye_pwm_applied_capture.sv').read_text()
changes=[('rst || stop || transfer_now || g_pending || !g_running','rst || stop || (transfer_now && (cfg_tag != expected_tag_q)) || !g_running'),('end else if (transfer_now || g_pending || !g_running) begin','end else if ((transfer_now && (cfg_tag != expected_tag_q)) || !g_running) begin'),('assign capture_rearm = capture_arm;','assign capture_rearm = capture_arm && (g_active_tag != expected_tag_q);')]
for old,new in changes:assert text.count(old)==1;text=text.replace(old,new)
(D/'snapshot/same-tag-cache.sv').write_text(text,encoding='utf8');m.save(D/'mutation.json',{'changes':changes,'purpose':'deliberately preserve binding/capture across same-tag T and application; expose pre-boundary interval','mutant_sha256':m.sha(D/'snapshot/same-tag-cache.sv'),'checker_sha256':m.sha(OWN/'review.py')})
code,tx,er=m.command('subst-before',['subst'],D);used={x[:2].upper()for x in tx.splitlines()};drive=next(x+':'for x in 'RSTUVWXYZQ'if x+':'not in used and not Path(x+':/').exists());a=drive+'/'
m.command('subst-create',['subst',drive,str(D)],D)
try:
    code,tx,er=m.command('vlib',[m.TOOL/'vlib.exe','lib'],a+'build');assert code==0
    code,tx,er=m.command('vlog',[m.TOOL/'vlog.exe','-sv','-work','lib',a+'snapshot/deepeye_atomic_pwm.sv',a+'snapshot/deepeye_pwm_coherent_capture.sv',a+'snapshot/same-tag-cache.sv',a+'snapshot/independent_tb.sv'],a+'build');assert code==0 and 'Errors: 0'in tx
    code,tx,er=m.command('vsim',[m.TOOL/'vsim.exe','-batch','-syncio','lib.independent_tb','-gCOUNT_W=4','-gWITNESS_W=8','-gTAG_W=8','+VEC='+a+'test.vec','+LOG='+a+'same-tag.trace','-l',a+'same-tag.transcript','-wlf',a+'same-tag.wlf','-do','run.do'],a+'build');assert code==0 and'INDEPENDENT_TRACE_DONE edges=2376'in tx and not re.search(r'\*\*\s+(?:Fatal|Error):',tx+er)
    rows=[[int(x,16)for x in line.split()]for line in (D/'test.vec').read_text().splitlines()[1:]];scenarios=json.loads((OWN/'attempt03/positive-4-8-8.scenarios.json').read_bytes());r=m.check(D/'same-tag.trace',rows,scenarios,4,8,8);m.save(D/'check.json',r);assert r['error_count']>0
    m.R.update(behaviorally_rejected=True,errors=r['errors'],error_count=r['error_count'],compiled=True,simulator_completed=True,exit=code)
finally:
    m.command('subst-remove',['subst',drive,'/d'],D);code,tx,er=m.command('subst-after',['subst'],D);m.R['mapping_removed']=not any(line.startswith(drive+'\\')for line in tx.splitlines());m.save(D/'receipt.json',m.R)
print(json.dumps({'errors':r['error_count'],'first':r['errors'][:12]}))

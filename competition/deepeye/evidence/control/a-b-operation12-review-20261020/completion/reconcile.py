"""Read-only reconciliation of preserved op12 simulation; no simulator launches."""
import ast
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
from datetime import datetime, timezone

OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
OLD = OWN.parent / 'b-pr30-followup-20261020'
SRC = OLD / 'source'
REV = OLD / 'review'
MAIN = REV / 'work/main-run-04'
EVID = SRC / 'competition/deepeye/evidence/control3d/pwm-atomic-20261020-12/main'
RTL = SRC / 'competition/deepeye/fpga/control3d/deepeye_atomic_pwm.sv'
TB = SRC / 'competition/deepeye/tests/rtl/control3d/main_tb_atomic_pwm.sv'
RUNNER = SRC / 'competition/deepeye/tools/control3d/main_verify_atomic_pwm.py'
HEAD = 'f7e95af8f8abae6d4a5312c08d99e095a7e5dec1'
CONTRACT = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'

def digest(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def identity(p):
    b = p.read_bytes()
    return {'bytes':len(b), 'sha256':digest(b)}
def require(c, m):
    if not c: raise AssertionError(m)
def write(name, obj):
    p = OWN / name
    data=json.dumps(obj, ensure_ascii=False, indent=2)+'\n'
    if p.exists():
        require(p.read_text(encoding='utf-8')==data, 'refuse changed overwrite '+name)
        return
    p.write_text(data, encoding='utf-8')
def inventory(root):
    return {p.relative_to(root).as_posix():identity(p) for p in sorted(root.rglob('*')) if p.is_file()}
def translate(cmd):
    out=[]; skip=False
    for item in cmd[1:]:
        if skip: skip=False; continue
        if item=='-onfinish': skip=True; continue
        if item=='-c': continue
        out.append(item)
    return [cmd[0],'-batch','-syncio',*out]

def main():
    source_start=inventory(SRC); review_start=inventory(REV)
    write('preserved-input-index.json', {'source':source_start, 'original_review':review_start})
    scope=load(REPO/'docs/competition/deepeye-2026/immutable_scope.json')
    require(digest(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==CONTRACT,'H01-H15 hash')
    require([r['id'] for r in scope['requirements']]==['H%02d'%i for i in range(1,16)],'H01-H15 ids')
    transfer=load(REPO/'.planning/deepeye-desktop-handoff-20261015/transfer.json')
    require(transfer['status']=='active' and transfer['director_generation']==2 and transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d','director')
    oldjob=load(OLD/'review-terminal.json')['result'][0]
    require(oldjob['job_id']=='child-5345bee33b45490bbc0c070bd3473a41' and oldjob['status']=='failed' and oldjob['terminal'] is True and oldjob['error']=='TimeoutError: ','original failure')
    integrity=load(OLD/'artifact-integrity.json')
    require(integrity['tested_head']==HEAD and integrity['code_commit']=='61141302a68c3085951721074abbfeec31bfcb3a','head and source')
    require(len(source_start)==357 and set(source_start)==set(integrity['files']),'selected files')
    for rel,expected in integrity['files'].items():
        b=(SRC/rel).read_bytes()
        got={**identity(SRC/rel),'git_blob':hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()}
        require(got==expected, 'source blob '+rel)
    mp=SRC/'handoffs/b/B-DEEPEYE-PWM-ATOMIC-20261020-12/manifest.json'
    ip=mp.with_name('input.json'); manifest=load(mp); inp=load(ip)
    require(identity(mp)['sha256']=='6d6de98ec58741efdd20110dba91ea3cff644ae59901413910fc654376b7cd04','manifest pin')
    require(digest(json.dumps(inp['request'],sort_keys=True,separators=(',',':')).encode())=='9951beb894c52fa1e9ec6ae6f487856125a9a91e7e91b8aae75c297b04420e56','request pin')
    require(len(manifest['files'])==353 and set(manifest['files'])==set(inp['artifacts']),'353 manifest files')
    for rel,entry in manifest['files'].items(): require(entry=={'size':source_start[rel]['bytes'],'sha256':source_start[rel]['sha256']},'manifest '+rel)
    archive=identity(OLD/'archive.raw'); require(archive=={'bytes':integrity['tar_bytes'],'sha256':integrity['tar_sha256']},'archive identity')
    with tarfile.open(OLD/'archive.raw') as tf:
        members=tf.getmembers()
        require(len(members)==2549,'archive member count')
        require(all(not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and not m.issym() and not m.islnk() for m in members),'safe archive members')
    current=load(OWN/'source-inventory-current.json')
    require(current['snapshot_aggregate_sha256']=='63bc299b223c2bab97eaa063f98bb9b7dec86ea951ef94bc25557d02d3995c5f','aggregate')
    for name in ['source-inventory-before.json','source-inventory-after.json']:
        require(load(REV/name)['files']==current['files'], 'source historical unchanged '+name)
    require(identity(RTL)['sha256']=='9dc8ecf96e59a2ae8467bda64572f62eb602d52db535733f236f64ff97c43428','RTL')
    require(identity(TB)['sha256']=='7bff8dbcdb4325910de35e498aea3ebe770db0b6b8ab1280009363f02d9cd228','TB')
    require(identity(RUNNER)['sha256']=='ba2491beffd479c2f1e28ab63dd7eefa4df82d29bf8e0bc2cb80856665cb6839','runner')
    captures=[]
    for p in sorted((REV/'logs').glob('*/command.json')):
        row=load(p); base=p.parent
        for stream in ['stdout','stderr']: require(identity(base/(stream+'.bin'))==row[stream], 'capture '+str(base)+' '+stream)
        require(int((base/'exit_code.txt').read_text())==row['exit_code'],'capture exit')
        captures.append({'label':row['label'],'argv':row['argv'],'exit_code':row['exit_code'],'timed_out':row['timed_out'],'started_utc':row['started_utc'],'finished_utc':row['finished_utc'],'stdout':row['stdout'],'stderr':row['stderr']})
    write('capture-reconciliation.json',captures)
    frozen=load(EVID/'oracle_frozen.json')
    # Execute only inspected definitions/imports, with __main__ disabled; no CLI or sim.
    ns={'__name__':'review_definitions','__file__':str(RUNNER)}
    exec(compile(RUNNER.read_bytes(),str(RUNNER),'exec'), ns)
    cases=[]; total=0
    result=load(MAIN/'result.json'); require(result['status']=='passed','positive result')
    runs=[(MAIN,'main-verifier-run-05')]+[(REV/('work/mutation-'+name+'-01'),'mutation-'+name.replace('_','-')+'-01') for name in ['pitch_from_yaw','stop_ignored']]
    commands=[]
    for run,capture in runs:
        rr=load(run/'result.json')
        for name,p in [('runner.py',RUNNER),('tb.sv',TB)]: require((run/name).read_bytes()==p.read_bytes(),'executed copy '+str(run/name))
        compat=[ast.literal_eval(line[len('COMPAT_VSIM '):]) for line in (REV/('logs/'+capture+'/stderr.bin')).read_text(encoding='utf-8').splitlines() if line.startswith('COMPAT_VSIM ')]
        actual=[]
        for c in rr['commands']:
            for stream in ['stdout','stderr']: require(identity(run/(c['name']+'.'+stream+'.txt'))['sha256']==c[stream+'_sha256'],'tool raw hash '+str(run)+' '+c['name'])
            require(c['exit_code']==0,'tool exit '+c['name'])
            argv=translate(c['command']) if Path(c['command'][0]).name.lower()=='vsim.exe' else c['command']
            if Path(c['command'][0]).name.lower()=='vsim.exe': actual.append(argv)
            commands.append({'run':str(run.relative_to(REV)),'name':c['name'],'runner_recorded_argv':c['command'],'actual_wrapper_argv':argv,'cwd':c['cwd'],'exit_code':c['exit_code'],'stdout_sha256':c['stdout_sha256'],'stderr_sha256':c['stderr_sha256']})
        require(actual==compat,'translated actual argv '+capture)
        require(load(REV/('logs/'+capture+'/command.json'))['exit_code']==0,'outer exit '+capture)
    require((MAIN/'dut.sv').read_bytes()==RTL.read_bytes(),'positive executed RTL copy')
    for f in frozen['cases']:
        w,t=f['count_w'],f['tag_w']; label='w%d_t%d'%(w,t)
        oracle=ns['vectors'](w,t)
        b=(str(len(oracle.rows))+'\n'+'\n'.join(' '.join('%x'%x for x in row) for row in oracle.rows)+'\n').encode('ascii')
        require(digest(b)==f['vectors_sha256'] and len(b)==f['bytes'] and len(oracle.rows)==f['rows'],'frozen schedule '+label)
        require((MAIN/(label+'.vectors.txt')).read_bytes()==b,'stored canonical schedule '+label)
        lines=(MAIN/(label+'.ports.txt')).read_text(encoding='ascii').splitlines()
        require(len(lines)==len(oracle.rows),'trace length '+label)
        for i,(line,row) in enumerate(zip(lines,oracle.rows)):
            fields=line.split(); require([int(fields[0],10),*[int(v,16) for v in fields[1:]]]==[i,*row[8:]],'trace '+label+' '+str(i))
        r=next(x for x in result['runs'] if x['count_w']==w and x['tag_w']==t)
        require(r['ports_sha256']==identity(MAIN/(label+'.ports.txt'))['sha256'] and r['coverage']==f['coverage'],'trace record '+label)
        raw=(MAIN/(label+'.stdout.txt')).read_text(encoding='utf-8')
        marker='MAIN_PWM_PASS rows=%d COUNT_W=%d TAG_W=%d'%(f['rows'],w,t)
        require(raw.count(marker)==1 and not re.search(r'\*\* (Error|Fatal)',raw) and 'Errors: 0, Warnings: 0' in raw,'clean positive '+label)
        require((MAIN/(label+'.stderr.txt')).stat().st_size==0,'positive stderr')
        cases.append({'case':label,'rows':len(lines),'vector':identity(MAIN/(label+'.vectors.txt')),'ports':identity(MAIN/(label+'.ports.txt')),'stdout':identity(MAIN/(label+'.stdout.txt')),'coverage':f['coverage']})
        total+=len(lines)
    require(total==46190,'46190 rows')
    longraw=(MAIN/'long.stdout.txt').read_text(encoding='utf-8')
    longmarker='MAIN_PWM_LONG_PASS full_period=2000000 high_counts=10000,490000,70000 new_period=37 new_frames=2'
    require(longraw.count(longmarker)==1 and not re.search(r'\*\* (Error|Fatal)',longraw) and 'Errors: 0, Warnings: 0' in longraw,'long positive')
    require((MAIN/'long.stderr.txt').stat().st_size==0,'long stderr')
    guards=[]
    for w,t in [(1,32),(33,32),(3,0),(3,65)]:
        p=MAIN/('invalid_w%d_t%d.stdout.txt'%(w,t)); raw=p.read_text(encoding='utf-8')
        marker='** Fatal: ATOMIC_PWM_UNSUPPORTED_PARAMETERS COUNT_W=%d TAG_W=%d'%(w,t)
        require(raw.count(marker)==1 and 'Time: 0 ps' in raw and 'Scope: main_tb_atomic_pwm.dut.g_param_guard File: dut.sv' in raw and 'Errors: 1, Warnings: 0' in raw and 'MAIN_PWM_PASS' not in raw,'guard '+marker)
        guards.append({'count_w':w,'tag_w':t,'exact_marker':marker,'exit_code':0,**identity(p)})
    mutations=[]
    for name,old,new,row,field,got,expected in [
        ('stop_ignored',b'if (rst || stop) begin',b'if (rst) begin',815,13,1,0),
        ('pitch_from_yaw',b'active_high_pitch_q  <= pending_high_pitch_q;',b'active_high_pitch_q  <= pending_high_yaw_q;',12,19,0,1)]:
        src=RTL.read_bytes(); mutant=REV/('mutations/'+name+'/dut.sv'); run=REV/('work/mutation-'+name+'-01')
        require(src.count(old)==1 and mutant.read_bytes()==src.replace(old,new,1),'exact real mutant '+name)
        require((run/'dut.sv').read_bytes()==mutant.read_bytes(),'compiled mutant copy '+name)
        rr=load(run/'result.json'); require(rr['rtl_sha256']==identity(mutant)['sha256'] and rr['status']=='expected_public_port_rejection' and rr['runs'][0]['passed'] is False,'mutant status')
        raw=(run/'w2_t1.stdout.txt').read_text(encoding='utf-8')
        marker='** Fatal: row=%d field=%d got=%016x expected=%016x'%(row,field,got,expected)
        require(raw.count(marker)==1 and 'Errors: 1, Warnings: 0' in raw and 'MAIN_PWM_PASS' not in raw,'counterexample '+name)
        trace=(run/'w2_t1.ports.txt').read_text(encoding='ascii').splitlines(); require(len(trace)==row+1,'partial mutant trace length')
        prefix=trace[-1].split(' FAIL expected=')[0].split(); require(int(prefix[0])==row and int(prefix[-1],16)==got,'mutant trace value')
        vector=(MAIN/'w2_t1.vectors.txt').read_text(encoding='ascii').splitlines()[row+1].split()
        require(int(vector[field],16)==expected,'oracle counterexample')
        require('field=%d'%field in trace[-1] and ('expected=%016x'%expected) in trace[-1],'partial trace diagnostic')
        mutations.append({'name':name,'row':row,'field':field,'got':got,'expected':expected,'mutant':identity(mutant),'stdout':identity(run/'w2_t1.stdout.txt'),'diff':''.join(difflib.unified_diff(src.decode().splitlines(True),mutant.read_text().splitlines(True)))})
    author=EVID/'author-rerun-01'; am=load(author/'AUTHOR_EVIDENCE_MANIFEST.json'); counts={'committed_verified':0,'unavailable_work_entries':0}; aliases=[]
    for ent in am['files']:
        rel=ent['path']; require(not PurePosixPath(rel).is_absolute() and '..' not in PurePosixPath(rel).parts,'author safe path')
        if rel.startswith('work/'):
            require(not (author/rel).exists(),'author work unexpectedly present'); counts['unavailable_work_entries']+=1; continue
        path=author/rel
        if not path.exists():
            require(rel in ['replay_events.log','transcript'],'author unexpected missing '+rel)
            path=author/(rel+'.txt'); aliases.append([rel,path.name])
        require(identity(path)=={'bytes':ent['size_bytes'],'sha256':ent['sha256']},'author published '+rel)
        counts['committed_verified']+=1
    require(len(am['files'])==85 and counts=={'committed_verified':40,'unavailable_work_entries':45},'author counts')
    summary=load(author/'run_summary.json'); author_summary=summary['main_simulation']['summary']
    require({key:author_summary[key] for key in ['cases','pass','fail','checks']}=={'cases':9,'pass':9,'fail':0,'checks':90644277},'author summary')
    orig_audit=load(REV/'result-audit.json'); require(orig_audit['public_port_edge_rows']==total and orig_audit['source_aggregate_sha256']==current['snapshot_aggregate_sha256'],'old result audit correspondence')
    require(orig_audit['main_result']['sha256']==identity(MAIN/'result.json')['sha256'],'old audit result pin')
    require(captures[[c['label'] for c in captures].index('subst-create-R')]['exit_code']==0 and captures[[c['label'] for c in captures].index('subst-remove-R')]['exit_code']==0,'R drive historical cleanup')
    tools={}
    for name,expected in orig_audit['tool_binaries'].items():
        require(identity(Path('C:/modeltech64_2020.4/win64')/name)==expected,'installed tool '+name)
        tools[name]=expected
    require(source_start==inventory(SRC) and review_start==inventory(REV),'preserved original bytes changed')
    output={'schema':1,'status':'evidence_reconciled','at_utc':datetime.now(timezone.utc).isoformat(),'tested_head':HEAD,'source_commit':integrity['code_commit'],'requirements_sha256':CONTRACT,'original_job_terminal':oldjob,'source_files_verified':357,'manifest_entries_verified':353,'archive':archive,'archive_safe_members':len(members),'source_snapshot_aggregate_sha256':current['snapshot_aggregate_sha256'],'original_source_and_review_unchanged_during_reconciliation':True,'captured_commands':len(captures),'simulator_command_records_verified':len(commands),'cases':cases,'public_port_edge_samples':total,'long_case':{'full_frame_intervals':2000000,'high_counts':[10000,490000,70000],'new_period':37,'new_complete_frames':2,'stdout':identity(MAIN/'long.stdout.txt')},'parameter_guards':guards,'mutants':mutations,'author':{**counts,'manifest_entries':85,'aliases':aliases,'groups':9,'author_assertion_invocations':90644277,'rerun':False},'installed_tool_binaries':tools,'frozen_oracle_runner_sha256':frozen['runner_sha256'],'executed_runner_sha256':identity(RUNNER)['sha256'],'frozen_vectors_regenerated_byte_exact':True,'simulation_rerun_by_this_job':False,'reason_no_simulation_rerun':'All unchanged raw simulation outputs, sources, canonical vectors, traces, guards and mutants reconcile; no missing falsifying check found.','not_run':['all_29_formal_cards','G05/B06/R03_system_acceptance','synthesis','implementation','timing','CDC/RDC','physical_board','ABI_or_motion_authority'],'notes':['Original result-audit author.files_verified=85 overstates locally verifiable published entries: 40 checked bytes, 45 unpublished work entries retained as absent.','Runner result records pre-wrapper argv; actual translated batch/syncio argv independently matched raw COMPAT_VSIM stderr.','Original child failed TimeoutError; this is a new evidence reconciliation result, not a relabel of the old job.']}
    write('simulator-command-reconciliation.json',commands)
    write('reconciliation.json',output)
    print(json.dumps({'status':output['status'],'source_files':357,'manifest_entries':353,'samples':total,'guards':len(guards),'mutants':len(mutations),'captured_commands':len(captures),'simulator_command_records':len(commands),'reconciliation':identity(OWN/'reconciliation.json')}))

if __name__=='__main__': main()

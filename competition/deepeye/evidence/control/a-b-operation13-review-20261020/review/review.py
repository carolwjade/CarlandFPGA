"""A child: bounded op13 source audit and independently checked port replay.

No B model/runner is imported. Frozen B vectors are stimulus inputs; every
expected port value is recomputed before compilation from absolute edge times.
All writes, simulator cwd/TEMP and private mutations stay under this directory.
"""
import datetime, difflib, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time, traceback

HERE = pathlib.Path(__file__).absolute().parent
REPO = HERE.parents[2]
INPUT = REPO / '.planning/deepeye-resume-20261018/b-pr30-operation13-20261020'
SRC = INPUT / 'source'
BASE = SRC / 'competition/deepeye'
EVID = BASE / 'evidence/control3d/pwm-edge-measure-20261020-13/main'
TOOL = pathlib.Path('C:/modeltech64_2020.4/win64')
PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
R = {'work_id':'A-B-OP13-INDEPENDENT-20261020-v1', 'agent_id':'/root/b_op13_review_20261020',
     'job_id':'child-353d776cb7564092a0960bce35b6c14f', 'status':'started', 'commands':[], 'cases':[], 'guards':[], 'mutants':[],
     'formal_cards':'29 not_run', 'main_acceptance':'reserved to quality main', 'board':'not_run', 'CDC_RDC':'not_run'}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def sha(p): return digest(p.read_bytes())
def put(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def save(): put(HERE/'receipt.json', R)

def command(label, argv, cwd, timeout=180):
    log = HERE/'commands'/label
    log.mkdir(parents=True)
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.update(TEMP=str(HERE/'temp'), TMP=str(HERE/'temp'), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    argv = list(map(str, argv)); start = now(); clock = time.monotonic()
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    timed_out = False
    try: out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        # Only this owned, recorded process tree may be ended on the bound.
        kill = subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        (log/'timeout-taskkill.stdout').write_bytes(kill.stdout); (log/'timeout-taskkill.stderr').write_bytes(kill.stderr)
        out, err = p.communicate(timeout=20)
    (log/'stdout.txt').write_bytes(out); (log/'stderr.txt').write_bytes(err)
    rec = {'argv':argv,'cwd':str(cwd),'pid':p.pid,'started_utc':start,'finished_utc':now(),'duration_s':round(time.monotonic()-clock,3),
           'exit_code':p.returncode,'timed_out':timed_out,'actual_process_exited':p.poll() is not None,'stdout_sha256':digest(out),'stderr_sha256':digest(err),
           'environment_overrides':{k:env[k] for k in ['TEMP','TMP','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE']}}
    put(log/'command.json',rec); R['commands'].append({'label':label,**rec}); save()
    assert not timed_out, label+' timeout'
    return p.returncode, out, err

def inventory():
    data=json.loads((INPUT/'artifact-integrity.json').read_bytes()); actual={}
    for rel, expected in data['files'].items():
        b=(SRC/rel).read_bytes()
        item={'bytes':len(b),'sha256':digest(b),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
        assert item==expected,(rel,item,expected)
        actual[rel]=item
    return actual

def authority():
    d=json.loads((REPO/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    h=digest(json.dumps(d['requirements'], ensure_ascii=False, sort_keys=True, separators=(',',':')).encode())
    assert h==PIN and [x['id'] for x in d['requirements']]==['H%02d'%i for i in range(1,16)]
    t=json.loads((REPO/'.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
    assert t['status']=='active' and t['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d' and t['director_generation']==2
    hand=SRC/'handoffs/b/B-DEEPEYE-PWM-EDGE-MEASURE-20261020-13'
    m=json.loads((hand/'manifest.json').read_bytes()); inp=json.loads((hand/'input.json').read_bytes())
    assert sha(hand/'manifest.json')=='47382b6eeb6a9fd24b60f6c0d209328c141a4e3f513a55c472e7313b50121230'
    assert m['request']==inp['request'] and m['request_hash']=='1a3bf5940f10ae3d0076ecb192490dfcd8e672efc9ab507194e8031b3ae5fd33'
    rq=inp['request']; assert rq['operation_id']=='B-DEEPEYE-PWM-EDGE-MEASURE-20261020-13' and rq['code_commit']=='923e19dedf53b0b38134e4a7da3cc121d8c0e505'
    return {'contract':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':h, 'requirement_ids':[x['id'] for x in d['requirements']],
            'director_generation':2,'director_thread':t['new_director_thread_id'],'tested_head':'732a58ba60c7cce0027d683e912d986453755843',
            'code_commit':rq['code_commit'],'operation_id':rq['operation_id'],'request_hash':m['request_hash'],'manifest_sha256':sha(hand/'manifest.json'),
            'selected_files':373,'manifest_entries':len(m['files'])}

class TimeOracle:
    """External sample history and transport mailbox; no DUT counters/state.

    A measurement is a pair of transition timestamps and an expiry deadline.
    Aborts establish a new epoch. An overflowing fresh rise establishes a new
    timestamp at the same edge, regardless of transport mailbox occupancy.
    """
    def __init__(self,w,t):
        self.max=(1<<w)-1; self.tm=(1<<t)-1; self.edge=-1; self.on=False
        self.level=0; self.origin=None; self.falling=None; self.deadline=None
        self.epoch_tag=0; self.mail=None; self.seen_ov=0; self.seen_drop=0; self.loss=0
        self.stats={'records':0,'retired':0,'overflow':0,'overrun':0,'saturated_events':0,'same_edge_replace':0,'fresh_overflow_rise':0}
        self.pairs=set(); self.witness=[]
    def step(self,reset,stop,rearm,level,tag,ready):
        self.edge+=1; e=self.edge
        masked=bool(reset or stop or rearm)
        pre=int(self.mail is not None and not masked); ov=drop=0
        if masked:
            self.on=bool(rearm and not(reset or stop)); self.level=level if self.on else 0
            self.origin=self.falling=self.deadline=None; self.mail=None
            self.epoch_tag=(tag&self.tm) if self.on else 0
            self.seen_ov=self.seen_drop=self.loss=0
        elif self.on:
            rising=level==1 and self.level==0; falling=level==0 and self.level==1
            self.level=level
            retired=self.mail is not None and ready
            if retired: self.mail=None; self.stats['retired']+=1
            if self.deadline is not None and e==self.deadline:
                ov=1; self.seen_ov=1
                self.witness.append({'edge':e,'kind':'overflow','origin':self.origin,'elapsed':e-self.origin,'fresh_rise':rising,'older_slot_retired':bool(retired),'older_slot_preserved':self.mail is not None})
                self.origin=self.falling=self.deadline=None
                if rising:
                    self.origin=e; self.deadline=e+self.max+1; self.stats['fresh_overflow_rise']+=1
            elif rising:
                if self.origin is not None:
                    assert self.falling is not None
                    p=e-self.origin; h=self.falling-self.origin
                    assert 1<=h<p<=self.max
                    self.pairs.add((p,h))
                    if self.mail is None:
                        self.mail=(p,h,self.epoch_tag); self.stats['records']+=1
                        self.stats['same_edge_replace']+=int(retired)
                    else: drop=1; self.seen_drop=1
                    if p>=32768: self.witness.append({'edge':e,'kind':'record','r0':self.origin,'fall':self.falling,'r1':e,'period':p,'high':h,'tag':self.epoch_tag,'dropped':bool(drop)})
                self.origin=e; self.falling=None; self.deadline=e+self.max+1
            elif falling and self.origin is not None:
                assert self.falling is None
                self.falling=e
            if ov or drop:
                self.stats['saturated_events']+=int(self.loss==self.max)
                self.loss=min(self.loss+1,self.max)
        self.stats['overflow']+=ov; self.stats['overrun']+=drop
        payload=self.mail or (0,0,0)
        return [pre,int(self.on),int(self.mail is not None and not masked),*payload,ov,drop,self.seen_ov,self.seen_drop,self.loss]

def check_vectors(w,t,p):
    lines=p.read_text(encoding='ascii').splitlines(); rows=[[int(x,16) for x in line.split()] for line in lines[1:]]
    assert int(lines[0])==len(rows)
    oracle=TimeOracle(w,t)
    for ri,row in enumerate(rows):
        assert len(row)==18
        for repeat in range(row[0]):
            exp=oracle.step(*row[1:7])
            assert exp==row[7:],{'row':ri,'repeat':repeat,'edge':oracle.edge,'independent_expected':exp,'frozen_values':row[7:]}
    if w<=4:
        required={(p,h) for p in range(2,1<<w) for h in range(1,p)}
        assert required<=oracle.pairs
        assert oracle.stats['saturated_events']>0
    if w==16:
        assert {(65535,1),(65535,32768),(65535,65534)}<=oracle.pairs
        assert any(v['kind']=='overflow' and v['elapsed']==65536 and v['fresh_rise'] for v in oracle.witness)
    return rows, {'count_w':w,'tag_w':t,'edges':oracle.edge+1,'rle_rows':len(rows),'vectors_sha256':sha(p),'events':oracle.stats,
                  'all_observed_pairs':sorted(oracle.pairs),'wide_and_overflow_witnesses':oracle.witness}

def good_compile(code,out,err):
    assert code==0 and not err and not re.search(rb'\*\* (?:Error|Fatal|Warning)',out)
    assert re.search(rb'Errors:\s*0,\s*Warnings:\s*0',out)

def main():
    assert not (HERE/'commands').exists(),'fresh output required'
    (HERE/'temp').mkdir(); (HERE/'run').mkdir(); R['started_utc']=now(); save()
    R['authority']=authority(); inv=inventory(); put(HERE/'source-inventory-before.json',inv)
    R['source_aggregate_sha256']=digest(json.dumps(inv,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    rtl=BASE/'fpga/control3d/deepeye_pwm_edge_measure.sv'; tb=BASE/'tests/rtl/control3d/main_tb_pwm_edge_measure.sv'
    R['source_hashes']={'rtl':sha(rtl),'public_tb':sha(tb),'b_main_runner':sha(BASE/'tools/control3d/main_verify_pwm_edge_measure.py'),'own_oracle_runner':sha(pathlib.Path(__file__))}
    R['tool_hashes']={exe:sha(TOOL/(exe+'.exe')) for exe in ['vlib','vlog','vsim','vsimk']}
    shutil.copyfile(rtl,HERE/'run/dut.sv'); shutil.copyfile(tb,HERE/'run/tb.sv')
    checked=[]
    for w,t in [(2,1),(3,64),(4,32),(16,64),(32,64)]:
        label=f'w{w}_t{t}'; src=EVID/'frozen-harness-03'/(label+'.vectors.txt'); dst=HERE/'run'/(label+'.vectors.txt')
        shutil.copyfile(src,dst); rows,rec=check_vectors(w,t,dst); checked.append((label,rows,rec)); R['cases'].append(rec)
    put(HERE/'independent-oracle-before-simulation.json', {'at_utc':now(),'runner_sha256':sha(pathlib.Path(__file__)),'cases':R['cases'],'method':'absolute timestamps, expiry deadlines and external transport mailbox; no B model import'})
    R['oracle_frozen_before_compile']=True; save()
    # Use only a verified unused mapping to this owned directory. No global env edits.
    code,out,err=command('subst-before',['subst'],HERE)
    assert code==0 and not err and not pathlib.Path('Q:/').exists() and b'Q:' not in out.upper()
    code,out,err=command('subst-create',['subst','Q:',str(HERE)],HERE)
    assert code==0 and not err
    R['mapping_created']=True; save()
    cwd=pathlib.Path('Q:/run')
    (HERE/'run/run.do').write_bytes(b'onerror {quit -code 1}\nrun -all\nquit -code 0\n')
    for exe in ['vlog','vsim']:
        c,o,e=command(exe+'-version',[TOOL/(exe+'.exe'),'-version'],cwd); assert c==0
    c,o,e=command('vlib',[TOOL/'vlib.exe','work'],cwd); assert c==0 and not e
    good_compile(*command('vlog',[TOOL/'vlog.exe','-sv','-work','work','dut.sv','tb.sv'],cwd))
    def launch(label,w,t,lib='work',v='w2_t1.vectors.txt'):
        return command(label,[TOOL/'vsim.exe','-batch','-syncio',lib+'.main_tb_pwm_edge_measure',f'-gCOUNT_W={w}',f'-gTAG_W={t}',
                              '+VECTORS='+v,'+TRACE='+label+'.ports.txt','-do','run.do'],cwd)
    for label,rows,rec in checked:
        c,o,e=launch(label,rec['count_w'],rec['tag_w'],v=label+'.vectors.txt')
        assert c==0 and not e and not re.search(rb'\*\* (?:Error|Fatal|Warning)',o)
        assert ('MAIN_EDGE_MEASURE_PASS edges=%d rows=%d'%(rec['edges'],rec['rle_rows'])).encode() in o
        assert re.search(rb'Errors:\s*0,\s*Warnings:\s*0',o)
        ports=HERE/'run'/(label+'.ports.txt'); lines=ports.read_text().splitlines(); assert len(lines)==len(rows)
        edges=0
        for ri,(line,row) in enumerate(zip(lines,rows)):
            edges+=row[0]; cols=line.split()
            assert list(map(int,cols[:3]))==[ri,edges,row[0]] and [int(x,16) for x in cols[3:]]==row[7:]
        rec.update(simulation_passed=True,ports_sha256=sha(ports),exit_code=c); save()
    for w,t in [(1,32),(33,32),(3,0),(3,65),(0,32),(-1,32),(3,-1)]:
        label=f'guard_w{w}_t{t}'; c,o,e=launch(label,w,t)
        fatal=f'PWM_EDGE_UNSUPPORTED_PARAMETERS COUNT_W={w} TAG_W={t}'.encode()
        assert not e and o.count(b'** Fatal:')==1 and fatal in o and b'MAIN_EDGE_MEASURE_PASS' not in o and b'PUBLIC_PORT_MISMATCH' not in o
        assert re.search(rb'Time:\s*0\s+(?:ps|ns)',o) and b'g_param_guard' in o and b'main_tb_pwm_edge_measure' in o
        assert re.search(rb'Errors:\s*1,\s*Warnings:\s*0',o) and b'** Error' not in o and b'** Warning' not in o
        R['guards'].append({'count_w':w,'tag_w':t,'actual_exit':c,'exact_fatal':fatal.decode(),'scope':'main_tb_pwm_edge_measure.dut.g_param_guard','time':'0','diagnostic':'Errors: 1, Warnings: 0','stdout_sha256':digest(o)}); save()
    original=rtl.read_bytes()
    for label in ['high-plus-one','rearm-stale-slot']:
        mut=EVID/'mutants'/(label+'.sv'); target=HERE/'run'/(label+'.sv'); shutil.copyfile(mut,target)
        before=original.decode().splitlines(keepends=True); after=target.read_text().splitlines(keepends=True)
        diff=''.join(difflib.unified_diff(before,after,fromfile='exact-original',tofile=label))
        (HERE/(label+'.diff')).write_text(diff,encoding='utf-8'); assert diff
        lib='mut_'+label.replace('-','_')
        c,o,e=command(label+'-vlib',[TOOL/'vlib.exe',lib],cwd); assert c==0 and not e
        good_compile(*command(label+'-vlog',[TOOL/'vlog.exe','-sv','-work',lib,target.name,'tb.sv'],cwd))
        c,o,e=launch(label,2,1,lib=lib)
        assert not e and b'PUBLIC_PORT_MISMATCH' in o and b'** Fatal:' in o and b'MAIN_EDGE_MEASURE_PASS' not in o
        assert b'file open failed' not in o and b'g_param_guard' not in o and re.search(rb'Errors:\s*1,\s*Warnings:\s*0',o)
        R['mutants'].append({'label':label,'actual_exit':c,'rtl_sha256':sha(target),'diff_sha256':sha(HERE/(label+'.diff')),
                             'public_counterexample':re.search(rb'PUBLIC_PORT_MISMATCH[^\r\n]*',o).group().decode(),'stdout_sha256':digest(o)}); save()
    assert rtl.read_bytes()==original
    after=inventory(); assert inv==after; put(HERE/'source-inventory-after.json',after)
    R['source_unchanged']=True; R['sampled_edges']=sum(x['edges'] for x in R['cases']); R['rle_rows']=sum(x['rle_rows'] for x in R['cases'])
    R['small_width_legal_pairs']=3+21+105; R['status']='bounded_independent_simulation_passed'; save()

if __name__=='__main__':
    try: main()
    except Exception as ex:
        R['status']='failed'; R['error']=repr(ex); (HERE/'failure-traceback.txt').write_text(traceback.format_exc(),encoding='utf-8'); save()
    finally:
        if R.get('mapping_created'):
            try:
                c,o,e=command('subst-remove',['subst','Q:','/D'],HERE); R['mapping_removed']=c==0 and not pathlib.Path('Q:/').exists()
            except Exception as ex: R['cleanup_error']=repr(ex)
        R['finished_utc']=now(); save()
    print(json.dumps({k:R.get(k) for k in ['status','error','sampled_edges','rle_rows','small_width_legal_pairs','source_unchanged','mapping_removed']},ensure_ascii=False))
    sys.exit(0 if R['status']=='bounded_independent_simulation_passed' and R.get('mapping_removed') else 1)

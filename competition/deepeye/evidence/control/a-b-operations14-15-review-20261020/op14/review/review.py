"""A bounded op14 review. No B Python module is imported or executed.

Public stimulus/replay TB are reused from the pinned handoff. Expected values
come from this event ledger, written after RTL/B-reference inspection. Freeze
chronology is before this A simulation only. All writes stay under HERE.
"""
import datetime, difflib, hashlib, itertools, json, os, pathlib, re, shutil, subprocess, sys, time, traceback

HERE=pathlib.Path(__file__).absolute().parent
REPO=HERE.parents[2]
INPUT=REPO/'.planning/deepeye-resume-20261018/b-pr30-operations14-15-20261020/14'
SRC=INPUT/'source'; BASE=SRC/'competition/deepeye'
EVID=BASE/'evidence/control3d/pwm-coherent-capture-20261020-14/main'
TOOL=pathlib.Path('C:/modeltech64_2020.4/win64')
PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
R={'work_id':'A-B-OP14-INDEPENDENT-20261020-v1','agent_id':'/root/b_op14_review_20261020',
   'job_id':'child-9f94617fff6047d9b56574520f9b431c','status':'started','commands':[],'cases':[],'guards':[],'mutants':[],
   'formal_cards':'29 not_run','main_acceptance':'reserved to quality main','board':'not_run','CDC_RDC':'not_run'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def put(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save():put(HERE/'receipt.json',R)

def command(label,argv,cwd,timeout=180):
    log=HERE/'commands'/label;log.mkdir(parents=True)
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    env.update(TEMP=str(HERE/'temp'),TMP=str(HERE/'temp'),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    argv=list(map(str,argv));start=now();clock=time.monotonic()
    p=subprocess.Popen(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    timed=False
    try:out,err=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed=True
        k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        (log/'timeout-taskkill.stdout').write_bytes(k.stdout);(log/'timeout-taskkill.stderr').write_bytes(k.stderr)
        out,err=p.communicate(timeout=20)
    (log/'stdout.txt').write_bytes(out);(log/'stderr.txt').write_bytes(err)
    rec={'argv':argv,'cwd':str(cwd),'pid':p.pid,'started_utc':start,'finished_utc':now(),'duration_s':round(time.monotonic()-clock,3),
         'exit_code':p.returncode,'timed_out':timed,'actual_process_exited':p.poll() is not None,'stdout_sha256':digest(out),'stderr_sha256':digest(err),
         'environment_overrides':{k:env[k] for k in ['TEMP','TMP','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE']}}
    put(log/'command.json',rec);R['commands'].append({'label':label,**rec});save()
    assert not timed,label+' timeout'
    return p.returncode,out,err

def inventory():
    data=json.loads((INPUT/'artifact-integrity.json').read_bytes());actual={}
    for rel,expected in data['files'].items():
        b=(SRC/rel).read_bytes()
        item={'bytes':len(b),'sha256':digest(b),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
        assert item==expected,(rel,item,expected)
        actual[rel]=item
    assert len(actual)==309
    return actual

def authority():
    d=json.loads((REPO/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    h=digest(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
    assert h==PIN and [x['id'] for x in d['requirements']]==['H%02d'%i for i in range(1,16)]
    t=json.loads((REPO/'.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
    assert t['status']=='active' and t['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d' and t['director_generation']==2
    hand=SRC/'handoffs/b/B-DEEPEYE-PWM-COHERENT-CAPTURE-20261020-14'
    m=json.loads((hand/'manifest.json').read_bytes());inp=json.loads((hand/'input.json').read_bytes())
    assert sha(hand/'manifest.json')=='f93e490bb0da5fb7e676538ec29e73aa56aacd388b574351de008b1d61ea8602'
    assert m['request']==inp['request'] and m['request_hash']=='1d23fc80980b0269bece376230d3722892355b725e217f7644e5b519b8230970'
    rq=inp['request'];assert rq['operation_id']=='B-DEEPEYE-PWM-COHERENT-CAPTURE-20261020-14' and rq['code_commit']=='21ae4c6bc9d03aea8a79bf784d9873ebdaf1c903'
    assert digest(json.dumps(rq,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==m['request_hash']
    return {'contract':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':h,'director_generation':2,'director_thread':t['new_director_thread_id'],
            'tested_head':'7dd2c4108ee49cc6e0feb7c715d786f8b11a99c2','code_commit':rq['code_commit'],'operation_id':rq['operation_id'],
            'request_hash':m['request_hash'],'manifest_sha256':sha(hand/'manifest.json'),'selected_files':309,'manifest_entries':len(m['files'])}

class EventLedger:
    """Timestamped observed transition history and a separate consumer mailbox.

    No per-lane capture counters or stored high widths. At a common closing
    rise, find each lane's first actual falling event strictly inside R0/R1.
    A common event selects a new R0; a subset event invalidates that selection.
    Expiry uses absolute sample deadlines and never a DUT-like incrementing age.
    """
    def __init__(self,c,w,t):
        self.cm=(1<<c)-1;self.wm=(1<<w)-1;self.tagmask=(1<<t)-1
        self.e=-1;self.enabled=False;self.last=0;self.window=None;self.r0=None
        self.events=[];self.tag=0;self.mail=None;self.seen=[0]*4;self.loss=0
        self.stats={k:0 for k in ['records','retired','incoherent','period_overflow','witness_overflow','overrun','saturated_faults','same_edge_refill','fresh_overflow_common','retire_unarmed','preserved_queue_faults','witness_outranks_count','mixed_rise_fall','tag_input_changed','abort_old_queue']}
        self.triples=set();self.tags=set();self.witness=[]
    def sample(self,rst,stop,rearm,levels,tag,ready):
        self.e+=1;e=self.e;mask=bool(rst or stop or rearm)
        pre=int(self.mail is not None and not mask);pulse=[0]*4
        oldmail=self.mail;oldr0=self.r0;fault=None;rise=fall=0;retired=False
        if mask:
            self.stats['abort_old_queue']+=int(oldmail is not None)
            self.enabled=bool(rearm and not(rst or stop));self.last=levels if self.enabled else 0
            self.window=e if self.enabled else None;self.r0=None;self.events=[]
            self.tag=tag&self.tagmask if self.enabled else 0;self.mail=None;self.seen=[0]*4;self.loss=0
        else:
            if self.mail is not None and ready:
                self.mail=None;retired=True;self.stats['retired']+=1;self.stats['retire_unarmed']+=int(not self.enabled)
            if self.enabled:
                self.stats['tag_input_changed']+=int((tag&self.tagmask)!=self.tag)
                if e>self.window+self.wm:
                    fault=2;self.enabled=False;self.r0=None
                    self.stats['witness_outranks_count']+=int(oldr0 is not None and e>oldr0+self.cm)
                else:
                    rise=(levels^self.last)&levels;fall=(levels^self.last)&self.last
                    self.last=levels
                    if rise or fall:self.events.append((e,rise,fall))
                    self.stats['mixed_rise_fall']+=int(bool(rise and fall))
                    if self.r0 is not None and e>self.r0+self.cm:
                        fault=1;self.r0=e if rise==7 else None
                        self.stats['fresh_overflow_common']+=int(rise==7)
                    elif rise==7:
                        if self.r0 is not None:
                            falls=[next((at for at,_,fm in self.events if self.r0<at<e and fm&(1<<lane)),None) for lane in range(3)]
                            if all(at is not None for at in falls):
                                p=e-self.r0;highs=tuple(at-self.r0 for at in falls)
                                assert all(1<=h<p<=self.cm for h in highs)
                                self.triples.add((p,*highs));self.tags.add(self.tag)
                                candidate=(p,*highs,self.r0-self.window,e-self.window,self.tag)
                                if self.mail is None:
                                    self.mail=candidate;self.stats['records']+=1;self.stats['same_edge_refill']+=int(retired)
                                else:fault=3
                                if p>=32768:self.witness.append({'edge':e,'kind':'candidate','r0':self.r0,'fall_edges':falls,'r1':e,'payload':candidate,'dropped':fault==3})
                            else:fault=0
                        self.r0=e
                        # History strictly before this new common event can never contribute.
                        self.events=[]
                    elif rise:
                        fault=0;self.r0=None;self.events=[]
            if fault is not None:
                pulse[fault]=1;self.seen[fault]=1
                self.stats[['incoherent','period_overflow','witness_overflow','overrun'][fault]]+=1
                self.stats['saturated_faults']+=int(self.loss==self.cm);self.loss=min(self.cm,self.loss+1)
                self.stats['preserved_queue_faults']+=int(oldmail is not None and not retired and self.mail==oldmail)
                if fault in [1,2]:self.witness.append({'edge':e,'kind':['incoherent','period_overflow','witness_overflow','overrun'][fault],
                    'window_tick':e-self.window,'old_r0':oldr0,'elapsed':None if oldr0 is None else e-oldr0,'rise':rise,'fall':fall,
                    'older_slot_preserved':oldmail is not None and not retired and self.mail==oldmail,'older_slot_retired':retired})
        payload=self.mail or (0,)*7
        return [pre,int(self.enabled),int(self.mail is not None and not mask),*payload,*pulse,*self.seen,self.loss]

def check_vectors(c,w,t,p):
    lines=p.read_text(encoding='ascii').splitlines();rows=[[int(x,16) for x in line.split()] for line in lines[1:]]
    assert len(rows)==int(lines[0]);oracle=EventLedger(c,w,t);fresh=[]
    for ri,row in enumerate(rows):
        assert len(row)==26
        for repeat in range(row[0]):
            expected=oracle.sample(*row[1:7])
            if expected!=row[7:]:
                put(HERE/'oracle-discrepancy.json',{'row':ri,'repeat':repeat,'edge':oracle.e,'input':row[1:7],'expected':expected,'frozen_values':row[7:]})
                raise AssertionError('Independent oracle differs from frozen handoff')
        fresh.append([row[0],*row[1:7],*expected])
    b=(str(len(fresh))+'\n'+'\n'.join(' '.join(format(x,'x') for x in row) for row in fresh)+'\n').encode('ascii')
    assert b==p.read_bytes(),'Independent expected-vector reconstruction must match bytes'
    if c<=3 and w>=6:
        legal={(p,*hs) for p in range(2,1<<c) for hs in itertools.product(range(1,p),repeat=3)}
        assert legal<=oracle.triples and oracle.stats['saturated_faults']>0
    if c==16:
        assert {(65535,1,32768,65534),(32768,1,16384,32767),(32769,32768,2,1)}<=oracle.triples
        assert any(v['kind']=='period_overflow' and v['elapsed']==65536 and v['rise']==7 for v in oracle.witness)
    return rows,{'count_w':c,'witness_w':w,'tag_w':t,'edges':oracle.e+1,'rle_rows':len(rows),'vectors_sha256':sha(p),
                 'events':oracle.stats,'observed_triples':sorted(oracle.triples),'admitted_or_dropped_epoch_tags':sorted(oracle.tags),'boundary_witnesses':oracle.witness}

def good_compile(code,out,err):
    assert code==0 and not err and not re.search(rb'\*\* (?:Error|Fatal|Warning)',out)
    assert re.search(rb'Errors:\s*0,\s*Warnings:\s*0',out)

def main():
    assert not (HERE/'commands').exists(),'fresh output required'
    (HERE/'temp').mkdir();(HERE/'run').mkdir();R['started_utc']=now();save()
    R['authority']=authority();before=inventory();put(HERE/'source-inventory-before.json',before)
    R['source_aggregate_sha256']=digest(json.dumps(before,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    rtl=BASE/'fpga/control3d/deepeye_pwm_coherent_capture.sv';tb=BASE/'tests/rtl/control3d/main_tb_pwm_coherent_capture.sv'
    R['source_hashes']={'rtl':sha(rtl),'public_tb':sha(tb),'b_main_runner':sha(BASE/'tools/control3d/main_verify_pwm_coherent_capture.py'),'own_oracle_runner':sha(pathlib.Path(__file__))}
    R['tool_hashes']={exe:sha(TOOL/(exe+'.exe')) for exe in ['vlib','vlog','vsim','vsimk']}
    shutil.copyfile(rtl,HERE/'run/dut.sv');shutil.copyfile(tb,HERE/'run/tb.sv');shutil.copyfile(HERE/'guard_tb.sv',HERE/'run/guard_tb.sv')
    checked=[]
    for c,w,t in [(2,6,1),(3,6,64),(2,2,64),(2,3,32),(16,17,64),(32,64,64)]:
        label=f'c{c}_w{w}_t{t}';dst=HERE/'run'/(label+'.vectors.txt');shutil.copyfile(EVID/'frozen-harness02'/dst.name,dst)
        rows,rec=check_vectors(c,w,t,dst);checked.append((label,rows,rec));R['cases'].append(rec)
    put(HERE/'independent-oracle-before-simulation.json',{'at_utc':now(),'runner_sha256':sha(pathlib.Path(__file__)),'cases':R['cases'],
        'method':'Observed transition ledger, absolute deadlines and separate transport mailbox; no B module/model import; after RTL/reference inspection, before A compilation'})
    R['oracle_frozen_before_compile']=True;save()
    c,o,e=command('subst-before',['subst'],HERE)
    assert c==0 and not e and not pathlib.Path('Q:/').exists() and b'Q:' not in o.upper()
    c,o,e=command('subst-create',['subst','Q:',str(HERE)],HERE);assert c==0 and not e;R['mapping_created']=True;save()
    cwd=pathlib.Path('Q:/run');(HERE/'run/run.do').write_bytes(b'onerror {quit -code 1}\nrun -all\nquit -code 0\n')
    for exe in ['vlog','vsim']:
        c,o,e=command(exe+'-version',[TOOL/(exe+'.exe'),'-version'],cwd);assert c==0 and not e
    c,o,e=command('vlib',[TOOL/'vlib.exe','work'],cwd);assert c==0 and not e
    good_compile(*command('vlog',[TOOL/'vlog.exe','-sv','-work','work','dut.sv','tb.sv','guard_tb.sv'],cwd))
    def launch(label,c,w,t,lib='work',top='main_tb_pwm_coherent_capture',v='c3_w6_t64.vectors.txt'):
        return command(label,[TOOL/'vsim.exe','-batch','-syncio',lib+'.'+top,f'-gCOUNT_W={c}',f'-gWITNESS_W={w}',f'-gTAG_W={t}',
                              '+VECTORS='+v,'+TRACE='+label+'.ports.txt','-do','run.do'],cwd)
    for label,rows,rec in checked:
        c,o,e=launch(label,rec['count_w'],rec['witness_w'],rec['tag_w'],v=label+'.vectors.txt')
        assert c==0 and not e and not re.search(rb'\*\* (?:Error|Fatal|Warning)',o)
        assert ('MAIN_COHERENT_CAPTURE_PASS edges=%d rows=%d'%(rec['edges'],rec['rle_rows'])).encode() in o
        assert re.search(rb'Errors:\s*0,\s*Warnings:\s*0',o)
        ports=HERE/'run'/(label+'.ports.txt');lines=ports.read_text().splitlines();assert len(lines)==len(rows);edges=0
        for ri,(line,row) in enumerate(zip(lines,rows)):
            edges+=row[0];cols=line.split();assert list(map(int,cols[:3]))==[ri,edges,row[0]] and [int(x,16) for x in cols[3:]]==row[7:]
        rec.update(simulation_passed=True,ports_sha256=sha(ports),trace_equals_B=sha(ports)==sha(EVID/'run-02'/ports.name),exit_code=c);save()
    for c,w,t in [(1,8,32),(33,8,32),(0,8,32),(-1,8,32),(3,1,32),(3,65,32),(3,0,32),(3,-1,32),(3,8,0),(3,8,-1),(3,8,65)]:
        label=f'guard_c{c}_w{w}_t{t}';code,o,e=launch(label,c,w,t,top='guard_tb')
        display=f'DEEPEYE_COHERENT_INVALID_PARAM COUNT_W={c} WITNESS_W={w} TAG_W={t}'.encode()
        fatal=b'** Fatal: DEEPEYE_COHERENT_INVALID_PARAM unsupported widths'
        assert not e and o.count(b'** Fatal:')==1 and fatal in o and display in o[:o.index(fatal)]
        assert b'GUARD_MISSING' not in o and b'MAIN_COHERENT_CAPTURE_PASS' not in o
        assert re.search(rb'Time:\s*0\s+(?:ps|ns)',o) and b'guard_tb.dut' in o
        assert re.search(rb'Errors:\s*1,\s*Warnings:\s*0',o) and b'** Error' not in o and b'** Warning' not in o
        R['guards'].append({'count_w':c,'witness_w':w,'tag_w':t,'actual_exit':code,'exact_display':display.decode(),
                            'exact_fatal':fatal.decode(),'scope':'guard_tb.dut','time':'0 ps','stdout_sha256':digest(o)});save()
    original=rtl.read_bytes()
    for label in ['relaxed_common_R1','stale_rearm_slot']:
        target=HERE/'run'/(label+'.sv');shutil.copyfile(EVID/(label+'.sv'),target)
        diff=''.join(difflib.unified_diff(original.decode().splitlines(keepends=True),target.read_text().splitlines(keepends=True),fromfile='exact-original',tofile=label))
        (HERE/(label+'.diff')).write_text(diff,encoding='utf-8');assert diff
        lib='mut_'+label.lower();c,o,e=command(label+'-vlib',[TOOL/'vlib.exe',lib],cwd);assert c==0 and not e
        good_compile(*command(label+'-vlog',[TOOL/'vlog.exe','-sv','-work',lib,target.name,'tb.sv'],cwd))
        c,o,e=launch(label,3,6,64,lib=lib)
        assert not e and b'PUBLIC_PORT_MISMATCH' in o and b'** Fatal:' in o and b'MAIN_COHERENT_CAPTURE_PASS' not in o
        assert b'file open failed' not in o and b'INVALID_PARAM' not in o and re.search(rb'Errors:\s*1,\s*Warnings:\s*0',o)
        R['mutants'].append({'label':label,'actual_exit':c,'rtl_sha256':sha(target),'diff_sha256':sha(HERE/(label+'.diff')),
                             'public_counterexample':re.search(rb'PUBLIC_PORT_MISMATCH[^\r\n]*',o).group().decode(),'stdout_sha256':digest(o)});save()
    assert rtl.read_bytes()==original
    after=inventory();assert before==after;put(HERE/'source-inventory-after.json',after)
    R.update(source_unchanged=True,sampled_edges=sum(x['edges'] for x in R['cases']),rle_rows=sum(x['rle_rows'] for x in R['cases']),
             small_width_legal_triples=450,repeated_short_window_triples=9,status='bounded_independent_simulation_passed');save()

if __name__=='__main__':
    try:main()
    except Exception as ex:
        R.update(status='failed',error=repr(ex));(HERE/'failure-traceback.txt').write_text(traceback.format_exc(),encoding='utf-8');save()
    finally:
        if R.get('mapping_created'):
            try:
                c,o,e=command('subst-remove',['subst','Q:','/D'],HERE);R['mapping_removed']=c==0 and not pathlib.Path('Q:/').exists()
            except Exception as ex:R['cleanup_error']=repr(ex)
        R['finished_utc']=now();save()
    print(json.dumps({k:R.get(k) for k in ['status','sampled_edges','rle_rows','source_unchanged','mapping_removed','error']}))
    sys.exit(0 if R['status']=='bounded_independent_simulation_passed' and R.get('mapping_removed') else 1)

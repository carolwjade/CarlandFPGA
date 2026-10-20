"""Fresh op15 public-port sample history checker; imports no B model or runner.
The checker observes absolute edge intervals, not DUT counters. It was written
after inspection; frozen before these fresh simulations, not before B authorship.
"""
import datetime,hashlib,json,os,re,shutil,subprocess,time,traceback
from pathlib import Path
OWN=Path(__file__).resolve().parent
D=OWN/'attempt03'
SRC=OWN.parent/'b-pr30-operations14-15-20261020/15/source/competition/deepeye'
TOOL=Path('C:/modeltech64_2020.4/win64')
R={'commands':[],'runs':[],'guards':[],'mutants':[],'formal_cards':'all29 not_run','authority':'quality main alone decides acceptance'}
FIELDS='cfg_ready accepted rejected applied frame_start running pending pwm active_period active_high_yaw active_high_pitch active_high_speed active_tag window_active window_started capture_armed out_valid out_period out_high0 out_high1 out_high2 out_start out_end out_tag expected_period expected_high0 expected_high1 expected_high2 expected_tag raw_fault_events failure_event failure_code'.split()
INPUT='rst stop cfg_valid cfg_period cfg_high_yaw cfg_high_pitch cfg_high_speed cfg_tag drive_levels loopback out_ready'.split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def command(label,args,cwd,timeout=90):
    out=D/'commands'/label;out.mkdir(parents=True)
    env=os.environ.copy();env.update(TEMP=str(D/'temp'),TMP=str(D/'temp'),PYTHONDONTWRITEBYTECODE='1')
    p=subprocess.Popen(list(map(str,args)),cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    start=now();timed=False
    try:a,b=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);(out/'kill.stdout').write_bytes(k.stdout);(out/'kill.stderr').write_bytes(k.stderr);a,b=p.communicate(timeout=20)
    (out/'stdout.txt').write_bytes(a);(out/'stderr.txt').write_bytes(b)
    r={'label':label,'argv':list(map(str,args)),'cwd':str(cwd),'pid':p.pid,'start':start,'end':now(),'exit':p.returncode,'timeout':timed,'process_exited':p.poll()is not None,'stdout_sha256':sha(out/'stdout.txt'),'stderr_sha256':sha(out/'stderr.txt')}
    save(out/'record.json',r);R['commands'].append(r);save(D/'receipt.json',R)
    assert not timed,label
    return p.returncode,a.decode('utf8','replace'),b.decode('utf8','replace')

def tb():
    # A new testbench logs both sides of every sampled edge through public ports.
    text='''`timescale 1ns/1ps
module independent_tb;
parameter COUNT_W=4,WITNESS_W=8,TAG_W=8;
localparam CW=(COUNT_W<2)?2:((COUNT_W>32)?32:COUNT_W);
localparam WW=(WITNESS_W<2)?2:((WITNESS_W>64)?64:WITNESS_W);
localparam TW=(TAG_W<1)?1:((TAG_W>64)?64:TAG_W);
reg clk=0,rst=1,stop=0,cfg_valid=0,out_ready=0,loopback=0;
reg [CW-1:0] cfg_period=0,cfg_high_yaw=0,cfg_high_pitch=0,cfg_high_speed=0;
reg [TW-1:0] cfg_tag=0;
reg [2:0] drive_levels=0;
wire [2:0] sample_levels,pwm;
assign sample_levels=loopback?pwm:drive_levels;
wire cfg_ready,accepted,rejected,applied,frame_start,running,pending;
wire [CW-1:0] active_period,active_high_yaw,active_high_pitch,active_high_speed;
wire [TW-1:0] active_tag;
wire window_active,window_started,capture_armed,out_valid;
wire [CW-1:0] out_period,out_high0,out_high1,out_high2;
wire [WW-1:0] out_start,out_end;
wire [TW-1:0] out_tag;
wire [CW-1:0] expected_period,expected_high0,expected_high1,expected_high2;
wire [TW-1:0] expected_tag;
wire [3:0] raw_fault_events;
wire failure_event;wire [2:0] failure_code;
deepeye_pwm_applied_capture #(.COUNT_W(COUNT_W),.WITNESS_W(WITNESS_W),.TAG_W(TAG_W)) dut(.*);
always #5 clk=~clk;
integer fd,lg,i,n,sid,got,rows,k; reg [63:0] x[0:11];
string vec,tracefile;
task emit(input string kind);
begin
 $fwrite(lg,"%s %0d %0d",kind,i,sid);
 EMIT
 $fwrite(lg,"\\n");
end
endtask
initial begin
 if(!$value$plusargs("VEC=%s",vec)||!$value$plusargs("LOG=%s",tracefile))$fatal(1,"MISSING_FILES");
 fd=$fopen(vec,"r");lg=$fopen(tracefile,"w");if(!fd||!lg)$fatal(1,"OPEN_FAILED");
 got=$fscanf(fd,"%d\\n",rows);if(got!=1||rows<1)$fatal(1,"BAD_HEADER");
 for(i=0;i<rows;i=i+1)begin
  @(negedge clk);
  got=$fscanf(fd,"SCAN\\n",SCANARGS);if(got!=12)$fatal(1,"BAD_VECTOR");
  sid=x[0];rst=x[1];stop=x[2];cfg_valid=x[3];cfg_period=x[4];cfg_high_yaw=x[5];cfg_high_pitch=x[6];cfg_high_speed=x[7];cfg_tag=x[8];drive_levels=x[9];loopback=x[10];out_ready=x[11];
  #1;emit("PRE");@(posedge clk);#1;emit("POST");
 end
 $fclose(fd);$fclose(lg);$display("INDEPENDENT_TRACE_DONE edges=%0d",rows);$finish;
end
endmodule
'''
    text=text.replace('EMIT','\n '.join('$fwrite(lg," %h",'+s+');' for s in INPUT+['sample_levels']+FIELDS))
    text=text.replace('SCANARGS',','.join('x[%d]'%i for i in range(12))).replace('SCAN',' '.join(['%h']*12))
    return text

def vectors(c,w,t):
    rows=[];scenarios=[];cm=(1<<c)-1;tag=(1<<t)-1;p=2 if w==2 else min(cm,5);hs=(1,p-1,max(1,p//2))
    def scenario(name,require=None):
        scenarios.append({'id':len(scenarios),'name':name,'require':require or {}})
    def step(rst=0,stop=0,valid=0,period=0,h=(0,0,0),tg=0,levels=0,loop=0,ready=1):rows.append([scenarios[-1]['id'],rst,stop,valid,period,*h,tg,levels,loop,ready])
    def hold(n,**kw):
        for _ in range(n):step(**kw)
    def begin(pp=p,hh=hs,tg=tag,levels=0,loop=0):
        hold(2,rst=1,levels=levels,loop=loop);step(valid=1,period=pp,h=hh,tg=tg,levels=levels,loop=loop);hold(2,levels=levels,loop=loop)
    def wave(pp=p,hh=hs,n=None,ready=1):
        for k in range(n or (3*pp+2)):step(levels=sum((k%pp<h)<<lane for lane,h in enumerate(hh)),ready=ready)
    scenario('independent_literal_positive',{'min_handshakes':1});begin(2,(1,1,1));wave(2,(1,1,1),n=5 if w==2 else 12)
    scenario('registered_pwm_loopback',{} if w==2 else {'min_handshakes':1});begin(loop=1);hold(4*p+5,loop=1)
    for pp,hh in [(1,(0,1,1)),(p,(0,1,1)),(p,(p,1,1)),(p,(1,p,1)),(p,(1,1,p))]:
        scenario('legal_unmeasurable_'+str(hh),{'code':6,'max_handshakes':0});begin(pp,hh);wave(pp,hh,n=2*pp+4)
    if w>2:
        for oldphase in range(p):
            for mode in ['same','changed','illegal']:
                scenario('transfer_phase_%d_%s'%(oldphase,mode));begin();wave(n=oldphase+1,ready=0)
                np,nh=(p,hs) if mode=='same' else((2,(1,1,1))if mode=='changed'else(0,(0,0,0)))
                step(valid=1,period=np,h=nh,tg=tag,levels=7,ready=1);wave(2,(1,1,1),n=4*p+12)
        for action in ['rst','stop','same','illegal']:
            scenario('old_full_slot_boundary_'+action,{'min_old_slots':1});begin();wave(n=p+1,ready=0)
            kw={'rst':1}if action=='rst'else({'stop':1}if action=='stop'else {'valid':1,'period':p if action=='same'else 0,'h':hs,'tg':tag})
            step(levels=0,ready=1,**kw);wave(n=3*p+6)
        for ready in [0,1]:
            scenario('held_valid_pending_'+str(ready));begin()
            for k in range(35):step(valid=1,period=2+(k%2),h=(1,1,1),tg=tag if k%2 else 0,levels=7 if k%2 else 0,ready=ready)
            hold(30)
        for code,kind in [(1,'mismatch'),(2,'incoherent'),(3,'period'),(4,'witness'),(5,'overrun')]:
            if (code==3 and c>8)or(code==4 and w>8):continue
            scenario('failure_'+kind,{'code':code});begin()
            if code==1:wave(2,(1,1,1),n=12)
            elif code==2:
                for level in [1,3,7,0,7]:step(levels=level)
            elif code==3:step(levels=7);hold(cm+2,levels=0)
            elif code==4:hold((1<<w)+2,levels=0)
            else:wave(n=3*p+2,ready=0)
            # Closed failed windows cannot self-recover even with matching waves.
            wave(n=3*p+5)
            step(valid=1,period=p,h=hs,tg=tag);hold(p+3);wave(n=3*p+5)
        for cut in range(2*p+2):
            for action in ['rst','stop']:
                scenario('abort_%s_%d'%(action,cut));begin();wave(n=cut+1,ready=0);step(**{action:1});wave(n=3*p+2)
        for levels in [0,7]:
            scenario('constant_'+str(levels),{'max_handshakes':0});begin(levels=levels);hold(2*p+6,levels=levels)
        scenario('bounded_max_command',{'max_handshakes':0});begin(cm,(1,cm-1,cm//2));hold(20)
    else:
        scenario('minimum_witness_exhaustion',{'code':4});begin();hold(8)
    return rows,scenarios

def check(trace,rows,scenarios,c,w,t):
    pairs=[]
    for line in trace.read_text(encoding='utf8').splitlines():
        a=line.split();assert a[0]in ['PRE','POST'];vals=[int(x,16)for x in a[3:]];assert len(vals)==len(INPUT)+1+len(FIELDS)
        pairs.append((a[0],int(a[1]),int(a[2]),dict(zip(INPUT+['sample_levels']+FIELDS,vals))))
    assert len(pairs)==2*len(rows)
    stats={s['id']:{'name':s['name'],'edges':0,'handshakes':0,'valid_observations':0,'starts':0,'codes':[],'old_slots':0}for s in scenarios}
    errors=[];history={};origin=None;context=None;bound=False;last_slot=None;accepted_queue=[]
    def demand(ok,label,n):
        if not ok:errors.append({'edge':n,'label':label})
    def tupleof(q,prefix):
        keys=['active_period','active_high_yaw','active_high_pitch','active_high_speed','active_tag']if prefix=='active'else(['expected_period','expected_high0','expected_high1','expected_high2','expected_tag']if prefix=='expected'else['out_period','out_high0','out_high1','out_high2','out_tag'])
        return tuple(q[k]for k in keys)
    def record(q,n,post):
        if not q['out_valid']:return
        st=stats[rows[n][0]];st['valid_observations']+=1
        demand(bound and context is not None,'valid_requires_live_application',n)
        demand(tupleof(q,'out')==context,'measured_tuple_tag_matches_applied_context',n)
        demand(q['capture_armed'] and not q['raw_fault_events'],'valid_masked_on_capture_fault',n)
        if origin is None:return
        start=origin+q['out_start'];end=origin+q['out_end']
        demand(origin<start<end<=(n if post else n-1),'full_interval_after_application_baseline',n)
        demand(q['out_period']==end-start,'absolute_period',n)
        if start-1 not in history or end not in history:
            demand(False,'witness_history_present',n);return
        demand((~history[start-1]&history[start]&7)==7 and (~history[end-1]&history[end]&7)==7,'both_endpoints_common_rise',n)
        for lane in range(3):
            falls=[i for i in range(start+1,end)if history[i-1]&(1<<lane)and not history[i]&(1<<lane)]
            demand(bool(falls) and falls[0]-start==q['out_high'+str(lane)],'first_fall_lane_'+str(lane),n)
        demand(all((~history[i-1]&history[i]&7)==0 for i in range(start+1,end)),'no_spliced_intermediate_rise',n)
    for n,row in enumerate(rows):
        kind,idx,sid,pre=pairs[2*n];pk,pi,ps,post=pairs[2*n+1];assert(kind,idx,sid,pk,pi,ps)==('PRE',n,row[0],'POST',n,row[0])
        s=stats[sid];s['edges']+=1
        demand([pre[k]for k in INPUT]==row[1:],'stimulus_matches_file',n)
        transfer=bool(pre['cfg_valid']and pre['cfg_ready']);halt=bool(pre['rst']or pre['stop']or transfer or pre['pending']or not pre['running'])
        payload=tuple(pre[k]for k in ['cfg_period','cfg_high_yaw','cfg_high_pitch','cfg_high_speed','cfg_tag'])
        legal=payload[0]>0 and all(h<=payload[0]for h in payload[1:4])
        demand(post['accepted']==int(transfer and legal),'accepted_public_transfer_tuple',n)
        demand(post['rejected']==int(transfer and not legal),'rejected_public_transfer_tuple',n)
        if pre['rst']or pre['stop']:accepted_queue=[]
        else:
            if post['applied']:
                demand(bool(accepted_queue) and tupleof(post,'active')==accepted_queue[0],'actual_application_matches_prior_accepted_command',n)
                if accepted_queue:accepted_queue.pop(0)
            if post['accepted']:accepted_queue.append(payload)
        active=tupleof(pre,'active');eligible=active[0]>=2 and all(0<h<active[0]for h in active[1:4])
        expected_start=bool(not halt and pre['applied']and eligible)
        if pre['out_period']and bound and (halt or pre['applied']):s['old_slots']+=1
        if halt or pre['applied']:demand(not pre['out_valid'],'preedge_control_suppresses_old_handshake',n)
        record(pre,n,False)
        if pre['out_valid']and pre['out_ready']:s['handshakes']+=1
        if halt:bound=False;context=None;origin=None;history={}
        elif pre['applied']:
            bound=eligible;context=active if eligible else None;origin=n if eligible else None;history={}
        elif post['failure_event']:bound=False;context=None
        history[n]=pre['sample_levels']
        demand(post['window_started']==int(expected_start),'start_only_observed_actual_applied',n)
        demand(post['window_active']==int(bound),'registered_binding_state',n)
        demand(tupleof(post,'expected')==(context if bound else(0,0,0,0,0)),'comparison_context_latched_actual_not_requested',n)
        if expected_start:s['starts']+=1;demand(post['capture_armed']==1,'fresh_arm_on_application',n)
        if post['failure_event']:s['codes'].append(post['failure_code'])
        if pre['rst']or pre['stop']:demand(not post['failure_event'] and post['failure_code']==0,'abort_priority_no_failure',n)
        record(post,n,True)
    for s in scenarios:
        st=stats[s['id']];req=s['require']
        demand(st['handshakes']>=req.get('min_handshakes',0),'scenario_min_handshake_'+s['name'],s['id'])
        demand(st['handshakes']<=req.get('max_handshakes',10**9),'scenario_max_handshake_'+s['name'],s['id'])
        demand(st['old_slots']>=req.get('min_old_slots',0),'scenario_old_slot_'+s['name'],s['id'])
        if 'code'in req:demand(req['code']in st['codes'],'required_failure_code_'+s['name'],s['id'])
    return {'edges':len(rows),'errors':errors[:100],'error_count':len(errors),'scenarios':list(stats.values()),'handshakes':sum(s['handshakes']for s in stats.values()),'valid_observations':sum(s['valid_observations']for s in stats.values())}

def main():
    D.mkdir(exist_ok=False)
    (D/'temp').mkdir(exist_ok=True);(D/'snapshot').mkdir();(D/'snapshot/independent_tb.sv').write_text(tb(),encoding='ascii')
    for name in ['deepeye_atomic_pwm.sv','deepeye_pwm_coherent_capture.sv','deepeye_pwm_applied_capture.sv']:shutil.copyfile(SRC/'fpga/control3d'/name,D/'snapshot'/name)
    save(D/'freeze.json',{'at':now(),'chronology':'after source review, before all fresh compile','files':{p.name:sha(p)for p in (D/'snapshot').iterdir()},'checker_sha256':sha(Path(__file__)),'imports_B_model':False})
    code,text,err=command('subst-before',['subst'],D);used={line[:2].upper()for line in text.splitlines()};drive=next(x+':'for x in 'RSTUVWXYZQ'if x+':'not in used and not Path(x+':/').exists())
    R['private_mapping']=drive;save(D/'receipt.json',R)
    command('subst-create',['subst',drive,str(D)],D)
    a=drive+'/'
    try:
        command('vlog-version',[TOOL/'vlog.exe','-version'],a);command('vsim-version',[TOOL/'vsim.exe','-version'],a)
        (D/'build').mkdir();(D/'build/run.do').write_text('onerror {quit -code 1}\nrun -all\nquit -code 0\n',encoding='ascii')
        code,tx,er=command('vlib',[TOOL/'vlib.exe','lib'],a+'build');assert code==0
        args=[TOOL/'vlog.exe','-sv','-work','lib']+[a+'snapshot/'+s for s in ['deepeye_atomic_pwm.sv','deepeye_pwm_coherent_capture.sv','deepeye_pwm_applied_capture.sv','independent_tb.sv']]
        code,tx,er=command('vlog',args,a+'build');assert code==0 and 'Errors: 0'in tx
        for c,w,t in [(4,8,8),(2,2,1),(32,64,64)]:
            name=f'positive-{c}-{w}-{t}';rows,scenarios=vectors(c,w,t);v=D/(name+'.vec');v.write_text(str(len(rows))+'\n'+'\n'.join(' '.join(format(x,'x')for x in row)for row in rows)+'\n',encoding='ascii');save(D/(name+'.scenarios.json'),scenarios)
            args=[TOOL/'vsim.exe','-batch','-syncio','lib.independent_tb','-l',a+name+'.transcript','-wlf',a+name+'.wlf','-do','run.do',f'-gCOUNT_W={c}',f'-gWITNESS_W={w}',f'-gTAG_W={t}','+VEC='+a+v.name,'+LOG='+a+name+'.trace']
            code,tx,er=command(name,args,a+'build');assert code==0 and 'INDEPENDENT_TRACE_DONE edges='+str(len(rows))in tx and not re.search(r'\*\*\s+(?:Fatal|Error):',tx+er)
            result=check(D/(name+'.trace'),rows,scenarios,c,w,t);result.update(name=name,config=[c,w,t],trace_sha256=sha(D/(name+'.trace')));save(D/(name+'.check.json'),result);R['runs'].append(result);save(D/'receipt.json',R)
        # Real exact DUT guards, distinguished from compile/tool failures.
        for c,w,t in [(0,64,32),(-1,64,32),(33,64,32),(32,0,32),(32,-2,32),(32,65,32),(32,64,0),(32,64,-1),(32,64,65)]:
            name=f'guard-{c}-{w}-{t}';args=[TOOL/'vsim.exe','-batch','-syncio','lib.independent_tb','-l',a+name+'.transcript','-wlf',a+name+'.wlf','-do','run.do',f'-gCOUNT_W={c}',f'-gWITNESS_W={w}',f'-gTAG_W={t}','+VEC='+a+'positive-4-8-8.vec','+LOG='+a+name+'.trace']
            code,tx,er=command(name,args,a+'build');diag=f'DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM COUNT_W={c} WITNESS_W={w} TAG_W={t} SAFE_COUNT_W={min(32,max(2,c))} SAFE_WITNESS_W={min(64,max(2,w))} SAFE_TAG_W={min(64,max(1,t))}'
            passed=code in [0,1]and diag in tx and '** Fatal: DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM unsupported widths'in tx and 'Time: 0 ps'in tx and 'INDEPENDENT_TRACE_DONE'not in tx
            R['guards'].append({'name':name,'exit':code,'exact_guard_diagnostic':passed,'diagnostic':diag,'actual_diagnostics':re.findall(r'\*\*\s+(?:Error|Fatal):[^\n]*',tx+er)});save(D/'receipt.json',R)
        R['status']='fresh_runs_complete'
    finally:
        code,tx,er=command('subst-remove',['subst',drive,'/d'],D);assert code==0
        code,tx,er=command('subst-after',['subst'],D);R['mapping_removed']=not any(line.startswith(drive+'\\')for line in tx.splitlines());save(D/'receipt.json',R)

if __name__=='__main__':
    try:main()
    except Exception:R['exception']=traceback.format_exc();save(D/'receipt.json',R);raise
    print(json.dumps({'runs':[{k:r[k]for k in ['name','edges','error_count','handshakes','valid_observations']}for r in R['runs']],'guards':R['guards'],'mapping_removed':R['mapping_removed']}))

import hashlib, importlib.util, json, re, sys
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parents[2]
BASE=D.parent/'b-pr30-operations14-15-20261020'/'15'
SRC=BASE/'source'
B=SRC/'competition/deepeye'
EV=B/'evidence/control3d/pwm-applied-capture-20261020-15'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def audit():
    meta=json.loads((BASE/'artifact-integrity.json').read_bytes())
    bad=[]
    for p,r in meta['files'].items():
        f=SRC/p
        if not f.is_file() or f.stat().st_size!=r['bytes'] or sha(f)!=r['sha256']:bad.append(p)
    h=json.loads((ROOT/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    canonical=hashlib.sha256(json.dumps(h['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    assert canonical=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    pins={p.name:sha(p) for p in (B/'fpga/control3d').glob('*.sv')}
    assert pins['deepeye_atomic_pwm.sv']=='9dc8ecf96e59a2ae8467bda64572f62eb602d52db535733f236f64ff97c43428'
    assert pins['deepeye_pwm_coherent_capture.sv']=='4baddfc31248c49000c00ac74bc2319cef6c9016c7df3f1822030c69cd82f456'
    result={'selected':len(meta['files']),'bad':bad,'head':meta['head'],'source':meta['code'],'request_hash':meta['request_hash'],'manifest_sha256':sha(SRC/'handoffs/b/B-DEEPEYE-PWM-APPLIED-CAPTURE-20261020-15/manifest.json'),'requirements_canonical_sha256':canonical,'rtl_pins':pins}
    assert not bad and result['selected']==1795 and result['manifest_sha256']==meta['manifest_sha256']
    for k in ['b-op14-independent-20261020','b-op12-review-completion-20261020']:
        f=D.parent/k/'final-result.txt';result.setdefault('dependency_evidence',[]).append({'path':str(f),'sha256':sha(f)})
    save(D/'source-audit.json',result)
    rdir=EV/'author/run-main-repaired-20261020-15-a'
    s=json.loads((rdir/'RUN_SUMMARY.json').read_bytes())
    commands=[]
    for cmd in s['commands']:
        row={'name':cmd['name'],'exit':cmd['exit'],'logs':{}}
        for stream in ['stdout','stderr']:
            f=rdir/'logs'/Path(cmd[stream].replace('\\','/')).name
            row['logs'][stream]={'sha256':sha(f),'matches':sha(f)==cmd[stream+'_sha256']}
        commands.append(row)
    positives=[]
    for e in s['positive']:
        text=(rdir/'logs'/Path(e['stdout'].replace('\\','/')).name).read_text(encoding='utf8')
        err=(rdir/'logs'/Path(e['stderr'].replace('\\','/')).name).read_text(encoding='utf8')
        positives.append({'id':e['id'],'exit':e['exit'],'stats':e['stats'],'pass_lines':re.findall(r'^# TB_PASS\s*$',text,re.M),'unexpected_diagnostics':re.findall(r'\*\*\s+(?:Error|Fatal):[^\n]*',text+'\n'+err)})
    mutants=[]
    for m in s['mutants']:
        for r in m['runs']:
            text=(rdir/'logs'/Path(r['stdout'].replace('\\','/')).name).read_text(encoding='utf8')
            mutants.append({'id':m['id'],'group':r['group'],'expect':r['expect'],'compiled':m['compile']['compiled'],'exit':r['exit'],'stats':r['stats'],'labels':r['mismatch_labels'],'diagnostics':re.findall(r'\*\*\s+(?:Error|Fatal):[^\n]*',text),'pass_lines':re.findall(r'^# TB_PASS\s*$',text,re.M)})
    guards=[]
    for e in s['invalid_parameters']:
        text=(rdir/'logs'/Path(e['record']['stdout'].replace('\\','/')).name).read_text(encoding='utf8')
        guards.append({'id':e['id'],'exit':e['record']['exit'],'diagnostic':e['diagnostic'],'own_fatal':e['own_fatal'],'diagnostics':re.findall(r'\*\*\s+(?:Error|Fatal):[^\n]*',text)})
    save(D/'repaired-run-audit.json',{'summary_sha256':sha(rdir/'RUN_SUMMARY.json'),'claimed_result':s['result'],'command_count':len(commands),'commands':commands,'positive_totals':s['positive_totals'],'positives':positives,'mutants':mutants,'guards':guards})
    return result

STATS='TB_STATS groups=1 cases=1 samples=1 assertions=1 records=0 raw_faults=0 failure_events=0 window_starts=0 handshakes=0 mismatches=0\n'
DIAG='DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM COUNT_W=0 WITNESS_W=64 TAG_W=32 SAFE_COUNT_W=2 SAFE_WITNESS_W=64 SAFE_TAG_W=32\n'
FATAL='** Fatal: DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM unsupported widths\n'
def qualify(label,path):
    out=D/('qualification-'+label);out.mkdir(exist_ok=False)
    spec=importlib.util.spec_from_file_location('runner_'+label,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    cases=[]
    def positive(name,text,code,expected,stderr=''):
        f=out/(name+'.stdout.txt');e=out/(name+'.stderr.txt');f.write_text(text,encoding='utf8');e.write_text(stderr,encoding='utf8')
        parsed=m.parse_tb_output(f,e);parsed.update(transcript=None,transcript_sha256=None,wlf=None,wlf_sha256=None)
        got=m.positive_entry({'id':name,'group':0,'count_w':4,'witness_w':8,'tag_w':8,'loopback':0},{'record':{'exit':code,'stdout':str(f),'stderr':str(e)},'parsed':parsed})['passed']
        cases.append({'name':name,'exit':code,'expected':expected,'observed':got,'matches':got==expected})
    for n,c in enumerate([0,1,2,'timeout','exception']):positive('terminal-'+str(n),'TB_PASS\n'+STATS,c,type(c)is int and c==0)
    positive('error-after-pass','TB_PASS\n'+STATS+'** Error: synthetic tool failure\n',0,False)
    for c in [0,1,2,'timeout','exception']:
        for fatal in [False,True]:
            name='guard-'+str(c)+'-'+str(fatal);(out/(name+'.stdout.txt')).write_text(DIAG+(FATAL if fatal else ''),encoding='utf8');(out/(name+'.stderr.txt')).write_text('',encoding='utf8')
            m.run_command=lambda *a,**kw:{'exit':c,'synthetic':True}
            got=m.run_invalid(out,out,[],{'vsim':'NOT_EXECUTED'},{'id':name,'count_w':0,'witness_w':64,'tag_w':32},1)['passed'];expected=type(c)is int and c in [0,1] and fatal
            cases.append({'name':name,'exit':c,'expected':expected,'observed':got,'matches':got==expected})
    baseline=len(cases)
    positive('substring-pass','NOT_TB_PASS_MARKER\n'+STATS,0,False)
    positive('duplicate-stats','TB_PASS\n'+STATS+STATS.replace('mismatches=0','mismatches=1'),0,False)
    positive('fatal-stderr','TB_PASS\n'+STATS,0,False,'** Fatal: unrelated actual failure\n')
    save(out/'result.json',{'source':str(path),'source_sha256':sha(path),'synthetic_only':True,'baseline_cases':cases[:baseline],'baseline_mismatches':sum(not x['matches'] for x in cases[:baseline]),'additional_cases':cases[baseline:]})
    return {'source_sha256':sha(path),'baseline_mismatches':sum(not x['matches'] for x in cases[:baseline]),'additional':cases[baseline:]}

if __name__=='__main__':
    a=audit()
    q={label:qualify(label,p) for label,p in [('original',EV/'main/runner-repair/original_runner.py'),('repaired',B/'tools/control3d/run_pwm_applied_capture.py')]}
    save(D/'qualification-summary.json',q)
    print(json.dumps({'source_bad':a['bad'],'selected':a['selected'],'qualification':q}))

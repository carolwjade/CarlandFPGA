import hashlib,importlib.util,json,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;S=D/'snapshot/saved';E=D/'snapshot/repo/competition/deepeye/evidence/control3d/pwm-runner-qualification-20261020-16';events=[]
def audit(event,args):
 if event in {'subprocess.Popen','os.system','os.startfile','socket.connect','socket.bind'}:events.append(event);raise AssertionError('prohibited effect '+event)
sys.addaudithook(audit)
def load(name,file):
 sp=importlib.util.spec_from_file_location(name,D/'snapshot'/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('reviewed_runner','runner.py');old=load('old_runner','previous-runner.py')
def sha(b):return hashlib.sha256(b).hexdigest()
summary=json.loads((S/'RUN_SUMMARY.json').read_bytes());records={r['name']:r for r in summary['commands']};assert len(records)==47
def paths(r):return [S/pathlib.PureWindowsPath(r[t]).name for t in ('stdout','stderr')]
for r in records.values():
 for t,p in zip(('stdout','stderr'),paths(r)):assert sha(p.read_bytes())==r[t+'_sha256']
def result(name):
 r=records[name];p=m.parse_tb_output(*paths(r));p.update(transcript=None,transcript_sha256=None,wlf=None,wlf_sha256=None);return {'record':r,'parsed':p}
obs=[]
for sp in m.POSITIVE_RUNS:
 r=result(sp['id']);obs.append(dict(name=sp['id'],kind='positive',accepted=m.positive_entry(sp,r)['passed'],stats=r['parsed']['stats'],protocol_errors=r['parsed']['protocol_errors']))
for mutant in m.MUTANT_SPECS:
 for sp in mutant['runs']:
  name=mutant['id']+'-g'+str(sp['group']);r=result(name);obs.append(dict(name=name,kind=sp['expect'],accepted=m.mutant_result(sp,r),stats=r['parsed']['stats'],protocol_errors=r['parsed']['protocol_errors']))
for sp in m.INVALID_RUNS:
 folder=D/'saved-guard'/sp['id'];folder.mkdir(parents=True);r=records[sp['id']]
 for t,p in zip(('stdout','stderr'),paths(r)):(folder/(sp['id']+'.'+t+'.txt')).write_bytes(p.read_bytes())
 m.run_command=lambda *a,r=r,**kw:r;got=m.run_invalid(folder,folder,[],{'vsim':'NEVER_EXECUTE'},sp,1);obs.append(dict(name=sp['id'],kind='guard',accepted=got['passed']))
saved=dict(origin_summary_sha256=sha((S/'RUN_SUMMARY.json').read_bytes()),saved_commands=47,saved_stdout_stderr_verified=94,new_simulator_commands=0,observations=obs,failed_count=sum(not r['accepted'] for r in obs),positive_samples=sum(r['stats']['samples'] for r in obs if r['kind']=='positive'));assert saved==json.loads((E/'check-02/SAVED_RUN_RECLASSIFIED.json').read_bytes());(D/'saved-reclassification.json').write_text(json.dumps(saved,indent=2),encoding='utf-8')
neg=[];sp=dict(id='original-A',group=0,loopback=0,count_w=4,witness_w=8,tag_w=8)
for name in ('substring-pass','duplicate-stats'):
 p=E/'a-original/op15/review/qualification-repaired';out=p/(name+'.stdout.txt');err=p/(name+'.stderr.txt');a=[]
 for module in (old,m):
  parsed=module.parse_tb_output(out,err);parsed.update(transcript=None,transcript_sha256=None,wlf=None,wlf_sha256=None);a.append(module.positive_entry(sp,dict(record={'exit':0},parsed=parsed))['passed'])
 assert a==[True,False];neg.append(dict(name=name,stdout_sha256=sha(out.read_bytes()),stderr_sha256=sha(err.read_bytes()),old_accepted=a[0],new_accepted=a[1],new_protocol_errors=parsed['protocol_errors']))
(D/'original-A-reclassification.json').write_text(json.dumps(neg,indent=2),encoding='utf-8')
cases=[];F=D/'counterexamples';F.mkdir();stats='TB_STATS groups=1 cases=1 samples=29 assertions=206 records=2 raw_faults=0 failure_events=0 window_starts=1 handshakes=1 mismatches=0\n';positive=stats+'TB_PASS group=0 loopback=0\n';diagnostic='DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM COUNT_W=0 WITNESS_W=64 TAG_W=32 SAFE_COUNT_W=2 SAFE_WITNESS_W=64 SAFE_TAG_W=32\n';fatal='** Fatal: DEEPEYE_APPLIED_CAPTURE_INVALID_PARAM unsupported widths\n'
def counter(name,text,kind,expected):
 folder=F/name;folder.mkdir();out=folder/('invalid-count-zero.stdout.txt' if kind=='guard' else 'case.stdout.txt');err=out.with_name(out.name.replace('stdout','stderr'));out.write_bytes(text.encode());err.write_bytes(b'')
 if kind=='guard':
  spec=m.INVALID_RUNS[0];m.run_command=lambda *a,**kw:{'exit':1};got=m.run_invalid(folder,folder,[],{'vsim':'NEVER_EXECUTE'},spec,1);accepted=got['passed']
 else:
  got=m.parse_tb_output(out,err);accepted=m.positive_result(sp,dict(record={'exit':0},parsed=got))
 cases.append(dict(name=name,expected_accepted=expected,observed_accepted=accepted,expectation_met=accepted==expected,kind=kind,stdout_path=str(out.relative_to(D)),stdout_sha256=sha(out.read_bytes()),stderr_sha256=sha(err.read_bytes()),result=got))
counter('positive-control',positive,'positive',True)
counter('code7-in-ordinary-group',m.CODE7_LINE+'\n'+positive,'positive',False)
counter('guard-control',diagnostic+fatal,'guard',True)
counter('guard-extra-unrelated-fatal',diagnostic+fatal+'** Fatal: unrelated simulator failure\n','guard',False)
counter('guard-prefixed-records','NOT_'+diagnostic+'NOT_'+fatal,'guard',False)
assert not events
(D/'counterexamples.json').write_text(json.dumps({'cases':cases,'process_network_attempts':events,'new_simulator_commands':0},indent=2),encoding='utf-8');print(json.dumps(dict(saved_scenarios=len(obs),saved_accepted=sum(r['accepted'] for r in obs),saved_positive_samples=saved['positive_samples'],original_A_rejected=2,counterexamples=[{k:v for k,v in c.items() if k in ['name','expected_accepted','observed_accepted','expectation_met']} for c in cases],prohibited_attempts=events)))

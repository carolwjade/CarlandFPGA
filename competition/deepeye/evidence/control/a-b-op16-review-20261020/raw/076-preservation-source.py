import hashlib,importlib.util,json,pathlib,subprocess
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[2];E=D/'snapshot/repo/competition/deepeye/evidence/control3d/pwm-runner-qualification-20261020-16';G='C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe';rows=[]
for p in sorted((E/'prior-b').rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(E/'prior-b').as_posix();path='competition/deepeye/evidence/control3d/pwm-applied-capture-20261020-15/main/'+rel;cmd=[G,'-C',str(ROOT),'cat-file','blob','df82af1bc91d01aeb9adee19f48c0890dfc1ac5b:'+path];q=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);b,err=q.communicate(timeout=10);assert q.returncode==0 and b==p.read_bytes();rows.append(dict(path=path,argv=cmd,pid=q.pid,exit=q.returncode,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert len(rows)==102
sp=importlib.util.spec_from_file_location('baseline_runner',D/'snapshot/previous-runner.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
cases=json.loads((D/'counterexamples.json').read_bytes())['cases'];baseline=[]
for c in cases:
 out=D/c['stdout_path'];err=out.with_name(out.name.replace('stdout','stderr'))
 if c['kind']=='guard':
  old.run_command=lambda *a,**kw:{'exit':1};got=old.run_invalid(out.parent,out.parent,[],{'vsim':'NEVER_EXECUTE'},old.INVALID_RUNS[0],1)['passed']
 else:
  parsed=old.parse_tb_output(out,err);got=bool(old.completed_process({'exit':0}) and parsed['passed'] and not parsed['failed'] and parsed['stats'] is not None and parsed['stats']['mismatches']==0)
 baseline.append(dict(name=c['name'],baseline_accepted=got,current_accepted=c['observed_accepted'],preexisting=got==c['observed_accepted']))
result=dict(prior_B_files_byte_identical=102,files=rows,counterexample_baseline_comparison=baseline);(D/'preservation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(dict(prior_B_files_byte_identical=102,counterexample_baseline_comparison=baseline)))

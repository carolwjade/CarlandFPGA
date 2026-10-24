import datetime,hashlib,io,json,pathlib,re,subprocess,zipfile
D=pathlib.Path(__file__).resolve().parent;OUT=D.parent;ROOT=D.parents[2];F=OUT/'a-b15-ooc-synthesis-fix2-20261020'
def check(c,s):
 if not c:raise AssertionError(s)
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pinfile=OUT/'background-synthesis-main-20261020/synthesis-public-inputs.json';pins=load(pinfile)
paths=[pinfile,pathlib.Path(__file__),D/'assignment.md']+[OUT/x['path'] for x in pins['artifacts']]
paths.extend(ROOT/p for p in ['docs/competition/deepeye-2026/immutable_scope.json','.planning/deepeye-desktop-handoff-20261015/transfer.json','.agents/skills/pynq-z2-single-node/SKILL.md','.agents/skills/pynq-z2-single-node/skill-role.json','.agents/skills/fpga-multi-node/SKILL.md','.agents/skills/fpga-multi-node/skill-role.json','.agents/skills/fpga-multi-node/references/protocol.md'])
before={str(p):sha(p) for p in paths};(D/'static-inputs-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
start=datetime.datetime.now(datetime.timezone.utc).isoformat();check(len(pins['artifacts'])==47,'47 pinned public inputs')
for row in pins['artifacts']:p=OUT/row['path'];check(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'frozen input '+row['path'])
scope=load(ROOT/'docs/competition/deepeye-2026/immutable_scope.json');h=hashlib.sha256(json.dumps(scope['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();check(h=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','H01-H15')
tr=load(ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json');check(tr['status']=='active' and tr['director_generation']==2,'director')
git=pathlib.Path('C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe');commit='df82af1bc91d01aeb9adee19f48c0890dfc1ac5b';inputs=load(F/'inputs.json');git_receipts=[]
for s in inputs['sources']:
 command=[str(git),'-C',str(ROOT),'cat-file','blob',commit+':'+s['path']];ts=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(command,capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS);check(p.returncode==0,'local Git source blob');digest=hashlib.sha256(p.stdout).hexdigest();check(digest==s['sha256'] and p.stdout==(F/s['snapshot']).read_bytes(),'exact source blob bytes');obj=hashlib.sha1(b'blob '+str(len(p.stdout)).encode()+b'\0'+p.stdout).hexdigest();check(obj==s['blob'],'Git object identity');git_receipts.append({'command':command,'started_utc':ts,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':digest,'stderr':p.stderr.decode('utf-8'),'git_blob':obj})
runs=[]
for name in ['a-b15-ooc-synthesis-20261020','a-b15-ooc-synthesis-fix1-20261020','a-b15-ooc-synthesis-fix2-20261020']:
 base=OUT/name;cfg=load(base/'inputs.json');r=load(base/'run-result.json');started=load(base/'run-started.json');log=(base/'vivado.log').read_text(encoding='utf-8',errors='replace');out=(base/'stdout.txt').read_text(encoding='utf-8',errors='replace');tcl=(base/'synthesize.tcl').read_text();runner=(base/'run_hidden.py').read_text()
 for s in cfg['sources']:check(sha(base/s['snapshot'])==s['sha256']==next(x for x in inputs['sources'] if x['path']==s['path'])['sha256'],'identical RTL across runs')
 for file,digest in started['input_hashes'].items():check(sha(base/file)==digest,'actual run source pin '+name)
 check(cfg['part']=='xc7z020clg400-1' and cfg['top']=='deepeye_pwm_applied_capture' and cfg['parameters']=={'COUNT_W':32,'WITNESS_W':64,'TAG_W':32},'source target')
 check(r['source_inputs_unchanged'] and not r['timeout'] and r['peak_job_committed_memory_bytes']<4294967296,'actual resource/result')
 actual_warnings=re.findall(r'^(?:CRITICAL WARNING:|WARNING:).*$',log,re.M);check(actual_warnings==r['warning_lines'],'all synthesis-log warnings')
 check('synth_design completed successfully' in log,'native synthesis completed stage')
 check('set_param general.maxThreads 1' in tcl and 'suspended; assigned to private kill-on-close job before resume'==started['creation'],'thread and suspended-job binding')
 check(started['resource_limits']=={'threads':1,'job_memory_bytes':4294967296,'timeout_seconds':240,'priority':'below_normal'},'original resource ceilings')
 check('0x200 | 0x2000 | 0x20' in runner and 'limits.job_memory = 4 * GiB' in runner and 'si.show = 0' in runner and '0x08000000 | 0x4 | 0x400 | 0x4000' in runner,'native hidden/priority/memory implementation')
 exact=len(re.findall(r'^DEEPEYE_OOC_SYNTHESIS_PASS\r?$',out,re.M))==1;check(exact==r['exact_stdout_pass_marker'],'stdout exact marker')
 runs.append({'run':name,'batch_exit':r['exit_code'],'python_runner_exit_is_not_batch_acceptance':True,'synthesis_completed':True,'exact_pass_marker':exact,'duration_seconds':r['duration_seconds'],'peak_job_committed_memory_bytes':r['peak_job_committed_memory_bytes'],'warning_lines':actual_warnings})
check([r['batch_exit'] for r in runs]==[1,1,0],'original failure and success statuses')
check('get_property NAME [current_design]' in (OUT/runs[0]['run']/'synthesize.tcl').read_text(),'first failure identity check');check('Unexpected synthesized top' in (OUT/runs[0]['run']/'stdout.txt').read_text(),'preserved first failure')
check('Common 17-1292' in (OUT/runs[1]['run']/'stdout.txt').read_text(),'preserved exporter failure')
check('write_checkpoint -force artifacts/synthesized.dcp' in (F/'synthesize.tcl').read_text(),'normal child export correction')
# Independently derive logical port identities from RTL and exported netlist.
top='deepeye_pwm_applied_capture';rtl=(F/'sources'/f'{top}.sv').read_text();widths={'COUNT_AW':32,'WITNESS_AW':64,'TAG_AW':32};ports={}
for direction,span,name in re.findall(r'^\s*(input|output)\s+logic\s*(?:\[([^]]+)\])?\s+(\w+)\s*,?\s*$',rtl.split('\n);',1)[0],re.M):
 width=1 if not span else int(span.split(':')[0])+1 if span[0].isdigit() else widths[span.split('-')[0]];ports[name]={'direction':direction.upper(),'width':width}
check(ports,'RTL ports parsed');net=(F/'artifacts/synthesized.v').read_text();module=re.search(r'^module '+top+r'\b(.*?)^endmodule',net,re.M|re.S);check(module,'exported top module');netports={}
for direction,span,name in re.findall(r'^\s*(input|output)\s*(?:\[([^]]+)\])?\s+(\w+)\s*;',module[1],re.M):netports[name]={'direction':direction.upper(),'width':1 if not span else int(span.split(':')[0])+1}
check(ports==netports,'generated Verilog top ports and exact default widths');expected_bits={name if x['width']==1 else name+'['+str(i)+']':x['direction'] for name,x in ports.items() for i in range(x['width'])};check(len(expected_bits)==798,'798 bit-level ports')
(D/'expected-ports.json').write_text(json.dumps({'logical':ports,'bit_level':expected_bits},indent=2),encoding='utf-8')
with zipfile.ZipFile(F/'artifacts/synthesized.dcp') as z:
 check(z.testzip() is None,'complete DCP ZIP CRC');dcp={'entries':len(z.infolist()),'members':[{'name':x.filename,'compressed_bytes':x.compress_size,'bytes':x.file_size,'crc32':x.CRC} for x in z.infolist()],'sha256':sha(F/'artifacts/synthesized.dcp')}
util=(F/'utilization.rpt').read_text();check(re.search(r'\| deepeye_pwm_applied_capture\s+\|\s+\(top\)\s+\|\s+842\s+\|\s+842\s+\|\s+0\s+\|\s+0\s+\|\s+1117',util),'utilization 842 LUTs/1117 FFs');drc=(F/'synthesis_drc.rpt').read_text();check('ZPS7-1#1 Warning' in drc,'PS7 DRC retained')
after={str(p):sha(p) for p in paths};check(before==after,'all static inputs unchanged');(D/'static-inputs-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
result={'status':'static_synthesis_evidence_verified','started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pinned_artifacts':47,'git_commands':git_receipts,'source_commit':commit,'runs':runs,'logical_ports':len(ports),'bit_ports':len(expected_bits),'DCP':dcp,'utilization':{'LUT':842,'FF':1117,'RAMB36':0,'RAMB18':0,'DSP':0},'warning_qualification':'five removed procedural temporaries; OOC incomplete DRC connectivity; ZPS7-1 missing PS7; clocks=0/timing not validated','requirements_sha256':h,'all29':'not_run'}
(D/'static-review-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['runs','git_commands','DCP']}))

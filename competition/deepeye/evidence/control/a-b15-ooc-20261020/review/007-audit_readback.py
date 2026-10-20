import ctypes,datetime,hashlib,json,pathlib,re
from ctypes import wintypes as w
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[2];OUT=D.parent
def check(c,s):
 if not c:raise AssertionError(s)
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=load(D/'native-readback-started.json');raw=load(D/'native-readback-result.json');facts=dict(line.split('=',1) for line in (D/'readback-facts.txt').read_text().splitlines());ports={}
for line in (D/'readback-ports.txt').read_text().splitlines():
 name,direction=line.split('|');check(name not in ports,'duplicate bit port');ports[name]={'IN':'INPUT','OUT':'OUTPUT','INPUT':'INPUT','OUTPUT':'OUTPUT'}[direction]
expected=load(D/'expected-ports.json')['bit_level'];check(ports==expected,'all 798 native DCP bit ports and directions')
check(facts['part']=='xc7z020clg400-1' and facts['threads']=='1' and facts['blackboxes']==facts['latches']==facts['clocks']=='0' and facts['cells']=='2397' and facts['bit_ports']=='798','native report facts')
util=(D/'readback-utilization.rpt').read_text();check(re.search(r'^\| Design\s+: deepeye_pwm_applied_capture\s*$',util,re.M),'native report design top identity');check(re.search(r'\| deepeye_pwm_applied_capture\s+\|\s+\(top\)\s+\|\s+842\s+\|\s+842\s+\|\s+0\s+\|\s+0\s+\|\s+1117',util),'native utilization same')
check(facts['top']=='' and facts['design_object_name']=='checkpoint_synthesized','actual post-open fileset property observation');check(raw['status']=='failed' and raw['batch_exit_code']==1 and not raw['timeout'],'preserve real native failure')
check(raw['duration_seconds']<50 and raw['peak_job_committed_memory_bytes']<raw['actual_job_memory_cap_bytes']==4294967296 and raw['actual_job_priority_class']==16384,'actual native bounds')
check(raw['new_open_checkpoint_runs']==1 and raw['new_synthesis_runs']==0 and raw['input_hashes_unchanged'],'single scoped native readback')
check(load(D/'native-inputs-before.json')==load(D/'native-inputs-after.json'),'exact native input pins before/after')
for p,h in load(D/'native-inputs-before.json').items():check(sha(pathlib.Path(p))==h,'current executed native source/DCP/launcher identity')
text=(D/'native-stdout.txt').read_text();check('open_checkpoint: Time' in text and 'Checkpoint was created with Vivado v2026.1' in text and 'B15_CHECKPOINT_READBACK_FAIL Unexpected checkpoint identity' in text,'native open succeeded then harness failed')
check(not raw['warning_lines'],'native checkpoint log warnings recorded')
# Narrow own-root process check; no unrelated process inventory or mutation.
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD;k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
handle=k.OpenProcess(0x100000,False,start['pid'])
if handle:
 try:check(k.WaitForSingleObject(handle,0)==0,'owned cmd process terminated');root_state='terminated_signaled'
 finally:k.CloseHandle(handle)
else:check(ctypes.get_last_error()==87,'owned PID check error');root_state='no_existing_process_for_owned_pid'
pinfile=OUT/'background-synthesis-main-20261020/synthesis-public-inputs.json';manifest=load(pinfile)
for f in manifest['artifacts']:check(sha(OUT/f['path'])==f['sha256'],'all 47 pinned author bytes unchanged after readback')
result={'status':'offline_readback_reports_verified_raw_native_harness_exit1_preserved','native_open_checkpoint_completed':True,'native_end_to_end_harness_pass':False,'failure_cause':'after open_checkpoint current_fileset TOP is empty; native utilization report Design is correct; no source/DCP identity discrepancy observed','native_report_top':'deepeye_pwm_applied_capture','native_fileset_top':facts['top'],'native_design_object_name':facts['design_object_name'],'native_ports_all_match':True,'logical_ports':43,'bit_ports':798,'cells':2397,'blackboxes':0,'latches':0,'clock_objects':0,'LUT':842,'FF':1117,'native_warning_count':0,'native_batch_exit':1,'native_duration_seconds':raw['duration_seconds'],'native_peak_job_committed_bytes':raw['peak_job_committed_memory_bytes'],'readback_native_runs':1,'new_synthesis_runs':0,'owned_root_process_state':root_state,'child_cleanup':'private job TerminateJobObject succeeded for residual member, followed by kill-on-job-close; see pinned harness','all47_inputs_unchanged':True,'all29':'not_run'}
(D/'readback-report-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

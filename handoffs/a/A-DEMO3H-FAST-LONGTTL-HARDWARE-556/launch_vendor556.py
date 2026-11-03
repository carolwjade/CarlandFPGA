import hashlib,json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((D/'BUILD_PLAN.json').read_bytes());r=json.loads((D/'Root-review.json').read_bytes())
assert r['approved'] is True and r['operation_id']==p['operation_id'] and r['build_id']==p['build_id'] and r['plan_sha256']==sha(D/'BUILD_PLAN.json')
for n,pin in p['frozen_inputs'].items():assert sha(D/n)==pin,n
with (D/'VENDOR_STARTED.json').open('x') as f:json.dump(dict(operation_id=p['operation_id'],board=False,simulation_first=True),f)
s=Path('D:/codex-tmp/a324/.local/a556/s');s.mkdir(parents=True,exist_ok=False);base=D/'inputs/readonly_sources/fpga/diagnostic/g05_capture/additive50_source_candidate/rtl';bin=Path('D:/AMDFPGA/2026.1/Vivado/bin')
commands=[['xvlog.bat','--sv','-i',str(base),str(base/'deepeye_g05_profile_50mhz.sv'),str(base/'deepeye_g05_command_map_50mhz.sv'),str(D/'inputs/tb_fast_longttl556.sv')],['xelab.bat','tb_fast_longttl556','-s','tb556_snapshot'],['xsim.bat','tb556_snapshot','-runall']]
for i,args in enumerate(commands):
 argv=[str(bin/args[0])]+args[1:];v=subprocess.run(argv,cwd=s,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW);(D/('RTL_SIM_%d_STDOUT.bin'%i)).write_bytes(v.stdout);(D/('RTL_SIM_%d_STDERR.bin'%i)).write_bytes(v.stderr)
 with (D/('RTL_SIM_%d_RETURNED.json'%i)).open('x') as f:json.dump(dict(argv=argv,returncode=v.returncode),f)
 if v.returncode!=0:raise RuntimeError('Focused RTL simulation stage failed; never continue vendor build')
 if i==2 and b'A556_FOCUSED_RTL_PASS ttl_cases=12 guard_cases=5' not in v.stdout:raise RuntimeError('Focused RTL sentinel absent; never continue build')
with (D/'RTL_SIM_PASSED.json').open('x') as f:json.dump(dict(ttl_cases=12,guard_cases=5,board=False),f)
v=subprocess.run(p['vendor_argv'],cwd=D,creationflags=subprocess.CREATE_NO_WINDOW)
with (D/'VENDOR_RETURNED.json').open('x') as f:json.dump(dict(returncode=v.returncode,board=False),f)
raise SystemExit(v.returncode)

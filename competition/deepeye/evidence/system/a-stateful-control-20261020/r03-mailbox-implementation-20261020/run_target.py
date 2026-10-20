import hashlib,json,os,pathlib,runpy,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parents[2]/'.local/deepeye-implementation-a/competition/deepeye';label=sys.argv[1];events=[]
def audit(event,args):
 if event in {'subprocess.Popen','socket.connect','socket.bind','os.system','os.startfile'}:events.append(event);raise AssertionError('external effects prohibited: '+event)
 if event=='open' and not isinstance(args[0],int):
  mode=args[1];flags=args[2];writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
  if writing and not pathlib.Path(args[0]).resolve().is_relative_to(D):raise AssertionError('unowned test write')
sys.addaudithook(audit);sys.path.insert(0,str(P/'integration'));sys.argv=[str(P/'integration/test_candidate_mailbox.py')]
try:
 if label=='deadline-negative-control':
  import importlib.util,types,unittest
  source=(P/'integration/candidate_mailbox.py').read_text(encoding='utf-8');needle='if start_ns >= deadline or start_ns < max(now, ready):';assert source.count(needle)==1
  mutated=source.replace(needle,'if start_ns < max(now, ready):');(D/'deadline-negative-control-mutant.py').write_text(mutated,encoding='utf-8')
  module=types.ModuleType('candidate_mailbox');module.__file__=str(D/'deadline-negative-control-mutant.py');module.__package__='';sys.modules['candidate_mailbox']=module;exec(compile(mutated,module.__file__,'exec'),module.__dict__)
  spec=importlib.util.spec_from_file_location('deadline_tests',P/'integration/test_candidate_mailbox.py');test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
  suite=unittest.defaultTestLoader.loadTestsFromName('MailboxTests.test_literal_fast_stress_timelines_both_modes',test);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(0 if result.wasSuccessful() else 1)
 runpy.run_path(sys.argv[0],run_name='__main__')
finally:
 files={}
 for m in tuple(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=pathlib.Path(f)
   if p.is_file():files[str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
 (D/(label+'-imports.json')).write_text(json.dumps({'worker_pid':os.getpid(),'prohibited_attempts':events,'module_file_hashes':files},indent=2)+'\n',encoding='utf-8')

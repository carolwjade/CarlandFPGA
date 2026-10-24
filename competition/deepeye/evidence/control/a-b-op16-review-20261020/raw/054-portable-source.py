import importlib.util,json,pathlib,sys,unittest
D=pathlib.Path(__file__).resolve().parent;mode=sys.argv[1];base=D/('minimal' if mode=='portable' else 'snapshot/repo');path=base/'competition/deepeye/tests/control/test_pwm_applied_capture_runner.py';events=[]
def guard(event,args):
 if event in {'subprocess.Popen','os.system','os.startfile','socket.connect','socket.bind'}:events.append(event);raise AssertionError('external effect prohibited in stdlib test: '+event)
 if event in {'os.mkdir','os.remove','os.rmdir'}:
  p=pathlib.Path(args[0]).resolve()
  if not p.is_relative_to(D):raise AssertionError('write outside assigned folder: '+event)
sys.addaudithook(guard)
spec=importlib.util.spec_from_file_location('reviewed_tests_'+mode,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);suite=unittest.defaultTestLoader.loadTestsFromModule(mod);count=suite.countTestCases();assert count==23,count
result=unittest.TextTestRunner(verbosity=2).run(suite);out={'mode':mode,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'prohibited_process_network_attempts':events,'source_path':str(path),'ModelSim_Vivado_board_runs':0};(D/(mode+'-result.json')).write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out));sys.exit(0 if result.wasSuccessful() and not events else 1)

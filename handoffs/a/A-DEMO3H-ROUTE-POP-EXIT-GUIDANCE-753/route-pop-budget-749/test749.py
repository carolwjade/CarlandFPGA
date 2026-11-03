from pathlib import Path
import sys,json,ast,dataclasses
from types import SimpleNamespace as N
R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发");D=Path(__file__).resolve().parent
p=json.loads((R/".local/a740/nav/plan.json").read_text(encoding="utf8"));stage=Path(sys.argv[1]) if len(sys.argv)>1 else D/"python-source";sys.path[:0]=[str(stage),p['hostdeps']]
from competition.deepeye.tools.diagnostic import functional50_board_a as b
from competition.deepeye.tools.diagnostic.functional50_demo_four_cycle_profile_a import DEMO_FOUR_CYCLE
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1 as ROUTE,NAV_FAST_LONGTTL_180S as OLD
fn=getattr(b,'_global_trace_pop_limit',None);assert fn is not None,'explicit typed route POP budget missing'
source=(stage/'competition/deepeye/tools/diagnostic/functional50_board_a.py').read_text(encoding='utf8');tree=ast.parse(source)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_TracePort');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_call')
checks=[n for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and any(isinstance(a,ast.Constant) and a.value=='global POP limit' for a in n.args)]
assert len(checks)==1
expr=compile(ast.Expression(checks[0].args[0]),'actual original _call global POP guard','eval')
def allows(profile,count):return eval(expr,dict(value=8,self=N(_commands={8:count}),selected=profile,_global_trace_pop_limit=fn))
def reject(f):
 try:f()
 except (ValueError,TypeError):return
 raise AssertionError('missing foreign-type rejection')
passed=[]
assert allows(None,4095) and not allows(None,4096);passed.append('old_default4096_exact_refusal')
assert fn(OLD)==4096 and fn(DEMO_FOUR_CYCLE)==4096;passed.append('old180_fourcycle_caps_unchanged')
assert 28*146==4088 and allows(None,4088+7) and not allows(None,4088+8)
assert all(allows(ROUTE,4088+k) for k in range(146));passed.append('actual146x28_trace29_ninthPOP_oldred_newgreen')
assert fn(ROUTE)==64*4096 and allows(ROUTE,64*4096-1) and not allows(ROUTE,64*4096);passed.append('route64_finite_global_boundary')
assert fn(dataclasses.replace(ROUTE))==4096;reject(lambda:fn({'profile_id':ROUTE.profile_id}));reject(lambda:fn(True));passed.append('foreign_equal_not_extended_untyped_rejected')
assert 'limits={1:1,2:4,3:4,4:4,5:1,8:4096}' in source
assert 'counts[value]<limits[value]' in source and 'self._count<limit' in source
assert ROUTE.max_trace_io==131072 if hasattr(ROUTE,'max_trace_io') else ROUTE.max_trace_io_count==131072
passed.append('per_scan4096_and_original_totalIO131072_untouched')
assert all(allows(ROUTE,i*146+145) for i in range(64));passed.append('64_selected146byte_scans_fit_without_renew_or_reset')
r=dict(passed=True,controls=passed,expected_actual740_POP_before29=4088,expected_old_failure_scan29_POP=9,new_route_global_POP_limit=fn(ROUTE),old_limit=4096,scope='pure host budget/actual guard AST controls; no board/RTL/model/PDE/native',final_gates='not_run')
(D/'CONTROLS.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(json.dumps(r))

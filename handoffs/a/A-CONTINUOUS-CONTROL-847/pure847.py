"""Two narrow AST-isolated controls; no imports of runtime/source/AI/board."""
import ast,math,pathlib,unittest
from types import SimpleNamespace
P=pathlib.Path(__file__).with_name('controller847.py')
TREE=ast.parse(P.read_bytes());MAIN=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='main')
NS={'math':math}
exec(compile(ast.Module(body=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in ('advice_applicable','stop_native_once')],type_ignores=[]),'pure847-helpers','exec'),NS)

class Controls(unittest.TestCase):
 def test_held_original_advice_epoch_age_pose_guard_without_age_renewal(self):
  check=NS['advice_applicable'];state=dict(position_m=[0,0,0],orientation_xyzw=[0,0,0,1])
  advice=dict(status='ADVISE',world_epoch='epoch',source_acquisition_qpc_ns='1000000000',
              source_pose=dict(position_m=[0,0,0],orientation_xyzw=[0,0,0,1]))
  self.assertTrue(check(advice,state,'epoch',6_000_000_000))
  self.assertFalse(check(advice,state,'epoch',6_000_000_001))
  self.assertFalse(check(advice,state,'foreign',2_000_000_000))
  self.assertFalse(check(advice,dict(state,position_m=[.250001,0,0]),'epoch',2_000_000_000))
  q=[0,math.sin(math.radians(7.51)),0,math.cos(math.radians(7.51))]
  self.assertFalse(check(advice,dict(state,orientation_xyzw=q),'epoch',2_000_000_000))
  self.assertEqual(advice['source_acquisition_qpc_ns'],'1000000000')
  # The actual held branch must call this guard before assigning command=held.
  held_branch=next(n for n in ast.walk(MAIN) if isinstance(n,ast.If) and
                  ast.get_source_segment(P.read_text(),n.test).replace(' ','').startswith('heldisnotNoneandgrant-now<7_000_000_000'))
  self.assertIn('advice_applicable(held_advice',ast.get_source_segment(P.read_text(),held_branch))
  held={'speed_code':2};ns=dict(NS,held=held,held_advice=advice,state=state,epoch='epoch',now=6_000_000_000,
      grant=7_000_000_000,control=SimpleNamespace(advice=None))
  code=compile(ast.Module(body=[held_branch],type_ignores=[]),'actual847-held-renewal','exec')
  exec(code,ns);self.assertIs(ns['command'],held)
  ns['now']+=1;exec(code,ns);self.assertEqual(ns['command']['speed_code'],0)
 def test_stop_once_immediate_and_late_apply_never_readmitted(self):
  stop=NS['stop_native_once']
  class Native:
   def __init__(self,fail=False):self.calls=0;self.fail=fail;self.applies=0
   def stop(self):
    self.calls+=1
    if self.fail:raise OSError('synthetic stop response unknown')
    return dict(ok=True,board_stop_acknowledged=False)
   def apply_pwm(self,*a,**k):self.applies+=1;raise AssertionError('terminal APPLY readmitted')
   pause=apply_pwm
  for failure in (False,True):
   native=Native(failure);result={};stop(native,result,'want_stop');stop(native,result,'finally')
   self.assertEqual(native.calls,1);self.assertTrue(result['native_stop_attempted'])
  branch=next(n for n in ast.walk(MAIN) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and
              isinstance(n.test.left,ast.Name) and n.test.left.id=='kind' and
              isinstance(n.test.comparators[0],ast.Constant) and n.test.comparators[0].value=='apply')
  class Control:
   def consume_initial(self,value):self.consumed=value
  native=Native();result={};stop(native,result,'arrival');control=Control();logs=[]
  ns=dict(actual=dict(response={'known':'original board reply'},host_deadline_qpc_ns=123),now=1,
          meta=dict(command=dict(speed_code=2),actual_advice=None,reserved_initial_speed=.1),
          control=control,native=native,want_stop=True,result=result,log=lambda event,**kw:logs.append(event))
  exec(compile(ast.Module(body=branch.body,type_ignores=[]),'actual847-apply-branch','exec'),ns)
  self.assertEqual(native.applies,0);self.assertEqual(logs,['actual-pwm-terminal-not-admitted'])
  guard=min([n for n in ast.walk(MAIN) if isinstance(n,ast.If) and
             'NATIVE_SAFETY_FAULT' in ast.get_source_segment(P.read_text(),n)],key=lambda n:n.end_lineno-n.lineno)
  self.assertFalse(eval(compile(ast.Expression(guard.test),'actual847-stop-guard','eval'),{},dict(state={'fault':'operator_stop'},want_stop=True,result=result)))
  outer=next(n for n in MAIN.body if isinstance(n,ast.Try) and n.finalbody)
  self.assertEqual(outer.handlers[0].body[0].value.func.id,'stop_native_once')
  self.assertEqual(outer.finalbody[0].value.func.id,'stop_native_once')

if __name__=='__main__':unittest.main()

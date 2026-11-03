import ast,json,pathlib,sys,types
p=pathlib.Path(sys.argv[1]);tree=ast.parse(p.read_text(encoding='utf8'));cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PcDirectRuntime');step=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='step');step.decorator_list=[]
helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_step_exception_diagnostic'];mod=ast.fix_missing_locations(ast.Module(body=helpers+[step],type_ignores=[]))
T=types.SimpleNamespace
class NoActive(ValueError):pass
class Geometry(ValueError):
 def __init__(self,status,checked):super().__init__('motion preparation rejected');self.status=status;self.checked_slices=checked
class Receipt:
 def __init__(self):self.boot='boot';self.command_seq=1;self.pose_revision=8;self.start_ns=10;self.end_ns=110
scope={'_NoActiveCommand':NoActive,'_integer':lambda *a:None,'CommitReceipt':Receipt,'StepResult':lambda c,r,receipt=None:T(committed=c,reason=r,receipt=receipt)};exec(compile(mod,'<actual-runtime-step>','exec'),scope);run=scope['step']
class Runtime:
 def __init__(self,error):
  self._last_step_exception={'old':True};self._busy=False;self._stepping=False;self._pose_revision=7;self._command=T(raw=b'original',sequence=1);self._boot='boot';self.error=error;self.trips=[];self._deps=T(prepare_step=self.prepare,commit_step=self.commit)
 def _trip(self,r):self.trips.append(r)
 def _active(self):pass
 def _same_boot(self,b):return b=='boot'
 def _ready(self,dt):return T(command_seq=1,checked_ns=10,step_end_ns=110)
 def prepare(self,*a):
  if self.error is not None:raise self.error
  return object()
 def commit(self,p,check):check();return Receipt()
checks=[]
for error,status,checked in [(Geometry('UNKNOWN',4),'UNKNOWN',4),(Geometry('BLOCKED',2),'BLOCKED',2),(ValueError('watchdog veto'),None,None),(NoActive('no current command'),None,None)]:
 r=Runtime(error);out=run(r,expected_pose_revision=7,dt_ns=100)
 assert out.committed is False and out.reason==str(error)
 d=r._last_step_exception;assert {k:v for k,v in d.items() if k!='origin'}==dict(type=type(error).__name__,message=str(error),status=status,checked_slices=checked),d
 assert d['origin']['function']=='prepare' and type(d['origin']['line']) is int and d['origin']['line']>0,d
 assert r._stepping is False
 if isinstance(error,NoActive):assert not r.trips
 else:assert r.trips==['step_veto']
 checks.append(type(error).__name__+':'+str(status))
r=Runtime(None);out=run(r,expected_pose_revision=7,dt_ns=100);assert out.committed and out.reason=='trusted_executor_receipt' and r._last_step_exception is None;checks.append('success clears prior failure')
print(json.dumps({'passed':True,'controls':checks,'MMIO':False,'model':False,'board':False}))
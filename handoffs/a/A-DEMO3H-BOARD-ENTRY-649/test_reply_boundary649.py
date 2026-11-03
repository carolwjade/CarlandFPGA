import ast,copy,json,pathlib,sys,types
p=pathlib.Path(sys.argv[1]);tree=ast.parse(p.read_text(encoding='utf8'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');loop=next(n for n in main.body if isinstance(n,ast.While));outer=next(n for n in loop.body if isinstance(n,ast.Try));start=next(i for i,n in enumerate(outer.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='response' for t in n.targets));tail=copy.deepcopy(outer);tail.body=tail.body[start:];init=next(n for n in loop.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='started' for t in n.targets));fn=ast.FunctionDef(name='tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Global(names=['step','route_archive'])]+[copy.deepcopy(n) for n in loop.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('started','reply_attempted') for t in n.targets)]+[tail],decorator_list=[]);mod=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
checks=[]
for kind,mode in [('init','normal'),('init','after_write_error'),('init','partial_write_error'),('apply','archive_error')]:
 emitted=[];journals=[];marker=object()
 class Seq:
  def __init__(self):self.n=0
  @property
  def demo_cycle_profile(self):
   if mode=='after_write_error' and emitted:raise RuntimeError('synthetic post-write error')
   return marker if kind=='apply' else None
 seq=Seq()
 def write(value,profile=None):
  emitted.append(value)
  if mode=='partial_write_error':raise OSError('synthetic failed flush after write attempt')
 class Archive:
  def __init__(self,*a):raise RuntimeError('synthetic archive failure')
 env=dict(__package__=None,raw=lambda x:json.dumps(x,sort_keys=True).encode(),SCHEMA='functional50_chain_v2',request_id='one',kind=kind,plan={'operation_id':'op'},result={},need=lambda x,msg:None if x else (_ for _ in ()).throw(ValueError(msg)),_demo=lambda:types.SimpleNamespace(reply_cap=lambda p:100000),sequence=seq,port=types.SimpleNamespace(_dir=pathlib.Path('synthetic')),step=0,put=lambda p,v:journals.append((str(p),v)),write_line=write,NAV_ROUTE_LONGTTL_600S_V1=marker,sent_response_paths=[],route_archive=None,_RouteEvidenceArchive=Archive,owner=None,gs=None)
 exec(compile(mod,'<original-tail>','exec'),env)
 try:env['tail']()
 except OSError:
  if mode!='partial_write_error':raise
 assert len(emitted)==1,(kind,mode,'duplicate/absent replies',len(emitted))
 if mode in ('after_write_error','partial_write_error'):assert any('post-reply-failed' in name for name,_ in journals),(mode,journals)
 checks.append(kind+':'+mode)
# Entry is executed with no package; every new import must be canonical.
assert not [n for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.level], 'relative import still present'
for statement in ['from competition.deepeye.tools.diagnostic import functional50_trace_cycles_a as cycles','from competition.deepeye.simulation.authority import navigation_session_profile as navigation','from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1']:
 node=ast.parse(statement).body[0];assert any(isinstance(n,ast.ImportFrom) and ast.dump(n)==ast.dump(node) for n in ast.walk(tree)),statement
# Execute canonical imports against ordinary module stubs, never MMIO.
names=['competition','competition.deepeye','competition.deepeye.tools','competition.deepeye.tools.diagnostic','competition.deepeye.tools.diagnostic.functional50_trace_cycles_a','competition.deepeye.simulation','competition.deepeye.simulation.authority','competition.deepeye.simulation.authority.navigation_session_profile']
old={n:sys.modules.get(n) for n in names}
try:
 for n in names:
  v=types.ModuleType(n);v.__path__=[];sys.modules[n]=v
 sys.modules[names[-1]].NAV_ROUTE_LONGTTL_600S_V1=object()
 env={'__package__':None}
 for statement in ['from competition.deepeye.tools.diagnostic import functional50_trace_cycles_a as cycles','from competition.deepeye.simulation.authority import navigation_session_profile as navigation','from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1']:exec(statement,env)
finally:
 for n,v in old.items():
  if v is None:sys.modules.pop(n,None)
  else:sys.modules[n]=v
checks.append('__package__None:canonical-imports')
print(json.dumps(dict(passed=True,checks=checks,MMIO=False,board=False,model=False)))
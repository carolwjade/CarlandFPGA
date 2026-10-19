"""Compare AST call shapes to current helper definitions without importing Win32."""
import ast,inspect,json,pathlib
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];BASE=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulation/isolation'
tree=ast.parse((BASE/'win32.py').read_text(encoding='utf-8'))
definitions={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
bindings={}
for x in tree.body:
    if isinstance(x,ast.Assign) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='bind':
        for target in x.targets:
            if isinstance(target,ast.Name) and len(x.value.args)>=3 and isinstance(x.value.args[2],ast.List):
                bindings[target.id]={'arity':len(x.value.args[2].elts),'restype':ast.unparse(x.value.args[3]) if len(x.value.args)>3 else 'W.BOOL'}
def signature(fn):
    args=fn.args;pars=[];pos=args.posonlyargs+args.args;required=len(pos)-len(args.defaults)
    for i,arg in enumerate(pos):pars.append(inspect.Parameter(arg.arg,inspect.Parameter.POSITIONAL_ONLY if i<len(args.posonlyargs) else inspect.Parameter.POSITIONAL_OR_KEYWORD,default=inspect.Parameter.empty if i<required else object()))
    if args.vararg:pars.append(inspect.Parameter(args.vararg.arg,inspect.Parameter.VAR_POSITIONAL))
    for arg,default in zip(args.kwonlyargs,args.kw_defaults):pars.append(inspect.Parameter(arg.arg,inspect.Parameter.KEYWORD_ONLY,default=inspect.Parameter.empty if default is None else object()))
    if args.kwarg:pars.append(inspect.Parameter(args.kwarg.arg,inspect.Parameter.VAR_KEYWORD))
    return inspect.Signature(pars)
rows=[]
for file in ['actor_owner.py','actor_lifetime.py']:
    root=ast.parse((BASE/file).read_text(encoding='utf-8'))
    for node in ast.walk(root):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or not isinstance(node.func.value,ast.Attribute) or node.func.value.attr!='_api':continue
        name=node.func.attr;row={'source':file,'line':node.lineno,'helper':name,'positional_count':len(node.args),'keyword_names':[x.arg for x in node.keywords]}
        assert not any(isinstance(x,ast.Starred) for x in node.args) and all(x.arg is not None for x in node.keywords)
        if name in definitions:
            sig=signature(definitions[name]);sig.bind(*([object()]*len(node.args)),**{x.arg:object() for x in node.keywords});row.update(kind='Python helper',signature=str(sig),compatible=True)
        elif name in bindings:
            assert len(node.args)==bindings[name]['arity'] and not node.keywords
            row.update(kind='ctypes binding',binding=bindings[name],compatible=True)
        else:raise AssertionError('unknown helper '+name)
        rows.append(row)
out={'verification':'PASS:static call-shape compatibility only','calls':rows,'native_execution':'not_run; ctypes DLL module never imported','resource_flow':'source review: paired native acquisitions registered inside unchanged helper; retained original process sampled; one sealed cleanup; unknown terminal retains recovery controls','native_limitations':['Real security token/ACL/mitigation/creation/resume behavior unexecuted','CreateProcess-to-AssignJob crash window remains','Post-sample death and authority-owner hang remain','available_output helper hard caps8192; smaller policy limit is checked after helper returns, not passed into native read']}
(H/'helper_signatures.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'verification':out['verification'],'calls':len(rows),'native_execution':out['native_execution']},indent=2))

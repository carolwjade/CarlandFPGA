from pathlib import Path
import hashlib,json,shutil,math,struct,random,sys,decimal,importlib.util
from fractions import Fraction as F

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
SIM=HERE/'stage/competition/deepeye/simulator'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def files(p): return {x.relative_to(p).as_posix():sha(x) for x in p.rglob('*') if x.is_file() and '.godot' not in x.parts and '__pycache__' not in x.parts}

def oracle(ef,eu,ev,xf,xu,xv):
    edge=all(math.isfinite(x) and abs(x)<=14.85 for x in [eu,ev,xu,xv])
    q=(F(eu)-F(xu))**2+(F(ev)-F(xv))**2-(2*F(.15))**2
    with decimal.localcontext() as c:
        c.prec=2500
        d=decimal.Decimal.from_float
        z=(d(eu)-d(xu))**2+(d(ev)-d(xv))**2-(2*d(.15))**2
    assert (q>0)-(q<0)==(z>0)-(z<0)
    return edge and (ef!=xf or q>=0),str(q)

def main():
    assert not SIM.exists()
    for p in [ROOT,PRODUCT]:
        scope=json.loads((p/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8'))
        assert hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    before=files(PRODUCT/'competition/deepeye/simulator')
    for rel in before:
        p=SIM/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PRODUCT/'competition/deepeye/simulator'/rel,p)
    for rel in ['editor/scene_document.gd','editor/layout_codec.gd']:
        p=HERE/'baseline'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SIM/rel,p)
    gpath=PRODUCT/'competition/deepeye/simulation/authority/motion/gate_geometry.py'
    gp=HERE/'oracle/gate_geometry.py';gp.parent.mkdir();shutil.copyfile(gpath,gp)
    spec=importlib.util.spec_from_file_location('authority_gate_geometry',gp);g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
    rows=[]
    faces=['top','bottom','front','back','left','right']
    def add(name,ef,eu,ev,xf,xu,xv):
        values=[eu,ev,xu,xv]
        want,residual=oracle(ef,*values[:2],xf,*values[2:])
        try: g.validate_gate_pair(g.Gate(ef,eu,ev),g.Gate(xf,xu,xv));authority=True
        except ValueError: authority=False
        assert want==authority
        rows.append(dict(name=name,entry_face=ef,exit_face=xf,hex=''.join(struct.pack('<d',v).hex() for v in values),want=want,values=values,residual=residual))
    for ef in faces:
        for xf in faces:
            add('all36-separated',ef,-1.,.75,xf,1.,-.75)
        xf=faces[(faces.index(ef)+1)%6]
        for sign in [-1,1]:
            for axis in [0,1]:
                for bound in [math.nextafter(14.85,0),14.85,math.nextafter(14.85,math.inf),14.8500000005,14.850001]:
                    a=[0.,0.];a[axis]=sign*bound
                    add('edge-neighbor',ef,*a,xf,0.,0.)
        for offset in [-14.5,-10.,-1.,-.3,-.15,0.,.15,1.,10.,14.5]:
            for sign in [-1,1]:
                for sep in [math.nextafter(.3,0),.3,math.nextafter(.3,math.inf),.2999999995,.299999,.300001]:
                    for axis in [0,1]:
                        a=[offset,.125];b=a.copy();b[axis]+=sign*sep
                        if max(map(abs,a+b))<=14.85: add('axis-boundary',ef,*a,ef,*b)
        for a,b in [(0.,.3),(-.15,.15),(-.3,0.)]:
            add('represented-tangent',ef,a,0.,ef,b,0.)
        for off in [-14.5,-1.,0.,1.,14.5]:
            for du,dv in [(.18,.24),(.24,.18),(.3/math.sqrt(2),.3/math.sqrt(2)),(-.18,.24),(.18,-.24)]:
                for u in [math.nextafter(du,-math.inf),du,math.nextafter(du,math.inf)]:
                    add('diagonal',ef,off,off,ef,off+u,off+dv)
        for tiny in [math.ulp(0.),2**-1022,2**-500]:
            add('tiny-axis',ef,0.,tiny,ef,.3,0.)
            add('tiny-overlap',ef,0.,tiny,ef,math.nextafter(.3,0),0.)
    dump(HERE/'cases.json',rows)
    shutil.copyfile(HERE/'cases.json',SIM/'tests/numeric_cases.json')
    dump(HERE/'source-before.json',{'product':before,'oracle':sha(gp),'cases':len(rows),'root_scope_verified':True,'product_scope_verified':True})
    print(json.dumps({'cases':len(rows),'product_files':len(before)}))
if __name__=='__main__':main()

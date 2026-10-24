from pathlib import Path
import json,math,struct,random
from fractions import Fraction as F
from decimal import Decimal,localcontext
H=Path(__file__).resolve().parent
rows=[]
def add(s,ok=True):
 try:v=float(s);want=ok and abs(v)<16 and math.isfinite(v)
 except ValueError:want=False;v=0.
 rows.append(dict(token=s,want=want,hex=struct.pack('<d',v).hex() if want else ''))
for s in ['0','-0','-0.0','0e9999999999','-0e-9999999999','14.850000000000001','-14.850000000000001','1.4850000000000001e1','4.9406564584124654e-324','2.2250738585072014e-308','1e-999999999','1e999999999','16','-16','15.999999999999999','0.'+'0'*2000+'1','1'+'0'*2048]:add(s,len(s)<=2048)
for value in [0.,math.ulp(0.),2*math.ulp(0.),math.nextafter(2**-1022,0),2**-1022,.15,.18,.24,.3,1.,14.85]:
 other=math.nextafter(value,math.inf)
 mid=(F(value)+F(other))/2
 with localcontext() as c:
  c.prec=2500
  m=Decimal(mid.numerator)/Decimal(mid.denominator)
  gap=Decimal(1).scaleb(m.as_tuple().exponent-2)
  for n in [m-gap,m,m+gap]:
   for sign in [1,-1]:add(str(sign*n))
rng=random.Random(20261020)
for _ in range(100):
 value=math.ldexp(rng.uniform(-1.,1.),rng.randint(-1074,3));add(format(value,'.17g'))
(H/'reader_cases.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(H/'stage/competition/deepeye/simulator/tests/reader_cases.json').write_text(json.dumps(rows),encoding='utf-8')
print('reader cases',len(rows))

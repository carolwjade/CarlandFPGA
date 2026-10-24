from pathlib import Path
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import struct,json
HERE=Path(__file__).resolve().parent
def f(x):return F.from_float(struct.unpack('<f',struct.pack('<f',float(x)))[0])
def dec(x):return D(x.numerator)/D(x.denominator) if isinstance(x,F) else D(x)
def fmt(x):return str(dec(x))
def rows(mode):return [json.loads(s[11:]) for s in (HERE/(mode+'-cast')/'stdout.log').read_text(encoding='utf-8').splitlines() if s.startswith('CAST_PROBE ')]
def distance2(t,low,high,c,h):
    # Squared distance between the entire capsule axis segment and solid AABB.
    center=[c[0],c[1],c[2]+2*t]
    gaps=[max(F(0),low[i]-center[i],center[i]-high[i]) for i in (0,1)]
    gaps.append(max(F(0),low[2]-(center[2]+h),(center[2]-h)-high[2]))
    return sum(x*x for x in gaps)
def oracle(row,q,mode):
    sh=row['fixture_shapes'][0]; c=list(map(f,row['body_origin']))
    p=list(map(f,sh['position']));size=list(map(f,sh['size']))
    low=[p[i]-size[i]/2 for i in range(3)]; high=[p[i]+size[i]/2 for i in range(3)]
    r=f(q['radius_readback' if mode=='raw' else 'radius_m']);height=f(q['height_readback' if mode=='raw' else 'height_m']);h=height/2-r
    assert row['body_axis']==[0,0,1] and row['motion']==[0,0,2]
    # Independent monotone bisection of segment-to-box distance on approach.
    tmid=(p[2]-c[2])/2
    if distance2(tmid,low,high,c,h)>r*r:return {'contact':False,'radius':fmt(r),'h':fmt(h),'min_distance2':fmt(distance2(tmid,low,high,c,h))}
    a=F(0);b=tmid
    for _ in range(240):
        m=(a+b)/2
        if distance2(m,low,high,c,h)<=r*r:b=m
        else:a=m
    return {'contact':True,'fraction_lo':fmt(a),'fraction_hi':fmt(b),'radius':fmt(r),'h':fmt(h),'distance_at_fraction_03':fmt(distance2(F(3,10),low,high,c,h)),'r2':fmt(r*r),'exact_tangency':distance2(tmid,low,high,c,h)==r*r,'bisection_arithmetic':'exact rational; 240 iterations'}
allout={};config=[]
with localcontext() as ctx:
    ctx.prec=100
    for backend in ('default','godot','jolt'):
        out=[];stats={m:dict(cases=0,contacts=0,misses=[],false_positives=[],max_late_m=D(0),max_early_m=D(0)) for m in ('raw','adapter')}
        for row in rows(backend):
            if not(row['label'].startswith('grazing_') or row['label']=='eccentric_cap_x_0.1'):continue
            entry={'label':row['label']}
            for mode in ('raw','adapter'):
                q=row[mode];truth=oracle(row,q,mode);hit=q['initial_count']>0 or q['endpoint_count']>0 or q['fractions'][0]<1
                s=stats[mode];s['cases']+=1;s['contacts']+=truth['contact']
                if truth['contact'] and not hit:s['misses'].append(row['label'])
                if not truth['contact'] and hit:s['false_positives'].append(row['label'])
                error=None
                if truth['contact'] and q['fractions'][0]<1:
                    error=2*(D.from_float(q['fractions'][0])-D(truth['fraction_hi']))
                    s['max_late_m']=max(s['max_late_m'],error);s['max_early_m']=max(s['max_early_m'],-error)
                entry[mode]={'truth':truth,'hit':hit,'fractions':q['fractions'],'safe_late_m':str(error)}
                if backend=='default':config.append(dict(label=row['label']+'_'+mode,position=row['fixture_shapes'][0]['position'],size=row['fixture_shapes'][0]['size'],radius=q['radius_readback' if mode=='raw' else 'radius_m'],height=q['height_readback' if mode=='raw' else 'height_m']))
            out.append(entry)
        allout[backend]={'stats':stats,'rows':out}
    a=rows('default');b=rows('godot')
    # IDs are per process; other query data and fractions must be identical.
    allout['default_explicit_godot_query_equality']=all(x['raw']==y['raw'] and x['adapter']['fractions']==y['adapter']['fractions'] for x,y in zip(a,b)) and len(a)==len(b)
(HERE/'independent-analysis.json').write_text(json.dumps(allout,default=str,indent=2)+'\n',encoding='utf-8')
(HERE/'independent-cases.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v['stats'] for k,v in allout.items() if isinstance(v,dict)},default=str,indent=2))

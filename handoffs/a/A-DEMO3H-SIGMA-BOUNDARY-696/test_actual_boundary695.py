import importlib.util,json,math,pathlib,struct,sys,types
D=pathlib.Path(__file__).parent;O=D.parent;N=pathlib.Path('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/a680/nav');p=json.loads((N/'plan.json').read_bytes());sys.path.insert(0,p['stage']);sys.path.append('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps')
from competition.deepeye.simulation.sensors import owned_world_field as old,forward_profile as forward
from competition.deepeye.simulation.authority.motion import solid_clearance as sc
result=json.loads((O/'source-fault-692/POINT_ENUMERATION_ACTUAL680.json').read_bytes());point=result['first_invalid']['point_m'];pose=result['reconstructed_pose']
name=old.__name__;spec=importlib.util.spec_from_file_location(name,D/'owned_world_field.py');new=importlib.util.module_from_spec(spec);sys.modules[name]=new;spec.loader.exec_module(new)
layout=json.loads((N/'p/owned-input/layout.json').read_bytes())['layout'];snapshot=json.loads((N/'n/original-snapshot.json').read_bytes());byid={str(x['object_id']):x for x in layout['obstacles']};pieces=[]
for ob in snapshot['assets']['objects']:
 x=byid[ob['object_id']];q=tuple(struct.unpack('>d',bytes.fromhex(v))[0] for v in ob['proposed_quaternion']);so=sc.Solid('Root-only-test-'+ob['object_id'],'offline695','cylinder' if x['kind']=='casing' else 'box',tuple(x['position'][k] for k in ('x','y','z')),tuple(x['size'][k]/2 for k in ('x','y','z')),q);pieces.append((old._PRIORITY[x['kind']],p['field_policy']['material_sigma'][x['kind']],so.kind,tuple(float(v) for v in so.centre),tuple(float(v) for v in so.dimensions),tuple(tuple(float(v) for v in row) for row in so.matrix)))
def field(mode=None,epsilon=0.,rows=None):
 x=object.__new__(new.OwnedWorldField);x._pieces=tuple(pieces if rows is None else rows);x._background=.005;x._epsilon=epsilon;x._demo_boundary_profile=mode;x._boundary_count=0;x._boundary_records=[];x._em_scope_factory=None;return x
checks=[];strict=field();assert old.OwnedWorldField._sample_sigma_pure(strict,*point) is None;assert strict._sample_sigma_pure(*point) is None;checks.append('actual692 first invalid point: old and new strict both None')
mode=new.DEMO_KNOWN_BOX_CLOSED_BOUNDARY_V1;demo=field(mode);assert demo._sample_sigma_pure(*point)==.01;checks.append('actual692 known rock boundary new typed mode ->0.01')
channels=forward._kernel_channels(forward.Pose(tuple(pose['position_m']),tuple(pose['orientation_xyzw'])),demo._sample_sigma_pure);assert channels is not None and all(math.isfinite(v) for v in channels);checks.append('same actual692 full scalar kernel recomputes finite channels')
assert field(mode,epsilon=1e-8)._sample_sigma_pure(*point) is None;checks.append('nonzero uncertainty band remains None in pure body')
rows=list(pieces);r=list(rows[1]);r[1]=None;rows[1]=tuple(r);assert field(mode,rows=rows)._sample_sigma_pure(*point) is None;checks.append('unknown material remains None')
pt=list(point);pt[2]=math.nextafter(.5,math.inf);assert field(mode)._sample_sigma_pure(*pt)==.005;checks.append('one representable value outside box returns original background; no band fill')
pt[2]=math.nextafter(.5,0.);assert field(mode)._sample_sigma_pure(*pt)==.01;checks.append('one representable inside unchanged conductivity')
cylinder=((1,.01,'cylinder',(0.,0.,0.),(1.,1.,1.),((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))),);assert field(mode,rows=cylinder)._sample_sigma_pure(1.,0.,0.) is None;checks.append('cylinder boundary remains strict None')
for foreign in ({'profile_id':mode.profile_id,'sha256':mode.sha256},True,new.DemoSigmaBoundaryProfile(mode.profile_id,mode.sha256)):
 try:new.validate_demo_boundary_profile(foreign)
 except TypeError:pass
 else:raise AssertionError('foreign profile accepted')
checks.append('dict/bool/foreign exact-value profile rejected')
for x,new_mode in ((strict,mode),(demo,None)):
 try:x._demo_boundary_profile=new_mode
 except AttributeError:pass
 else:raise AssertionError('original boundary profile rebound')
checks.append('default/demo profile cannot be rebound after original construction')
for _ in range(20):demo._sample_sigma_pure(*point)
e=demo.demo_boundary_evidence();assert len(e['first_records'])<=16 and e['query_boundary_approximations']>16;e['first_records'][0]['point_m'][0]=999.;assert demo.demo_boundary_evidence()['first_records'][0]['point_m'][0]!=999.;checks.append('diagnostics bounded16 and detached')
x=dict(passed=True,checks=checks,new_kernel_channels=list(channels),boundary_evidence=demo.demo_boundary_evidence(),original680_fault_preserved=True,quality_scope='new offline fresh calculation under explicit engineering approximation; no real source/board qualification claimed',authority_minted=False,AI_model=False,PDE=False,board=False,UI=False)
(D/'FOCUSED_RESULT.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n',encoding='utf8');print(json.dumps(x))
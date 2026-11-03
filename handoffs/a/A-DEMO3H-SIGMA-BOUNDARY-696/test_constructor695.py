import importlib.util,inspect,json,pathlib,sys,types
D=pathlib.Path(__file__).parent;O=D.parent;sys.path.insert(0,str(O/'turn-trig-integration-678/python-source'));sys.path.append('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps')
name='competition.deepeye.simulation.sensors._constructor_seam695';spec=importlib.util.spec_from_file_location(name,pathlib.Path(sys.argv[1]));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
T=types.SimpleNamespace
class Scene:
 def __init__(self):self.objects=();self.scene_id='inert-seam';self.digest='inert-digest'
class Solid:pass
class Executor:
 def __init__(self):self._scene=Scene();self._world_binding='inert-binding'
 def authority_snapshot(self):return T(world_invalid=False,phase=T(context=T(run_id='inert',epoch=1)))
# Inert dependencies only: execute the actual candidate __init__, not a duplicate.
# This class is not the actual OwnedMotionExecutor; no original factory/authority is minted.
m.OwnedMotionExecutor=Executor;m.geometry=T(Scene=Scene,Solid=Solid,_digest=lambda s:s.digest)
policy=dict(material_sigma={k:None for k in m._PRIORITY},background_sigma=.005,max_pieces=1);e=Executor();checks=[]
default=m.OwnedWorldField(e,**policy);assert default._demo_boundary_profile is None and default._epsilon==0.;checks.append('actual __init__ old default completes without NameError')
inspect.signature(m.OwnedWorldField).bind(e,**policy,demo_boundary_profile=m.DEMO_KNOWN_BOX_CLOSED_BOUNDARY_V1);selected=m.OwnedWorldField(e,**policy,demo_boundary_profile=m.DEMO_KNOWN_BOX_CLOSED_BOUNDARY_V1);assert selected._demo_boundary_profile is m.DEMO_KNOWN_BOX_CLOSED_BOUNDARY_V1;checks.append('actual __init__ new keyword binds and completes')
try:m.OwnedWorldField(e,**policy,demo_boundary_profile=m.DEMO_KNOWN_BOX_CLOSED_BOUNDARY_V1,sample_epsilon_m=1e-8)
except ValueError as error:assert 'nonzero uncertainty band' in str(error)
else:raise AssertionError('finite band allowed')
checks.append('actual __init__ new mode nonzero epsilon rejects')
try:m.OwnedWorldField(e,**policy,demo_boundary_profile={})
except TypeError as error:assert 'exact explicit' in str(error)
else:raise AssertionError('foreign dict allowed')
checks.append('actual __init__ foreign mode rejects before binding')
print(json.dumps(dict(passed=True,checks=checks,real_constructor_body=True,inert_executor_and_scene=True,source_authority_minted=False,board=False,AI=False,PDE=False)))
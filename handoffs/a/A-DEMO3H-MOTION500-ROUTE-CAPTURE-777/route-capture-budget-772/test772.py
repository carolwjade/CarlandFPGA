from pathlib import Path
import sys,json,ast,threading,dataclasses
from types import SimpleNamespace as N
R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发");D=Path(__file__).resolve().parent;p=json.loads((R/".local/a770/nav/plan.json").read_bytes());stage=Path(sys.argv[1]) if len(sys.argv)>1 else D/'python-source';sys.path[:0]=[str(stage),p['hostdeps']]
from competition.deepeye.simulation.authority.source_projection_v1 import assembler as a,provider
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1 as NAV,NAV_FAST_LONGTTL_180S as OLD
obs=getattr(a,'_observation_capacity',None);ids=getattr(a,'_binding_capacity',None)
assert obs is not None and ids is not None,'typed observation/binding caps missing'
passed=[]
def rejects(fn):
 try:fn()
 except (ValueError,TypeError):return
 raise AssertionError('missing rejection')
def producer(profile):
 source=N(_navigation_profile=profile);book=N(_navigation_profile=profile,_source=source,_samples=[]);owner=object();link=N(owner=owner,book=book,source=source,binding=object(),_registered=lambda:None);source._source_book=book;book._owner=owner;book._actor_custody=N(link=link,book=book,_context=lambda:None)
 prod=a.Producer(a._KEY,owner,link,book,{})
 session=provider.ProjectionSession(provider._KEY,owner,link,book,prod)
 return prod,session,book
# Actual provider observe_capture -> original Producer.attach_capture loop; DTO fixtures only.
for profile,cap in ((None,32),(OLD,32),(NAV,64)):
 prod,s,b=producer(profile)
 for i in range(cap):
  sample={'index':i};b._samples.append(sample);token=N(_draft=sample,_book=b,_ended=True);s.observe_capture(object(),token,candidate={'i':i},fields={})
 assert len(prod._captures)==len(s._tokens)==cap
 sample={'index':cap};b._samples.append(sample);rejects(lambda:s.observe_capture(object(),N(_draft=sample,_book=b,_ended=True),candidate={},fields={}))
passed.append('actual_provider_capture_default32_old32_route64_and_plus1_refusal')
prod,s,b=producer(NAV)
for i in range(64):prod.attach_registry(object(),{},1,as_of_qpc_ns=i)
rejects(lambda:prod.attach_registry(object(),{},1,as_of_qpc_ns=64));assert len(prod._registry)==64;passed.append('same_route_registry64_exact_boundary')
# Pure original read collector seam; no native getter/Root authority.
saved=a._collect_original_reads;a._collect_original_reads=lambda book:({'valid_span':None},{})
try:
 for i in range(64):prod.read_current()
 rejects(lambda:prod.read_current())
finally:a._collect_original_reads=saved
assert len(prod._readings)==64;passed.append('original_read_current64_exact_boundary')
# Execute the exact new outer source quota expression, without invoking getters.
text=(stage/'competition/deepeye/tools/run_causal_functional_chain.py').read_text(encoding='utf8');tree=ast.parse(text);node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='read_current_with_registry');guard=next(n for n in node.body if isinstance(n,ast.If) and 'original registry observation cap exhausted' in ast.unparse(n))
expr=compile(ast.Expression(guard.test),'original outer source guard','eval')
for profile,cap in ((None,32),(OLD,32),(NAV,64)):
 obj=N(book=N(_navigation_profile=profile),_registry_observations=[None]*(cap-1));assert not eval(expr,dict(self=obj,_observation_capacity=obs));obj._registry_observations.append(None);assert eval(expr,dict(self=obj,_observation_capacity=obs))
passed.append('outer_original_registry_observation_same32_or64_guard')
for profile,cap in ((None,8192),(OLD,8192),(NAV,65536)):
 prod,s,b=producer(profile);refs=[(object(),'id'+str(i)) for i in range(cap-1)];prod._ids=refs
 first=refs[0];last=object();prod.bind_id(last,'last');assert len(prod._ids)==cap and prod._ids[0] is first
 assert prod.bind_id(last,'last')=='last';rejects(lambda:prod.bind_id(object(),'over'));rejects(lambda:prod.bind_id(last,'changed'));rejects(lambda:prod.bind_id(object(),'last'))
passed.append('IDs_old8192_route65536_finite_no_reset_reuse_or_rebind')
foreign=dataclasses.replace(NAV);assert obs(foreign)==32 and ids(foreign)==8192;rejects(lambda:obs({}));rejects(lambda:ids(True));passed.append('foreign_equal_no_extension_untyped_rejected')
prod,s,b=producer(NAV);b._navigation_profile=OLD;rejects(prod._check);passed.append('original_same_profile_binding_check_unchanged')
assert 'need(len(history_refs)<=32' in (stage/'competition/deepeye/simulation/authority/source_projection_v1/assembler.py').read_text(encoding='utf8');passed.append('legacy_export_history32_unchanged')
r=dict(passed=True,controls=passed,scope='pure DTO/method/AST budget seams; no original source authority, native/model/PDE/board/UI',final_gates='not_run');(D/'CONTROLS.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(json.dumps(r))

"""Original authenticated G05 projection plus explicit missing-feature metadata."""
import copy
import importlib
MAX_SOURCE_AGE_NS=30_000_000_000
def project_original_g05(association, *, max_source_age_ns):
    if type(max_source_age_ns) is not int or not 0 < max_source_age_ns <= MAX_SOURCE_AGE_NS:
        raise ValueError('DEMO_AGE_LIMIT')
    if association is None or isinstance(association,(dict,list,tuple,str,bytes,bytearray,int,float,bool)):
        raise ValueError('original private association required; public JSON is not provenance')
    original=importlib.import_module('competition.deepeye.simulation.authority.g05_csr_projection_v1')
    # This original call validates the real RootBook/scoped source/four E4 CRC
    # association. No wrapper boolean can substitute for that capability.
    projected=original.project_original_g05(association,max_source_age_ns=max_source_age_ns)
    result=dict(projected)
    public=copy.deepcopy(projected['public_input'])
    if public['projection_id']!='g05_csr_c28_demo_view_v1':
        raise ValueError('original G05 projection version changed')
    public['projection_id']='g05_csr_em3_demo_view_v2'
    descriptor=association.g05_mapping.channels.policy.demo_ai_profile
    public['engineering_profile']=dict(descriptor.engineering_profile)
    for obs in public['history']+[public['observation']]:
        obs['missing_feature_mask']=(~obs['quality']) & 15
    result['public_input']=public
    return result

"""Lazy facade for A343's typed original-G05 projection; never clones C36."""
import importlib

MAX_SOURCE_AGE_NS = 5_000_000_000

def project_original_g05(association, *, max_source_age_ns):
    if type(max_source_age_ns) is not int or not 0 < max_source_age_ns <= MAX_SOURCE_AGE_NS:
        raise ValueError('DEMO_AGE_LIMIT')
    if association is None or isinstance(association,(dict,list,tuple,str,bytes,bytearray,int,float,bool)):
        raise ValueError('original private association required; public JSON is not provenance')
    module = importlib.import_module('competition.deepeye.simulation.authority.g05_csr_projection_v1')
    return module.project_original_g05(association,max_source_age_ns=max_source_age_ns)

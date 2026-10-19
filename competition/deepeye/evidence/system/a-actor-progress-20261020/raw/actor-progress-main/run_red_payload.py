import hashlib,json,sys,unittest
from pathlib import Path
DEST=Path(__file__).resolve().parent;ROOT=DEST.parents[2];PRODUCT=ROOT/'.local/deepeye-implementation-a'
sys.path[:0]=[str(PRODUCT),str(PRODUCT/'competition/deepeye'),str(ROOT/'.local/deepeye-host-deps'),str(DEST)]
names=['progress_gap_red.ProgressWitness.'+n for n in ('test_expiry_after_real_geometry_must_not_commit','test_expiry_only_inside_commit_must_reach_final_fence','test_full_step_end_on_progress_deadline_must_fail')]
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
modules={}
for n,m in list(sys.modules.items()):
    f=getattr(m,'__file__',None)
    if f and Path(f).is_file() and Path(f).resolve().is_relative_to(PRODUCT):
        modules[n]={'path':str(Path(f).resolve()),'sha256':hashlib.sha256(Path(f).read_bytes()).hexdigest()}
with (DEST/'red-result.json').open('x',encoding='utf-8') as f:json.dump({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'module_origins':modules},f,indent=2);f.write('\n')
sys.exit(0 if result.wasSuccessful() else 1)

import difflib, json, shutil
from verify import OUT, ROOT, SIM, OWNED, REVIEW, sha, read, write, sources

initial=read(OUT/'audit-before.json')['source_manifest']
current=sources(SIM)
assert set(current)==set(initial)
assert all(current[p]==h for p,h in initial.items() if p not in OWNED)
assert sha(REVIEW/'stage/tests/review_boundary.gd')==sha(OUT/'independent-boundary-original.gd')==sha(OUT/'stage/tests/review_boundary.gd')
for rel in OWNED:
    dest=OUT/'candidate'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(SIM/rel,dest)
    before=(OUT/'baseline'/rel).read_text(encoding='utf-8').splitlines(True)
    after=(SIM/rel).read_text(encoding='utf-8').splitlines(True)
    (OUT/(pathlib_name:=dest.name+'.diff')).write_text(''.join(difflib.unified_diff(before,after,fromfile='baseline/'+rel,tofile='candidate/'+rel)),encoding='utf-8')
runs={}
for folder in sorted((OUT/'logs').iterdir()):
    if not (folder/'result.json').exists(): continue
    r=read(folder/'result.json')
    before=r['source_before_sha256']; after=r['source_after_sha256']
    changed={p:{'before':before[p],'after':after.get(p)} for p in before if before[p]!=after.get(p)}
    added={p:h for p,h in after.items() if p not in before}
    assert not changed
    assert all(p.endswith('.gd.uid') and p[:-4] in before for p in added)
    assert r['terminated'] and not r['timed_out'] and r['product_unchanged']
    runs[folder.name]={'pid':r['pid'],'exit_code':r['exit_code'],'terminated':r['terminated'],'timed_out':r['timed_out'],'stage_existing_files_unchanged':not changed,'stage_added':added,'source_unchanged':r['source_unchanged'],'product_unchanged':r['product_unchanged']}
for name in ['tooltip-bound-green','independent-candidate','editor696-candidate','persistence618-candidate','scene-smoke-candidate','import-candidate']:
    r=read(OUT/'logs'/name/'result.json')
    assert r['exit_code']==0
    assert all(r['source_before_sha256'][p]==current[p] for p in current)
for name,needle in [('tooltip-bound-green','UI_FIT checks=266 failures=0'),('independent-candidate','BOUNDARY_RESULT checks=15 failures=0'),('editor696-candidate','TESTS checks=696 failures=0'),('persistence618-candidate','TESTS checks=618 failures=0')]:
    assert needle in (OUT/'logs'/name/'stdout.bin').read_text(encoding='utf-8')
write(OUT/'process-termination.json',runs)
write(OUT/'audit-after.json',{'source_manifest':current,'only_owned_changed':True,'changed_product_paths':[p for p in initial if initial[p]!=current[p]],'unchanged_independent_probe_sha256':sha(OUT/'independent-boundary-original.gd')})
pins={p:{'path':str((SIM/p).relative_to(ROOT)).replace('\\','/'),'sha256':current[p]} for p in [*OWNED,'project.godot']}
write(OUT/'final-hashes.json',pins)
print(json.dumps({'candidate_files':pins,'owned_changed_only':True,'processes_terminated':len(runs),'stage_import_additions':{k:v['stage_added'] for k,v in runs.items() if v['stage_added']}},ensure_ascii=False,indent=2))
